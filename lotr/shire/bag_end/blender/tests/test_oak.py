import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from bagend import layout as L, oak, scene, terrain, treekit

_built = {}


def grown():
    """The oak, built once for the tests below (rebuilt if another test has reset the scene)."""
    o = _built.get("oak")
    try:
        if o is not None and bpy.data.objects.get("oak_trunk") == o.trunk:
            return o
    except ReferenceError:
        pass
    scene.reset_scene()
    _built["oak"] = oak.build()
    return _built["oak"]


def coords(obj):
    co = np.empty(3 * len(obj.data.vertices))
    obj.data.vertices.foreach_get("co", co)
    m = np.array(obj.matrix_world)
    return co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]


def shells(obj):
    sh = np.empty(len(obj.data.vertices), dtype=np.int32)
    obj.data.attributes["shell"].data.foreach_get("value", sh)
    return sh


def triangles(mesh):
    """Every face as a fan of triangles: (n, 3) vertex indices."""
    starts = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_start", starts)
    total = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_total", total)
    loops = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loops)
    n = total - 2
    poly = np.repeat(np.arange(len(starts)), n)
    k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    first = starts[poly]
    return np.stack([loops[first], loops[first + k + 1], loops[first + k + 2]], axis=1)


def test_oak_is_a_separate_print_in_its_own_collection():
    o = grown()
    assert {o.trunk.users_collection[0].name, o.crown.users_collection[0].name} == {"oak"}
    assert "preview" not in bpy.data.collections


def test_oak_wood_and_foliage_are_closed_solids():
    o = grown()
    for obj in (o.trunk, o.crown):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        try:
            assert all(e.is_manifold for e in bm.edges), obj.name
            assert bm.calc_volume(signed=True) > 0, obj.name
        finally:
            bm.free()


def test_every_wood_shell_is_a_clean_solid():
    # Overlapping closed shells are fine; a shell that is inside out or crosses itself is not.
    o = grown()
    assert o.tangled == 0
    co, sh, tri = coords(o.trunk), shells(o.trunk), triangles(o.trunk.data)
    tri_shell = sh[tri[:, 0]]
    vol = np.einsum("ij,ij->i", co[tri[:, 0]], np.cross(co[tri[:, 1]], co[tri[:, 2]])) / 6.0
    per_shell = np.bincount(tri_shell, weights=vol)
    assert np.all(per_shell > 0), np.nonzero(per_shell <= 0)
    local = np.empty(len(sh), dtype=np.int64)
    for s in range(sh.max() + 1):
        vidx = np.nonzero(sh == s)[0]
        local[vidx] = np.arange(len(vidx))
        tree = BVHTree.FromPolygons(co[vidx].tolist(), local[tri[tri_shell == s]].tolist())
        assert not tree.overlap(tree), s


def test_foliage_never_crosses_itself_and_every_clump_is_held_by_a_branch():
    o = grown()
    tree = BVHTree.FromObject(o.crown, bpy.context.evaluated_depsgraph_get())
    assert not tree.overlap(tree)
    lab = treekit.islands(o.crown.data)

    def inside(p):
        hits, origin, up = 0, Vector(p), Vector((0.0, 0.0, 1.0))
        while True:
            loc, _, _, _ = tree.ray_cast(origin, up)
            if loc is None:
                return hits % 2 == 1
            hits += 1
            origin = loc + up * 1e-4

    held = set()
    for tip in o.tips:
        if inside(tip):
            loc, _, idx, _ = tree.find_nearest(Vector(tip))
            held.add(int(lab[o.crown.data.polygons[idx].vertices[0]]))
    assert held == set(np.unique(lab).tolist()), (len(held), len(np.unique(lab)))
    assert sum(inside(t) for t in o.tips) >= 0.9 * len(o.tips)          # the twigs end in leaves


def test_crown_is_a_full_dome_not_a_flat_parasol():
    o = grown()
    x, y = L.OAK
    g = float(terrain.ground(x, y))
    co = coords(o.crown)
    rho = np.hypot(co[:, 0] - x, co[:, 1] - y)
    width = max(np.ptp(co[:, 0]), np.ptp(co[:, 1]))
    height = np.ptp(co[:, 2])
    assert 0.8 * L.OAK_CROWN <= width <= 1.15 * L.OAK_CROWN, width
    assert height >= 0.45 * width, (height, width)                      # the old crown: 1.7 of 10 m
    assert abs(co[:, 2].max() - g - L.OAK_HEIGHT) < 0.6, co[:, 2].max() - g
    tops = [co[(rho >= b) & (rho < b + 0.5), 2].max() for b in np.arange(0.0, 0.8 * width / 2, 0.5)]
    assert all(b <= a + 0.15 for a, b in zip(tops, tops[1:])), np.round(tops, 2)   # falls away outward...
    assert tops[0] - co[rho > 0.8 * width / 2, 2].max() > 1.0, tops[0]           # ...domed, highest in the middle
    # dense: seen from above, nearly all of the crown's disc is foliage
    tree = BVHTree.FromObject(o.crown, bpy.context.evaluated_depsgraph_get())
    hits = total = 0
    for gx in np.linspace(-0.7, 0.7, 15) * width / 2:
        for gy in np.linspace(-0.7, 0.7, 15) * width / 2:
            if math.hypot(gx, gy) > 0.7 * width / 2:
                continue
            total += 1
            hits += tree.ray_cast(Vector((x + gx, y + gy, 30.0)), Vector((0, 0, -1)))[0] is not None
    assert hits >= 0.85 * total, (hits, total)


def test_oak_has_a_trunk_with_low_spreading_limbs():
    o = grown()
    x, y = L.OAK
    g = float(terrain.ground(x, y))
    trunk, limbs = o.branches[0], [b for b in o.branches if b.level == 1]
    assert trunk.radii[:5].max() >= 1.2 * L.OAK_GIRTH / 2                # the root flare
    assert len(limbs) >= 8
    starts = [b.pts[0, 2] - g for b in limbs if np.linalg.norm(b.pts[0, :2] - trunk.pts[0, :2]) < 0.6]
    assert min(starts) < 1.2 * L.OAK_FORK                                 # limbs leave low...
    reach = [np.hypot(*(b.pts[-1, :2] - (x, y))) for b in limbs]
    assert max(reach) > 0.35 * L.OAK_CROWN                                # ...and spread


def test_branches_are_thick_enough_to_print():
    o = grown()
    assert min(b.radii.min() for b in o.branches) >= L.OAK_TWIG / 2 - 1e-9
    w, l, depth = oak._bark_scale(np.array([L.OAK_TWIG / 2, 0.1, 0.2, 0.6]))
    assert np.all(depth <= 0.3 * np.array([L.OAK_TWIG / 2, 0.1, 0.2, 0.6]))   # bark never eats a twig


def test_bark_relief_is_deep_enough_to_print():
    # HO loses grooves under ~1.5 cm real: furrows 1.5-3 cm deep on the old wood, a few cm apart.
    w, l, depth = oak._bark_scale(np.array([L.OAK_GIRTH / 2, 0.2]))
    assert np.all((depth >= 0.015) & (depth <= 0.031)), depth
    assert np.all((w >= 0.04) & (w <= 0.1)) and np.all(l > 2.5 * w), (w, l)   # long ridges along the wood
    nz = treekit.Noise(1)
    theta, s = np.meshgrid(np.linspace(0, 2 * np.pi, 400, endpoint=False), np.linspace(0, 1.5, 120))
    relief = oak._bark(nz, theta.ravel(), s.ravel(), np.full(theta.size, L.OAK_GIRTH / 2), 0.3, 0.0)
    assert relief.max() <= 0 and relief.min() < -0.9 * depth[0]
    furrows = np.mean(relief < -0.5 * depth[0])
    assert 0.15 < furrows < 0.6, furrows
    around, along = oak._grain(np.array([L.OAK_GIRTH / 2, 0.2]))
    assert np.all(around <= w / 4) and np.all(along <= l / 3)            # the mesh resolves the furrows


def test_oak_stands_on_the_turf_and_has_a_peg_below_it():
    o = grown()
    x, y = L.OAK
    g = float(terrain.ground(x, y))
    co, sh = coords(o.trunk), shells(o.trunk)
    peg, wood = co[sh == sh.max()], co[sh < sh.max()]
    below = wood[:, 2] - terrain.ground(wood[:, 0], wood[:, 1])
    assert below.min() > -L.OAK_SEAT - 0.03, below.min()                 # nothing but the peg goes into the hill
    footprint = np.hypot(wood[:, 0] - x, wood[:, 1] - y)
    seated = footprint[below < 0.0]
    assert len(seated) and seated.max() > 0.8 * L.OAK_GIRTH              # the foot and the roots sit on the turf
    dia, depth = L.OAK_PEG
    assert abs(peg[:, 2].min() - (g - L.OAK_SEAT - depth)) < 1e-6
    assert peg[:, 2].max() > g                                           # it runs up into the trunk
    assert abs(np.ptp(peg[:, 0]) - dia) < 0.01 and np.ptp(peg[:, 1]) < 0.9 * dia   # keyed: one flat side
    assert np.hypot(peg[:, 0].mean() - x, peg[:, 1].mean() - y) < 0.1


def test_oak_fits_a_256_mm_print_bed_at_ho_and_at_o():
    o = grown()
    co = np.concatenate([coords(o.trunk), coords(o.crown)])
    size = np.ptp(co, axis=0)
    for scale in (87, 48):
        assert np.all(size / scale * 1000 <= 256), (scale, size / scale * 1000)


def test_oak_vertex_count_is_reasonable():
    o = grown()
    n = len(o.trunk.data.vertices) + len(o.crown.data.vertices)
    assert n < 450_000, n


def test_oak_is_repeatable():
    def shape():
        scene.reset_scene()
        o = oak.build()
        return [np.round(coords(obj), 5) for obj in (o.trunk, o.crown)]
    a, b = shape(), shape()
    assert all(x.shape == y.shape and np.array_equal(x, y) for x, y in zip(a, b))

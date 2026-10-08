import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, geometry
from mathutils.bvhtree import BVHTree

from bagend import parts as P, scene, wood as W


def is_closed(obj):
    """Manifold, no holes, and normals pointing out (positive volume)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        return (all(e.is_manifold for e in bm.edges) and not any(e.is_boundary for e in bm.edges)
                and bm.calc_volume(signed=True) > 0)
    finally:
        bm.free()


def crossings(bm):
    """Places where a shell of bm passes through itself (shells may touch or overlap each other).
    The BVH finds candidate triangle pairs; an edge of one must cut the other away from their
    shared corners to count. Pairs sharing an edge, and triangles of one flat face, are skipped."""
    bm = bm.copy()
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="EAR_CLIP")
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    seen, found = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        shell, stack = [], [f0]
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            shell.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        index = {}
        tris = [[index.setdefault(v.index, len(index)) for v in f.verts] for f in shell]
        co = [bm.verts[i].co.copy() for i, _ in sorted(index.items(), key=lambda t: t[1])]
        tree = BVHTree.FromPolygons(co, tris, all_triangles=True)
        for a, b in tree.overlap(tree):
            if len(set(tris[a]) & set(tris[b])) >= 2:
                continue
            A, B = [co[i] for i in tris[a]], [co[i] for i in tris[b]]
            na, nb = geometry.normal(A), geometry.normal(B)
            if abs(na.dot(nb)) > 0.99999 and abs(na.dot(B[0] - A[0])) < 1e-7:
                continue
            for X, Y in ((A, B), (B, A)):
                for i in range(3):
                    d = X[(i + 1) % 3] - X[i]
                    p = geometry.intersect_ray_tri(Y[0], Y[1], Y[2], d.normalized(), X[i], True)
                    if p is not None and (p - X[i]).length <= d.length and min((p - v).length for v in A + B) > 1e-6:
                        found.append(tuple(p))
    bm.free()
    return found


ARCH = lambda u: 2.0 + 0.3 * math.sqrt(max(0.0, 1 - (u / 0.86) ** 2))    # noqa: E731  an eave with steep feet
US = [-0.86 + 1.72 * i / 60 for i in range(61)]
PIECES = {
    "post": lambda bm, s: W.timber(bm, (0, 0, 1), (0.12, 0.12, 2.1), seed=s, hidden=(2,)),
    "turned post": lambda bm, s: W.timber(bm, (0, 0, 1), (0.12, 0.12, 0.95), Matrix.Rotation(0.2, 4, "Z"), seed=s),
    "seat plank": lambda bm, s: W.timber(bm, (0, 0, 0.45), (1.4, 0.12, 0.04), seed=s, amp=0.004),
    "back rail": lambda bm, s: W.timber(bm, (0, 0, 0.45), (1.4, 0.035, 0.11), seed=s, amp=0.004),
    "brace": lambda bm, s: W.timber(bm, (0, 0, 0.5), (1.14, 0.05, 0.09), Matrix.Rotation(-0.6, 4, "Y"), seed=s),
    "clad box": lambda bm, s: W.timber(bm, (0, 0, 2.2), (0.26, 0.26, 0.3), seed=s, seams=0.085, amp=0.003),
    "door ring": lambda bm, s: W.segmented_ring(bm, 0, 0.84, 0.785, 0.865, -0.03, 0.23, 10, random.Random(s), s),
    "window ring": lambda bm, s: W.segmented_ring(bm, 0, 0.84, 0.18, 0.245, -0.025, 0.12, 6, random.Random(s), s),
    "knee brace": lambda bm, s: W.knee_brace(bm, 0.0, 2.0, seed=s),
    "header band": lambda bm, s: W.header_band(bm, US, ARCH, ((-0.43, 0.43), (0.43, 0.43)), s),
    "eave hood": lambda bm, s: W.eave_hood(bm, bm, US, ARCH, 0.32, random.Random(s), s),
    "door": lambda bm, s: W.plank_door(bm, 0.845, 0.781, 0.22, 0.06, random.Random(s), s),
    "log": lambda bm, s: W.log(bm, (0, 0, 0.98), 0.13, 0.12, 0.48, Matrix.Rotation(math.pi / 2, 4, "X"), s),
    "finial": lambda bm, s: W.finial(bm, 0.0, 0.0, 1.2, s),
}


def test_every_kind_of_wood_is_closed_and_never_passes_through_itself():
    # Deep grooves and checks, worn corners and split ends must not fold a piece through itself,
    # even at the steep feet of an arched eave and on a soffit board sheared to follow it.
    scene.reset_scene()
    for name, build in PIECES.items():
        for seed in (1, 2, 9):
            bm = bmesh.new()
            build(bm, seed)
            assert not crossings(bm), (name, seed, crossings(bm)[:3])
            assert is_closed(P.to_object(f"{name}_{seed}", bm, None, "test", bevel=0.012)), (name, seed)


def test_timber_is_repeatable_per_seed_and_stays_near_its_box():
    def post(seed):
        bm = bmesh.new()
        W.timber(bm, (0.0, 0.0, 0.0), (0.12, 0.12, 2.0), seed=seed)
        out = [tuple(v.co) for v in bm.verts]
        bm.free()
        return out
    a = post(3)
    assert a == post(3) and a != post(4)
    assert all(abs(x) <= 0.06 + 0.016 and abs(z) <= 1.0 + 0.016 for x, _, z in a)


def test_grain_cuts_in_deep_enough_to_print_and_no_deeper_than_safe():
    # A 12 cm post, unbent. Down the middle of each face (clear of the worn corners) its grain and
    # checks cut in by at least 1.5 cm somewhere (0.17 mm at HO), never more than CUT_LIMIT of its
    # thickness; most of each face is cut a little, with uncut wood between the grooves; and
    # nothing but a knot stands proud of the sawn face, by less than 6 mm.
    for seed in range(6):
        bm = bmesh.new()
        W.timber(bm, (0.0, 0.0, 0.0), (0.12, 0.12, 2.0), seed=seed, amp=0.0)
        depth = [0.06 - max(abs(v.co.x), abs(v.co.y)) for v in bm.verts
                 if min(abs(v.co.x), abs(v.co.y)) < 0.019 and abs(v.co.z) < 0.9]
        cut = sum(d > 0.004 for d in depth) / len(depth)
        assert 0.015 < max(depth) <= W.CUT_LIMIT * 0.12 + 1e-6, (seed, max(depth))
        assert min(depth) > -0.006, (seed, min(depth))
        assert 0.1 < cut < 0.75, (seed, cut)
        bm.free()


def along_grooves(g, s, keep):
    """Depths along the grain lines of Grain g that keep(groove) picks, sampled at s."""
    out = [t[3] * np.clip(t[7] + t[8] * W._noise((t[6][1], t[6][0]), s, 0.45), t[9], 1.0) for t in g.grooves if keep(t)]
    return np.concatenate(out) if out else np.zeros(0)


def test_thick_faces_get_deeper_grain():
    # Through 8 cm or more (posts, beams, a header band's face) the main grain is cut 1.6-2.4 cm
    # deep (0.18-0.28 mm at HO), and fades only a little along the piece: over the main grooves'
    # whole length 80 % is at least 1.4 cm deep. (Fine lines, half-width under 1 cm, are left out.)
    s = np.linspace(0.0, 2.0, 200)
    for seed in range(10):
        g = W.Grain(seed, 2.0, [W.Side(0.12, 0.12, 0.036, True, soft=0.018) for _ in range(4)])
        main = [t for t in g.grooves if t[2] >= 0.0095]
        assert main and all(0.016 - 1e-9 <= t[3] <= 0.024 + 1e-9 for t in main), [t[3] for t in main]
        assert np.percentile(along_grooves(g, s, lambda t: t[2] >= 0.0095), 20) >= 0.014


def test_door_boards_and_thin_pieces_have_grain_that_reads_at_ho():
    # The door's 6 cm boards: grooves about 1 cm deep along their length (0.11 mm at HO). Boards,
    # legs and rails 3.5-8 cm thick: about 0.7-0.8 cm; a narrow face (a leg's, a plank's edge) has
    # one or two lines that deep. All within 20 % of the thickness. Under 3.5 cm (the birdhouse's
    # roof boards) the grain is as it was.
    door, plank, leg, slab = [], [], [], []
    for seed in range(20):
        s = np.linspace(0.0, 1.5, 150)
        g = W.Grain(seed, 1.5, [W.Side(0.125, 0.06, 0.008, True)])
        assert all(t[3] <= W.GRAIN_LIMIT * 0.06 + 1e-9 for t in g.grooves)
        door.append(along_grooves(g, s, lambda t: t[2] >= 0.0095))
        g = W.Grain(seed, 1.5, [W.Side(0.12, 0.04, 0.012, True, soft=0.006), W.Side(0.04, 0.12, 0.012, True, soft=0.006)] * 2)
        assert all(t[3] <= W.GRAIN_LIMIT * 0.04 + 1e-9 for t in g.grooves if t[0] in (0, 2))
        plank.append(along_grooves(g, s, lambda t: t[0] in (0, 2) and t[2] >= 0.0095))
        g = W.Grain(seed, 0.5, [W.Side(0.07, 0.07, 0.021, True, soft=0.0105) for _ in range(4)])
        assert {t[0] for t in g.grooves} == {0, 1, 2, 3}                    # every face has a line
        leg.append(along_grooves(g, np.linspace(0.0, 0.5, 60), lambda t: True))
        g = W.Grain(seed, 0.34, [W.Side(0.24, 0.03, 0.009, True, soft=0.0045), W.Side(0.03, 0.24, 0.009, True, soft=0.0045)] * 2)
        assert all(t[7:10] == W.FADE for t in g.grooves if t[0] in (0, 2) and t[2] >= 0.0095)
    assert 0.009 <= np.median(np.concatenate(door)) <= 0.0125, np.median(np.concatenate(door))
    assert 0.0065 <= np.median(np.concatenate(plank)) <= 0.0085, np.median(np.concatenate(plank))
    assert 0.0065 <= np.median(np.concatenate(leg)) <= 0.0085, np.median(np.concatenate(leg))


def test_door_board_cuts_reach_about_a_centimetre_and_no_further_than_safe():
    # Built, unbent and square to the door: away from its rolled edges the board's face is cut in
    # by over 0.9 cm in places, and nowhere deeper than CUT_LIMIT of its 6 cm.
    for seed in range(4):
        bm = bmesh.new()
        verts = W.door_board(bm, 0.84, 0.78, -0.06, 0.06, 0.22, 0.06, 0.0, 0.0, seed)
        front = [v for v in verts if v.co.y < 0.22 + 0.06 - 1e-6 and abs(v.co.x) < 0.045 and abs(v.co.z - 0.84) < 0.6]
        depth = [v.co.y - 0.22 for v in front]
        assert max(depth) > 0.009, (seed, max(depth))
        assert max(depth) <= W.CUT_LIMIT * 0.06 + 0.004, (seed, max(depth))           # + the board's bend
        bm.free()


def test_grain_is_cut_in_the_pieces_own_frame():
    # Turned 0.7 rad about y, a beam's relief turns with it: in its own frame every vertex is
    # inside its box (but for a knot's few mm), as for the same beam unturned.
    turn = Matrix.Rotation(0.7, 4, "Y")
    bm = bmesh.new()
    W.timber(bm, (0.5, 0.2, 1.0), (1.2, 0.1, 0.14), turn, seed=5, amp=0.0)
    back = (Matrix.Translation((0.5, 0.2, 1.0)) @ turn).inverted()
    for v in bm.verts:
        x, y, z = back @ v.co
        assert abs(x) <= 0.6 + 1e-6 and abs(y) <= 0.05 + 0.006 and abs(z) <= 0.07 + 0.006, (x, y, z)
    bm.free()


def test_ring_segments_follow_their_curve_and_only_cut_in():
    bm = bmesh.new()
    W.arc_timber(bm, 0.3, 1.0, 0.5, 0.6, 0.0, 1.2, -0.03, 0.2, seed=4, amp=0.0)
    for v in bm.verts:
        r = math.hypot(v.co.x - 0.3, v.co.z - 1.0)
        a = math.atan2(v.co.z - 1.0, v.co.x - 0.3)
        assert 0.5 - 0.006 <= r <= 0.6 + 0.006 and -0.03 - 0.006 <= v.co.y <= 0.2 + 1e-6, tuple(v.co)
        assert -1e-6 <= a <= 1.2 + 1e-6, a
    bm.free()


def test_knee_brace_is_a_closed_solid_even_when_bevelled():
    scene.reset_scene()
    bm = bmesh.new()
    W.knee_brace(bm, 0.0, 2.0, seed=3)
    assert is_closed(P.to_object("brace", bm, None, "test", bevel=0.012))


def test_door_boards_stay_inside_the_doorway():
    r, cz, front = 0.78, 0.84, 0.22
    bm = bmesh.new()
    W.plank_door(bm, cz, r, front, 0.06, random.Random(1), 7)
    assert len(bm.verts) > 0
    for v in bm.verts:
        assert math.hypot(v.co.x, v.co.z - cz) <= r + 0.006, tuple(v.co)
        assert front - 0.02 <= v.co.y <= front + 0.06 + 1e-6, tuple(v.co)
    bm.free()


def test_wood_uses_the_shared_rng_as_the_plain_parts_did():
    # The door, the rings and the soffit draw on a front's shared rng; drawing exactly as the plain
    # parts did keeps everything built after them (bricks, nails, sills) where it was.
    def plain_door(rng, r):
        u = -r
        while u < r - 0.02:
            w, gap = rng.uniform(0.105, 0.15), rng.uniform(0.008, 0.016)
            u0, u1 = u + gap / 2, min(r - 0.002, u + w - gap / 2)
            u += w
            if u1 - u0 >= 0.02:
                rng.uniform(-0.006, 0.004), rng.uniform(-0.007, 0.007)

    def plain_soffit(rng, us):
        u, u1 = us[0], us[-1]
        while u < u1 - 0.02:
            w, gap = rng.uniform(0.085, 0.12), rng.uniform(0.008, 0.016)
            a, b = u + gap / 2, min(u1, u + w - gap / 2)
            u += w
            if b - a >= 0.02:
                rng.uniform(-0.006, 0.004)

    for build, plain in (
            (lambda rng: W.plank_door(bmesh.new(), 0.84, 0.78, 0.22, 0.06, rng, 7), lambda rng: plain_door(rng, 0.78)),
            (lambda rng: W.segmented_ring(bmesh.new(), 0, 0.84, 0.78, 0.86, -0.03, 0.23, 10, rng, 7),
             lambda rng: [rng.uniform(-1, 1) for _ in range(20)]),
            (lambda rng: W.eave_hood(bmesh.new(), bmesh.new(), US, ARCH, 0.32, rng, 7), lambda rng: plain_soffit(rng, US))):
        a, b = random.Random(5), random.Random(5)
        build(a)
        plain(b)
        assert a.random() == b.random()


def test_bevel_leaves_wood_alone_and_the_wood_tag_is_not_kept():
    # The worn corners replace the bevel: a bevel would only bead the grooves. The tag that tells
    # to_object so is not written into the mesh.
    scene.reset_scene()
    bm = bmesh.new()
    W.timber(bm, (0, 0, 1), (0.12, 0.12, 1.0), seed=2)
    n = len(bm.verts)
    obj = P.to_object("post", bm, None, "test", bevel=0.012)
    assert len(obj.data.vertices) == n
    assert W.TAG not in obj.data.attributes


def test_wood_vertex_counts_stay_sane():
    # Dense across the grain, sparse along it: a 2 m post is a few thousand vertices.
    bm = bmesh.new()
    W.timber(bm, (0, 0, 1), (0.12, 0.12, 2.0), seed=1)
    assert 1500 < len(bm.verts) < 6000, len(bm.verts)
    bm.free()


def test_every_timber_object_in_the_scene_is_closed():
    from bagend import doorfront, fronts, garden
    scene.reset_scene()
    doorfront.build()
    fronts.build()
    garden.build()
    wood = {"timber", "ring", "door", "green_paint"}
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.data.materials
            and o.data.materials[0].name in wood]
    assert len(objs) > 25
    for o in objs:
        assert is_closed(o), o.name

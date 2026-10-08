import random

import bmesh
import numpy as np
from mathutils.bvhtree import BVHTree

from bagend import scene, stone

KINDS = (("rubble", stone.RUBBLE, None), ("wall_face", stone.RUBBLE, (1, -1)), ("slate", stone.SLATE, None),
         ("riser", stone.SLATE, (0, 1)), ("flag", stone.FLAG, None))


def is_closed(obj):
    """Manifold, no holes, and normals pointing out (positive volume)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        return (all(e.is_manifold for e in bm.edges) and not any(e.is_boundary for e in bm.edges)
                and bm.calc_volume(signed=True) > 0)
    finally:
        bm.free()


def one(style, face, seed, size=(0.34, 0.26, 0.2)):
    pile = stone.Pile()
    w = stone.block(pile, (0.0, 0.0, 0.0), size, random.Random(seed), style=style, face=face)
    return pile, w


def folds(verts, quads):
    """Pairs of triangles of one shell that cross each other (not merely touching at a shared vertex)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in verts]
    for q in quads:
        bm.faces.new([vs[i] for i in q])
    bm.verts.index_update()
    tris = bm.calc_loop_triangles()
    tree = BVHTree.FromBMesh(bm)
    bad = 0
    for i, j in tree.overlap(tree):
        if i != j and not ({lp.vert.index for lp in tris[i]} & {lp.vert.index for lp in tris[j]}):
            bad += 1
    bm.free()
    return bad


def test_every_kind_of_stone_is_a_closed_outward_solid():
    scene.reset_scene()
    for name, style, face in KINDS:
        for seed in range(3):
            pile, _ = one(style, face, seed)
            assert is_closed(pile.to_object(f"{name}_{seed}", None, "test")), (name, seed)
    pile = stone.Pile()                                   # several stones, overlapping, in one object
    rng = random.Random(9)
    for k in range(4):
        stone.block(pile, (0.15 * k, 0.0, 0.0), (0.3, 0.2, 0.16), rng)
    stone.slab(pile, (0.2, 0.0, 0.12), (0.8, 0.4, 0.08), rng)
    assert is_closed(pile.to_object("heap", None, "test"))


def test_stones_never_fold_through_themselves():
    # Every vertex moves only along its own ray from the stone's core, so however rough the faces,
    # no stone's shell crosses itself (the brief: self-intersecting shells do not print).
    for name, style, face in KINDS:
        for seed in range(4):
            pile, _ = one(style, face, seed)
            assert folds(pile.verts[0], pile.quads[0]) == 0, (name, seed)
    pile = stone.Pile()
    stone.slab(pile, (0.0, 0.0, 0.0), (1.0, 0.6, 0.09), random.Random(3))      # a tread
    assert folds(pile.verts[0], pile.quads[0]) == 0


def test_wall_stone_faces_carry_print_scale_relief_and_stay_in_their_box():
    # Split faces, breaks and pits: the show face varies by 1.5 cm or more (0.17 mm at HO, the
    # brief's floor), and nothing bulges more than 4 cm past the stone's nominal box.
    for seed in range(6):
        _, w = one(stone.RUBBLE, (1, -1), seed)
        front = w[(np.abs(w[:, 0]) < 0.12) & (np.abs(w[:, 2]) < 0.06) & (w[:, 1] < 0.0)]
        relief = front[:, 1].max() - front[:, 1].min()
        assert 0.015 <= relief <= 0.12, (seed, relief)
        assert np.all(np.abs(w) <= np.array([0.17, 0.13, 0.1]) + 0.04), seed


def test_slate_top_is_its_height_flat_but_flaked_and_its_edges_layered():
    for seed in range(6):
        pile = stone.Pile()
        t = stone.slab(pile, (0.0, 0.0, 0.0), (1.0, 0.6, 0.09), random.Random(seed))
        assert abs(t[:, 2].max()) < 1e-9, seed                               # the top is the tread height
        top = t[(np.abs(t[:, 0]) < 0.4) & (np.abs(t[:, 1]) < 0.24) & (t[:, 2] > -0.045)]
        assert 0.008 <= top[:, 2].max() - top[:, 2].min() <= 0.045, seed    # flakes off, still walkable
        end = t[(t[:, 0] > 0.3) & (np.abs(t[:, 1]) < 0.1)]                   # one end, band by band
        bands = np.round(end[:, 2] / 0.01)
        reach = np.array([end[bands == b][:, 0].max() for b in np.unique(bands)])
        assert np.max(np.abs(np.diff(reach))) >= 0.01, seed                 # laminae stepped 1 cm or more


def test_stones_are_repeatable():
    _, a = one(stone.SLATE, None, 5)
    _, b = one(stone.SLATE, None, 5)
    _, c = one(stone.SLATE, None, 6)
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_a_hidden_back_stays_coarse():
    # A wall stone shows only its face: the lattice is fine near it and coarse behind.
    full, _ = one(stone.RUBBLE, None, 1)
    faced, _ = one(stone.RUBBLE, (1, -1), 1)
    assert len(faced.verts[0]) < 0.8 * len(full.verts[0])

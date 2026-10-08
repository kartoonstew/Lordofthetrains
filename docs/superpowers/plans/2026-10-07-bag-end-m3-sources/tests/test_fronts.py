import dataclasses

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

from bagend import frontkit as K, fronts, hill, layout as L, scene

NAMES = ("round_window_west", "round_window_rack", "lattice_window", "ornate")


def first_hit(origin, target):
    dg = bpy.context.evaluated_depsgraph_get()
    o, t = Vector(origin), Vector(target)
    hit, _, _, _, obj, _ = bpy.context.scene.ray_cast(dg, o, (t - o).normalized())
    return obj.name if hit else None


def test_every_front_is_built_named_and_has_one_material_per_part():
    scene.reset_scene()
    fronts.build()
    for name in NAMES:
        objs = list(bpy.data.collections[f"{name}_front"].objects)
        assert len(objs) >= 9, (name, len(objs))
        for o in objs:
            assert o.name.startswith(name + "_"), o.name
            assert len(o.data.materials) == 1, o.name
    assert not [o.name for o in bpy.data.objects if o.name.startswith("cutter")]


def test_windows_can_be_seen_with_the_hill_built():
    # Look straight at the middle of every window from 3 m out: its glass or bars come first.
    scene.reset_scene()
    hill.build()
    fronts.build()
    targets = [(n, *fronts.ROUND_WINDOWS[n][:2]) for n in NAMES]
    half, z0, height = fronts.ARCHED_WINDOW
    targets.append(("ornate", 0.0, z0 + 0.4 * height))
    for name, u, z in targets:
        place = K.placement(L.front(name))
        centre = place @ Vector((u, 0.0, z))
        out = (place.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
        hit = first_hit(centre + 3.0 * out, centre)
        assert hit and hit.startswith(name + "_") and "window" in hit, (name, u, z, hit)


def test_each_front_fills_its_dug_out():
    # layout.py sets each front's width; its wall spans it exactly, so no hill gap opens beside it.
    scene.reset_scene()
    fronts.build()
    for name in NAMES:
        f = L.front(name)
        wall = bpy.data.objects[f"{name}_wall"]
        to_front = K.placement(f).inverted() @ wall.matrix_world
        us = [(to_front @ v.co).x for v in wall.data.vertices]
        assert abs(min(us) + f.width / 2) < 0.02 and abs(max(us) - f.width / 2) < 0.02, (name, min(us), max(us))


def test_ornate_bargeboard_follows_the_eave():
    scene.reset_scene()
    fronts.build()
    f = L.front("ornate")
    band = bpy.data.objects["ornate_bargeboard"]
    to_front = K.placement(f).inverted() @ band.matrix_world
    pts = [to_front @ v.co for v in band.data.vertices]
    crown = max(p.z for p in pts if abs(p.x) < 0.1)
    assert abs(crown - (f.eave + 0.03)) < 0.01, crown
    assert max(abs(p.x) for p in pts) < f.width / 2


def test_fronts_follow_their_layout_placement():
    # The lattice front is turned in layout.py; moved and turned further, all of it must follow.
    def world_points():
        fronts.lattice_front()
        return {o.name: [o.matrix_world @ v.co for v in o.data.vertices]
                for o in bpy.data.collections["lattice_window_front"].objects}

    scene.reset_scene()
    f = L.front("lattice_window")
    before, old = world_points(), K.placement(f)
    moved = dataclasses.replace(f, x=f.x - 2.0, y=f.y + 0.5, floor=f.floor + 0.2, yaw=f.yaw + 12.0)
    saved = L.FRONTS
    L.FRONTS = tuple(moved if g is f else g for g in saved)
    try:
        scene.reset_scene()
        after, shift = world_points(), K.placement(moved) @ old.inverted()
    finally:
        L.FRONTS = saved
    assert after.keys() == before.keys()
    for name, pts in before.items():
        assert len(after[name]) == len(pts), name
        tree = KDTree(len(pts))
        for i, p in enumerate(after[name]):
            tree.insert(p, i)
        tree.balance()
        assert max(tree.find(shift @ p)[2] for p in pts) < 1e-4, name


def test_fronts_are_repeatable():
    def snapshot():
        scene.reset_scene()
        fronts.build()
        return {n: sorted(tuple(round(c, 6) for c in v.co) for v in bpy.data.objects[n].data.vertices)
                for n in ("ornate_bargeboard_knots", "lattice_window_window_bars", "round_window_west_window_frame")}
    assert snapshot() == snapshot()

import dataclasses
import math

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

from bagend import doorfront as DF, frontkit as K, hill, layout as L, scene


def first_hit(origin, target):
    dg = bpy.context.evaluated_depsgraph_get()
    o, t = Vector(origin), Vector(target)
    hit, _, _, _, obj, _ = bpy.context.scene.ray_cast(dg, o, (t - o).normalized())
    return obj.name if hit else None


def test_every_part_is_named_and_has_one_material():
    scene.reset_scene()
    objs = DF.build()
    assert len(objs) > 30
    for o in objs:
        assert o.name.startswith("doorfront_"), o.name
        assert len(o.data.materials) == 1, o.name
    assert not [o.name for o in bpy.data.objects if not o.name.startswith("doorfront_")]


def test_door_and_portholes_can_be_seen_with_the_hill_built():
    # The prototype's hill reached into the door's recess and hid its lower half.
    scene.reset_scene()
    hill.build()
    DF.build()
    for dz in (-0.6, 0.0, 0.6):
        z = DF.CZ + dz * DF.R_DOOR
        name = first_hit((0.1, -4.0, z), (0.1, 0.0, z))
        assert name and name.startswith("doorfront_door"), (dz, name)
    place = K.placement(L.front("door"))
    for s in (-1, 1):
        facet = place @ DF.side_matrix(s)
        centre = facet @ Vector((DF.S / 2, 0.0, DF.P_CZ))
        out = facet.to_3x3() @ Vector((0.0, -1.0, 0.0))
        name = first_hit(centre + 3.0 * out.normalized(), centre)
        assert name and "porthole" in name, (s, name)


def test_door_front_is_the_size_layout_says():
    # layout.py is the single source: the built front fills its dug-out and its eave is the layout's.
    scene.reset_scene()
    DF.build()
    door = L.front("door")
    xs = [(o.matrix_world @ v.co).x for n in ("doorfront_wall_left", "doorfront_wall_right")
          for o in [bpy.data.objects[n]] for v in o.data.vertices]
    for edge in (max(xs), -min(xs)):
        assert door.width / 2 - 0.1 <= edge <= door.width / 2, (edge, door.width / 2)
    fascia = bpy.data.objects["doorfront_fascia_centre"]
    top = max((fascia.matrix_world @ v.co).z for v in fascia.data.vertices)
    assert abs(top - (door.floor + door.eave + 0.01)) < 0.03, top


def test_nothing_but_the_door_shows_through_the_doorway():
    # Looking straight in around the rim of the doorway you see the door (or the lantern hanging in
    # front of it), never plaster: the side walls swing back behind the centre facet and must be
    # cut clear of the doorway too.
    scene.reset_scene()
    DF.build()
    r = DF.R_DOOR - 0.015
    for k in range(36):
        a = 2 * math.pi * k / 36
        u, z = r * math.cos(a), DF.CZ + r * math.sin(a)
        name = first_hit((u, -3.0, z), (u, 0.0, z))
        assert name and name.startswith(("doorfront_door", "doorfront_lantern")), (k, name)   # it hangs in front


def test_door_front_follows_its_layout_placement():
    # Every part, its boolean cut-outs included, must move with the front as one piece.
    def world_points():
        return {o.name: [o.matrix_world @ v.co for v in o.data.vertices] for o in DF.build()}

    scene.reset_scene()
    before, old = world_points(), K.placement(L.front("door"))
    door = L.front("door")
    moved = dataclasses.replace(door, x=door.x + 5.0, y=door.y + 1.0, floor=door.floor + 0.3, yaw=10.0)
    saved = L.FRONTS
    L.FRONTS = tuple(moved if f is door else f for f in saved)
    try:
        scene.reset_scene()
        after, shift = world_points(), K.placement(L.front("door")) @ old.inverted()
    finally:
        L.FRONTS = saved
    assert after.keys() == before.keys()
    for name, pts in before.items():
        assert len(after[name]) == len(pts), name
        tree = KDTree(len(pts))                 # vertex order may differ between builds; match by position
        for i, p in enumerate(after[name]):
            tree.insert(p, i)
        tree.balance()
        worst = max(tree.find(shift @ p)[2] for p in pts)
        assert worst < 1e-4, (name, worst)


def test_door_front_is_repeatable():
    def arch():
        scene.reset_scene()
        DF.build(seed=7)
        return [tuple(round(c, 6) for c in v.co) for v in bpy.data.objects["doorfront_door_arch"].data.vertices]
    assert arch() == arch()

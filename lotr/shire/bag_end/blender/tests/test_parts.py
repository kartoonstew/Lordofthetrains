import math
import random

import bmesh
import bpy
from mathutils import Vector

from bagend import parts as P, scene


def is_closed(obj):
    """Manifold, no holes, and normals pointing out (positive volume)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        return (all(e.is_manifold for e in bm.edges) and not any(e.is_boundary for e in bm.edges)
                and bm.calc_volume(signed=True) > 0)
    finally:
        bm.free()


def test_materials_are_made_once_per_scene():
    scene.reset_scene()
    first = P.materials()
    nodes = {name: len(m.node_tree.nodes) for name, m in first.items()}
    second = P.materials()
    assert {"plaster", "brick", "timber", "ring", "door", "glass", "stone", "turf"} <= set(first)
    assert all(first[k] is second[k] for k in first)
    assert nodes == {name: len(m.node_tree.nodes) for name, m in second.items()}


def test_plaster_comes_out_as_a_closed_solid():
    scene.reset_scene()
    bm = bmesh.new()
    P.plaster_slab(bm, -0.5, 0.5, 0.0, lambda u: 1.0 + 0.2 * math.cos(3 * u), 0.8, seed=2)
    assert is_closed(P.to_object("slab", bm, None, "test"))


def test_bevel_rounds_the_edges_of_solids_built_face_by_face():
    # Faces made with bm.faces.new carry no normals until updated; the bevel must still find edges.
    scene.reset_scene()
    counts = []
    for bevel in (0.0, 0.01):
        bm = bmesh.new()
        P.extrude(bm, [(0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2)], 0.0, 0.2)
        obj = P.to_object(f"prism_{bevel}", bm, None, "test", bevel=bevel)
        assert is_closed(obj), bevel
        counts.append(len(obj.data.vertices))
    assert counts[1] > counts[0], counts


def test_plaster_meets_its_eave_line_and_bulges_only_outward():
    def top(u):
        return 1.0 + 0.2 * math.cos(3 * u)
    bm = bmesh.new()
    P.plaster_slab(bm, -0.5, 0.5, 0.0, top, 0.8, seed=2, amp=0.012)
    for v in bm.verts:
        assert v.co.z <= top(v.co.x) + 1e-6
        assert -0.012 - 1e-6 <= v.co.y <= 0.8 + 1e-6
    assert sum(abs(v.co.z - top(v.co.x)) < 1e-6 for v in bm.verts) >= 2 * 34   # whole top row
    bm.free()


def test_arch_bricks_sit_between_the_circles_and_thicken_at_the_crown():
    r_in, r_out, lift = 0.87, 0.98, 0.10
    bm = bmesh.new()
    P.crescent_bricks(bm, 0.0, 0.0, r_in, r_out, lift, 0.065, -0.4, random.Random(1))
    radial = [(math.hypot(v.co.x, v.co.z), v.co.z) for v in bm.verts]
    assert radial
    assert min(r for r, _ in radial) >= r_in - 0.01
    assert max(r for r, _ in radial) <= r_out + lift + 0.01
    crown = max(r for r, z in radial if z > 0.9 * r)
    side = max(r for r, z in radial if abs(z) < 0.1 * r)
    assert crown - side > 0.05, (crown, side)
    assert min(z for _, z in radial) >= -0.4 - 1e-9
    bm.free()


def test_glazing_bars_stay_inside_their_pane():
    cu, cz, r, v = 0.3, 1.2, 0.4, 0.06
    for bars in (P.lattice_bars, P.wheel_bars):
        bm = bmesh.new()
        bars(bm, cu, cz, r, v)
        assert len(bm.verts) > 0, bars.__name__
        for p in bm.verts:
            assert math.hypot(p.co.x - cu, p.co.z - cz) <= r + 0.03, (bars.__name__, tuple(p.co))
            assert abs(p.co.y - v) <= 0.02 + 1e-6, (bars.__name__, tuple(p.co))
        bm.free()


def test_bake_cuts_makes_a_real_hole_and_removes_the_cutters():
    scene.reset_scene()
    bm = bmesh.new()
    P.box(bm, (0.0, 0.4, 1.0), (2.0, 0.8, 2.0))
    slab = P.to_object("slab", bm, None, "test")
    P.bake_cuts(slab, [P.cylinder_cutter(0.0, 1.0, 0.3, -0.5, 1.5, "test")])
    assert not slab.modifiers and slab.data.name == "slab"
    assert [o.name for o in bpy.data.objects] == ["slab"]
    assert not [m.name for m in bpy.data.meshes if m.name.startswith("cutter")]
    dg = bpy.context.evaluated_depsgraph_get()
    through, *_ = bpy.context.scene.ray_cast(dg, Vector((0.0, -1.0, 1.0)), Vector((0.0, 1.0, 0.0)))
    beside, *_ = bpy.context.scene.ray_cast(dg, Vector((0.6, -1.0, 1.0)), Vector((0.0, 1.0, 0.0)))
    assert not through and beside


def test_rough_materials_vary_across_a_surface():
    # Plaster, stone, turf and soil vary in soft patches, so they don't render as flat toy colours.
    scene.reset_scene()
    m = P.materials()
    assert {"soil", "bark", "leaves"} <= set(m)
    for name in ("plaster", "stone", "turf", "soil"):
        kinds = {n.type for n in m[name].node_tree.nodes}
        colour = m[name].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        assert "TEX_NOISE" in kinds and colour.is_linked, name

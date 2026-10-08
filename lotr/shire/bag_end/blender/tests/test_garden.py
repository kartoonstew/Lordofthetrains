import bmesh
import bpy

from bagend import garden, layout as L, scene, terrain


def test_chimneys_sit_in_the_turf_and_stand_proud():
    scene.reset_scene()
    garden.build()
    for k, (x, y) in enumerate(L.CHIMNEYS):
        zs = [v.co.z for v in bpy.data.objects[f"chimney_{k}"].data.vertices]
        ground = float(terrain.ground(x, y))
        assert min(zs) < ground - 0.3
        assert max(zs) >= ground + L.CHIMNEY_HEIGHT - 0.01


def test_every_step_slab_top_is_its_tread_height():
    scene.reset_scene()
    garden.build()
    for k, (_, _, z) in enumerate(L.STEPS):
        zs = [v.co.z for v in bpy.data.objects[f"step_{k}"].data.vertices]
        assert z - 0.01 <= max(zs) <= z + 1e-6, k                # worn slate: its top dips a little


def test_dry_stone_wall_stops_short_of_the_thin_edges():
    # Its stones may lean a few centimetres into the edge fall, never beyond it.
    scene.reset_scene()
    garden.build()
    xs = [v.co.x for n in ("wall_west", "wall_east") for v in bpy.data.objects[n].data.vertices]
    assert min(xs) >= L.MODEL_X[0] + L.EDGE_FALL - 0.1, min(xs)
    assert max(xs) <= L.MODEL_X[1] - L.EDGE_FALL + 0.1, max(xs)


def test_garden_parts_are_closed_solids_standing_on_the_ground():
    scene.reset_scene()
    garden.build()
    for coll in ("garden", "props"):
        for o in bpy.data.collections[coll].objects:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            try:
                assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True) > 0, o.name
            finally:
                bm.free()
            low = min((o.matrix_world @ v.co).z for v in o.data.vertices)
            x, y = o.matrix_world.translation.x, o.matrix_world.translation.y
            hung = o.name.endswith(("_sign", "_lantern", "_glass"))   # these hang from a post or the gate
            if coll == "props" and not hung:                       # the rest are planted, not floating
                assert low <= float(terrain.ground(x, y)) + 0.01, (o.name, low)


def test_the_oak_is_a_preview_with_a_trunk_and_a_crown():
    scene.reset_scene()
    garden.build()
    names = {o.name for o in bpy.data.collections["preview"].objects}
    assert {"oak_trunk", "oak_crown"} <= names, names


def islands(obj):
    """How many separate pieces a mesh is made of."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    seen, count = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        count += 1
        stack = [v]
        while stack:
            w = stack.pop()
            if w.index in seen:
                continue
            seen.add(w.index)
            stack.extend(e.other_vert(w) for e in w.link_edges)
    bm.free()
    return count


def test_garden_is_built_in_detail():
    # Stone by stone and slab by slab, not plain blocks: refs/04, 05, 07.
    scene.reset_scene()
    garden.build()
    names = {o.name for o in bpy.data.objects}
    for k in range(len(L.CHIMNEYS)):
        assert {f"chimney_{k}", f"chimney_cap_{k}", f"chimney_pot_{k}"} <= names, k
    assert {f"bed_{k}" for k in range(len(L.BEDS))} <= names
    assert islands(bpy.data.objects["wall_west"]) > 40           # a core and its stones
    assert len(bpy.data.objects["step_0"].data.vertices) > 8      # an irregular slate, not a box
    assert islands(bpy.data.objects["chimney_0"]) > 20            # laid brick by brick

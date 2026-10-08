import bpy
from mathutils import Vector

from bagend import parts, render, scene

CUBE = ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
        [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])


def test_every_reference_camera_is_created_with_its_lens():
    scene.reset_scene()
    render.setup()
    assert {"ref01", "ref02", "ref03", "ref09", "ref10"} <= set(render.CAMERAS)
    for name, (_, _, lens) in render.CAMERAS.items():
        cam = bpy.data.objects[name]
        assert cam.type == "CAMERA" and cam.data.lens == lens


def test_cameras_see_the_whole_hill():
    scene.reset_scene()
    render.setup()
    for name, (loc, target, _) in render.CAMERAS.items():
        reach = (Vector(target) - Vector(loc)).length + 40.0
        assert bpy.data.objects[name].data.clip_end >= reach, name


def test_paint_gives_each_mesh_one_material_by_name_prefix():
    scene.reset_scene()
    for name in ("chimney_cap_0", "oak_crown", "bench"):
        scene.add_mesh_object(name, *CUBE, "test")
    render.paint()
    got = {o.name: [m.name for m in o.data.materials] for o in bpy.data.objects}
    assert got == {"chimney_cap_0": ["plain_chimney"], "oak_crown": ["plain_oak_crown"], "bench": ["plain_timber"]}, got


def test_setup_makes_the_overview_the_active_camera():
    scene.reset_scene()
    render.setup()
    assert bpy.context.scene.camera is bpy.data.objects["overview"]


def test_paint_leaves_detailed_parts_their_own_materials():
    scene.reset_scene()
    obj = scene.add_mesh_object("doorfront_wall_centre", *CUBE, "test")
    obj.data.materials.append(bpy.data.materials.new("plaster"))
    render.paint()
    assert [m.name for m in obj.data.materials] == ["plaster"]


def test_light_is_a_sky_rendered_in_plain_colours():
    scene.reset_scene()
    render.setup()
    s = bpy.context.scene
    nodes = s.world.node_tree.nodes
    assert any(n.type == "TEX_SKY" for n in nodes)
    assert nodes["Background"].inputs["Color"].is_linked
    assert s.view_settings.view_transform == "Standard"


def test_paint_never_reuses_a_detailed_part_material():
    # Garden props fall back to plain timber; the door front's "timber" must stay its own.
    scene.reset_scene()
    detailed = parts.materials()["timber"]
    bench = scene.add_mesh_object("bench", *CUBE, "test")
    render.paint()
    assert bench.data.materials[0] is not detailed
    assert detailed.node_tree.nodes["Principled BSDF"].inputs["Base Color"].is_linked

import bpy

from bagend import scene


def test_blender_is_5_or_newer():
    assert bpy.app.version >= (5, 0, 0), bpy.app.version_string


def test_reset_scene_is_empty_and_metric():
    s = scene.reset_scene()
    assert s.unit_settings.system == "METRIC"
    assert s.unit_settings.scale_length == 1.0
    assert len(bpy.data.objects) == 0


def test_add_mesh_object_points_normals_outward():
    scene.reset_scene()
    verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    obj = scene.add_mesh_object("cube", verts, faces, "test")
    top = max(obj.data.polygons, key=lambda p: p.center.z)
    assert top.normal.z > 0.99
    bottom = min(obj.data.polygons, key=lambda p: p.center.z)
    assert bottom.normal.z < -0.99
    assert obj.users_collection[0].name == "test"

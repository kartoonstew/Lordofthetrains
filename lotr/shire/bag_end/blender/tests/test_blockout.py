import bpy

from bagend import blockout, layout as L, scene


def test_every_front_has_wall_and_eave_at_its_layout_position():
    scene.reset_scene()
    blockout.build()
    for f in L.FRONTS:
        wall = bpy.data.objects[f"front_{f.name}"]
        assert bpy.data.objects.get(f"eave_{f.name}") is not None, f.name
        xs = [(wall.matrix_world @ v.co).x for v in wall.data.vertices]
        assert abs((min(xs) + max(xs)) / 2 - f.x) < 0.1, f.name


def test_fronts_built_in_detail_are_left_out():
    scene.reset_scene()
    blockout.build(exclude=("door",))
    names = [o.name for o in bpy.data.objects]
    assert not [n for n in names if "door" in n], names
    assert "front_ornate" in names and "window_lattice_window_+0" in names

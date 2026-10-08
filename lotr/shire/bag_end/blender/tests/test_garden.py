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
        assert abs(max(zs) - z) < 1e-6, k


def test_dry_stone_wall_stops_short_of_the_thin_edges():
    scene.reset_scene()
    garden.build()
    xs = [v.co.x for n in ("wall_west", "wall_east") for v in bpy.data.objects[n].data.vertices]
    assert min(xs) >= L.MODEL_X[0] + L.EDGE_FALL - 1e-6, min(xs)
    assert max(xs) <= L.MODEL_X[1] - L.EDGE_FALL + 1e-6, max(xs)

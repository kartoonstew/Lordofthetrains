import bmesh

from bagend import hill, layout as L, scene, terrain


def test_hill_mesh_is_watertight():
    scene.reset_scene()
    obj = hill.build()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        assert all(e.is_manifold for e in bm.edges)
        assert not any(e.is_boundary for e in bm.edges)
    finally:
        bm.free()


def test_hill_top_follows_the_ground_function():
    scene.reset_scene()
    obj = hill.build()
    top = [v.co for v in obj.data.vertices if v.co.z > L.BASE_Z + 0.01]
    assert top
    for co in top[:: max(1, len(top) // 200)]:
        assert abs(co.z - float(terrain.ground(co.x, co.y))) < 1e-4


def test_hill_covers_the_model_footprint_exactly():
    scene.reset_scene()
    obj = hill.build()
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    assert abs(min(xs) - L.MODEL_X[0]) < 1e-4 and abs(max(xs) - L.MODEL_X[1]) < 1e-4, (min(xs), max(xs))
    assert abs(min(ys) - L.LANE_Y) < 1e-4 and abs(max(ys) - L.BACK_Y) < 1e-4, (min(ys), max(ys))


def test_hill_is_about_17_by_12_cm_at_ho_and_under_8_cm_tall():
    scene.reset_scene()
    obj = hill.build()
    size = [(max(v.co[i] for v in obj.data.vertices) - min(v.co[i] for v in obj.data.vertices)) * 1000 / 87
            for i in range(3)]
    assert 150 <= size[0] <= 185 and 110 <= size[1] <= 135 and size[2] < 80, size


def test_no_mesh_cell_slopes_in_front_of_a_facade():
    # The hill's last dug grid row must lie behind every facade, inside the wall mass.
    for f in L.FRONTS:
        for u in (-0.4 * f.width, 0.0, 0.4 * f.width):
            x, y = L.to_world(f, u, float(L.facade_v(f, u)) + hill.STEP + 0.01)
            assert float(terrain.ground(x, y)) <= f.floor + 0.05, (f.name, u)


def test_hill_is_shaded_smooth():
    scene.reset_scene()
    obj = hill.build()
    assert all(p.use_smooth for p in obj.data.polygons)

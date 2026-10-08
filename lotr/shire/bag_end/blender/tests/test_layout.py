import math

import numpy as np

from bagend import layout as L


def test_fronts_run_left_to_right_without_overlapping():
    for a, b in zip(L.FRONTS, L.FRONTS[1:]):
        assert a.x + a.width / 2 < b.x - b.width / 2, (a.name, b.name)


def test_door_front_matches_refs_01_and_02():
    door = L.front("door")
    assert abs(door.width / L.D - 2.08) < 0.01        # outside to outside of the outer posts
    assert abs(door.eave / L.D - 1.39) < 0.01


def test_eave_line_of_a_faceted_front():
    # The door front's eave arches over its centre facet, then falls along the side facets.
    door = L.front("door")
    assert abs(L.eave_top(door, 0.0) - door.eave) < 1e-9
    assert abs(L.eave_top(door, door.centre) - door.eave_post) < 1e-9
    assert abs(L.eave_top(door, -door.width / 2) - door.eave_ends) < 1e-9
    us = np.linspace(-door.width / 2, door.width / 2, 41)
    tops = L.eave_top(door, us)
    assert tops.shape == us.shape and np.all(np.diff(tops[20:]) <= 1e-12)    # never rises outward


def test_row_leaves_room_for_the_end_banks():
    first, last = L.FRONTS[0], L.FRONTS[-1]
    left, right = first.x - first.width / 2, last.x + last.width / 2
    assert 24.0 < right - left < 26.5, right - left
    assert left - L.MODEL_X[0] >= 1.2 and L.MODEL_X[1] - right >= 1.2, (left, right)


def test_model_is_about_30_by_18_cm_at_ho():
    width_mm = (L.MODEL_X[1] - L.MODEL_X[0]) * 1000 / 87
    depth_mm = (L.BACK_Y - L.LANE_Y) * 1000 / 87
    assert 300 <= width_mm <= 330, width_mm
    assert 170 <= depth_mm <= 200, depth_mm


def test_facade_recedes_only_beyond_the_centre_facet():
    door = L.front("door")
    assert L.facade_v(door, 0.0) == 0.0 and L.facade_v(door, -door.centre) == 0.0
    for u in (door.centre + 1.0, -door.centre - 1.0):
        assert abs(L.facade_v(door, u) - math.tan(math.radians(door.wing_angle))) < 1e-9
    us = np.linspace(-2.0, 2.0, 9)
    assert L.facade_v(door, us).shape == us.shape
    assert np.allclose(L.facade_v(L.front("ornate"), us), 0.0)


def test_hill_top_items_stand_on_the_model_away_from_its_thin_edges():
    for x, y in L.CHIMNEYS + (L.OAK,):
        assert y > 2.0, (x, y)
        assert L.MODEL_X[0] + L.EDGE_FALL < x < L.MODEL_X[1] - L.EDGE_FALL, (x, y)
        assert y < L.BACK_Y - L.EDGE_FALL, (x, y)


def test_steps_descend_from_door_to_gate():
    zs = [z for _, _, z in L.STEPS]
    assert zs[0] == L.TERRACE_Z
    assert all(a > b for a, b in zip(zs, zs[1:]))

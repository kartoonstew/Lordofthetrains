import numpy as np

from bagend import layout as L, terrain


def g(x, y):
    return float(terrain.ground(x, y))


def test_door_landing_is_level():
    for u in (-0.6, 0.0, 0.6):
        assert abs(g(u, -0.8) - L.TERRACE_Z) < 0.05, u


def test_turf_comes_down_onto_every_front():
    # Over the back of each wall mass the ground meets the turf on the eave (within the soft blend),
    # and behind it the hill climbs on: no bare eave, and no cliff of hill standing behind the front.
    for f in L.FRONTS:
        for u in np.linspace(-0.95 * f.width / 2, 0.95 * f.width / 2, 9):
            turf = f.floor + L.eave_top(f, u) + L.SOD
            fv = float(L.facade_v(f, u))
            over = g(*L.to_world(f, u, fv + L.WALL_DEPTH - 0.05))
            behind = g(*L.to_world(f, u, fv + L.WALL_DEPTH + 0.6))
            assert turf - 0.35 <= over <= turf + 0.01, (f.name, round(u, 2), over, turf)
            assert behind >= over - 0.05, (f.name, round(u, 2), behind, over)


def test_turf_covers_the_ends_of_every_wall_mass():
    # Beside a front, behind its facade line, the bank stands at the turf on its eave ends: no slot.
    # A side facet's wall ends square to the facet, so behind the outer post the ground is turf too.
    for f in L.FRONTS:
        lip = f.floor + f.eave_ends + L.SOD
        for s in (-1, 1):
            for u, vs in ((s * (f.width / 2 + 0.05), np.arange(0.1, L.WALL_DEPTH, 0.1)),
                          (s * (f.width / 2 - 0.03), (0.2, 0.4) if f.centre else ())):
                for v in vs:
                    z = g(*L.to_world(f, u, float(L.facade_v(f, u)) + v))
                    assert z >= lip - 0.35, (f.name, round(u, 2), round(v, 1), z, lip)


def test_no_cliffs_around_the_fronts():
    # Behind and beside every front, outside all wall masses and the model's falling edges, the
    # turf never rises more than 1 m within 0.1 m (M2's first build had 3 m steps there).
    for f in L.FRONTS:
        us = np.arange(-f.width / 2 - 1.5, f.width / 2 + 1.5 + 1e-9, 0.1)
        vs = np.arange(0.05, 2.5 + 1e-9, 0.1)                       # just behind the facade line on
        uu, vv = np.meshgrid(us, vs)
        a = np.radians(f.yaw)
        back = vv + L.facade_v(f, uu)
        x = f.x + uu * np.cos(a) - back * np.sin(a)
        y = f.y + uu * np.sin(a) + back * np.cos(a)
        z = terrain.ground(x, y)
        keep = (x > L.MODEL_X[0] + L.EDGE_FALL) & (x < L.MODEL_X[1] - L.EDGE_FALL)
        for h in L.FRONTS:
            b = np.radians(h.yaw)
            hu = (x - h.x) * np.cos(b) + (y - h.y) * np.sin(b)
            hv = -(x - h.x) * np.sin(b) + (y - h.y) * np.cos(b) - L.facade_v(h, hu)
            keep &= ~((np.abs(hu) <= h.width / 2) & (hv >= -0.05) & (hv <= L.WALL_DEPTH))
        rise_u = np.abs(np.diff(z, axis=1))[keep[:, 1:] & keep[:, :-1]]
        rise_v = np.abs(np.diff(z, axis=0))[keep[1:, :] & keep[:-1, :]]
        assert max(rise_u.max(), rise_v.max()) < 1.0, (f.name, rise_u.max(), rise_v.max())


def test_ground_is_dug_out_in_front_of_every_front():
    for f in L.FRONTS:
        for u in np.linspace(-0.95 * f.width / 2, 0.95 * f.width / 2, 7):
            x, y = L.to_world(f, u, float(L.facade_v(f, u)) - 0.05)
            assert g(x, y) <= f.floor + 0.05, (f.name, round(u, 2), g(x, y))


def test_door_front_is_dug_out_to_its_recess_depth():
    # The door sits 0.22 m back in its ring, across the centre facet; the hill must not reach into it.
    door = L.front("door")
    for u in np.linspace(-door.centre, door.centre, 7):
        x, y = L.to_world(door, u, float(L.facade_v(door, u)) + door.dig_behind - 0.05)
        assert g(x, y) <= door.floor + 0.05, (round(u, 2), g(x, y))


def test_terrace_path_stays_level_along_the_row():
    # A dug-out's floor meeting the level path is no crease: blending must not sink the path. Only the
    # bank the stone steps are set into dips from it, and that within 2.05 m of the steps' centreline
    # (0.72 m of turf level with the tread ends, then at most 0.9 m down at L.BANK, plus its shoulders).
    for y in (-3.4, -2.5, -1.7):
        for x in np.linspace(L.MODEL_X[0] + L.EDGE_FALL, L.MODEL_X[1] - L.EDGE_FALL, 200):
            s, d = terrain.path_frame(np.array([x]), np.array([y]))
            if s[0] > -0.3 and abs(d[0]) < 2.05:
                continue
            assert abs(g(x, y) - L.TERRACE_Z) < 0.01, (round(x, 2), y, g(x, y))


def test_smin_rounds_only_near_crossings():
    a = np.zeros(4)
    b = np.array([2.0, 0.2, 0.0, np.inf])
    z = terrain.smin(a, b, 0.5)
    assert z[0] == 0.0 and z[3] == 0.0           # far apart, or dug-out not reaching: plain minimum
    assert z[2] == -0.125 and -0.125 < z[1] < 0.0  # near a crossing: rounded, by at most k / 4
    assert np.all(z <= np.minimum(a, b))


def test_hill_climbs_to_its_top_behind_the_fronts():
    door = L.front("door")
    top = g(*L.OAK)
    assert top >= L.DOME_TOP - 0.3, top
    assert top > door.floor + door.eave + 1.0, top          # refs/03: well above the door's eave


def test_sides_and_back_fall_to_a_thin_edge():
    for y in np.linspace(L.LANE_Y, L.BACK_Y, 9):
        for x in L.MODEL_X:
            assert abs(g(x, y) - L.EDGE_Z) < 1e-9, (x, y, g(x, y))
    for x in np.linspace(*L.MODEL_X, 9):
        assert abs(g(x, L.BACK_Y) - L.EDGE_Z) < 1e-9, (x, g(x, L.BACK_Y))
    assert (L.EDGE_Z - L.BASE_Z) * 1000 / 87 < 4.0           # the edge is under 4 mm thick at HO


def test_no_step_is_buried():
    for x, y, z in L.STEPS:
        assert g(x, y) <= z + 0.01, (x, y, z, g(x, y))


def test_lawn_falls_from_the_wall_to_the_lane():
    assert abs(g(-3.0, L.WALL_Y - 0.01) - L.LAWN_Z) < 0.05
    assert abs(g(-3.0, L.LANE_Y) - L.LANE_Z) < 0.05


def test_the_bank_meets_the_tread_ends_with_no_trench():
    # refs/04, 05: the treads are set into an open grassy bank. At each tread's ends the turf is at
    # about tread height (between the tread's top and the next tread's), and from there outward, up to
    # the dry-stone wall, it climbs steadily to the terrace or falls to the lawn: no ditch beside the
    # steps, and no slope steeper than 50 degrees.
    pts = terrain.path_line()
    zs = [z for _, _, z in L.STEPS]
    for k, (x, y, z) in enumerate(L.STEPS):
        u = pts[k + 1] - pts[k]
        v = np.array([-u[1], u[0]]) / np.linalg.norm(u)
        below = zs[k + 1] if k + 1 < len(zs) else z - 0.1
        profiles = 0
        for side in (-1, 1):
            end = g(x + side * v[0] * 0.68, y + side * v[1] * 0.68)
            assert below - 0.03 <= end <= z, (k, side, end, z)
            offs = [o for o in np.arange(0.68, 2.4, 0.05)        # up to the wall, whose drop isn't the bank
                    if (y + side * v[1] * o - L.WALL_Y) * (y - L.WALL_Y) > 0 and abs(y + side * v[1] * o - L.WALL_Y) > 0.1]
            if len(offs) < 4:
                continue                                      # the tread in the wall's gap
            prof = np.array([g(x + side * v[0] * o, y + side * v[1] * o) for o in offs])
            step = np.diff(prof)
            assert np.all(step >= -0.01) or np.all(step <= 0.01), (k, side, np.round(prof, 2))
            assert np.abs(step).max() / 0.05 <= np.tan(np.radians(50)), (k, side, np.abs(step).max())
            profiles += 1
        assert profiles >= 1 or abs(y - L.WALL_Y) < 0.3, k

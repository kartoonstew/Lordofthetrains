"""Ground height as a function of plan position, vectorised over numpy arrays."""
import numpy as np

from . import layout as L


def ease(t):
    t = np.clip(t, 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * t)


def ramp(v, a, b):
    return ease((v - a) / (b - a))


def smin(a, b, k):
    """Minimum with the crease rounded over about k, so banks meet in soft hollows, not sharp V's."""
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k / 4


# The turf's lumps: a few long gentle waves and some short ones, crossing at odd angles, so the
# hill reads as grown rather than modelled. (amplitude m, wavelength m, direction °, phase)
_waves = np.random.default_rng(7)
LUMPS = tuple((0.04, wl, d, p) for wl, d, p in zip(_waves.uniform(2.5, 5.0, 5), _waves.uniform(0, 180, 5),
                                                     _waves.uniform(0, 2 * np.pi, 5))) + \
        tuple((0.012, wl, d, p) for wl, d, p in zip(_waves.uniform(0.8, 1.4, 8), _waves.uniform(0, 180, 8),
                                                      _waves.uniform(0, 2 * np.pi, 8)))


def lumps(x, y):
    """Gentle irregular undulation for the turf, about ±0.1 m."""
    z = 0.0 * x
    for amp, wl, deg, phase in LUMPS:
        a = np.radians(deg)
        z = z + amp * np.sin(2 * np.pi / wl * (x * np.cos(a) + y * np.sin(a)) + phase)
    return z


def garden(x, y):
    """Lane and lawn in front, the dry-stone wall, then the terrace path along the fronts."""
    lawn = L.LANE_Z + (L.LAWN_Z - L.LANE_Z) * ramp(y, L.LANE_Y, L.WALL_Y)
    return np.where(y < L.WALL_Y, lawn, L.TERRACE_Z) + 0.0 * x


def hill(x, y):
    """The Hill, refs/03: a rounded dome over the fronts, flat-topped, with a bank in front over the
    fronts and any swells layout.py adds. At its ends and back it falls steeply to the model's thin
    edge (3-4.6 m within the last 1 m)."""
    cx, cy = L.DOME_CENTRE
    ax, ay = L.DOME_RADII
    r = np.sqrt(((x - cx) / ax) ** 2 + ((y - cy) / ay) ** 2)
    dome = np.clip(1.0 - r ** L.DOME_POWER, 0.0, None)
    swell = 0.0 * x
    for sx, sh, sw in L.SWELLS:
        swell = swell + sh * np.exp(-(((x - sx) / sw) ** 2))
    height = (L.CREST_Z + (L.DOME_TOP - L.CREST_Z) * ramp(y, L.CREST_Y, L.DOME_CENTRE[1] + 0.8) + swell) * dome
    front = ramp(y, L.CREST_Y - 2.2, L.CREST_Y)
    h = height * front
    return h + lumps(x, y) * ramp(h, 0.0, 1.0)      # lumps only where the hill has risen


BACK_SLOPE = 62.0   # degrees: the turf climbs from a front's eave back into the hill
TUCK = 0.03         # the hill passes this far under each front's sod, so the sod shows, not the hill


def dig(f, x, y):
    """Ground dug out for a front: its floor in front, grass banks either side, turf over the top.

    In front of the facade the floor runs straight ahead, and beside it the bank stands as high as
    the turf on the eave ends, sloping down toward the garden (refs/01, 03). Behind the facade the
    floor runs on f.dig_behind, clear of the door recess and more than one hill grid cell (hill.STEP
    = 0.15), so the mesh's sloped cell lands inside the wall mass. Over the wall mass the ground
    comes down to the turf on the eave, and behind it climbs back into the hill at BACK_SLOPE, so
    the turf rolls down onto the front instead of standing behind it as a cliff.
    """
    a = np.radians(f.yaw)
    dx, dy = x - f.x, y - f.y
    u = dx * np.cos(a) + dy * np.sin(a)
    v = -dx * np.sin(a) + dy * np.cos(a) - L.facade_v(f, u)
    du = np.maximum(0.0, np.abs(u) - f.width / 2)
    inside = du == 0.0                   # behind the facade, within the front's wall mass
    ue = np.abs(u)                       # where along the front the sod above this point sits...
    deep = v                             # ...and how far behind the facade, square to it
    if f.centre:                         # a side facet's wall ends square to the facet, not to the row
        w = np.radians(f.wing_angle)
        side = ue > f.centre
        along = (ue - f.centre) * np.cos(w) + (v + L.facade_v(f, u)) * np.sin(w)
        inside &= along <= (f.width / 2 - f.centre) / np.cos(w) - L.POST / 2
        ue = np.where(side, f.centre + along * np.cos(w), ue)
        deep = np.where(side, v * np.cos(w), v)
    sod = L.eave_top(f, ue)
    lip = f.eave_ends + L.SOD
    cheek = lip * ramp(du, 0.0, 0.25) * ramp(v, -lip / np.tan(np.radians(60)), 0.0)   # meets the turf at the facade
    bank = f.floor + np.tan(np.radians(50)) * du + cheek
    turf = (f.floor + sod + L.SOD - TUCK
            + np.maximum(0.0, deep - L.WALL_DEPTH) * np.tan(np.radians(BACK_SLOPE)))
    behind = np.where(inside & (v < f.dig_behind), f.floor, np.maximum(bank, turf))
    return np.where(v < 0.0, bank, behind)


def edge(x, y):
    """1 inside the model, easing to 0 at its sides and back, where the ground falls to a thin edge."""
    return (ramp(x, L.MODEL_X[0], L.MODEL_X[0] + L.EDGE_FALL) * ramp(L.MODEL_X[1] - x, 0.0, L.EDGE_FALL)
            * ramp(L.BACK_Y - y, 0.0, L.EDGE_FALL))


def path_line():
    """The path's centreline in plan: through the middle of every tread, on to the gate."""
    return np.array([(x, y) for x, y, _ in L.STEPS] + [L.GATE])


def path_frame(x, y):
    """Where (x, y) is relative to the path: chainage s along its centreline from the top tread, and
    signed offset d from it (positive to the right going down). Before the top tread s is negative:
    the distance behind it along the first stretch's line, and d the offset from that line."""
    pts = path_line()
    seg = np.diff(pts, axis=0)
    length = np.hypot(seg[:, 0], seg[:, 1])
    start = np.concatenate([[0.0], np.cumsum(length)])
    best = np.full(np.shape(x), np.inf)
    s = np.zeros(np.shape(x))
    d = np.zeros(np.shape(x))
    for k, ((x0, y0), (sx, sy), n) in enumerate(zip(pts[:-1], seg, length)):
        raw = ((x - x0) * sx + (y - y0) * sy) / (n * n)
        dist = np.hypot(x - (x0 + np.clip(raw, 0.0, 1.0) * sx), y - (y0 + np.clip(raw, 0.0, 1.0) * sy))
        closer = dist < best
        best = np.where(closer, dist, best)
        t = np.minimum(raw, 1.0) if k == 0 else np.clip(raw, 0.0, 1.0)     # the first runs on back
        px, py = x - (x0 + t * sx), y - (y0 + t * sy)
        s = np.where(closer, start[k] + t * n, s)
        d = np.where(closer, -np.sign(sx * py - sy * px) * np.hypot(px, py), d)
    return s, d


def tread_chainage():
    """Chainage of every tread's middle and of its front edge (where the next tread's going starts)."""
    pts = path_line()
    start = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    mid = start[:-1]
    front = mid + 0.5 * np.diff(start)
    return mid, front


TREAD_ENDS = 0.72     # the bank's turf runs level with the path this far either side of its centre


def bank_level(s):
    """The turf's height along the path at chainage s, where it meets the tread ends: a steady slope
    from the back of each tread's going (level with it) down to its front (level with the next), so
    the treads are set into the bank, their ends showing more of their thickness toward the front."""
    mid, front = tread_chainage()
    zs = [z for _, _, z in L.STEPS]
    ss = [mid[0] - 0.2] + list(front[:-1]) + [front[-1] + 0.05]
    hs = [zs[0]] + zs[1:] + [zs[-1] - 0.06]
    return np.interp(s, ss, np.array(hs) - 0.015)


def path_bank(x, y, z):
    """The open grassy bank the path is set into (refs/04, 05): beside the treads the turf is at
    bank_level, and beyond them it climbs to the terrace, or falls to the lawn, at the slope L.BANK
    with rounded shoulders; past the last tread it eases back to the lawn before the gate."""
    s, d = path_frame(x, y)
    level = bank_level(s)
    k = 0.12                                             # how far the shoulders are rounded
    off = np.abs(d) - TREAD_ENDS
    run = np.where(off > k, off, np.where(off < -k, 0.0, (off + k) ** 2 / (4 * k)))    # a soft start
    rise = np.abs(z - level)
    h = np.maximum(smin(run * L.BANK, rise, k), 0.0)    # a soft finish at the ground beyond
    bank = level + np.sign(z - level) * h
    _, front = tread_chainage()
    gate = float(np.sum(np.hypot(*np.diff(path_line(), axis=0).T)))
    f = 1.0 - ease((s - front[-1] - 0.05) / max(0.05, gate - front[-1] - 0.1))
    f = f * (1.0 - ease(-s / 0.25))                     # and behind the top tread, back to the landing
    return z + (bank - z) * f


BLEND = 0.8   # how softly each dug-out meets the hill and the next one


def ground(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = garden(x, y) + hill(x, y)       # the hill rises from the terrace; it is zero over the lawn
    for f in L.FRONTS:
        d = dig(f, x, y)
        # Round the crease where a dug-out cuts into the hill, but never below the front's floor:
        # where the dug floor meets level ground (the terrace path) there is no crease to round.
        z = np.maximum(smin(z, d, BLEND), np.minimum(np.minimum(z, d), f.floor))
    z = path_bank(x, y, z)
    z = L.EDGE_Z + (z - L.EDGE_Z) * edge(x, y)
    return np.maximum(z, L.EDGE_Z)

"""The four fronts other than the door front, in rustic detail, built with frontkit and parts.

- round_window_west, round_window_rack: small fronts with an arched eave and one round window
  with wheel glazing (refs/09, 10).
- lattice_window: the round window with a square lattice in a heavy timber ring (refs/03, 05).
- ornate: the big front with the carved arched bargeboard, half-timbering and a tall arched
  leaded window, plus a small round window on its left wing (refs/08, 09).
"""
import math

import bmesh
from mathutils import Matrix

from . import frontkit as K, layout as L, parts as P

D = L.D

# Round windows: (u, centre height above the front's floor, radius to the outside of the frame),
# refs/03, 05, 08-10. The ornate front's is the small one on its left wing.
ROUND_WINDOWS = {
    "round_window_west": (0.0, 0.70 * D, 0.20 * D),
    "round_window_rack": (0.0, 0.72 * D, 0.22 * D),
    "lattice_window": (0.0, 0.87, 0.30 * D),
    "ornate": (-1.9 * D, 0.90 * D, 0.17 * D),
}
# The ornate front's tall arched window, refs/08: half-width, sill height, height
ARCHED_WINDOW = (0.6 * D, 0.55 * D, 0.95 * D)


def round_window_front(name, seed):
    f = L.front(name)
    b = K.Builder(f, seed=seed)
    cut = K.round_window(b, "window", *ROUND_WINDOWS[name], glazing="wheel", frame_mat="timber")
    K.wall(b, [cut])
    K.eave(b, panels=((0.0, f.width / 2),))
    return b.objects()


def lattice_front(seed=13):
    f = L.front("lattice_window")
    b = K.Builder(f, seed=seed)
    cut = K.round_window(b, "window", *ROUND_WINDOWS[f.name], frame=0.09, glazing="grid", frame_mat="timber")
    K.wall(b, [cut])
    K.eave(b, panels=((0.0, f.width / 2),))
    return b.objects()


def arched_outline(half, z0, spring, n=24, grow=0.0):
    """A round-headed opening: straight jambs from z0 to spring, a semicircle over them."""
    r = half + grow
    pts = [(-r, z0 - grow), (r, z0 - grow)]
    pts += [(r * math.cos(math.pi * k / n), spring + r * math.sin(math.pi * k / n)) for k in range(n + 1)]
    return pts


def ornate_front(seed=17):
    f = L.front("ornate")
    b = K.Builder(f, seed=seed)
    half, arch = f.width / 2, f.arch
    top = K.eave_line(f)
    w_half, w_z0, w_height = ARCHED_WINDOW
    spring = w_z0 + w_height - w_half
    cut = b.outline_cutter(arched_outline(w_half, w_z0, spring), -0.3, 0.10)
    side = K.round_window(b, "side_window", *ROUND_WINDOWS["ornate"], glazing="wheel", frame_mat="timber")
    K.wall(b, [cut, side])

    # window: glass, leaded bars, timber frame and sill
    glass = bmesh.new()
    P.extrude(glass, arched_outline(w_half, w_z0, spring), 0.07, 0.09)
    b.obj("window_glass", glass, "glass")
    bars = bmesh.new()
    for u in (-w_half / 2, 0.0, w_half / 2):
        h = spring + math.sqrt(max(w_half ** 2 - u * u, 0.0)) - w_z0
        P.box(bars, (u, 0.06, w_z0 + h / 2), (0.024, 0.03, h))
    P.box(bars, (0.0, 0.06, spring), (2 * w_half, 0.03, 0.024))
    for k in range(1, 6):
        a = math.pi * k / 6
        P.box(bars, (0.5 * w_half * math.cos(a), 0.06, spring + 0.5 * w_half * math.sin(a)), (w_half, 0.03, 0.024),
              Matrix.Rotation(-a, 4, "Y"))
    P.arc_block(bars, 0.0, spring, 0.36 * w_half, 0.36 * w_half + 0.024, 0.0, math.pi, 0.045, 0.075, seg=12)
    b.obj("window_bars", bars, "iron", bevel=0.004)
    frame = bmesh.new()
    for s in (-1, 1):
        P.timber(frame, (s * (w_half + 0.045), -0.01, (w_z0 + spring) / 2), (0.09, 0.14, spring - w_z0),
                 seed=seed + s)
    P.arc_block(frame, 0.0, spring, w_half, w_half + 0.09, 0.0, math.pi, -0.08, 0.06, seg=20)
    P.timber(frame, (0.0, -0.05, w_z0 - 0.06), (2 * w_half + 0.3, 0.2, 0.12), seed=seed + 3)
    b.obj("window_frame", frame, "timber", bevel=0.008)

    # half-timbering: posts either side of the window, a timber arch over it, braces up to the eave
    ht = bmesh.new()
    post_u = w_half + 0.32
    for s in (-1, 1):
        P.timber(ht, (s * post_u, -0.02, spring / 2), (0.14, 0.12, spring), seed=seed + 10 * s)
        P.timber(ht, (s * (arch - 0.08), -0.02, top(arch - 0.08) / 2), (0.14, 0.12, top(arch - 0.08)),
                 seed=seed + 20 * s)
        z0, z1 = spring + 0.2, top(arch - 0.08) - 0.1          # from the inner post up to the outer post top
        dx = s * (arch - 0.08 - post_u)
        ang = math.atan2(z1 - z0, dx)
        P.timber(ht, (s * (post_u + arch - 0.08) / 2, -0.02, (z0 + z1) / 2), (math.hypot(dx, z1 - z0), 0.1, 0.11),
                 Matrix.Rotation(-ang, 4, "Y"), seed=seed + 30 * s)
    P.arc_block(ht, 0.0, spring, post_u - 0.07, post_u + 0.07, 0.0, math.pi, -0.06, 0.06, seg=24)
    b.obj("timbering", ht, "timber", bevel=0.01)

    # the carved bargeboard: a broad band along the arched eave, with knots carved along it
    us = K.samples(-arch - 0.25, arch + 0.25, 80)
    band = bmesh.new()
    P.extrude(band, [(u, top(u) + 0.03) for u in us] + [(u, top(u) - 0.30) for u in reversed(us)], -0.56, -0.44)
    for edge in (0.0, -0.27):
        P.extrude(band, [(u, top(u) + edge + 0.03) for u in us] + [(u, top(u) + edge) for u in reversed(us)],
                  -0.59, -0.54)
    b.obj("bargeboard", band, "timber", bevel=0.008)
    knots = bmesh.new()
    run = 0.0
    for u0, u1 in zip(us, us[1:]):
        run += math.hypot(u1 - u0, top(u1) - top(u0))
        if run >= 0.17:
            run = 0.0
            slope = math.atan2(top(u1) - top(u0), u1 - u0)
            P.box(knots, (u1, -0.58, top(u1) - 0.135), (0.09, 0.05, 0.09),
                  Matrix.Rotation(-slope - math.pi / 4, 4, "Y"))
    b.obj("bargeboard_knots", knots, "timber", bevel=0.01)

    K.eave(b, panels=((-(arch + half) / 2, (half - arch) / 2), (0.0, arch), ((arch + half) / 2, (half - arch) / 2)),
           out=0.5)
    return b.objects()


def build():
    """Build the four fronts; return their objects."""
    objs = []
    objs += round_window_front("round_window_west", seed=11)
    objs += round_window_front("round_window_rack", seed=12)
    objs += lattice_front()
    objs += ornate_front()
    return objs

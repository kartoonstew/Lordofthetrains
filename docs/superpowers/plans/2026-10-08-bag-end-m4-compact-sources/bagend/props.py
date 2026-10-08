"""The garden's wooden props, refs/04, 05, 07, 09: bench, gate, letterbox, lamp posts, birdhouse and
the rack. Each is built where layout.py puts it, standing on the ground, into the "props"
collection, from rustic parts (bent timber, worn planks)."""
import math
import random

import bmesh
from mathutils import Matrix

from . import parts as P, terrain

COLL = "props"


def _place(x, y, yaw_deg=0.0, sink=0.0):
    z = float(terrain.ground(x, y)) - sink
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")


def _obj(name, bm, mat, place, bevel=0.0):
    return P.to_object(name, bm, P.materials()[mat], COLL, place, bevel)


def bench(x, y, yaw=-8.0, seed=31):
    """Plank seat and back on four legs, a little weathered (refs/04, 05)."""
    bm = bmesh.new()
    for k, v in enumerate((-0.14, 0.0, 0.14)):                          # seat planks
        P.timber(bm, (0.0, v, 0.45), (1.4, 0.12, 0.04), seed=seed + k, amp=0.004)
    for k, z in enumerate((0.66, 0.82)):                                 # back rails, leaning back
        P.timber(bm, (0.0, 0.22 + 0.04 * k, z), (1.4, 0.035, 0.11), seed=seed + 5 + k, amp=0.004)
    for su in (-0.6, 0.6):
        for sv in (-0.17, 0.17):
            P.timber(bm, (su, sv, 0.2), (0.07, 0.07, 0.5), seed=seed + 10 + round(su * 10 + sv * 10), amp=0.003)
        P.timber(bm, (su, 0.21, 0.5), (0.07, 0.06, 0.95), seed=seed + 20 + round(su * 10), amp=0.003)
        P.timber(bm, (su, 0.0, 0.62), (0.06, 0.42, 0.05), seed=seed + 30 + round(su * 10), amp=0.003)
    return _obj("bench", bm, "timber", _place(x, y, yaw, sink=0.06), bevel=0.008)


def gate(x, y, seed=37):
    """Two stout posts with ball tops and a braced plank gate between them, its sign on the front
    (refs/04, 05)."""
    bm = bmesh.new()
    for s in (-1, 1):
        P.timber(bm, (s * 0.62, 0.0, 0.55), (0.16, 0.16, 1.3), seed=seed + s, amp=0.005)
        P.disc(bm, s * 0.62, 1.22, 0.07, -0.07, 0.07, seg=16)                       # neck
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.1,
                                  matrix=Matrix.Translation((s * 0.62, 0.0, 1.34)))
    for k, u in enumerate((-0.42, -0.21, 0.0, 0.21, 0.42)):                         # boards
        P.timber(bm, (u, 0.0, 0.52), (0.18, 0.04, 0.82), seed=seed + 10 + k, amp=0.004)
    for z in (0.2, 0.84):                                                            # rails
        P.timber(bm, (0.0, -0.04, z), (1.04, 0.05, 0.1), seed=seed + 20 + round(z * 10), amp=0.004)
    brace = math.atan2(0.64, 0.95)
    P.timber(bm, (0.0, -0.04, 0.52), (1.14, 0.05, 0.09), Matrix.Rotation(-brace, 4, "Y"), seed=seed + 30, amp=0.004)
    gate_obj = _obj("gate", bm, "timber", _place(x, y, sink=0.12), bevel=0.008)
    sign = bmesh.new()
    P.box(sign, (0.0, -0.1, 0.62), (0.62, 0.025, 0.38))
    _obj("gate_sign", sign, "stone", _place(x, y, sink=0.12), bevel=0.005)
    return gate_obj


def letterbox(x, y, seed=41):
    """A hollow-log letterbox on a short post (refs/04)."""
    bm = bmesh.new()
    P.timber(bm, (0.0, 0.0, 0.42), (0.1, 0.1, 0.95), seed=seed, amp=0.004)
    log = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.13, radius2=0.12, depth=0.48,
                                matrix=Matrix.Translation((0.0, 0.0, 0.98)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    P.wobble(log["verts"], 0.008, 6.0, seed)
    return _obj("letterbox", bm, "timber", _place(x, y, sink=0.12), bevel=0.006)


def lamp_post(name, x, y, seed=43):
    """A timber post with an iron arm and a hanging lantern, like the door's (refs/07, 09)."""
    place = _place(x, y, sink=0.15)
    bm = bmesh.new()
    P.timber(bm, (0.0, 0.0, 1.0), (0.11, 0.11, 2.15), seed=seed, amp=0.006)
    _obj(f"{name}_post", bm, "timber", place, bevel=0.01)
    iron, glass = bmesh.new(), bmesh.new()
    P.lantern(iron, glass, 0.0, 2.0, v=-0.36)
    _obj(f"{name}_lantern", iron, "iron", place)
    _obj(f"{name}_glass", glass, "glass", place)


def birdhouse(x, y, seed=47):
    """A little house with a steep roof on a tall pole (refs/05, 07)."""
    bm = bmesh.new()
    P.timber(bm, (0.0, 0.0, 1.0), (0.07, 0.07, 2.2), seed=seed, amp=0.006)
    P.box(bm, (0.0, 0.0, 2.2), (0.26, 0.26, 0.3))
    for s in (-1, 1):                                                                # roof slabs
        P.box(bm, (s * 0.09, 0.0, 2.42), (0.24, 0.34, 0.03), Matrix.Rotation(s * math.radians(-50), 4, "Y"))
    _obj("birdhouse", bm, "timber", _place(x, y, sink=0.2), bevel=0.005)


def rack(x, y, seed=53):
    """The rustic wooden frame by the round-window front: two posts, rails and braces (refs/09)."""
    bm = bmesh.new()
    for s in (-1, 1):
        P.timber(bm, (s * 1.0, 0.0, 0.8), (0.1, 0.1, 1.9), seed=seed + s, amp=0.01)
        P.timber(bm, (s * 0.72, 0.0, 1.32), (0.62, 0.07, 0.07),
                 Matrix.Rotation(s * math.radians(40), 4, "Y"), seed=seed + 3 * s, amp=0.008)
    for k, z in enumerate((1.6, 0.9)):
        P.timber(bm, (0.0, 0.0, z), (2.15, 0.08, 0.08), seed=seed + 10 + k, amp=0.012)
    return _obj("rack", bm, "timber", _place(x, y, sink=0.2), bevel=0.008)

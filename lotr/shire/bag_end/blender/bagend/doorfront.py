"""Bag End's door front in full, rustic detail: the green door in its brick arch, two portholes
on side facets that turn back into the hill, timber posts and knee braces, the eave and lantern.

Built in the front's own frame (u along the facade, v into the wall, z up from its floor) and
placed where layout.py puts the door front. Its outline (width, facets, eave line) comes from
layout.py; the door, portholes and trim are sized here, in metres, from refs/01, 02 and 06.
"""
import math

import bmesh
from mathutils import Matrix

from . import frontkit as K, layout as L, parts as P

D = L.D
F = L.front("door")
SILL = 0.06
R_DOOR = D / 2
CZ = SILL + R_DOOR            # door centre: a full circle resting on the sill
RING = 0.08                   # grey timber ring lining the doorway
REVEAL = 0.22                 # door boards set back from the facade
C = F.centre                  # centre facet half-width (inner posts at +-C)
PHI = math.radians(F.wing_angle)        # side facets angle back into the hill
POST = K.POST
S = (F.width / 2 - C) / math.cos(PHI) - POST / 2   # side facet length, to the outer post's centre
EAVE_OUT = K.EAVE_OUT
P_CZ = 0.75 * D + SILL        # porthole centre height
P_GLASS, P_FRAME = 0.18, 0.065
WALL_DEPTH = L.WALL_DEPTH


def eave_centre(u):
    """Eave top over the centre facet, from layout.py."""
    return L.eave_top(F, u)


def eave_side(s):
    """Eave top along a side facet, s from the inner post, from layout.py."""
    return L.eave_top(F, C + s * math.cos(PHI))


def side_matrix(sign):
    """Side facet frame: u from 0 at the inner post outward along the facet, v into the wall."""
    return (Matrix.Translation((sign * C, 0, 0)) @ Matrix.Rotation(sign * PHI, 4, "Z")
            @ Matrix.Scale(sign, 4, (1, 0, 0)))


def build(seed=7):
    """Build every part of the door front into the "door_front" collection and return them; its
    flower pots go to "props", since they print separately."""
    b = K.Builder(L.front("door"), "doorfront", seed)
    rng, m, place, obj = b.rng, b.m, b.place, b.obj

    us = [-C + 2 * C * i / 60 for i in range(61)]
    su = [S * i / 20 for i in range(21)]

    # --- centre facet -------------------------------------------------------------------
    bm = bmesh.new()
    P.plaster_slab(bm, -C, C, -0.3, eave_centre, WALL_DEPTH, seed)
    wall = obj("wall_centre", bm, "plaster")
    P.bake_cuts(wall, [b.disc_cutter(0.0, CZ, R_DOOR + RING - 0.002, -0.3, REVEAL + 0.08)])

    bm = bmesh.new()
    P.segmented_ring(bm, 0.0, CZ, R_DOOR, R_DOOR + RING, -0.03, REVEAL + 0.01, 10, rng, seed)
    obj("door_ring", bm, "ring", bevel=0.008)

    bm = bmesh.new()
    P.crescent_bricks(bm, 0.0, CZ, R_DOOR + RING + 0.004, 0.98, 0.10, 0.065, 0.42, rng)
    obj("door_arch", bm, "brick", bevel=0.007)

    bm = bmesh.new()
    P.plank_door(bm, CZ, R_DOOR - 0.004, REVEAL, 0.06, rng, seed)
    obj("door_boards", bm, "door", bevel=0.006)
    bm = bmesh.new()
    P.disc(bm, 0.0, CZ, R_DOOR - 0.004, REVEAL + 0.03, REVEAL + 0.07, seg=96)
    obj("door_backing", bm, "iron")
    bm = bmesh.new()
    P.door_nails(bm, CZ, R_DOOR - 0.004, REVEAL, rng)
    obj("door_nails", bm, "iron")
    bm = bmesh.new()
    P.disc(bm, 0.0, CZ, 0.06, REVEAL - 0.018, REVEAL, seg=32)
    P.disc(bm, 0.0, CZ, 0.016, REVEAL - 0.07, REVEAL - 0.01, seg=16)
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.042,
                              matrix=Matrix.Translation((0.0, REVEAL - 0.09, CZ)))
    obj("door_knob", bm, "brass")

    bm = bmesh.new()
    P.rough_stone(bm, (0.0, -0.06, (SILL - 0.2) / 2), (1.3, 0.62, SILL + 0.2), rng, seed)
    obj("door_sill", bm, "stone", bevel=0.015)

    bm = bmesh.new()
    P.header_band(bm, us, eave_centre, panels=((-C / 2, C / 2), (C / 2, C / 2)), seed=seed)
    for s in (-1, 1):
        P.timber(bm, (s * C, 0.0, (0.95 + eave_centre(C)) / 2), (POST, POST, eave_centre(C) - 0.95),
                 Matrix.Rotation(s * PHI / 2, 4, "Z"), seed=seed + s)
        P.knee_brace(bm, s * C, eave_centre(C) - 0.06, seed=seed + 3 * s)
    obj("timber_centre", bm, "timber", bevel=0.012)

    fascia, soffit = bmesh.new(), bmesh.new()
    P.eave_hood(fascia, soffit, us, eave_centre, EAVE_OUT, rng, seed)
    obj("fascia_centre", fascia, "timber", bevel=0.008)
    obj("soffit_centre", soffit, "timber", bevel=0.006)

    iron, glass = bmesh.new(), bmesh.new()
    P.lantern(iron, glass, -0.13, eave_centre(0.0) - 0.12)     # hangs clear of the door
    obj("lantern", iron, "iron")
    obj("lantern_glass", glass, "glass")

    bm = bmesh.new()
    P.sod(bm, us, eave_centre, -EAVE_OUT + 0.06, WALL_DEPTH)     # turf over the hood too, as in the photos
    obj("sod_centre", bm, "turf")

    # --- side facets, each with a porthole -----------------------------------------------
    for s, label in ((-1, "left"), (1, "right")):
        mat = side_matrix(s)
        uc = S / 2
        bm = bmesh.new()
        P.plaster_slab(bm, 0.0, S, -0.3, eave_side, WALL_DEPTH, seed + 10 * s)
        wall = obj(f"wall_{label}", bm, "plaster", mat)
        P.bake_cuts(wall, [b.disc_cutter(uc, P_CZ, P_GLASS + P_FRAME - 0.002, -0.3, 0.09, mat),
                           # the side slab swings back behind the centre facet: keep it out of the doorway
                           b.disc_cutter(0.0, CZ, R_DOOR + RING - 0.002, -0.3, REVEAL + 0.08)])

        bm = bmesh.new()
        P.segmented_ring(bm, uc, P_CZ, P_GLASS, P_GLASS + P_FRAME, -0.025, 0.12, 6, rng, seed + s)
        obj(f"{label}_porthole_frame", bm, "green_paint", mat, bevel=0.006)
        glass, came = bmesh.new(), bmesh.new()
        P.leaded_glass(glass, came, uc, P_CZ, P_GLASS, 0.066)
        obj(f"{label}_porthole_glass", glass, "glass", mat)
        obj(f"{label}_porthole_came", came, "iron", mat)

        bm = bmesh.new()
        P.crescent_bricks(bm, uc, P_CZ, P_GLASS + P_FRAME + 0.005, 0.34, 0.07, 0.075, 0.0, rng)
        P.brick_row(bm, uc, P_CZ - P_GLASS - P_FRAME - 0.075, 6, 0.058, 0.08, 0.1, rng)
        obj(f"{label}_bricks", bm, "brick", mat, bevel=0.006)

        bm = bmesh.new()
        P.header_band(bm, su, eave_side, panels=((S / 2, S / 2),), seed=seed + 20 * s)
        P.timber(bm, (S, 0.0, (-0.2 + eave_side(S)) / 2), (POST, POST, eave_side(S) + 0.2), seed=seed + 30 * s)
        P.knee_brace(bm, S - 0.02, eave_side(S) - 0.06, seed=seed + 40 * s)
        obj(f"{label}_timber", bm, "timber", mat, bevel=0.012)

        fascia, soffit = bmesh.new(), bmesh.new()
        P.eave_hood(fascia, soffit, su, eave_side, EAVE_OUT, rng, seed + 50 * s)
        obj(f"{label}_fascia", fascia, "timber", mat, bevel=0.008)
        obj(f"{label}_soffit", soffit, "timber", mat, bevel=0.006)

        bm = bmesh.new()
        # the side turf reaches back over the centre facet too, so no wedge opens behind the post
        P.sod(bm, [-0.4 + (S + 0.4) * i / 24 for i in range(25)], eave_side, -EAVE_OUT + 0.06, WALL_DEPTH)
        obj(f"{label}_sod", bm, "turf", mat)

        P.pot(f"doorfront_pot_{label}", m["terracotta"], "props", place @ Matrix.Translation((s * 1.02, -0.42, 0.0)))
    return b.objects()

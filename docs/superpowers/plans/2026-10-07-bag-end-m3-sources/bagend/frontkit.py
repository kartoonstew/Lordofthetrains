"""Shared pieces for the detailed fronts: placement, an object builder, and the assemblies every
front repeats (the plastered wall, the eave with its timber and turf, round windows).

Everything is built in the front's own frame (u along the facade, v into the wall, z up from its
floor) and placed where layout.py puts the front.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix

from . import layout as L, parts as P

POST = 0.12        # timber posts, square
EAVE_OUT = 0.32    # how far an eave hood projects


def placement(f):
    """Front frame to world: where layout.py puts the front, turned by its yaw."""
    return Matrix.Translation((f.x, f.y, f.floor)) @ Matrix.Rotation(math.radians(f.yaw), 4, "Z")


class Builder:
    """Makes one front's objects: named <prefix>_<part>, in one collection, placed with the front."""

    def __init__(self, f, prefix=None, seed=7):
        self.f, self.prefix, self.coll, self.seed = f, prefix or f.name, f"{f.name}_front", seed
        self.place = placement(f)
        self.m = P.materials()
        self.rng = random.Random(seed)

    def obj(self, name, bm, mat, matrix=None, bevel=0.0):
        local = Matrix.Identity(4) if matrix is None else matrix
        return P.to_object(f"{self.prefix}_{name}", bm, self.m[mat], self.coll, self.place @ local, bevel)

    def disc_cutter(self, cu, cz, r, v0, v1, matrix=None):
        local = Matrix.Identity(4) if matrix is None else matrix
        return P.cylinder_cutter(cu, cz, r, v0, v1, self.coll, self.place @ local)

    def outline_cutter(self, outline, v0, v1):
        bm = bmesh.new()
        P.extrude(bm, outline, v0, v1)
        obj = P.to_object("cutter", bm, None, self.coll, self.place)
        obj.hide_render = True
        return obj

    def objects(self):
        return list(bpy.data.collections[self.coll].objects)


def eave_line(f):
    return lambda u: L.eave_top(f, u)


def samples(u0, u1, step=0.03):
    """Evenly spaced u from u0 to u1, about step apart, so curved eaves stay smooth."""
    n = max(2, round((u1 - u0) / step))
    return [u0 + (u1 - u0) * i / n for i in range(n + 1)]


def wall(b, cutters, u0=None, u1=None, name="wall"):
    """Plastered wall mass across the front, its top on the eave line, with openings cut."""
    half = b.f.width / 2
    u0 = -half if u0 is None else u0
    u1 = half if u1 is None else u1
    bm = bmesh.new()
    P.plaster_slab(bm, u0, u1, -0.3, eave_line(b.f), L.WALL_DEPTH, b.seed)
    obj = b.obj(name, bm, "plaster")
    if cutters:
        P.bake_cuts(obj, cutters)
    return obj


def eave(b, panels, posts=True, label="", out=EAVE_OUT):
    """Header band, end posts with knee braces, curved fascia and soffit, and turf on top."""
    f, half = b.f, b.f.width / 2
    top = eave_line(f)
    us = samples(-half, half)
    bm = bmesh.new()
    P.header_band(bm, us, top, panels=panels, seed=b.seed)
    if posts:
        for s in (-1, 1):
            u = s * (half - POST / 2)
            P.timber(bm, (u, 0.0, (top(u) - 0.2) / 2), (POST, POST, top(u) + 0.2), seed=b.seed + 5 * s)
            P.knee_brace(bm, u - s * 0.02, top(u) - 0.06, seed=b.seed + 7 * s)
    b.obj(f"timber{label}", bm, "timber", bevel=0.012)
    fascia, soffit = bmesh.new(), bmesh.new()
    P.eave_hood(fascia, soffit, us, top, out, b.rng, b.seed)
    b.obj(f"fascia{label}", fascia, "timber", bevel=0.008)
    b.obj(f"soffit{label}", soffit, "timber", bevel=0.006)
    bm = bmesh.new()
    P.sod(bm, us, top, -out + 0.06, L.WALL_DEPTH)     # turf over the hood too, as in the photos
    b.obj(f"sod{label}", bm, "turf")


def round_window(b, label, cu, cz, r_open, frame=0.07, glazing="wheel", frame_mat="green_paint",
                 bricks=True, sill=True):
    """A round window: segmented frame, glass with lead cames or glazing bars, a brick crescent
    over it and a brick sill under it. Returns the cutter for its opening (cut to 0.09 deep)."""
    r = r_open - frame
    bm = bmesh.new()
    P.segmented_ring(bm, cu, cz, r, r_open, -0.03, 0.12, max(6, round(2 * math.pi * r_open / 0.3)),
                     b.rng, b.seed + round(cu * 10))
    b.obj(f"{label}_frame", bm, frame_mat, bevel=0.006)
    glass, bars = bmesh.new(), bmesh.new()
    if glazing == "diamond":
        P.leaded_glass(glass, bars, cu, cz, r, 0.066)
    else:
        P.disc(glass, cu, cz, r, 0.071, 0.091)
        (P.grid_bars if glazing == "grid" else P.wheel_bars)(bars, cu, cz, r, 0.06)
    b.obj(f"{label}_glass", glass, "glass")
    b.obj(f"{label}_bars", bars, "iron" if glazing == "diamond" else frame_mat, bevel=0.004)
    if bricks or sill:
        bm = bmesh.new()
        if bricks:
            P.crescent_bricks(bm, cu, cz, r_open + 0.005, r_open + 0.16, 0.06, 0.075, cz - 0.15, b.rng)
        if sill:
            P.brick_row(bm, cu, cz - r_open - 0.07, max(4, round(2 * r_open / 0.07)), 0.058, 0.08, 0.1, b.rng)
        b.obj(f"{label}_bricks", bm, "brick", bevel=0.006)
    return b.disc_cutter(cu, cz, r_open - 0.002, -0.3, 0.09)

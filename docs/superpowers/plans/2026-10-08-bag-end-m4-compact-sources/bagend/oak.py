"""The oak above Bag End, for previews only: it is never printed (milestone 5 gives the hill a
socket for a bought or wire-armature tree). A gnarled trunk splits into long, spreading limbs with
leaf clumps along them, so the renders read like refs/03 and 09 rather than a lollipop."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

from . import layout as L, parts as P, scene, terrain

COLL = "preview"


def _limb(start, azimuth, elevation, length, droop, r0, r1, rng, n=8):
    """Points and radii of a limb that leaves `start` at an angle and bends toward level."""
    pts, radii = [], []
    p = Vector(start)
    step = length / n
    for i in range(n + 1):
        t = i / n
        el = math.radians(elevation) * (1 - t) - math.radians(droop) * t
        az = math.radians(azimuth) + 0.25 * noise.noise(Vector((t * 3, azimuth, 0.0)))
        pts.append(p.copy())
        radii.append(r0 + (r1 - r0) * t)
        p += Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * step
        p += Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), rng.uniform(-0.04, 0.04)))
    return pts, radii


def _spline(curve, pts, radii):
    sp = curve.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for point, p, r in zip(sp.points, pts, radii):
        point.co = (*p, 1.0)
        point.radius = r


def build(seed=71):
    rng = random.Random(seed)
    x, y = L.OAK
    z = float(terrain.ground(x, y))
    curve = bpy.data.curves.new("oak_trunk", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 1.0
    curve.bevel_resolution = 3
    trunk, tr = _limb((x, y, z - 0.4), 200.0, 80.0, 2.1, -72.0, 0.62, 0.4, rng)        # short and stout
    _spline(curve, trunk, tr)
    top = trunk[-1]
    tips = []                                                  # where leaf clusters grow
    for k in range(6):
        az = 60 * k + rng.uniform(-18, 18)
        pts, radii = _limb(top, az, rng.uniform(14, 30), rng.uniform(3.8, 5.0), rng.uniform(4, 18), 0.26, 0.05, rng)
        _spline(curve, pts, radii)
        tips += pts[4:]
        for j in (3, 5, 7):                                    # side branches off each limb
            side_az = az + rng.choice((-1, 1)) * rng.uniform(30, 60)
            bp, br = _limb(pts[j], side_az, rng.uniform(10, 35), rng.uniform(1.0, 1.8), 10.0, 0.09, 0.03, rng, n=5)
            _spline(curve, bp, br)
            tips += bp[2:]
    trunk_obj = bpy.data.objects.new("oak_trunk", curve)
    trunk_obj.data.materials.append(P.materials()["bark"])
    scene.collection(COLL).objects.link(trunk_obj)

    crown = bmesh.new()
    for i, tip in enumerate(tips):                             # many small clusters, not a few blobs
        r = rng.uniform(0.38, 0.7)
        lift = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(0.1, 0.35)))
        flat = Matrix.Diagonal((1.1, 1.1, 0.5, 1.0))
        made = bmesh.ops.create_icosphere(crown, subdivisions=2, radius=r,
                                          matrix=Matrix.Translation(tip + lift) @ flat)
        P.wobble(made["verts"], 0.3 * r, 3.0, seed + i)
    obj = P.to_object("oak_crown", crown, P.materials()["leaves"], COLL)
    obj.data.shade_smooth()
    return obj

"""Block-out fronts: a plain wall mass with its eave and opening markers, for each front not yet
built in detail (the door front has its own module, doorfront.py)."""
import math

import bpy

from . import layout as L, scene

D = L.D
DEPTH = 0.8        # wall mass behind the facade
EAVE_OUT = 0.35    # how far the eave projects
EAVE_THICK = 0.18

# Openings from refs/03, 05, 08-10, heights above the front's floor:
# ("disc", u, z, r) or ("arched", u, z_bottom, width, height)
OPENINGS = {
    "round_window_west": [("disc", 0.0, 0.70 * D, 0.20 * D)],
    "round_window_rack": [("disc", 0.0, 0.72 * D, 0.22 * D)],
    "ornate": [("arched", 0.0, 0.55 * D, 1.2 * D, 0.95 * D), ("disc", -1.9 * D, 0.9 * D, 0.17 * D)],
    "lattice_window": [("disc", 0.0, 0.87, 0.3 * D)],
}


def prism(name, outline, v0, v1, coll):
    """Extrude a closed (u, z) outline along v, from v0 to v1, in front-local coordinates."""
    n = len(outline)
    verts = [(u, v0, z) for u, z in outline] + [(u, v1, z) for u, z in outline]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return scene.add_mesh_object(name, verts, faces, coll)


def place(obj, f):
    obj.location = (f.x, f.y, 0.0)
    obj.rotation_euler = (0.0, 0.0, math.radians(f.yaw))
    return obj


def profile(f, z_offset=0.0, samples=40):
    """The eave line across the front, left to right, as (u, z)."""
    half = f.width / 2
    us = [-half + 2 * half * i / samples for i in range(samples + 1)]
    return [(u, f.floor + L.eave_top(f, u) + z_offset) for u in us]


def wall(f):
    outline = [(-f.width / 2, f.floor - 0.6)] + profile(f) + [(f.width / 2, f.floor - 0.6)]
    return place(prism(f"front_{f.name}", outline, 0.0, DEPTH, "fronts"), f)


def eave(f):
    band = profile(f, 0.02) + list(reversed(profile(f, -EAVE_THICK)))
    return place(prism(f"eave_{f.name}", band, -EAVE_OUT, 0.3, "fronts"), f)


def disc(name, f, u, z, r, segments=32):
    ring = [(u + r * math.cos(2 * math.pi * k / segments), z + r * math.sin(2 * math.pi * k / segments))
            for k in range(segments)]
    return place(prism(name, ring, -0.03, 0.01, "openings"), f)


def arched(name, f, u, z0, w, h):
    r = w / 2
    top = [(u - r * math.cos(math.pi * k / 16), z0 + h - r + r * math.sin(math.pi * k / 16)) for k in range(17)]
    return place(prism(name, [(u - r, z0)] + top + [(u + r, z0)], -0.03, 0.01, "openings"), f)


def build(exclude=()):
    """Block out every front except those named in exclude (built in detail elsewhere)."""
    for f in L.FRONTS:
        if f.name in exclude:
            continue
        wall(f)
        eave(f)
        for kind, u, z, *size in OPENINGS.get(f.name, ()):
            name = f"window_{f.name}_{round(u * 100):+d}"
            if kind == "arched":
                arched(name, f, u, f.floor + z, *size)
            else:
                disc(name, f, u, f.floor + z, size[0])
    bpy.context.view_layer.update()

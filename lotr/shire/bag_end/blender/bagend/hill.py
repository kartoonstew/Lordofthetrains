"""The hill as one closed mesh: the ground function on a grid, with skirts and a flat bottom."""
import math

import numpy as np

from . import layout as L, scene, terrain

X_RANGE = L.MODEL_X
Y_RANGE = (L.LANE_Y, L.BACK_Y)
STEP = 0.15   # largest grid spacing; the grid spans the ranges exactly, so cells come out a touch smaller


def axis(lo, hi):
    return np.linspace(lo, hi, math.ceil((hi - lo) / STEP - 1e-9) + 1)


def build():
    xs = axis(*X_RANGE)
    ys = axis(*Y_RANGE)
    nx, ny = len(xs), len(ys)
    gx, gy = np.meshgrid(xs, ys)                 # row j is ys[j]
    top = terrain.ground(gx, gy)
    n = nx * ny
    idx = np.arange(n).reshape(ny, nx)
    verts = np.concatenate([
        np.stack([gx.ravel(), gy.ravel(), top.ravel()], axis=1),
        np.stack([gx.ravel(), gy.ravel(), np.full(n, L.BASE_Z)], axis=1),
    ])
    a, b = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel()
    c, d = idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    top_faces = np.stack([a, b, c, d], axis=1)
    bottom_faces = np.stack([a, d, c, b], axis=1) + n
    ring = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])
    nxt = np.roll(ring, -1)
    side_faces = np.stack([ring, ring + n, nxt + n, nxt], axis=1)
    faces = np.concatenate([top_faces, bottom_faces, side_faces]).tolist()
    obj = scene.add_mesh_object("hill", verts.tolist(), faces, "terrain")
    obj.data.shade_smooth()     # render only: hides the grid's facets on steep banks...
    obj.data.set_sharp_from_angle(angle=math.radians(50))   # ...but keeps real creases and skirts crisp
    return obj

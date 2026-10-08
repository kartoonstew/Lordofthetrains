"""The garden, refs/03-05, 07, 09, 10: slate flagstone steps, the dry-stone wall laid stone by stone,
soil beds for planting, brick chimneys with their caps and pots, the wooden props (props.py) and
the preview oak (oak.py)."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, noise, Vector

from . import layout as L, oak, parts as P, props, terrain

COLL = "garden"


def ground_at(x, y):
    return float(terrain.ground(x, y))


def _obj(name, bm, mat, coll=COLL, bevel=0.0):
    return P.to_object(name, bm, P.materials()[mat], coll, bevel=bevel)


def steps(seed=61):
    """One worn slate slab per tread, laid across the path, its top at the tread height."""
    rng = random.Random(seed)
    pts = list(L.STEPS) + [(L.GATE[0], L.GATE[1], L.STEPS[-1][2])]
    for k, (x, y, z) in enumerate(L.STEPS):
        nx, ny, _ = pts[k + 1]
        across = math.atan2(ny - y, nx - x) + math.pi / 2
        bm = bmesh.new()
        P.flagstone(bm, (x, y, z), 1.05, 0.44, 0.1, across, rng, seed + k)
        _obj(f"step_{k}", bm, "stone", bevel=0.012)


def _course(bm, x0, x1, z, h, face, rng, seed, depth=0.22, length=(0.24, 0.46), stagger=0.0):
    """One course of rough stones along x, their fronts a little proud of the wall face."""
    x = x0 + 0.04 + stagger
    k = 0
    while x < x1 - 0.1:
        n = min(rng.uniform(*length), x1 - 0.04 - x)
        d = depth + rng.uniform(0.0, 0.06)
        rot = Matrix.Rotation(rng.uniform(-0.05, 0.05), 4, "Z") @ Matrix.Rotation(rng.uniform(-0.06, 0.06), 4, "Y")
        P.rough_stone(bm, (x + n / 2, face + d / 2 - rng.uniform(0.02, 0.05), z + h / 2),
                      (n - 0.018, d, h - 0.016), rng, seed + k, amp=0.012, rot=rot, cuts=2)
        x += n
        k += 1


def wall(seed=67):
    """The dry-stone wall holding up the path: courses of rough stones over a solid core, capped
    with flatter stones, with a gap where the steps go through (refs/07)."""
    rng = random.Random(seed)
    gap = (L.STEPS[3][0] - 0.55, L.STEPS[3][0] + 0.55)
    face = L.WALL_Y - 0.2
    z0, z1 = L.LAWN_Z - 0.12, L.TERRACE_Z
    for name, x0, x1 in (("wall_west", L.MODEL_X[0] + L.EDGE_FALL, gap[0]),
                         ("wall_east", gap[1], L.MODEL_X[1] - L.EDGE_FALL)):
        bm = bmesh.new()
        P.box(bm, ((x0 + x1) / 2, face + 0.17, (z0 - 0.15 + z1) / 2), (x1 - x0, 0.26, z1 - z0 + 0.15))
        z, course = z0, 0
        while z < z1 - 0.1:
            h = min(rng.uniform(0.13, 0.2), z1 - z)
            _course(bm, x0, x1, z, h, face, rng, seed + 100 * course, stagger=0.15 * (course % 2))
            z += h
            course += 1
        _course(bm, x0, x1, z1, 0.08, face, rng, seed + 999, depth=0.34, length=(0.35, 0.6))   # capstones
        _obj(name, bm, "stone", bevel=0.012)


def beds(seed=73):
    """Low mounds of soil for flowers and shrubs, following the ground."""
    for k, (cx, cy, hl, hw, deg) in enumerate(L.BEDS):
        a = math.radians(deg)
        rings, around = 4, 24
        bm = bmesh.new()
        tip = bm.verts.new((cx, cy, ground_at(cx, cy) + 0.1))
        grid, bottom = [], []
        for i in range(1, rings + 1):
            rho = i / rings
            row = []
            for j in range(around):
                t = 2 * math.pi * j / around
                r = rho * (1.0 + 0.18 * noise.noise(Vector((math.cos(t), math.sin(t), seed + k))))
                u, v = hl * r * math.cos(t), hw * r * math.sin(t)
                x, y = cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a)
                row.append(bm.verts.new((x, y, ground_at(x, y) + 0.09 * (1 - rho * rho) + 0.01)))
                if i == rings:
                    bottom.append(bm.verts.new((x, y, ground_at(x, y) - 0.06)))
            grid.append(row)
        for j in range(around):
            jj = (j + 1) % around
            bm.faces.new((tip, grid[0][j], grid[0][jj]))
            for i in range(rings - 1):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][jj], grid[i][jj]))
            bm.faces.new((grid[-1][j], bottom[j], bottom[jj], grid[-1][jj]))
        bm.faces.new(list(reversed(bottom)))
        _obj(f"bed_{k}", bm, "soil")


def chimneys(seed=79):
    """Brick stacks, course by course, with a stone cap and a clay pot (refs/03, 10)."""
    rng = random.Random(seed)
    s, h = L.CHIMNEY_SIZE, L.CHIMNEY_HEIGHT
    for k, (x, y) in enumerate(L.CHIMNEYS):
        z = ground_at(x, y)
        bm = bmesh.new()
        P.box(bm, (x, y, z - 0.5 + (h + 0.5) / 2), (s - 0.03, s - 0.03, h + 0.5))      # core
        zc, course = z - 0.2, 0
        while zc < z + h - 0.07:
            for side in range(4):
                a = math.pi / 2 * side
                out = Matrix.Rotation(a, 4, "Z")
                u = -s / 2 + (0.11 if course % 2 else 0.0)
                while u < s / 2 - 0.02:
                    n = min(0.215, s / 2 - u)
                    c = out @ Vector((u + n / 2, -s / 2 + 0.03, zc + 0.034))
                    P.box(bm, (x + c.x, y + c.y, c.z), (n - 0.012, 0.07 + rng.uniform(-0.004, 0.004), 0.064), out)
                    u += n
            zc += 0.076
            course += 1
        _obj(f"chimney_{k}", bm, "brick", bevel=0.004)
        cap = bmesh.new()
        P.rough_stone(cap, (x, y, z + h + 0.04), (s + 0.14, s + 0.14, 0.08), rng, seed + k, amp=0.008, cuts=2)
        _obj(f"chimney_cap_{k}", cap, "stone", bevel=0.01)
        pot = bmesh.new()
        bmesh.ops.create_cone(pot, cap_ends=True, segments=16, radius1=0.12, radius2=0.09, depth=0.32,
                              matrix=Matrix.Translation((x + 0.05, y, z + h + 0.24)))
        _obj(f"chimney_pot_{k}", pot, "terracotta", bevel=0.006)


def build():
    steps()
    wall()
    beds()
    chimneys()
    props.bench(*L.BENCH)
    props.gate(*L.GATE)
    props.letterbox(L.GATE[0] - 1.0, L.GATE[1])
    for k, (x, y) in enumerate(L.LAMPS):
        props.lamp_post(f"lamp_{k}", x, y)
    props.birdhouse(*L.BIRDHOUSE)
    props.rack(*L.RACK)
    oak.build()
    bpy.context.view_layer.update()

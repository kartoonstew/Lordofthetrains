"""The garden, refs/03-05, 07, 09, 10: the stone path and the dry-stone wall (stone.py),
soil beds for planting, brick chimneys with their caps and pots, the wooden props (props.py) and
the oak (oak.py, a separate print that plugs into the hill)."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, noise, Vector

from . import layout as L, oak, parts as P, props, stone, terrain

COLL = "garden"


def ground_at(x, y):
    return float(terrain.ground(x, y))


def _obj(name, bm, mat, coll=COLL, bevel=0.0):
    return P.to_object(name, bm, P.materials()[mat], coll, bevel=bevel)


def steps():
    """The stone path: a flagged landing at the door, slate steps on stacked risers down through the
    wall to the gate, small stones packed along them (stone.py)."""
    stone.path()


def wall():
    """The dry-stone wall holding up the terrace, its gap for the steps and the cheek walls lining
    their cutting (stone.py)."""
    stone.walls()


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
        cap = stone.Pile()                                  # a split slate slab
        stone.slab(cap, (x, y, z + h + 0.09), (s + 0.16, s + 0.16, 0.09), rng, rng.uniform(-0.1, 0.1))
        cap.to_object(f"chimney_cap_{k}", "stone", COLL)
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
    if L.RACK:
        props.rack(*L.RACK)
    oak.build()
    bpy.context.view_layer.update()

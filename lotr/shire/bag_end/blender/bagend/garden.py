"""Milestone 1 block-out: steps, dry-stone wall, props, chimneys and the preview oak."""
import math

import bmesh
import bpy

from . import layout as L, scene, terrain


def ground_at(x, y):
    return float(terrain.ground(x, y))


def box(name, x, y, z0, sx, sy, sz, coll, yaw=0.0):
    """Box centred on (x, y) in plan, from z0 up by sz, turned by yaw degrees."""
    a = math.radians(yaw)
    corners = [(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)]
    pts = [(x + cx * math.cos(a) - cy * math.sin(a), y + cx * math.sin(a) + cy * math.cos(a)) for cx, cy in corners]
    verts = [(px, py, z0) for px, py in pts] + [(px, py, z0 + sz) for px, py in pts]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return scene.add_mesh_object(name, verts, faces, coll)


def solid(name, make, coll, location, scale=(1.0, 1.0, 1.0)):
    """Object from a bmesh primitive builder, placed and scaled."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    make(bm)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection(coll).objects.link(obj)
    obj.location = location
    obj.scale = scale
    return obj


def steps():
    pts = list(L.STEPS) + [(L.GATE[0], L.GATE[1], L.STEPS[-1][2])]
    for k, (x, y, z) in enumerate(L.STEPS):
        nx, ny, _ = pts[k + 1]
        yaw = math.degrees(math.atan2(ny - y, nx - x)) + 90
        box(f"step_{k}", x, y, z - 0.3, 0.95, 0.7, 0.3, "garden", yaw)


def wall():
    gap = (L.STEPS[3][0] - 0.55, L.STEPS[3][0] + 0.55)
    for name, x0, x1 in (("wall_west", L.MODEL_X[0] + L.EDGE_FALL, gap[0]),
                         ("wall_east", gap[1], L.MODEL_X[1] - L.EDGE_FALL)):
        box(name, (x0 + x1) / 2, L.WALL_Y - 0.1, L.LAWN_Z - 0.3, x1 - x0, 0.25, 0.35 - L.LAWN_Z, "garden")


def props():
    x, y = L.BENCH
    z = ground_at(x, y)
    box("bench", x, y, z - 0.1, 1.5, 0.45, 0.55, "props", yaw=-8)
    box("bench_back", x, y + 0.2, z - 0.1, 1.5, 0.06, 0.95, "props", yaw=-8)
    x, y = L.BIRDHOUSE
    z = ground_at(x, y)
    box("birdhouse_post", x, y, z - 0.2, 0.08, 0.08, 1.6, "props")
    box("birdhouse", x, y, z + 1.4, 0.32, 0.32, 0.38, "props")
    for k, (x, y) in enumerate(L.LAMPS):
        z = ground_at(x, y)
        box(f"lamp_post_{k}", x, y, z - 0.2, 0.1, 0.1, 1.9, "props")
        box(f"lamp_{k}", x, y, z + 1.6, 0.24, 0.24, 0.32, "props")
    x, y = L.GATE
    z = ground_at(x, y)
    for side in (-1, 1):
        box(f"gate_post_{side:+d}", x + side * 0.6, y, z - 0.2, 0.14, 0.14, 1.3, "props")
    box("gate", x, y, z + 0.05, 1.06, 0.06, 0.95, "props")
    box("letterbox_post", x - 1.0, y, z - 0.2, 0.1, 0.1, 1.1, "props")
    box("letterbox", x - 1.0, y, z + 0.9, 0.3, 0.45, 0.3, "props")
    x, y = L.RACK
    z = ground_at(x, y)
    for side in (-1, 1):
        box(f"rack_post_{side:+d}", x + side * 1.0, y, z - 0.2, 0.1, 0.1, 1.8, "props")
    box("rack_rail", x, y, z + 1.45, 2.1, 0.08, 0.08, "props")


def chimneys():
    s = L.CHIMNEY_SIZE
    for k, (x, y) in enumerate(L.CHIMNEYS):
        z = ground_at(x, y)
        box(f"chimney_{k}", x, y, z - 0.5, s, s, L.CHIMNEY_HEIGHT + 0.5, "chimneys")
        box(f"chimney_cap_{k}", x, y, z + L.CHIMNEY_HEIGHT, s + 0.15, s + 0.15, 0.12, "chimneys")


def oak():
    """Preview only: never exported."""
    x, y = L.OAK
    z = ground_at(x, y)
    solid("oak_trunk", lambda bm: bmesh.ops.create_cone(
        bm, cap_ends=True, segments=16, radius1=0.5, radius2=0.35, depth=3.0), "preview", (x, y, z + 1.2))
    solid("oak_crown", lambda bm: bmesh.ops.create_uvsphere(
        bm, u_segments=24, v_segments=12, radius=L.OAK_CROWN / 2), "preview", (x, y, z + 4.2), (1.0, 0.8, 0.38))


def build():
    steps()
    wall()
    props()
    chimneys()
    oak()
    bpy.context.view_layer.update()

import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from bagend import garden, layout as L, scene, terrain


def test_chimneys_sit_in_the_turf_and_stand_proud():
    scene.reset_scene()
    garden.build()
    for k, (x, y) in enumerate(L.CHIMNEYS):
        zs = [v.co.z for v in bpy.data.objects[f"chimney_{k}"].data.vertices]
        ground = float(terrain.ground(x, y))
        assert min(zs) < ground - 0.3
        assert max(zs) >= ground + L.CHIMNEY_HEIGHT - 0.01


def test_every_step_slab_top_is_its_tread_height():
    # The tread is the highest stone of its step: riser and packing stones stay below it.
    scene.reset_scene()
    garden.build()
    for k, (_, _, z) in enumerate(L.STEPS):
        zs = [v.co.z for v in bpy.data.objects[f"step_{k}"].data.vertices]
        assert z - 0.01 <= max(zs) <= z + 1e-6, k                # worn slate: its top dips a little


def test_dry_stone_wall_stops_short_of_the_thin_edges():
    # Its stones may lean a few centimetres into the edge fall, never beyond it.
    scene.reset_scene()
    garden.build()
    xs = [v.co.x for n in ("wall_west", "wall_east") for v in bpy.data.objects[n].data.vertices]
    assert min(xs) >= L.MODEL_X[0] + L.EDGE_FALL - 0.1, min(xs)
    assert max(xs) <= L.MODEL_X[1] - L.EDGE_FALL + 0.1, max(xs)


def test_garden_parts_are_closed_solids_standing_on_the_ground():
    scene.reset_scene()
    garden.build()
    for coll in ("garden", "props"):
        for o in bpy.data.collections[coll].objects:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            try:
                assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True) > 0, o.name
            finally:
                bm.free()
            low = min((o.matrix_world @ v.co).z for v in o.data.vertices)
            x, y = o.matrix_world.translation.x, o.matrix_world.translation.y
            hung = o.name.endswith(("_sign", "_lantern", "_glass"))   # these hang from a post or the gate
            if coll == "props" and not hung:                       # the rest are planted, not floating
                assert low <= float(terrain.ground(x, y)) + 0.01, (o.name, low)


def test_the_oak_is_its_own_print_standing_on_the_hill_top():
    # A separate print in its own collection (no longer a preview), planted at layout.OAK.
    scene.reset_scene()
    garden.build()
    assert "preview" not in bpy.data.collections
    names = {o.name for o in bpy.data.collections["oak"].objects}
    assert names == {"oak_trunk", "oak_crown"}, names
    x, y = L.OAK
    ground = float(terrain.ground(x, y))
    trunk = bpy.data.objects["oak_trunk"]
    zs = [v.co.z for v in trunk.data.vertices if (v.co.x - x) ** 2 + (v.co.y - y) ** 2 < 0.3 ** 2]
    assert min(zs) < ground - L.OAK_PEG[1] + 0.01 and max(zs) > ground + L.OAK_FORK      # peg below, bole above


def islands(obj):
    """How many separate pieces a mesh is made of."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    seen, count = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        count += 1
        stack = [v]
        while stack:
            w = stack.pop()
            if w.index in seen:
                continue
            seen.add(w.index)
            stack.extend(e.other_vert(w) for e in w.link_edges)
    bm.free()
    return count


def test_garden_is_built_in_detail():
    # Stone by stone and slab by slab, not plain blocks: refs/04, 05, 07.
    scene.reset_scene()
    garden.build()
    names = {o.name for o in bpy.data.objects}
    for k in range(len(L.CHIMNEYS)):
        assert {f"chimney_{k}", f"chimney_cap_{k}", f"chimney_pot_{k}"} <= names, k
    assert {f"bed_{k}" for k in range(len(L.BEDS))} <= names
    assert islands(bpy.data.objects["wall_west"]) > 40           # a core and its stones
    assert {f"step_{k}" for k in range(len(L.STEPS))} | {"landing"} <= names
    assert islands(bpy.data.objects["chimney_0"]) > 20            # laid brick by brick


def _hit(origin, direction):
    dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, _, _, obj, _ = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    return (obj.name, loc) if ok else (None, None)


def test_wall_courses_reach_the_capstones():
    # M4's wall stopped its courses up to 6 cm short of the capstones, showing the plain core. Now,
    # where the wall stands full height, a level ray just under the capstones meets a stone face (within
    # 5 cm of the face line; the core sits 12 cm back) everywhere but in the joints between stones.
    scene.reset_scene()
    garden.build()
    face = L.WALL_Y - 0.2
    tried = stone_faces = 0
    for x in np.arange(L.MODEL_X[0] + L.EDGE_FALL + 0.15, L.MODEL_X[1] - L.EDGE_FALL - 0.15, 0.04):
        if terrain.ground(x, L.WALL_Y + 0.03) < L.TERRACE_Z - 0.005:
            continue                                   # where the wall's top follows the bank down
        for z in (L.TERRACE_Z - 0.03, L.TERRACE_Z - 0.07):
            name, loc = _hit((x, face - 1.0, z), (0.0, 1.0, 0.0))
            tried += 1
            stone_faces += bool(name and name.startswith("wall_") and loc.y < face + 0.05)
    assert tried > 400 and stone_faces >= 0.75 * tried, (stone_faces, tried)


def test_the_wall_follows_the_bank_down_to_the_path():
    # Either side of the path the turf behind the wall falls with the bank, and the wall's top falls
    # with it: never above the turf by more than a capstone, never more than a course below it.
    scene.reset_scene()
    garden.build()
    co = np.concatenate([np.array([v.co[:] for v in bpy.data.objects[n].data.vertices])
                         for n in ("wall_west", "wall_east")])
    checked = 0
    for x in np.arange(L.MODEL_X[0] + L.EDGE_FALL + 0.2, L.MODEL_X[1] - L.EDGE_FALL - 0.2, 0.1):
        turf = float(terrain.ground(x, L.WALL_Y + 0.03))
        front = float(terrain.ground(x, L.WALL_Y - 0.25))
        near = co[np.abs(co[:, 0] - x) < 0.06]
        if turf - front < 0.25:
            continue                                   # the gap: the path comes through here
        checked += 1
        assert len(near) and turf - 0.3 <= near[:, 2].max() <= turf + 0.1, (round(x, 2), turf, near[:, 2].max())
    assert checked > 80

def test_every_step_stands_on_a_riser():
    # A built step, not a slab floating on a slope (refs/05): under each tread's front edge the slab's
    # own thick edge, or where the rise is more than that a course of stacked stone, fills the height
    # down to the next tread.
    scene.reset_scene()
    garden.build()
    pts = terrain.path_line()
    for k in range(len(L.STEPS) - 1):
        p, nxt = pts[k], pts[k + 1]
        u = (nxt - p) / np.linalg.norm(nxt - p)
        v = np.array([-u[1], u[0]])
        nose = p + u * np.linalg.norm(nxt - p) / 2
        top, below = L.STEPS[k][2], L.STEPS[k + 1][2]
        gap = top - L.TREAD - 0.012 - below            # between the tread's underside and the next tread
        z = below + gap / 2 if gap > 0.03 else below + 0.6 * (top - below)
        found = 0
        for off in (-0.3, -0.1, 0.1, 0.3):
            o = nose + u * 0.4 + v * off
            name, loc = _hit((o[0], o[1], z), (-u[0], -u[1], 0.0))
            found += bool(name == f"step_{k}" and (Vector((o[0], o[1], z)) - loc).length < 0.4 + 0.12)
        assert found >= 3, (k, found)


def test_the_path_runs_clear_from_the_door_to_the_gate():
    # Looking straight down on the middle of each tread: the tread itself, at its height; no wall or
    # cheek stone lies across the way. And flags cover the landing in front of the door.
    scene.reset_scene()
    garden.build()
    pts = terrain.path_line()
    for k, (x, y, z) in enumerate(L.STEPS):
        u = (pts[k + 1] - pts[k]) / np.linalg.norm(pts[k + 1] - pts[k])
        on_tread = 0
        for off in (-0.25, 0.0, 0.25):                    # a tread of two slabs has a joint somewhere
            name, loc = _hit((x - u[1] * off, y + u[0] * off, z + 2.0), (0.0, 0.0, -1.0))
            on_tread += bool(name == f"step_{k}" and z - 0.04 <= loc.z <= z + 1e-6)
        assert on_tread >= 2, (k, on_tread)
    (x0, y0), (x1, y1) = L.LANDING
    hits = [_hit((x, y, 1.0), (0.0, 0.0, -1.0))[0] for x in np.linspace(x0 + 0.05, x1 - 0.05, 9)
            for y in np.linspace(y0 + 0.05, y1 - 0.05, 5)]
    assert hits.count("landing") >= 0.75 * len(hits), hits


def test_the_path_is_dense():
    # refs/04: a run of many long, narrow slabs, close together. Looking straight down on the path,
    # from the top tread to the last one's front, there is stone all the way across it: no band of
    # grass between treads (a joint between two slabs laid side by side may let one ray through).
    scene.reset_scene()
    garden.build()
    assert len(L.STEPS) >= 10
    pts = terrain.path_line()
    goings = np.hypot(*np.diff(pts[:-1], axis=0).T)
    assert goings.max() <= 0.36, goings
    _, front = terrain.tread_chainage()
    start = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    for sv in np.arange(0.0, front[-1], 0.04):
        x, y = np.interp(sv, start, pts[:, 0]), np.interp(sv, start, pts[:, 1])
        k = min(np.searchsorted(start, sv, side="right") - 1, len(pts) - 2)
        u = (pts[k + 1] - pts[k]) / np.linalg.norm(pts[k + 1] - pts[k])
        hits = 0
        for off in (-0.25, 0.0, 0.25):
            name, _ = _hit((x - u[1] * off, y + u[0] * off, 1.0), (0.0, 0.0, -1.0))
            hits += bool(name and name.startswith("step_"))
        assert hits >= 2, (round(sv, 2), hits)
    assert islands(bpy.data.objects["landing"]) >= 5


def test_each_tread_is_stacked_on_the_one_below():
    # refs/05: each slab's back runs in under the front of the slab above it, by 3 cm or more.
    scene.reset_scene()
    garden.build()
    _, front = terrain.tread_chainage()
    for k in range(1, len(L.STEPS)):
        co = np.array([v.co[:] for v in bpy.data.objects[f"step_{k}"].data.vertices])
        s, d = terrain.path_frame(co[:, 0], co[:, 1])
        tread = co[(np.abs(d) < 0.3) & (co[:, 2] > L.STEPS[k][2] - 0.14)]
        s, _ = terrain.path_frame(tread[:, 0], tread[:, 1])
        assert s.min() <= front[k - 1] - 0.03, (k, s.min(), front[k - 1])

def test_beds_and_furniture_keep_clear_of_the_path():
    # Nothing planted on the treads: beds, bench, birdhouse and lamp all stand beyond the longest
    # slab's end (0.65 m, set up to 0.08 m off the path's centre).
    things = [(cx, cy, hl, hw, deg) for cx, cy, hl, hw, deg in L.BEDS] + [(*L.BENCH, 0.75, 0.3, -8.0),
                                                                          (*L.BIRDHOUSE, 0.15, 0.15, 0.0)]
    things += [(x, y, 0.1, 0.1, 0.0) for x, y in L.LAMPS]
    for cx, cy, hl, hw, deg in things:
        a = math.radians(deg)
        for du in (-hl, 0.0, hl):
            for dv in (-hw, 0.0, hw):
                x, y = cx + du * math.cos(a) - dv * math.sin(a), cy + du * math.sin(a) + dv * math.cos(a)
                s, d = terrain.path_frame(np.array([x]), np.array([y]))
                assert s[0] < -0.3 or abs(d[0]) >= L.STEP_LENGTH[1] / 2 + 0.08, ((cx, cy), (x, y), d[0])

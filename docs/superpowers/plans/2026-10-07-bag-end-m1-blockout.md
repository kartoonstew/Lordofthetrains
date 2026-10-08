# Bag End Milestone 1 (Rough Layout) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A scripted Blender block-out of the whole Bag End hill. It covers the landform, all five
fronts as plain masses with eaves and openings, the garden, steps, wall, props, chimneys and a
preview oak, rendered from cameras matched to the reference photos so the layout can be checked.

**Architecture:** A small Python package (`bagend`) runs inside headless Blender 5.0. The
landform is a numpy height function turned into one closed mesh, and the fronts sit in ground the
function digs out for them. Everything is in real-world metres. `build.py` regenerates the
`.blend` and the renders, and a shell wrapper adds photo-next-to-render sheets.

**Tech Stack:** Blender 5.0.1 (bpy, bmesh, mathutils, bundled numpy 1.26), Cycles, Python 3.11
inside Blender, system Python 3 + Pillow for the comparison sheets.

**Spec:** `docs/superpowers/specs/2026-10-07-bag-end-blender-design.md`

## Global Constraints

- Blender at `/Applications/Blender.app/Contents/MacOS/Blender`, version 5.0 or newer; override
  with `BLENDER=...`.
- Units are real-world metres.
- Frame: origin at the centre of the door sill. +x runs left to right along the row as seen from
  the garden, +y goes back into the hill, +z is up.
- D = 1.57 m (door diameter). Facade sizes are multiples of D measured from the refs.
- No grass, bushes or ivy geometry; the owner flocks after printing.
- HO scale (1:87) is applied only at export (milestone 5), never in the model.
- The project is not a git repository, so there are no commit steps. Ask Ryan before running
  `git init`.

## Review Focus

- **Rebuilding in the same Blender session** must not leave duplicate objects (`hill.001`). Test:
  Task 6, `test_build_twice_gives_one_of_each`.
- **The far reference camera** (ref 09, about 60 m out) must not clip the scene. Test: Task 5,
  `test_cameras_see_the_whole_hill`.
- **A turned front** (the lattice window front, yaw −5°) must still be covered by turf and dug
  out in front. Covered by Task 2's terrain tests, which loop over every front, yawed one
  included.
- **An older Blender** must fail loudly, not half-build. Test: Task 1,
  `test_blender_is_5_or_newer`.
- **A missing `renders/` folder** must be created rather than crash the render. Handled in
  `render.render_all` (`mkdir(parents=True)`); exercised by Task 6's build run.

---

## File structure

```
lotr/shire/bag_end/
  blender/
    build.py              entry point: build the scene, save .blend, render
    bagend/
      __init__.py
      scene.py            reset to an empty metric scene; collections; mesh objects
      layout.py           every position and size, in metres (pure data, no bpy)
      terrain.py          ground height function (numpy only)
      hill.py             the landform as one closed mesh
      blockout.py         the five fronts: wall mass, eave, opening markers
      garden.py           steps, dry-stone wall, props, chimneys, preview oak
      render.py           materials, light, matched cameras, Cycles renders
    tests/
      run_tests.py        runs tests/test_*.py inside Blender
      test_*.py
  bag_end.blend           generated
  renders/                generated: render_<camera>.png, compare_<camera>.png
  old_openscad/           the two earlier attempts, archived
tools/
  blender.sh              run a script in headless Blender with bagend importable
  build_bag_end.sh        build + comparison sheets
```

---

### Task 1: Harness: headless runner, test runner, metric scene; archive the old attempts

**Files:**
- Create: `tools/blender.sh`, `lotr/shire/bag_end/blender/bagend/__init__.py`,
  `lotr/shire/bag_end/blender/bagend/scene.py`, `lotr/shire/bag_end/blender/tests/run_tests.py`,
  `lotr/shire/bag_end/blender/tests/test_scene.py`
- Move: `lotr/shire/bag_end/{bag_end.scad,stl,renders,README.md}` → `lotr/shire/bag_end/old_openscad/`
- Modify: `tools/build.sh` (drop the Bag End section), `README.md` (catalogue row)

**Interfaces:**
- Produces: `tools/blender.sh <script> [args]`;
  `scene.reset_scene() -> bpy.types.Scene`; `scene.collection(name) -> bpy.types.Collection`;
  `scene.add_mesh_object(name, verts, faces, coll_name) -> bpy.types.Object` (normals
  recalculated outward).

- [ ] **Step 1: Archive the OpenSCAD attempts**

```bash
cd ~/App_dev/ho-movie-scenery/lotr/shire/bag_end
mkdir -p old_openscad && mv bag_end.scad stl renders README.md old_openscad/
```

In `tools/build.sh`, delete everything from `# compare <ref photo>` to the end of the file, and
add `# No OpenSCAD models yet; Bag End is built by tools/build_bag_end.sh.` after the `png()`
function. In `README.md`, replace the Bag End catalogue row with:
`| [Bag End](lotr/shire/bag_end/) | about 40 × 26 m real; scale chosen at export | – | – | Blender rebuild, milestone 1 |`

- [ ] **Step 2: Write `tools/blender.sh`**

```bash
#!/usr/bin/env bash
# Run a Python script in headless Blender with the Bag End package importable.
#   tools/blender.sh path/to/script.py [args for the script...]
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
script=$1; shift
exec "$BLENDER" --background --factory-startup --python-exit-code 1 \
    --python-expr "import sys; sys.path.insert(0, '$PWD/lotr/shire/bag_end/blender')" \
    --python "$script" -- "$@"
```

Run: `chmod +x tools/blender.sh`

- [ ] **Step 3: Write the test runner `tests/run_tests.py`**

```python
"""Run every test_* function in tests/test_*.py inside Blender; exit 1 on any failure.

    tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py [test_module ...]
"""
import importlib.util
import pathlib
import sys
import traceback

here = pathlib.Path(__file__).parent
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ran = failed = 0
for path in sorted(here.glob("test_*.py")):
    if only and path.stem not in only:
        continue
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        ran += 1
        try:
            getattr(module, name)()
            print(f"PASS {path.stem}.{name}")
        except Exception:
            failed += 1
            print(f"FAIL {path.stem}.{name}")
            traceback.print_exc()
print(f"{ran - failed}/{ran} passed")
sys.exit(1 if failed or not ran else 0)
```

- [ ] **Step 4: Write the failing test `tests/test_scene.py`**

```python
import bpy

from bagend import scene


def test_blender_is_5_or_newer():
    assert bpy.app.version >= (5, 0, 0), bpy.app.version_string


def test_reset_scene_is_empty_and_metric():
    s = scene.reset_scene()
    assert s.unit_settings.system == "METRIC"
    assert s.unit_settings.scale_length == 1.0
    assert len(bpy.data.objects) == 0


def test_add_mesh_object_points_normals_outward():
    scene.reset_scene()
    verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    obj = scene.add_mesh_object("cube", verts, faces, "test")
    top = max(obj.data.polygons, key=lambda p: p.center.z)
    assert top.normal.z > 0.99
    assert obj.users_collection[0].name == "test"
```

- [ ] **Step 5: Run it and watch it fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_scene 2>&1 | grep -E "PASS|FAIL|passed|Error"`
Expected: FAIL with `ModuleNotFoundError: No module named 'bagend'`

- [ ] **Step 6: Implement `bagend/__init__.py` (empty) and `bagend/scene.py`**

```python
"""Scene setup shared by the build and the tests."""
import bmesh
import bpy


def reset_scene():
    """Empty the file and set real-world metric units (1 Blender unit = 1 m)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"
    return scene


def collection(name):
    """Get or create a top-level collection."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def add_mesh_object(name, verts, faces, coll_name):
    """Make a mesh object from vertices and faces, with face normals pointing outward."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection(coll_name).objects.link(obj)
    return obj
```

- [ ] **Step 7: Run the tests and watch them pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_scene 2>&1 | grep -E "PASS|FAIL|passed"`
Expected: `3/3 passed`, and the command's exit code is 0.

---

### Task 2: Layout data and the ground function

**Files:**
- Create: `bagend/layout.py`, `bagend/terrain.py`, `tests/test_layout.py`, `tests/test_terrain.py`

**Interfaces:**
- Produces: `layout.D`; `layout.Front(name, x, y, width, floor, eave, eave_ends, arch=0.0, yaw=0.0)`;
  `layout.FRONTS`; `layout.front(name) -> Front`; `layout.eave_top(f, u) -> float`;
  `layout.to_world(f, u, v) -> (x, y)`. Constants: `TERRACE_Z, WALL_Y, LAWN_Z, LANE_Z, LANE_Y,
  CREST_Y, CREST_Z, ORNATE_RISE, TOP_RISE, WEST_X, EAST_X, BACK_Y, BASE_Z, CHIMNEYS,
  CHIMNEY_SIZE, CHIMNEY_HEIGHT, OAK, OAK_CROWN, STEPS, GATE, BENCH, BIRDHOUSE, LAMPS, RACK`.
  `terrain.ground(x, y)` returns a numpy array (0-d for scalars) of ground heights in metres.

- [ ] **Step 1: Write the failing tests**

`tests/test_layout.py`:

```python
from bagend import layout as L


def test_fronts_run_left_to_right_without_overlapping():
    for a, b in zip(L.FRONTS, L.FRONTS[1:]):
        assert a.x + a.width / 2 < b.x - b.width / 2, (a.name, b.name)


def test_door_front_matches_refs_01():
    door = L.front("door")
    assert abs(door.width / L.D - 2.24) < 0.01
    assert abs(door.eave / L.D - 1.39) < 0.01


def test_row_is_about_30_metres():
    first, last = L.FRONTS[0], L.FRONTS[-1]
    length = (last.x + last.width / 2) - (first.x - first.width / 2)
    assert 25.0 < length < 35.0, length


def test_chimneys_and_oak_stand_behind_the_facades():
    for x, y in L.CHIMNEYS + (L.OAK,):
        assert y > 2.0, (x, y)


def test_steps_descend_from_door_to_gate():
    zs = [z for _, _, z in L.STEPS]
    assert zs[0] == L.TERRACE_Z
    assert all(a > b for a, b in zip(zs, zs[1:]))
```

`tests/test_terrain.py`:

```python
import numpy as np

from bagend import layout as L, terrain


def g(x, y):
    return float(terrain.ground(x, y))


def test_door_landing_is_level():
    for u in (-0.6, 0.0, 0.6):
        assert abs(g(u, -0.8) - L.TERRACE_Z) < 0.05, u


def test_turf_covers_every_front():
    for f in L.FRONTS:
        for u in np.linspace(-f.width / 2, f.width / 2, 9):
            for v in (0.4, 0.8, 1.2):
                x, y = L.to_world(f, u, v)
                need = f.floor + L.eave_top(f, u) + 0.15
                assert g(x, y) >= need, (f.name, round(u, 2), v, g(x, y), need)


def test_ground_is_dug_out_in_front_of_every_front():
    for f in L.FRONTS:
        for u in np.linspace(-0.95 * f.width / 2, 0.95 * f.width / 2, 7):
            x, y = L.to_world(f, u, -0.05)
            assert g(x, y) <= f.floor + 0.05, (f.name, round(u, 2), g(x, y))


def test_no_step_is_buried():
    for x, y, z in L.STEPS:
        assert g(x, y) <= z + 0.01, (x, y, z, g(x, y))


def test_lawn_falls_from_the_wall_to_the_lane():
    assert abs(g(-10.0, L.WALL_Y - 0.01) - L.LAWN_Z) < 0.05
    assert abs(g(-10.0, L.LANE_Y) - L.LANE_Z) < 0.05
```

- [ ] **Step 2: Run and watch them fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_layout test_terrain 2>&1 | grep -E "PASS|FAIL|passed|Error"`
Expected: FAIL with `ImportError: cannot import name 'layout'`

- [ ] **Step 3: Implement `bagend/layout.py`**

```python
"""Where everything on Bag End goes, in metres, measured from the reference photos.

Frame: origin at the centre of the door sill. +x runs left to right along the row as seen
from the garden, +y goes back into the hill, +z is up. D is the door diameter; most sizes
are multiples of it, measured in refs/01, 03, 09 and 10.
"""
import math
from dataclasses import dataclass

D = 1.57


@dataclass(frozen=True)
class Front:
    name: str
    x: float           # centre of the facade along the row
    y: float           # facade line: front face of the wall
    width: float
    floor: float       # z at the bottom of the facade
    eave: float        # eave top above the floor, at the centre
    eave_ends: float   # eave top above the floor, at the outer ends
    arch: float = 0.0  # half-width of the arched centre; 0 means the whole front
    yaw: float = 0.0   # degrees; positive turns the front to face right


FRONTS = (
    Front("round_window_west", -14.4 * D, 0.0, 1.6 * D, 0.0, 1.25 * D, 1.05 * D),
    Front("round_window_rack", -10.95 * D, 0.0, 1.9 * D, 0.0, 1.30 * D, 1.10 * D),
    Front("ornate", -4.9 * D, 0.0, 4.75 * D, 0.0, 2.35 * D, 1.30 * D, arch=1.25 * D),
    Front("door", 0.0, 0.0, 2.24 * D, 0.0, 1.39 * D, 1.15 * D),
    Front("lattice_window", 2.8 * D, 0.4, 1.3 * D, 0.45, 1.25 * D, 1.05 * D, yaw=-5.0),
)


def front(name):
    return next(f for f in FRONTS if f.name == name)


def eave_top(f, u):
    """Eave top above the front's floor, at distance u along it from its centre."""
    half = f.arch or f.width / 2
    t = max(0.0, 1.0 - (u / half) ** 2)
    return f.eave_ends + (f.eave - f.eave_ends) * math.sqrt(t)


def to_world(f, u, v):
    """Front-local (u along the facade, v into the hill) to world (x, y)."""
    a = math.radians(f.yaw)
    return (f.x + u * math.cos(a) - v * math.sin(a), f.y + u * math.sin(a) + v * math.cos(a))


# Garden
TERRACE_Z = 0.0           # the path along the fronts
WALL_Y = -3.6             # face of the dry-stone wall holding up the path
LAWN_Z = -0.9             # lawn at the foot of the wall...
LANE_Z = -1.7             # ...falling to the lane along the front edge
LANE_Y = -9.0

# Hill
CREST_Y = 0.6             # crest line, just behind the facades
CREST_Z = 1.75 * D        # crest above the door sill, refs/03
ORNATE_RISE = 1.5         # the hill swells higher over the ornate front, refs/09
TOP_RISE = 0.9            # dome behind the crest
WEST_X, EAST_X = -27.5, 9.0   # where the hill's ends meet the ground
BACK_Y = 16.0                 # where its back meets the ground
BASE_Z = -2.4             # underside of the model

# Hill top, refs/03, 09, 10
CHIMNEYS = ((-22.0, 4.0), (-15.5, 4.5), (-3.0, 5.0), (5.0, 4.0))   # (x, y)
CHIMNEY_SIZE = 0.6
CHIMNEY_HEIGHT = 1.1      # above the turf
OAK = (0.3, 6.5)          # trunk; refs/01 and 03 put it almost over the door
OAK_CROWN = 4.3 * D       # crown diameter, refs/03

# Flagstone steps from the door landing down to the gate: (x, y, top of slab), refs/04, 05.
STEPS = (
    (0.30, -1.3, 0.00),
    (0.60, -2.1, -0.18),
    (1.00, -2.9, -0.40),
    (1.35, -3.7, -0.68),
    (1.70, -4.6, -0.98),
    (2.00, -5.5, -1.15),
    (2.25, -6.4, -1.29),
    (2.45, -7.3, -1.43),
)
GATE = (2.6, -8.2)
BENCH = (-2.6, -2.4)
BIRDHOUSE = (3.7, -1.7)
LAMPS = ((-10.7, -0.7), (-2.7, -1.6))
RACK = (-13.9, -1.0)
```

- [ ] **Step 4: Implement `bagend/terrain.py`**

```python
"""Ground height as a function of plan position, vectorised over numpy arrays."""
import numpy as np

from . import layout as L


def ease(t):
    t = np.clip(t, 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * t)


def ramp(v, a, b):
    return ease((v - a) / (b - a))


def garden(x, y):
    """Lane and lawn in front, the dry-stone wall, then the terrace path along the fronts."""
    lawn = L.LANE_Z + (L.LAWN_Z - L.LANE_Z) * ramp(y, L.LANE_Y, L.WALL_Y)
    return np.where(y < L.WALL_Y, lawn, L.TERRACE_Z) + 0.0 * x


def hill(x, y):
    """The Hill: a crest just behind the facades, swelling over the ornate front, a dome behind."""
    ornate = L.front("ornate")
    crest = L.CREST_Z + L.ORNATE_RISE * np.exp(-(((x - ornate.x) / 5.0) ** 2))
    height = crest + L.TOP_RISE * ramp(y, L.CREST_Y, L.CREST_Y + 5.0)
    ends = ramp(x, L.WEST_X, L.WEST_X + 3.5) * ramp(L.EAST_X - x, 0.0, 3.4)
    front = ramp(y, L.CREST_Y - 2.2, L.CREST_Y)
    back = ramp(L.BACK_Y - y, 0.0, 6.0)
    return height * ends * front * back


# Dig this far behind each facade line, more than one hill grid cell (hill.STEP = 0.15), so the
# mesh's sloped cell lands inside the front's wall mass instead of standing in front of it.
DIG_BEHIND = 0.2


def dig(f, x, y):
    """Ground dug out in front of a front: its floor straight ahead, grass banks either side.

    Beside the front the bank stands about as high as the eave ends and slopes down
    toward the garden (refs/01, 03). From just behind the facade line (DIG_BEHIND) the hill is left alone.
    """
    a = np.radians(f.yaw)
    dx, dy = x - f.x, y - f.y
    u = dx * np.cos(a) + dy * np.sin(a)
    v = -dx * np.sin(a) + dy * np.cos(a)
    du = np.maximum(0.0, np.abs(u) - f.width / 2)
    cheek = f.eave_ends * ramp(du, 0.0, 0.5) * ramp(v, -f.eave_ends / np.tan(np.radians(60)), 0.0)
    z = f.floor + np.tan(np.radians(50)) * du + cheek
    return np.where(v >= DIG_BEHIND, np.inf, z)


def steps_cut(x, y):
    """Lower the ground along the flagstone steps so every slab sits on it."""
    pts = list(L.STEPS) + [(L.GATE[0], L.GATE[1], L.STEPS[-1][2] - 0.1)]
    out = np.full(np.shape(x), np.inf)
    for (x0, y0, z0), (x1, y1, z1) in zip(pts[:-1], pts[1:]):
        sx, sy = x1 - x0, y1 - y0
        t = np.clip(((x - x0) * sx + (y - y0) * sy) / (sx * sx + sy * sy), 0.0, 1.0)
        d = np.hypot(x - (x0 + t * sx), y - (y0 + t * sy))
        z = z0 + t * (z1 - z0) - 0.03 + np.maximum(0.0, d - 0.45) * 3.0
        out = np.minimum(out, z)
    return out


def ground(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = garden(x, y) + hill(x, y)       # the hill rises from the terrace; it is zero over the lawn
    for f in L.FRONTS:
        z = np.minimum(z, dig(f, x, y))
    z = np.minimum(z, steps_cut(x, y))
    return np.maximum(z, L.BASE_Z + 0.3)
```

- [ ] **Step 5: Run and watch them pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_layout test_terrain 2>&1 | grep -E "PASS|FAIL|passed"`
Expected: `10/10 passed`. If `test_turf_covers_every_front` fails, raise that front's local crest
(`CREST_Z` or `ORNATE_RISE`), not the test margin.

---

### Task 3: The landform mesh

**Files:**
- Create: `bagend/hill.py`, `tests/test_hill.py`

**Interfaces:**
- Consumes: `terrain.ground`, `layout` constants, `scene.add_mesh_object`.
- Produces: `hill.build() -> bpy.types.Object` named `hill` in collection `terrain`; `hill.STEP`
  (grid spacing, m).

- [ ] **Step 1: Write the failing test `tests/test_hill.py`**

```python
import bmesh

from bagend import hill, layout as L, scene, terrain


def test_hill_mesh_is_watertight():
    scene.reset_scene()
    obj = hill.build()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        assert all(e.is_manifold for e in bm.edges)
        assert not any(e.is_boundary for e in bm.edges)
    finally:
        bm.free()


def test_hill_top_follows_the_ground_function():
    scene.reset_scene()
    obj = hill.build()
    top = [v.co for v in obj.data.vertices if v.co.z > L.BASE_Z + 0.01]
    for co in top[:: max(1, len(top) // 200)]:
        assert abs(co.z - float(terrain.ground(co.x, co.y))) < 1e-4


def test_no_mesh_cell_slopes_in_front_of_a_facade():
    # The hill's last dug grid row must lie behind every facade, inside the wall mass.
    for f in L.FRONTS:
        for u in (-0.4 * f.width, 0.0, 0.4 * f.width):
            x, y = L.to_world(f, u, hill.STEP + 0.01)
            assert float(terrain.ground(x, y)) <= f.floor + 0.05, (f.name, u)
```

- [ ] **Step 2: Run and watch it fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_hill 2>&1 | grep -E "PASS|FAIL|passed|Error"`
Expected: FAIL with `ImportError: cannot import name 'hill'`

- [ ] **Step 3: Implement `bagend/hill.py`**

```python
"""The hill as one closed mesh: the ground function on a grid, with skirts and a flat bottom."""
import numpy as np

from . import layout as L, scene, terrain

X_RANGE = (L.WEST_X - 2.0, L.EAST_X + 1.5)
Y_RANGE = (L.LANE_Y, L.BACK_Y + 1.0)
STEP = 0.15


def build():
    xs = np.arange(X_RANGE[0], X_RANGE[1] + 1e-9, STEP)
    ys = np.arange(Y_RANGE[0], Y_RANGE[1] + 1e-9, STEP)
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
    return scene.add_mesh_object("hill", verts.tolist(), faces, "terrain")
```

- [ ] **Step 4: Run and watch it pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_hill 2>&1 | grep -E "PASS|FAIL|passed"`
Expected: `3/3 passed`

---

### Task 4: Fronts block-out, and garden, props, chimneys and preview oak

**Files:**
- Create: `bagend/blockout.py`, `bagend/garden.py`, `tests/test_blockout.py`, `tests/test_garden.py`

**Interfaces:**
- Consumes: `layout`, `terrain.ground`, `scene.add_mesh_object`, `scene.collection`.
- Produces:
  - `blockout.build()` creates `front_<name>` and `eave_<name>` (collection `fronts`) plus
    opening markers `door_<front>_<u in cm>` and `window_<front>_<u in cm>` (collection `openings`).
  - `garden.build()` creates `step_<k>`, `wall_west`, `wall_east` (collection `garden`); props
    (`bench`, `birdhouse`, `lamp_<k>`, `gate`, `letterbox`, `rack_rail`, posts) in `props`;
    `chimney_<k>`, `chimney_cap_<k>` in `chimneys`; and `oak_trunk`, `oak_crown` in `preview`.

- [ ] **Step 1: Write the failing tests**

`tests/test_blockout.py`:

```python
import bpy

from bagend import blockout, layout as L, scene


def test_every_front_has_wall_and_eave_at_its_layout_position():
    scene.reset_scene()
    blockout.build()
    for f in L.FRONTS:
        wall = bpy.data.objects[f"front_{f.name}"]
        assert bpy.data.objects.get(f"eave_{f.name}") is not None, f.name
        xs = [(wall.matrix_world @ v.co).x for v in wall.data.vertices]
        assert abs((min(xs) + max(xs)) / 2 - f.x) < 0.1, f.name


def test_door_front_has_door_and_two_portholes():
    scene.reset_scene()
    blockout.build()
    names = [o.name for o in bpy.data.objects]
    assert sum(n.startswith("door_door") for n in names) == 1
    assert sum(n.startswith("window_door") for n in names) == 2
```

`tests/test_garden.py`:

```python
import bpy

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
    scene.reset_scene()
    garden.build()
    for k, (_, _, z) in enumerate(L.STEPS):
        zs = [v.co.z for v in bpy.data.objects[f"step_{k}"].data.vertices]
        assert abs(max(zs) - z) < 1e-6, k
```

- [ ] **Step 2: Run and watch them fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_blockout test_garden 2>&1 | grep -E "PASS|FAIL|passed|Error"`
Expected: FAIL with `ImportError: cannot import name 'blockout'`

- [ ] **Step 3: Implement `bagend/blockout.py`**

```python
"""Milestone 1 block-out: each front as a plain wall mass with its eave and opening markers."""
import math

from . import layout as L, scene

D = L.D
DEPTH = 0.8        # wall mass behind the facade
EAVE_OUT = 0.35    # how far the eave projects
EAVE_THICK = 0.18

# Openings from refs/01, 03, 05, 08-10, heights above the front's floor:
# ("disc", u, z, r), ("door", u, z, r), ("arched", u, z_bottom, width, height)
OPENINGS = {
    "round_window_west": [("disc", 0.0, 0.70 * D, 0.20 * D)],
    "round_window_rack": [("disc", 0.0, 0.72 * D, 0.22 * D)],
    "ornate": [("arched", 0.0, 0.55 * D, 1.2 * D, 0.95 * D), ("disc", -1.9 * D, 0.9 * D, 0.17 * D)],
    "door": [("door", 0.0, 0.05 + D / 2, D / 2),
             ("disc", -0.83 * D, 0.75 * D, 0.115 * D), ("disc", 0.83 * D, 0.75 * D, 0.115 * D)],
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


def build():
    for f in L.FRONTS:
        wall(f)
        eave(f)
        for kind, u, z, *size in OPENINGS[f.name]:
            name = f"{'door' if kind == 'door' else 'window'}_{f.name}_{round(u * 100):+d}"
            if kind == "arched":
                arched(name, f, u, f.floor + z, *size)
            else:
                disc(name, f, u, f.floor + z, size[0])
```

- [ ] **Step 4: Implement `bagend/garden.py`**

```python
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
    for name, x0, x1 in (("wall_west", L.WEST_X, gap[0]), ("wall_east", gap[1], L.EAST_X)):
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
```

- [ ] **Step 5: Run and watch them pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_blockout test_garden 2>&1 | grep -E "PASS|FAIL|passed"`
Expected: `4/4 passed`

---

### Task 5: Materials, light and matched cameras

**Files:**
- Create: `bagend/render.py`, `tests/test_render.py`

**Interfaces:**
- Consumes: object names from Tasks 3–4; `scene.collection`.
- Produces: `render.CAMERAS: dict[name, (location, look_at, lens_mm)]`; `render.setup()` adds
  materials, light and cameras; `render.render_all(out_dir: Path)` writes
  `out_dir/render_<camera>.png`.

- [ ] **Step 1: Write the failing test `tests/test_render.py`**

```python
import bpy
from mathutils import Vector

from bagend import render, scene


def test_every_reference_camera_is_created_with_its_lens():
    scene.reset_scene()
    render.setup()
    for name, (_, _, lens) in render.CAMERAS.items():
        cam = bpy.data.objects[name]
        assert cam.type == "CAMERA" and cam.data.lens == lens


def test_cameras_see_the_whole_hill():
    scene.reset_scene()
    render.setup()
    for name, (loc, target, _) in render.CAMERAS.items():
        reach = (Vector(target) - Vector(loc)).length + 40.0
        assert bpy.data.objects[name].data.clip_end >= reach, name


def test_paint_gives_each_mesh_one_material_by_name_prefix():
    scene.reset_scene()
    cube = ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
            [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    for name in ("chimney_cap_0", "oak_crown", "bench"):
        scene.add_mesh_object(name, *cube, "test")
    render.paint()
    got = {o.name: [m.name for m in o.data.materials] for o in bpy.data.objects}
    assert got == {"chimney_cap_0": ["chimney"], "oak_crown": ["oak_crown"], "bench": ["timber"]}, got
```

- [ ] **Step 2: Run and watch it fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_render 2>&1 | grep -E "PASS|FAIL|passed|Error"`
Expected: FAIL with `ImportError: cannot import name 'render'`

- [ ] **Step 3: Implement `bagend/render.py`**

```python
"""Plain-material Cycles renders from cameras matched to the reference photos."""
import math
from pathlib import Path

import bpy
from mathutils import Vector

from . import scene

# Object name prefix -> base colour (linear RGB). First match wins.
COLOURS = (
    ("hill", (0.20, 0.32, 0.10)),
    ("front_", (0.78, 0.60, 0.28)),
    ("eave_", (0.20, 0.13, 0.08)),
    ("door_", (0.05, 0.30, 0.17)),
    ("window_", (0.04, 0.05, 0.07)),
    ("step_", (0.45, 0.44, 0.40)),
    ("wall_", (0.42, 0.40, 0.36)),
    ("chimney", (0.40, 0.16, 0.10)),
    ("oak_trunk", (0.18, 0.13, 0.08)),
    ("oak_crown", (0.12, 0.25, 0.08)),
)
TIMBER = (0.33, 0.23, 0.14)

# Cameras matched by eye to the reference photos: (location, look-at, focal length in mm).
CAMERAS = {
    "ref09": ((14.0, -60.0, 3.0), (-9.0, 0.0, 1.6), 135),
    "ref10": ((-21.0, -20.0, -2.0), (-12.0, 2.0, 2.6), 50),
    "ref03": ((-0.3, -9.0, -0.3), (1.2, 2.0, 2.0), 24),
    "overview": ((-30.0, -38.0, 22.0), (-8.0, 2.0, 0.0), 40),
}


def material(name, colour):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def paint():
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        name, colour = next(((p, c) for p, c in COLOURS if obj.name.startswith(p)), ("timber", TIMBER))
        obj.data.materials.clear()
        obj.data.materials.append(material(name.rstrip("_"), colour))


def light():
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.80, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    bpy.context.scene.world = world
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 4.0
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-35))
    scene.collection("lights").objects.link(sun)


def add_camera(name, location, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36.0
    data.clip_end = (Vector(target) - Vector(location)).length + 100.0
    cam = bpy.data.objects.new(name, data)
    scene.collection("cameras").objects.link(cam)
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    return cam


def setup():
    paint()
    light()
    for name, (location, target, lens) in CAMERAS.items():
        add_camera(name, location, target, lens)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = 32
    s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = 1400, 930


def render_all(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    s = bpy.context.scene
    for name in CAMERAS:
        s.camera = bpy.data.objects[name]
        s.render.filepath = str(out_dir / f"render_{name}.png")
        bpy.ops.render.render(write_still=True)
```

- [ ] **Step 4: Run and watch it pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_render 2>&1 | grep -E "PASS|FAIL|passed"`
Expected: `3/3 passed`

---

### Task 6: Build entry point, comparison sheets, full run

**Files:**
- Create: `lotr/shire/bag_end/blender/build.py`, `tools/build_bag_end.sh`, `tests/test_build.py`

**Interfaces:**
- Consumes: `scene.reset_scene`, `hill.build`, `blockout.build`, `garden.build`,
  `render.setup`, `render.render_all`, `tools/side_by_side.py`.
- Produces: `build.build_scene()` (importable, used by the test);
  `tools/build_bag_end.sh [--no-render]` writes `bag_end.blend`, `renders/render_*.png` and
  `renders/compare_*.png`.

- [ ] **Step 1: Write the failing test `tests/test_build.py`**

```python
import importlib.util
import pathlib
import re

import bpy

BUILD = pathlib.Path(__file__).resolve().parents[1] / "build.py"


def load_build():
    spec = importlib.util.spec_from_file_location("bag_end_build", BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_twice_gives_one_of_each():
    build = load_build()
    build.build_scene()
    build.build_scene()
    names = [o.name for o in bpy.data.objects]
    assert "hill" in names and "front_door" in names and "oak_crown" in names
    dupes = [n for n in names if re.search(r"\.\d{3}$", n)]
    assert not dupes, dupes
```

- [ ] **Step 2: Run and watch it fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_build 2>&1 | grep -E "PASS|FAIL|passed|Error"`
Expected: FAIL with `FileNotFoundError` for `build.py`

- [ ] **Step 3: Implement `build.py`**

```python
"""Build Bag End: tools/blender.sh lotr/shire/bag_end/blender/build.py [--no-render]

Writes lotr/shire/bag_end/bag_end.blend and renders/render_<camera>.png.
"""
import sys
from pathlib import Path

import bpy

from bagend import blockout, garden, hill, render, scene

OUT = Path(__file__).resolve().parents[1]


def build_scene():
    scene.reset_scene()
    hill.build()
    blockout.build()
    garden.build()
    render.setup()


def main(args):
    build_scene()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bag_end.blend"))
    if "--no-render" not in args:
        render.render_all(OUT / "renders")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
```

Blender runs `--python` scripts with `__name__ == "__main__"`, so the test's import of
`build.py` doesn't trigger a build.

- [ ] **Step 4: Write `tools/build_bag_end.sh`**

```bash
#!/usr/bin/env bash
# Build Bag End in Blender (.blend + renders), then put each render next to its reference photo.
#   tools/build_bag_end.sh [--no-render]
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=lotr/shire/bag_end
tools/blender.sh $DIR/blender/build.py "$@" > /dev/null
for pair in 09_across_valley_ross:ref09 10_from_below_chimneys_ross:ref10 03_front_with_oak_hall:ref03; do
    ref=${pair%%:*}
    cam=${pair##*:}
    if [[ -f $DIR/renders/render_$cam.png ]]; then
        tools/side_by_side.py $DIR/refs/$ref.jpg $DIR/renders/render_$cam.png $DIR/renders/compare_$cam.png
        echo "compare $DIR/renders/compare_$cam.png"
    fi
done
```

Run: `chmod +x tools/build_bag_end.sh`

- [ ] **Step 5: Run the whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py 2>&1 | grep -E "PASS|FAIL|passed"`
Expected: `24/24 passed`

- [ ] **Step 6: Full build and look at it**

Run: `time tools/build_bag_end.sh`
Expected: `bag_end.blend`, `renders/render_{ref09,ref10,ref03,overview}.png` and
`renders/compare_{ref09,ref10,ref03}.png` exist, in a few minutes or less. Open every
comparison sheet and the overview. Fix anything clearly wrong with the layout: a front buried
or floating, the turf not reaching the eaves, steps in the air, a camera pointing at nothing.
Fix it in `layout.py` (data) rather than the builders, and re-run Steps 5–6.

- [ ] **Step 7: Milestone 1 review**

Show Ryan the overview and the three comparison sheets, list what was estimated rather than
measured (chimney and oak depth, the left fronts' sizes), and stop for his corrections.

---

## Later milestones (each gets its own plan after the previous review)

- **M2, door front in full detail:** a `parts.py` of real-geometry pieces (brick arch with
  individual bricks, porthole with brick sill, planked door with nail heads, posts with knee
  braces, curved eave, lantern on bracket), assembled into the door front and rendered against
  refs 01, 02 and the owner's low-angle photo.
- **M3:** the other four fronts from the same parts.
- **M4, garden detail:** worn stone slabs, dry-stone wall, soil beds, real props.
- **M5, print prep:** split the hill along banks, front pockets with 0.2 mm clearance, pins,
  hollowing, HO export, print checks, slicing estimates, then a test print of the door front and
  one hill section.

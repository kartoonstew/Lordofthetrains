# Bag End Milestone 2 (Door Front in Detail) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the door front's block-out with a rustic, fully detailed door front. Fold in
Ryan's milestone 1 layout decisions: the hill compressed to about 30 × 18 cm with every front
true size, a much higher and steeper hill, and thin side and back edges.

**Architecture:** Three pieces are added to the `bagend` package from milestone 1:
- `parts.py`, a library of rustic building parts. These are bmesh builders whose irregularity
  is real geometry: jittered bricks, bowed boards, noise-bent timber, wavy plaster.
- `doorfront.py`, which assembles the door front from those parts in the front's own frame and
  places it where `layout.py` puts it.
- A facet-aware dug-out in `terrain.py`, so the hill clears the door front's angled side
  facets and its deep door recess.

The other four fronts stay block-outs until milestone 3. The code was prototyped and checked
before this plan was written: 53/53 tests pass and a full build takes about a minute. The two
new modules are saved, final, in `docs/superpowers/plans/2026-10-07-bag-end-m2-sources/`.

**Tech Stack:** Blender 5.0.1 (bpy, bmesh, mathutils, bundled numpy 1.26), Cycles, Python 3.11
inside Blender, system Python 3 + Pillow for the comparison sheets.

**Spec:** `docs/superpowers/specs/2026-10-07-bag-end-blender-design.md` (updated with the
milestone 1 decisions: size, steps, detail style, four chimneys, oak pending).

## Global Constraints

- Blender at `/Applications/Blender.app/Contents/MacOS/Blender`, version 5.0 or newer; override
  with `BLENDER=...`. All commands run from the project root,
  `/Users/ryanstewart/App_dev/ho-movie-scenery`.
- Units are real-world metres. Frame: origin at the centre of the door sill, +x left to right
  along the row as seen from the garden, +y back into the hill, +z up. D = 1.57 m.
- Every front stays true size. Only the banks between fronts and the hill's back slope are
  compressed. The model must come to 300–330 × 170–200 mm at 1:87.
- HO scale is applied only at export (milestone 5), never in the model.
- No grass, bushes or ivy geometry; Ryan flocks after printing.
- Rustic detail is geometry, and it is repeatable. Every random choice comes from a seeded
  `random.Random` or seeded `mathutils.noise`, so a rebuild gives identical meshes.
- Detailed parts carry their own materials from `parts.materials()`. `render.paint()` colours
  only objects that have no material yet (the block-outs).
- The door front's objects are named `doorfront_*` and live in the collection `door_front`.
- The oak stays a preview at `layout.OAK` until Ryan's aerial photo arrives. The steps stay as
  they are, winding down to the right.
- The project is not a git repository, so there are no commit steps. The controller takes a
  directory snapshot before each task for review. Never run `git init` or any git command.
- Tests run inside Blender:
  `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py [test_module ...]`. It prints
  one `PASS`/`FAIL` line per test and ends with `N/M passed`.

## Review Focus

- **Rebuilding in one Blender session** (with booleans) must leave no stray `cutter` objects or
  meshes and no `.001` names. Tests: Task 2, `test_bake_cuts_makes_a_real_hole_and_removes_the_cutters`;
  Task 4, `test_build_twice_gives_one_of_each`.
- **The hill must not reach into the door's 0.22 m recess** or cover the portholes on the
  angled side facets. The prototype hit exactly this bug. Tests: Task 3,
  `test_door_and_portholes_can_be_seen_with_the_hill_built`; Task 1,
  `test_door_front_is_dug_out_to_its_recess_depth`.
- **`paint()` must not repaint the detailed door front** with plain block-out colours. Test:
  Task 4, `test_paint_leaves_detailed_parts_their_own_materials`.
- **A door front moved or turned in `layout.py`** must move as one piece, cut-outs included.
  Test: Task 3, `test_door_front_follows_its_layout_placement`.
- **Nothing but the preview oak may stick out past the model's footprint**, which falls to a
  thin edge and is cut there at export. Test: Task 4,
  `test_everything_but_the_preview_oak_fits_on_the_model`.

---

## File structure

```
lotr/shire/bag_end/blender/
  bagend/
    layout.py      MODIFY  compressed positions, Front facets + dig depth, model extents, ridge
    terrain.py     MODIFY  facet-following dug-out, soft blending, ridge, thin edges
    hill.py        MODIFY  grid spans the model exactly; smooth shading
    garden.py      MODIFY  dry-stone wall stops short of the thin edges
    parts.py       CREATE  rustic parts library (copy of the saved source)
    doorfront.py   CREATE  the detailed door front (copy of the saved source)
    blockout.py    MODIFY  build(exclude=...); door openings removed
    render.py      MODIFY  shared colours, paint() skips detailed parts, sky light, cameras
  build.py         MODIFY  door front replaces its block-out
  tests/
    test_layout.py test_terrain.py test_hill.py   REPLACE
    test_garden.py                                 APPEND one test
    test_parts.py test_doorfront.py                CREATE
    test_blockout.py                               REPLACE
    test_render.py test_build.py                   MODIFY
tools/build_bag_end.sh   MODIFY  compare sheets for refs 01 and 02; --no-render skips sheets
lotr/shire/bag_end/README.md, README.md   MODIFY (Task 5)
```

---

### Task 1: Compressed layout, steeper hill, thin edges

**Files:**
- Modify: `lotr/shire/bag_end/blender/bagend/layout.py` (whole file given below)
- Modify: `lotr/shire/bag_end/blender/bagend/terrain.py` (whole file given below)
- Modify: `lotr/shire/bag_end/blender/bagend/hill.py` (whole file given below)
- Modify: `lotr/shire/bag_end/blender/bagend/garden.py:48` (one line)
- Test: `lotr/shire/bag_end/blender/tests/test_layout.py`, `test_terrain.py`, `test_hill.py`
  (replace), `test_garden.py` (append)

**Interfaces:**
- Consumes: milestone 1's `layout`, `terrain`, `hill`, `garden`, `scene`.
- Produces:
  - `layout.Front` gains three fields, all with defaults: `centre: float = 0.0` (half-width of
    a flat centre facet), `wing_angle: float = 0.0` (degrees the facade turns back beyond it),
    and `dig_behind: float = 0.2` (how far behind the facade the ground is dug out). The door
    front has `centre=0.55 * D`, `wing_angle=25.0` and `dig_behind=0.6`.
  - `layout.facade_v(f, u) -> float | ndarray`: how far the facade sits behind the front's line
    at u. It works on scalars and arrays.
  - New constants in `layout`: `RIDGE_Y`, `RIDGE_Z`, `MODEL_X` (a tuple), `BACK_Y`, `EDGE_Z`,
    `EDGE_FALL`, `END_FALL`, `BACK_FALL`. `WEST_X`, `EAST_X` and `TOP_RISE` are removed.
  - In `terrain`: `smin(a, b, k)`, `edge(x, y)` and the constant `BLEND`. `DIG_BEHIND` is
    removed.
  - In `hill`: `axis(lo, hi)`. The hill object is smooth-shaded.

- [ ] **Step 1: Write the failing tests**

Replace `lotr/shire/bag_end/blender/tests/test_layout.py` with:

```python
import math

import numpy as np

from bagend import layout as L


def test_fronts_run_left_to_right_without_overlapping():
    for a, b in zip(L.FRONTS, L.FRONTS[1:]):
        assert a.x + a.width / 2 < b.x - b.width / 2, (a.name, b.name)


def test_door_front_matches_refs_01():
    door = L.front("door")
    assert abs(door.width / L.D - 2.24) < 0.01
    assert abs(door.eave / L.D - 1.39) < 0.01


def test_row_leaves_room_for_the_end_banks():
    first, last = L.FRONTS[0], L.FRONTS[-1]
    left, right = first.x - first.width / 2, last.x + last.width / 2
    assert 24.0 < right - left < 26.5, right - left
    assert left - L.MODEL_X[0] >= 1.2 and L.MODEL_X[1] - right >= 1.2, (left, right)


def test_model_is_about_30_by_18_cm_at_ho():
    width_mm = (L.MODEL_X[1] - L.MODEL_X[0]) * 1000 / 87
    depth_mm = (L.BACK_Y - L.LANE_Y) * 1000 / 87
    assert 300 <= width_mm <= 330, width_mm
    assert 170 <= depth_mm <= 200, depth_mm


def test_facade_recedes_only_beyond_the_centre_facet():
    door = L.front("door")
    assert L.facade_v(door, 0.0) == 0.0 and L.facade_v(door, -door.centre) == 0.0
    for u in (door.centre + 1.0, -door.centre - 1.0):
        assert abs(L.facade_v(door, u) - math.tan(math.radians(door.wing_angle))) < 1e-9
    us = np.linspace(-2.0, 2.0, 9)
    assert L.facade_v(door, us).shape == us.shape
    assert np.allclose(L.facade_v(L.front("ornate"), us), 0.0)


def test_hill_top_items_stand_on_the_model_away_from_its_thin_edges():
    for x, y in L.CHIMNEYS + (L.OAK,):
        assert y > 2.0, (x, y)
        assert L.MODEL_X[0] + L.EDGE_FALL < x < L.MODEL_X[1] - L.EDGE_FALL, (x, y)
        assert y < L.BACK_Y - L.EDGE_FALL, (x, y)


def test_steps_descend_from_door_to_gate():
    zs = [z for _, _, z in L.STEPS]
    assert zs[0] == L.TERRACE_Z
    assert all(a > b for a, b in zip(zs, zs[1:]))
```

Replace `lotr/shire/bag_end/blender/tests/test_terrain.py` with:

```python
import numpy as np

from bagend import layout as L, terrain


def g(x, y):
    return float(terrain.ground(x, y))


def test_door_landing_is_level():
    for u in (-0.6, 0.0, 0.6):
        assert abs(g(u, -0.8) - L.TERRACE_Z) < 0.05, u


def test_turf_covers_every_front():
    # Sampled just behind each front's dug-out, which follows its facade (side facets included).
    for f in L.FRONTS:
        for u in np.linspace(-f.width / 2, f.width / 2, 9):
            for behind in (0.2, 0.6, 1.0):
                v = float(L.facade_v(f, u)) + f.dig_behind + behind
                x, y = L.to_world(f, u, v)
                need = f.floor + L.eave_top(f, u) + 0.15
                assert g(x, y) >= need, (f.name, round(u, 2), round(v, 2), g(x, y), need)


def test_ground_is_dug_out_in_front_of_every_front():
    for f in L.FRONTS:
        for u in np.linspace(-0.95 * f.width / 2, 0.95 * f.width / 2, 7):
            x, y = L.to_world(f, u, float(L.facade_v(f, u)) - 0.05)
            assert g(x, y) <= f.floor + 0.05, (f.name, round(u, 2), g(x, y))


def test_door_front_is_dug_out_to_its_recess_depth():
    # The door sits 0.22 m back in its ring; the hill must not reach into that recess.
    door = L.front("door")
    for u in np.linspace(-0.9 * door.width / 2, 0.9 * door.width / 2, 7):
        x, y = L.to_world(door, u, float(L.facade_v(door, u)) + door.dig_behind - 0.05)
        assert g(x, y) <= door.floor + 0.05, (round(u, 2), g(x, y))


def test_terrace_path_stays_level_along_the_row():
    # A dug-out's floor meeting the level path is no crease: blending must not sink the path.
    for y in (-3.4, -2.5, -1.7):
        for x in np.linspace(L.MODEL_X[0] + L.EDGE_FALL, L.MODEL_X[1] - L.EDGE_FALL, 200):
            if min(np.hypot(x - sx, y - sy) for sx, sy, _ in L.STEPS) < 1.2:
                continue                                   # the steps are cut lower
            assert abs(g(x, y) - L.TERRACE_Z) < 0.01, (round(x, 2), y, g(x, y))


def test_smin_rounds_only_near_crossings():
    a = np.zeros(4)
    b = np.array([2.0, 0.2, 0.0, np.inf])
    z = terrain.smin(a, b, 0.5)
    assert z[0] == 0.0 and z[3] == 0.0           # far apart, or dug-out not reaching: plain minimum
    assert z[2] == -0.125 and -0.125 < z[1] < 0.0  # near a crossing: rounded, by at most k / 4
    assert np.all(z <= np.minimum(a, b))


def test_hill_climbs_to_its_top_behind_the_fronts():
    door = L.front("door")
    top = g(*L.OAK)
    assert top >= L.RIDGE_Z - 0.3, top
    assert top > 2 * (door.floor + door.eave), top          # refs/09: the hill towers over the row


def test_sides_and_back_fall_to_a_thin_edge():
    for y in np.linspace(L.LANE_Y, L.BACK_Y, 9):
        for x in L.MODEL_X:
            assert abs(g(x, y) - L.EDGE_Z) < 1e-9, (x, y, g(x, y))
    for x in np.linspace(*L.MODEL_X, 9):
        assert abs(g(x, L.BACK_Y) - L.EDGE_Z) < 1e-9, (x, g(x, L.BACK_Y))
    assert (L.EDGE_Z - L.BASE_Z) * 1000 / 87 < 4.0           # the edge is under 4 mm thick at HO


def test_no_step_is_buried():
    for x, y, z in L.STEPS:
        assert g(x, y) <= z + 0.01, (x, y, z, g(x, y))


def test_lawn_falls_from_the_wall_to_the_lane():
    assert abs(g(-10.0, L.WALL_Y - 0.01) - L.LAWN_Z) < 0.05
    assert abs(g(-10.0, L.LANE_Y) - L.LANE_Z) < 0.05
```

Replace `lotr/shire/bag_end/blender/tests/test_hill.py` with:

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
    assert top
    for co in top[:: max(1, len(top) // 200)]:
        assert abs(co.z - float(terrain.ground(co.x, co.y))) < 1e-4


def test_hill_covers_the_model_footprint_exactly():
    scene.reset_scene()
    obj = hill.build()
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    assert abs(min(xs) - L.MODEL_X[0]) < 1e-4 and abs(max(xs) - L.MODEL_X[1]) < 1e-4, (min(xs), max(xs))
    assert abs(min(ys) - L.LANE_Y) < 1e-4 and abs(max(ys) - L.BACK_Y) < 1e-4, (min(ys), max(ys))


def test_hill_is_about_30_by_18_cm_at_ho_and_under_11_cm_tall():
    scene.reset_scene()
    obj = hill.build()
    size = [(max(v.co[i] for v in obj.data.vertices) - min(v.co[i] for v in obj.data.vertices)) * 1000 / 87
            for i in range(3)]
    assert 300 <= size[0] <= 330 and 170 <= size[1] <= 200 and size[2] < 110, size


def test_no_mesh_cell_slopes_in_front_of_a_facade():
    # The hill's last dug grid row must lie behind every facade, inside the wall mass.
    for f in L.FRONTS:
        for u in (-0.4 * f.width, 0.0, 0.4 * f.width):
            x, y = L.to_world(f, u, float(L.facade_v(f, u)) + hill.STEP + 0.01)
            assert float(terrain.ground(x, y)) <= f.floor + 0.05, (f.name, u)


def test_hill_is_shaded_smooth():
    scene.reset_scene()
    obj = hill.build()
    assert all(p.use_smooth for p in obj.data.polygons)
```

Append to `lotr/shire/bag_end/blender/tests/test_garden.py`:

```python


def test_dry_stone_wall_stops_short_of_the_thin_edges():
    scene.reset_scene()
    garden.build()
    xs = [v.co.x for n in ("wall_west", "wall_east") for v in bpy.data.objects[n].data.vertices]
    assert min(xs) >= L.MODEL_X[0] + L.EDGE_FALL - 1e-6, min(xs)
    assert max(xs) <= L.MODEL_X[1] - L.EDGE_FALL + 1e-6, max(xs)
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_layout test_terrain test_hill test_garden`
Expected: several FAILs with `AttributeError` (`MODEL_X`, `facade_v`, `smin`, `RIDGE_Z`), and
an exit code of 1.

- [ ] **Step 3: Implement**

Replace `lotr/shire/bag_end/blender/bagend/layout.py` with:

```python
"""Where everything on Bag End goes, in metres, measured from the reference photos.

Frame: origin at the centre of the door sill. +x runs left to right along the row as seen
from the garden, +y goes back into the hill, +z is up. D is the door diameter; most sizes
are multiples of it, measured in refs/01, 03, 09 and 10.
"""
import math
from dataclasses import dataclass

import numpy as np

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
    centre: float = 0.0       # half-width of a flat centre facet; 0 means the facade is flat
    wing_angle: float = 0.0   # degrees the facade turns back into the hill beyond the centre facet
    dig_behind: float = 0.2   # the ground is dug out to this far behind the facade


# Each front is true HO size; the grass banks between them are shortened so the whole hill
# comes to about 30 x 18 cm at 1:87 (decided with the owner in milestone 1).
FRONTS = (
    Front("round_window_west", -12.08 * D, 0.0, 1.6 * D, 0.0, 1.25 * D, 1.05 * D),
    Front("round_window_rack", -9.69 * D, 0.0, 1.9 * D, 0.0, 1.30 * D, 1.10 * D),
    Front("ornate", -4.9 * D, 0.0, 4.75 * D, 0.0, 2.35 * D, 1.30 * D, arch=1.25 * D),
    Front("door", 0.0, 0.0, 2.24 * D, 0.0, 1.39 * D, 1.15 * D,
          centre=0.55 * D, wing_angle=25.0, dig_behind=0.6),
    Front("lattice_window", 2.53 * D, 0.4, 1.3 * D, 0.45, 1.25 * D, 1.05 * D, yaw=-5.0),
)


def front(name):
    return next(f for f in FRONTS if f.name == name)


def eave_top(f, u):
    """Eave top above the front's floor, at distance u along it from its centre."""
    half = f.arch or f.width / 2
    t = max(0.0, 1.0 - (u / half) ** 2)
    return f.eave_ends + (f.eave - f.eave_ends) * math.sqrt(t)


def facade_v(f, u):
    """How far the facade sits behind the front's line at u: zero on the centre facet, then
    receding at wing_angle (the door front's side facets turn back into the hill)."""
    if not f.centre:
        return 0.0 * u
    return np.maximum(0.0, np.abs(u) - f.centre) * math.tan(math.radians(f.wing_angle))


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

# Hill, refs/03, 09: a bank over the fronts, then a steep climb to the hill top behind
CREST_Y = 0.6             # bank top, just behind the facades...
CREST_Z = 1.75 * D        # ...above the door sill, refs/03
RIDGE_Y = 4.5             # the hill top, where the oak stands...
RIDGE_Z = 5.4             # ...about two and a half door-front heights above the path, refs/09
ORNATE_RISE = 1.2         # the hill swells higher over the ornate front, refs/09

# The model: about 30 x 18 cm at 1:87. Its sides and back fall to a thin edge.
MODEL_X = (-21.5, 6.5)
BACK_Y = 7.6
BASE_Z = -2.4             # underside of the model
EDGE_Z = BASE_Z + 0.3     # ground height at the side and back edges
EDGE_FALL = 1.2           # the ground falls to EDGE_Z over this distance from those edges
END_FALL = 2.0            # the hill's ends fall away over this distance inside the sides
BACK_FALL = 2.8           # and its back over this distance

# Hill top, refs/03, 09, 10
CHIMNEYS = ((-18.4, 3.6), (-13.5, 4.0), (-3.0, 4.2), (4.6, 3.4))   # (x, y)
CHIMNEY_SIZE = 0.6
CHIMNEY_HEIGHT = 1.1      # above the turf
OAK = (0.3, 4.6)          # trunk; refs/01 and 03 put it almost over the door
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
BIRDHOUSE = (3.3, -1.7)
LAMPS = ((-10.7, -0.7), (-2.7, -1.6))
RACK = (-12.6, -1.0)
```

Replace `lotr/shire/bag_end/blender/bagend/terrain.py` with:

```python
"""Ground height as a function of plan position, vectorised over numpy arrays."""
import numpy as np

from . import layout as L


def ease(t):
    t = np.clip(t, 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * t)


def ramp(v, a, b):
    return ease((v - a) / (b - a))


def smin(a, b, k):
    """Minimum with the crease rounded over about k, so banks meet in soft hollows, not sharp V's."""
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k / 4


def garden(x, y):
    """Lane and lawn in front, the dry-stone wall, then the terrace path along the fronts."""
    lawn = L.LANE_Z + (L.LAWN_Z - L.LANE_Z) * ramp(y, L.LANE_Y, L.WALL_Y)
    return np.where(y < L.WALL_Y, lawn, L.TERRACE_Z) + 0.0 * x


def hill(x, y):
    """The Hill: a bank over the fronts, then a steep climb to the top, swelling over the ornate front."""
    ornate = L.front("ornate")
    swell = L.ORNATE_RISE * np.exp(-(((x - ornate.x) / 5.0) ** 2))
    height = L.CREST_Z + swell + (L.RIDGE_Z - L.CREST_Z) * ramp(y, L.CREST_Y, L.RIDGE_Y)
    front = ramp(y, L.CREST_Y - 2.2, L.CREST_Y)
    ends = ramp(x, L.MODEL_X[0], L.MODEL_X[0] + L.END_FALL) * ramp(L.MODEL_X[1] - x, 0.0, L.END_FALL)
    back = ramp(L.BACK_Y - y, 0.0, L.BACK_FALL)
    return height * front * ends * back


def dig(f, x, y):
    """Ground dug out in front of a front: its floor straight ahead, grass banks either side.

    Beside the front the bank stands about as high as the eave ends and slopes down toward the
    garden (refs/01, 03). The dug floor follows the facade, side facets included, and runs on
    f.dig_behind past it, more than one hill grid cell (hill.STEP = 0.15), so the mesh's sloped
    cell lands inside the front's wall mass instead of standing in front of it.
    """
    a = np.radians(f.yaw)
    dx, dy = x - f.x, y - f.y
    u = dx * np.cos(a) + dy * np.sin(a)
    v = -dx * np.sin(a) + dy * np.cos(a) - L.facade_v(f, u)
    du = np.maximum(0.0, np.abs(u) - f.width / 2)
    cheek = f.eave_ends * ramp(du, 0.0, 0.5) * ramp(v, -f.eave_ends / np.tan(np.radians(60)), 0.0)
    z = f.floor + np.tan(np.radians(50)) * du + cheek
    return np.where(v >= f.dig_behind, np.inf, z)


def edge(x, y):
    """1 inside the model, easing to 0 at its sides and back, where the ground falls to a thin edge."""
    return (ramp(x, L.MODEL_X[0], L.MODEL_X[0] + L.EDGE_FALL) * ramp(L.MODEL_X[1] - x, 0.0, L.EDGE_FALL)
            * ramp(L.BACK_Y - y, 0.0, L.EDGE_FALL))


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


BLEND = 0.5   # how softly each dug-out meets the hill and the next one


def ground(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = garden(x, y) + hill(x, y)       # the hill rises from the terrace; it is zero over the lawn
    for f in L.FRONTS:
        d = dig(f, x, y)
        # Round the crease where a dug-out cuts into the hill, but never below the front's floor:
        # where the dug floor meets level ground (the terrace path) there is no crease to round.
        z = np.maximum(smin(z, d, BLEND), np.minimum(np.minimum(z, d), f.floor))
    z = np.minimum(z, steps_cut(x, y))
    z = L.EDGE_Z + (z - L.EDGE_Z) * edge(x, y)
    return np.maximum(z, L.EDGE_Z)
```

Replace `lotr/shire/bag_end/blender/bagend/hill.py` with:

```python
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
    obj.data.shade_smooth()     # render only: hides the grid's facets on steep banks
    return obj
```

In `lotr/shire/bag_end/blender/bagend/garden.py`, function `wall()`, replace the line

```python
    for name, x0, x1 in (("wall_west", L.WEST_X, gap[0]), ("wall_east", gap[1], L.EAST_X)):
```

with

```python
    for name, x0, x1 in (("wall_west", L.MODEL_X[0] + L.EDGE_FALL, gap[0]),
                         ("wall_east", gap[1], L.MODEL_X[1] - L.EDGE_FALL)):
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_layout test_terrain test_hill test_garden`
Expected: `26/26 passed`.

- [ ] **Step 5: Run the whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `36/36 passed`. The milestone 1 block-out, render and build tests still pass on the
new layout.

- [ ] **Step 6: Report** (no commit; the controller snapshots the tree)

---

### Task 2: Rustic parts library

**Files:**
- Create: `lotr/shire/bag_end/blender/bagend/parts.py`, as a byte-for-byte copy of
  `docs/superpowers/plans/2026-10-07-bag-end-m2-sources/parts.py`
- Test: `lotr/shire/bag_end/blender/tests/test_parts.py` (create)

**Interfaces:**
- Consumes: `scene.collection(name)` from milestone 1.
- Produces (all in `bagend.parts`):
  - Colours `PLASTER`, `BRICK`, `STONE`, `TURF` (linear RGB tuples).
  - `materials() -> dict[str, bpy.types.Material]`, with keys `plaster`, `brick`, `timber`,
    `ring`, `door`, `iron`, `brass`, `glass`, `green_paint`, `stone`, `terracotta` and
    `turf`. Each material is made once per scene.
  - Mesh plumbing:
    - `to_object(name, bm, mat | None, coll, matrix=None, bevel=0.0, segments=2) -> Object`
      (frees bm)
    - `bevel_sharp(bm, offset, segments=2, angle=0.6)`, which updates normals first, so it
      also works on faces made with `bm.faces.new`
    - `wobble(verts, amp, scale, seed)`
    - `new_verts(bm, build) -> list`
    - `hexa(bm, front4, back4)`
    - `box(bm, centre, size, rot=None) -> verts`
    - `timber(bm, centre, size, rot=None, amp=0.008, seed=0, cuts=6)`
    - `extrude(bm, outline_uz, v0, v1) -> verts`
    - `disc(bm, cu, cz, r, v0, v1, seg=48)`
    - `arc_block(...)`
    - `bake_cuts(obj, cutters)`, which also deletes the cutter objects and their meshes and
      keeps the object's mesh name
    - `cylinder_cutter(cu, cz, r, v0, v1, coll, matrix=None) -> Object`
  - Parts:
    - `plaster_slab(bm, u0, u1, z0, top, depth, seed, step=0.03, amp=0.012)`
    - `crescent_bricks(bm, cu, cz, r_in, r_out, lift, pitch, z_min, rng, ...)`
    - `brick_row(bm, cu, cz, count, width, height, proud, rng, gap=0.012)`
    - `plank_door(bm, cz, r, front_v, depth, rng, seed)`
    - `door_nails(bm, cz, r, front_v, rng)`
    - `segmented_ring(bm, cu, cz, r_in, r_out, v0, v1, segments, rng, seed, gap=0.012)`
    - `header_band(bm, us, eave, panels, seed, ...)`
    - `eave_hood(bm_fascia, bm_soffit, us, eave, out, rng, seed)`
    - `knee_brace(bm, u, z_top, seed, ...)`: a solid corner bracket with a curved underside
    - `lantern(bm_iron, bm_glass, u, z_hang, v=-0.13)`
    - `leaded_glass(bm_glass, bm_came, cu, cz, r, v)`
    - `rough_stone(bm, centre, size, rng, seed, amp=0.012)`
    - `pot(name, mat, coll, matrix) -> Object`
    - `sod(bm, us, eave, v0, v1)`
  - All of these work in a front-local frame: u along the facade, v into the wall (the viewer
    is at −v), z up.

- [ ] **Step 1: Write the failing test**

Create `lotr/shire/bag_end/blender/tests/test_parts.py`:

```python
import math
import random

import bmesh
import bpy
from mathutils import Vector

from bagend import parts as P, scene


def is_closed(obj):
    """Manifold, no holes, and normals pointing out (positive volume)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        return (all(e.is_manifold for e in bm.edges) and not any(e.is_boundary for e in bm.edges)
                and bm.calc_volume(signed=True) > 0)
    finally:
        bm.free()


def test_materials_are_made_once_per_scene():
    scene.reset_scene()
    first = P.materials()
    nodes = {name: len(m.node_tree.nodes) for name, m in first.items()}
    second = P.materials()
    assert {"plaster", "brick", "timber", "ring", "door", "glass", "stone", "turf"} <= set(first)
    assert all(first[k] is second[k] for k in first)
    assert nodes == {name: len(m.node_tree.nodes) for name, m in second.items()}


def test_wobble_is_repeatable_per_seed_and_small():
    def timber(seed):
        bm = bmesh.new()
        P.timber(bm, (0.0, 0.0, 0.0), (0.12, 0.12, 2.0), seed=seed)
        out = [tuple(v.co) for v in bm.verts]
        bm.free()
        return out
    a = timber(3)
    assert a == timber(3) and a != timber(4)
    assert all(abs(x) <= 0.06 + 0.016 and abs(z) <= 1.0 + 0.016 for x, _, z in a)


def test_timber_and_plaster_come_out_as_closed_solids():
    scene.reset_scene()
    bm = bmesh.new()
    P.timber(bm, (0.0, 0.0, 1.0), (0.12, 0.12, 2.0), seed=1)
    assert is_closed(P.to_object("post", bm, None, "test", bevel=0.012))
    bm = bmesh.new()
    P.plaster_slab(bm, -0.5, 0.5, 0.0, lambda u: 1.0 + 0.2 * math.cos(3 * u), 0.8, seed=2)
    assert is_closed(P.to_object("slab", bm, None, "test"))


def test_bevel_rounds_the_edges_of_solids_built_face_by_face():
    # Faces made with bm.faces.new carry no normals until updated; the bevel must still find edges.
    scene.reset_scene()
    counts = []
    for bevel in (0.0, 0.01):
        bm = bmesh.new()
        P.extrude(bm, [(0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2)], 0.0, 0.2)
        obj = P.to_object(f"prism_{bevel}", bm, None, "test", bevel=bevel)
        assert is_closed(obj), bevel
        counts.append(len(obj.data.vertices))
    assert counts[1] > counts[0], counts


def test_knee_brace_is_a_closed_solid_even_when_bevelled():
    scene.reset_scene()
    bm = bmesh.new()
    P.knee_brace(bm, 0.0, 2.0, seed=3)
    assert is_closed(P.to_object("brace", bm, None, "test", bevel=0.012))


def test_plaster_meets_its_eave_line_and_bulges_only_outward():
    def top(u):
        return 1.0 + 0.2 * math.cos(3 * u)
    bm = bmesh.new()
    P.plaster_slab(bm, -0.5, 0.5, 0.0, top, 0.8, seed=2, amp=0.012)
    for v in bm.verts:
        assert v.co.z <= top(v.co.x) + 1e-6
        assert -0.012 - 1e-6 <= v.co.y <= 0.8 + 1e-6
    assert sum(abs(v.co.z - top(v.co.x)) < 1e-6 for v in bm.verts) >= 2 * 34   # whole top row
    bm.free()


def test_arch_bricks_sit_between_the_circles_and_thicken_at_the_crown():
    r_in, r_out, lift = 0.87, 0.98, 0.10
    bm = bmesh.new()
    P.crescent_bricks(bm, 0.0, 0.0, r_in, r_out, lift, 0.065, -0.4, random.Random(1))
    radial = [(math.hypot(v.co.x, v.co.z), v.co.z) for v in bm.verts]
    assert radial
    assert min(r for r, _ in radial) >= r_in - 0.01
    assert max(r for r, _ in radial) <= r_out + lift + 0.01
    crown = max(r for r, z in radial if z > 0.9 * r)
    side = max(r for r, z in radial if abs(z) < 0.1 * r)
    assert crown - side > 0.05, (crown, side)
    assert min(z for _, z in radial) >= -0.4 - 1e-9
    bm.free()


def test_door_boards_stay_inside_the_doorway():
    r, cz, front = 0.78, 0.84, 0.22
    bm = bmesh.new()
    P.plank_door(bm, cz, r, front, 0.06, random.Random(1), 7)
    assert len(bm.verts) > 0
    for v in bm.verts:
        assert math.hypot(v.co.x, v.co.z - cz) <= r + 0.006, tuple(v.co)
        assert front - 0.02 <= v.co.y <= front + 0.06 + 1e-6, tuple(v.co)
    bm.free()


def test_bake_cuts_makes_a_real_hole_and_removes_the_cutters():
    scene.reset_scene()
    bm = bmesh.new()
    P.box(bm, (0.0, 0.4, 1.0), (2.0, 0.8, 2.0))
    slab = P.to_object("slab", bm, None, "test")
    P.bake_cuts(slab, [P.cylinder_cutter(0.0, 1.0, 0.3, -0.5, 1.5, "test")])
    assert not slab.modifiers and slab.data.name == "slab"
    assert [o.name for o in bpy.data.objects] == ["slab"]
    assert not [m.name for m in bpy.data.meshes if m.name.startswith("cutter")]
    dg = bpy.context.evaluated_depsgraph_get()
    through, *_ = bpy.context.scene.ray_cast(dg, Vector((0.0, -1.0, 1.0)), Vector((0.0, 1.0, 0.0)))
    beside, *_ = bpy.context.scene.ray_cast(dg, Vector((0.6, -1.0, 1.0)), Vector((0.0, 1.0, 0.0)))
    assert not through and beside
```

- [ ] **Step 2: Run the test to make sure it fails**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_parts`
Expected: the module fails to import (`ImportError: cannot import name 'parts'`), so the run
aborts with a traceback and exit code 1.

- [ ] **Step 3: Implement**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m2-sources/parts.py lotr/shire/bag_end/blender/bagend/parts.py
```

Read the copied file through once, so the report can describe what each part makes. Do not
change it: any finding goes in the report as a concern.

- [ ] **Step 4: Run the test to make sure it passes**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_parts`
Expected: `9/9 passed`.

- [ ] **Step 5: Run the whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `45/45 passed`.

- [ ] **Step 6: Report** (no commit; the controller snapshots the tree)

---

### Task 3: The detailed door front

**Files:**
- Create: `lotr/shire/bag_end/blender/bagend/doorfront.py`, as a byte-for-byte copy of
  `docs/superpowers/plans/2026-10-07-bag-end-m2-sources/doorfront.py`
- Test: `lotr/shire/bag_end/blender/tests/test_doorfront.py` (create)

**Interfaces:**
- Consumes:
  - From Task 1: `layout.front("door")` with `centre`, `wing_angle`, `x`, `y`, `floor`, `yaw`.
    The door front reads its facet geometry from these, so layout.py stays the single source.
  - From Task 2: `parts` (all of it).
  - From milestone 1: `hill.build()`, used in the tests.
- Produces (in `bagend.doorfront`):
  - `build(seed=7) -> list[Object]`: everything in the collection `door_front`, named
    `doorfront_*`, for example `doorfront_wall_centre`, `doorfront_door_boards`,
    `doorfront_door_arch` and `doorfront_left_porthole_glass`. Each object has one material.
  - `placement() -> Matrix`: the front frame to world, read from `layout` at call time.
  - `side_matrix(sign) -> Matrix`.
  - Constants `CZ`, `R_DOOR`, `S`, `P_CZ`, `REVEAL`, `C`, `PHI`.
  - The brick arch is `crescent_bricks(..., 0.98, 0.10, 0.065, ...)`: thicker at the sides
    and with smaller bricks than the first prototype, to match refs/02.

- [ ] **Step 1: Write the failing test**

Create `lotr/shire/bag_end/blender/tests/test_doorfront.py`:

```python
import dataclasses

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

from bagend import doorfront as DF, hill, layout as L, scene


def first_hit(origin, target):
    dg = bpy.context.evaluated_depsgraph_get()
    o, t = Vector(origin), Vector(target)
    hit, _, _, _, obj, _ = bpy.context.scene.ray_cast(dg, o, (t - o).normalized())
    return obj.name if hit else None


def test_every_part_is_named_and_has_one_material():
    scene.reset_scene()
    objs = DF.build()
    assert len(objs) > 30
    for o in objs:
        assert o.name.startswith("doorfront_"), o.name
        assert len(o.data.materials) == 1, o.name
    assert not [o.name for o in bpy.data.objects if not o.name.startswith("doorfront_")]


def test_door_and_portholes_can_be_seen_with_the_hill_built():
    # The prototype's hill reached into the door's recess and hid its lower half.
    scene.reset_scene()
    hill.build()
    DF.build()
    for dz in (-0.6, 0.0, 0.6):
        z = DF.CZ + dz * DF.R_DOOR
        name = first_hit((0.1, -4.0, z), (0.1, 0.0, z))
        assert name and name.startswith("doorfront_door"), (dz, name)
    place = DF.placement()
    for s in (-1, 1):
        facet = place @ DF.side_matrix(s)
        centre = facet @ Vector((DF.S / 2, 0.0, DF.P_CZ))
        out = facet.to_3x3() @ Vector((0.0, -1.0, 0.0))
        name = first_hit(centre + 3.0 * out.normalized(), centre)
        assert name and "porthole" in name, (s, name)


def test_door_front_follows_its_layout_placement():
    # Every part, its boolean cut-outs included, must move with the front as one piece.
    def world_points():
        return {o.name: [o.matrix_world @ v.co for v in o.data.vertices] for o in DF.build()}

    scene.reset_scene()
    before, old = world_points(), DF.placement()
    door = L.front("door")
    moved = dataclasses.replace(door, x=door.x + 5.0, y=door.y + 1.0, floor=door.floor + 0.3, yaw=10.0)
    saved = L.FRONTS
    L.FRONTS = tuple(moved if f is door else f for f in saved)
    try:
        scene.reset_scene()
        after, shift = world_points(), DF.placement() @ old.inverted()
    finally:
        L.FRONTS = saved
    assert after.keys() == before.keys()
    for name, pts in before.items():
        assert len(after[name]) == len(pts), name
        tree = KDTree(len(pts))                 # vertex order may differ between builds; match by position
        for i, p in enumerate(after[name]):
            tree.insert(p, i)
        tree.balance()
        worst = max(tree.find(shift @ p)[2] for p in pts)
        assert worst < 1e-4, (name, worst)


def test_door_front_is_repeatable():
    def arch():
        scene.reset_scene()
        DF.build(seed=7)
        return [tuple(round(c, 6) for c in v.co) for v in bpy.data.objects["doorfront_door_arch"].data.vertices]
    assert arch() == arch()
```

- [ ] **Step 2: Run the test to make sure it fails**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_doorfront`
Expected: an import failure for `doorfront` and exit code 1.

- [ ] **Step 3: Implement**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m2-sources/doorfront.py lotr/shire/bag_end/blender/bagend/doorfront.py
```

Do not change it: any finding goes in the report as a concern.

- [ ] **Step 4: Run the test to make sure it passes**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_doorfront`
Expected: `4/4 passed`.

- [ ] **Step 5: Run the whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `49/49 passed`.

- [ ] **Step 6: Report** (no commit; the controller snapshots the tree)

---

### Task 4: Build integration, render look and cameras

**Files:**
- Modify: `lotr/shire/bag_end/blender/bagend/blockout.py` (module docstring, `OPENINGS`,
  `build`)
- Modify: `lotr/shire/bag_end/blender/build.py` (import, `build_scene`)
- Modify: `lotr/shire/bag_end/blender/bagend/render.py` (import, `COLOURS`, the `CAMERAS`
  comment and dict, `paint`, `light`)
- Modify: `tools/build_bag_end.sh` (whole file given below)
- Test: `tests/test_blockout.py` (replace), `tests/test_render.py` and `tests/test_build.py`
  (modify)

**Interfaces:**
- Consumes: from Task 1, `layout.MODEL_X`, `LANE_Y` and `BACK_Y`. From Task 2,
  `parts.PLASTER`, `STONE`, `BRICK` and `TURF`. From Task 3, `doorfront.build()`.
- Produces:
  - `blockout.build(exclude=())`, which blocks out every front except those named.
  - `build.build_scene()`, which now builds hill → block-outs except the door → door front →
    garden → render setup.
  - `render.CAMERAS` gains `ref01` and `ref02`. `ref09`, `ref10` and `overview` are
    re-aimed at the compressed hill.
  - `render.paint()` skips objects that already have a material.
  - `render.light()` sets up a sky texture, the Standard view transform and exposure −2.4.

- [ ] **Step 1: Write the failing tests**

Replace `lotr/shire/bag_end/blender/tests/test_blockout.py` with:

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


def test_fronts_built_in_detail_are_left_out():
    scene.reset_scene()
    blockout.build(exclude=("door",))
    names = [o.name for o in bpy.data.objects]
    assert not [n for n in names if "door" in n], names
    assert "front_ornate" in names and "window_lattice_window_+0" in names
```

In `lotr/shire/bag_end/blender/tests/test_render.py`:

- Add this module-level constant after the imports:

```python
CUBE = ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
        [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
```

- Change the import line to `from bagend import parts, render, scene`.
- In `test_paint_gives_each_mesh_one_material_by_name_prefix`, delete the local `cube = (...)`
  assignment, use `*CUBE` in place of `*cube`, and make the expected names `plain_*`:

```python
    assert got == {"chimney_cap_0": ["plain_chimney"], "oak_crown": ["plain_oak_crown"], "bench": ["plain_timber"]}, got
```
- In `test_every_reference_camera_is_created_with_its_lens`, add this as the first line after
  `render.setup()`:

```python
    assert {"ref01", "ref02", "ref03", "ref09", "ref10"} <= set(render.CAMERAS)
```

- Append:

```python


def test_paint_leaves_detailed_parts_their_own_materials():
    scene.reset_scene()
    obj = scene.add_mesh_object("doorfront_wall_centre", *CUBE, "test")
    obj.data.materials.append(bpy.data.materials.new("plaster"))
    render.paint()
    assert [m.name for m in obj.data.materials] == ["plaster"]


def test_light_is_a_sky_rendered_in_plain_colours():
    scene.reset_scene()
    render.setup()
    s = bpy.context.scene
    nodes = s.world.node_tree.nodes
    assert any(n.type == "TEX_SKY" for n in nodes)
    assert nodes["Background"].inputs["Color"].is_linked
    assert s.view_settings.view_transform == "Standard"


def test_paint_never_reuses_a_detailed_part_material():
    # Garden props fall back to plain timber; the door front's "timber" must stay its own.
    scene.reset_scene()
    detailed = parts.materials()["timber"]
    bench = scene.add_mesh_object("bench", *CUBE, "test")
    render.paint()
    assert bench.data.materials[0] is not detailed
    assert detailed.node_tree.nodes["Principled BSDF"].inputs["Base Color"].is_linked
```

In `lotr/shire/bag_end/blender/tests/test_build.py`:

- Add these imports after `import bpy`:

```python
import numpy as np

from bagend import layout as L
```

- In `test_build_twice_gives_one_of_each`, replace the lines from `assert "hill" in names ...`
  to the end of the function with:

```python
    assert "hill" in names and "doorfront_door_boards" in names and "oak_crown" in names
    assert "front_door" not in names
    dupes = [n for n in names if re.search(r"\.\d{3}$", n)]
    assert not dupes, dupes
    assert not [m.name for m in bpy.data.meshes if m.name.startswith("cutter")]
```

- Append:

```python


def test_everything_but_the_preview_oak_fits_on_the_model():
    load_build().build_scene()
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.users_collection[0].name == "preview":
            continue
        co = np.empty(3 * len(obj.data.vertices))
        obj.data.vertices.foreach_get("co", co)
        m = np.array(obj.matrix_world)
        world = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        assert world[:, 0].min() >= L.MODEL_X[0] - 1e-3 and world[:, 0].max() <= L.MODEL_X[1] + 1e-3, obj.name
        assert world[:, 1].min() >= L.LANE_Y - 1e-3 and world[:, 1].max() <= L.BACK_Y + 1e-3, obj.name
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_blockout test_render test_build`
Expected these to FAIL:
- `test_fronts_built_in_detail_are_left_out`: `build()` takes no `exclude`.
- The camera-set assertion: no `ref01`.
- `test_paint_leaves_detailed_parts_their_own_materials`: the material is replaced.
- `test_light_is_a_sky_rendered_in_plain_colours`
- `test_build_twice_gives_one_of_each`: `doorfront_door_boards` is missing.

- [ ] **Step 3: Implement**

In `lotr/shire/bag_end/blender/bagend/blockout.py`:

- Replace the module docstring with:

```python
"""Block-out fronts: a plain wall mass with its eave and opening markers, for each front not yet
built in detail (the door front has its own module, doorfront.py)."""
```

- Replace the openings comment and dict with:

```python
# Openings from refs/03, 05, 08-10, heights above the front's floor:
# ("disc", u, z, r) or ("arched", u, z_bottom, width, height)
OPENINGS = {
    "round_window_west": [("disc", 0.0, 0.70 * D, 0.20 * D)],
    "round_window_rack": [("disc", 0.0, 0.72 * D, 0.22 * D)],
    "ornate": [("arched", 0.0, 0.55 * D, 1.2 * D, 0.95 * D), ("disc", -1.9 * D, 0.9 * D, 0.17 * D)],
    "lattice_window": [("disc", 0.0, 0.87, 0.3 * D)],
}
```

- Replace `build()` with:

```python
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
```

In `lotr/shire/bag_end/blender/build.py`:
- Change the import to
  `from bagend import blockout, doorfront, garden, hill, render, scene`.
- Make `build_scene()`:

```python
def build_scene():
    scene.reset_scene()
    hill.build()
    blockout.build(exclude=("door",))
    doorfront.build()
    garden.build()
    render.setup()
```

In `lotr/shire/bag_end/blender/bagend/render.py`:

- Change `from . import scene` to `from . import parts, scene`.
- Replace `COLOURS` (the `door_` entry goes, since no `door_*` objects are left):

```python
COLOURS = (
    ("hill", parts.TURF),
    ("front_", parts.PLASTER),
    ("eave_", (0.20, 0.13, 0.08)),
    ("window_", (0.04, 0.05, 0.07)),
    ("step_", parts.STONE),
    ("wall_", parts.STONE),
    ("chimney", parts.BRICK),
    ("oak_trunk", (0.18, 0.13, 0.08)),
    ("oak_crown", (0.12, 0.25, 0.08)),
)
```

- Replace the cameras comment and `CAMERAS` with:

```python
# Cameras matched to the reference photos by eye: (location, look-at, focal length in mm).
# ref01, ref02 and ref03 look at the door front, which is true size, so they line up with their
# photos. The hill around the fronts is compressed (layout.py), so ref09 and ref10 only frame
# the same view of it.
CAMERAS = {
    "ref09": ((12.0, -52.0, 3.0), (-5.0, 0.0, 2.6), 90),
    "ref10": ((-16.5, -13.0, -1.3), (-10.0, 0.0, 3.2), 24),
    "ref03": ((2.45, -7.3, 0.1), (0.1, 1.7, 3.8), 24),
    "ref01": ((0.15, -6.0, 1.35), (0.15, 0.0, 1.25), 38),
    "ref02": ((-1.4, -3.6, 0.55), (0.05, 0.0, 1.25), 30),
    "overview": ((-24.0, -30.0, 18.0), (-7.0, 1.0, 0.5), 40),
}
```

- Make `paint()` skip detailed parts, and name its materials `plain_*` so they never reuse a
  detailed part's material (both have a "timber"):

```python
def paint():
    """Plain colours by name prefix, for block-out parts; detailed parts keep their own materials.

    The plain materials are named plain_*, so they never reuse a detailed part's material.
    """
    for obj in bpy.data.objects:
        if obj.type != "MESH" or any(obj.data.materials):
            continue
        name, colour = next(((p, c) for p, c in COLOURS if obj.name.startswith(p)), ("timber", TIMBER))
        obj.data.materials.append(material("plain_" + name.rstrip("_"), colour))
```

- Replace `light()` with:

```python
def light():
    # Blender 5.0: new worlds already carry a node tree with "Background", and
    # World.use_nodes is deprecated, so it is not set here.
    world = bpy.data.worlds.new("sky")
    nt = world.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(38)
    sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.3
    s = bpy.context.scene
    s.world = world
    s.view_settings.view_transform = "Standard"   # plain colours, as in the photos; AgX washes them out
    s.view_settings.exposure = -2.4
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.5
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-35))
    scene.collection("lights").objects.link(sun)
```

Replace `tools/build_bag_end.sh` with (keep it executable). A missing render now fails the
script instead of being skipped silently, and `--no-render` no longer remakes sheets from
stale renders:

```bash
#!/usr/bin/env bash
# Build Bag End in Blender (.blend + renders), then put each render next to its reference photo.
#   tools/build_bag_end.sh [--no-render]
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=lotr/shire/bag_end
tools/blender.sh $DIR/blender/build.py "$@" > /dev/null
[[ " $* " == *" --no-render "* ]] && exit 0
for pair in 01_door_elevation_broad:ref01 02_door_closeup_ross:ref02 03_front_with_oak_hall:ref03 \
            09_across_valley_ross:ref09 10_from_below_chimneys_ross:ref10; do
    ref=${pair%%:*}
    cam=${pair##*:}
    tools/side_by_side.py $DIR/refs/$ref.jpg $DIR/renders/render_$cam.png $DIR/renders/compare_$cam.png
    echo "compare $DIR/renders/compare_$cam.png"
done
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_blockout test_render test_build`
Expected: `11/11 passed`.

- [ ] **Step 5: Run the whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `53/53 passed`.

- [ ] **Step 6: Run the full build**

Run: `tools/build_bag_end.sh`
Expected:
- It takes about one minute and prints five `compare ...` lines.
- It writes `lotr/shire/bag_end/bag_end.blend`, six `renders/render_*.png` (`overview`,
  `ref01`, `ref02`, `ref03`, `ref09`, `ref10`) and five `renders/compare_*.png`.

Open `renders/compare_ref01.png` and `renders/compare_ref02.png`. In each, the green planked
door must be fully visible inside its grey ring and brick arch, with a leaded porthole either
side. Describe in the report what each sheet shows. Do not tune anything.

- [ ] **Step 7: Report** (no commit; the controller snapshots the tree and shows Ryan the sheets)

---

### Task 5: Documentation

**Files:**
- Modify: `lotr/shire/bag_end/README.md`
- Modify: `README.md` (project root), catalogue row only
- Delete: `docs/superpowers/plans/2026-10-07-bag-end-m2-sources/` (after the check in Step 1)

**Interfaces:**
- Consumes: the finished tree from Tasks 1–4. Docs only, no code.

- [ ] **Step 1: Check the saved sources were copied unchanged, then delete them**

Run:
```bash
diff docs/superpowers/plans/2026-10-07-bag-end-m2-sources/parts.py lotr/shire/bag_end/blender/bagend/parts.py
diff docs/superpowers/plans/2026-10-07-bag-end-m2-sources/doorfront.py lotr/shire/bag_end/blender/bagend/doorfront.py
```
Expected: no output from either. If either differs, stop and report the diff instead of
deleting. Otherwise:
```bash
rm -r docs/superpowers/plans/2026-10-07-bag-end-m2-sources
```

- [ ] **Step 2: Update `lotr/shire/bag_end/README.md`**

Make these changes and leave the rest as it is.

- **Status:**

```markdown
## Status

**Milestone 1, rough layout: done.** The hill, five fronts as plain blocks, four chimneys, the
garden (flagstone steps, dry-stone wall, gate, bench and other props) and a preview oak.

**Milestone 2, door front in detail: done.**

- The door front is built in full, rustic detail: the green planked door with its nails and
  brass knob in a grey timber ring, a hand-laid brick arch, leaded portholes on side facets
  that turn back into the hill, timber posts with knee braces, a planked eave and the lantern.
- The layout follows the milestone 1 review. Every front is true HO size, with the banks
  between them and the back of the hill shortened. The hill climbs steeply to its top as in
  refs/09, and its sides and back fall to a thin edge.
- The other four fronts are still plain blocks.

**Next:** the other four fronts in detail (M3), garden detail (M4), and print prep (M5: split,
pockets, pins, hollowing, HO 1:87 export). The oak's position waits on an aerial photo.

There is no STL export yet. The model is in real-world metres and the scale is applied at
export. The door is D = 1.57 m across, which is a choice (see the spec). The model is
27.9 × 16.6 m, which comes to about 32 × 19 cm at 1:87 and about 10 cm tall.
```

- In **Build and test**, change the `--no-render` comment to
  `# .blend only: no renders, no comparison sheets`.
- **Where things land:**

```markdown
## Where things land

- `bag_end.blend`: the generated scene. Its active camera is the overview.
- `renders/render_<camera>.png`: one render per camera (`overview`, `ref01`, `ref02`, `ref03`,
  `ref09`, `ref10`).
- `renders/compare_<camera>.png`: the reference photo on the left and the matching render on
  the right, for `ref01`, `ref02`, `ref03`, `ref09` and `ref10`. The fronts are true size, so
  the door views (01, 02, 03) line up with their photos. The hill is compressed, so the wide
  views (09, 10) only frame the same scene.
```

- **Code:**

```markdown
## Code

Under `blender/bagend/`:

- `layout.py` holds every position and size: fronts (including the door front's facets), garden,
  hill, model extents and oak.
- `terrain.py` and `hill.py` make the landform.
- `parts.py` is the library of rustic building parts.
- `doorfront.py` builds the detailed door front from those parts.
- `blockout.py` holds the fronts still in plain blocks, with their opening markers.
- `garden.py` has the garden and chimneys.
- `render.py` has the materials, light and camera positions.
- `scene.py` has the shared helpers.

`blender/build.py` runs them all, and `blender/tests/` has the tests.
```

- In **Documents**, add a line after the milestone 1 plan:
  `- [Milestone 2 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m2-door-front.md)`
- **Archive:** replace the first sentence with
  "`old_openscad/` holds the last OpenSCAD attempt, with its own README, STLs and renders."

- [ ] **Step 3: Update the root `README.md` catalogue row**

Replace the Bag End row with:

```markdown
| [Bag End](lotr/shire/bag_end/) | about 32 × 19 × 10 cm at HO; fronts true size | – | – | Blender rebuild, milestone 2 |
```

- [ ] **Step 4: Check the links**

Run: `ls docs/superpowers/plans/2026-10-07-bag-end-m2-door-front.md lotr/shire/bag_end/refs/ATTRIBUTION.md`
Expected: both paths listed.

- [ ] **Step 5: Report** (no commit)

---

## Later milestones (outline; each gets its own plan)

- **M3, the other four fronts.** Each gets its own module, built from `parts.py` against refs
  03, 05, 08–10: the ornate front with its carved bargeboard, half-timbering and large leaded
  window, the two round-window fronts, and the lattice-window front. It needs closer photos of
  fronts 1–3.
- **M4, the garden:** flagstone steps as worn slabs, a dry-stone wall of individual stones,
  soil beds, and props (bench, birdhouse, lamp posts, gate with sign, letterbox, rack). The
  oak goes where the aerial photo puts it.
- **M5, print prep:**
  - split the hill into two sections with pins
  - pockets with 0.2 mm clearance for the fronts and chimneys
  - hollow the hill to a 2.5 mm shell, open underneath
  - export at 1:87
  - check minimum feature sizes and overhangs
  - slicing estimates
  - a test print of the door front and one hill section

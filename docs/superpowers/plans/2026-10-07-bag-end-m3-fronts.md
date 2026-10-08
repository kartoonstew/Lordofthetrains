# Bag End Milestone 3 (The Other Four Fronts) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the four remaining fronts in the same rustic detail as the door front:
- the ornate front, with its carved arched bargeboard, half-timbering and tall arched leaded window
- the lattice-window front
- the two small wheel-window fronts

This replaces the last block-outs, so every front of Bag End is detailed. Clean up where the hill
meets the fronts.

**Architecture:** A new `frontkit.py` collects what every front shares:
- placement from `layout.py` and an object builder
- the plastered wall, and the eave with timber, hood and turf
- round windows

`fronts.py` builds the four fronts from it and `parts.py`, which gains grid and wheel glazing
bars. The door front moves onto the kit too: its flower pots go to the props collection, and its
turf now runs over the hood as in the photos.

`terrain.py` is tightened where the hill meets the fronts:
- no floor slot behind the door front's angled side walls
- the hill tucks 3 cm under each front's sod
- the hill mesh keeps hard edges at real creases

`blockout.py` is retired, and `build.py` builds all five detailed fronts. Two new cameras match
refs 05 and 08.

The code was prototyped and checked before this plan was written. Replaying the three code
tasks in order gives the RED and GREEN results stated in each task, ending at 63/63 tests with a
1.5 min build. Every new front part is a closed solid. The final files are saved in
`docs/superpowers/plans/2026-10-07-bag-end-m3-sources/`, with the same paths as under
`lotr/shire/bag_end/blender/` (plus `tools/`).

**Tech Stack:** Blender 5.0.1 (bpy, bmesh, mathutils, bundled numpy 1.26), Cycles, Python 3.11
inside Blender, system Python 3 + Pillow for the comparison sheets.

**Spec:** `docs/superpowers/specs/2026-10-07-bag-end-blender-design.md` (updated for M3: the
front kit, windows as blind recesses until M5).

## Global Constraints

- Blender 5.0 or newer at `/Applications/Blender.app/Contents/MacOS/Blender`. Run every command
  from the project root, `/Users/ryanstewart/App_dev/ho-movie-scenery`.
- Units are real-world metres. Frame: origin at the door sill centre, +x along the row, +y into
  the hill, +z up. D = 1.57 m.
- Every front stays true size. `layout.py` is the single source for each front's position,
  width and eave line. A front's own module sizes only its openings and trim.
- Rustic detail is geometry, and it is repeatable: only seeded `random.Random` and
  `mathutils.noise`.
- Each front's objects live in the collection `<front name>_front`. The door front's objects
  are named `doorfront_*`; the others are named `<front name>_*`. Each part has its own material
  from `parts.materials()`. Flower pots go in `props`.
- Windows are blind recesses (0.09 m) behind their glass until M5.
- No grass, bushes or ivy geometry. HO scale only at export (M5).
- The project is a git repository (GitHub `kartoonstew/Lordofthetrains`). Work happens on the
  branch `feat/bag-end-m3`. Implementers do not run git. The controller commits each task after
  its review, using the conventional prefixes, or hands Ryan the commands if he prefers.
- Tests: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py [module ...]`. They
  print a PASS/FAIL line per test and end with `N/M passed`.
- Copied files are copied byte for byte from the sources folder. Implementers do not edit them;
  any finding goes in the report.

## Review Focus

- **Every window must be visible with the hill built.** It must not be buried in turf or hidden
  behind plaster. Test: Task 2, `test_windows_can_be_seen_with_the_hill_built`.
- **No gap or slot beside any front's wall,** including behind the door front's angled side
  walls. Tests: Task 2, `test_each_front_fills_its_dug_out`; Task 1,
  `test_turf_covers_the_ends_of_every_wall_mass` (now also samples behind the outer posts of a
  faceted front).
- **A front moved or turned in layout must move as one piece,** cut-outs included. The lattice
  front is the turned one. Tests: Task 2, `test_fronts_follow_their_layout_placement`; Task 1,
  the door front's placement test.
- **Rebuilding in one session with many more booleans** must leave no stray cutters or `.001`
  names. Tests: Task 2 (no cutters after `fronts.build()`); Task 3,
  `test_build_twice_gives_one_of_each`.
- **No block-out left in the build.** Test: Task 3, `test_build_twice_gives_one_of_each`
  asserts no `front_*`, `eave_*` or `window_*` objects.

---

## File structure

```
lotr/shire/bag_end/blender/
  bagend/
    frontkit.py   CREATE   placement, Builder, wall(), eave(), round_window()          (Task 1)
    doorfront.py  REPLACE  built with frontkit; pots to "props"; turf over the hood     (Task 1)
    terrain.py    REPLACE  no slot behind faceted side walls; hill tucks under the sod  (Task 1)
    hill.py       REPLACE  hard edges at creases (set_sharp_from_angle)               (Task 1)
    parts.py      REPLACE  + grid_bars, wheel_bars                                     (Task 2)
    fronts.py     CREATE   the four fronts; ROUND_WINDOWS, ARCHED_WINDOW               (Task 2)
    render.py     REPLACE  block-out colours removed; cameras ref05, ref08             (Task 3)
    blockout.py   DELETE                                                               (Task 3)
  build.py        REPLACE  door front + fronts.build(); no block-outs                  (Task 3)
  tests/
    test_doorfront.py, test_terrain.py  REPLACE                                        (Task 1)
    test_parts.py REPLACE, test_fronts.py CREATE                                       (Task 2)
    test_build.py, test_render.py REPLACE; test_blockout.py DELETE                     (Task 3)
tools/build_bag_end.sh   REPLACE  comparison sheets for refs 05 and 08 too             (Task 3)
READMEs                  MODIFY                                                        (Task 4)
```

`S` below stands for `docs/superpowers/plans/2026-10-07-bag-end-m3-sources` and `B` for
`lotr/shire/bag_end/blender`.

---

### Task 1: Front kit; the door front on it; the hill meets the fronts cleanly

**Files:**
- Create: `B/bagend/frontkit.py` (from `S/bagend/frontkit.py`)
- Replace: `B/bagend/doorfront.py`, `B/bagend/terrain.py`, `B/bagend/hill.py` (from `S/bagend/`)
- Replace: `B/tests/test_doorfront.py`, `B/tests/test_terrain.py` (from `S/tests/`)

**What changes:**
- `frontkit.py`:
  - `placement(f)` gives the front frame to world.
  - `Builder(f, prefix=None, seed=7)`:
    - collection `<f.name>_front`
    - `obj()` names parts `<prefix>_<part>`
    - `disc_cutter()` and `outline_cutter()` make cutters in the front's frame
    - `objects()` returns the front's objects
  - `wall(b, cutters)` builds a plaster slab across the front's width on its layout eave line,
    with openings cut.
  - `eave(b, panels, posts=True, label="", out=EAVE_OUT)` builds the header band, end posts with
    knee braces, fascia and soffit, and turf from just behind the fascia back over the wall.
  - `round_window(...)` builds a segmented frame, glass with lead cames or glazing bars, a brick
    crescent and a brick sill, and returns the opening's cutter.
- `doorfront.py`:
  - It builds with `K.Builder(L.front("door"), "doorfront", seed)`. Its own `placement()` is gone.
  - The pots go to the `props` collection.
  - Its turf now starts at `-EAVE_OUT + 0.06`, over the hood.
- `terrain.py`, in `dig()`:
  - The floor behind a faceted front is limited to its walls' footprint. A side facet's wall ends
    square to the facet, which closes the reviewer's one-cell slot behind each outer post.
  - The turf cap sits `TUCK = 0.03` under the sod top.
- `hill.py`: after `shade_smooth()`, `set_sharp_from_angle(angle=radians(50))` keeps creases and
  skirts crisp. This removes the dark smooth-shading bands at the ornate front's wings.
- Tests:
  - `test_doorfront.py` uses `K.placement(L.front("door"))`.
  - In `test_terrain.py`, the door-recess test samples the centre facet, where the recess is. The
    wall-end test also samples behind a faceted front's outer posts, at u = ±(width/2 − 0.03),
    v = 0.2 and 0.4.

**Interfaces:**
- Consumes: `layout` (`front`, `eave_top`, `facade_v`, `WALL_DEPTH`, `SOD`), `parts` (as in M2).
- Produces: `bagend.frontkit` as above, with `POST = 0.12` and `EAVE_OUT = 0.32`; and
  `terrain.TUCK`. Task 2's `fronts.py` uses every frontkit name. Its `round_window()` calls
  `parts.grid_bars` and `parts.wheel_bars`, which arrive in Task 2; nothing calls them in Task 1.

- [ ] **Step 1: Copy the tests first**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/tests/test_doorfront.py lotr/shire/bag_end/blender/tests/
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/tests/test_terrain.py lotr/shire/bag_end/blender/tests/
```

- [ ] **Step 2: RED**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_terrain`
Expected: `11/12 passed`. Only `test_turf_covers_the_ends_of_every_wall_mass` fails, with an
assertion like `('door', -1.6, 0.2, 0.0, 1.867)`: the floor slot behind the outer post.

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_doorfront`
Expected: the run aborts with `ImportError: cannot import name 'frontkit'`.

- [ ] **Step 3: Copy the code**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/bagend/{frontkit,doorfront,terrain,hill}.py lotr/shire/bag_end/blender/bagend/
```

Then check that each copied file is identical to its source, with `diff` for every file.

- [ ] **Step 4: GREEN**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_doorfront test_terrain test_hill`
Expected: `24/24 passed`.

- [ ] **Step 5: Whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `58/58 passed`.

- [ ] **Step 6: Report** (the controller reviews, then commits:
  `refactor(bag_end): front kit; door front on it; hill meets fronts cleanly`)

---

### Task 2: The four fronts

**Files:**
- Replace: `B/bagend/parts.py` (from `S/bagend/parts.py`)
- Create: `B/bagend/fronts.py` (from `S/bagend/fronts.py`)
- Replace: `B/tests/test_parts.py`; create: `B/tests/test_fronts.py` (from `S/tests/`)

**What changes:**
- `parts.py` gains two glazing patterns:
  - `grid_bars(bm, cu, cz, r, v, pitch=0.13, width=0.03, depth=0.04)`: a square lattice clipped to
    the round pane.
  - `wheel_bars(bm, cu, cz, r, v, spokes=8, ...)`: a hub ring and spokes.
- `fronts.py`:
  - `ROUND_WINDOWS[name] = (u, centre height, outer radius)` for the four fronts, from the old
    block-out openings (refs 03, 05, 08–10). The ornate front's entry is the small window on its
    left wing.
  - `ARCHED_WINDOW = (0.6 D, 0.55 D, 0.95 D)` for the ornate front (refs/08).
  - `round_window_front(name, seed)`: wheel window, wall, and an eave arched over the width.
  - `lattice_front()`: a 0.47 m window with a 0.09 m timber ring and grid bars.
  - `ornate_front()`, which builds:
    - the arched window, with glass, leaded mullions, transom, radial head bars and a ring
    - a timber frame and sill
    - half-timbering: inner posts, a timber arch over the window, and braces to the outer posts
    - the carved bargeboard: a band 0.33 m deep along the arched eave, with beads and carved knots
    - a 0.5 m deep eave hood
    - the left-wing round window
  - `build()` builds all four.
- `test_parts.py`: adds `test_glazing_bars_stay_inside_their_pane`.
- `test_fronts.py` (6 tests):
  - every front is built, named and has one material per part
  - every window can be seen with the hill built (ray from 3 m out hits its glass or bars)
  - each front's wall spans exactly its layout width
  - the ornate bargeboard crown sits at eave + 0.03 and stays within the width
  - the lattice front, moved and turned, carries every vertex with it (KDTree match)
  - fronts are repeatable

**Interfaces:**
- Consumes: `frontkit` (Task 1), `layout` (`front`, `eave_top`, `D`), `parts`.
- Produces: `fronts.build() -> list[Object]`, `fronts.ROUND_WINDOWS`, `fronts.ARCHED_WINDOW`,
  `parts.grid_bars` and `parts.wheel_bars`. Task 3's `build.py` calls `fronts.build()`.

- [ ] **Step 1: Copy the tests first**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/tests/{test_parts,test_fronts}.py lotr/shire/bag_end/blender/tests/
```

- [ ] **Step 2: RED**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_parts`
Expected: `9/10 passed`. `test_glazing_bars_stay_inside_their_pane` fails with
`AttributeError: ... 'grid_bars'`.

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_fronts`
Expected: the run aborts with `ImportError: cannot import name 'fronts'`.

- [ ] **Step 3: Copy the code**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/bagend/{parts,fronts}.py lotr/shire/bag_end/blender/bagend/
```

Check that each copied file is identical to its source, with `diff`.

- [ ] **Step 4: GREEN**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_parts test_fronts`
Expected: `16/16 passed`.

- [ ] **Step 5: Whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `65/65 passed`.

- [ ] **Step 6: Report** (the controller reviews, then commits:
  `feat(bag_end): ornate, lattice and round-window fronts`)

---

### Task 3: Every front detailed in the build; cameras for refs 05 and 08

**Files:**
- Replace: `B/build.py`, `B/bagend/render.py`, `tools/build_bag_end.sh` (from `S/build.py`,
  `S/bagend/render.py`, `S/tools/build_bag_end.sh`; keep the script executable)
- Delete: `B/bagend/blockout.py`, `B/tests/test_blockout.py`
- Replace: `B/tests/test_build.py`, `B/tests/test_render.py` (from `S/tests/`)

**What changes:**
- `build.py`: `build_scene()` runs `hill.build()`, `doorfront.build()`, `fronts.build()`,
  `garden.build()` and `render.setup()`. Block-outs are gone. With all five fronts detailed,
  `blockout.py` and its tests are deleted, so their opening data can't drift from `fronts.py`.
- `render.py`:
  - The `front_`, `eave_` and `window_` colours go.
  - Cameras `ref05` ((2.9, −5.4, 0.7) → (1.0, 0, 1.1), 24 mm) and `ref08`
    ((−10.2, −4.2, 0.35) → (−7.4, 0, 2.1), 24 mm) are added.
  - The camera comment lists the front views that line up with their photos.
- `tools/build_bag_end.sh` also makes `compare_ref05.png` and `compare_ref08.png`.
- Tests:
  - `test_build.py` asserts that `ornate_bargeboard` and `lattice_window_window_bars` exist and
    that no `front_*`, `eave_*` or `window_*` objects are left.
  - `test_render.py`'s camera set includes ref05 and ref08.

**Interfaces:**
- Consumes: `fronts.build()` (Task 2), `doorfront.build()` (Task 1).
- Produces: the full scene, and renders/compare sheets for refs 01, 02, 03, 05, 08, 09 and 10.

- [ ] **Step 1: Tests first**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/tests/{test_build,test_render}.py lotr/shire/bag_end/blender/tests/
rm lotr/shire/bag_end/blender/tests/test_blockout.py
```

- [ ] **Step 2: RED**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_build test_render`
Expected: `7/9 passed`. `test_build_twice_gives_one_of_each` fails (no `ornate_bargeboard`), and
so does `test_every_reference_camera_is_created_with_its_lens` (no `ref05`).

- [ ] **Step 3: Copy the code and delete the block-outs**

```bash
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/build.py lotr/shire/bag_end/blender/
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/bagend/render.py lotr/shire/bag_end/blender/bagend/
cp docs/superpowers/plans/2026-10-07-bag-end-m3-sources/tools/build_bag_end.sh tools/
rm lotr/shire/bag_end/blender/bagend/blockout.py
```

Check that each copied file is identical to its source, with `diff`, and that
`grep -rn blockout lotr tools` finds nothing in code.

- [ ] **Step 4: GREEN**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_build test_render`
Expected: `9/9 passed`.

- [ ] **Step 5: Whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `63/63 passed`.

- [ ] **Step 6: Full build**

Run: `tools/build_bag_end.sh`
Expected: about 1.5 minutes, and seven `compare ...` lines. Open `compare_ref08.png`,
`compare_ref05.png` and `render_overview.png` under `lotr/shire/bag_end/renders/` and describe
them:
- every front's windows visible
- the ornate front's arched bargeboard over its arched window
- turf running down onto every eave with no dark band or slot

Do not tune anything.

- [ ] **Step 7: Report** (the controller reviews, then commits:
  `feat(bag_end): build every front in detail; cameras for refs 05 and 08`; the compare sheets
  are committed with it)

---

### Task 4: Documentation

**Files:**
- Modify: `lotr/shire/bag_end/README.md`, `README.md` (catalogue row)
- Delete: `docs/superpowers/plans/2026-10-07-bag-end-m3-sources/`, after the check in Step 1

- [ ] **Step 1: Check the sources were copied unchanged, then delete them**

Run `diff` between each file under `S/` and its copy in the project:
- `S/bagend/*` against `B/bagend/`
- `S/build.py` against `B/build.py`
- `S/tests/*` against `B/tests/`
- `S/tools/build_bag_end.sh` against `tools/build_bag_end.sh`

Expected: no output. If anything differs, stop and report it. Otherwise run
`rm -r docs/superpowers/plans/2026-10-07-bag-end-m3-sources`.

- [ ] **Step 2: Update `lotr/shire/bag_end/README.md`**

- **Status:** add after the milestone 2 paragraph:

```markdown
**Milestone 3, the other four fronts: done.** The ornate front has its carved arched bargeboard,
half-timbering and a tall arched leaded window, with a small wheel window on its left wing. The
lattice-window front has its square-lattice round window in a heavy timber ring, and the two
small fronts each have a wheel window under an arched eave. They are built from a shared front
kit, which the door front now uses too. The turf runs down over every eave. Windows are 9 cm
recesses behind their glass until milestone 5 decides on lighting.
```

- Change **Next** to: garden detail (M4), then print prep (M5: split, pockets, pins, hollowing,
  HO 1:87 export). The oak's position still waits on an aerial photo.
- Edit the **Status** sentence "The other four fronts are still plain blocks." Delete it, or say
  it was true at M2.
- **Where things land:** the cameras are `overview`, `ref01`, `ref02`, `ref03`, `ref05`, `ref08`,
  `ref09` and `ref10`. The comparison sheets cover all of them except the overview. ref05 and
  ref08 are front views that line up with their photos.
- **Code:** replace the `blockout.py` bullet with `frontkit.py` ("what every front shares:
  placement, wall, eave, round windows") and `fronts.py` ("the ornate, lattice-window and two
  round-window fronts").
- **Documents:** add `- [Milestone 3 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m3-fronts.md)`.

- [ ] **Step 3: Root `README.md` catalogue row**

Change the status cell to `Blender rebuild, milestone 3`.

- [ ] **Step 4: Check the links**

Run: `ls docs/superpowers/plans/2026-10-07-bag-end-m3-fronts.md`
Expected: the path is listed.

- [ ] **Step 5: Report** (the controller reviews, then commits: `docs(bag_end): milestone 3`)

---

## After the tasks

The controller pushes `feat/bag-end-m3` and opens a PR into `main`, after Ryan's say-so on how
git is handled. The final whole-milestone review runs on the branch diff.

Carried to later milestones (from the M2 ledger):
- **M4:** soft creases up the hill face; the look (plaster saturation, turf colour); the lantern
  overlapping the door top.
- **M5:** minimum feature sizes (cames 0.14 mm, lantern posts 0.23 mm at HO); lantern
  connectivity; mirrored-side export winding; face-order determinism; through-cut windows and
  lighting.

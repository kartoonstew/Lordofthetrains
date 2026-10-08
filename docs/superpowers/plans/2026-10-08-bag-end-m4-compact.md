# Bag End Milestone 4 (The Compact Bag End, in the Look of the Photos) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the full row into the compact Bag End Ryan chose on 2026-10-08:
- three fronts under one rounded hill, with the oak on top, as in refs/03:
  - a small round window in the hill's left end
  - the door front
  - the lattice window
- the garden built in detail: slate steps, a dry-stone wall, soil beds, props and a brick chimney
- render materials and turf that read less like a toy

**Architecture:** The work comes in three code tasks and a docs task.

Task 1 adds the parts:
- `parts.py` gains mottled render materials (soft colour patches) and new materials: soil, bark
  and leaves.
- It also gains `flagstone()` and a `rough_stone()` that can turn.
- New `props.py`: the bench, gate, letterbox, lamp post, birdhouse and rack.
- New `oak.py`: an organic preview oak.

Task 2 rebuilds `garden.py` from those parts. At this point it still serves the full row: one
`BEDS` line goes into the full row's `layout.py`.

Task 3 switches the scene to the compact Bag End:
- `layout.py` keeps three fronts and moves the full row's other three to `SPARE_FRONTS`.
- `terrain.py` makes the hill a flat-topped dome with organic lumps, and its turf follows a
  faceted front's side facets.
- `fronts.py` builds whatever `layout.FRONTS` lists, through a `BUILDERS` table.
- The cameras match refs 01–05.

The code was prototyped and checked before this plan was written. Replaying the three code
tasks in order on a scratch copy gives the RED and GREEN results stated in each task, ending at
77/77 tests with a build of about 1.5 minutes. The final files are saved in
`docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/`, with the same paths as under
`lotr/shire/bag_end/blender/` (plus `tools/`).

**Tech Stack:** Blender 5.0.1 (bpy, bmesh, mathutils, bundled numpy 1.26), Cycles, Python 3.11
inside Blender, system Python 3 + Pillow for the comparison sheets.

**Spec:** `docs/superpowers/specs/2026-10-07-bag-end-blender-design.md` (updated 2026-10-08 for
the compact scope, the O-scale option and the saved full row).

**After execution:** the sources folder was removed once every copy had been checked; the files now live under `lotr/shire/bag_end/blender/` and `tools/`. To replay a task, take the sources from commit 4cc1e83.

## Global Constraints

- Blender 5.0 or newer at `/Applications/Blender.app/Contents/MacOS/Blender`. Run every command
  from the worktree root, `/Users/ryanstewart/App_dev/ho-movie-scenery/.superpowers/worktrees/bag-end-compact`.
- Units are real-world metres. Frame: origin at the door sill centre, +x along the row, +y into
  the hill, +z up. D = 1.57 m.
- Every front stays true size. `layout.py` is the single source for each front's position,
  width and eave line, and for every garden position.
- Rustic detail is geometry, and it is repeatable: only seeded `random.Random`,
  `np.random.default_rng(seed)` and `mathutils.noise`.
- Collections: each front's objects live in `<front name>_front`. The garden, wall, steps, beds
  and chimney are in `garden`. Props and flower pots are in `props`. The oak is in `preview` and
  is never printed. Each part has its own material from `parts.materials()`.
- Windows are blind recesses (0.09 m) behind their glass until M5.
- No grass, bushes or ivy geometry. The scale (HO 1:87 or O 1:48) is applied only at export (M5).
- The project is a git repository (GitHub `kartoonstew/Lordofthetrains`). Work happens on the
  branch `feat/bag-end-compact`, in the worktree above. Implementers do not run git. The
  controller commits each task after its review, using the conventional prefixes.
- Tests: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py [module ...]`. They
  print a PASS/FAIL line per test and end with `N/M passed`.
- Copied files are copied byte for byte from the sources folder. Implementers do not edit them;
  any finding goes in the report.

## Review Focus

- **Props must stand on the ground, not float or sink out of sight.** The exception is what hangs
  from a post or the gate. Tests: Task 1,
  `test_every_prop_is_a_closed_solid_planted_in_the_ground`; Task 2,
  `test_garden_parts_are_closed_solids_standing_on_the_ground`.
- **No cliff, slot or wedge where the hill meets a front,** including along the door front's
  turned side facets. Tests: Task 3, `test_terrain`'s no-cliffs and wall-end tests (sampling from
  just behind the facade line); the door front's sod test.
- **The compact model must fit one HO print, and the full row's fronts must still build** for
  later hobbit holes. Tests: Task 3, `test_compact_model_is_one_print_at_ho`,
  `test_hill_is_about_17_by_12_cm_at_ho_and_under_8_cm_tall`,
  `test_the_full_rows_spare_fronts_still_build`.
- **Every window must be visible with the hill built,** the new left window included. Test:
  Task 3, `test_windows_can_be_seen_with_the_hill_and_garden_built` (its targets come from
  `layout.FRONTS`).
- **Rebuilding in one session leaves one of each object,** with the garden and props included.
  Test: Task 3, `test_build_twice_gives_one_of_each`.

---

## File structure

```
lotr/shire/bag_end/blender/
  bagend/
    parts.py      REPLACE  mottled materials; soil, bark, leaves; flagstone; rough_stone(rot, cuts) (Task 1)
    props.py      CREATE   bench, gate, letterbox, lamp_post, birdhouse, rack            (Task 1)
    oak.py        CREATE   preview oak: curve trunk and limbs, leaf clusters             (Task 1)
    garden.py     REPLACE  slate steps, stone wall, beds, brick chimneys, props, oak     (Task 2)
    layout.py     MODIFY   + BEDS for the full row                                        (Task 2)
    layout.py     REPLACE  the compact layout                                             (Task 3)
    terrain.py    REPLACE  dome hill, lumps, turf along side facets                       (Task 3)
    hill.py, frontkit.py, doorfront.py, fronts.py, render.py   REPLACE                    (Task 3)
  tests/
    test_parts.py REPLACE, test_props.py, test_oak.py CREATE                              (Task 1)
    test_garden.py REPLACE                                                                (Task 2)
    test_layout, test_terrain, test_hill, test_fronts, test_build, test_render  REPLACE   (Task 3)
tools/build_bag_end.sh   REPLACE  comparison sheets for refs 01–05                        (Task 3)
lotr/shire/bag_end/renders/compare_ref08,09,10.png   DELETE (those cameras are gone)      (Task 3)
READMEs                  MODIFY                                                           (Task 4)
```

`S` below stands for `docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources` and `B` for
`lotr/shire/bag_end/blender`.

---

### Task 1: Parts, props and the preview oak

**Files:**
- Replace: `B/bagend/parts.py`; create: `B/bagend/props.py`, `B/bagend/oak.py` (from `S/bagend/`)
- Replace: `B/tests/test_parts.py`; create: `B/tests/test_props.py`, `B/tests/test_oak.py` (from
  `S/tests/`)

**What changes:**
- `parts.py`:
  - The colours are toned down to the photos: PLASTER (0.50, 0.34, 0.10), STONE
    (0.12, 0.115, 0.105), TURF (0.03, 0.08, 0.014).
  - `materials()`'s `mat()` gains `mottle=(colour2, scale)`. A Noise texture in Object
    coordinates drives a two-colour ramp. With `vary` as well, the per-piece variation multiplies
    over it. Plaster, stone (moss patches), turf and the new soil are mottled. Bark and leaves
    are new.
  - `rough_stone(..., rot=None, cuts=4)` can turn and use fewer cuts.
  - `flagstone(bm, centre, length, width, thick, yaw, rng, seed)`: a 10-point irregular slate
    slab whose top is at `centre`'s z, dipping by up to 6 mm.
  - The lattice centre square is now 0.45 r. This is an M3 leftover; the photos show a bigger
    centre.
- `props.py` (collection `props`, each placed on `terrain.ground` and turned by yaw):
  - `bench(x, y, yaw=-8)`
  - `gate(x, y)`, with ball finials and `gate_sign`
  - `letterbox(x, y)`: a log
  - `lamp_post(name, x, y)`, which makes `<name>_post`, `<name>_lantern` and `<name>_glass`
  - `birdhouse(x, y)` and `rack(x, y)`
- `oak.py`: `build(seed=71)` returns the `oak_crown` mesh.
  - `oak_trunk` is a curve object, with a gnarled trunk and six spreading limbs that carry side
    branches.
  - `oak_crown` is clusters of flattened, wobbled icospheres at the limb and branch tips.
  - Both are in `preview`.
- Tests:
  - `test_parts.py` adds `test_flagstone_is_a_closed_slab_with_its_top_at_the_tread` and
    `test_rough_materials_vary_across_a_surface`.
  - `test_props.py` (2 tests): every prop is a closed solid planted in the ground, except the
    hung parts; props are repeatable.
  - `test_oak.py` (2 tests): the oak is a preview whose crown spreads at least 3.5 m and wider
    than 0.6 × its height; the oak is repeatable.

**Interfaces:**
- Consumes: `terrain.ground(x, y)`, `layout.OAK`, `scene.collection(name)`, and the existing
  `parts` helpers (`box`, `wobble`, `to_object`).
- Produces:
  - `parts.flagstone`, `parts.rough_stone(..., rot, cuts)`, and `parts.materials()` keys `soil`,
    `bark` and `leaves`
  - `props.bench`, `gate`, `letterbox`, `lamp_post(name, x, y)`, `birdhouse` and `rack`
  - `oak.build() -> Object` (the crown)
  Task 2's `garden.py` uses all of them.

- [ ] **Step 1: Copy the tests first**

```bash
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/tests/{test_parts,test_props,test_oak}.py lotr/shire/bag_end/blender/tests/
```

- [ ] **Step 2: RED**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_parts`
Expected: `10/12 passed`. Two tests fail:
- `test_flagstone_is_a_closed_slab_with_its_top_at_the_tread`, with
  `AttributeError: module 'bagend.parts' has no attribute 'flagstone'`
- `test_rough_materials_vary_across_a_surface`, with an `AssertionError` (no `soil` material)

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_props`
Expected: the run aborts with `ImportError: cannot import name 'props' from 'bagend'`.

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_oak`
Expected: the run aborts with `ImportError: cannot import name 'oak' from 'bagend'`.

- [ ] **Step 3: Copy the code**

```bash
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/bagend/{parts,props,oak}.py lotr/shire/bag_end/blender/bagend/
```

Then check that each copied file is identical to its source, with `diff` for every file.

- [ ] **Step 4: GREEN**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_parts test_props test_oak`
Expected: `16/16 passed`.

- [ ] **Step 5: Whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `73/73 passed`.

- [ ] **Step 6: Report** (the controller reviews, then commits:
  `feat(bag_end): mottled materials, slate and stone parts, props and the preview oak`)

---

### Task 2: The garden in detail

**Files:**
- Replace: `B/bagend/garden.py` (from `S/bagend/garden.py`)
- Modify: `B/bagend/layout.py`, with one insertion (Step 3). Task 3 replaces this file.
- Replace: `B/tests/test_garden.py` (from `S/tests/test_garden.py`)

**What changes:**
- `garden.py` (collection `garden`):
  - `steps()`: one slate `flagstone` per tread, laid across the path toward the next tread, its
    top at the tread height.
  - `wall()`: the dry-stone wall in two lengths, `wall_west` and `wall_east`, with a gap for the
    steps. Each is courses of rough stones, staggered, over a solid core, with capstones. The
    stones may lean up to 0.1 m into the edge fall.
  - `beds()`: low soil mounds from `layout.BEDS`, following the ground, named `bed_<k>`.
  - `chimneys()`: brick stacks laid course by course over a core (`chimney_<k>`), a rough stone
    cap (`chimney_cap_<k>`) and a terracotta pot (`chimney_pot_<k>`).
  - `build()` builds those, then the props from `layout`: bench, gate, letterbox one metre left of
    the gate, lamp posts, birdhouse, and the rack only `if L.RACK`. Then it builds the oak.
- `layout.py` gains `BEDS` for the full row, so the garden builds before Task 3 changes the
  layout.
- `test_garden.py`:
  - The step test allows the slate's top to dip by 1 cm.
  - The wall test allows stones up to 0.1 m into the edge fall.
  - It adds three tests:
    - `test_garden_parts_are_closed_solids_standing_on_the_ground`
    - `test_the_oak_is_a_preview_with_a_trunk_and_a_crown`
    - `test_garden_is_built_in_detail`: the wall has more than 40 pieces, a step has more than 8
      vertices, a chimney has more than 20 bricks, and every bed and chimney part exists

**Interfaces:**
- Consumes: Task 1's `parts`, `props` and `oak`, and `layout`'s `STEPS`, `GATE`, `WALL_Y`,
  `LAWN_Z`, `TERRACE_Z`, `MODEL_X`, `EDGE_FALL`, `CHIMNEYS`, `CHIMNEY_SIZE`, `CHIMNEY_HEIGHT`,
  `BENCH`, `LAMPS`, `BIRDHOUSE`, `RACK` and `BEDS`.
- Produces: `garden.build()`. Its objects are named `step_<k>`, `wall_west`, `wall_east`,
  `bed_<k>`, `chimney_<k>`, `chimney_cap_<k>` and `chimney_pot_<k>`, plus the props and the oak.
  `build.py` already calls it. Task 3's layout keeps every name `garden.py` reads, with
  `RACK = None`.

- [ ] **Step 1: Copy the test first**

```bash
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/tests/test_garden.py lotr/shire/bag_end/blender/tests/
```

- [ ] **Step 2: RED**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_garden`
Expected: `4/6 passed`. Two tests fail:
- `test_garden_is_built_in_detail` (no `chimney_cap_0`)
- `test_garden_parts_are_closed_solids_standing_on_the_ground`, with
  `AssertionError: ('birdhouse', 1.39...)`: the old block birdhouse sits on the path, not in the
  ground

- [ ] **Step 3: Copy the code, and add the beds to the layout**

```bash
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/bagend/garden.py lotr/shire/bag_end/blender/bagend/
```

Check it is identical to its source, with `diff`. Then, in `lotr/shire/bag_end/blender/bagend/layout.py`,
insert these lines directly after the line `GATE = (2.6, -8.2)`:

```python
# Soil beds for Ryan's flowers and shrubs, either side of the steps, refs/04, 05: (x, y, half-length,
# half-width, direction in degrees)
BEDS = ((-0.6, -2.3, 0.55, 0.3, 20.0), (2.0, -2.5, 0.5, 0.3, -30.0),
        (0.4, -5.2, 0.6, 0.35, 70.0), (3.2, -5.6, 0.6, 0.3, 75.0))
```

- [ ] **Step 4: GREEN**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_garden`
Expected: `6/6 passed`.

- [ ] **Step 5: Whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `76/76 passed`.

- [ ] **Step 6: Report** (the controller reviews, then commits:
  `feat(bag_end): garden in detail: slate steps, stone wall, beds, brick chimneys, props`)

---

### Task 3: The compact Bag End

**Files:**
- Replace (from `S/bagend/`): `B/bagend/layout.py`, `terrain.py`, `hill.py`, `frontkit.py`,
  `doorfront.py`, `fronts.py` and `render.py`
- Replace: `tools/build_bag_end.sh` (from `S/tools/build_bag_end.sh`; keep it executable)
- Replace (from `S/tests/`): `B/tests/test_layout.py`, `test_terrain.py`, `test_hill.py`,
  `test_fronts.py`, `test_build.py` and `test_render.py`
- Delete: `lotr/shire/bag_end/renders/compare_ref08.png`, `compare_ref09.png` and
  `compare_ref10.png`, since those cameras are gone

**What changes:**
- `layout.py`:
  - `FRONTS` is three fronts:
    - `round_window_left` (−2.5 D, y 0.3, 1.5 D wide, turned 6°)
    - `door` (unchanged)
    - `lattice_window` (2.53 D, y 0.4, floor 0.45, turned −5°)
  - The full row's other three fronts move to `SPARE_FRONTS`. `front(name)` searches both.
  - `POST = 0.12` moves here from `frontkit.py`.
  - Garden:
    - the lane at `LANE_Z = −1.2`, `LANE_Y = −5.2`
    - five steps ending at `GATE = (1.95, −4.95)`
    - three `BEDS`
    - the bench at (3.7, −4.4) and one lamp at (−2.2, −1.5)
    - `RACK = None`
  - The hill:
    - a dome with `DOME_TOP = 3.5`, `DOME_CENTRE = (0.0, 1.2)`, `DOME_RADII = (7.6, 4.6)`,
      `DOME_POWER = 4.0`
    - one swell under the oak
  - The model: `MODEL_X = (−7.6, 7.2)`, `BACK_Y = 5.4`, `BASE_Z = −2.0`, `EDGE_FALL = 1.0`.
    That is about 170 × 122 × 68 mm at HO.
  - One chimney at (4.5, 2.4); the oak at (0.3, 2.5).
- `terrain.py`:
  - `hill()` is the dome, flat on top, with the bank over the fronts.
  - `lumps(x, y)` adds gentle waves of about ±0.1 m, only where the hill has risen.
  - In `dig()`, behind a faceted front's side facet, the turf follows that facet's sod line, and
    its back slope is measured square to the facet. The floor stops half a post short of the
    outer post. The cheek ramp is 0.25 m, so the turf meets the facade line without a cliff.
- `hill.py` gives the hill the mottled `turf` material.
- `frontkit.py` takes `POST` from `layout`.
- `doorfront.py`:
  - The lantern hangs at `eave_centre(0) − 0.12`, clear of the door.
  - The side sod reaches back over the centre facet, so no wedge opens behind the inner post.
- `fronts.py`:
  - `ROUND_WINDOWS` gains `round_window_left`.
  - A `BUILDERS` table names a builder for every front, spare ones included.
  - `build()` builds the non-door fronts in `layout.FRONTS`.
  - Two M3 leftovers: the ornate front's studs run up into the header band, and its corbels are
    flush with the beads.
- `render.py`:
  - cameras `ref01`, `ref02`, `ref03`, `ref04`, `ref05` and `overview`, framed on the compact hill
  - `ref08`, `ref09` and `ref10` are gone
- `tools/build_bag_end.sh` makes comparison sheets for refs 01–05.
- Tests:
  - `test_layout`: the row spans 9.5–11 m with at least 2 m to each model edge; the model is
    150–185 × 110–135 mm at HO and fits the 256 mm bed.
  - `test_terrain`:
    - the hill top reaches `DOME_TOP − 0.3` and stands more than 1 m above the door's eave
    - the lawn and lane are sampled at x = −3.0
    - the no-cliffs samples start just behind the facade line (v = 0.05)
  - `test_hill`: 150–185 × 110–135 mm and under 80 mm tall at HO.
  - `test_fronts`:
    - `NAMES` comes from `layout.FRONTS` and `fronts.BUILDERS`
    - the ornate tests build `fronts.ornate_front()` directly
    - it adds `test_the_full_rows_spare_fronts_still_build`
  - `test_build`: asserts `round_window_left_window_bars`, `lattice_window_window_bars` and the
    garden's parts.
  - `test_render`: the camera set is ref01–ref05.

**Interfaces:**
- Consumes: Task 2's `garden.build()`, which reads every layout name listed there (still present,
  with `RACK = None`), and Task 1's `parts.materials()["turf"]`.
- Produces: the compact scene, with renders and comparison sheets for refs 01–05.

- [ ] **Step 1: Copy the tests first**

```bash
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/tests/{test_layout,test_terrain,test_hill,test_fronts,test_build,test_render}.py lotr/shire/bag_end/blender/tests/
```

- [ ] **Step 2: RED**

Run each module on its own:
`tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py <module>`

Expected:
- `test_layout`: `6/8 passed`. `test_compact_model_is_one_print_at_ho` and
  `test_row_leaves_room_for_the_hill_to_slope_down_at_its_ends` fail (321.8 mm wide; a 25.2 m
  row).
- `test_terrain`: `11/12 passed`. `test_hill_climbs_to_its_top_behind_the_fronts` fails with
  `AttributeError: ... 'DOME_TOP'`.
- `test_hill`: `5/6 passed`. `test_hill_is_about_17_by_12_cm_at_ho_and_under_8_cm_tall` fails
  (about 322 × 191 × 103 mm).
- `test_fronts`: the run aborts with `AttributeError: module 'bagend.fronts' has no attribute
  'BUILDERS'`.
- `test_build`: `1/2 passed`. `test_build_twice_gives_one_of_each` fails.
- `test_render`: `6/7 passed`. `test_every_reference_camera_is_created_with_its_lens` fails (no
  `ref04`).

- [ ] **Step 3: Copy the code; delete the old sheets**

```bash
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/bagend/{layout,terrain,hill,frontkit,doorfront,fronts,render}.py lotr/shire/bag_end/blender/bagend/
cp docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/tools/build_bag_end.sh tools/
rm lotr/shire/bag_end/renders/compare_ref08.png lotr/shire/bag_end/renders/compare_ref09.png lotr/shire/bag_end/renders/compare_ref10.png
```

Check that each copied file is identical to its source, with `diff` (this replaces Task 2's
edited `layout.py`). Check that `tools/build_bag_end.sh` is still executable (`ls -l`).

- [ ] **Step 4: GREEN**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_layout test_terrain test_hill test_fronts test_build test_render`
Expected: `45/45 passed`.

- [ ] **Step 5: Whole suite**

Run: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`
Expected: `77/77 passed`.

- [ ] **Step 6: Full build**

Run: `tools/build_bag_end.sh`
Expected: about 1.5 minutes, and five `compare ...` lines (ref01–ref05). Open
`compare_ref03.png`, `compare_ref05.png` and `render_overview.png` under
`lotr/shire/bag_end/renders/`, and describe:
- whether all three fronts' windows and the door are visible
- the dome hill with the oak over the door and the chimney behind the lattice window
- the slate steps winding down through the wall to the gate, the beds, the bench and the lamp
- whether there is any dark band, slot or cliff where the turf meets a front

Do not tune anything.

- [ ] **Step 7: Report** (the controller reviews, then commits:
  `feat(bag_end): the compact Bag End: three fronts under a dome hill, cameras for refs 01-05`;
  the five compare sheets go with it, and the three removed sheets are staged as deletions)

---

### Task 4: Documentation

**Files:**
- Modify: `lotr/shire/bag_end/README.md`, `README.md` (catalogue row)
- Delete: `docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources/`, after the check in
  Step 1

- [ ] **Step 1: Check the sources were copied unchanged, then delete them**

Run `diff` between each file under `S/` and its copy in the project:
- `S/bagend/*` against `B/bagend/`
- `S/tests/*` against `B/tests/`
- `S/tools/build_bag_end.sh` against `tools/build_bag_end.sh`

Expected: no output. If anything differs, stop and report it. Otherwise run
`rm -r docs/superpowers/plans/2026-10-08-bag-end-m4-compact-sources`.

- [ ] **Step 2: Update `lotr/shire/bag_end/README.md`**

- Change the intro paragraph's first sentence to:

```markdown
Bilbo's hobbit hole under The Hill, modelled on the Hobbiton Movie Set in Matamata, New
Zealand: the green door with a window either side under its own small hill, and the oak on top.
```

- **Status:** add after the milestone 3 paragraph:

```markdown
**Milestone 4, the compact Bag End: done.** On 2026-10-08 Ryan chose a more contained Bag End
as the piece to finish first, as in refs/03:
- three fronts under one rounded hill, with gentle lumps in its turf and the oak on top:
  - a small round window in the hill's left end
  - the door front
  - the lattice window
- the garden in detail: slate steps winding down through the dry-stone wall to the gate, soil
  beds for planting, a brick chimney with its cap and pot, and the bench, lamp post, birdhouse
  and letterbox
- mottled render materials, so plaster, stone and turf read less like a toy

The full row of five fronts from milestones 1–3 is saved at git tag `bag-end-full-row-m3`. The
branch `wip/bag-end-full-row-m4` holds its built `.blend`, its renders and
`lotr/shire/bag_end/saved/FULL_ROW_ROADMAP.md`. The full row's other fronts are kept in
`layout.SPARE_FRONTS`, so their builders stay usable for more hobbit holes later.
```

- Change **Next** to: `**Next:** print prep (M5): choose HO or O, split if needed, pockets,
  pins, hollowing, export, and a test print.`
- Replace the size paragraph's last two sentences ("The model is 28.0 × 16.6 m, ...") with:
  `The model is 14.8 × 10.6 m, which comes to about 17 × 12 × 7 cm at HO (1:87), one print. Ryan's
  train is O scale (1:48), where it would be about 31 × 22 × 12 cm: two prints, or a trimmed edge.`
- Change `**Milestone 1, rough layout: done.**` to `**Milestone 1, rough layout (full row):
  done.**`, and `**Milestone 3, the other four fronts: done.**` to `**Milestone 3, the full
  row's other four fronts: done.**`.
- **Where things land:**
  - the cameras are `overview`, `ref01`, `ref02`, `ref03`, `ref04` and `ref05`
  - the comparison sheets cover all of them except the overview
  - the door views (01, 02) line up with their photos; 03, 04 and 05 show the compact hill from
    near where those photos were taken
  Remove the sentences about the compressed hill and refs 08, 09 and 10.
- **Code:**
  - the `layout.py` bullet adds "and the full row's spare fronts"
  - the `fronts.py` bullet becomes "builds the other fronts, through a builder for every front,
    spare ones included"
  - the `garden.py` bullet becomes "has the steps, wall, beds and chimney"
  - add `props.py` ("the bench, gate, letterbox, lamp post, birdhouse and rack") and `oak.py`
    ("the preview oak, never printed")
- **Documents:** add `- [Milestone 4 plan](../../../docs/superpowers/plans/2026-10-08-bag-end-m4-compact.md)`.

- [ ] **Step 3: Root `README.md` catalogue row**

Change the Bag End size cell to `about 17 × 12 × 7 cm at HO (31 × 22 × 12 cm at O); fronts true
size` and the status cell to `Blender rebuild, milestone 4`.

- [ ] **Step 4: Check the links**

Run: `ls docs/superpowers/plans/2026-10-08-bag-end-m4-compact.md docs/superpowers/specs/2026-10-07-bag-end-blender-design.md`
Expected: both paths are listed.

- [ ] **Step 5: Report** (the controller reviews, then commits: `docs(bag_end): milestone 4, the compact Bag End`)

---

## After the tasks

The final whole-milestone review runs on the branch diff. Then the controller pushes
`feat/bag-end-compact` and opens a PR into `main`. The branch was cut from `feat/bag-end-m3`,
so the PR notes that it depends on PR #1 (milestone 3) and should be merged after it.

Carried to milestone 5:
- **Choose the scale.** At HO it is one print. At O it needs splitting, or the lane edge trimmed.
- **Look items for Ryan:**
  - The turf beside each front rises in a near-vertical step at the facade line (up to about
    1.8 m beside the door front), fading within about 0.2 m; between the door and lattice fronts it
    reads as a tall tongue of turf (compare_ref05). `test_no_cliffs` starts at v = 0.05, so nothing
    guards this step.
  - The hill's back and ends fall steeply to the thin edge (3–4.6 m within the last metre).
- The hill rises up to 3 cm above the door front's sod at its inner posts (concave corners).
- Print parts:
  - `gate_sign` hangs about 2 cm in front of the gate and is 0.29 mm thick at HO: attach and thicken it.
  - Props are unions of overlapping shells, not welded solids.
  - Stone and brick joints are about 0.2 mm at HO, brick relief about 0.23 mm.
  - The chimney is in the `garden` collection with the hill's printed parts; export must split it
    out by name. On the dome's slope its lowest course stands about 9 cm above the ground on the
    downhill side; the chimney socket should cover that.
  - The dry-stone wall's courses stop up to 6 cm short of the capstones, showing the core.
- Code:
  - The door front's side sod uses bare numbers (−0.4, 24); nothing tests the no-wedge fix or the
    lantern clearance.
  - The letterbox offset and the wall gap (tied to `STEPS[3]`) are set in `garden.py`, not `layout.py`.
  - No whole-scene test checks that every mesh has exactly one material from `parts.materials()`.
- From earlier ledgers:
  - minimum feature sizes (cames 0.14 mm, lantern posts 0.23 mm at HO)
  - lantern connectivity
  - mirrored-side export winding
  - face-order determinism
  - through-cut windows and lighting
  - triangulating the long wobbled caps before STL export

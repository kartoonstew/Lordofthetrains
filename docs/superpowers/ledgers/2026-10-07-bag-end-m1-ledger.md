# SDD ledger — plan: docs/superpowers/plans/2026-10-07-bag-end-m1-blockout.md

Spec: docs/superpowers/specs/2026-10-07-bag-end-blender-design.md (read).
Ruling: no git in this project, so no worktree/commits; review packages come from directory snapshots (snapdiff.sh snap/diff) taken before each task and fix round — the plan's Global Constraints forbid git init without Ryan — cost if wrong: diffs exclude generated files (.blend, png, stl), so reviewers judge those only via reports.

## Pre-flight scan

| Tasks | Shared file / interface | Producer vs consumer | Found |
|---|---|---|---|
| T1→T3,T4,T5,T6 | scene.py | reset_scene(), collection(name), add_mesh_object(name, verts, faces, coll) vs hill/blockout/garden/render/build calls | consistent |
| T1→all | tools/blender.sh, tests/run_tests.py | sys.path to lotr/shire/bag_end/blender; module filter by stem | consistent |
| T2→T3 | layout constants, terrain.ground | WEST_X, EAST_X, LANE_Y, BACK_Y, BASE_Z; ground(array) vs hill.build grid | consistent |
| T2→T4 | layout FRONTS/eave_top/STEPS/GATE/CHIMNEYS/etc, terrain.ground | names used by blockout/garden all defined | consistent |
| T3→T6 | hill.build() -> object "hill" | build_scene + test_build expects "hill" | consistent |
| T4→T5 | object name prefixes | render.COLOURS prefixes front_/eave_/door_/window_/step_/wall_/chimney/hill/oak_* match blockout/garden names | consistent |
| T4→T6 | blockout.build, garden.build, names front_door, oak_crown | consumed by build_scene/test_build | consistent |
| T5→T6 | render.setup, render_all, CAMERAS | build.py; build_bag_end.sh expects render_ref09/ref10/ref03 | consistent |
| T1 self | test_scene (3) vs scene.py | asserts match code; archive step edits tools/build.sh + README row (row text exists) | consistent |
| T2 self | test_terrain vs terrain.py | test_turf_covers_every_front FAILS for door u≈0.44,v=0.4: steps_cut cheek slope 1.5 lowers hill behind door to 1.85 < 2.33 | DEFECT |
| T3 self | test_hill vs hill.py | float32 coords within 1e-4 tolerance; ring traversal covers boundary once | consistent |
| T4 self | tests vs blockout/garden | names use cm ints (no '.'), chimney/step heights match | consistent |
| T5 self | tests vs render.py | clip_end = dist+100 >= dist+40; possible Blender 5.0 use_nodes deprecation — implementer to adapt minimally | risk noted |
| T6 self | test_build vs build.py; count 21 | 3+5+4+2+2+2+2+1 = 21 | consistent; Step 7 (show Ryan) is the controller's job |

Ruling: steps_cut cheek slope 1.5 -> 3.0 (edited in plan Task 2 Step 4) — the gentle cheeks dug the hill down behind the door, failing the turf-cover requirement the spec's realism depends on — cost if wrong: steeper banks beside the steps (cosmetic, revisited in M4).
Ruling: Task 6 Step 7 (show Ryan) is done by the controller, not the implementer — reviews belong to the controller — cost if wrong: none.
Task 1: dispatched implementer (haiku) — snapshot snap-t1
Task 1: implementer DONE (3/3); review dispatched (sonnet) on review-t1.diff
Task 1: review — spec ❌ minor only (extra tests/__init__.py; RED run order), 1 Important (plan-mandated): normals test passes without recalc.
Ruling: strengthen test_add_mesh_object_points_normals_outward to also assert the bottom face points down (deviates from plan text) — the plan's test asserted nothing about the helper's one job — cost if wrong: none.
Task 1: minor (deferred): extra empty tests/__init__.py
Task 1: minor (deferred): test_reset_scene_is_empty_and_metric only meaningfully checks object count; length_unit unasserted
Task 1: minor (deferred): run_tests.py exec_module outside try — a broken test module aborts the run without a FAIL line
Task 1: minor (deferred): tools/blender.sh path handling (cd to root, unquoted $PWD in python-expr, bare unbound-variable on missing arg)
Task 1: minor (deferred): doc drift — root README lines 27/28/41 describe old OpenSCAD Bag End workflow; build.sh stl()/png() have no callers
Task 1: minor (deferred): archived old_openscad/bag_end.scad include path and README refs link no longer resolve
Task 1: minor (deferred): scene.collection() returns an existing same-named collection even if unlinked
Task 1: fix round 1/5 dispatched (resume implementer) — fix base snap-t1f1
Task 1: fix round 1/5 (1 addressed, 0 open; snap-t1f1 -> tree)
Task 1: complete (snap-t1 -> tree, review clean after fix round 1)
Task 2: dispatched implementer (haiku) — snapshot snap-t2
Task 2: implementer DONE (12/12); review dispatched (sonnet) on review-t2.diff
Task 2: review — spec ✅, Approved, 2 Important (plan-mandated): (1) dig edge at v=-0.45 leaves a hill strip up to 2.4 m high in front of every facade (door/windows hidden), turf test never samples near the facade; (2) yawed-front handling untested (yaw=0 in dig still passes).
Ruling: dig edge moves from the eave front (v=-0.45) to the facade line (v=0), and the dug-out test probes v=-0.05 across ±0.95 of the half-width — the spec needs the fronts visible and the eave overhangs open; probing just in front of the facade also makes a yaw error fail — cost if wrong: a heightfield fillet up to one grid cell (0.15 m) can sit against the foot of a facade not aligned to the grid (lattice front); M2's detailed fronts get proper CSG clearance.
Task 2: minor (deferred): terrain.py magic numbers (60°, 50°, 0.5, 0.45, 3.0) unnamed; line 45 117 chars
Task 2: minor (deferred): garden() broadcasts with `+ 0.0 * x` (NaN-propagating); np.broadcast_arrays cleaner
Task 2: minor (deferred): ground() returns np.float64 for scalars though brief says 0-d array
Task 2: minor (deferred): test_layout overlap check ignores yaw (~0.09 m at 5°)
Task 2: minor (deferred): hill() local named `front` shadows the idea of L.front
Task 2: minor (deferred): report line counts slightly off
Task 2: fix round 1/5 dispatched (resume implementer) — fix base snap-t2f1
Task 2: fix round 1/5 (2 addressed, 0 open; snap-t2f1 -> tree)
Task 2: complete (snap-t2 -> tree, review clean after fix round 1)
Task 3: dispatched implementer (haiku) — snapshot snap-t3
Task 3: implementer DONE (14/14); review dispatched (sonnet) on review-t3.diff
Task 3: minor (deferred): hill winding untested (add_mesh_object recalcs anyway) — could assert signed volume > 0
Task 3: minor (deferred): test_hill_top_follows samples could be vacuous if top empty — add assert top
Task 3: minor (deferred): np.arange grid stops up to one STEP short of declared X_RANGE/Y_RANGE (x max 10.4, y max 16.95)
Task 3: minor (deferred): report figures wrong (vert/face counts, timing label)
Task 3: complete (snap-t3 -> tree, review clean)
Task 4: dispatched implementer (haiku) — snapshot snap-t4
Task 4: implementer DONE (18/18; added view_layer.update() in build()); review dispatched (sonnet) on review-t4.diff
Task 4: review — spec ✅ (code faithful; view_layer.update() justified in blockout), Needs fixes: 1 Important — terrain.ground uses max(garden, hill) and hill is 0 (not negative) off the hill, so the lawn/lane are clamped up to 0: dry-stone wall shows only a 5 cm lip, letterbox buried. Root cause is Task 2's plan code.
Ruling: terrain.ground combines as garden + hill (hill rises from the terrace and is zero wherever the garden is below it) and test_terrain gains test_lawn_falls_from_the_wall_to_the_lane — the spec's dry-stone wall and lower garden must exist — cost if wrong: if hill and garden ever overlap where garden != 0, heights would add; today hill is 0 in front of y=-1.6, well behind the wall (y=-3.6). Fixed through Task 4's fix loop because Task 4's review found it.
Ruling: full-suite count is now 22 at Task 6 (one extra terrain test) — cost if wrong: none.
Task 4: minor (deferred): gate posts/letterbox reuse ground_at(GATE) for offset parts (fine while lawn is flat in x)
Task 4: minor (deferred): preview oak crown floats ~0.22 m above trunk top (preview only)
Task 4: minor (deferred): outer corners of steps 2–4 sit up to 0.2 m under the channel cheeks
Task 4: minor (deferred): blockout/garden tests thin (x-midpoint only; no step-on-ground or opening-inside-outline checks)
Task 4: minor (deferred): view_layer.update() lacks a comment explaining it is needed for matrix_world; report claimed no deviations and "six fronts" (five)
Task 4: fix round 1/5 dispatched (resume implementer) — fix base snap-t4f1
Task 4: fix round 1/5 (1 addressed, 0 open; snap-t4f1 -> tree)
Task 4: complete (snap-t4 -> tree, review clean after fix round 1)
Task 5: dispatched implementer (sonnet — Blender 5.0 node API may differ from plan) — snapshot snap-t5
Task 5: implementer DONE (21/21; dropped use_nodes — Blender 5.0.1 deprecates it, nodes on by default); review dispatched (sonnet) on review-t5.diff
Task 5: implementer concern verified by controller (smoke render): fronts render green — the hill mesh's one-cell slope (grid 0.15 m) sits in front of every facade because dig ends exactly at v=0 (my Task 2 ruling), covering each facade with a slanted turf sliver.
Ruling: terrain.dig digs to v < 0.2 (DIG_BEHIND, more than one hill grid cell behind the facade line) so the mesh's sloped cell lies inside the wall mass (0.8 m deep); a test asserts ground is dug at v = hill.STEP + 0.01 behind every front — the spec needs the fronts visible — cost if wrong: a small notch beside each front's outer corners exposing ~0.2 m of the wall block's side; turf meets the eave top one cell further back. Reopens Task 2 as fix round 2 (resume Task 2 implementer); fix base snap-t2f2.
Task 2: fix round 2 implementer DONE (22/22; render confirms fronts visible); re-review dispatched
Task 5: review — spec ✅ (use_nodes removal correct for 5.0.1), Approved; 1 Important (plan-mandated): paint()/light()/render_all untested (tests run on an empty scene).
Ruling: add one paint() test (dummy meshes chimney_cap_0, oak_crown, bench -> materials chimney, oak_crown, timber); no render_all unit test — Task 6's full build exercises it and a render in the suite costs seconds per run — cost if wrong: a render_all regression shows up only at build time.
Task 5: minor (deferred): test_cameras_see_the_whole_hill restates the implementation margin instead of measuring the hill
Task 5: minor (deferred): setup() never sets scene.camera, so bag_end.blend opens without an active camera
Task 5: minor (deferred): setup() not idempotent without reset_scene() (docstring note)
Task 5: minor (deferred): COLOURS "chimney" prefix lacks trailing underscore on purpose — comment it
Task 5: fix round 1/5 dispatched (resume implementer) — fix base snap-t5f1
Task 5: fix round 1 implementer DONE (23/23); re-review dispatched
Task 2: fix round 2/5 (1 addressed, 0 open; snap-t2f2 -> tree)
Task 2: complete again (review clean after fix round 2)
Task 5: fix round 1/5 (1 addressed, 0 open; snap-t5f1 -> tree)
Task 5: complete (snap-t5 -> tree, review clean after fix round 1)
Ruling: Task 6 may also adjust render.CAMERAS (not only layout.py) when a matched camera clearly fails to frame its photo's view — the cameras are data in render.py, and the ref03 smoke render sits low behind the dry-stone wall — cost if wrong: camera tweaks are by eye, revisited at Ryan's review.
Task 6: dispatched implementer (sonnet — full build + visual judgment) — snapshot snap-t6
Task 6: implementer DONE_WITH_CONCERNS (24/24; cameras re-fitted, layout untouched; concerns = layout mismatches for Ryan's review: oak, chimneys, lattice height, hill steepness); review dispatched (sonnet)
Task 6: minor (deferred): render.py CAMERAS comment overclaims "least-squares fitted"; ref03 location chosen from trials; method not reproducible in-project
Task 6: minor (deferred): build_bag_end.sh --no-render rebuilds compare sheets from stale renders and silently skips missing ones
Task 6: minor (deferred): test_build checks object names only (not data-block duplicates); main() path covered only by manual run
Task 6: minor (deferred): bag_end.blend1 backup and __pycache__ dirs generated in the project
Task 6: minor (deferred): ref03 camera 2.45 m off the door axis because STEPS drift sideways — layout question for Ryan
Task 6: complete (snap-t6 -> tree, review clean)
Final review: dispatched (opus) on review-final.diff (snap-t1 -> tree)
Final review (opus): Ready to build M2 on — with fixes. 0 Critical. Important: (1) model envelope 39.9x26x7.9 m = 459x298x90 mm at 1:87 vs spec ~290x160x60 mm, edges are 28 mm skirts not tapered; (2) 4 chimneys vs spec's 3, oak position contradicts spec/ref09; (3) README/tools/build.sh/bag_end README describe the archived OpenSCAD flow. Minor: no scene.camera; CAMERAS comment overclaims; OPENINGS belong in layout; spec/plan say six fronts (five); turf cliff at garden ends beyond the wall; build.py lacks Blender version guard.
Ruling: Important 1 and 2 are layout/spec decisions for Ryan's M1 review (plan Task 6 Step 7) — not code fixes — cost if wrong: none; M2 waits on his answers.
Ruling: one fix dispatch covers Important 3 + Minor 1 (scene.camera = overview, with a test) + Minor 2 (honest CAMERAS comment) + Minor 4 (five-fronts wording in spec/plan) — the reviewer marked these fix-before-M2 — cost if wrong: none.
Ruling: deferred to later milestones per reviewer triage: OPENINGS -> layout (M2), garden-end cliffs (M4), version guard in build.py, the "can wait" minors; dropped: the "drop" minors — cost if wrong: small cleanup later.
Final fix: dispatched (sonnet) — fix base snap-final1
Final fix: DONE_WITH_CONCERNS (25/25); scoped re-review dispatched
Final fix: re-review — all 4 findings ADDRESSED, no new Critical/Important. 25/25.
Final: parked — README wording: old_openscad/ described as "two earlier attempts" (folder holds only the last); --no-render described as ".blend only" (it also rebuilds compare sheets from existing renders); ".blend opens on the overview camera" (active camera, viewport not looking through it) — Ruling: fix when M2 starts touching these READMEs — cost if wrong: slightly misleading docs until then.
Ruling: no git, so the ledger is preserved at docs/superpowers/ledgers/2026-10-07-bag-end-m1-ledger.md and the workspace (snapshots, briefs, reports) is deleted — the ledger is the only record of rulings — cost if wrong: task reports are gone; rulings and findings survive in the ledger.
MILESTONE 1 COMPLETE — awaiting Ryan's layout review (envelope/size, oak position, chimney count, step axis, hill steepness, bank between door and lattice fronts).

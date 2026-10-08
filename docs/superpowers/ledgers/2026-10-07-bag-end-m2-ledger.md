# SDD ledger — plan: docs/superpowers/plans/2026-10-07-bag-end-m2-door-front.md

Spec: docs/superpowers/specs/2026-10-07-bag-end-blender-design.md (read; updated with the M1 decisions before the plan was written).
Ryan approved the plan 2026-10-07 ("do it, 32cm is fine"); execution method: subagent-driven (his choice since M1).
Ruling: no git in this project, so no worktree or commits; review packages come from directory snapshots (snapdiff.sh snap/diff in this workspace), taken before each task and fix round — the plan's Global Constraints forbid git — cost if wrong: diffs exclude generated files (.blend, png), so reviewers judge those only through reports.
Ruling: the skill's sdd-workspace/task-brief/review-package scripts need git; replaced by this workspace (.superpowers/sdd/bag-end-m2), briefs cut from the plan by "### Task N:" headings with the Global Constraints appended — cost if wrong: none.

## Pre-flight scan

The plan's code was prototyped and run before the plan was written (staged copy: 49/49 tests, full build ~1 min, renders checked by eye).

| Tasks | Shared file / interface | Producer vs consumer | Found |
|---|---|---|---|
| T1→T3 | layout.Front centre/wing_angle/dig_behind; front("door") | layout fields vs doorfront.py (C = F.centre, PHI = wing_angle, placement() reads x/y/floor/yaw) | consistent (staged run) |
| T1→T4 | layout.MODEL_X, LANE_Y, BACK_Y | constants vs test_build footprint test | consistent |
| T1→T3 tests | hill.build() | test_doorfront visibility test builds the hill | consistent; T3 depends on T1's dig_behind=0.6 (mutation-checked: 0.2 makes it fail) |
| T2→T3 | parts API: to_object(mat None ok), cylinder_cutter(matrix), pot(name, mat, coll, matrix), materials() | sources/parts.py vs sources/doorfront.py | consistent (same staged run) |
| T2→T4 | parts.PLASTER/STONE/BRICK/TURF | parts constants vs render.COLOURS | consistent |
| T3→T4 | doorfront.build(); object names doorfront_* | build.py + test_build expects doorfront_door_boards, no front_door | consistent |
| T4→T5 | cameras ref01/ref02, --no-render semantics | render.CAMERAS + build_bag_end.sh vs README text | consistent |
| T5→T2/T3 | sources dir | T5 diffs sources vs copies, then deletes them | consistent; T5 runs last |
| T1 self | tests vs code | staged 25/25 for the four modules; 35/35 full-suite count computed (25 M1 − 15 replaced + 25) not run as a set | count risk only |
| T2 self | test_parts vs parts.py | staged 7/7 | consistent |
| T3 self | test_doorfront vs doorfront.py | staged 4/4 (re-run after wrapping one long line) | consistent |
| T4 self | blockout/render/build tests vs edits | staged 10/10; Step 2 expected-fail list excludes the footprint test (may pass before Step 3) | consistent |
| T5 self | docs text vs tree | README text cites 27.9 × 16.6 m, 6 renders, 5 sheets — matches staged build | consistent |

Plan-mandated items the rubric may flag: T2/T3 say "copy, do not change" — reviewers' code findings on the copied sources are handled by controller rulings, not by implementer edits.

Task 1: dispatched implementer (haiku) — snapshot snap-t1
Task 1: implementer DONE (25/25 focused, 35/35 full); review dispatched (sonnet) on review-t1.diff
Note: Ryan gave a GitHub repo mid-run (github.com/kartoonstew/Lordofthetrains, "set it up at some point") — Ruling: set up git after M2 completes, not mid-plan — switching the review mechanism mid-run risks confusion; M2 lands as the first commits — cost if wrong: a few hours' delay on version control.
Task 1: review — spec ✅ (exact transcription), Needs fixes: 1 Important (plan-mandated): smin(z, dig) sinks the terrace path by up to 0.125 m wherever a dug floor meets level ground (dug floor = terrace = 0 → smin gives −k/4); tests missed it. Verified by controller: new terrace test fails on the unfixed code (−0.083 at x=−20.3, y=−3.4).
Ruling: clamp the blend at the front's floor — z = max(smin(z, d, BLEND), min(z, d, f.floor)) — and add test_terrace_path_stays_level_along_the_row (3 rows × 200 samples, steps excluded); plan Task 1 edited, test counts +1 through Task 4 (26/36/43/47/50), briefs regenerated — verified in staging: 50/50 — cost if wrong: creases at or below a floor are no longer rounded (cosmetic).
Task 1: minor (deferred): shade_smooth() also smooths the skirts, bottom and facade cliffs (render-only; could mark sharp by angle)
Task 1: minor (deferred): facade_v unbounded past the facade's physical end (harmless: bank rise dominates); undocumented
Task 1: minor (deferred): test_dry_stone_wall tolerance 1e-6 vs float32 spacing ~1.9e-6 at x≈−20 (passes deterministically)
Task 1: minor (deferred): test_no_mesh_cell_slopes samples ground(), not the built mesh (pre-existing)
Task 1: minor (noted): report's per-module counts wrong (terrain 9, hill 6), total right
Task 1: fix round 1/5 dispatched (resume implementer) — fix base snap-t1f1
Task 1: fix round 1 implementer DONE (10/10 test_terrain, 26/26 focused, 36/36 full; RED −0.0826 at (−20.3, −3.4)); scoped re-review dispatched (haiku) on review-t1f1.diff
Task 1: fix round 1/5 (1 addressed, 0 open; snap-t1f1 -> tree) — re-review Approved
Task 1: complete (snap-t1 -> tree, review clean after fix round 1)
Task 2: dispatched implementer (haiku) — snapshot snap-t2
Task 2: implementer DONE (7/7, 43/43; copy verified identical by controller cmp); review dispatched (sonnet) on review-t2.diff
Task 2: review — spec ✅ (byte-identical copy, tests match brief), Needs fixes: 2 Important (plan-mandated): (1) bevel_sharp is a silent no-op on every bm.faces.new-built part (no normals → face angle 0), so the door front's bevels (ring, arch, boards, fascia, soffit, bricks) never ran; (2) knee_brace non-manifold (interior partitions) and bevel corrupts it — controller also found its two ellipses cross at ~41°, pinching the brace to zero thickness.
Ruling: bevel_sharp calls bm.normal_update() first; knee_brace rebuilt as one closed prism (concave quarter-ellipse underside, back/top edges sunk 0.03 into post and soffit); bake_cuts keeps the mesh name; is_closed test helper also requires positive volume; tests added test_bevel_rounds_the_edges_of_solids_built_face_by_face, test_knee_brace_is_a_closed_solid_even_when_bevelled, mesh-name assert — sources/parts.py and plan Task 2 updated, counts 9/45/49/52, briefs regenerated; verified in staging: 52/52, every door-front object closed with positive volume, close-up render checked (softer brick/ring edges, solid brackets) — cost if wrong: brace shape is a design call (solid bracket vs curved strut), easily revisited in M3.
Task 2: minor (deferred to M5 print checks): lantern iron is 3 disconnected pieces; strap touches nothing; body hangs 5 mm below the arm (render-invisible)
Task 2: minor (deferred): untested builders (brick_row, door_nails, segmented_ring, header_band, eave_hood, lantern, leaded_glass, rough_stone, pot, sod, extrude, arc_block); materials test asserts 8 of 12 keys; plaster test hard-codes 2*34
Task 2: minor (deferred): rough_stone rng unused; header_band next() without default → bare StopIteration; to_object frees bm only on success
Task 2: minor (noted): report line counts wrong and "no concerns" despite issues
Task 2: fix round 1/5 dispatched (resume implementer) — fix base snap-t2f1
Task 2: fix round 1 implementer DONE (RED 6/9 on the 3 new checks; GREEN 9/9, 45/45; copy verified identical); scoped re-review dispatched (sonnet) on review-t2f1.diff
Task 2: fix round 1/5 (2 Important + 1 nit addressed, 0 open; snap-t2f1 -> tree) — re-review (same reviewer) Approved; brace probed over 5 seeds ± bevel, wobble ≤ 0.004 m vs 0.03 m sink
Task 2: complete (snap-t2 -> tree, review clean after fix round 1)
Task 3: dispatched implementer (haiku) — snapshot snap-t3
Task 3: implementer DONE (4/4, 49/49; copy verified identical); review dispatched (sonnet) on review-t3.diff
Task 3: review — spec ✅ (byte-identical, tests match), Approved, 0 Critical/Important; reviewer verified all 34 objects + cutters follow placement (probe), mirrored side manifold, visibility test non-vacuous (fails at dig_behind ≤ 0.2).
Ruling: strengthen test_door_front_follows_its_layout_placement (plan-mandated weakness on a Review Focus item: default placement is identity and the test checked only wall_centre's bbox, so cutters without placement / parts ignoring place / floor ignored all passed) — new test moves x, y, floor and yaw and requires every object's every vertex to move by place_new @ place_old⁻¹ (KDTree match, < 1e-4); verified in staging: passes, and fails when the door cutter ignores placement — cost if wrong: none.
Ruling: header_band cusp over the arch crown (Minor 5) is intended — refs/02 shows the timber coming down to a point over the crown where the lantern hangs — cost if wrong: cosmetic, revisit with Ryan.
Task 3: minor (deferred to M5): face order of nails/knob/pots varies between builds (vertex positions and face sets identical) — matters only for byte-for-byte STL comparison
Task 3: minor (deferred to M5): mirrored left-side objects (det −1) need winding flipped if export bakes matrix_world itself
Task 3: minor (deferred): doorfront reads facet geometry (C, PHI) at import, placement live — docstring could say so
Task 3: minor (deferred): len(objs) > 30 is a weak count check
Task 3: fix round 1/5 dispatched (resume implementer) — fix base snap-t3f1
Task 3: fix round 1 implementer DONE (4/4, 49/49; test file verified identical to plan block); scoped re-review dispatched (same reviewer) on review-t3f1.diff
Task 3: fix round 1/5 (Minor 1 addressed for cutters and parts ignoring place; 12 random placements all within ~1e-6) — re-review Approved
Task 3: minor (deferred): the placement test is self-consistent with placement(), so placement() itself dropping floor would pass — an independent assert on placement().translation would close it
Task 3: complete (snap-t3 -> tree, review clean after fix round 1)
Task 4: dispatched implementer (sonnet — multi-file integration + full build + visual check) — snapshot snap-t4
Task 4: implementer DONE (RED 5/10 as listed; GREEN 10/10, 52/52; build 1:03, 6 renders + 5 sheets; ref01/02 door + portholes visible); review dispatched (sonnet) on review-t4.diff
Task 4: review — spec ✅ (edit-for-edit; script verified both branches; cameras: 01/02 line up, 09/10/03 frame the scene), Approved, 1 Important (plan-mandated, probe-confirmed): paint()'s fallback material("timber") reuses and mutates parts' detailed "timber" — 16 garden props render in door-front timber, TIMBER constant dead, and the door front's timber depends on build order.
Ruling: paint() names its materials "plain_*" (all of them, not only timber, so no future collision) and skips objects with any real material (any(...)), dead clear() removed; test_paint_gives... expects plain_* names; new test_paint_never_reuses_a_detailed_part_material — plan Task 4 updated (11/11, 53/53), brief regenerated; verified in staging 53/53 — cost if wrong: material names in the .blend change (nothing reads them).
Task 4: minor (deferred): light test doesn't assert exposure; test_build doesn't check duplicate materials
Task 4: minor (noted, M4): large block-out step slab in the ref01 foreground; plain hill, flush-looking door, saturated plaster — look tuning with Ryan
Task 4: fix round 1/5 dispatched (resume implementer) — fix base snap-t4f1
Task 4: fix round 1 implementer DONE (RED 5/7 test_render; GREEN 11/11, 53/53; rebuild 1:03); controller verified paint() and test_render.py identical to the staged versions; scoped re-review dispatched (same reviewer)
Task 4: fix round 1/5 (Important 1 + Minors 1, 2 addressed; ref09 props now plain mid-brown) — re-review Approved
Task 4: minor (noted): new test's second assertion (Base Color linked) is inert; the identity assertion discriminates
Task 4: complete (snap-t4 -> tree, review clean after fix round 1)
Task 5: dispatched implementer (haiku) — snapshot snap-t5
Task 5: implementer DONE (sources verified identical then deleted; READMEs updated); review dispatched (sonnet) on review-t5.diff
Task 5: review — spec ❌ 1 Important: Archive paragraph lost two still-true sentences (brief said replace the first sentence only); Minor: "27.9 × 16.6 m" should be 28.0 (plan-supplied; the old arange grid stopped short); root README still says "attempts" (plural) and --no-render "skips the Cycles renders"; layout.py comments still say "about 30 x 18 cm".
Ruling: one fix round covers all four (restore the two sentences; 28.0; align root README lines 32 and 56; layout.py comments → "about 32 x 19 cm") — docs consistency, all small — cost if wrong: none. Test names keep "about_30_by_18" (they name the target; bounds 300–330 × 170–200 hold).
Task 5: fix round 1/5 dispatched (resume implementer) — fix base snap-t5f1
Task 5: fix round 1 implementer DONE (4 edits; test_layout 7/7); scoped re-review dispatched (same reviewer)
Task 5: fix round 1/5 (4 items addressed) — re-review Approved
Task 5: minor (noted): root README.md:56 now 105 chars, longer than its neighbours
Task 5: complete (snap-t5 -> tree, review clean after fix round 1)
Final review: dispatched (opus) on review-final.diff (snap-t1 -> tree)
Final review (opus): With fixes. 0 Critical; Important: (1) the hill doesn't meet the door front — abrupt dig end (inf beyond dig_behind) leaves 2.5–3.2 m cliffs behind every front and 1.7–2 m slots beside the wall ends (built front narrower than layout width); (2) layout.py not the single source for the door front's size (S and eave heights hard-coded in doorfront.py; built ±1.578 vs layout ±1.758, eave 2.256 vs 2.182). Minors: side walls poke into the door reveal; pots in the door-front collection; portholes are blind recesses; sub-0.3 mm features (cames, lantern posts); placement()/obj() helpers to share in M3. Agrees with all ledger deferrals except the reasoning on facade_v.
Ruling (Important 2): layout carries the door outline — width 2.08D (outer posts, matches refs/01/02; was 2.24D block-out estimate), eave 1.39D, eave_post 1.20D (new Front field), eave_ends 1.10D; layout.eave_top handles faceted fronts (arch over the centre facet from eave_post, straight fall to eave_ends) and works on arrays; doorfront derives S from width, eaves from eave_top; WALL_DEPTH and SOD move to layout — cost if wrong: door eave 6 cm lower than the approved prototype and the side-facet step at the inner posts is gone (sub-mm at HO).
Ruling (Important 1): dig() no longer returns inf behind the facade — floor only within the front's width up to dig_behind; over the wall mass the ground comes down to the turf on the eave (eave_top + SOD) and climbs back at BACK_SLOPE 62°; beside the front it is max(bank, turf); cheek height = eave_ends + SOD over a 0.4 m du ramp; BLEND 0.5 → 0.8 — tuned by renders (45° made troughs up the hill above each front; 62° + 0.8 smooth) — measured: max rise per 0.1 m outside wall masses 0.31–0.75 (was 2.5–3.2), wall ends covered (was −1.7 to −2.1 m) — cost if wrong: look tuning with Ryan.
Ruling (Minor 1): the door cutter also cuts both side walls (they swing back behind the centre facet) — real print defect, one line — cost if wrong: none.
Ruling: tests — test_turf_covers_every_front replaced by test_turf_comes_down_onto_every_front; new test_turf_covers_the_ends_of_every_wall_mass, test_no_cliffs_around_the_fronts, test_eave_line_of_a_faceted_front, test_door_front_is_the_size_layout_says, test_nothing_but_the_door_shows_through_the_doorway; refs_01 test → 2.08D — all 7 fail on the pre-fix tree, 58/58 pass on the fix (staged).
Final: deferred to M3 — pots to a props collection; porthole/window convention (through-cut + non-print glass); shared placement(front) and obj() helpers. Deferred to M5 — minimum feature sizes (cames 0.14 mm, lantern posts 0.23 mm at HO): record before M3 copies the parts.
Final fix: dispatched (sonnet) — fix base snap-final1
Final fix: DONE_WITH_CONCERNS (RED 19/26 = 7 expected; copies identical; GREEN 26/26, 58/58; build 1:04; images: door + portholes clear, turf meets every front; cosmetic concerns: angular shadow on ref01 left bank, soft creases on hill face); report saved by controller (subagent Write refused); scoped re-review dispatched (final reviewer, opus) on review-finalfix.diff
Final fix: re-review (opus) — Important 2 ADDRESSED (posts end exactly at layout half-width 1.633; fascia top = eave + 0.01); Important 1 ADDRESSED for cliffs and turf-on-eave, PARTLY for slots; Minor 1 ADDRESSED (0 plaster hits in the doorway, was 20). No new Critical/Important. Verdict: Ready to build M3 on — Yes.
Final: residual minor → M3 first task: one-cell floor slot behind each door-front outer post (side wall ends are square to the angled facet; dig floors the whole |u| ≤ width/2 band to dig_behind) — limit the floor to the side walls' footprint; neither new test samples that triangle.
Final: residual minor → M3: block-out wall tops poke through the turf (ornate up to 9 cm, lattice 2 cm) — gone when the block-outs are replaced.
Final: residual minor (cosmetic, look tuning with Ryan): lantern now overlaps the top of the door (eave 6 cm lower); soft creases up the hill face from the blend dips; angular cast shadow on the ref01 left bank.
MILESTONE 2 COMPLETE — 58/58 tests, full build 1:04. Ledger preserved at docs/superpowers/ledgers/2026-10-07-bag-end-m2-ledger.md; workspace deleted (no git, so the ledger is the record).

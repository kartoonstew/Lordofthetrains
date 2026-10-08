# SDD ledger — plan: docs/superpowers/plans/2026-10-07-bag-end-m3-fronts.md

Spec: docs/superpowers/specs/2026-10-07-bag-end-blender-design.md (read; updated for M3 before the plan).
Ryan approved 2026-10-07 ("Run it is fine"); git: "You do it" — the controller runs the milestone's git (branch feat/bag-end-m3, commits, push, PR).
Ruling: implementers don't run git; the controller commits each task's files as soon as the implementer reports (so review-package has a BASE..HEAD range) and fix rounds land as follow-up commits — the plan said "commit after review"; committing first is what the review tooling needs — cost if wrong: a reviewed-and-rejected state briefly exists as a commit on the feature branch (fixed by the next commit before merge).
BASE for Task 1: ac24624 (plan commit).

## Pre-flight scan

All code tasks were replayed in order on a scratch copy before the plan was written (RED/GREEN counts in the plan are measured: T1 11/12 + ImportError → 24/24, 58/58; T2 9/10 + ImportError → 16/16, 65/65; T3 7/9 → 9/9, 63/63).

| Tasks | Shared file / interface | Producer vs consumer | Found |
|---|---|---|---|
| T1→T2 | frontkit (Builder, wall, eave, round_window, placement, POST, EAVE_OUT) | frontkit.py vs fronts.py | consistent (replayed) |
| T1→T2 | parts.grid_bars / wheel_bars | called by frontkit.round_window (T1) but defined in T2's parts.py | consistent: nothing calls round_window until T2 (replay passed T1 full suite) |
| T1→T3 | doorfront pots in "props" | footprint + build-twice tests | consistent (T3 replay 63/63) |
| T2→T3 | fronts.build(), object names ornate_bargeboard, lattice_window_window_bars | build.py + test_build | consistent |
| T3→T4 | cameras ref05/ref08, compare sheets | README text | consistent |
| T4→T1-3 | sources dir | T4 diffs all copies then deletes | consistent; runs last |
| T1 self | tests vs code | replayed | consistent |
| T2 self | tests vs code | replayed; 42 new parts all closed solids | consistent |
| T3 self | tests vs code; script pairs | replayed; staged build 1:30, 8 renders | consistent |
| T4 self | README text vs tree | 8 cameras, 7 sheets | consistent |

Task 1: dispatched implementer (haiku); DONE (RED 11/12 + ImportError as planned; GREEN 24/24; 58/58; copies identical — controller cmp) — committed f4a7f80; review dispatched (sonnet)
Task 1: review — spec ✅, Approved, 0 Critical/Important. Minors: (1) set_sharp_from_angle(50°) saw-tooths a hill valley (plan-mandated); (2) nothing pins TUCK; (3) placement test no longer covers the pots (now in props); (4) 6 cm floor sliver behind each door-front outer post (limit is the post's outer face, slab ends at S); (5) TUCK deepens transitional block-out wall-top exposure (gone in Task 3); (6) doorfront.COLL unused.
Ruling: drop set_sharp_from_angle — controller render comparison shows TUCK alone removes the ornate-wing dark band, and without hard edges the valley is smooth — hill.py restored to main's version (controller, git restore); plan Task 1 no longer touches hill.py — cost if wrong: skirts/creases render soft (render-only).
Ruling: add test_the_sod_shows_on_top_of_the_door_front_not_the_hill (downward rays onto the centre facet hit doorfront_sod_centre; verified fails at TUCK=0); remove unused doorfront.COLL; counts +1 (25/59/66/64), briefs regenerated — cost if wrong: none.
Task 1: minor (deferred, M4 terrain pass): 6 cm floor sliver behind each door-front outer post; pots not covered by the placement test.
Task 1: fix round 1/5 dispatched (resume implementer) — fix base f4a7f80 (+ controller's hill.py restore in the working tree)
Task 1: fix round 1 implementer DONE (25/25, 59/59; copies identical) — committed 04f8d0a (+ plan/sources docs commit); scoped re-review dispatched (same reviewer)
Task 1: fix round 1/5 (3 addressed, 0 open) — re-review Approved
Task 1: complete (ac24624 -> 04f8d0a, review clean after fix round 1)
Task 2: dispatched implementer (haiku) — BASE e52fe4c
Task 2: implementer DONE (RED 9/10 + ImportError; GREEN 16/16; 66/66; copies identical) — committed 241b24a; review dispatched (sonnet)
Task 2: review — spec ✅ (byte-identical; values match blockout.OPENINGS), Approved, 0 Critical/Important; all 42 parts closed. Minors: (1) window-visibility assertion vacuous for the three fronts with "window" in their names (plastered-over passes); (2) ornate outer posts sized at their centre poke 0.30 above the steep eave edge; (3) bargeboard knots embed 0.005 m; arched glass/cut 0.07–0.09/0.10 vs round 0.071–0.091/0.09; unused grow param; (4) eave sampling coarse on the ornate (60 over 7.46 m; chord sag up to 0.1 m; faceted sod); (5) bargeboard test checks only the crown; glazing test bound loose; (6) data dup until Task 3; (7) bar width ~0.3 mm at HO (M5).
Ruling: fix 1–5 now in one fix round (cheap, real): suffix-based window assertion (verified it now fails when windows are plastered over); outer post height = eave at its outer edge, brace lands under it; knots at v −0.575; arched cut 0.09 / glass 0.071–0.091; grow removed; frontkit.samples by step (0.03 m; bargeboard 0.02 m) — touches Task 1's frontkit.py, ruled in scope because the defect shows on Task 2's front; bargeboard test samples the band at 0, ±0.5–0.8 arch — staged: 64/64 at the final state, 42 parts closed — cost if wrong: none.
Task 2: minor (deferred to M5): glazing bars ~0.3 mm wide at HO; glazing-bar test bound loose.
Task 2: fix round 1/5 dispatched (resume implementer) — fix base 241b24a
Task 2: fix round 1 implementer DONE (stricter test failed first on the bargeboard at u=0.981, then 23/23, 66/66; copies identical) — committed 0b458b4 (+ sources docs commit); scoped re-review dispatched (same reviewer)
Task 2: fix round 1/5 (5 addressed, 0 open) — re-review Approved; chord sag 0.103→0.044 (eave), 0.135→0.076 (band); fronts build 1.1 s
Task 2: minor (queued for the final fix batch): ornate_soffit board pokes 0.05–0.16 above the sod at the arch shoulder (eave_hood boards sit at their centre's eave height; eave falls steeply there) — fix: board at the lower eave of its two edges
Task 2: minor (noted): post top up to 0.09 below the header band for u≈1.81–1.845 (small plaster notch)
Task 2: complete (e52fe4c -> 0b458b4, review clean after fix round 1)
Task 3: dispatched implementer (sonnet — integration + full build + visual check) — BASE e06be38
Task 3: implementer DONE (RED 7/9; GREEN 9/9; 64/64; build 1:29, 7 sheets; images OK; concerns: README blockout bullet stale (Task 4), stale pyc) — committed 3752802; review dispatched (sonnet)
Task 3: review — spec ✅ (byte-identical; no blockout/front_/eave_/window_ references left; ref05/ref08 frame their photos), Approved, 0 Critical/Important.
Task 3: minor (queued for the final fix batch): render.paint docstring still says "for block-out parts" (now garden/preview props); garden.py docstring still says "Milestone 1 block-out".
Task 3: minor (noted): turf green shows between the ornate bargeboard's soffit rails from below (hill beneath, not a hole); paint test doesn't cover step_/wall_/hill paths (pre-existing).
Task 3: stale blockout .pyc deleted by controller (gitignored anyway).
Task 3: complete (e06be38 -> 3752802, review clean)
Task 4: dispatched implementer (haiku) — BASE 3752802
Task 4: implementer DONE (sources diffed clean, deleted; READMEs updated) — committed e3a2912; review dispatched (sonnet)
Task 4: review — 1 Important: the "Where things land" edit dropped which comparison views line up (01–03, 05, 08) and that 09/10 only frame the compressed hill (brief gap); Minor: the plan still points at the deleted sources folder.
Ruling: restore the line-up/compression sentence with the new views; add an "After execution" note to the plan — cost if wrong: none.
Task 4: fix round 1/5 (both addressed; controller checked the two-line diff directly — docs-only, exact text) — committed
Task 4: complete (3752802 -> HEAD)
Final review: dispatched (opus) on the branch diff main..feat/bag-end-m3
Final review (opus): Ready to merge — With fixes. 0 Critical; Important: (1) ornate soffit boards step like ladder rungs on the steep arch (the queued "lower edge" fix would widen the gaps); (2) the bargeboard band and beads taper to slivers at the feet (vertical offset from an eave that turns vertical) and knots spill off; (3) LAMPS[0] stands in front of the ornate front's wing window (the window test never built the garden). Minors: TUCK fails at concave eave corners and along the door's side facets (hill up to 0.20 above sod, invisible but matters for M5 pockets); lattice glazing doesn't match refs/05 (central square + cross + diagonals); ornate upper plaster bare (refs show studs); ornate knee braces short of its 0.5 m hood; unused frontkit options and repeated 0.09 recess literal; docs overstate which views line up; parts.py:16 stale comment; long non-planar wobbled caps (M5 triangulate).
Ruling (one fix dispatch): soffit boards are sloped prisms following the eave across their width (parts.eave_hood); bargeboard built from frontkit.arch_offset (normal offset of the elliptical arch, sampled by angle), beads likewise, corbel block at each foot, knots on the centre line rotated to the tangent; LAMPS[0] → (−10.0, −0.7) and the window test builds the garden; plus the cheap minors: refs/05 lattice glazing (parts.lattice_bars replaces grid_bars), three studs above the ornate window, knee-brace depth = hood depth − 0.06, docs wording (README + spec Checking list), stale docstrings (render.paint, garden.py, parts.py:16). New tests: bargeboard keeps its width down the flanks; arch_offset keeps its distance; soffit boards follow the eave; the garden-built window test — all fail on the branch, 67/67 on the fix (staged), 42 parts closed, renders checked — cost if wrong: look changes Ryan hasn't seen (sent with the PR).
Final: deferred → M4/M5: TUCK at concave corners and door side facets (sample turf along facets; min eave_top over ±STEP; extend the sod test to all fronts); K.RECESS constant; unused frontkit options; non-planar cap triangulation before STL export.
Final fix: dispatched (sonnet) — base a01a443
Final fix: DONE (RED 14/19 = 5 expected; GREEN 19/19, 67/67; build OK, 7 sheets; renders: even bargeboard + corbels, continuous soffit, refs/05 lattice, no window blocked) — committed 32ecb59; scoped re-review dispatched (final reviewer, opus)
Final fix: re-review (opus) — Important 1, 2, 3 ADDRESSED (continuous soffit; true normal-offset band, no fold, knots inside, corbels attached; lamp between window and arch); minors done. No new Critical/Important. Ready to merge: Yes.
Final: residual minors → M4 look pass: studs stop 0.13–0.15 below the header band (z1 ≈ top(u) − 0.10); lattice centre square 0.34 r vs ~0.5 r in refs/05; bead ends 0.02 proud of the corbel faces.
MILESTONE 3 COMPLETE — 67/67 tests, build ~1.5 min, 7 comparison sheets. Ledger preserved at docs/superpowers/ledgers/2026-10-07-bag-end-m3-ledger.md; PR opened from feat/bag-end-m3.

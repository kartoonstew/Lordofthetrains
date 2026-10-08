# Wood prototype: grain, checks, knots and worn arrises on every timber part

Ryan: "the wood features have no grain or texture." Every timber part was a smooth box (bent a
little), a smooth extrusion or a smooth arc. Now all of it is built as weathered, hand-worked oak,
in geometry that prints.

## The idea

Every piece of timber is a **sweep**: a cross-section carried along the piece's grain. The
section's points are a few mm apart across the grain and its stations a few cm apart along it
(1 cm apart over a knot), so there are vertices where the relief needs them and few elsewhere. A
height field over the surface, in the piece's own frame (s along the grain; `along` across a face,
measured from that face's corner), moves each point along its section's normal. Because the frame
is the piece's own, a turned beam (`rot`), a curved ring segment or a knee brace bent round its
curve all carry their grain the right way.

The relief, laid out per piece from a seeded `random.Random` and `mathutils.noise`:

- **grain**: open, weathered grooves running the length of each face, wandering a little (two
  octaves of noise) and fading in and out along the piece; now and then a finer, shallower line
  between two of them. Grooves fade out before the rounded corners. A narrow face (less than 6 cm
  between its usual worn corners: a leg, a rail's edge, an arm, a fascia's underside) gets one or
  two lines, off centre, instead: one full groove down its middle made a moulding of it.
  - Through 8 cm or more of wood (`THICK`: posts, beams, the header band's face, the door ring's
    lining where the ring is 8 cm or more, the lattice window's ring) the grain is cut deeper, a
    little wider apart, and fades less (revision 2, below).
  - Through 3.5-8 cm (`MID`: the door boards, bench planks, legs and rails, gate boards, fascias,
    soffit boards, knee braces) it keeps its depth but fades less too, and narrow faces' lines are
    cut about as deep (revision 3, below).
- **checks**: long, lens-shaped, deeper splits along the grain on the faces of posts and beams
  (1-3 on a big post); and **splits** running in from a worn end, deepest at the end.
- **knots**: an oval, standing a few mm proud (a hard knot left as the wood wore) or sunk (where
  one fell out), with a groove round it and the grain lines swerving past it.
- **worn arrises**: each corner's radius wanders along the piece, with the odd ding; ends are
  chamfered, cut a little out of square and split. The bevel in `parts.to_object` now leaves wood
  alone (it would only bead the grooves).

The section on the face of a header band or fascia is measured from its top edge, so the grain
follows the arched eave and the band's arched lower edge cuts across it, as on a real board. The
knee brace is swept along its curved underside, so its grain follows the curve. The round door's
boards keep their grid (their ends are cut on the circle) with grain on their faces and rolled
edges. The letterbox is a weathered log (bark long gone): deep furrows, long checks, growth rings
and radial splits across its ends. The gate's ball tops are turned finials, smooth but checked.

Everything only cuts into the wood (but a knot, at most 5 mm proud), no deeper than 20 % (grain)
or 30 % (checks, splits) of the piece's thickness through that face, so every piece stays one
closed shell that does not pass through itself. Three things had to be got right for that, each
found by the self-intersection check:

1. **End caps are one face, ear-clipped.** Deep grooves make a sawn section's outline far from
   star-shaped, so a fan or rings from its centre fold. A flat cap, triangulated by ear clipping
   (with its normal set first: a new face has none, and the triangulator projects along it), is
   always clean. Only round logs, cut radially, get ringed ends (growth rings, end splits).
2. **The bend stays in each station's plane.** At the steep feet of an arched eave a band's top
   meets its end face at about 14 degrees; `parts.wobble`'s 3-D bend tilted the end through it.
3. **Cuts follow the section's frame, not its true normal.** A soffit board at the foot of an arch
   is a parallelogram sheared to about 17 degrees; displacing along the true normal slid points
   sideways and folded it.
4. **Near a corner, nothing cuts deeper than its distance from that corner** (revision 2). With
   2.4 cm grooves a groove on one face could run into a groove on the face round the corner; capping
   each cut at its distance from the sharp corner the rounding stands for makes that impossible.

## Revision 3: grain that reads at HO on the door and thinner pieces

After revision 2 the door boards and the 3.5-8 cm pieces still had grain about 0.5 cm deep along its
length (0.05 mm at HO), and the narrow faces' lines about 0.15 cm: they would have printed smooth.
Now, on every face with 3.5 cm or more of wood behind it:

- grooves fade along the piece as on the thick pieces (from 100 % down to about 60 %, not 10 %);
  their deepest stays 1.0-1.6 cm, under the 20 % cap;
- a narrow face (under 6 cm between its worn corners: legs, rails' edges, a plank's edge, the door
  ring's and porthole frames' fronts, the fascia's underside, the knee brace's underside) gets one or
  two off-centre lines (never none) 0.7-0.9 cm deep at their deepest, with the same eased fade;
- the door boards lose their 0.75 factor (it scaled their checks and knots too: the checks may now
  reach 1.8 cm, the 30 % cap on 6 cm);
- the knee brace's underside is sized by its typical depth (about 15 cm), not the 3 cm at its buried
  ends, which had held its lines at 0.6 cm. The cut per point is still capped at 30 % of the depth
  there, so its ends stay safe.

Under 3.5 cm (only the birdhouse roof boards, 3 cm) the faces are as they were; their narrow 3 cm
edges, with 24 cm behind them, get the deeper lines. Thick pieces, the log and the finials are as
they were.

Depth along the grain (`proto_out/groove_depths.py`, 40 seeds), now and after revision 2:

| piece | main grooves: p10 / median / p90 | was | narrow-face lines: median | was |
|---|---|---|---|---|
| door board (6 cm) | 0.92 / 1.09 / 1.20 cm (median 0.13 mm at HO) | 0.25 / 0.48 / 0.72 cm (with the 0.75) | | |
| bench seat plank 12 x 4 | 0.64 / 0.76 / 0.80 cm (0.09 mm) | 0.22 / 0.44 / 0.66 cm | 0.75 cm (its edges) | 0.17 cm |
| bench back rail 11 x 3.5 | 0.57 / 0.67 / 0.70 cm (20 % cap: 0.7) | 0.20 / 0.38 / 0.58 cm | 0.75 cm | 0.16 cm |
| bench leg 7 x 7 | (narrow faces only) | | 0.75 cm (p10 0.63, p90 0.85) | 0.15 cm |
| gate board 18 x 4 | 0.65 / 0.76 / 0.80 cm | 0.21 / 0.44 / 0.66 cm | 0.74 cm | 0.15 cm |
| birdhouse roof board 24 x 3 | 0.16 / 0.33 / 0.49 cm (unchanged) | the same | 0.74 cm | 0.17 cm |
| 12 cm post (revision 2) | 1.50 / 1.82 / 2.24 cm (unchanged) | the same | | |

Trade-off: with its depth more even, a groove runs more steadily down a door board, and the door
reads a little more regular (nearer to fluting) than in revision 2; `sheet_thin_clay.png` shows
both. If that's too even, letting a third of each board's grooves keep the old, stronger fade
would break it up again.

## Revision 2: deeper grain on thick pieces

The first pass cut main grooves 1.0-1.6 cm deep, but that was each groove's deepest point: the fade
along the piece left a groove's median depth at about 0.7 cm (0.08 mm at HO), so most of it would
not have shown once painted. (The first version of this table gave only the 1.0-1.6 cm peak, which
overstated it.) Now, on any face with 8 cm or more of wood behind it:

- grooves are cut 1.6-2.4 cm deep (0.18-0.28 mm at HO), still capped at 20 % of the thickness,
- spaced 3.4-5.2 cm apart instead of 3.0-4.8, and
- fade along the piece only from 100 % down to about 60 % (it was 100 % down to 10 %).

Measured along the grooves (`proto_out/groove_depths.py`, 40 seeds, 2 m pieces):

| piece | depth along the main grooves, p10 / median / p90 | was (first pass) |
|---|---|---|
| 12 cm post | 1.50 / 1.82 / 2.24 cm (0.17 / 0.21 / 0.26 mm) | 0.33 / 0.69 / 1.09 cm |
| 16 cm gate post | 1.50 / 1.83 / 2.23 cm | 0.36 / 0.71 / 1.09 cm |
| 10 cm rack post (20 % cap: 2.0 cm) | 1.48 / 1.77 / 2.00 cm | 0.35 / 0.71 / 1.10 cm |
| 4 cm plank face (unchanged) | 0.22 / 0.44 / 0.66 cm | the same |
| 7 cm bench leg (unchanged) | fine lines only, 0.4-0.7 cm | the same |

Checks, splits, knots, worn corners, thin boards and the log are as they were. The grain lines now
draw on their own random stream, so retuning them no longer moves the knots and checks. This
change did move them once, though: in the gate view both posts' knots now sit on faces the camera
does not see (one on the outer side, one on the back), and a long check shows instead. Knot
frequency is unchanged at about 0.6 per post.

## Files

- `bagend/wood.py` (new): `Grain` (the relief), `sweep` (the shell), `rect_section`,
  `circle_section`, `worn_radii`, and the builders: `timber`, `arc_timber`, `segmented_ring`,
  `header_band`, `eave_hood`, `soffit_board`, `knee_brace`, `plank_door`, `door_board`, `log`,
  `finial`.
- `bagend/parts.py`: `to_object` drops the "wood" vertex tag; `bevel_sharp` skips edges between
  two wood vertices. `timber`, `plank_door`, `segmented_ring`, `header_band`, `eave_hood` and
  `knee_brace` moved to wood.py (removed here; nothing else used them). Untouched: everything the
  stone prototype changes (`rough_stone`, `flagstone`), materials, lantern, glazing bars.
- `bagend/frontkit.py`, `doorfront.py`: `P.` -> `W.` for those builders; posts pass `hidden=(2,)`
  (their back is in the wall: built coarse, uncut).
- `bagend/fronts.py`: the spare ornate front's timbers and its two arches (`P.arc_block` ->
  `W.arc_timber`).
- `bagend/props.py`: every prop through `W.timber`; the letterbox log is `W.log`; the gate's ball
  tops are `W.finial`; the birdhouse box is a plank-clad timber (`seams`) under two board roof
  slabs; the lamp post gains a timber arm and a brace under it (inside its `lamp_0_post` object).
- The shared `rng` of each front is drawn on exactly as before (door, rings, soffit), so bricks,
  nails and everything built after are where they were (there is a test for it).
- `bake_cuts` (EXACT booleans) only ever cuts the plaster walls; no timber is cut, so denser
  timber does not slow it.

## Relief sizes (real cm; mm at HO 1:87)

| feature | width | depth |
|---|---|---|
| grain groove, face with 8 cm+ of wood behind it | 2.0-2.8 cm (0.23-0.32 mm), 3.4-5.2 cm apart | 1.6-2.4 cm (0.18-0.28 mm) at its deepest; median along it 1.8 cm (0.21 mm) |
| grain groove, 3.5-8 cm behind it | 2.0-2.8 cm (0.23-0.32 mm), 3.0-4.8 cm apart | 1.0-1.6 cm at its deepest, under the 20 % cap; median along it 0.67 cm (3.5 cm rail) to 1.1 cm (door, 6 cm) |
| grain groove, under 3.5 cm (roof boards) | 2.0-2.8 cm, 3.0-4.8 cm apart | 0.6 cm at most (20 % of 3 cm); median along it 0.33 cm |
| line on a narrow face, 3.5 cm+ behind it | 1.2-1.6 cm (0.14-0.18 mm), one or two | 0.7-0.9 cm at its deepest; median along it 0.75 cm (0.09 mm) |
| fine line between two grooves, and on narrow faces of thinner wood | 1.2-1.6 cm (0.14-0.18 mm) | 0.4-0.7 cm (bonus at HO, shows at O) |
| check (face) | 1.5-2.1 cm (0.17-0.24 mm), 30-75 % of the piece long | 1.8-2.8 cm (0.21-0.32 mm) |
| split from an end | 1.5-2.1 cm, 8-30 cm long | 1.5-2.5 cm at the end |
| knot | 5-8 cm along x 3.2-4.6 cm across (0.6-0.9 x 0.4-0.5 mm) | +0.3-0.5 cm proud or 0.8-1.3 cm sunk; rim groove 0.5 cm |
| worn corner radius | about 15 % of the thinner side, wandering +-45 %, dings, at most 30 % | |
| end chamfer | 0.3-0.9 cm in over 0.5-1.6 cm | end cut up to ~0.6 cm out of square |
| board seams (birdhouse) | 1.2 cm | 0.8 cm |
| log | furrows 1.4x deeper and 1.15x wider; growth rings every 2.6 cm, 0.3 cm deep | |

All capped at 20 % (grain) / 30 % (cuts) of the thickness through that face, so thin boards get
shallower grain (a 4 cm bench plank: 0.8 cm grain at most, 1.2 cm checks). The turned finials have
checks only. Within the distance of a face's corner, no cut goes deeper than that distance.

## Vertex counts and build time

Mesh spacing: 0.7 cm across the grain on faces that show, 3 cm on hidden faces, 4.5 cm along
(1 cm over knots, 2.5 cm up the door boards). Wood vertices, before -> after:

| object | before | after |
|---|---|---|
| doorfront_door_boards | 3,696 | 15,922 |
| doorfront_door_ring | 1,640 | 11,422 |
| doorfront_timber_centre (inner posts, braces, header) | 1,236 | 12,238 |
| doorfront_left/right_timber | 524 / 524 | 7,245 / 7,245 |
| doorfront fascias (centre, left, right) | 748 / 284 / 284 | 2,684 / 924 / 924 |
| doorfront soffits (centre, left, right) | 936 / 392 / 448 | 4,032 / 1,656 / 1,824 |
| doorfront porthole frames (2) | 984 / 984 | 2,306 / 2,333 |
| round_window_left_timber / fascia / soffit / window_frame | 1,444 / 964 / 1,272 / 1,148 | 15,610 / 3,476 / 5,400 / 2,880 |
| lattice_window_timber / fascia / soffit / window_frame | 1,324 / 844 / 1,160 / 1,640 | 14,772 / 3,036 / 4,856 / 4,720 |
| bench | 1,664 | 14,296 |
| gate | 1,764 | 23,900 |
| letterbox | 248 | 6,040 |
| lamp_0_post | 128 | 3,736 |
| birdhouse | 296 | 5,328 |
| glazing bars (unchanged) | 1,384 | 1,384 |
| **all wood** | **27,960** | **180,189 (+152,229)** |
| whole scene | 147,418 | 299,647 |

A 2 m post is about 3,000 vertices. The gate is the largest (16 cm posts, five boards, two
finials).

Build, `time tools/build_bag_end.sh --no-render`, three runs each, back to back on this machine:
**8.7 s** (8.3, 8.7, 9.1 s) against **5.7 s** (6.0, 5.1, 5.9 s) for the unchanged code built from a
copy of the base, on a busier machine than earlier (revision 2 measured 6.2 against 3.4 s, the first
pass 5.3 against 3.6 s). The gap stays about 3 s. Revision 3 changed only depths, so the vertex
counts are as revision 2's. The brief's ~1.5 min is the build with its renders; the wood adds about
3 s to it. (Counts: `proto_out/counts_before.txt`, `counts_after.txt`.)

## Tests

`tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py`: **89/89 passed** (78/78 at the
start; three moved, fourteen added). Output in `proto_out/tests_run.txt`.

Changed (test_parts.py), because the builders moved to wood.py:
- `test_wobble_is_repeatable_per_seed_and_small` -> `test_wood.test_timber_is_repeatable_per_seed_and_stays_near_its_box` (same bounds, `W.timber`).
- `test_timber_and_plaster_come_out_as_closed_solids` -> `test_plaster_comes_out_as_a_closed_solid` (the timber half is covered, far harder, in test_wood).
- `test_knee_brace_is_a_closed_solid_even_when_bevelled` and `test_door_boards_stay_inside_the_doorway` -> moved unchanged to test_wood.py, calling `W.`.

Added (test_wood.py):
- `test_every_kind_of_wood_is_closed_and_never_passes_through_itself`: posts (straight and
  turned), plank, rail, diagonal brace, plank-clad box, door ring, window ring, knee brace, header
  band and eave hood under an arch with vertical feet, door, log and finial, three seeds each:
  closed after `to_object` with a bevel, and no shell crossing itself (BVH candidates confirmed by
  an exact edge-triangle test; touching or overlapping separate shells are allowed, as before).
- `test_grain_cuts_in_deep_enough_to_print_and_no_deeper_than_safe`: down the middle of each face
  of a 12 cm post the cuts reach > 1.5 cm somewhere and never exceed 30 % of its thickness; 10-75 %
  of the face is cut > 4 mm (grooves with wood between); nothing stands proud by 6 mm or more.
- `test_thick_faces_get_deeper_grain` (revision 2; renamed in revision 3 from
  `..._and_thin_boards_keep_theirs`, whose thin-board half moved to the next test): on a 12 cm face
  every main groove is 1.6-2.4 cm deep at its deepest, and over the main grooves' whole length
  80 % is at least 1.4 cm deep.
- `test_door_boards_and_thin_pieces_have_grain_that_reads_at_ho` (revision 3): along their length,
  door-board grooves have a median depth of 0.9-1.25 cm, a 4 cm plank's and a 7 cm leg's 0.65-0.85 cm;
  every face of the leg has a line; all within 20 % of the thickness; a 3 cm board's faces keep the
  old fade.
- `test_door_board_cuts_reach_about_a_centimetre_and_no_further_than_safe` (revision 3): a built
  board, unbent, is cut over 0.9 cm deep in places and never past 30 % of its 6 cm.
- `test_grain_is_cut_in_the_pieces_own_frame`: a beam turned 0.7 rad keeps its relief inside its
  own box.
- `test_ring_segments_follow_their_curve_and_only_cut_in`.
- `test_wood_uses_the_shared_rng_as_the_plain_parts_did`: door, rings and soffit leave a front's
  rng exactly where the plain parts did.
- `test_bevel_leaves_wood_alone_and_the_wood_tag_is_not_kept`.
- `test_wood_vertex_counts_stay_sane`: a 2 m post is 1,500-6,000 vertices.
- `test_every_timber_object_in_the_scene_is_closed`: every timber, ring, door and painted-frame
  object of the built fronts and garden.

## Every wooden part, and what it got

Door front
- centre facet: 2 inner posts (turned with the facets), 2 knee braces, the header band, the
  curved fascia, every soffit board: grain, checks, knots, worn corners; braces grained round
  their curve; header and fascia grain following the eave.
- each side facet: outer post, knee brace, header band, fascia, soffit boards: the same.
- the green door: 13 boards, grain on their faces, rolled edges, sunk knots, splits at their
  ends (nails unchanged).
- the grey door ring: 10 curved segments, grain round the curve on the front and the lining,
  V-worn joints, the odd check and knot.
- the two porthole frames (green): 6 curved segments each, as the ring.
- not timber, unchanged: the lantern and its bracket (iron), the knob (brass), nails, glass and
  cames.

Round window (left) and lattice window fronts
- 2 posts, 2 knee braces, header band, fascia, soffit boards: as the door front.
- the window ring (timber): curved segments, as the door ring (the lattice one is the heavy ring).
- left as they were (per the brief): the glazing bars (lattice and wheel), 2.5-4 cm thin.

Garden props
- bench: 3 seat planks, 2 back rails, 4 legs, 2 back posts, 2 cross rails.
- gate: 2 posts with turned, checked ball finials, 5 boards, 2 rails, the brace. (The sign board
  on it is the stone-coloured placard: left flat, it carries the notice.)
- letterbox: its post, and the log (furrows, checks, knot, growth rings and splits on its ends).
- lamp post: the post, plus a new timber arm and a brace under it. The lantern (`parts.lantern`,
  iron, unchanged) still brings its own top bar, now inside the timber arm, and its lower iron
  stay, a thin horizontal bar that shows under the brace.
- birdhouse: the pole, the box (now plank-clad: vertical board seams with grain), 2 roof boards.
- rack (not in the compact scene, layout.RACK = None): 2 posts, 2 braces, 2 rails, through the
  same `W.timber`.

Spare ornate front (not in this scene): jambs, sill, the window arch, the half-timber posts,
braces, studs and arch are grained; its carved bargeboard and its knots are still the plain
extrusion.

No moss or greenery geometry anywhere.

## Renders (proto_out/)

- `sheet_clay.png`, `sheet_colour.png`: before | after, for the door front straight on (like
  refs/01), the door close-up with its ring and a post with its knee brace (like refs/02), the
  lattice window front, the bench, gate and letterbox (like refs/04), and the lamp post.
- `sheet_detail_clay.png`, `sheet_detail_colour.png`: closer still: the inner post and door ring,
  the knee brace side on along the facade, and the gate and letterbox log.
- `sheet_deeper_clay.png` (revision 2): post, brace and gate in clay, before | first pass |
  deeper grain.
- `sheet_thin_clay.png` (revision 3): the door boards close and the bench in clay, revision 2 |
  revision 3. The other sheets and `gallery_clay.png` still show the first pass.
- `gallery_clay.png`: the pieces on their own (post with brace, header band, ring, door boards,
  log, plank, gate post with finial).
- `renders/`: every single render. Scripts: `render_views.py` (cameras, clay override with a
  20-22 degree raking sun, colour with the scene's own light), `sheet.py`, `gallery.py`,
  `smoke_wood.py` + `meshcheck.py` (closed / self-crossing check over many seeds; 24 seeds of
  all 14 piece kinds pass after revision 2), `groove_depths.py` (depth along the grooves),
  `inspect_counts.py`, `before.blend` / `after.blend`.

## Not right yet, and next steps

- The grain is the same kind of groove everywhere; real weathered oak also shows medullary-ray
  flecks and the odd raised, bleached ridge. At HO those would be under the print's resolution,
  but at O scale a finer second pass (0.4 cm) on large faces would read. Costs vertices.
- End grain on sawn pieces is a flat cap with notched outline (no rings or cross-cap splits): the
  ring/fan caps folded on non-star outlines. A constrained triangulation with interior points
  (or a ring cap on a convexified copy of the outline) would allow rings on post ends too.
- The knee brace is grained along its curve as one crook; the photos' brackets look like a plank
  cut to shape, whose grain would run straight across the curve. Both read as wood at HO.
- The door boards are fairly regular (similar groove counts per board, and since revision 3 a
  steadier depth); a little more variety in board width and grain, or a few boards with a long
  check, would loosen it.
- The ornate front's bargeboard is still smooth (it is not in this scene).
- The lamp post's lantern still carries the wall lantern's lower iron stay; with a timber arm and
  brace it is redundant. `parts.lantern` could take a flag to leave it off for a post.
- The birdhouse's 3 cm roof boards still have shallow grain on their faces (median 0.33 cm), under
  the 3.5 cm line; at HO they are 0.35 mm boards, and their edges do get the deeper lines.
- The fine lines between two main grooves (0.4-0.7 cm) are a bonus that shows only at O scale.
- Vertex count roughly doubled the scene (+152k). If a slicer struggles, STEP_ACROSS 0.7 -> 0.9 cm
  and STEP_ALONG 4.5 -> 6 cm cut the wood by about 40 % with little visible loss at HO.

# Stone prototype: the stone path and stone texture (revision 2)

Ryan's notes this answers: the walkway "needs more density and realistic textures", and the stones
have "no grain or texture". No moss or greenery is modelled: every stone is bare relief for paint,
drybrushing and his own scenery moss.

Revision 2 follows the coordinator's comparison with refs/04, 05 and 07. Revision 1 had put the
steps in a cutting lined with dry-stone cheek walls. Revision 2 has:

- no cutting and no cheek walls;
- a dense run of long, narrow slate treads set into an open grassy bank, each stacked on the one
  below, winding down to the right from the door to the gate;
- flatter, more slab-like wall stones;
- the beds back near their original spots.

The stone-making approach in `stone.py` (fracture, chips, laminae) is unchanged.

Sheets (before | after, one row per view):

- `proto_out/sheet_clay.png`: clay, raking sun 22 degrees. Views: from the gate up to the door
  (like refs/04), up the steps from the right (like refs/05), a close-up of the wall's end at the
  gap and a couple of steps, and the whole garden from above.
- `proto_out/sheet_colour.png`: the same views in the scene's own materials and light.
- `proto_out/sheet_extra_clay.png`, `sheet_extra_colour.png`: down the steps from the landing, the
  landing at the door, the dry-stone wall's face close up, and the chimney's cap.
- Single renders are in `proto_out/final/`. `proto_out/before.blend` and `after.blend` are the
  scenes they came from.

## The design

### One way of making stone

This is `bagend/stone.py`, a new module. Every stone starts as a convex block: a box whose faces are
tilted a little and whose corners and edges are split off by fracture planes. That gives flat split
faces with breaks between them. On that block go the marks of splitting and weather:

- chips scooped out of the arrises;
- pits in the faces;
- on slate, layered edges and flaked-off patches of the top lamina;
- on wall stones, bedding layers.

The surface is a lattice over the box's faces, one vertex per 2 cm (slate) or 2.2 cm (rubble).
Each lattice point moves along a ray from the nearest point of a smaller core box inside the stone:
first to where the ray meets the fractured block, then in or out along the same ray for the marks.

- Rays from a convex core never cross, so a stone's shell can't fold through itself however rough
  it gets. A test checks this with a BVH overlap.
- Fracture edges are rounded over about 0.7 cm with a smooth minimum, so the lattice doesn't alias
  them into a saw-tooth.
- A wall stone's hidden back gets a coarse lattice; only its face gets the fine one.
- Stones are collected in a `Pile` and turned into one mesh per object with numpy, not bmesh.

Three styles:

- `RUBBLE`, for wall stones: flat beds (top and bottom tilted at most 3 degrees), splits mostly
  square to the beds, 65% of them showing bedding layers 3-5.5 cm thick, and the show face split
  again into 1-3 facets.
- `SLATE`, for treads, risers, capstones, the chimney cap and the door sill: a flat cleaved top,
  layered edges and spalls.
- `FLAG`, for the landing flags: slate, worn flatter.

### The path

This is `stone.path()`. Its positions are `layout.STEPS`, `LANDING`, `STEP_LENGTH`, `TREAD`,
`RISER_DEPTH` and `BANK`.

- **Landing** (`layout.LANDING`). Six slate flags in front of the door sill, between the door pots,
  with open joints of 1.8-3 cm. Their tops sit 1.8-2.8 cm proud of the terrace.
- **Route.** The steps follow the original `layout.STEPS` line, a gentle curve winding down to the
  right from the door, through the wall's gap, to the gate. There are now 13 treads instead of 5.
  The open going is 0.27-0.32 m (about 0.3 m) and the rises are 5-13 cm. The top tread is level
  with the landing, and the tread in the wall's gap is at the lawn. The last tread's front is
  20 cm short of the gate.
- **Treads.** Each tread is one long, narrow slab, 0.95-1.3 m across by about 0.4 m front to back.
  One in five is two slabs side by side, as in refs/05. Each slab is set up to 8 cm off-centre and
  turned up to 3.5 degrees. Its back runs 6-11 cm behind the riser line, under the tread above, and its
  nose overhangs 1.5-3 cm. It falls a little forward.
- **Stacked like refs/05.** Each tread's front rests straight on the back of the tread below. Its
  own 7-13 cm edge is the riser. Where the rise is more than the slab is thick plus 3.5 cm, a course
  of stacked slate stands on the tread below under its front edge (`stone.riser`), set back 3.5 cm
  so the nosing casts a shadow line.
- **Packing stones.** These are sparse: at each tread end there is a 40% chance of one small slate
  stone, 12-22 cm long, set in the turf.

### The terrain

The terrain is in `terrain.py`. `steps_cut`, `steps_fill` and `stair_bed` are gone. They are
replaced by:

- `bank_level(s)`: the turf's height along the path. Beside the treads it runs as a steady slope
  from each tread's back, level with its top, down to its front, level with the next tread. So the
  treads are set into the bank: their ends show more of their thickness toward the front, as in
  refs/05.
- `path_bank(x, y, z)`: the open grassy bank. For 0.72 m either side of the path's centre (about the
  longest slab's end) the turf is at `bank_level`. Beyond that it climbs to the terrace, or falls to
  the lawn, at `layout.BANK` = 0.85 (40 degrees), with 12 cm rounded shoulders. It eases back to the
  terrace behind the top tread and to the lawn before the gate.
- `ground()` changed by one line, to call `path_bank`.

`path_frame` now gives a negative chainage before the top tread rather than nan, so the bank can
fade out smoothly at the landing.

### The wall

This is `stone.walls()` and `stone.dry_wall()`.

- **Flatter, layered stones.** Courses are lower: a 16-22 cm bottom course and 10-19 cm courses
  above. Stones are longer: 0.22-0.62 m. Two-thirds of the stones show bedding layers, and their
  beds stay flat.
- **The top follows the bank.** The wall's top is the turf behind it. Where the bank dips to the
  path, the wall steps down with it: top-course stones are trimmed to the turf, the stones nearest
  the gap disappear into the bank in front, and the capstones step down short and level, as copes
  on a sloping wall do. The gap is simply where the bank reaches the treads, `stone.wall_gap()`.
- **Kept from revision 1.** Courses are scaled to fill the height exactly, so the known gap where
  courses stopped 6 cm short of the capstones stays fixed. Joints are 1.4-3.6 cm. The core sits
  12 cm back, so joints read as deep shadow. About 28% of stones are short, each with a flat pinning
  stone over it, and wedges are driven into the wide joints.
- **Core blocks.** The core is now a run of 0.25 m blocks that follow the top. Alternate blocks are
  set back 4 mm so overlapping faces never share a plane; shared planes rendered as black lines in
  Cycles.

### Elsewhere

These are unchanged from revision 1:

- The chimney's cap is a split slate slab (`garden.chimneys`, 3 lines). The brickwork is
  untouched.
- The door sill is a split slate slab (`doorfront.py`, 3 lines), with its own random seed.

### What moved

- Bed 0 is at (-0.75, -2.3). It was originally at (-0.6, -2.3), so it moved 15 cm left.
- Bed 1 is at (2.25, -2.5). It was originally at (2.0, -2.5), so it moved 25 cm right.
- At their original spots both beds reached onto the slabs' ends; they now clear the longest slab
  end by at least 5 cm. Revision 1 had moved them much further.
- The bench, gate, letterbox, lamp and birdhouse have not moved.

## Relief sizes (real; HO 1:87, where 1 cm is 0.115 mm)

| feature | real | at HO |
|---|---|---|
| corners and edges split off: rubble / slate | 1-5 / 2-6 cm deep | 0.12-0.7 mm |
| a wall stone's face split into facets | 1.5-5 cm deep | 0.17-0.57 mm |
| measured relief across a wall stone's face (6 seeds) | 1.6-5.2 cm | 0.18-0.6 mm |
| wall bedding layers | 3-5.5 cm thick, set back up to 1.4 cm | 0.35-0.63 mm layers, up to 0.16 mm steps |
| chips out of arrises | 6-11 cm across, 1-2 cm deep | 0.7-1.3 mm across, 0.11-0.23 mm deep |
| slate laminae | 1.8-2.8 cm thick, edges set back up to 2.4 cm | 0.21-0.32 mm layers, up to 0.28 mm steps |
| measured lamina steps on a tread's edge (test, 6 seeds) | 1.1-5.2 cm | 0.13-0.6 mm |
| spalls (top lamina flaked off) | 1.3-2.4 cm deep | 0.15-0.28 mm |
| measured relief across a tread's top (test) | 1-3.3 cm | 0.12-0.38 mm |
| pits: rubble / slate | 5-7 / 3-4.5 cm across, 0.6-1.2 cm deep | 0.6-0.8 / 0.35-0.5 mm across, 0.07-0.14 mm deep |
| wall joints | 1.4-3.6 cm wide, 12+ cm deep | 0.16-0.41 mm wide, 1.4+ mm deep |
| a tread's edge (its riser) | 7-13 cm | 0.8-1.5 mm |
| nosing over the tread below | 1.5-3 cm | 0.17-0.35 mm |
| arris rounding | about 0.7 cm | about 0.08 mm |
| lattice spacing: slate / rubble | 2 / 2.2 cm | 0.23 / 0.25 mm |

The wall's bedding steps and the pits are at or under the brief's 1.5 cm depth floor. They are
bonus detail and may soften in resin. Everything else is at or above the floor.

## Size and time

Vertices, from `proto_out/count.py`, before → after:

| part | before | after | added |
|---|---|---|---|
| walls | 36,297 | 141,512 | +105,215 |
| steps (13, with risers and packing stones) | 460 | 53,260 | +52,800 |
| landing | 0 | 10,026 | +10,026 |
| door sill | 296 | 8,832 | +8,536 |
| chimney cap | 152 | 4,258 | +4,106 |
| **whole scene** | **147,418** | **328,101** | **+180,683** |

Revision 1 was 343,329 in all; the cheek walls are gone and the treads are simpler. The increase
is about +360k triangles, roughly +18 MB of binary STL.

The full build, `time tools/build_bag_end.sh --no-render`, takes 3.3 s, the same as before. The
brief's ~1.5 min must include the renders.

## Tests

`tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py` gives **91/91 passed**: 78 at
the start, 1 removed, 14 added. Full output is in `proto_out/test_output.txt`.

### Changed or removed

- `test_parts.test_flagstone_is_a_closed_slab_with_its_top_at_the_tread`: **removed**, together
  with `parts.flagstone`, which nothing uses now. Its properties (a closed slab whose top is the
  tread height) are tested on the new slab in `test_stone`.
- `test_garden.test_garden_is_built_in_detail`: the line `len(step_0.vertices) > 8`, "an irregular
  slate, not a box", tested the old one-slab step. It now checks that every step and the landing
  exist; density has its own test.
- `test_garden.test_every_step_slab_top_is_its_tread_height`: the assertion is unchanged. A comment
  notes that it now also means riser and packing stones stay below the tread.
- `test_build.test_build_twice_gives_one_of_each`: the expected names now include `landing`,
  `chimney_cap_0`, `wall_west` and `wall_east`.
- `test_terrain.test_terrace_path_stays_level_along_the_row`: this skipped points within 1.2 m of
  the old step points, where the steps were cut lower. It now skips points within 2.05 m of the
  steps' centreline: the open bank's reach is 0.72 m of turf level with the tread ends, plus at most
  0.9 m of drop at 40 degrees, plus the shoulders. Everywhere else the terrace must still be level.

### Added in the new `tests/test_stone.py`

- `test_every_kind_of_stone_is_a_closed_outward_solid`: rubble, wall-face, slate, riser and flag
  stones, 3 seeds each, plus a heap of overlapping stones in one object.
- `test_stones_never_fold_through_themselves`: a BVH self-overlap check per shell, ignoring
  triangles that only touch at a shared vertex. There are 0 crossings over 21 stones.
- `test_wall_stone_faces_carry_print_scale_relief_and_stay_in_their_box`: the show face varies by
  at least 1.5 cm, and nothing bulges more than 4 cm past the nominal box.
- `test_slate_top_is_its_height_flat_but_flaked_and_its_edges_layered`.
- `test_stones_are_repeatable`.
- `test_a_hidden_back_stays_coarse`.

### Added in `test_garden.py`

- `test_wall_courses_reach_the_capstones`. Where the wall stands full height, level rays just under
  the capstones hit a stone face. They must hit within 5 cm of the face line; the core is 12 cm
  back. At least 75% must hit, and the misses are the joints.
- `test_the_wall_follows_the_bank_down_to_the_path` (new in revision 2). Beside the gap, the wall's
  top is never more than 10 cm above the turf behind it, and never more than 30 cm below it.
- `test_every_step_stands_on_a_riser`. Rays into the space under each tread's nose hit that step:
  its stacked riser course, or the slab's own thick edge.
- `test_each_tread_is_stacked_on_the_one_below` (new in revision 2). Each tread's back runs at least
  3 cm under the front of the tread above.
- `test_the_path_runs_clear_from_the_door_to_the_gate`. Looking down on each tread you see the tread
  at its height, and at least 75% of the landing is flagged.
- `test_the_path_is_dense` (rewritten in revision 2). There are 10 or more treads, every going is
  0.36 m or less, and from the top tread to the last one's front there is stone across the path at
  every 4 cm. No band of grass lies between treads; a side-by-side joint may let one of three rays
  through.
- `test_beds_and_furniture_keep_clear_of_the_path`. Beds, bench, birdhouse and lamp all stand
  beyond the longest slab's end.
- `test_every_stone_is_its_own_outward_shell`. Every island of the steps, landing, walls and cap
  encloses positive volume. In revision 1 this caught an inside-out riser stone.

### Added in `test_terrain.py`

- `test_the_bank_meets_the_tread_ends_with_no_trench` (replaces revision 1's staircase-cutting
  test). At both ends of every tread the turf is between the tread's top and the next tread's top.
  From there out to the wall, the cross-section climbs to the terrace, or falls to the lawn, steadily
  and never steeper than 50 degrees. There is no ditch beside the steps.

### Unchanged and still meaningful

- `test_terrain.test_no_step_is_buried`
- `test_layout.test_steps_descend_from_door_to_gate`
- `test_garden.test_dry_stone_wall_stops_short_of_the_thin_edges`
- `test_garden.test_garden_parts_are_closed_solids_standing_on_the_ground`

## Merge notes

The new module is `bagend/stone.py`. The edits elsewhere are small.

- `garden.py`
  - `steps()` and `wall()` are one call each, to `stone.path()` and `stone.walls()`.
  - `_course` is gone.
  - The chimney cap is 3 lines.
  - `import stone`, and one docstring line.
- `doorfront.py`: the sill (3 lines), plus imports of `random` and `stone`.
- `parts.py`
  - `rough_stone` and `flagstone` are **removed**; nothing else used them. If the wood or oak
    prototype uses `rough_stone`, keep it, or switch that use to `stone.block`.
  - The `"stone"` material's mottle is grey-brown instead of green, so the previews don't look
    painted with moss. It is a one-line preview change, away from the `timber` line.
- `layout.py`
  - `STEPS` has 13 new values.
  - New: `LANDING`, `STEP_LENGTH`, `TREAD`, `RISER_DEPTH`, `BANK`.
  - `BEDS` 0 and 1 are nudged.
- `terrain.py`
  - New: `path_line`, `path_frame`, `tread_chainage`, `TREAD_ENDS`, `bank_level`, `path_bank`.
  - `steps_cut` is removed.
  - `ground()` changed by one line.

## What isn't right yet, and next steps

- **The bank is wide.** It cuts a hollow into the terrace up to 2 m either side of the path at the
  wall. With it, the wall is under 0.4 m tall for about 2.3 m around the gap, the path itself taking
  1.5 m of that. That follows from the M4 layout: a level terrace 0.9 m above the lawn and a path
  through the wall. Possible fixes:
  - A steeper `BANK`, at 50 degrees or more.
  - Letting more of the descent happen out on the lawn below the wall.
- **Lattice aliasing in close-ups.** At 2-2.2 cm spacing some scoop rims and facet edges show small
  stair-steps in the closest renders. At HO that's 0.23-0.25 mm, at the edge of what resin
  resolves. Possible fixes:
  - Refine the lattice only near arrises.
  - Accept about +60% vertices at 1.6 cm spacing.
- **Wall stones read a little pillowy** at their ends, from the arris rounding. With less rounding
  the aliasing above comes back.
- **The landing** is a jittered 3-column grid of flags. True crazy paving (a Voronoi partition)
  would read better.
- **The door sill** is slate, so a 26 cm sill shows many thin laminae. A rubble sill might suit
  it better.
- **Pits** are shallow for print. If Ryan wants visible pitting, raise them to 1.5 cm deep and
  5+ cm across.

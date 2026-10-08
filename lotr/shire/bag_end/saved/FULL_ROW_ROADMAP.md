# Bag End, full row: saved, with the roadmap for finishing it

On 2026-10-08 Ryan chose a more contained Bag End as the piece to finish first: the green-door
front, its windows, a contained hill and the oak on top, as in refs/03. The full row of five fronts
is saved here so it can be finished later.

## Where it is

- **Code at the end of milestone 3:** git tag `bag-end-full-row-m3`, which is the branch
  `feat/bag-end-m3` and PR #1. Everything there is reviewed and tested (67/67).
- **Saved files** (in `saved/full_row_m3/`):
  - `bag_end_full_row_m3.blend`: the built scene. Rebuild it any time from the tag with
    `tools/build_bag_end.sh`.
  - `overview_m3.png` and `fronts_vs_photos_m3.png`: what it looked like.
- **Milestone 4 prototype:** `saved/full_row_m4_prototype/bagend/` is a full copy of the package
  with the garden work started (see below). It is unreviewed and its tests are not updated.

## Size and scope

Five fronts at true HO size, from left to right:
1. round_window_west
2. round_window_rack
3. ornate
4. door
5. lattice_window

The hill is compressed to 28.0 × 16.6 m, which is about 32 × 19 × 10 cm at 1:87, in two printed
hill sections.

## What is left

### Milestone 4: garden and look

These are prototyped in `saved/full_row_m4_prototype` and need review and tests:
- [x] Organic turf lumps on the hill (`terrain.lumps`, only where the hill rises).
- [x] Turf colour and plaster colour toned down to match the photos.
- [x] The door lantern hangs clear of the door.
- [x] Slate flagstone steps (`parts.flagstone`). Update `test_garden`'s step test, since slab tops
  now vary by up to 6 mm.
- [x] The dry-stone wall, laid stone by stone over a solid core, with capstones.
- [x] Soil beds (`layout.BEDS`).
- [x] Brick chimneys course by course, with stone caps and clay pots.
- [x] Props (`props.py`): bench, gate with ball finials and sign, log letterbox, lamp posts with
  lanterns, birdhouse, rack.
- [x] The organic preview oak (`oak.py`): a gnarled trunk, six spreading limbs and leaf clumps.
- [x] The door front's side-facet turf follows the facets; no wedge behind the inner posts.
- [x] Leftovers from M3: studs up into the header band, the lattice centre square at 0.45 r,
  corbels flush with the beads.
- [ ] Tests for all of the above, then review.
- [ ] Look at every comparison sheet against its photo.

### Milestone 5: print prep (deferred items are in the M2 and M3 ledgers)

- Split the hill into two sections with pins. Make pockets with clearance for each front and
  chimney, and a socket for the oak.
- Hollow the hill (2.5 mm shell, open underneath).
- Through-cut windows and lighting, or keep the 9 cm recesses.
- Check minimum feature sizes. Lead cames are 0.14 mm and lantern posts 0.23 mm at HO; both are
  too fine for the 0.2 nozzle.
- Fix the hill poking above the sod at the ornate front's arch shoulders (up to 0.17 m) and at the
  door's inner posts (3 cm).
- Triangulate the long, non-planar wobbled caps before STL export, and flip winding on mirrored
  parts.
- Export at 1:87, slice with `tools/estimate.sh`, and test-print a front and a hill section.

## How to pick it back up

1. `git switch -c feat/bag-end-full-row bag-end-full-row-m3`
2. Copy the prototype package over the real one:
   `cp -R lotr/shire/bag_end/saved/full_row_m4_prototype/bagend/* lotr/shire/bag_end/blender/bagend/`
3. Run the tests and build. Write the milestone 4 plan from the checklist above, as milestones 2
   and 3 were done.

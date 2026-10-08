# Bag End

Bilbo's hobbit hole under The Hill, modelled on the Hobbiton Movie Set in Matamata, New
Zealand: the green door with a window either side under its own small hill, and the oak on top.
It is built by Python scripts in headless Blender, from measurements taken off the reference
photos in [refs/](refs/).

## Status

**Milestone 1, rough layout (full row): done.** The hill, five fronts as plain blocks, four
chimneys, the garden (flagstone steps, dry-stone wall, gate, bench and other props) and a
preview oak.

**Milestone 2, door front in detail: done.**

- The door front is built in full, rustic detail: the green planked door with its nails and
  brass knob in a grey timber ring, a hand-laid brick arch, leaded portholes on side facets
  that turn back into the hill, timber posts with knee braces, a planked eave and the lantern.
- The layout follows the milestone 1 review. Every front is true HO size, with the banks
  between them and the back of the hill shortened. The hill climbs steeply to its top as in
  refs/09, and its sides and back fall to a thin edge.

**Milestone 3, the full row's other four fronts: done.** The ornate front has its carved
arched bargeboard, half-timbering and a tall arched leaded window, with a small wheel window
on its left wing. The lattice-window front has its square-lattice round window in a heavy
timber ring, and the two small fronts each have a wheel window under an arched eave. They are
built from a shared front kit, which the door front now uses too. The turf runs down over
every eave. Windows are 9 cm recesses behind their glass until milestone 5 decides on
lighting.

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

**Next:** print prep (M5): choose HO or O, split if needed, pockets, pins, hollowing, export,
and a test print.

There is no STL export yet. The model is in real-world metres and the scale is applied at
export. The door is D = 1.57 m across, which is a choice (see the spec). The model is
14.8 × 10.6 m, which comes to about 17 × 12 × 7 cm at HO (1:87), one print; the heights are the
hill without the chimney pot and oak (with the pot it is about 7.3 cm at HO). Ryan's train is O
scale (1:48), where it would be about 31 × 22 × 12 cm: two prints, or a trimmed edge.

## Build and test

Run these from the project root. They need Blender 5.0 or newer at
`/Applications/Blender.app/Contents/MacOS/Blender`; set `BLENDER=/path/to/Blender` to use
another copy. The comparison sheets also need Python 3 with Pillow.

```
tools/build_bag_end.sh               # .blend, renders and comparison sheets
tools/build_bag_end.sh --no-render   # .blend only: no renders, no comparison sheets
tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py              # all tests
tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py test_layout  # one module
```

The tests run inside Blender and print one `PASS` or `FAIL` line each.

## Where things land

- `bag_end.blend`: the generated scene. Its active camera is the overview.
- `renders/render_<camera>.png`: one render per camera (`overview`, `ref01`, `ref02`, `ref03`,
  `ref04` and `ref05`).
- `renders/compare_<camera>.png`: the reference photo on the left and the matching render on
  the right, for `ref01`, `ref02`, `ref03`, `ref04` and `ref05`. The fronts are true size, so
  the door views (01, 02) line up with their photos; 03, 04 and 05 show the compact hill from
  near where those photos were taken.

## Code

Under `blender/bagend/`:

- `layout.py` holds every position and size: fronts (including the door front's facets), garden,
  hill, model extents, oak and the full row's spare fronts.
- `terrain.py` and `hill.py` make the landform.
- `parts.py` is the library of rustic building parts, and the render materials with their colours.
- `doorfront.py` builds the detailed door front from those parts.
- `frontkit.py` holds what every front shares: placement, wall, eave, round windows.
- `fronts.py` builds the other fronts, through a builder for every front, spare ones included.
- `garden.py` has the steps, wall, beds and chimney.
- `props.py` has the bench, gate, letterbox, lamp post, birdhouse and rack.
- `oak.py` builds the oak, a separate print in its own `oak` collection that plugs into the hill
  with a keyed peg; `treekit.py` has its helpers (seeded noise, tubes, mesh assembly).
- `render.py` has the light, the cameras and the renders; `tools/side_by_side.py` makes the
  comparison sheets.
- `scene.py` has the shared helpers.

`blender/build.py` runs them all, and `blender/tests/` has the tests.

## Documents

- [Design spec](../../../docs/superpowers/specs/2026-10-07-bag-end-blender-design.md)
- [Milestone 1 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m1-blockout.md)
- [Milestone 2 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m2-door-front.md)
- [Milestone 3 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m3-fronts.md)
- [Milestone 4 plan](../../../docs/superpowers/plans/2026-10-08-bag-end-m4-compact.md)
- [Reference photo credits](refs/ATTRIBUTION.md)

## Archive

`old_openscad/` holds the last OpenSCAD attempt, with its own README, STLs and renders.
Nothing in the Blender build uses it. It was moved as it was, so its `.scad` include path
and its README's `refs/` links no longer resolve.

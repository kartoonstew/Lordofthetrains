# Bag End

Bilbo's hobbit hole under The Hill, modelled on the Hobbiton Movie Set in Matamata, New
Zealand. It is built by Python scripts in headless Blender, from measurements taken off the
reference photos in [refs/](refs/).

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

**Milestone 3, the other four fronts: done.** The ornate front has its carved arched bargeboard,
half-timbering and a tall arched leaded window, with a small wheel window on its left wing. The
lattice-window front has its square-lattice round window in a heavy timber ring, and the two
small fronts each have a wheel window under an arched eave. They are built from a shared front
kit, which the door front now uses too. The turf runs down over every eave. Windows are 9 cm
recesses behind their glass until milestone 5 decides on lighting.

**Next:** garden detail (M4), then print prep (M5: split, pockets, pins, hollowing,
HO 1:87 export). The oak's position still waits on an aerial photo.

There is no STL export yet. The model is in real-world metres and the scale is applied at
export. The door is D = 1.57 m across, which is a choice (see the spec). The model is
28.0 × 16.6 m, which comes to about 32 × 19 cm at 1:87 and about 10 cm tall.

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
  `ref05`, `ref08`, `ref09`, `ref10`).
- `renders/compare_<camera>.png`: the reference photo on the left and the matching render on
  the right, for `ref01`, `ref02`, `ref03`, `ref05`, `ref08`, `ref09` and `ref10`. The fronts
  are true size, so the door views (01, 02, 03) line up with their photos, and 05 and 08 show
  their fronts from near where those photos were taken. The hill is compressed, so the wide
  views (09, 10) only frame the same scene.

## Code

Under `blender/bagend/`:

- `layout.py` holds every position and size: fronts (including the door front's facets), garden,
  hill, model extents and oak.
- `terrain.py` and `hill.py` make the landform.
- `parts.py` is the library of rustic building parts.
- `doorfront.py` builds the detailed door front from those parts.
- `frontkit.py` holds what every front shares: placement, wall, eave, round windows.
- `fronts.py` builds the ornate, lattice-window and two round-window fronts.
- `garden.py` has the garden and chimneys.
- `render.py` has the materials, light and camera positions.
- `scene.py` has the shared helpers.

`blender/build.py` runs them all, and `blender/tests/` has the tests.

## Documents

- [Design spec](../../../docs/superpowers/specs/2026-10-07-bag-end-blender-design.md)
- [Milestone 1 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m1-blockout.md)
- [Milestone 2 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m2-door-front.md)
- [Milestone 3 plan](../../../docs/superpowers/plans/2026-10-07-bag-end-m3-fronts.md)
- [Reference photo credits](refs/ATTRIBUTION.md)

## Archive

`old_openscad/` holds the last OpenSCAD attempt, with its own README, STLs and renders.
Nothing in the Blender build uses it. It was moved as it was, so its `.scad` include path
and its README's `refs/` links no longer resolve.

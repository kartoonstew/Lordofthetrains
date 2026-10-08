# Bag End realism pass: prototype brief (shared by the three prototype jobs)

## The project

Bag End (Bilbo's hobbit hole on the Hobbiton Movie Set) is modelled by Python scripts in
headless Blender 5.0.1 for 3D printing. The owner, Ryan, paints and flocks the print himself.
The current build is the compact Bag End: three fronts (small round window at the left, the green
door, the lattice window) under one dome hill, a garden with steps, a dry-stone wall, beds, a brick
chimney, props (bench, gate, letterbox, lamp post, birdhouse) and an oak on top.

Ryan's verdict on it: **"it looks like a playskool toy right now."** His notes:
- "The stone walkway doesn't look good ... I think the stone path needs more density and
  realistic textures."
- "The wood features have no grain or texture, same with the stones."
- "The tree looks as if it were playskool also." The oak will be **a separate print added
  later**, and should get more texture and realism.
- "Brickwork seems fine." Leave brickwork alone.
- "Lighting is not important since this will be a 3D print." Only **geometry** matters: the colour
  materials are just for previews.

So the realism must live in the mesh: relief that survives printing, painting and flocking.

## Scale and print facts (design to these)

- The model is in real-world metres. The door is D = 1.57 m across. Origin at the door sill
  centre, +x along the front, +y into the hill, +z up.
- Printed at HO 1:87 (1 mm = 8.7 cm real) or O 1:48 (1 mm = 4.8 cm real), on resin or a 0.2 mm
  FDM nozzle. **Texture must be exaggerated to print**: a groove under about 1.5 cm real
  (0.17 mm at HO) is lost; aim for relief of roughly 1.5–3 cm real depth/width (0.17–0.35 mm at
  HO) for the main texture, with finer detail only as a bonus. Main features at least 0.3 mm at HO
  (2.6 cm real). Noise finer than ~1 cm real is wasted vertices.
- Every printed object is a closed solid: every edge manifold and positive signed volume (the
  tests' `is_closed`). Overlapping closed shells inside one object are acceptable (existing
  practice), self-intersecting single shells are not.
- Everything is repeatable: only seeded `random.Random`, `np.random.default_rng(seed)` and
  `mathutils.noise`.
- `layout.py` is the single source for positions and sizes.
- Keep the full build reasonable: it is ~1.5 min now (`tools/build_bag_end.sh`); stay under ~3 min
  total, and say how many vertices your area adds.

## How to work

- Work only in **your own scratch copy** (path in your dispatch). It is a plain copy of the repo
  (not a git checkout): `lotr/shire/bag_end/blender/` is the package (`bagend/`) and its tests
  (`tests/`), `tools/` has the scripts, `lotr/shire/bag_end/refs/` has the reference photos.
- Run everything from your copy's root:
  - tests: `tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py [test_module ...]`
    (prints PASS/FAIL per test and `N/M passed`; 78/78 pass at the start)
  - build the scene without renders: `tools/build_bag_end.sh --no-render` → `lotr/shire/bag_end/bag_end.blend`
  - Blender binary: `/Applications/Blender.app/Contents/MacOS/Blender` (use `--background
    --factory-startup`). Runs take minutes: use long timeouts (600000 ms).
- Read the reference photos in `lotr/shire/bag_end/refs/` that matter for your area (they are
  JPGs you can open with your Read tool).
- Judge your work with **close-up renders**: write your own render script that opens the built
  `.blend` (or builds just your parts), adds a camera and renders with Cycles. Render each view
  twice:
  1. **clay**: override every material with one plain light-grey diffuse material and light it
     with a low, raking sun (15–25° elevation). That shows the relief as the unpainted print will.
  2. **colour**: the scene's own materials.
  Use 1200–1600 px wide, 32–64 samples, denoise on. A small helper that composes several PNGs
  into one labelled sheet with Pillow (system `python3` has Pillow) is handy. Look at your renders
  and iterate until it no longer reads as a toy next to the photos.
- Make before/after sheets: the same views of the current build (before) and yours (after).
- Keep the tests passing. If a test encodes the old design (e.g. old step heights or the old
  preview oak), change it to test the new design's real properties, and list every test change
  and why. Add tests for new properties that matter (closed solids, relief depth bounds, sizes).
- Do not run git. Do not dispatch subagents. Do not edit anything outside your scratch copy.

## Deliverables (in your scratch copy)

1. The code changes.
2. `NOTES.md` at the copy root:
   - what you changed (files, functions, new modules) and the design idea
   - the relief sizes you chose, in cm real and mm at HO
   - vertex counts added, and the full build time (`time tools/build_bag_end.sh --no-render`)
   - test results (`N/M passed`, real output) and every test you changed or added, with why
   - anything you could not get right, and ideas for next steps
3. `proto_out/` with the render scripts you used and the before/after sheets (PNG). Name the main
   sheets `sheet_clay.png` and `sheet_colour.png`.

Reply at the end with only: status, the sheet paths, test summary, build time, and a 3-line
summary of the approach. The detail lives in NOTES.md.

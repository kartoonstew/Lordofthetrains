# Oak prototype: the oak as a separate, realistic print

Sheets: `proto_out/sheet_clay.png` (front, three-quarter from above, the tree alone, bark and
root-flare close-up) and `proto_out/sheet_colour.png` (front, above, tree), before on the left
and after on the right.

## What changed

The preview oak (a curve trunk with six limbs under a flat umbrella of icosphere blobs, 9.9 x
10.4 m wide and 1.7 m thick) is replaced by an old, gnarled oak built as a printable piece. It
has a thick trunk with buttresses and surface roots, low spreading limbs that each fork,
branches grown into the crown, and a full domed crown of knobbly leaf clumps with a few gaps
where limbs show. A keyed peg goes under the trunk. Following Ryan's note, the bark is bare
relief: no moss or ivy.

Files:

- `blender/bagend/oak.py`: rewritten.
  - `skeleton(seed)` grows the structure:
    - `_trunk`: a leaning bole that bends on up into the leader.
    - `_limbs`: 6 limbs. Five leave the trunk low (0.6–0.9 of `OAK_FORK`), sag, then rise at
      their ends; one climbs. Each forks once, so there are 12 limbs in all.
    - `_clumps`: leaf-clump centres spread over a dome by Poisson disc. There is an outer layer,
      a clump on top, and a sparser inner layer so a gap shows foliage behind it; about 7% are
      dropped to leave gaps.
    - `_colonize`: space colonization grows branches from the outer limbs toward a cloud of
      points in each clump.
    - `_branches`: turns the grown nodes into branch chains. Thickness follows the pipe model,
      and the limbs thicken to carry their branches. No branch is thinner than `OAK_TWIG`.
  - `build(seed)` makes the meshes and returns
    `Oak(trunk, crown, branches, tips, tangled)`; the old version returned the crown object.
    - Wood, `_tube`: each trunk, limb and branch is a tube of star-shaped rings around its path.
      Bark, gnarl and a collar swelling where it leaves its parent are added; `untangle` smooths
      the path until no ring crosses the next.
    - `_trunk_mesh`: buttress fins toward the roots, swellings up into each limb and burls. The
      lowest 0.45 m drapes onto the turf, and the bark follows the drape.
    - `_root`: half-round ridges whose undersides lie on the turf. Each root stops where the
      ground falls more than 1 m or gets steeper than 48°, and ends in a point.
    - `_peg`: the keyed peg.
    - `_foliage`: each clump is a core plus many lumpy leaf-cluster blobs, with more blobs along
      the twigs that carry it. All of them are voxel-remeshed into one surface, then single-voxel
      specks and sealed bubbles are dropped (`treekit.drop_specks`).
- `blender/bagend/treekit.py` (new): helpers in numpy.
  - Seeded lattice noise (`Noise`: Worley F1/F2, gradient "perlin", value noise and fbm), all from
    `np.random.default_rng(seed)` tables, so it is repeatable.
  - Path tools: `frames` (parallel transport), `untangle`.
  - Tube topology: `tube_faces`, with quads between rings of equal size and a triangle zipper
    between rings of different size; `ring_sizes`, `ring_angles`.
  - `MeshData`: fast mesh assembly with `foreach_set`. It also writes a per-vertex `shell`
    attribute that numbers the closed shells.
  - `islands`: a vectorised union-find over the edges, 0.08 s for 216k vertices.
- Wiring:
  - `layout.py`: `OAK_CROWN`, `OAK_HEIGHT`, `OAK_GIRTH`, `OAK_FORK`, `OAK_TWIG`, `OAK_PEG`,
    `OAK_SEAT`, `OAK_LEAF_VOXEL`; `OAK` itself is unchanged.
  - `garden.py`: one docstring line only. `garden.build()` still calls `oak.build()`.
  - `lotr/shire/bag_end/README.md`: the code list.
  - Collection: `oak`, replacing `preview`. The object names are still `oak_trunk` (all the wood
    plus the peg) and `oak_crown` (the foliage), so `render.py` and `test_build` keep working.

Design idea: the skeleton decides the realism (low, heavy, forking limbs and a pipe-model
taper), and the surface carries the print detail. Wood is anisotropic tubes, so bark furrows
along the wood get fine spacing around and coarse spacing along, which is cheap. Foliage is a
voxel iso-surface, which by construction is closed, never crosses itself and has no hidden
faces inside.

**Solids: say which.**
- The wood is **overlapping closed shells**, not a boolean union: 226 shells (the trunk with its
  leader, 7 roots, 12 limbs, 205 branches, the peg). Each child starts on its parent's axis, so
  it is buried in the parent. Every shell is closed, has positive volume and does not cross
  itself; a test checks every shell with a BVH self-overlap.
- The crown is **one voxel-remeshed surface per clump group**: 6 islands, each holding branch
  tips inside it.
- Wood and crown overlap where the twigs run into the clumps, so the canopy is carried. Printed
  together, they are overlapping closed shells (slicers union them).

## Sizes (real m; HO 1:87; O 1:48)

| | real | HO | O |
|---|---|---|---|
| whole piece (wood + crown + peg) | 8.69 x 8.59 x 7.21 m | **100 x 99 x 83 mm** | **181 x 179 x 150 mm** |
| crown spread (`OAK_CROWN` = 5.6 D) | 8.7 m | 100 mm | 181 mm |
| crown top above the turf (`OAK_HEIGHT` = 3.9 D) | 6.2 m | 71 mm | 129 mm |
| crown depth (top to lowest foliage, 1.5 m above the turf) | 4.7 m (old crown: 1.7 m) | 54 mm | 97 mm |
| trunk diameter above the flare (`OAK_GIRTH`) | 1.13 m | 13 mm | 24 mm |
| limbs leave the trunk (`OAK_FORK` = 0.95 D) | 0.9–1.5 m up | | |
| thickest limb (radius) | 0.27 m | 3.1 mm | 5.6 mm |
| thinnest branch (`OAK_TWIG`, diameter) | 7 cm | 0.80 mm | 1.46 mm |
| peg (`OAK_PEG`): round with one flat on the +y side, 5 cm chamfer | 0.5 m dia, 0.6 m below the seat | 5.7 x 6.9 mm | 10.4 x 12.5 mm |

It fits a 256 mm bed at HO and at O; this is a test. The 7.21 m height runs from the lowest
root tip, 1.0 m down the hill's slope, to the crown top. The crown clears the turf by at least
2.2 m and the chimney pot by 1.0 m, and no other part's bounding box touches the oak
(`proto_out/checks/clearance.py`).

## Relief sizes

Bark (`oak._bark_scale` and `_bark`) is a network of furrows along the wood: the zero lines of
stretched gradient noise, splitting and joining, broken into plates by Worley cell ends, with
the ridges rounded over. Measured from `proto_out/checks/numbers.py`:

| wood (radius) | ridge spacing | plate length | furrow depth | furrows (deeper than half) | mesh around x along |
|---|---|---|---|---|---|
| trunk (0.565 m) | 9.2 cm = 1.06 mm HO | 32 cm | **2.9 cm = 0.33 mm HO** (0.60 mm O) | ~4.6 cm wide = 0.53 mm HO | 1.5 x 4.5 cm |
| limb base (0.25 m) | 5.8 cm = 0.67 mm | 20 cm | **1.9 cm = 0.22 mm** (0.41 mm O) | ~2.9 cm = 0.33 mm | 1.0 x 4.2 cm |
| limb (0.20 m) | 5.2 cm = 0.60 mm | 18 cm | **1.8 cm = 0.21 mm** | ~2.6 cm = 0.30 mm | 1.0 x 4.3 cm |
| branch (0.12 m) | 4.3 cm = 0.49 mm | 15 cm | **1.6 cm = 0.18 mm** | ~2.2 cm | 1.1 x 4.3 cm |
| branch (0.08 m) | 3.9 cm | 14 cm | 0.6 cm (bonus only) | | 1.0 x 3.9 cm |
| twigs (0.05 m or less) | none | | 0 (it would not print) | | 1.8 x 4.5 cm |

Larger relief:
- Trunk burls: ±6% of the radius (±3.4 cm). Limb gnarl: ±8%; branch gnarl: ±6%.
- Buttress fins: up to 0.75 x root size x the trunk radius out at the foot (+30 to +47 cm),
  fading over 0.5 m.
- Limb swellings: up to 0.6 x the limb's share of the trunk radius.
- Collars: +25% where a limb or branch leaves its parent.
- Roots: 0.3–0.47 m tall by the trunk, tapering to 3.5 cm (0.4 mm HO) at their tips.

Foliage:
- Knobs (leaf clusters): 17–27 cm radius = 2.0–3.1 mm HO.
- Clumps: 0.6–0.95 m radius = 7–11 mm HO.
- Surface grain: `OAK_LEAF_VOXEL` = 4.5 cm = 0.52 mm HO. Finer leaf texture is left to the
  flock.

## Vertex counts and build time

- **Oak: 421,450 vertices.**
  - Wood: 205,606 (trunk 24.5k, roots 8.2k, limbs 85.9k, branches 86.9k, peg 144).
  - Crown: 215,844.
  - The old preview oak was 5,994.
- Whole model: 564,584 vertices (was 149,128).
- `oak.build()`: 3.3–4.6 s. Profile: foliage voxel remesh ~1.7 s, tubes ~1.0 s, skeleton 0.2 s.
- Full build, `time tools/build_bag_end.sh --no-render`:
  - **5.5 s wall, 6.7 s user** (before: 6.3 s wall, 3.6 s user).
  - While the machine was heavily loaded by the parallel jobs (load average around 300) it read
    18–24 s wall with the same ~7 s of CPU. Well under the 3 min budget.

## Tests

`tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py` gives **88/88 passed**, in 130–153 s
(`proto_out/test_output.txt`). The count went from 78: 2 old oak tests were replaced by 12 new
ones. The suite builds the oak about 12 times (the oak tests, the 6 `garden.build()` tests and the 3
`build_scene()` tests), which adds roughly 50 s.

Changed:
- `test_oak.py`, both tests replaced:
  - `test_oak_is_a_preview_with_a_spreading_crown_over_its_trunk` encoded the old design: a
    curve trunk in `preview`, and a crown whose spread beat 0.6 x its height (a flat parasol).
  - `test_oak_is_repeatable` compared the first 500 crown vertices. Its replacement compares
    every vertex of both objects.
- `test_garden.py`: `test_the_oak_is_a_preview_with_a_trunk_and_a_crown` became
  `test_the_oak_is_its_own_print_standing_on_the_hill_top`. It checks the `oak` collection holds
  exactly `oak_trunk` and `oak_crown`, that there is no `preview` collection, and that at
  `layout.OAK` the wood reaches below the turf by the peg depth and above it past `OAK_FORK`.
- `test_build.py`: `test_everything_but_the_preview_oak_fits_on_the_model` became
  `test_everything_but_the_oak_fits_on_the_model`, skipping the `oak` collection instead of
  `preview`. The oak is its own print, and its crown overhangs the hill's back edge as a real
  tree's would: crown y reaches 6.6 m, `BACK_Y` is 5.4 m.

New, in `test_oak.py`:
- `test_oak_is_a_separate_print_in_its_own_collection`: both objects are in `oak`, and there is
  no `preview` collection.
- `test_oak_wood_and_foliage_are_closed_solids`: every edge is manifold and the signed volume is
  positive, for both objects.
- `test_every_wood_shell_is_a_clean_solid`: each of the 226 shells has positive volume and does
  not cross itself (BVH self-overlap), and no tube failed `untangle`.
- `test_foliage_never_crosses_itself_and_every_clump_is_held_by_a_branch`: the crown has no
  self-overlap, every crown island contains a branch tip, and at least 90% of the tips end inside
  foliage.
- `test_crown_is_a_full_dome_not_a_flat_parasol`:
  - Spread is within 0.8–1.15 x `OAK_CROWN`.
  - Crown height is at least 0.45 x its width (measured 0.54; the old crown was 0.16).
  - The top is within 0.6 m of `OAK_HEIGHT` above the turf.
  - The top falls away outward ring by ring and is at least 1 m lower at 0.8 of the half-width.
  - Dense: at least 85% of vertical rays over the inner crown disc hit foliage.
- `test_oak_has_a_trunk_with_low_spreading_limbs`: the root flare is at least 1.2 x the trunk
  radius, there are at least 8 limbs, one leaves below 1.2 x `OAK_FORK`, and one reaches out past
  0.35 x `OAK_CROWN`.
- `test_branches_are_thick_enough_to_print`: every skeleton radius is at least `OAK_TWIG`/2, and
  bark depth never exceeds 0.3 of the wood's radius.
- `test_bark_relief_is_deep_enough_to_print`:
  - Furrows are 1.5–3.1 cm deep on the trunk and limbs.
  - Ridge spacing is 4–10 cm, with plates over 2.5x longer than wide.
  - The relief reaches at least 0.9 x the depth, and furrows cover 15–60% of the bark.
  - The mesh spacing resolves it.
- `test_oak_stands_on_the_turf_and_has_a_peg_below_it`:
  - No wood except the peg goes more than 5 cm into the hill.
  - The foot and roots sit on the turf out past 0.8 x `OAK_GIRTH`.
  - The peg's bottom is at exactly turf − seat − depth, it runs up into the trunk, its diameter
    matches, it has one flat (keyed), and it is centred at `layout.OAK`.
- `test_oak_fits_a_256_mm_print_bed_at_ho_and_at_o`.
- `test_oak_vertex_count_is_reasonable`: under 450k.
- `test_oak_is_repeatable`: every vertex of both objects matches across two builds.

## Not right yet, and next steps

- **Print support:** the crown is a domed shell of clumps over open limbs, so it has big
  overhangs and needs supports (resin: supports up inside the dome). It might print better upside
  down, or with the crown as a second part pinned onto the branch ends.
- **Union for export:** the wood is 226 overlapping shells. Slicers union them, but for one clean
  STL, union at export (M6): either a wood voxel remesh at ~0.5 cm, which would cost vertices and
  soften the bark a little, or an exact boolean.
- **Seat:** the foot is a cast of this hill's top. The trunk drapes over the narrow rise the oak
  stands on, which falls 0.4 m within a metre to the front and back, and the roots run up to 1 m
  down its slopes. So the piece seats only on this hill, as intended. `OAK_SEAT` = 2 cm sinks it
  into the turf for the preview; set it to 0, or a small negative clearance, for the print. The
  socket, the peg size plus clearance, is for the next milestone.
- **Thin branches:** at HO the thinnest are 0.8 mm. That is fine in resin but marginal on a
  0.2 mm FDM nozzle. Raise `OAK_TWIG` for FDM.
- **Twigs with foliage hidden:** they are smooth (no printable bark at that size) and end in
  short cones, so they look like pipes. Inside the clumps they don't show.
- **Junctions:** trunk–limb joins are swellings plus overlapping shells, not true fillets. They
  read well at model scale; a close-up still shows the seam line.
- **Front framing:** the oak stands about 0.5 m behind the hill's ridge line, so low front views
  hide part of its foot. That is the terrain, not a gap.
- **Wispier, like refs/03:** refs/03 shows a wispier tree with long bare sinuous limbs. This
  follows the brief's full, domed, dense crown (closer to refs/09 and 10). The knobs:
  `OAK_CROWN`/`OAK_HEIGHT`, the clump layers and gap rate in `_clumps`, and the seed range on
  the limbs (`_colonize` seeds only the outer 55%).
- **Vertex budget:** the oak is about 75% of the model's vertices. To save:
  - `OAK_LEAF_VOXEL` 0.05 brings the crown to ~175k.
  - Coarser limb bark: `_grain` uses w/(4..6).
  - For an O-scale export, use a finer voxel (0.03, about 2x the crown) for smoother knobs.
- The tests now build the oak about 12 times. If that gets slow, `garden.build()` could stop
  building the oak and `build.py` call `oak.build()` directly. I left the call in place to keep
  the change small.

## proto_out

- `render_oak.py`: the views.
  - front, above, tree, bark; clay with a 20° raking sun at 65° to the view, and colour with
    the scene's materials.
  - Two debug views: base (the foot without the hill) and plan (the wood from above).
  - Usage: `tools/blender.sh proto_out/render_oak.py <blend> <out_dir> [views] [--samples N] [--width W]`.
- `sheet.py`: composes the before/after sheets (system python3 with Pillow).
- `dev_oak.py`: builds the hill and oak only, with stats; `--check` adds the closed-solid
  checks.
- `stats.py`: vertex counts per collection.
- `checks/`: verification scripts.
  - `selfx.py`: per-shell self-overlap.
  - `crowncheck.py`: crown islands held by tips.
  - `clearance.py`: chimney and hill clearance.
  - `numbers.py`: the relief, size and vertex numbers above.
  - `budget.py`: the vertex breakdown.
- `before/`, `after/`: the renders; `before.blend`, `after.blend`: the scenes they came from.
- `build_time.txt`, `vertex_counts.txt`, `test_output.txt`.

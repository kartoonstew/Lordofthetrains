# Bag End realism pass (milestone 5): saved prototype and handoff

Saved 2026-10-08, as is, so another model or session can take a look. The prototype is **merged
and tested but not yet reviewed**, and has no plan document yet. Read this file first, then the
three `notes/*_NOTES.md`.

## Where things stand

| Milestone | What | Where |
|---|---|---|
| M1–M2 | Layout block-out; door front in detail | `main` |
| M3 | The full row's other four fronts | PR #1, `feat/bag-end-m3` |
| M4 | The compact Bag End: three fronts under a dome hill, detailed garden and props | PR #2, `feat/bag-end-compact` (stacked on PR #1) |
| **M5** | **Realism pass, in geometry: this prototype** | **branch `wip/bag-end-realism-m5`** (cut from `feat/bag-end-compact` at f9e132a) |
| M6 | Print prep (was M5): choose HO or O, split, pockets, pins, hollowing, export, test print | not started; carried items are in `docs/superpowers/plans/2026-10-08-bag-end-m4-compact.md`, "Carried to milestone 5" |

The spec (`docs/superpowers/specs/2026-10-07-bag-end-blender-design.md`) still describes
milestone 5 as print prep. It needs updating to M5 = realism and M6 = print prep, and the oak
moving from "preview only" to a separate print.

## Why: Ryan's review of M4 (2026-10-08)

- "It looks like a playskool toy right now."
- "The stone walkway doesn't look good ... the stone path needs more density and realistic
  textures."
- "The wood features have no grain or texture, same with the stones." He wants grain on every
  wooden part: structural posts, light posts, rail posts, door, frames and props.
- "The tree looks as if it were playskool also." Decision: **the oak becomes a separate print**,
  added to the hill later, with real texture.
- "Brickwork seems fine." It is untouched.
- "Lighting is not important since this will be a 3D print." Only geometry matters; the colour
  materials are previews.
- No moss or greenery in the model. Ryan adds real moss and scenery himself.

## What the prototype changes

Three prototypes were built in parallel from the M4 build and merged here. Each one's design,
relief sizes, tests and open points are in its notes.

- **Wood** (`bagend/wood.py`, new; `notes/wood_NOTES.md`):
  - Every timber piece is swept from its cross-section, with grain grooves, checks, end splits,
    knots and worn corners, cut in the piece's own frame.
  - Thick faces (8 cm or more) get 1.6–2.4 cm deep grain (0.18–0.28 mm at HO). The door boards
    get about 1.1 cm (0.13 mm at HO), and thin pieces about 0.7–0.8 cm.
  - The old timber builders moved out of `parts.py`. `frontkit`, `doorfront`, `fronts` and
    `props` call `wood`.
  - The lamp post gained a timber arm. The letterbox is a log with growth rings.
- **Stone** (`bagend/stone.py`, new; `notes/stone_NOTES.md`):
  - Every stone is a block split by fracture planes, then chipped, pitted and, for slate, layered.
  - The dry-stone wall has flat, bedded stones with deep joints and pinning stones, and its
    courses now reach the capstones.
  - The path is a flagstone landing at the door, then 13 long slate treads stacked into the open
    grass bank (refs/04, 05). It winds down to the right through the wall gap to the gate, and
    `terrain.py` shapes the bank around it.
  - The chimney cap and door sill are split slate.
  - `parts.rough_stone` and `parts.flagstone` are gone. Two beds moved slightly.
- **Oak** (`bagend/oak.py` rewritten, `bagend/treekit.py` new; `notes/oak_NOTES.md`):
  - A printable oak in its own `oak` collection: a gnarled trunk with buttresses and roots, deep
    bark furrows, twelve low spreading limbs, and a domed crown of foliage clumps carried on the
    branch ends.
  - A keyed peg (`layout.OAK_PEG`) plugs into the hill; the socket is cut in M6.
  - It is about 100 × 99 × 83 mm at HO and 181 × 179 × 150 mm at O.

Numbers for the merged build:
- **Tests:** 112/112 pass. The prototypes added tests for wood, stone, path and oak.
- **Build:** `tools/build_bag_end.sh --no-render` takes about 7 s.
- **Vertices:** about 897k (oak 421k, garden 221k, door front 105k, props 54k, side fronts
  42k + 40k, terrain 14k), against 147k at M4.

## Open decision (ask Ryan)

**The oak's foliage.** In clay renders the canopy's clumps read as smooth popcorn, which is the
part that still edges toward "toy". The options put to Ryan:
1. Leafier printed clumps: a broken, leafy surface instead of smooth knobs.
2. Print only the trunk and branch armature, with bark, and Ryan adds real foliage clumps. This
   is the usual way to get the most realistic model tree, and an easier print with no big
   overhangs.
3. Keep the canopy as is.

He hadn't answered when this was saved.

## Known issues and next steps (details in the notes)

- **Stone:** at very close range some stone edges show small stair-steps from the 2–2.5 cm vertex
  spacing (about 0.25 mm at HO). The wall stays under 0.4 m for about 2.3 m around the gap,
  because the bank cuts into the terrace there.
- **Wood:** the door's grain is now fairly even, close to fluting. Letting about a third of each
  board's grooves fade more would break it up. The vertex count can drop about 40% via
  `wood.STEP_ACROSS` and `STEP_ALONG` if a slicer struggles.
- **Oak:**
  - The domed crown has big overhangs, so it needs supports.
  - The wood shells should be unioned at export.
  - `OAK_SEAT` sinks the foot 2 cm into the turf for previews; set it to 0 for printing.
- **Not touched:** the soil beds are still smooth ovals, and the hill turf is smooth (Ryan flocks
  it).

## How to look at it

From the repo root on this branch:

```
tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py   # 112 tests
tools/build_bag_end.sh                                           # .blend, renders, compare sheets
```

`bag_end_realism_m5.blend` (here) is the built scene, so you can open it in Blender without
building.

The sheets are in `sheets/`:
- **Merged build:** `merged/realism_clay.jpg` (whole model, door, path, oak) and
  `merged/realism_merged.jpg` (whole model plus refs 04 and 05).
- **Before and after, per area:** `wood/`, `stone/` and `oak/`.

"Clay" means one plain grey material under a low raking sun, which shows the relief the way the
bare print will. Two scripts reproduce the views:
- `scripts/clay_views.py`: clay renders
- `scripts/whole_views.py`: whole-model views that include the full oak

Run either with Blender:
`Blender --background --factory-startup --python <script> -- <out_dir> <path to bag_end.blend>`

`notes/PROTOTYPE_BRIEF.md` is the brief the three prototypes were built to: print scale facts,
relief targets and the closed-solid rule.

## How the work has been run

Each milestone so far went the same way:
1. Prototype in a scratch copy, and show Ryan renders.
2. Write a plan that copies the verified files from a `-sources` folder, with RED and GREEN test
   counts replayed beforehand.
3. Execute it task by task with a review after each task, then a whole-branch review.
4. Push a `feat/` branch and open a PR. Ryan merges; nothing is merged for him.

M5 would follow the same steps from this prototype once Ryan has seen it and settled the foliage
question.

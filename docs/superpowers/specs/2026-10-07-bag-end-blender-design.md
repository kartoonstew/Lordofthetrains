# Bag End in Blender: design

Date: 2026-10-07, updated 2026-10-08 for the compact scope. Replaces the two OpenSCAD attempts;
nothing from them is carried over except the reference photos and the tooling in `tools/`
(slicing estimates).

## Goal

A realistic, organic model of Bag End as it stands on the Hobbiton Movie Set: the green-door
front with a window either side under its own small hill, and the oak on top, as in refs/03.
"Realistic" means it should read like the set photos and like a Tripo-style organic mesh, not
assembled primitives. The owner adds moss and grass (flock, static grass) after printing, so
vegetation is not modelled.

### Decided with the owner

- Built in Blender by script, no AI generation service.
- Target look: the Hobbiton set photos in `lotr/shire/bag_end/refs/`, plus the owner's three
  chat images: a wide front photo, a low-angle door photo, and a digital artwork used only as
  the bar for 3D detail quality, not for layout.
- Detail suitable for both resin and the Centauri Carbon 0.2 mm nozzle.
- Scope (2026-10-08): the compact Bag End. Three fronts under one hill:
  - a small round window tucked into the hill's left end (the owner asked for it)
  - the door front
  - the lattice window at the right
  The oak stands on top, almost over the door ("placement is fine as is"). The full row of five
  fronts built in milestones 1–3 is saved for later at git tag `bag-end-full-row-m3`. The branch
  `wip/bag-end-full-row-m4` holds its built `.blend`, its renders, an unreviewed garden prototype
  and `saved/FULL_ROW_ROADMAP.md`.
- Scale: chosen at export. The owner's train is O scale (1:48), but there is no room for a full
  O layout yet. The compact piece is about 17 × 12 × 7 cm at HO (1:87), one print on the 256 mm
  bed. At O it is about 31 × 22 × 12 cm, which needs two prints or a trimmed edge (milestone 5).
- Every front stays true size. Only the hill around them is shaped to fit.
- Steps (milestone 1 review): they wind down to the right, from the door to the gate.
- Detail style (milestone 2 prototype): rustic and worn, with the irregularity in the geometry:
  uneven bricks, warped boards, rounded and chipped timber, wavy plaster.
- No grass, bushes or ivy in the model.

### Assumptions (from the photos)

- **Fronts, left to right (refs/01–05):**
  1. A small round window front set into the hill's left end, turned a little toward the path.
  2. The door front: green door, two portholes, lantern.
  3. The front with the round lattice window, set a little back and turned toward the steps.
- **Hill:** a rounded dome, flat on top where the oak stands, with a bank over the fronts and a
  slight rise under the oak (refs/03). Its turf has gentle lumps. One square brick chimney
  stands behind the lattice window (refs/03). Every side falls to a thin edge.
- **Garden:** a path along the fronts at front level, held up by a dry-stone wall (refs/07).
  Slate flagstone steps wind down through a gap in the wall to the gate with its sign and
  letterbox (refs/04, 05). It also has:
  - soil beds either side of the steps
  - a lamp post by the left window
  - the birdhouse post in front of the lattice window
  - the bench on the lawn below the wall
- **Real-world size:** the door is D = 1.57 m across (from the terracotta pots in refs/01; the
  set was built at mixed scales, so this is a choice).

## How it is built

- Blender 5.0.1 (installed), driven by Python scripts run headless. One command regenerates
  the `.blend`, every print part, and the renders. The `.blend` can be opened to inspect or
  hand-tweak.
- Modelled in real-world metres. The scale is applied only at export.
- Code in `lotr/shire/bag_end/blender/`:
  - `layout.py`: every position and size. It also keeps the full row's other fronts as spare
    fronts, which are not built into this scene.
  - `terrain.py` and `hill.py`: the landform.
  - `parts.py`: shared building pieces and the render materials.
  - `frontkit.py`: what every front shares (placement from `layout.py`, plastered wall, eave
    with timber and turf, round windows). `doorfront.py` and `fronts.py` are assembled from it
    and `parts.py`. `fronts.py` keeps a builder for every front, spare ones included.
  - `garden.py`: steps, the dry-stone wall, soil beds and chimneys.
  - `props.py`: the bench, gate, letterbox, lamp post and birdhouse.
  - `oak.py`: the preview oak.
  - `export.py` (milestone 5): scaling, splitting, pockets, pins, hollowing, STL per part.
  - `render.py`: Cycles renders from cameras matched to the reference photos, and
    photo-next-to-render sheets.
- Realism comes from geometry first:
  - bricks laid individually with slight jitter and rounded edges
  - planks with gaps and nail heads
  - stones laid one by one, and slate slabs with irregular outlines
  - timber with slight warp and grain
  - plaster with gentle unevenness
  - turf with gentle lumps
  The render materials add soft colour patches (mottle) so plaster, stone, turf and soil don't
  read as flat toy colours. That is only for the previews; the print carries the geometry alone.
- Main features are at least 0.3 mm at HO so they read on the 0.2 nozzle; finer surface
  texture sits on top for resin and softens on FDM.

## Print parts

- **Hill:** the landform with the wall, steps and beds. It is one piece at HO; at O it is split
  into two, with two alignment pins at the joint. It is a hollow shell (about 2.5 mm walls), open
  underneath, which leaves room for lights behind the windows. Its edges taper to a thin flat
  base. FDM, 0.4 nozzle is fine.
- **Fronts (3):** each printed face-up as one plate: plaster, timber, brick, door, windows,
  eave, lantern. Each drops into a pocket in the hill with 0.2 mm clearance, and the hill's turf
  sits on its eave. Windows open right through with glazing bars at the front. Resin or the
  0.2 nozzle.
- **Chimney (1):** printed upright, plugging into a socket in the hill top.
- **Props:** bench, birdhouse post, lamp post, gate with sign, letterbox, flower pots. Printed
  separately, each pinned into a small hole in the ground.
- **Oak:** a socket in the hill top for a bought tree or wire armature. The modelled oak is for
  previews only.

## Checking

- **Matched-camera renders** for refs 01, 02, 03, 04 and 05, placed next to the photo. The
  fronts are true size, so the door views (01, 02) line up with their photos. 03, 04 and 05 show
  the compact hill from near where those photos were taken.
- **Print checks on every exported part:**
  - watertight
  - nothing under 0.3 mm at HO where it matters
  - no unsupported overhangs in its print orientation
  - fits the bed, and each front fits its pocket
  - FDM time and filament from `tools/estimate.sh`

## Milestones (owner reviews each)

1. Rough layout: hill shape, the fronts as plain blocks in place and proportion, chimneys, oak
   position, steps and garden layout, against the wide shots. (Done, for the full row.)
2. Door front in full detail, against 01, 02 and the owner's low-angle photo. This sets the
   detail standard. (Done.)
3. The other fronts, built from a shared front kit that the door front moves onto too. Windows
   stay blind recesses behind their glass until milestone 5 decides on lighting. (Done, for the
   full row's four.)
4. The compact Bag End, in the look of the photos:
   - the three fronts under their own dome hill, with organic turf
   - the garden: slate steps, dry-stone wall, soil beds, props, a chimney and the preview oak
   - mottled render materials
5. Print prep at the chosen scale:
   - split if needed, pockets, pins, hollowing
   - export
   - a test print of the door front and the hill before the full run

## Open items

- HO or O: decided at milestone 5, or both exported.
- Windows that open right through (for lights behind them) need a hollow pocket in the hill;
  decide in milestone 5. Until then every window is a 9 cm recess behind its glass.
- Concave corners where the hill rises a few centimetres above a front's sod (the door front's
  inner posts) are fixed in milestone 5.
- The owner's three chat images are not on disk; they belong in `refs/` with credits if they
  are to be kept.

# Bag End in Blender: design

Date: 2026-10-07. Replaces the two OpenSCAD attempts; nothing from them is carried over
except the reference photos and the tooling in `tools/` (slicing estimates).

## Goal

A realistic, organic model of the whole Bag End hill as it stands on the Hobbiton Movie Set,
printed for an HO layout. "Realistic" means it should read like the set photos and like a
Tripo-style organic mesh, not assembled primitives. The owner adds moss and grass (flock,
static grass) after printing, so vegetation is not modelled.

### Decided with the owner

- Built in Blender by script, no AI generation service.
- Target look: the Hobbiton set photos in `lotr/shire/bag_end/refs/`, plus the owner's three
  chat images: a wide front photo, a low-angle door photo, and a digital artwork used only as
  the bar for 3D detail quality, not for layout.
- Detail suitable for both resin and the Centauri Carbon 0.2 mm nozzle.
- Scope: the whole hill. Scale is chosen at export.
- Print breakdown: hill sections plus separate fronts, chimneys and props.
- No grass, bushes or ivy in the model.
- Size (milestone 1 review): every front stays true HO size; the grass banks between fronts
  and the hill's back slope are shortened so the whole model comes to about 30 × 18 cm, in two
  hill sections. As built in milestone 2 it is about 32 × 19 cm, and about 10 cm tall.
- Steps (milestone 1 review): they wind down to the right, from the door to the gate.
- Detail style (milestone 2 prototype): rustic and worn, with the irregularity in the geometry:
  uneven bricks, warped boards, rounded and chipped timber, wavy plaster.

### Assumptions (from the photos)

- **Layout, left to right (refs/09, 10):**
  1. Small front with a round window.
  2. Small front with a round window, plus the wooden rack and a lamp post.
  3. Big ornate front: carved arched bargeboard, half-timbering, large leaded window.
  4. Ivy and grass bank.
  5. Door front: green door, two portholes, lantern.
  6. Front with the round lattice window.
- **Hill:** turf over the whole row, climbing steeply behind it to the hill top (refs/09);
  four square brick chimneys (refs/03, 09, 10); the oak on the hill top. Its position along the
  row waits on the owner's aerial photo; until then it stays almost over the door (refs/01, 03).
- **Garden:** a path along the front at front level, held up by a dry-stone wall with soil
  beds. Flagstone steps wind down from the door to the gate with its sign and letterbox. The
  bench sits on the slope left of the door; the birdhouse post is in front of the lattice
  window front.
- **Real-world size:** the door is D = 1.57 m across (from the terracotta pots in refs/01; the
  set was built at mixed scales, so this is a choice). The fronts are that true size; see Size
  above for the compressed hill around them.

## How it is built

- Blender 5.0.1 (installed), driven by Python scripts run headless. One command regenerates
  the `.blend`, every print part, and the renders. The `.blend` can be opened to inspect or
  hand-tweak.
- Modelled in real-world metres. The scale (default 1:87) is applied only at export.
- Code in `lotr/shire/bag_end/blender/`:
  - `hill.py`: the landform.
  - `parts.py`: shared building pieces: brick arch, porthole with brick sill, planked door with
    nail heads, timber post with knee brace, curved eave, lantern on bracket, stone slab,
    chimney.
  - `frontkit.py`: what every front shares (placement from `layout.py`, plastered wall, eave
    with timber and turf, round windows); `doorfront.py` and `fronts.py` (the other four) are
    assembled from it and `parts.py`.
  - `garden.py`: dry-stone walls, steps, soil beds, props.
  - `export.py`: scaling, splitting, pockets, pins, hollowing, STL per part.
  - `render.py`: Cycles renders from cameras matched to the reference photos, and
    photo-next-to-render sheets.
- Realism comes from geometry, not textures:
  - bricks laid individually with slight jitter and rounded edges
  - planks with gaps and nail heads
  - stone slabs as irregular blocks with worn edges
  - timber with slight warp and grain
  - plaster with gentle unevenness
- Main features are at least 0.3 mm at HO so they read on the 0.2 nozzle; finer surface
  texture sits on top for resin and softens on FDM.

## Print parts

- **Hill sections (2):** the landform with walls, steps and beds. Cut through grass banks
  between fronts, with two alignment pins per joint. Hollow shells (about 2.5 mm walls), open
  underneath, which leaves room for lights behind any window. Edges taper to a thin flat base.
  FDM, 0.4 nozzle is fine.
- **Fronts (5):** each printed face-up as one plate: plaster, timber, brick, door, windows,
  eave, lantern. Each drops into a pocket in the hill with 0.2 mm clearance, and the hill's turf
  sits on its eave. Windows open right through with glazing bars at the front. Resin or the
  0.2 nozzle.
- **Chimneys (4):** printed upright, each plugging into a socket in the hill top.
- **Props:** bench, birdhouse post, lamp posts, gate with sign, letterbox, flower pots. Printed
  separately, each pinned into a small hole in the ground.
- **Oak:** a socket in the hill top for a bought tree or wire armature.

## Checking

- **Matched-camera renders** for refs 01, 02, 03, 09 and 10, with plain materials (ochre
  plaster, brick, timber, stone, flat green for flocked areas), placed next to the photo. The
  fronts are true size, so close views of them (01, 02, 03) line up with their photos; the hill
  is compressed, so the wide views (09, 10) only frame the same scene.
- **Print checks on every exported part:**
  - watertight
  - nothing under 0.3 mm at HO where it matters
  - no unsupported overhangs in its print orientation
  - fits the bed, and each front fits its pocket
  - FDM time and filament from `tools/estimate.sh`

## Milestones (owner reviews each)

1. Rough layout: hill shape, five fronts as plain blocks in place and proportion, chimneys, oak
   position, steps and garden layout, against the wide shots.
2. Door front in full detail, against 01, 02 and the owner's low-angle photo. This sets the
   detail standard. It also carries the layout fixes from the milestone 1 review: the size
   compression, a higher and steeper hill, and thin side and back edges.
3. The other four fronts, built from a shared front kit that the door front moves onto too.
   Windows stay blind recesses behind their glass until milestone 5 decides on lighting.
4. Garden: steps, walls, beds, props.
5. Print prep: split, pockets, pins, hollowing, export at 1:87, and a test print of the door
   front and one hill section before the full run.

## Open items

- No straight-on photos of fronts 1–3 yet; detail there comes from refs/08–10 until better
  photos arrive.
- Windows that open right through (for lights behind them) need a hollow pocket in the hill;
  decide in milestone 5. Until then every window is a 9 cm recess behind its glass.
- The owner's three chat images are not on disk; they belong in `refs/` with credits if they
  are to be kept.

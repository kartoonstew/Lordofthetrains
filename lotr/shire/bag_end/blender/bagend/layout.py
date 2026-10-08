"""Where everything on Bag End goes, in metres, measured from the reference photos.

Frame: origin at the centre of the door sill. +x runs left to right along the row as seen
from the garden, +y goes back into the hill, +z is up. D is the door diameter; most sizes
are multiples of it, measured in refs/01, 03, 09 and 10.
"""
import math
from dataclasses import dataclass

import numpy as np

D = 1.57


@dataclass(frozen=True)
class Front:
    name: str
    x: float           # centre of the facade along the row
    y: float           # facade line: front face of the wall
    width: float
    floor: float       # z at the bottom of the facade
    eave: float        # eave top above the floor, at the centre
    eave_ends: float   # eave top above the floor, at the outer ends
    arch: float = 0.0  # half-width of the arched centre; 0 means the whole front
    yaw: float = 0.0   # degrees; positive turns the front to face right
    centre: float = 0.0       # half-width of a flat centre facet; 0 means the facade is flat
    eave_post: float = 0.0    # with a centre facet: eave top where it meets the side facets
    wing_angle: float = 0.0   # degrees the facade turns back into the hill beyond the centre facet
    dig_behind: float = 0.2   # the ground is dug out to this far behind the facade


# Each front is true HO size.
# The compact Bag End (chosen 2026-10-08): the green-door front, a small round window tucked into
# the hill's left end and the lattice window at its right, under their own hill, as in refs/03.
# The full row of five fronts is saved at git tag bag-end-full-row-m3.
FRONTS = (
    Front("round_window_left", -2.5 * D, 0.3, 1.5 * D, 0.0, 1.22 * D, 1.02 * D, yaw=6.0),
    Front("door", 0.0, 0.0, 2.08 * D, 0.0, 1.39 * D, 1.10 * D,
          centre=0.55 * D, eave_post=1.20 * D, wing_angle=25.0, dig_behind=0.6),
    Front("lattice_window", 2.53 * D, 0.4, 1.3 * D, 0.45, 1.25 * D, 1.05 * D, yaw=-5.0),
)
# The full row's other fronts, kept so their builders stay usable for more hobbit holes later;
# they are not built into this scene.
SPARE_FRONTS = (
    Front("round_window_west", -12.08 * D, 0.0, 1.6 * D, 0.0, 1.25 * D, 1.05 * D),
    Front("round_window_rack", -9.69 * D, 0.0, 1.9 * D, 0.0, 1.30 * D, 1.10 * D),
    Front("ornate", -4.9 * D, 0.0, 4.75 * D, 0.0, 2.35 * D, 1.30 * D, arch=1.25 * D),
)


def front(name):
    return next(f for f in FRONTS + SPARE_FRONTS if f.name == name)


def eave_top(f, u):
    """Eave top above the front's floor, at distance u along it from its centre (scalar or array).

    A front with a centre facet (the door front) arches over it from eave_post up to eave, then
    falls straight along its side facets to eave_ends at the outer posts. Any other front arches
    over its arched centre (or its whole width) from eave_ends up to eave.
    """
    a = np.abs(u)
    if f.centre:
        arch = f.eave_post + (f.eave - f.eave_post) * np.sqrt(np.clip(1.0 - (a / f.centre) ** 2, 0.0, None))
        run = np.clip((a - f.centre) / (f.width / 2 - f.centre), 0.0, 1.0)
        side = f.eave_post + (f.eave_ends - f.eave_post) * run
        top = np.where(a <= f.centre, arch, side)
    else:
        half = f.arch or f.width / 2
        top = f.eave_ends + (f.eave - f.eave_ends) * np.sqrt(np.clip(1.0 - (a / half) ** 2, 0.0, None))
    return top if np.ndim(top) else float(top)


def facade_v(f, u):
    """How far the facade sits behind the front's line at u: zero on the centre facet, then
    receding at wing_angle (the door front's side facets turn back into the hill)."""
    if not f.centre:
        return 0.0 * u
    return np.maximum(0.0, np.abs(u) - f.centre) * math.tan(math.radians(f.wing_angle))


def to_world(f, u, v):
    """Front-local (u along the facade, v into the hill) to world (x, y)."""
    a = math.radians(f.yaw)
    return (f.x + u * math.cos(a) - v * math.sin(a), f.y + u * math.sin(a) + v * math.cos(a))


# Every front is a wall mass this deep behind its facade, with turf this thick on its eave, and
# square timber posts this wide
WALL_DEPTH = 0.8
SOD = 0.14
POST = 0.12

# Garden
TERRACE_Z = 0.0           # the path along the fronts
WALL_Y = -3.6             # face of the dry-stone wall holding up the path
LAWN_Z = -0.9             # lawn at the foot of the wall...
LANE_Z = -1.2             # ...falling to the lane along the front edge
LANE_Y = -5.2

# Hill, refs/03: a rounded dome, flat on top where the oak stands, its front a bank over the fronts
CREST_Y = 0.6             # bank top, just behind the facades...
CREST_Z = 1.75 * D        # ...above the door sill, refs/03
DOME_TOP = 3.5            # the hill top, about 1.3 m above the door's eave, refs/03
DOME_CENTRE = (0.0, 1.2)  # (x, y)
DOME_RADII = (7.6, 4.6)   # where it meets the ground, across and back
DOME_POWER = 4.0          # higher keeps the top flatter and the ends steeper
SWELLS = ((0.6, 0.35, 1.8),)  # (x, height, width): a little rise under the oak

# The model: about 17 x 12 cm at 1:87, one print. Its sides and back fall to a thin edge.
MODEL_X = (-7.6, 7.2)
BACK_Y = 5.4
BASE_Z = -2.0             # underside of the model
EDGE_Z = BASE_Z + 0.3     # ground height at the side and back edges
EDGE_FALL = 1.0           # the ground falls to EDGE_Z over this distance from those edges

# Hill top, refs/03
CHIMNEYS = ((4.5, 2.4),)  # (x, y): the one behind the lattice window
CHIMNEY_SIZE = 0.6
CHIMNEY_HEIGHT = 1.1      # above the turf
# The oak (oak.py), refs/01, 03, 09, 10: a separate print, plugged into a socket in the hill top
OAK = (0.3, 2.5)          # trunk, almost over the door (refs/01, 03)
OAK_CROWN = 5.6 * D       # crown spread: 8.8 m (101 mm at HO, 183 mm at O)
OAK_HEIGHT = 3.9 * D      # crown top above the turf at the trunk: 6.1 m
OAK_GIRTH = 0.72 * D      # trunk diameter above the root flare: 1.13 m
OAK_FORK = 0.95 * D       # the main limbs leave the trunk about this high: 1.5 m
OAK_TWIG = 0.07           # thinnest branch, diameter: 0.8 mm at HO
OAK_PEG = (0.5, 0.6)      # peg under the trunk, diameter and depth below the turf: 5.7 x 6.9 mm at HO
OAK_SEAT = 0.02           # the trunk base and roots sit this far into the turf
OAK_LEAF_VOXEL = 0.045    # the foliage surface's grain (the remesh voxel)

# The stone path, refs/04, 05: a landing of slate flags in front of the door sill, then a dense run
# of long, narrow slate treads set into an open grassy bank, winding down to the right through the
# gap in the dry-stone wall to the gate. Each tread is stacked on the back of the one below it, so
# the steps read as built (refs/05); where a rise is more than the slab is thick, a course of stacked
# stone under its front edge makes up the riser. The bank's turf meets the tread ends at about tread
# height. Each step: (x, y, top of its tread) at the middle of the tread's open part (its going).
LANDING = ((-0.8, -1.12), (0.82, -0.38))   # (x0, y0), (x1, y1): between the door pots, up to the sill
STEPS = (
    (0.30, -1.30, 0.00),
    (0.40, -1.58, -0.06),
    (0.50, -1.86, -0.17),
    (0.62, -2.15, -0.28),
    (0.75, -2.41, -0.33),
    (0.89, -2.67, -0.46),
    (1.02, -2.94, -0.58),
    (1.13, -3.20, -0.69),
    (1.25, -3.47, -0.78),
    (1.37, -3.74, -0.85),     # in the wall's gap, at the lawn; the rest are set in the lawn
    (1.49, -4.03, -0.90),
    (1.60, -4.28, -1.00),
    (1.72, -4.54, -1.06),
)
STEP_LENGTH = (0.95, 1.3) # the slabs' length across the path (refs/04: long and narrow)
TREAD = 0.09              # tread slab thickness (each varies about it)
RISER_DEPTH = 0.12        # front to back of the stacked riser stones under a tread's front edge
BANK = 0.85               # the bank's slope beside the path (40 degrees), rising to the terrace or
                          # falling to the lawn: an open grassy bank, not a cutting
GATE = (1.95, -4.95)
# Soil beds for Ryan's flowers and shrubs, either side of the steps, refs/04, 05: (x, y, half-length,
# half-width, direction in degrees)
BEDS = ((-0.75, -2.3, 0.55, 0.3, 20.0), (2.25, -2.5, 0.5, 0.3, -30.0), (0.2, -4.5, 0.5, 0.3, 80.0))
BENCH = (3.7, -4.4)
BIRDHOUSE = (3.3, -1.7)
LAMPS = ((-2.2, -1.5),)
RACK = None               # the rack belongs to the full row's left end

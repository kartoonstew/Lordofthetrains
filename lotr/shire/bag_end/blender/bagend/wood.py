"""Weathered, hand-worked oak for every timber part of Bag End, as relief that prints.

Each piece is a sweep: a cross-section carried along the piece's grain, its points a few mm apart
across the grain and its stations a few cm apart along it (closer over a knot). A height field over
the surface, in the piece's own frame (s along the grain, `along` across a face from its corner),
moves each point along the section's normal:

- grain: open, weathered grooves running the length of the piece, wandering a little and fading
  in and out, as on old oak whose soft wood has worn away between the hard
- checks: a few longer, deeper splits along the grain on the faces of posts and beams, and splits
  running in from the ends, carried on across the end grain
- knots: an oval, proud or sunken, with a groove round it and the grain swerving past it
- worn arrises: corners rounded by an amount that wanders along the piece, with dings; ends
  chamfered, cut a little out of square, and split

All sizes are real metres, exaggerated so they print at HO (1 mm = 8.7 cm). Relief only cuts into
the wood (a knot stands a few mm proud) and never deeper than a fraction of the piece's thickness,
and features keep clear of the rounded corners, so every piece stays one closed shell that does
not pass through itself.

Wood vertices carry the vertex layer TAG, so parts.to_object's bevel leaves them alone: the worn
corners here replace it there.
"""
import math
import random

import bmesh
import numpy as np
from mathutils import Matrix, Vector, noise

from . import parts as P

TAG = "wood"

# Mesh spacing
STEP_ACROSS = 0.007   # across the grain, on a face that shows
STEP_HIDDEN = 0.03    # across the grain, on a face hidden in a wall, a post or under turf
STEP_ALONG = 0.045    # between stations along the grain
STEP_KNOT = 0.01      # between stations over a knot
STEP_DOOR = 0.025     # between rows up a door board (the door is seen close)

# Relief (metres real; at HO divide by 0.087 for mm)
GROOVE_SPACING = (0.030, 0.048)   # grain lines, centre to centre across a face
GROOVE_WIDTH = (0.020, 0.028)     # full width of a grain groove
GROOVE_DEPTH = (0.010, 0.016)
THICK = 0.08                      # through a face this thick or more (posts, beams, the header band's
GROOVE_DEPTH_THICK = (0.016, 0.024)   # face), the grain is cut deeper, wider apart, and fades less
GROOVE_SPACING_THICK = (0.034, 0.052)
MID = 0.035                       # through a face this thick or more (boards, legs, rails, the door)
                                  # the grain also fades less, so it still reads at HO
FADE = (0.55, 0.75, 0.1)          # how a groove's depth comes and goes along the piece: base, gain on
FADE_EASED = (0.95, 0.4, 0.6)     # the noise, floor (as a fraction of its depth)
FINE_WIDTH = (0.012, 0.016)       # a finer, shallower line between two grain grooves, now and then,
FINE_DEPTH = (0.004, 0.007)       # and the only lines on a narrow face thinner than MID...
NARROW_DEPTH = (0.007, 0.009)     # ...or this deep on a narrow face MID or more thick
NARROW = 0.06                     # a face with less room than this between its usual worn corners
CHECK_WIDTH = (0.015, 0.021)      # long splits in the faces
CHECK_DEPTH = (0.018, 0.028)
SPLIT_LENGTH = (0.08, 0.30)       # splits running in from an end
KNOT_LENGTH = (0.05, 0.08)        # full size of a knot's oval, along and across the grain
KNOT_WIDTH = (0.032, 0.046)
KNOT_PROUD = (0.003, 0.005)       # a hard knot left standing...
KNOT_SUNK = (0.008, 0.013)        # ...or a hollow where one fell out
KNOT_RIM = 0.005                  # depth of the groove round a knot
GRAIN_LIMIT = 0.2                 # grain no deeper than this fraction of the piece's thickness...
CUT_LIMIT = 0.3                   # ...nor any cut deeper than this


# ---------------------------------------------------------------- small helpers

def _rng(seed, what):
    return random.Random(f"wood:{what}:{seed}")


def _noise(key, s, wavelength):
    """Smooth 1-D noise in about [-1, 1] at s (any shape), one stream per key."""
    s = np.asarray(s, dtype=float)
    lo, hi = float(s.min()) - 0.05, float(s.max()) + 0.05
    grid = np.linspace(lo, hi, max(4, int((hi - lo) / (wavelength / 10.0)) + 2))
    vals = [noise.noise(Vector((g / wavelength, key[0], key[1]))) for g in grid]
    return np.interp(s, grid, vals)


def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _layer(bm):
    return bm.verts.layers.int.get(TAG) or bm.verts.layers.int.new(TAG)


class Side:
    """One face of a section, for laying out features: its length corner to corner, its thickness
    (the section's size through it), the largest corner radius at its ends (knots and checks keep
    clear of it), the usual one (`soft`: grain lines keep clear of that, and fade out before any
    larger rounding), whether it shows, and a period for a section that wraps round (a log)."""

    def __init__(self, length, thick, radius, visible=True, period=None, soft=None):
        self.length, self.thick, self.radius, self.visible, self.period = length, thick, radius, visible, period
        self.soft = radius if soft is None else soft


class Section:
    """Points round one station's cross-section, in its (E1, E2) plane: position, outward normal,
    which side each lies on, its distance `along` that side from the side's start corner, its
    distance `edge` from the nearest rounded corner (negative on a corner), the thickness through
    it, and its distance `corner` from the nearest sharp corner of its side (the corner the
    rounding stands in for)."""

    def __init__(self, pts, nrm, side, along, edge, thick, corner=None):
        self.pts, self.nrm = np.asarray(pts, float), np.asarray(nrm, float)
        self.side, self.along = np.asarray(side, int), np.asarray(along, float)
        self.edge, self.thick = np.asarray(edge, float), np.asarray(thick, float)
        self.corner = np.full(len(self.pts), 1.0) if corner is None else np.asarray(corner, float)


def rect_section(x0, x1, y0, y1, radii, counts, arc_n=3, offset=0.0):
    """A rectangle with rounded corners, anticlockwise from its bottom-left corner. Sides: 0 bottom
    (y0), 1 right (x1), 2 top (y1), 3 left (x0); radii and counts (points on each side's flat)
    in that order, the radii at the corners where those sides start. offset is added to `along`
    (an end chamfered in by offset keeps its features lined up with the rest)."""
    C = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    D = ((1, 0), (0, 1), (-1, 0), (0, -1))
    N = ((0, -1), (1, 0), (0, 1), (-1, 0))
    Ls = (x1 - x0, y1 - y0, x1 - x0, y1 - y0)
    thick = (y1 - y0, x1 - x0, y1 - y0, x1 - x0)
    pts, nrm, side, along, edge, th, corner = [], [], [], [], [], [], []
    for j in range(4):
        k = (j + 1) % 4
        rj, rk, L = radii[j], radii[k], Ls[j]
        n = counts[j]
        for i in range(n):
            a = rj + (L - rj - rk) * i / n
            pts.append((C[j][0] + D[j][0] * a, C[j][1] + D[j][1] * a))
            nrm.append(N[j])
            side.append(j)
            along.append(a + offset)
            edge.append(min(a - rj, L - rk - a))
            th.append(thick[j])
            corner.append(min(a, L - a))
        cx = C[k][0] - D[j][0] * rk + D[k][0] * rk
        cy = C[k][1] - D[j][1] * rk + D[k][1] * rk
        t0 = math.atan2(N[j][1], N[j][0])
        for i in range(arc_n):
            f = i / arc_n
            t = t0 + f * math.pi / 2
            pts.append((cx + rk * math.cos(t), cy + rk * math.sin(t)))
            nrm.append((math.cos(t), math.sin(t)))
            if f < 0.5:
                side.append(j)
                along.append(L - rk + rk * math.sin(f * math.pi / 2) + offset)
                th.append(thick[j])
            else:
                side.append(k)
                along.append(rk - rk * math.cos(f * math.pi / 2) + offset)
                th.append(thick[k])
            edge.append(-1.0)
            corner.append(0.0)
    return Section(pts, nrm, side, along, edge, th, corner)


def circle_section(r, n, along_r=None):
    """A round section (a log): one side that wraps round, `along` measured round it (at radius
    along_r, if given, so grain lines on a turned piece keep their angle as its radius changes)."""
    t = np.arange(n) * 2 * math.pi / n
    c, s = np.cos(t), np.sin(t)
    return Section(np.stack([r * c, r * s], 1), np.stack([c, s], 1), np.zeros(n), (along_r or r) * t,
                   np.full(n, 1.0), np.full(n, 2 * r))


def side_counts(lengths, radius, visible):
    return [max(2, math.ceil(max(L - 2 * radius, 0.002) / (STEP_ACROSS if vis else STEP_HIDDEN)))
            for L, vis in zip(lengths, visible)]


def worn_radii(seed, s, base, limit, corners=4, worn=(True, True, True, True)):
    """Corner radii at stations s, (len(s), corners): each corner rounded by its own amount that
    wanders along the piece, with the odd ding where it was knocked. An unworn corner (one hidden
    in a wall) keeps a small even radius."""
    rng = _rng(seed, "radii")
    s = np.asarray(s, float)
    length = float(s.max() - s.min()) or 1.0
    out = np.empty((len(s), corners))
    for c in range(corners):
        if not worn[c]:
            out[:, c] = min(0.003, limit)
            continue
        r0 = base * rng.uniform(0.7, 1.3)
        r = r0 * (1.0 + 0.45 * _noise((rng.uniform(0, 99), rng.uniform(0, 99)), s, 0.3))
        for _ in range(int(length / 0.7 + rng.random())):
            sd, w = rng.uniform(s.min(), s.max()), rng.uniform(0.03, 0.08)
            r = r + r0 * rng.uniform(0.8, 1.5) * np.clip(1 - ((s - sd) / w) ** 2, 0, None)
        out[:, c] = np.clip(r, 0.003, limit)
    return out


# ---------------------------------------------------------------- the relief

class Grain:
    """The relief of one piece, laid out over its sides (Side) and its length.

    knots/checks: how many, chosen at random from the tuple; splits: the chance of a split at each
    worn end per side (at most two per end); scale: every cut deeper or shallower by this; sunk: knots only
    sunken (where nothing may stand proud); seams: board joints across each shown side, this far
    apart (a box clad in planks); grain: how deep the grain lines are, against the usual (0 for a
    turned finial, which keeps only its checks); deep: cut the grain deeper on a face THICK or more
    through (GROOVE_DEPTH_THICK)."""

    def __init__(self, seed, length, sides, ends=(True, True), knots=(0,), checks=(0,), splits=0.3,
                 scale=1.0, sunk=False, seams=0.0, grain=1.0, deep=True):
        # the grain lines draw on their own stream, so retuning them leaves knots, checks and
        # splits where they were
        rng = _rng(seed, "grooves")
        self.rng = _rng(seed, "grain")
        self.length, self.scale = length, scale
        self.period = {j: sd.period for j, sd in enumerate(sides) if sd.period}
        self.grooves, self.checks, self.splits, self.knots, self.seams = [], [], [], [], []
        shown = [j for j, sd in enumerate(sides) if sd.visible]

        def key():
            return (rng.uniform(0, 500), rng.uniform(0, 500))

        for j in shown:                                  # grain lines along every face that shows
            sd = sides[j]
            room = sd.length - 2 * sd.soft
            mid = deep and sd.thick >= MID
            if not sd.period and room < NARROW:
                # a narrow face (a leg, a rail, an arm): a full groove down its middle would make a
                # moulding of it, so it gets one or two fine lines, off centre
                for _ in range(rng.choice((1, 1, 2) if mid else (0, 1, 1, 2))):
                    hw, amp = rng.uniform(*FINE_WIDTH) / 2, rng.uniform(0.002, 0.004)
                    lo, hi = sd.soft + hw + amp, sd.length - sd.soft - hw - amp
                    if hi > lo:
                        d = grain * min(rng.uniform(*(NARROW_DEPTH if mid else FINE_DEPTH)), GRAIN_LIMIT * sd.thick)
                        self.grooves.append((j, rng.uniform(lo, hi), hw, d, amp, rng.uniform(0.4, 1.0), key(),
                                             *(FADE_EASED if mid else (0.3, 1.0, 0.0)), 1.3))
                continue
            thick = deep and sd.thick >= THICK
            spacing = rng.uniform(*(GROOVE_SPACING_THICK if thick else GROOVE_SPACING))
            n = max(1, int(room / spacing)) if not sd.period else max(1, round(sd.period / spacing))
            pitch = (room if not sd.period else sd.period) / n
            lines = []
            for k in range(n):
                hw = min(rng.uniform(*GROOVE_WIDTH) / 2, 0.42 * pitch)
                amp = min(rng.uniform(0.003, 0.008), 0.25 * pitch)
                p = (sd.soft if not sd.period else 0.0) + (k + 0.5 + rng.uniform(-0.3, 0.3)) * pitch
                if not sd.period:
                    p = min(max(p, sd.soft + hw + amp), sd.length - sd.soft - hw - amp)
                d = grain * min(rng.uniform(*(GROOVE_DEPTH_THICK if thick else GROOVE_DEPTH)), GRAIN_LIMIT * sd.thick)
                # (side, place, half-width, depth, wander, its wavelength, noise key, how the depth
                # comes and goes along the piece: base, gain, floor; and how sharp its bottom is)
                fade = FADE_EASED if mid else FADE
                lines.append((j, p, hw, d, amp, rng.uniform(0.5, 1.2), key(), *fade, rng.uniform(1.0, 1.6)))
            for a, b in zip(lines, lines[1:] + ([lines[0]] if sd.period and len(lines) > 2 else [])):
                gap = (b[1] - a[1]) % (sd.period or 1e9) - a[2] - b[2]           # between the two grooves
                if gap > 0.016 and rng.random() < 0.7:
                    hw = min(rng.uniform(*FINE_WIDTH) / 2, 0.4 * gap)
                    p = a[1] + a[2] + gap / 2 + rng.uniform(-0.15, 0.15) * gap
                    d = grain * min(rng.uniform(*FINE_DEPTH), GRAIN_LIMIT * sd.thick)
                    lines.append((j, p, hw, d, min(0.004, 0.2 * gap), rng.uniform(0.4, 1.0), key(), 0.15, 1.1, 0.0, 1.3))
            self.grooves += lines
            if seams:
                for k in range(1, max(1, round(sd.length / seams))):
                    self.seams.append((j, sd.length * k / round(sd.length / seams), 0.006,
                                       min(0.008, GRAIN_LIMIT * sd.thick)))
        rng = self.rng                                   # knots, checks and splits

        def spot(width, j):
            """A place on side j for a feature this wide, clear of its corners (None if none)."""
            sd = sides[j]
            if sd.period:
                return rng.uniform(0, sd.period)
            lo, hi = sd.radius + width / 2 + 0.006, sd.length - sd.radius - width / 2 - 0.006
            return rng.uniform(lo, hi) if hi > lo else None

        for _ in range(rng.choice(knots) if shown and length > 0.3 else 0):
            j = rng.choice(shown)
            a_s, a_p = rng.uniform(*KNOT_LENGTH) / 2, rng.uniform(*KNOT_WIDTH) / 2
            a_p = min(a_p, (sides[j].length - 2 * sides[j].radius) / 2 - 0.012) if not sides[j].period else a_p
            p = spot(2 * a_p + 0.012, j) if a_p > 0.01 else None
            if p is None or length < 4 * a_s + 0.1:
                continue
            s = rng.uniform(0.12 * length + 2 * a_s, 0.88 * length - 2 * a_s)
            proud = not sunk and rng.random() < 0.55
            h = rng.uniform(*KNOT_PROUD) if proud else -min(rng.uniform(*KNOT_SUNK), CUT_LIMIT * sides[j].thick)
            self.knots.append((j, s, p, a_s, a_p, h))

        for _ in range(rng.choice(checks) if shown else 0):
            j = rng.choice(shown)
            hw = rng.uniform(*CHECK_WIDTH) / 2
            p = spot(2 * hw, j)
            if p is None:
                continue
            run = rng.uniform(0.3, 0.75) * length
            s0 = rng.uniform(0.05 * length, 0.95 * length - run)
            d = min(rng.uniform(*CHECK_DEPTH), CUT_LIMIT * sides[j].thick)
            self.checks.append((j, p, hw, d, s0, s0 + run, key()))

        for end in (0, 1):
            if not ends[end]:
                continue
            made = 0
            for j in rng.sample(shown, len(shown)):
                if made == 2 or rng.random() > splits:
                    continue
                hw = rng.uniform(*CHECK_WIDTH) / 2
                p = spot(2 * hw, j)
                if p is None:
                    continue
                ell = min(rng.uniform(*SPLIT_LENGTH), 0.45 * length)
                d = min(rng.uniform(0.015, 0.025), CUT_LIMIT * sides[j].thick)
                self.splits.append((j, p, hw, d, end, ell, key()))
                made += 1

    def knot_spans(self):
        """(s, half-length) of each knot, so the sweep can put stations close over it."""
        return [(k[1], k[3]) for k in self.knots]

    def _dist(self, j, along, c):
        d = along - c
        if j in self.period:
            per = self.period[j]
            d = (d + per / 2) % per - per / 2
        return d

    def on(self, s, sec):
        """Heights over a Section at s along the grain."""
        return self.heights(s, sec.side, sec.along, sec.edge, sec.thick, sec.corner)

    def heights(self, s, side, along, edge, thick, corner=None):
        """Height (+ out of the wood) at points on `side` at `along`, at s along the grain. Within
        `corner` of a face's sharp corner nothing cuts deeper than that distance, so cuts on two
        faces that meet there can never run into each other."""
        s = np.broadcast_to(np.asarray(s, float), along.shape)
        G = np.zeros(along.shape)                       # depth of the cuts, positive

        def cut(mask, depth):
            return np.maximum(G, np.where(mask, depth, 0.0))

        for j, p, hw, d, amp, wl, key, f0, f1, flo, sharp in self.grooves:
            m = side == j
            if not m.any():
                continue
            c = p + amp * (_noise(key, s, wl) + 0.35 * _noise((key[0] + 7.0, key[1]), s, 0.3 * wl))
            for kj, ks, kp, a_s, a_p, _ in self.knots:   # the grain swerves round a knot
                if kj == j:
                    off = self._dist(j, c, kp)
                    c = c + np.sign(off) * 1.5 * a_p * np.exp(-((s - ks) / (2.0 * a_s)) ** 2) \
                        * np.exp(-(off / (2.5 * a_p)) ** 2)
            depth = d * np.clip(f0 + f1 * _noise((key[1], key[0]), s, 0.45), flo, 1.0)
            x = np.clip(self._dist(j, along, c) / hw, -1.0, 1.0)
            G = cut(m, depth * (0.5 + 0.5 * np.cos(np.pi * x)) ** sharp)
        for j, p, hw, d in self.seams:
            x = np.clip(self._dist(j, along, p) / hw, -1.0, 1.0)
            G = cut(side == j, d * np.sqrt(1 - x * x))
        for kj, ks, kp, a_s, a_p, _ in self.knots:     # no grain lines across the knot itself
            rho = np.sqrt(((s - ks) / a_s) ** 2 + (self._dist(kj, along, kp) / a_p) ** 2)
            G = np.where(side == kj, G * _smooth(1.1, 1.8, rho), G)
        for j, p, hw, d, s0, s1, key in self.checks:
            t = np.clip((s - s0) / (s1 - s0), 0.0, 1.0)
            lens = np.sqrt(np.sin(np.pi * t))
            c = p + 0.25 * hw * _noise(key, s, 0.3)
            x = self._dist(j, along, c) / (hw * (0.35 + 0.65 * lens) + 1e-9)
            G = cut(side == j, d * lens * np.clip(1 - x * x, 0.0, 1.0) ** 0.7)
        for j, p, hw, d, end, ell, key in self.splits:
            e = s if end == 0 else self.length - s
            t = np.clip(1 - e / ell, 0.0, 1.0)
            c = p + 0.2 * hw * _noise(key, s, 0.3)
            x = self._dist(j, along, c) / (hw * (0.4 + 0.6 * t))
            G = cut(side == j, d * t ** 0.8 * np.clip(1 - x * x, 0.0, 1.0) ** 0.7)
        G = G * _smooth(0.0, 0.006, edge)                # cuts fade out before a rounded corner
        G = np.minimum(G * self.scale, CUT_LIMIT * thick)
        if corner is not None:
            G = np.minimum(G, np.maximum(corner - 0.003, 0.0))
        H = -G
        for kj, ks, kp, a_s, a_p, kh in self.knots:
            rho = np.sqrt(((s - ks) / a_s) ** 2 + (self._dist(kj, along, kp) / a_p) ** 2)
            m = side == kj
            core = kh * np.sqrt(np.clip(1 - rho * rho, 0.0, 1.0)) ** (1.0 if kh > 0 else 0.5)
            H = np.where(m & (rho < 1), core * self.scale, H)
            ring = (rho - 1) * a_p                       # distance out from the oval, roughly
            rim = KNOT_RIM * np.clip(1 - ((ring - 0.006) / 0.006) ** 2, 0.0, 1.0)
            H = np.where(m & (rho >= 1), np.minimum(H, -rim * self.scale), H)
        return H

    def end_depth(self, end, ring2d, centre, tilt, outline=None):
        """depth(q, ring): how far points q (k, 2) of an end's cap go into the end grain. The end is
        cut up to `tilt` out of square (its outline, ring 0, takes only that: it must stay clear of
        the chamfer's station). On a ringed cap (a log's: outline(j, along) gives where a split
        meets the outline) each split from that end runs on across the cap towards the pith.
        ring2d is the end's outline, which keeps the cut's lowest point on it at zero."""
        rng = _rng((self.rng.random(), end), "end")
        g = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1)])
        span = np.ptp(ring2d, axis=0).max() or 1.0
        g *= rng.uniform(0.4, 1.0) * tilt / span / (np.abs(g).sum() or 1.0)
        base = -float(((ring2d - centre) @ g).min())
        pith = centre + (np.array([rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2)]) * span * 0.5)
        splits = []
        for j, p, hw, d, e, ell, key in self.splits:
            if e == end and outline is not None:
                at = outline(j, p)
                if at is not None:
                    splits.append((np.asarray(at, float), hw, d, rng.uniform(0.45, 0.85)))

        def depth(q, ring):
            q = np.atleast_2d(q)
            dep = base + (q - centre) @ g
            for at, hw, d, reach in splits if ring else ():
                axis = pith - at
                length = np.linalg.norm(axis) * reach
                axis = axis / (np.linalg.norm(axis) or 1.0)
                u = (q - at) @ axis
                w = np.abs((q - at) @ np.array([-axis[1], axis[0]]))
                t = np.clip(1 - u / length, 0.0, 1.0) * (u > -0.004)
                x = w / (hw * (0.4 + 0.6 * t) + 1e-9)
                dep = dep + 0.8 * d * t ** 0.8 * np.clip(1 - x * x, 0.0, 1.0) ** 0.7
            return dep
        return depth


# ---------------------------------------------------------------- the sweep

def flat_cap(bm, loop):
    """Close a planar outline with triangles by ear clipping. Left as one face, the outline (a long
    run of nearly collinear points down a grooved face) would be split by whatever triangulator
    reads it later, and some make slivers that overlap; ear clipping keeps every triangle inside."""
    face = bm.faces.new(loop)
    face.normal_update()                 # a new face has no normal, and triangulate projects along it
    bmesh.ops.triangulate(bm, faces=[face], quad_method="BEAUTY", ngon_method="EAR_CLIP")


def _bend(P3, normal, amp, scale, seed):
    """parts.wobble's smooth bend, kept in the section's plane (normal), so an end stays flat."""
    if not amp:
        return P3
    o = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    d = np.array([(noise.noise(p), noise.noise(p + Vector((31.7, 0, 0))), noise.noise(p + Vector((0, 57.1, 0))))
                  for p in (Vector(q) * scale + o for q in P3.tolist())]) * amp
    return P3 + d - np.outer(d @ normal, normal)


def sweep(bm, frames, secs, H, caps, bend=(0.0, 1.0, 0)):
    """Build a closed shell: each station's section (secs[i]) in its frame (O, E1, E2), moved by
    the heights H[i] along its normals, faces between stations, and a cap at each end.

    caps: (start, end), each None for a flat cap or (rings, depth): depth(q, ring) gives how far
    points go into the end grain, the outline itself taking depth at ring 0. With rings = 0 the cap
    is one face on the outline: deep cuts make a sawn section's outline anything but star-shaped,
    so no fan or ring from its centre could cap it without folding. A round section (a log), cut
    only radially, takes rings of the cap between its outline and its centre.

    bend: (amp, scale, seed) of a smooth bend like parts.wobble's, but moving each station only in
    its own plane: an arched eave meets a band's end face at a shallow angle, and a bend out of
    that plane would fold the band through its own end. Returns the new vertices."""
    tag = _layer(bm)
    rows, rings2d, mats = [], [], []
    for (O, E1, E2), sec, h in zip(frames, secs, H):
        M = np.array([tuple(E1), tuple(E2)]).T                 # 3 x 2
        G = np.linalg.inv(M.T @ M)
        n3 = sec.nrm @ M.T              # the section's normals carried by its frame: in a sheared frame
        n3 /= np.linalg.norm(n3, axis=1)[:, None]      # (a steep soffit board) cuts stay square to
                                                       # their side in the frame, so they cannot fold
        P3 = np.array(tuple(O)) + sec.pts @ M.T + n3 * h[:, None]
        rows.append(P3)
        mats.append((np.array(tuple(O)), M, M @ G))
        rings2d.append((P3 - np.array(tuple(O))) @ (M @ G))
    n = len(rows)
    outs = []
    for i, nb in ((0, 1), (n - 1, n - 2)):
        nP = Vector(np.cross(mats[i][1][:, 0], mats[i][1][:, 1]).tolist()).normalized()
        outs.append(nP if nP.dot(Vector((rows[i].mean(0) - rows[nb].mean(0)).tolist())) > 0 else -nP)
    for end, cap in enumerate(caps):                          # the outline of a worn end, cut askew
        i = 0 if end == 0 else n - 1
        if cap is not None:
            rows[i] = rows[i] - np.outer(cap[1](rings2d[i], 0), np.array(tuple(outs[end])))
    planes = [np.cross(M[:, 0], M[:, 1]) / np.linalg.norm(np.cross(M[:, 0], M[:, 1])) for _, M, _ in mats]
    verts = []
    vrows = []
    for P3, nrm in zip(rows, planes):
        row = [bm.verts.new(p) for p in _bend(P3, nrm, *bend).tolist()]
        vrows.append(row)
        verts += row
    m = len(vrows[0])
    for i in range(n - 1):
        a, b = vrows[i], vrows[i + 1]
        for k in range(m):
            kk = (k + 1) % m
            bm.faces.new((a[k], a[kk], b[kk], b[k]))
    for end in (0, 1):
        i = 0 if end == 0 else n - 1
        O, M, _ = mats[i]
        ring2d = rings2d[i]
        centre2d = ring2d.mean(0)
        rings, depth = caps[end] if caps[end] is not None else (0, None)
        if rings == 0:
            flat_cap(bm, list(reversed(vrows[i])) if end == 0 else vrows[i])
            continue
        out = np.array(tuple(outs[end]))
        loops = [vrows[i]]
        base2d, dent = secs[i].pts, ring2d - secs[i].pts
        outer = np.linalg.norm(ring2d - centre2d, axis=1)
        for r in range(1, rings + 1):
            # the outline's dents (grooves running out at the end) fade over the first rings, so the
            # rest of the end is round growth rings; each point stays on its ray, inside the last
            q = centre2d + (base2d - centre2d + dent * max(0.0, 1 - r / 4.5)) * (1 - r / (rings + 1))
            rad = np.linalg.norm(q - centre2d, axis=1)
            fit = np.minimum(rad, outer - 0.002) / np.maximum(rad, 1e-9)
            q = centre2d + (q - centre2d) * fit[:, None]
            outer = rad * fit
            P3 = O + q @ M.T - np.outer(depth(q, r), out)
            loop = [bm.verts.new(p) for p in _bend(P3, planes[i], *bend).tolist()]
            loops.append(loop)
            verts += loop
        dc = float(depth(centre2d[None, :], rings + 1)[0])
        centre = bm.verts.new(_bend((O + M @ centre2d - out * dc)[None, :], planes[i], *bend)[0].tolist())
        verts.append(centre)
        for r in range(len(loops) - 1):
            a, b = loops[r], loops[r + 1]
            for k in range(m):
                kk = (k + 1) % m
                bm.faces.new((a[kk], a[k], b[k], b[kk]) if end == 0 else (a[k], a[kk], b[kk], b[k]))
        inner = loops[-1]
        for k in range(m):
            kk = (k + 1) % m
            bm.faces.new((inner[kk], inner[k], centre) if end == 0 else (inner[k], inner[kk], centre))
    for v in verts:
        v[tag] = 1
    return verts


def _stations(length, knots, chamfer=(0.0, 0.0), step=STEP_ALONG):
    """Positions along the grain: every `step` or so, every STEP_KNOT over a knot, and the short
    first and last steps of a chamfered end."""
    n = max(2, math.ceil(length / step))
    s = set(np.linspace(0.0, length, n + 1).tolist())
    for ks, a in knots:
        s.update(np.arange(ks - 2.5 * a, ks + 2.5 * a, STEP_KNOT).tolist())
    lo, hi = chamfer[0], length - chamfer[1]
    s = {x for x in s if lo <= x <= hi} | {0.0, lo, hi, length}
    out = []
    for x in sorted(s):
        if out and x - out[-1] < 0.003:
            if x in (hi, length):             # keep the chamfer's and the end's stations exact
                out[-1] = x
            continue
        out.append(x)
    return out


# ---------------------------------------------------------------- straight timber

def timber(bm, centre, size, rot=None, amp=0.008, seed=0, ends=(True, True), hidden=(), knots=None,
           checks=None, seams=0.0, scale=1.0):
    """A worn oak post, beam or plank: size in its own frame (turned by rot), grain along its
    longest side, bent a little (amp) as hand-hewn timber is. ends: which ends show, worn and
    split; hidden: sides that never show (0 is the -E2 face, 1 +E1, 2 +E2, 3 -E1, where E1 and E2
    are the next axes round from the grain's), built coarse and plain."""
    g = max(range(3), key=lambda i: size[i])
    i1, i2 = (g + 1) % 3, (g + 2) % 3
    length, w, h = size[g], size[i1], size[i2]
    R = (rot or Matrix.Identity(4)).to_3x3()
    axes = [R @ Vector(tuple(1.0 if a == b else 0.0 for b in range(3))) for a in range(3)]
    T, E1, E2 = axes[g], axes[i1], axes[i2]
    rng = _rng(seed, "timber")
    thin = min(w, h)
    base = min(max(0.15 * thin, 0.004), 0.02)
    limit = 0.3 * thin
    visible = [j not in hidden for j in range(4)]
    big = length >= 0.8 and thin >= 0.09
    grain = Grain(seed, length,
                  [Side(L, t, limit, vis, soft=base) for L, t, vis in zip((w, h, w, h), (h, w, h, w), visible)],
                  ends=ends, seams=seams, scale=scale,
                  knots=knots or ((0, 1, 1, 2) if big else (0, 0, 1) if length >= 0.6 and thin >= 0.07 else (0,)),
                  checks=checks or ((1, 2, 2, 3) if big else (0, 1) if length >= 0.4 else (0,)))
    ch = [max(0.003, rng.uniform(0.004, 0.009) * min(1.0, thin / 0.1)) if e else 0.0 for e in ends]
    ch_len = [c * rng.uniform(1.3, 1.8) for c in ch]
    s = _stations(length, grain.knot_spans(), ch_len)
    radii = worn_radii(seed, s, base, limit)
    counts = side_counts((w, h, w, h), base, visible)
    c = Vector(centre)
    frames, secs = [], []
    for i, si in enumerate(s):
        inset = ch[0] if (i == 0 and ch[0]) else ch[1] if (i == len(s) - 1 and ch[1]) else 0.0
        r = [max(0.003, x - 0.5 * inset) for x in radii[i]]
        secs.append(rect_section(-w / 2 + inset, w / 2 - inset, -h / 2 + inset, h / 2 - inset, r, counts,
                                 offset=inset))
        frames.append((c + T * (si - length / 2), E1, E2))
    H = np.array([grain.on(si, sec) for si, sec in zip(s, secs)])
    caps = []
    for end in (0, 1):
        if not ends[end]:
            caps.append(None)
            continue
        sec = secs[0 if end == 0 else -1]
        caps.append((0, grain.end_depth(end, sec.pts, sec.pts.mean(0), 0.4 * ch_len[end])))
    return sweep(bm, frames, secs, H, caps, (amp, 2.5, seed))


# ---------------------------------------------------------------- curved timber

def arc_timber(bm, cu, cz, r0, r1, a0, a1, v0, v1, seed, amp=0.004, hidden=(1, 2), ends=(True, True),
               scale=1.0, knots=None):
    """A curved block (part of an annulus from angle a0 to a1, v0 to v1 deep) with the grain
    running round the curve. Sides: 0 the front (v0), 1 the outside, 2 the back, 3 the inside."""
    rm, vm = (r0 + r1) / 2, (v0 + v1) / 2
    w, d = r1 - r0, v1 - v0
    length = rm * (a1 - a0)
    rng = _rng(seed, "arc")
    thin = min(w, d)
    base = min(max(0.15 * thin, 0.004), 0.016)
    limit = 0.4 * thin
    visible = [j not in hidden for j in range(4)]
    grain = Grain(seed, length,
                  [Side(L, t, limit, vis, soft=base) for L, t, vis in zip((w, d, w, d), (d, w, d, w), visible)],
                  ends=ends, scale=scale, splits=0.2,
                  knots=knots or ((0, 0, 1) if length > 0.35 else (0,)), checks=(0, 1) if length > 0.3 else (0,))
    ch = [rng.uniform(0.004, 0.007) if e else 0.0 for e in ends]
    ch_len = [c * rng.uniform(1.3, 1.8) for c in ch]
    s = _stations(length, grain.knot_spans(), ch_len, step=min(STEP_ALONG, 0.04))
    worn = [visible[3] or visible[0], visible[0] or visible[1], visible[1] or visible[2], visible[2] or visible[3]]
    radii = worn_radii(seed, s, base, limit, worn=worn)
    counts = side_counts((w, d, w, d), base, visible)
    frames, secs = [], []
    for i, si in enumerate(s):
        a = a0 + si / rm
        inset = ch[0] if (i == 0 and ch[0]) else ch[1] if (i == len(s) - 1 and ch[1]) else 0.0
        r = [max(0.003, x - 0.5 * inset) for x in radii[i]]
        secs.append(rect_section(r0 - rm + inset, r1 - rm - inset, v0 - vm + inset, v1 - vm - inset, r, counts,
                                 offset=inset))
        frames.append((Vector((cu + rm * math.cos(a), vm, cz + rm * math.sin(a))),
                       Vector((math.cos(a), 0.0, math.sin(a))), Vector((0.0, 1.0, 0.0))))
    H = np.array([grain.on(si, sec) for si, sec in zip(s, secs)])
    caps = []
    for end in (0, 1):
        if not ends[end]:
            caps.append(None)
            continue
        sec = secs[0 if end == 0 else -1]
        caps.append((0, grain.end_depth(end, sec.pts, sec.pts.mean(0), 0.4 * ch_len[end])))
    return sweep(bm, frames, secs, H, caps, (amp, 4.0, seed))


def segmented_ring(bm, cu, cz, r_in, r_out, v0, v1, segments, rng, seed, gap=0.012, scale=1.0):
    """A round frame built from curved timber segments, their ends worn into V joints. Uses rng
    exactly as the plain ring did, so the parts built after it come out the same."""
    for k in range(segments):
        a0 = 2 * math.pi * k / segments + gap / r_out
        a1 = 2 * math.pi * (k + 1) / segments - gap / r_out
        dr = rng.uniform(-0.008, 0.008)
        arc_timber(bm, cu, cz, r_in, r_out + dr, a0, a1, v0 + rng.uniform(-0.004, 0.004), v1, seed * 31 + k,
                   scale=scale)


# ---------------------------------------------------------------- eave timbers

def _band(bm, us, lo, hi, v0, v1, seed, amp, wl, sides_shown, worn, knots, checks):
    """A board swept along u (the eave), its section in (v, z) from v0 to v1 and lo(u) to hi(u):
    sides 0 underside, 1 back, 2 top, 3 front. Grain runs along u; on the front, `along` is the
    distance below the top, so the grain follows the eave and the lower edge cuts across it."""
    heights = [hi(u) - lo(u) for u in us]
    d = v1 - v0
    tall = max(heights)
    visible = [j in sides_shown for j in range(4)]
    base = 0.012
    length = us[-1] - us[0]
    grain = Grain(seed, length, [Side(L, t, base * 1.4, vis) for L, t, vis in
                                 zip((d, tall, d, tall), (min(heights), d, min(heights), d), visible)],
                  ends=(False, False), knots=knots, checks=checks)
    s = sorted(set(u - us[0] for u in us) | set(x for ks, a in grain.knot_spans()
                                                for x in np.arange(ks - 2.5 * a, ks + 2.5 * a, STEP_KNOT).tolist()))
    s = [x for x in s if 0.0 <= x <= length]
    radii = worn_radii(seed, s, base, 0.4 * min(min(heights), d), worn=worn)
    counts = side_counts((d, tall, d, tall), base, visible)
    frames, secs = [], []
    for i, si in enumerate(s):
        u = us[0] + si
        secs.append(rect_section(v0, v1, lo(u), hi(u), radii[i], counts))
        frames.append((Vector((u, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))))
    H = np.array([grain.on(si, sec) for si, sec in zip(s, secs)])
    return sweep(bm, frames, secs, H, (None, None), (amp, wl, seed))


def header_band(bm, us, eave, panels, seed, h_min=0.07, h_dip=0.30, proud=0.035):
    """Timber under the eave whose lower edge arches up over each panel and dips at the posts."""
    def bot(u):
        pc, ph = next((c, h) for c, h in panels if abs(u - c) <= h + 1e-9)
        t = (u - pc) / ph
        return eave(u) - 0.05 - h_min - h_dip * t * t
    return _band(bm, us, bot, lambda u: eave(u) - 0.05, -proud, 0.1, seed, 0.007, 3.0, (0, 3),
                 (True, False, False, True), knots=(1, 1, 2), checks=(0, 1, 1))


def eave_hood(bm_fascia, bm_soffit, us, eave, out, rng, seed):
    """Curved fascia board at the front edge, and uneven soffit boards behind it, grain along each.
    Uses rng exactly as the plain hood did."""
    _band(bm_fascia, us, lambda u: eave(u) - 0.14, lambda u: eave(u) + 0.01, -out, -out + 0.06, seed + 1,
          0.008, 2.5, (0, 3), (True, False, False, True), knots=(0, 1, 1), checks=(0, 1))
    u, u1 = us[0], us[-1]
    while u < u1 - 0.02:
        w = rng.uniform(0.085, 0.12)
        gap = rng.uniform(0.008, 0.016)
        a, b = u + gap / 2, min(u1, u + w - gap / 2)
        u += w
        if b - a < 0.02:
            continue
        drop = rng.uniform(-0.006, 0.004)            # each board follows the eave across its width,
        ea, eb = eave(a) + drop, eave(b) + drop      # so on a steep arch the boards stay edge to edge
        soffit_board(bm_soffit, a, b, ea, eb, -out + 0.06, 0.05, seed + u)


def soffit_board(bm, a, b, ea, eb, v0, v1, seed, thick=0.07):
    """One soffit board under the eave, from (a, ea) to (b, eb) along its top, `thick` deep, running
    from v0 to v1 into the wall; grain along v, shown on its underside."""
    chord = math.hypot(b - a, eb - ea)
    E1 = Vector((b - a, 0.0, eb - ea)).normalized()
    E2 = Vector((0.0, 0.0, 1.0))
    length = v1 - v0
    vis = (True, False, False, False)
    grain = Grain(seed, length, [Side(chord, thick, 0.01, vis[0]), Side(thick, chord, 0.01, False),
                                 Side(chord, thick, 0.01, False), Side(thick, chord, 0.01, False)],
                  ends=(False, False), checks=(0, 0, 1))
    s = _stations(length, grain.knot_spans())
    radii = worn_radii(seed, s, 0.008, 0.02, worn=(True, True, False, False))
    counts = [max(2, math.ceil(chord / 0.009)), 2, 2, 2]
    frames, secs = [], []
    for i, si in enumerate(s):
        secs.append(rect_section(0.0, chord, -thick, 0.0, radii[i], counts))
        frames.append((Vector((a, v0 + si, ea)), E1, E2))
    H = np.array([grain.on(si, sec) for si, sec in zip(s, secs)])
    return sweep(bm, frames, secs, H, (None, None), (0.004, 5.0, seed))


def knee_brace(bm, u, z_top, seed, depth=0.26, rise=0.42, width=0.075, seg=16, grip=0.03):
    """Curved timber bracket filling the corner between a post and the eave above it.

    Its underside is a concave quarter-ellipse from the post out to the eave's front edge; its back
    and top edges sink `grip` into the post and the soffit, so it is one closed, attached solid. It
    is swept along that curve, so its grain follows the curve as in a bracket cut from a crook."""
    v0, v1 = -0.06, -0.06 - depth
    z0 = z_top - rise
    ts = [math.pi / 2 * i / seg for i in range(seg + 1)]
    A = np.array([(v1 + depth * math.cos(t), z0 + rise * math.sin(t)) for t in ts])
    run = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(A, axis=0), axis=1))])
    path = np.array([(v0 + grip, z0), (v0 + grip, z_top + grip), (v1, z_top + grip)])
    seg_len = np.linalg.norm(np.diff(path, axis=0), axis=1)
    total = seg_len.sum()
    B = []
    for f in run / run[-1]:
        x = f * total
        k = 0 if x <= seg_len[0] else 1
        x -= 0 if k == 0 else seg_len[0]
        B.append(path[k] + (path[k + 1] - path[k]) * min(x / seg_len[k], 1.0))
    B = np.array(B)
    reach = np.linalg.norm(B - A, axis=1)
    length = float(run[-1])
    vis = (True, True, False, True)
    # the underside's thickness is the bracket's typical depth behind it, not the 3 cm at its buried
    # ends: the cap per point (CUT_LIMIT of the depth there) still keeps the ends safe
    grain = Grain(seed, length, [Side(width, float(np.median(reach)), 0.012, True), Side(float(reach.max()), width, 0.012, True),
                                 Side(width, float(reach.min()), 0.012, False), Side(float(reach.max()), width, 0.012, True)],
                  ends=(False, False), checks=(0, 1), knots=(0,))
    radii = worn_radii(seed, run, 0.01, 0.3 * width, worn=(True, True, False, False))
    counts = side_counts((width, float(reach.max()), width, float(reach.max())), 0.01, vis)
    frames, secs = [], []
    for i in range(len(ts)):
        e2 = (B[i] - A[i]) / reach[i]
        secs.append(rect_section(-width / 2, width / 2, 0.0, float(reach[i]), radii[i], counts))
        frames.append((Vector((u, A[i][0], A[i][1])), Vector((1.0, 0.0, 0.0)), Vector((0.0, e2[0], e2[1]))))
    H = np.array([grain.on(float(si), sec) for si, sec in zip(run, secs)])
    return sweep(bm, frames, secs, H, (None, None), (0.005, 4.0, seed))


# ---------------------------------------------------------------- the door

def plank_door(bm, cz, r, front_v, depth, rng, seed):
    """Round planked door: boards of uneven width, slightly bowed and misaligned, each with its
    grain, worn edges and the odd split at its ends. Uses rng exactly as the plain door did."""
    u = -r
    k = 0
    while u < r - 0.02:
        w = rng.uniform(0.105, 0.15)
        gap = rng.uniform(0.008, 0.016)
        u0, u1 = u + gap / 2, min(r - 0.002, u + w - gap / 2)
        u += w
        k += 1
        if u1 - u0 < 0.02:
            continue
        lean = rng.uniform(-0.006, 0.004)
        bow = rng.uniform(-0.007, 0.007)
        door_board(bm, cz, r, u0, u1, front_v, depth, lean, bow, seed * 31 + k)


def _edge_steps(width, step):
    """Positions from 0 to width: fine at both edges (for the worn arris), `step` apart between."""
    inner = max(1, math.ceil((width - 0.016) / step))
    mid = [0.008 + (width - 0.016) * i / inner for i in range(inner + 1)]
    return [0.0, 0.003] + mid + [width - 0.003, width]


def door_board(bm, cz, r, u0, u1, front_v, depth, lean, bow, seed, roll=0.008):
    """One board of the round door, its ends cut on the circle; the grain is on its front only."""
    def zr(uu):
        return math.sqrt(max(r * r - uu * uu, 0.0))
    width = u1 - u0
    cols = _edge_steps(width, STEP_ACROSS)
    tall = max(2 * zr(u0 + a) for a in cols)
    inner = max(4, math.ceil((tall - 0.016) / STEP_DOOR))
    grain = Grain(seed, tall, [Side(width, depth, roll, True)], ends=(True, True), splits=0.25,
                  knots=(0, 0, 1), checks=(0, 0, 1), sunk=True)
    us = np.array([u0 + a for a in cols])
    H = np.array([2 * zr(uu) for uu in us])
    rows = np.array([[0.0, 0.003] + [0.008 + (h - 0.016) * i / inner for i in range(inner + 1)] + [h - 0.003, h]
                     for h in H]).T                                     # (rows, cols): distance up the board
    across = np.broadcast_to(np.array(cols), rows.shape)
    e = np.minimum(np.minimum(across, width - across), np.minimum(rows, H[None, :] - rows))
    worn = np.where(e < roll, roll - np.sqrt(np.clip(roll * roll - (roll - e) ** 2, 0.0, None)), 0.0)
    hgt = grain.heights(rows, np.zeros(rows.shape, int), across, e - roll, np.full(rows.shape, depth))
    t = rows / H[None, :]
    v = front_v + lean + bow * np.sin(np.pi * t) + worn - hgt
    z = cz - H[None, :] / 2 + rows
    tag = _layer(bm)
    nr, nc = rows.shape
    front = [[bm.verts.new((float(us[i]), float(v[j, i]), float(z[j, i]))) for i in range(nc)] for j in range(nr)]
    for j in range(nr - 1):
        for i in range(nc - 1):
            bm.faces.new((front[j][i], front[j][i + 1], front[j + 1][i + 1], front[j + 1][i]))
    rim = ([front[0][i] for i in range(nc)] + [front[j][nc - 1] for j in range(1, nr)]
           + [front[nr - 1][i] for i in range(nc - 2, -1, -1)] + [front[j][0] for j in range(nr - 2, 0, -1)])
    back = [bm.verts.new((f.co.x, front_v + depth, f.co.z)) for f in rim]
    m = len(rim)
    for k in range(m):
        kk = (k + 1) % m
        bm.faces.new((rim[kk], rim[k], back[k], back[kk]))
    flat_cap(bm, list(reversed(back)))
    verts = [x for row in front for x in row]
    for x in verts + back:
        x[tag] = 1
    P.wobble(verts, 0.003, 6.0, seed)
    return verts + back


# ---------------------------------------------------------------- a log

def log(bm, centre, r0, r1, length, rot, seed, amp=0.008):
    """A weathered log, its bark long gone: deep open grain and long checks along it, growth rings
    and radial splits across its ends. Its axis is local +z turned by rot, r0 at the -z end."""
    R = rot.to_3x3()
    T, E1, E2 = R @ Vector((0, 0, 1)), R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0))
    circ = 2 * math.pi * max(r0, r1)
    n = math.ceil(circ / 0.008)
    grain = Grain(seed, length, [Side(circ, 2 * min(r0, r1), 0.0, True, period=circ)], ends=(True, True),
                  splits=1.0, knots=(1, 2), checks=(2, 3), deep=False)
    for k, g in enumerate(grain.grooves):                         # deeper, wider furrows than a sawn face
        grain.grooves[k] = (g[0], g[1], g[2] * 1.15, g[3] * 1.4) + g[4:]
    s = _stations(length, grain.knot_spans(), (0.008, 0.008))
    c = Vector(centre)
    frames, secs = [], []
    for i, si in enumerate(s):
        r = r0 + (r1 - r0) * si / length - (0.008 if i in (0, len(s) - 1) else 0.0)
        secs.append(circle_section(r, n))
        frames.append((c + T * (si - length / 2), E1, E2))
    H = np.array([grain.on(si, sec) for si, sec in zip(s, secs)])
    rings = 9
    caps = []
    for end in (0, 1):
        sec = secs[0 if end == 0 else -1]
        rad = float(np.linalg.norm(sec.pts[0]))

        def at(j, a, rad=rad):
            t = a / rad
            return (rad * math.cos(t), rad * math.sin(t))
        dep = grain.end_depth(end, sec.pts, np.zeros(2), 0.003, at)

        def cap(q, ring, dep=dep):          # every other ring of the cap is a growth ring, cut in
            return dep(q, ring) + (0.003 if 0 < ring <= rings and ring % 2 else 0.0)
        caps.append((rings, cap))
    return sweep(bm, frames, secs, H, caps, (amp, 6.0, seed))


# ---------------------------------------------------------------- a turned finial

FINIAL = ((0.07, -0.05), (0.07, 0.0), (0.077, 0.008), (0.077, 0.022), (0.062, 0.032), (0.055, 0.045))


def finial(bm, x, y, z, seed, ball=0.1):
    """A turned ball on a collared neck, on top of a post whose top is at z: weathered, with faint
    grain up it and a check or two split down the ball."""
    prof = list(FINIAL)
    zc = 0.045 + ball * math.cos(0.6)                     # the ball meets the neck 0.6 rad off its foot
    for k in range(1, 25):
        phi = -math.pi / 2 + 0.6 + (math.pi - 0.75) * k / 24
        prof.append((ball * math.cos(phi), zc + ball * math.sin(phi)))
    n = math.ceil(2 * math.pi * ball / 0.008)
    length = prof[-1][1] - prof[0][1]
    circ = 2 * math.pi * ball
    grain = Grain(seed, length, [Side(circ, 0.1, 0.0, True, period=circ)], ends=(False, False),
                  knots=(0,), checks=(1, 2), grain=0.0)          # turned smooth, but checked
    frames, secs, s = [], [], []
    for r, dz in prof:
        secs.append(circle_section(r, n, along_r=ball))
        frames.append((Vector((x, y, z + dz)), Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))))
        s.append(dz - prof[0][1])
    H = np.array([grain.on(si, sec) for si, sec in zip(s, secs)])
    return sweep(bm, frames, secs, H, (None, None), (0.002, 6.0, seed))

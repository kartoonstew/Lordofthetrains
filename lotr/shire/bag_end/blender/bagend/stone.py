"""Fractured stone, refs/04, 05, 07: the path's slate treads, flags and risers, the dry-stone wall
and its capstones, the chimney cap and the door sill.

Every stone starts as a convex block: a box whose faces are tilted a little and whose corners and
edges are split off by fracture planes, so it has flat split faces with sharp-ish breaks between
them, as broken stone does. On that block go the marks of splitting and weather, exaggerated for HO
(the brief: relief under ~1.5 cm real, 0.17 mm at 1:87, is lost in print and paint). Sizes real:

    splits        corners and edges split off 2-7 cm deep; a wall stone's face split again into
                  2-4 facets 1.5-5 cm deep; arrises rounded over about 1 cm, not knife-sharp
    chips         round scoops out of the arrises, 6-11 cm across, 1-2 cm deep
    pits          round pocks in the faces: 5-7 cm across on rubble, 3-4.5 cm on slate, 0.6-1.2
                  cm deep
    laminae       slate: 1.8-2.8 cm thick; along the edges each sits back from its neighbours by
                  up to 2.4 cm, and patches of the top lamina, mostly near the edges, have flaked
                  off (spalls 1.3-2.4 cm deep)
    waves         split faces waved +-0.2-0.3 cm: below what prints, kept only for the previews

The surface is a lattice over the box's six faces (about one vertex per 2-2.5 cm). Each lattice
point is moved along a ray from the nearest point of a smaller core box inside the stone, to where
the ray meets the fractured block, and then in or out along the same ray by the marks above. Rays
from a convex core never cross, so however rough the surface gets it never folds through itself:
every stone is one closed, outward-facing shell. No moss or greenery: the stone stays bare for
paint, drybrushing and Ryan's own scenery moss.

Stones are gathered in a Pile and made into one mesh object at the end (numpy, no bmesh), since a
wall holds hundreds of them.
"""
import math
import random

import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

from . import layout as L, parts, scene, terrain

# How each kind of stone breaks. Lengths in metres.
RUBBLE = dict(                      # dry-stone wall stones: flat, bedded, split on all sides (refs/07)
    res=0.022, round=0.007, tilt=0.14, bed_tilt=0.05, facets=(3, 6), facet_depth=(0.25, 0.7),
    vertical_facets=False, flat_beds=True,
    chips=(0, 2), chip_r=(0.07, 0.11), chip_depth=(0.01, 0.016), bedded=0.65,
    pits=(0, 2), pit_r=(0.035, 0.05), pit_depth=(0.008, 0.012),
    wave=0.002, wave_len=0.09, lam=(0.03, 0.055), lam_inset=0.014, spall=0.0, face_splits=(1, 3))
SLATE = dict(                       # treads, flags, risers, capstones: flat cleaved top, layered edges
    res=0.02, round=0.007, tilt=0.012, facets=(2, 4), facet_depth=(0.3, 0.9), vertical_facets=True,
    chips=(5, 9), chip_r=(0.05, 0.08), chip_depth=(0.01, 0.02), bedded=1.0,
    pits=(0, 2), pit_r=(0.018, 0.026), pit_depth=(0.006, 0.01),
    wave=0.003, wave_len=0.14, lam=(0.018, 0.028), lam_inset=0.024, spall=0.28)
FLAG = dict(SLATE, spall=0.12, chips=(2, 4))      # flags at the door: worn flatter, fewer flakes off
CORE = 0.07        # rays start this far (at most) inside each face of the stone's box


class Pile:
    """Stones gathered for one object: vertices and quads in world space."""

    def __init__(self):
        self.verts, self.quads, self.n = [], [], 0

    def add(self, verts, quads):
        self.verts.append(verts)
        self.quads.append(quads + self.n)
        self.n += len(verts)

    def into(self, bm):
        """Add the stones to a bmesh, for builders that place and finish their own objects."""
        vs = [bm.verts.new(p) for p in np.concatenate(self.verts)]
        for q in np.concatenate(self.quads):
            bm.faces.new([vs[i] for i in q])
        return bm

    def to_object(self, name, mat, coll):
        me = bpy.data.meshes.new(name)
        if self.verts:
            v = np.concatenate(self.verts)
            q = np.concatenate(self.quads)
            me.vertices.add(len(v))
            me.vertices.foreach_set("co", v.astype(np.float32).ravel())
            me.loops.add(4 * len(q))
            me.loops.foreach_set("vertex_index", q.astype(np.int32).ravel())
            me.polygons.add(len(q))
            me.polygons.foreach_set("loop_start", np.arange(0, 4 * len(q), 4, dtype=np.int32))
            me.update(calc_edges=True)
            # renders only: smooth within a face, sharp across every break (over 20 degrees), so the
            # preview shows the fractures and not the lattice's quads
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(20))
        obj = bpy.data.objects.new(name, me)
        scene.collection(coll).objects.link(obj)
        if mat is not None:
            obj.data.materials.append(parts.materials()[mat] if isinstance(mat, str) else mat)
        return obj


def lattice(xs, ys, zs):
    """The surface of a box as a quad lattice on the given levels along x, y and z (each ascending,
    from -1 to 1): points (n, 3) and outward-facing quads (m, 4)."""
    xs, ys, zs = (np.asarray(a, float) for a in (xs, ys, zs))
    nx, ny, nz = len(xs) - 1, len(ys) - 1, len(zs) - 1
    on = np.zeros((nx + 1, ny + 1, nz + 1), bool)
    on[[0, -1], :, :] = on[:, [0, -1], :] = on[:, :, [0, -1]] = True
    ijk = np.argwhere(on)
    idx = -np.ones(on.shape, int)
    idx[tuple(ijk.T)] = np.arange(len(ijk))
    pts = np.stack([xs[ijk[:, 0]], ys[ijk[:, 1]], zs[ijk[:, 2]]], axis=1)
    quads = []
    for k, out in ((nz, True), (0, False)):          # top and bottom, in (x, y)
        g = idx[:, :, k]
        q = np.stack([g[:-1, :-1], g[1:, :-1], g[1:, 1:], g[:-1, 1:]], -1).reshape(-1, 4)
        quads.append(q if out else q[:, ::-1])
    for i, out in ((nx, True), (0, False)):          # ends, in (y, z)
        g = idx[i, :, :]
        q = np.stack([g[:-1, :-1], g[1:, :-1], g[1:, 1:], g[:-1, 1:]], -1).reshape(-1, 4)
        quads.append(q if out else q[:, ::-1])
    for j, out in ((ny, True), (0, False)):          # front and back, in (z, x)
        g = idx[:, j, :]
        q = np.stack([g[:-1, :-1], g[:-1, 1:], g[1:, 1:], g[1:, :-1]], -1).reshape(-1, 4)
        quads.append(q if out else q[:, ::-1])
    return pts, np.concatenate(quads)


def _levels(n):
    return np.linspace(-1.0, 1.0, n + 1)


def _laminae(h, rng, lam):
    """Lamina boundaries across a slab of half-thickness h, from the bottom up."""
    out, z = [], -h + rng.uniform(*lam)
    while z < h - 0.6 * lam[0]:
        out.append(z)
        z += rng.uniform(*lam)
    return out


def _softmin(T, tau):
    """Smooth minimum along the last axis: within ~tau of each other the values blend, so where two
    faces meet the edge is rounded over a couple of centimetres instead of aliased by the lattice."""
    m = T.min(axis=-1)
    with np.errstate(invalid="ignore"):
        return m - tau * np.log(np.sum(np.exp(-(T - m[..., None]) / tau), axis=-1))


def _scoop(R, c, d, S, r, tau):
    """Pull every ray that meets the sphere (S, r) back to where it enters it: a round chip or pit."""
    sc = S - c
    b = np.einsum("ij,ij->i", d, sc)
    disc = b * b - (np.einsum("ij,ij->i", sc, sc) - r * r)
    t = b - np.sqrt(np.maximum(disc, 0.0))
    hit = (disc > 0) & (t > 0)
    return np.where(hit, _softmin(np.stack([R, np.where(hit, t, R + 1.0)], -1), tau), R)


def _shown(n, h, sign, res):
    """Levels along an axis whose only visible end is `sign`: fine for 8 cm from it, then coarse."""
    fine = [sign * (1.0 - k * res / h) for k in range(n + 1) if k * res < min(0.08, 1.2 * h)]
    rest = [x for x in (-0.5 * sign, -sign) if sign * x < sign * fine[-1] - res / h]
    return np.array(sorted(fine + rest))


def block(pile, centre, size, rng, rot=None, style=RUBBLE, face=None):
    """One fractured stone on a box of `size` about `centre`, turned by `rot`; returns its world
    vertices (an array, also added to the pile). face=(axis, sign): the stone's only visible face
    (a wall stone's front), which then gets the detail, while its hidden back stays coarse."""
    st = style
    h = np.array(size, float) / 2
    assert np.all(h > 0.0), size
    res = st["res"]
    n = [max(2, math.ceil(2 * a / res)) for a in h]
    lam_b = _laminae(h[2], rng, st["lam"]) if rng.random() < st["bedded"] else []
    zs = list(_levels(n[2]) * h[2])
    for b in lam_b:                     # crisp steps between laminae: two rows 3 mm apart at each
        zs = [z for z in zs if abs(z - b) > 0.006] + [b - 0.0015, b + 0.0015]
    levels = [_levels(n[0]), _levels(n[1]), np.array(sorted(zs)) / h[2]]
    if face is not None and face[0] < 2:
        levels[face[0]] = _shown(n[face[0]], h[face[0]], face[1], res)
    p, quads = lattice(*levels)
    p = p * h

    # rays from the core box
    s = np.minimum(0.85 * h, CORE)
    core = h - s
    c = np.clip(p, -core, core)
    d = p - c
    d /= np.linalg.norm(d, axis=1)[:, None]

    # the fractured block: six tilted faces and a few fracture planes
    planes = []
    for a in range(3):
        for sg in (-1.0, 1.0):
            nrm = np.zeros(3)
            nrm[a] = sg
            t = st["tilt"] if (a == 2 or not st["vertical_facets"]) else 0.12
            if a == 2 and "bed_tilt" in st:             # bedded stone: its top and bottom stay flat
                t = st["bed_tilt"]
            for b in range(3):
                if b != a and not (st["vertical_facets"] and a < 2 and b == 2):
                    nrm[b] += rng.uniform(-t, t)
            nrm /= np.linalg.norm(nrm)
            off = h[a] * (1.0 - rng.uniform(0.0, 0.05 if a == 2 else 0.08))
            planes.append((nrm, off * abs(nrm[a])))
    for _ in range(rng.randint(*st["facets"])):
        sg = np.array([rng.choice((-1.0, 1.0)) for _ in range(3)])
        w = np.array([rng.uniform(0.25, 1.0) for _ in range(3)])
        if st["vertical_facets"]:
            w[2] = 0.0
        elif rng.random() < 0.4:
            w[rng.randrange(3)] = 0.0                      # an edge split rather than a corner
        if st.get("flat_beds"):
            w[2] *= 0.35                                   # bedded stone splits mostly square to its beds
        nrm = sg * w
        nrm /= np.linalg.norm(nrm)
        support = float(np.abs(nrm) @ h)
        depth = rng.uniform(*st["facet_depth"]) * float(min(s[a] for a in range(3) if nrm[a]))
        planes.append((nrm, support - depth))
    if face is not None:                      # the show face split into a few flat facets
        a = face[0]
        for _ in range(rng.randint(*st.get("face_splits", (0, 0)))):
            nrm = np.zeros(3)
            nrm[a] = face[1]
            for b in range(3):
                if b != a:
                    nrm[b] = rng.choice((-1.0, 1.0)) * rng.uniform(0.0, 0.6)
            nrm /= np.linalg.norm(nrm)
            support = float(np.abs(nrm) @ h)
            planes.append((nrm, support - rng.uniform(0.25, 0.7) * float(s[a])))
    N = np.array([q[0] for q in planes])
    D = np.array([q[1] for q in planes])
    nd = d @ N.T
    with np.errstate(divide="ignore", invalid="ignore"):
        tt = np.where(nd > 1e-6, (D[None, :] - c @ N.T) / nd, np.inf)
    R0 = np.linalg.norm(p - c, axis=1)
    R = _softmin(tt, st["round"])

    o = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    hit = c + R[:, None] * d
    horiz = np.hypot(d[:, 0], d[:, 1])

    # split faces gently waved
    if st["wave"]:
        wl = st["wave_len"]
        R = R + st["wave"] * np.array([noise.noise(Vector(q) / wl + o) for q in hit])

    # laminae: each sits back from its neighbours along the edges by its own amount
    if lam_b:
        k = np.searchsorted(np.array(lam_b), p[:, 2])
        top_k = len(lam_b)
        inset = np.empty(len(p))
        for i, (q, kk) in enumerate(zip(hit, k)):
            v = noise.noise(Vector((q[0] / 0.13, q[1] / 0.13, kk * 2.7)) + o)
            bias = -0.35 if kk == top_k else (0.15 if kk == 0 else 0.0)
            inset[i] = min(1.0, max(0.0, 1.3 * v + 0.35 + bias))
        R = R - st["lam_inset"] * inset * np.clip((horiz - 0.35) / 0.5, 0.0, 1.0)

    # spalls: patches of the top lamina flaked off, more often near the edges
    if st["spall"] and lam_b:
        drop = h[2] - lam_b[-1]
        e = np.maximum(np.abs(p[:, 0]) / h[0], np.abs(p[:, 1]) / h[1])
        top = p[:, 2] > lam_b[-1] + 0.002        # the whole top lamina, its edges too
        thr = 0.75 - 0.65 * np.clip((e - 0.65) / 0.35, 0.0, 1.0) - (st["spall"] - 0.25)
        for i in np.nonzero(top)[0]:             # a soft ramp, so the scar's rim is not grid-stepped
            q = hit[i]
            v = noise.noise(Vector((q[0] / 0.22, q[1] / 0.22, 7.7)) + o) - thr[i]
            R[i] -= 0.85 * drop * min(1.0, max(0.0, v / 0.07)) / max(d[i, 2], 0.45)

    # chips out of the arrises and pits in the faces: round scoops
    def surface_point(sel):
        i = rng.choice(sel)
        return c[i] + R[i] * d[i], d[i]
    on = np.sum(np.abs(p) > h - 1e-6, axis=1)
    shown = np.ones(len(p), bool) if face is None else (p[:, face[0]] * face[1] > h[face[0]] - 1e-6)
    edge = np.nonzero((on == 2) & shown)[0]   # along the arrises, not at the corners, where rays crowd
    faces = np.nonzero((on == 1) & shown)[0]
    small = float(h.min())               # a small stone takes small chips
    span = float(h[0] + h[1]) / 0.8          # fewer chips on a small stone
    for _ in range(max(1, round(rng.randint(*st["chips"]) * min(1.0, span)))):
        q, dq = surface_point(edge)
        r = min(rng.uniform(*st["chip_r"]), 1.2 * small)
        R = _scoop(R, c, d, q + dq * (r - min(rng.uniform(*st["chip_depth"]), 0.35 * small)), r, st["round"])
    if len(faces):
        area = 4 * (h[0] * h[1] + h[1] * h[2] + h[0] * h[2])
        if face is not None:
            area = 4 * np.prod([h[b] for b in range(3) if b != face[0]]) * 2.5
        for _ in range(round(rng.randint(*st["pits"]) * max(0.5, area / 0.25))):
            q, dq = surface_point(faces)
            r = min(rng.uniform(*st["pit_r"]), 0.6 * small)
            R = _scoop(R, c, d, q + dq * (r - min(rng.uniform(*st["pit_depth"]), 0.3 * small)), r, 0.5 * st["round"])

    R = np.maximum(R, 0.25 * R0)
    local = c + R[:, None] * d
    m = np.array(Matrix.Translation(centre) @ (rot or Matrix.Identity(4)))
    world = local @ m[:3, :3].T + m[:3, 3]
    pile.add(world, quads)
    return world


def slab(pile, centre_top, size, rng, yaw=0.0, tilt=(0.0, 0.0), style=SLATE):
    """A slate slab whose highest point is centre_top's height: (x, y, top), size (length along its
    yaw, width, thickness). tilt: small (pitch, roll) in radians. Returns its world vertices."""
    x, y, top = centre_top
    rot = (Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(tilt[0], 4, "Y")
           @ Matrix.Rotation(tilt[1], 4, "X"))
    w = block(pile, (x, y, top - size[2] / 2), size, rng, rot, style)
    dz = top - w[:, 2].max()
    w[:, 2] += dz            # the pile holds this same array, so the stone moves with it
    return w


# ---------------------------------------------------------------- the path

COLL = "garden"


def _frame(k):
    """Tread k's middle (x, y), its downhill direction, and how far it is to the treads behind and
    ahead (its open going)."""
    pts = terrain.path_line()
    p = pts[k]
    ahead = np.linalg.norm(pts[k + 1] - p)
    behind = np.linalg.norm(p - pts[k - 1]) if k else 0.5
    u = pts[k + 1] - (pts[k - 1] if k else p)
    return p, u / np.linalg.norm(u), behind, ahead


def _yaw(u):
    return math.atan2(u[1], u[0])


def _ground(q):
    return float(terrain.ground(q[0], q[1]))


def path(seed=61):
    """The landing, then step by step a long, narrow slate tread (now and then two side by side)
    whose back is tucked under the tread above and whose front rests on the tread below; where the
    rise is more than the slab is thick, a course of stacked stone under its front edge; and here and
    there a small stone packed at a tread's end (refs/04, 05)."""
    rng = random.Random(seed)
    landing(rng)
    n = len(L.STEPS)
    for k, (x, y, z) in enumerate(L.STEPS):
        pile = Pile()
        p, u, behind, ahead = _frame(k)
        v = np.array([-u[1], u[0]])                 # across, to the left going down
        yaw = _yaw(u)
        last = k == n - 1
        nose = ahead / 2 + rng.uniform(0.015, 0.03)                  # past the next tread's riser line
        back = (behind / 2 if k else 0.1) + rng.uniform(0.06, 0.11)  # tucked under the tread above
        mid = p + u * (nose - back) / 2 + v * rng.uniform(-0.08, 0.08)
        below = _ground(p + u * nose) if last else L.STEPS[k + 1][2]
        rise = z - below
        t = rng.uniform(0.07, 0.1)
        stacked = rise - t <= 0.035
        if stacked:                                  # rests straight on the tread below (refs/05)
            t = min(max(t, rise + 0.004), 0.13)
        length = rng.uniform(*L.STEP_LENGTH)
        tilt = (rng.uniform(0.004, 0.015), rng.uniform(-0.01, 0.01))      # falls a little forward
        if rng.random() < 0.2:                       # two slabs side by side, as in refs/05
            split = rng.uniform(0.38, 0.62)
            joint = rng.uniform(0.02, 0.03)
            for a, b in ((-length / 2, -length / 2 + split * length - joint / 2),
                         (-length / 2 + split * length + joint / 2, length / 2)):
                c = mid + v * (a + b) / 2 + u * rng.uniform(-0.015, 0.015)
                slab(pile, (c[0], c[1], z - rng.uniform(0.0, 0.006)), (nose + back + rng.uniform(-0.03, 0.0), b - a, t),
                     rng, yaw + rng.uniform(-0.03, 0.03), tilt)
        else:
            slab(pile, (mid[0], mid[1], z), (nose + back, length, t), rng, yaw + rng.uniform(-0.06, 0.06), tilt)
        if not stacked:                              # the riser: stacked stone on the tread below
            riser(pile, p + u * (nose - 0.035 - L.RISER_DEPTH / 2), u, length - rng.uniform(0.05, 0.15),
                  below - 0.008, z - t + 0.008, rng)
        for side in (-1, 1):                         # a small stone packed at the end, now and then
            if rng.random() > 0.4:
                continue
            ln, wd = rng.uniform(0.12, 0.22), rng.uniform(0.07, 0.12)
            c = mid + u * rng.uniform(-0.3, 0.6) * nose + v * side * (length / 2 + 0.02 + wd / 2)
            g = _ground(c)
            top = min(z - 0.02, g + rng.uniform(0.02, 0.045))
            hgt = top - (g - 0.04)
            block(pile, (c[0], c[1], top - hgt / 2), (ln, wd, hgt), rng,
                  Matrix.Rotation(yaw + rng.uniform(-0.3, 0.3), 4, "Z"), SLATE)
        pile.to_object(f"step_{k}", "stone", COLL)


def riser(pile, centre, u, width, z0, z1, rng):
    """Stacked slate under a tread's front edge, from z0 up to z1: one course, or two if tall."""
    v = np.array([-u[1], u[0]])
    yaw = _yaw(u)
    h = z1 - z0
    courses = 1 if h < 0.11 else 2
    zc = z0
    for c in range(courses):
        hc = h / courses
        a = -width / 2 + rng.uniform(-0.03, 0.03) + (0.12 if c % 2 else 0.0)
        a = max(a, -width / 2)
        while a < width / 2 - 0.05:
            ln = min(rng.uniform(0.24, 0.45), width / 2 - a)
            depth = L.RISER_DEPTH + rng.uniform(-0.02, 0.01)
            q = centre + v * (a + ln / 2) + u * rng.uniform(-0.015, 0.01)
            block(pile, (q[0], q[1], zc + hc / 2), (depth, ln - 0.015, hc + 0.004), rng,
                  Matrix.Rotation(yaw + rng.uniform(-0.04, 0.04), 4, "Z"), SLATE, face=(0, 1))
            a += ln
        zc += hc


def landing(rng):
    """Slate flags laid in front of the door, crazy-paving fashion, their joints left open."""
    (x0, y0), (x1, y1) = L.LANDING
    pile = Pile()
    cols = 3
    xs = [x0] + [x0 + (x1 - x0) * (i + rng.uniform(-0.12, 0.12)) / cols for i in range(1, cols)] + [x1]
    for i in range(cols):
        rows = rng.choice((2, 2, 3))
        ys = [y0] + [y0 + (y1 - y0) * (j + rng.uniform(-0.15, 0.15)) / rows for j in range(1, rows)] + [y1]
        for j in range(rows):
            jx, jy = rng.uniform(0.018, 0.03), rng.uniform(0.018, 0.03)
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            slab(pile, (cx, cy, L.TERRACE_Z + rng.uniform(0.018, 0.028)),
                 (xs[i + 1] - xs[i] - jx, ys[j + 1] - ys[j] - jy, rng.uniform(0.07, 0.085)), rng,
                 rng.uniform(-0.05, 0.05), (rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01)), FLAG)
    pile.to_object("landing", "stone", COLL)


# ---------------------------------------------------------------- the dry-stone wall

def block_box(pile, centre, size, yaw):
    """A plain box (a wall's hidden core)."""
    p, q = lattice([-1, 1], [-1, 1], [-1, 1])
    m = np.array(Matrix.Translation(centre) @ Matrix.Rotation(yaw, 4, "Z"))
    pile.add((p * np.array(size) / 2) @ m[:3, :3].T + m[:3, 3], q)


def dry_wall(pile, x0, x1, face, z0, top, ground, rng, depth=(0.22, 0.3), core=(0.12, 0.36)):
    """A dry-stone wall whose face runs along y = face from x0 to x1 and looks toward -y (refs/07).

    It stands from z0 up to top(x), the turf behind it, which falls where the bank dips to the path;
    ground(x) is the turf in front of it, which buries its lowest stones there. A recessed core, then
    courses of flat, bedded stones of mixed lengths with deep joints, pinning stones over the short
    ones and wedges in the wide joints, and capstones following the top.
    """
    z1 = max(top(x) for x in np.linspace(x0, x1, 40))
    # core: plain blocks well behind the stone faces, so the joints read as deep shadow
    x, i = x0, 0
    while x < x1 - 1e-6:
        b = min(x + 0.25, x1)
        zt = min(top(x), top(b)) - 0.06
        back = 0.004 * (i % 2)              # overlapping blocks never share a face plane
        if zt - z0 > 0.08:
            block_box(pile, ((x + b) / 2, face + (core[0] + core[1]) / 2 + back, (z0 - 0.15 + zt) / 2 - back),
                      (b - x + 0.02, core[1] - core[0], zt - z0 + 0.15), 0.0)
        x, i = b, i + 1
    # courses, filling z0..z1 exactly; bigger stones low down, all of them long and flat
    hs = []
    while sum(hs) < z1 - z0:
        hs.append(rng.uniform(0.16, 0.22) if not hs else rng.uniform(0.1, 0.19))
    hs = [h * (z1 - z0) / sum(hs) for h in hs]
    z = z0
    for ci, hc in enumerate(hs):
        a = x0 + rng.uniform(0.0, 0.18) - 0.04 * (ci % 2)
        while a < x1 - 0.06:
            ln = rng.choice((rng.uniform(0.22, 0.36), rng.uniform(0.3, 0.48), rng.uniform(0.4, 0.62)))
            ln = min(ln, x1 + 0.02 - a)
            if ln < 0.1:
                break
            gap = rng.uniform(0.014, 0.036)
            mid = a + ln / 2
            room = min(top(a), top(a + ln)) - z        # up to the turf behind, at this stone's lower end
            if room < 0.05 or z + min(hc, room) < ground(mid) + 0.02:
                a += ln                                 # above the turf here, or buried in the bank
                continue
            reaches = z + hc >= room + z - 0.04         # this course meets the top here
            short = rng.random() < 0.28 and not reaches
            hs_ = (room if reaches else hc - rng.uniform(0.012, 0.028)) * (rng.uniform(0.6, 0.8) if short else 1.0)
            deep = rng.uniform(*depth)
            proud = rng.uniform(-0.005, 0.03)
            zc = z + hs_ / 2 + (0.0 if reaches else rng.uniform(0.0, 0.01))
            rot = (Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, "Z")
                   @ Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, "Y")
                   @ Matrix.Rotation(rng.uniform(-0.03, 0.03), 4, "X"))
            if hs_ > 0.035:
                block(pile, (mid, face + deep / 2 - proud, zc), (ln - gap, deep, hs_), rng, rot, RUBBLE, face=(1, -1))
            if short and ln > 0.22:                      # a flat pinning stone over a short one
                pl = rng.uniform(0.5, 0.85) * (ln - gap)
                block(pile, (mid + rng.uniform(-0.05, 0.05), face + 0.07, z + hs_ + (hc - hs_) / 2),
                      (pl, 0.14, max(0.03, hc - hs_ - 0.012)), rng,
                      Matrix.Rotation(rng.uniform(-0.1, 0.1), 4, "Z"), SLATE, face=(1, -1))
            if gap > 0.026 and hc > 0.1 and not reaches and rng.random() < 0.6:   # a wedge in a wide joint
                block(pile, (a + ln - gap / 2, face + 0.06, z + rng.uniform(0.3, 0.7) * hc),
                      (gap + 0.012, 0.12, rng.uniform(0.03, 0.05)), rng,
                      Matrix.Rotation(rng.uniform(-0.2, 0.2), 4, "Z"), SLATE, face=(1, -1))
            a += ln
        z += hc
    # flat capstones, a little overhanging; where the top falls to the path they step down with it,
    # each one short and level, as copes on a sloping wall do
    a = x0 + rng.uniform(0.0, 0.08)
    while a < x1 - 0.08:
        steep = abs(top(a + 0.3) - top(a)) > 0.06
        ln = min(rng.uniform(0.22, 0.32) if steep else rng.uniform(0.3, 0.55), x1 + 0.04 - a)
        mid = a + ln / 2
        low = min(top(a), top(a + ln))
        if low - max(ground(mid), z0) > 0.1:
            th = rng.uniform(0.05, 0.075)
            slab(pile, (mid, face + 0.17 + rng.uniform(-0.02, 0.01), low + th), (ln - rng.uniform(0.012, 0.03), 0.38, th),
                 rng, rng.uniform(-0.04, 0.04), (rng.uniform(-0.015, 0.015), rng.uniform(-0.015, 0.01)))
        a += ln


def wall_gap():
    """Where the wall stops either side of the path: the bank there comes down to the treads."""
    face = L.WALL_Y - 0.2
    xs = np.linspace(L.MODEL_X[0], L.MODEL_X[1], 3000)
    _, d = terrain.path_frame(xs, np.full_like(xs, face))
    inside = xs[np.abs(d) < terrain.TREAD_ENDS + 0.02]
    return float(inside.min()), float(inside.max())


def walls(seed=67):
    """The dry-stone wall holding up the terrace (refs/07), with a gap where the path comes through;
    either side of the gap its top follows the bank down to the treads."""
    rng = random.Random(seed)
    face = L.WALL_Y - 0.2
    gap = wall_gap()
    z0 = L.LAWN_Z - 0.12

    def top(x):
        return min(L.TERRACE_Z, float(terrain.ground(x, L.WALL_Y + 0.03)))

    def ground(x):
        return float(terrain.ground(x, face - 0.05))
    for name, x0, x1 in (("wall_west", L.MODEL_X[0] + L.EDGE_FALL, gap[0]),
                         ("wall_east", gap[1], L.MODEL_X[1] - L.EDGE_FALL)):
        pile = Pile()
        dry_wall(pile, x0, x1, face, z0, top, ground, rng)
        pile.to_object(name, "stone", COLL)

"""The oak on the hill top over Bag End (refs/01, 03, 09, 10), a separate print that plugs into a
socket in the hill.

An old, gnarled oak: a thick trunk whose root flare runs out into surface roots over the turf,
heavy limbs that leave it low and spread, rising at their ends, and finer branches that grow out
into a full, domed crown of leaf clumps with gaps where the limbs show.

How it is made:
- the skeleton: the trunk (bending on up into the leader) and the limbs are grown as bending paths;
  the branches are grown from the outer limbs by space colonization toward clouds of points, one
  cloud per leaf clump, the clumps spread over a dome; branches and limbs are as thick as the twigs
  they carry (the pipe model), never thinner than OAK_TWIG.
- the wood (oak_trunk): the trunk, every root, limb and branch, and the peg are each their own
  closed tube, overlapping where they join (overlapping closed shells, not a boolean union). Each
  tube's rings are star-shaped round its path, and the path is smoothed until no ring crosses the
  next, so no shell crosses itself. Oak bark is cut into the tubes: long ridges between furrows
  that run along the wood, splitting and joining, broken into plates; 3 cm deep on the trunk,
  shallower on the limbs, none on the twigs (it would not print). The trunk swells into
  buttresses and up into each limb; the roots and the trunk's foot lie on the turf; a keyed peg
  under the trunk goes into a socket in the hill.
- the foliage (oak_crown): each clump is a core with many knobbly leaf clusters over it, and more
  along the twigs that carry it, voxel-remeshed into one closed surface: no hidden faces, no
  self-crossing, held up by the branch tips inside it, and knobbly enough to take flock and
  drybrushing.

Ryan adds any moss himself: the bark is bare relief.
"""
import math
import random
from dataclasses import dataclass

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

from . import layout as L, parts as P, terrain, treekit as T

COLL = "oak"


@dataclass
class Branch:
    pts: np.ndarray        # (n, 3) path from its base (inside its parent) to its end
    radii: np.ndarray      # (n,) radius of the wood (before bark)
    level: int             # 0 trunk, 1 limb, 2 and up branches
    twist: float = 0.0     # spiral of the bark, radians per metre
    exit: float = 0.0      # how far along it the branch comes out of its parent


@dataclass
class Oak:
    trunk: object          # the wood: trunk, roots, limbs, branches and peg
    crown: object          # the foliage clumps
    branches: list         # the skeleton (trunk, limbs, branches), for tests
    tips: np.ndarray       # branch ends that carry foliage
    tangled: int = 0       # tubes whose rings could not be kept apart (none expected)


def ground(x, y):
    return terrain.ground(x, y)


# ---------------------------------------------------------------- skeleton

def _direction(az, el):
    return np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])


def _turn(d, want, max_angle):
    """Turn unit vector d toward want by at most max_angle."""
    c = float(np.clip(np.dot(d, want), -1.0, 1.0))
    ang = math.acos(c)
    if ang <= max_angle:
        return want
    axis = np.cross(d, want)
    n = np.linalg.norm(axis)
    if n < 1e-9:
        return d
    axis /= n
    a = max_angle
    return d * math.cos(a) + np.cross(axis, d) * math.sin(a) + axis * np.dot(axis, d) * (1 - math.cos(a))


def _grow(start, az, elevation, length, r0, r1, seed, step=0.1, meander=0.45, curl=3.5, d0=None):
    """A bending limb: heads off at azimuth az (or along d0), its elevation following
    elevation(t), meandering side to side, never bending tighter than `curl` times its radius."""
    n = max(2, int(length / step))
    p = np.array(start, dtype=float)
    d = _direction(az, elevation(0.0)) if d0 is None else np.array(d0, dtype=float)
    pts = [p.copy()]
    for k in range(1, n + 1):
        t = k / n
        a = az + meander * noise.noise(Vector((t * 2.3, seed * 1.7, 0.5)))
        e = elevation(t) + 0.22 * noise.noise(Vector((t * 2.9, seed * 1.7, 7.5)))
        r = r1 + (r0 - r1) * (1 - t) ** 1.3
        d = _turn(d, _direction(a, e), step / (curl * r))
        p = p + d * step
        pts.append(p.copy())
    ts = np.linspace(0.0, 1.0, len(pts))
    return np.array(pts), r1 + (r0 - r1) * (1 - ts) ** 1.3


def _profile(e0, e1, e2):
    """Elevation (radians) along a limb: e0 where it leaves, e1 at 45 %, e2 at its end."""
    def f(t):
        return math.radians(e0 + (e1 - e0) * T.smoothstep(0.0, 0.45, t) + (e2 - e1) * T.smoothstep(0.45, 1.0, t))
    return f


def _arc(pts):
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])


def _at(br, s):
    """Point and radius at arc length s along a branch."""
    a = _arc(br.pts)
    return np.array([np.interp(s, a, br.pts[:, k]) for k in range(3)]), float(np.interp(s, a, br.radii))


def _exit(pts, parent):
    """How far along a path it leaves its parent's wood."""
    a = _arc(pts)
    for i, p in enumerate(pts):
        d = np.linalg.norm(parent.pts - p, axis=1)
        j = int(d.argmin())
        if d[j] > 1.05 * parent.radii[j]:
            return float(a[i])
    return float(a[-1])


def _trunk(base, rng, seed):
    """The trunk: a short, leaning bole flaring into its roots, which bends on up into the leader,
    the thickest of the rising limbs."""
    H, R = L.OAK_FORK, L.OAK_GIRTH / 2
    lean_az = rng.uniform(0, 2 * math.pi)
    lean = math.radians(rng.uniform(5, 9))
    lean_v = np.array([math.cos(lean_az), math.sin(lean_az), 0.0])
    side_v = np.array([-lean_v[1], lean_v[0], 0.0])
    hs = np.linspace(0.0, H, 30)
    bole = np.array([base + lean_v * h * math.tan(lean) + side_v * 0.06 * math.sin(math.pi * h / H)
                     + np.array([0.0, 0.0, h]) for h in hs])
    d0 = T.unit(bole[-1] - bole[-2])
    lead, lead_r = _grow(bole[-1], lean_az, _profile(70, 55, 66), rng.uniform(3.3, 3.8), 0.62 * R, 0.05,
                         seed + 3, d0=d0)
    pts = np.concatenate([bole, lead[1:]])
    s = _arc(pts)
    flare = R * (1 + 0.3 * np.exp(-s / (0.5 * R)))
    up = np.interp(s - H, _arc(lead), lead_r, left=lead_r[0])
    w = T.smoothstep(H - 0.5, H + 0.6, s)                      # the bole narrows into the leader
    radii = flare * (1 - w) + up * w
    return Branch(pts, radii, 0, twist=0.35), lean_az


def _limbs(trunk, lean_az, rng, seed):
    """Heavy limbs: most leave the trunk low and spread, sagging and then rising at their ends
    (refs/03); one more climbs beside the leader to carry the top of the dome. Each forks once."""
    H, R = L.OAK_FORK, L.OAK_GIRTH / 2
    n = 6
    limbs, sockets = [], []
    for k in range(n):
        az = lean_az + 2 * math.pi * (k + 0.5) / n + rng.uniform(-0.25, 0.25)
        rising = k == 2
        if rising:
            h = rng.uniform(0.95, 1.05) * H
            prof = _profile(rng.uniform(52, 62), rng.uniform(40, 50), rng.uniform(58, 70))
            length, r0 = rng.uniform(3.2, 3.7), rng.uniform(0.45, 0.5) * R
        else:
            h = rng.uniform(0.6, 0.92) * H
            prof = _profile(rng.uniform(14, 28), rng.uniform(-2, 8), rng.uniform(30, 46))
            length, r0 = rng.uniform(3.6, 4.2), rng.uniform(0.40, 0.48) * R
        start, _ = _at(trunk, h)
        pts, radii = _grow(start, az, prof, length, r0, 0.05, seed + 31 * k)
        limbs.append(Branch(pts, radii, 1, twist=0.25, exit=_exit(pts, trunk)))
        sockets.append((az, h, r0))
        j = int(len(pts) * rng.uniform(0.35, 0.55))           # a fork: a second limb off this one
        side = rng.choice((-1, 1))
        sub_prof = _profile(rng.uniform(28, 42), rng.uniform(12, 24), rng.uniform(40, 58))
        sp, sr = _grow(pts[j], az + side * math.radians(rng.uniform(32, 52)), sub_prof,
                       rng.uniform(1.9, 2.6), 0.62 * radii[j], 0.045, seed + 31 * k + 17)
        limbs.append(Branch(sp, sr, 1, twist=0.25, exit=_exit(sp, limbs[-1])))
    return limbs, sockets


def _clumps(base, g0, rng):
    """Leaf clump centres and radii: an outer layer over a dome (Poisson-disc), its rim hanging a
    little lower than its underside, which rises toward the trunk so the limbs show beneath it
    (refs/09, 10); a clump on top; and a sparser inner layer, so a gap shows foliage behind it."""
    A = L.OAK_CROWN / 2
    top = g0 + L.OAK_HEIGHT
    rim = g0 + 0.4 * L.OAK_HEIGHT
    cx, cy = base[0], base[1] - 0.25              # the crown leans a little out over the door

    def dome(e, phi, inset):
        rho = (A - inset) * math.cos(e)
        z = rim + (top - rim - inset) * math.sin(e) * (0.6 if e < 0 else 1.0)
        return np.array([cx + rho * math.cos(phi), cy + rho * math.sin(phi), z])

    r_top = 0.95
    pts, radii = [dome(math.pi / 2, 0.0, 0.7 * r_top)], [r_top]
    for layer, (n_try, gap, inset0, inset1) in enumerate(((4000, 1.12, 0.0, 0.5), (1500, 1.5, 1.1, 1.6))):
        for _ in range(n_try):
            e = math.asin(rng.uniform(-0.25 if layer == 0 else 0.1, 1.0))    # even over the dome
            r = rng.uniform(0.6, 0.95)
            c = dome(e, rng.uniform(0, 2 * math.pi), 0.7 * r + rng.uniform(inset0, inset1))
            if np.min(np.linalg.norm(np.array(pts) - c, axis=1)) > gap:
                pts.append(c)
                radii.append(r)
    keep = [i for i in range(len(pts)) if rng.random() > 0.07 or pts[i][2] > top - 1.5]   # a few gaps
    return np.array(pts)[keep], np.array(radii)[keep]


def _colonize(limbs, centres, radii, rng, step=0.16, reach=2.6, kill=0.3, iters=100):
    """Space colonization: branches grow from the limbs toward clouds of points, one per clump.
    Returns node positions, parents (-1 for a limb point) and, for limb points, (limb, index)."""
    att = []
    for c, r in zip(centres, radii):
        n = int(8 + 12 * r)
        att.append(c + rng.normal(0.0, 0.4 * r, (n, 3)) * np.array([1.0, 1.0, 0.75]))
    att = np.concatenate(att)
    R = L.OAK_GIRTH / 2
    nodes, parent, seat = [], [], []
    for li, lb in enumerate(limbs):                    # branches leave the outer limbs only
        s = _arc(lb.pts)
        for i in list(range(0, len(lb.pts) - 1, 5)) + [len(lb.pts) - 1]:
            if s[i] > max(1.3 * R, 0.45 * s[-1]):
                nodes.append(lb.pts[i])
                parent.append(-1)
                seat.append((li, i))
    kids = [0] * len(nodes)
    for _ in range(iters):
        if len(att) == 0:
            break
        Pn = np.array(nodes)
        d2 = (att ** 2).sum(1)[:, None] + (Pn ** 2).sum(1)[None, :] - 2 * att @ Pn.T
        near = d2.argmin(1)
        dist = np.sqrt(np.maximum(d2[np.arange(len(att)), near], 0.0))
        live = dist < reach
        if not live.any():
            break
        pull = {}
        for a in np.nonzero(live)[0]:
            v = att[a] - Pn[near[a]]
            pull.setdefault(int(near[a]), []).append(v / (np.linalg.norm(v) + 1e-9))
        grew = False
        for node, dirs in sorted(pull.items()):
            if kids[node] >= 3:
                continue
            d = np.sum(dirs, axis=0)
            d = d / (np.linalg.norm(d) + 1e-9) + np.array([0.0, 0.0, 0.18]) + rng.normal(0.0, 0.12, 3)
            nodes.append(Pn[node] + d / np.linalg.norm(d) * step)
            parent.append(node)
            seat.append(None)
            kids.append(0)
            kids[node] += 1
            grew = True
        if not grew:
            break
        Pn = np.array(nodes)
        d2 = (att ** 2).sum(1)[:, None] + (Pn ** 2).sum(1)[None, :] - 2 * att @ Pn.T
        att = att[np.sqrt(np.maximum(d2.min(1), 0.0)) > kill]
    return np.array(nodes), np.array(parent), seat


def _fair(path, rad, ratio=2.2, passes=12):
    """Smooth a branch's path (ends fixed) until it bends no tighter than `ratio` times its
    radius; _tube's untangle makes sure of the rest."""
    path = np.array(path, dtype=float)
    for _ in range(passes):
        v = np.diff(path, axis=0)
        ln = np.linalg.norm(v, axis=1)
        c = np.einsum("ij,ij->i", v[:-1], v[1:]) / (ln[:-1] * ln[1:] + 1e-12)
        ang = np.arccos(np.clip(c, -1.0, 1.0))
        bend = np.minimum(ln[:-1], ln[1:]) / (2 * np.sin(ang / 2) + 1e-12)
        if len(path) < 3 or np.all(bend >= ratio * rad[1:-1]):
            break
        path = T.smooth_path(path, passes=1)
    return path


def _branches(limbs, nodes, parent, seat, gamma=2.0):
    """Chains of grown nodes made into branches, as thick as the twigs they carry (pipe model),
    never thinner than OAK_TWIG; and the tips."""
    r_tip = L.OAK_TWIG / 2
    n = len(nodes)
    kids = [[] for _ in range(n)]
    for i, p in enumerate(parent):
        if p >= 0:
            kids[p].append(i)
    r = np.zeros(n)
    for i in range(n - 1, -1, -1):           # children always come after their parents
        if parent[i] < 0:
            continue
        r[i] = r_tip if not kids[i] else max(r_tip, sum(r[c] ** gamma for c in kids[i]) ** (1 / gamma))
    carried = {}                               # the limbs grow as thick as the branches they carry
    for i in range(n):
        if parent[i] < 0 and kids[i]:
            li, k = seat[i]
            carried.setdefault(li, []).append((k, sum(r[c] ** gamma for c in kids[i])))
    for li, load in carried.items():
        lb = limbs[li]
        acc = np.zeros(len(lb.radii))
        for k, a in load:
            acc[:k + 1] += a
        lb.radii = np.maximum(lb.radii, 1.05 * acc ** (1 / gamma))
        if lb.level > 0:
            lb.pts = _fair(lb.pts, lb.radii, ratio=2.0)
    out, tips = [], []
    starts = []                                # (first node, base point, cap on the radius, level)
    for i in range(n):
        if parent[i] < 0:
            li, k = seat[i]
            for c in kids[i]:
                starts.append((c, nodes[i], max(r_tip, 0.62 * limbs[li].radii[k]), 2, limbs[li].radii[k]))
    while starts:
        first, base, cap, level, r_parent = starts.pop(0)
        path, rad = [base], [max(r_tip, min(r[first], cap))]
        i = first
        while True:
            path.append(nodes[i])
            rad.append(max(r_tip, min(r[i], cap)))
            if not kids[i]:
                tips.append(nodes[i])
                break
            main = max(kids[i], key=lambda c: r[c])
            for c in kids[i]:
                if c != main:
                    starts.append((c, nodes[i], max(r_tip, 0.7 * min(r[i], cap)), level + 1, min(r[i], cap)))
            i = main
        rad = np.array(rad)
        out.append(Branch(_fair(path, rad), rad, level, twist=0.2, exit=1.2 * r_parent))
    return out, np.array(tips)


# ---------------------------------------------------------------- bark and wood

def _bark_scale(r):
    """Oak bark for wood of radius r: ridge spacing across, ridge length along, furrow depth (m)."""
    rr = np.minimum(r, 0.6)
    w = 0.03 + 0.11 * rr
    depth = (0.012 + 0.03 * rr) * T.smoothstep(0.05, 0.12, r)   # none on twigs: it would not print
    return w, 3.5 * w, depth


def _grain(r):
    """Mesh spacing around and along wood of radius r: fine enough for the bark's furrows on old
    wood, coarser on the branches."""
    w, l, depth = _bark_scale(r)
    fine = T.smoothstep(0.1, 0.3, r)
    around = np.where(depth > 0.004, w / (4.0 + 2.0 * fine), 0.018)
    along = np.where(depth > 0.004, l / (3.5 + 1.5 * fine), 0.045)
    return np.clip(around, 0.007, 0.02), np.clip(along, 0.016, 0.045)


def _bark(nz, theta, s, r, twist, off):
    """Radial bark relief (<= 0): long ridges between a network of furrows that run along the
    wood, splitting and joining (the zero lines of stretched gradient noise), broken across into
    plates here and there (Worley cell ends), the ridges rounded over."""
    w, l, depth = _bark_scale(r)
    a = theta + twist * s
    q = np.stack([np.cos(a) * r / w, np.sin(a) * r / w, s / l + off], axis=1)
    n = nz.perlin(q) + 0.35 * nz.perlin(q * 2.1 + 13.7)
    furrow = 1.0 - T.smoothstep(0.0, 0.3, np.abs(n))
    ridge = 1.0 - T.smoothstep(0.0, 0.7, np.abs(n))          # ridges rounded over
    f1, f2 = nz.worley(q * np.array([0.6, 0.6, 1.4]) + 5.3)
    breaks = 1.0 - T.smoothstep(0.0, 0.18, f2 - f1)
    return -depth * np.maximum(np.maximum(furrow, 0.75 * breaks), 0.3 * ridge)


def _resample_by_radius(br):
    """Path points spaced to the bark's plate length (closer on thin wood), with radii."""
    pts, rad = br.pts, br.radii
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    out = [0.0]
    while out[-1] < s[-1]:
        step = float(_grain(float(np.interp(out[-1], s, rad)))[1])
        out.append(min(s[-1], out[-1] + step))
    t = np.array(out)
    if t[-1] - t[-2] < 1e-4:
        t = t[:-1]
    P_ = np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], axis=1)
    return P_, np.interp(t, s, rad), t


def _tube(md, br, nz, seed, shape=None, collar=0.0, ground_fn=None):
    """Make one branch into a closed tube with bark. shape(theta, ring, s, dirs) is a factor on
    the radius (lobes, burrs); collar swells the base where it leaves its parent."""
    P_, rad, s = _resample_by_radius(br)
    if len(P_) < 3:
        return True
    if collar:                       # a swelling where it comes out of its parent, fading outward
        r0 = float(br.radii[0])
        rad = rad * (1 + collar * np.exp(-np.maximum(s - br.exit, 0.0) / (1.2 * r0)))
    gnarl = 0.08 if br.level <= 1 else 0.06                  # burrs and twists on the wood
    reach = rad * (1 + gnarl) * (1.6 if shape is not None else 1.0)
    P_, (Tn, N, B), ok = T.untangle(P_, reach)               # rings never cross: a clean solid
    s = _arc(P_)
    da = _grain(rad)[0]
    shape_max = np.ones(len(rad))
    if shape is not None:                          # how far the lobes reach out, ring by ring
        m = 64
        th = np.tile(np.linspace(0, 2 * np.pi, m, endpoint=False), len(rad))
        rg = np.repeat(np.arange(len(rad)), m)
        dd = N[rg] * np.cos(th)[:, None] + B[rg] * np.sin(th)[:, None]
        shape_max = shape(th, rg, s, dd).reshape(-1, m).max(axis=1)
    sizes = T.ring_sizes(2 * np.pi * rad * shape_max / da, minimum=8)
    theta, ring = T.ring_angles(sizes)
    r = rad[ring]
    dirs = N[ring] * np.cos(theta)[:, None] + B[ring] * np.sin(theta)[:, None]
    rho = r * (1.0 + gnarl * nz.fbm(np.stack([np.cos(theta) * r, np.sin(theta) * r, s[ring]], 1) * 2.2 + seed))
    if shape is not None:
        rho = rho * shape(theta, ring, s, dirs)
    verts = P_[ring] + dirs * rho[:, None]
    along = s[ring]
    if ground_fn is not None:                      # the bark follows the drape onto the turf...
        along = along + ground_fn(verts.copy(), ring, s)[:, 2] - verts[:, 2]
    if _bark_scale(rad)[2].max() > 0.0:            # twigs carry no bark (it would not print)
        bark = np.maximum(_bark(nz, theta, along, r, br.twist, seed * 3.7), 0.5 * r - rho)
        verts = verts + dirs * bark[:, None]
    if ground_fn is not None:                      # ...and the drape is made where the bark put it
        verts = ground_fn(verts, ring, s)
    faces, extra = T.tube_faces(sizes)
    tip = P_[-1] + Tn[-1] * (1.2 * rad[-1] + 0.01)          # a tapered end, not a blunt one
    md.add(np.concatenate([verts, [P_[0], tip]]), faces)
    return ok


def _trunk_mesh(md, trunk, roots_az, sockets, nz, g0):
    """The trunk: lobed toward its roots near the turf (buttresses) and burred; its lowest rings
    drape down over the hump of the turf so the base sits on it."""
    R = L.OAK_GIRTH / 2

    def shape(theta, ring, s, dirs):
        h = s[ring]
        world_az = np.arctan2(dirs[:, 1], dirs[:, 0])
        roots = np.zeros_like(theta)
        for k, (az, size) in enumerate(roots_az):      # buttress fins run down into the roots
            roots = np.maximum(roots, 0.75 * size * np.maximum(np.cos(world_az - az), 0.0) ** 8)
        limbs = np.zeros_like(theta)
        for az, hl, rl in sockets:                     # the trunk swells up into each limb
            fall = np.where(h < hl, np.exp(-((h - hl) / 0.45) ** 2), np.exp(-((h - hl) / 0.3) ** 2))
            limbs += 0.6 * (rl / R) * fall * np.maximum(np.cos(world_az - az), 0.0) ** 8
        burl = 0.06 * nz.fbm(np.stack([np.cos(theta) * 1.4, np.sin(theta) * 1.4, h * 1.6], 1) + 11.0)
        return 1.0 + roots * np.exp(-h / (0.85 * R)) + limbs + burl

    def drape(verts, ring, s):
        h = s[ring]
        g = ground(verts[:, 0], verts[:, 1]) - L.OAK_SEAT
        blend = T.smoothstep(0.0, 0.45, h)
        verts[:, 2] = (g + h) * (1 - blend) + verts[:, 2] * blend
        return verts

    return _tube(md, trunk, nz, 5.0, shape=shape, ground_fn=drape)


def _root(md, base, az, length, width, height, nz, seed, g0):
    """A surface root: a half-round ridge lying on the turf, running out from the trunk. It stops
    short where the turf falls away (the oak stands on a narrow rise), so the base sits on it."""
    n = max(4, int(length / 0.04))
    ts = np.linspace(0.0, 1.0, n)
    a = az + 0.35 * np.array([noise.noise(Vector((t * 1.8, seed, 2.0))) for t in ts])
    step = length / (n - 1)
    xy = np.cumsum(np.stack([np.cos(a), np.sin(a)], 1) * step, axis=0) - np.array([math.cos(az), math.sin(az)]) * step
    xy = xy + np.array(base[:2]) + np.array([math.cos(az), math.sin(az)]) * 0.25 * L.OAK_GIRTH / 2
    g = ground(xy[:, 0], xy[:, 1])
    slope = np.abs(np.diff(g, prepend=g[0])) / step
    low = np.nonzero((g < g0 - 1.0) | (slope > 1.1))[0]
    if len(low):
        n = max(8, int(low[0] * 0.9))
        length = length * (n - 1) / (len(ts) - 1)
        xy, ts = xy[:n], np.linspace(0.0, 1.0, n)
    tan = np.gradient(xy, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    side = np.stack([-tan[:, 1], tan[:, 0]], 1)
    tip = T.smoothstep(1.0, 0.75, ts)                         # the end narrows to a point
    wid = (width * (1 - 0.6 * ts) + 0.03) * (0.4 + 0.6 * tip)     # a tall ridge by the trunk, diving
    hgt = height * (1 - ts) ** 0.9 + 0.035                        # under the turf, still 0.4 mm at HO
    m_arc, m_flat = 28, 6
    rings = []
    for i in range(n):
        phi = np.linspace(0.0, np.pi, m_arc)                    # over the top, from one side to the other
        u = wid[i] * np.cos(phi)
        v = hgt[i] * np.sin(phi) ** 0.8
        uf = np.linspace(-wid[i], wid[i], m_flat + 2)[1:-1]      # back along the underside
        u = np.concatenate([u, uf])
        v = np.concatenate([v, np.zeros(m_flat)])
        rings.append((u, v))
    sizes = np.full(n, m_arc + m_flat)
    U = np.concatenate([u for u, _ in rings])
    V = np.concatenate([v for _, v in rings])
    ring = np.repeat(np.arange(n), m_arc + m_flat)
    s = ts[ring] * length
    r_eff = np.maximum(0.5 * (wid[ring] + hgt[ring]), 0.03)
    theta = np.arctan2(V, U)
    bark = _bark(nz, theta, s, r_eff, 0.1, seed * 2.3) * T.smoothstep(0.0, 0.06, V)
    f = np.maximum(1.0 + bark / r_eff, 0.6)                    # bark cut in toward the root's core
    U, V = U * f, V * f
    x = xy[ring, 0] + side[ring, 0] * U
    y = xy[ring, 1] + side[ring, 1] * U
    z = ground(x, y) - L.OAK_SEAT + V                          # the underside lies on the turf
    verts = np.stack([x, y, z], 1)
    # each ring runs from the root's left side over the top and back along its underside:
    # counter-clockwise looking outward, as tube_faces wants
    faces, _ = T.tube_faces(sizes)                             # a fan inside the trunk, a point at the end
    end = np.append(xy[-1] + (xy[-1] - xy[-2]) * 1.5, 0.0)
    end[2] = float(ground(end[0], end[1])) - L.OAK_SEAT + 0.005
    start = np.append(xy[0], float(ground(*xy[0])) + 0.3 * hgt[0])
    md.add(np.concatenate([verts, [start, end]]), faces)


def _peg(md, base, g0):
    """A keyed peg under the trunk (round with one flat) that plugs into a socket in the hill."""
    dia, depth = L.OAK_PEG
    rp = dia / 2
    flat = 0.6 * rp
    pts = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        x, y = rp * math.cos(t), rp * math.sin(t)
        pts.append((x, min(y, flat)))
    out = np.array(pts)
    inset = out * (1 - 0.05 / rp)
    z_top, z_bot = g0 + 0.35, g0 - L.OAK_SEAT - depth
    levels = [(inset, z_bot), (out, z_bot + 0.05), (out, z_top)]
    verts = np.concatenate([np.column_stack([o + base[:2], np.full(len(o), z)]) for o, z in levels])
    m = len(out)
    faces = [np.arange(m)[::-1][None, :]]                      # bottom, facing down
    for k in range(2):
        j = np.arange(m)
        faces.append(np.stack([k * m + j, k * m + (j + 1) % m, (k + 1) * m + (j + 1) % m, (k + 1) * m + j], 1))
    faces.append((2 * m + np.arange(m))[None, :])              # top, inside the trunk
    md.add(verts, faces)


# ---------------------------------------------------------------- foliage

def _sphere(subdivisions):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    v = np.array([x.co[:] for x in bm.verts])
    f = np.array([[x.index for x in face.verts] for face in bm.faces])
    bm.free()
    return v, f


def _foliage(centres, radii, branches, rng, nz):
    """Each clump: a core and many knobbly leaf clusters crowded over it, more on top than
    beneath, and more clusters along the twigs that carry it; all voxel-remeshed into one closed
    surface (no hidden faces, no self-crossing) whose knobs take flock and drybrushing."""
    cores, leaves = [], []
    for c, r in zip(centres, radii):
        cores.append((c + np.array([0.0, 0.0, -0.1 * r]), 0.62 * r))
        for _ in range(int(16 + 26 * r)):
            d = rng.normal(0.0, 1.0, 3) + np.array([0.0, 0.0, 0.25])
            d /= np.linalg.norm(d)
            leaves.append((c + d * r * rng.uniform(0.45, 0.82) * np.array([1.0, 1.0, 0.85]),
                           rng.uniform(0.17, 0.27) * (0.65 + 0.45 * r)))
    for br in branches:
        if br.level < 2:
            continue
        s = _arc(br.pts)
        for i in range(1, len(br.pts)):
            if s[-1] - s[i] < 0.7 and rng.random() < 0.7:
                leaves.append((br.pts[i] + rng.normal(0.0, 0.06, 3), rng.uniform(0.16, 0.24)))
    md = T.MeshData()
    for k, (items, subdivisions, flat) in enumerate(((cores, 3, 0.8), (leaves, 2, 0.75))):
        tv, tf = _sphere(subdivisions)
        C = np.array([c for c, _ in items])
        Rr = np.array([r for _, r in items])
        nb, nv = len(items), len(tv)
        d = np.tile(tv, (nb, 1))
        blob = np.repeat(np.arange(nb), nv)
        lobe = 0.14 * nz.fbm(d * 1.4 + (blob * 3.1 + 500.0 * k)[:, None], octaves=2)   # lumpy, not round
        rr = np.repeat(Rr, nv) * (1.0 + lobe)
        squash = np.where(d[:, 2] < 0, flat, 1.0)                                     # flatter undersides
        verts = np.repeat(C, nv, axis=0) + d * np.stack([rr, rr, rr * squash], 1)
        md.add(verts, [(tf[None, :, :] + (np.arange(nb) * nv)[:, None, None]).reshape(-1, 3)])
    obj = md.to_object("oak_crown", P.materials()["leaves"], COLL)
    mod = obj.modifiers.new("remesh", "REMESH")
    mod.mode, mod.voxel_size, mod.adaptivity = "VOXEL", L.OAK_LEAF_VOXEL, 0.0
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    old = obj.data
    obj.data = mesh
    bpy.data.meshes.remove(old)
    mesh.name = "oak_crown"
    T.drop_specks(mesh)
    if not mesh.materials:
        mesh.materials.append(P.materials()["leaves"])
    mesh.shade_smooth()
    return obj


# ---------------------------------------------------------------- the oak

def skeleton(seed=71):
    """The oak's structure, as a dict: base, ground height g0, trunk, roots (azimuth, size),
    sockets where limbs leave the trunk, limbs, branches, tips, clump centres and radii, and the
    random generator to carry on with."""
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    x, y = L.OAK
    g0 = float(ground(x, y))
    base = np.array([x, y, g0 - L.OAK_SEAT])
    trunk, lean_az = _trunk(base, rng, seed)
    limbs, sockets = _limbs(trunk, lean_az, rng, seed)
    centres, radii = _clumps(base, g0, rng)
    nodes, parent, seat = _colonize([trunk] + limbs, centres, radii, nrng)
    branches, tips = _branches([trunk] + limbs, nodes, parent, seat)
    n_roots = 7
    az0 = rng.uniform(0, 2 * math.pi)
    roots_az = [(az0 + 2 * math.pi * k / n_roots + rng.uniform(-0.3, 0.3), rng.uniform(0.7, 1.1))
                for k in range(n_roots)]
    return dict(base=base, g0=g0, trunk=trunk, roots_az=roots_az, sockets=sockets, limbs=limbs, branches=branches,
                tips=tips, centres=centres, radii=radii, rng=rng)


def build(seed=71):
    """Build the oak into the `oak` collection: oak_trunk (the wood: shell 0 the trunk, then the
    roots, limbs and branches, the peg last; the mesh's "shell" attribute numbers them) and
    oak_crown (the foliage)."""
    sk = skeleton(seed)
    rng, base, g0 = sk["rng"], sk["base"], sk["g0"]
    nz = T.Noise(seed)
    md = T.MeshData()
    ok = [_trunk_mesh(md, sk["trunk"], sk["roots_az"], sk["sockets"], nz, g0)]
    R = L.OAK_GIRTH / 2
    for k, (az, size) in enumerate(sk["roots_az"]):
        _root(md, base, az, (1.2 + 0.7 * size) * rng.uniform(0.9, 1.1), 0.5 * size * R, 0.7 * size * R,
              nz, seed + 101 * k, g0)
    for k, lb in enumerate(sk["limbs"]):
        ok.append(_tube(md, lb, nz, 13.0 + k, collar=0.25))
    for k, br in enumerate(sk["branches"]):
        ok.append(_tube(md, br, nz, 50.0 + k, collar=0.25))
    _peg(md, base, g0)
    wood = md.to_object("oak_trunk", P.materials()["bark"], COLL)
    crown = _foliage(sk["centres"], sk["radii"], sk["branches"], np.random.default_rng(seed + 7), nz)
    return Oak(wood, crown, [sk["trunk"]] + sk["limbs"] + sk["branches"], sk["tips"], ok.count(False))

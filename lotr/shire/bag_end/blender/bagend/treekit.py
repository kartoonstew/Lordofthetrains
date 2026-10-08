"""Helpers for printable trees, in numpy: seeded lattice noise, tubes whose cross-sections are any
radial shape, and fast mesh assembly.

Every tube is its own closed shell: rings around a path (each ring a star-shaped outline round the
path, so it never crosses itself), quads between rings of equal size and a triangle zipper between
rings of different size, a flat fan closing its start and a pointed fan closing its end.
"""
import bmesh
import bpy
import numpy as np

from . import scene

OFFSETS = np.array([(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)], dtype=np.int64)
CORNERS = np.array([(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)], dtype=np.int64)


class Noise:
    """Seeded lattice noise over arrays of points (N, 3).

    The randomness is a table drawn from np.random.default_rng(seed), looked up through a
    permutation hash of the integer lattice (as in Perlin's noise), so it is repeatable and smooth
    across any number of separate calls.
    """

    def __init__(self, seed, size=512):
        rng = np.random.default_rng(seed)
        self.mask = size - 1
        self.perm = rng.permutation(size)
        self.points = rng.random((size, 3))            # one feature point per Worley cell
        self.values = rng.uniform(-1.0, 1.0, size)     # one value per lattice corner
        g = rng.normal(0.0, 1.0, (size, 3))
        self.grads = g / np.linalg.norm(g, axis=1, keepdims=True)   # one gradient per corner

    def _hash(self, cells):
        p, m = self.perm, self.mask
        return p[(p[(p[cells[:, 0] & m] + cells[:, 1]) & m] + cells[:, 2]) & m]

    def worley(self, pts):
        """Distances to the nearest and second-nearest cell points (F1, F2), in lattice units."""
        cell = np.floor(pts).astype(np.int64)
        frac = pts - cell
        f1 = np.full(len(pts), 1e9)
        f2 = np.full(len(pts), 1e9)
        for off in OFFSETS:
            d = off + self.points[self._hash(cell + off)] - frac
            dd = np.einsum("ij,ij->i", d, d)
            f2 = np.minimum(f2, np.maximum(f1, dd))
            f1 = np.minimum(f1, dd)
        return np.sqrt(f1), np.sqrt(f2)

    def smooth(self, pts):
        """Smooth value noise in [-1, 1]."""
        cell = np.floor(pts).astype(np.int64)
        f = pts - cell
        u = f * f * (3.0 - 2.0 * f)
        out = np.zeros(len(pts))
        for c in CORNERS:
            w = np.prod(np.where(c == 1, u, 1.0 - u), axis=1)
            out += w * self.values[self._hash(cell + c)]
        return out

    def perlin(self, pts):
        """Gradient noise, about [-1, 1], zero on every lattice point: its zero set is a network of
        smooth lines/sheets, good for furrows."""
        cell = np.floor(pts).astype(np.int64)
        f = pts - cell
        u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0)
        out = np.zeros(len(pts))
        for c in CORNERS:
            w = np.prod(np.where(c == 1, u, 1.0 - u), axis=1)
            g = self.grads[self._hash(cell + c)]
            out += w * np.einsum("ij,ij->i", g, f - c)
        return out * 1.6

    def fbm(self, pts, octaves=3):
        out, amp, norm = np.zeros(len(pts)), 1.0, 0.0
        for k in range(octaves):
            out += amp * self.smooth(pts * (2.0 ** k) + 17.3 * k)
            norm += amp
            amp *= 0.5
        return out / norm


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def resample(pts, step):
    """Points along a polyline at even arc-length spacing (about `step`), ends kept."""
    pts = np.asarray(pts, dtype=float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(2, int(round(s[-1] / step)) + 1)
    t = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], axis=1), t


def smooth_path(pts, passes=2):
    """Soften the kinks of a polyline (ends fixed)."""
    pts = np.array(pts, dtype=float)
    for _ in range(passes):
        if len(pts) < 3:
            break
        pts[1:-1] = 0.25 * pts[:-2] + 0.5 * pts[1:-1] + 0.25 * pts[2:]
    return pts


def frames(pts):
    """Parallel-transport frames along a path: unit tangents T, normals N and binormals B."""
    T = np.gradient(pts, axis=0)
    T = unit(T)
    N = np.empty_like(T)
    ref = np.array([0.0, 0.0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    n = np.cross(T[0], ref)
    N[0] = n / np.linalg.norm(n)
    for i in range(1, len(T)):
        n = N[i - 1] - np.dot(N[i - 1], T[i]) * T[i]
        N[i] = n / np.linalg.norm(n)
    B = np.cross(T, N)
    return T, N, B


def untangle(pts, reach, passes=60):
    """Smooth a densely sampled path (ends fixed) until no ring crosses the next: each ring, of
    radius up to reach[k] round pts[k] square to the path, must lie wholly behind the next ring's
    plane and the next wholly in front of its own. Returns the path and its frames."""
    pts = np.array(pts, dtype=float)
    for _ in range(passes + 1):
        Tn, N, B = frames(pts)
        d = np.diff(pts, axis=0)
        sin = np.linalg.norm(np.cross(Tn[:-1], Tn[1:]), axis=1)
        ahead = np.einsum("ij,ij->i", d, Tn[1:]) - reach[:-1] * sin       # ring k behind plane k+1
        behind = np.einsum("ij,ij->i", d, Tn[:-1]) - reach[1:] * sin      # ring k+1 ahead of plane k
        if len(pts) < 3 or (ahead.min() > 0.0 and behind.min() > 0.0):
            return pts, (Tn, N, B), True
        pts[1:-1] = 0.25 * pts[:-2] + 0.5 * pts[1:-1] + 0.25 * pts[2:]
    return pts, (Tn, N, B), False


def islands(mesh):
    """A label per vertex: which connected piece of the mesh it is on (hook-and-compress
    union-find over the edges, vectorised)."""
    lab = np.arange(len(mesh.vertices))
    ed = np.empty(2 * len(mesh.edges), dtype=np.int64)
    mesh.edges.foreach_get("vertices", ed)
    a, b = ed[0::2], ed[1::2]
    while True:
        la, lb = lab[a], lab[b]
        diff = la != lb
        if not diff.any():
            return lab
        lab[np.maximum(la[diff], lb[diff])] = np.minimum(la[diff], lb[diff])
        while True:
            nxt = lab[lab]
            if np.array_equal(nxt, lab):
                break
            lab = nxt


def drop_specks(mesh, min_verts=60):
    """Delete the tiny pieces a voxel remesh can leave (single-voxel specks, sealed bubbles)."""
    lab = islands(mesh)
    roots, counts = np.unique(lab, return_counts=True)
    small = set(roots[counts < min_verts].tolist())
    if not small:
        return 0
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(np.isin(lab, list(small)))[0]], context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    return len(small)


class MeshData:
    """Vertices and faces gathered from many shells, then made into one mesh in a few calls."""

    def __init__(self):
        self.verts, self.loops, self.sizes, self.shells = [], [], [], []
        self.count = 0

    def add(self, verts, faces):
        """Add a shell: verts (n, 3) and faces as a list of index arrays (local to verts)."""
        for f in faces:
            f = np.asarray(f, dtype=np.int64)
            if f.ndim == 1:
                f = f[None, :]
            self.loops.append((f + self.count).ravel())
            self.sizes.append(np.full(len(f), f.shape[1], dtype=np.int64))
        self.verts.append(np.asarray(verts, dtype=float))
        self.shells.append(np.full(len(verts), len(self.shells), dtype=np.int32))
        self.count += len(verts)

    def to_object(self, name, mat, coll):
        verts = np.concatenate(self.verts)
        loops = np.concatenate(self.loops).astype(np.int32)
        sizes = np.concatenate(self.sizes)
        starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", verts.ravel())
        mesh.loops.add(len(loops))
        mesh.loops.foreach_set("vertex_index", loops)
        mesh.polygons.add(len(sizes))
        mesh.polygons.foreach_set("loop_start", starts)
        mesh.update(calc_edges=True)
        shell = mesh.attributes.new("shell", "INT", "POINT")      # which closed shell each vertex is on
        shell.data.foreach_set("value", np.concatenate(self.shells))
        obj = bpy.data.objects.new(name, mesh)
        scene.collection(coll).objects.link(obj)
        if mat is not None:
            mesh.materials.append(mat)
        return obj


def tube_faces(sizes, start_cap=True, end_cap=True):
    """Faces for rings of the given sizes laid end to end (ring k's vertices follow ring k-1's), each
    ring counter-clockwise looking along the path. A start-cap centre vertex and an end apex vertex
    come after the rings. Returns (faces, number of extra vertices)."""
    offs = np.concatenate([[0], np.cumsum(sizes)])
    faces = []
    for k in range(len(sizes) - 1):
        a0, na, b0, nb = offs[k], sizes[k], offs[k + 1], sizes[k + 1]
        if na == nb:
            j = np.arange(na)
            faces.append(np.stack([a0 + j, a0 + (j + 1) % na, b0 + (j + 1) % nb, b0 + j], axis=1))
        else:                                      # zip two rings of different size with triangles
            tris, i, j = [], 0, 0
            while i < na or j < nb:
                if j == nb or (i < na and (i + 1) / na < (j + 1) / nb):
                    tris.append((a0 + i, a0 + (i + 1) % na, b0 + j % nb))
                    i += 1
                else:
                    tris.append((a0 + i % na, b0 + (j + 1) % nb, b0 + j))
                    j += 1
            faces.append(np.array(tris))
    extra, total = 0, offs[-1]
    if start_cap:
        n = sizes[0]
        j = np.arange(n)
        faces.append(np.stack([np.full(n, total), (j + 1) % n, j], axis=1))
        extra += 1
    if end_cap:
        n, b0 = sizes[-1], offs[-2]
        j = np.arange(n)
        faces.append(np.stack([b0 + j, b0 + (j + 1) % n, np.full(n, total + extra)], axis=1))
        extra += 1
    return faces, extra


def ring_angles(sizes):
    """The angle of every ring vertex, and the ring each belongs to."""
    ring = np.repeat(np.arange(len(sizes)), sizes)
    start = np.repeat(np.concatenate([[0], np.cumsum(sizes)[:-1]]), sizes)
    idx = np.arange(len(ring)) - start
    return 2.0 * np.pi * idx / np.repeat(sizes, sizes), ring


def ring_sizes(targets, minimum=6, change=0.18):
    """Vertices per ring: follow the wanted counts, but change only when off by more than `change`,
    so most of a tube is plain quads."""
    out, cur = [], None
    for t in targets:
        t = max(minimum, int(round(t)))
        if cur is None or abs(t - cur) > change * cur:
            cur = t
        out.append(cur)
    return np.array(out, dtype=np.int64)

"""Rustic building parts for the Bag End fronts.

Everything is built in a front-local frame: u along the facade, v into the wall (the viewer is
at -v), z up. Irregularity is real geometry: jittered corners, noise-bent timber, bowed boards,
wavy plaster, so the printed part looks hand-built rather than machined.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

from . import scene

# Base colours (linear RGB), shared with render.py so block-out parts match the detailed ones.
PLASTER = (0.62, 0.42, 0.13)
BRICK = (0.30, 0.085, 0.045)
STONE = (0.25, 0.24, 0.22)
TURF = (0.06, 0.14, 0.03)


# ---------------------------------------------------------------- materials (renders only)

def materials():
    """Render materials by name, made once per scene: per-island colour variation and fine bump."""
    def mat(name, colour, rough=0.85, metal=0.0, vary=0.0, bump=0.0, bump_scale=40.0):
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        m = bpy.data.materials.new(name)
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if vary:
            geo = nt.nodes.new("ShaderNodeNewGeometry")
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = (*[c * (1 - vary) for c in colour], 1)
            ramp.color_ramp.elements[1].color = (*[min(1.0, c * (1 + vary)) for c in colour], 1)
            nt.links.new(geo.outputs["Random Per Island"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        else:
            b.inputs["Base Color"].default_value = (*colour, 1)
        if bump:
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.inputs["Scale"].default_value = bump_scale
            bmp = nt.nodes.new("ShaderNodeBump")
            bmp.inputs["Strength"].default_value = bump
            nt.links.new(tex.outputs["Fac"], bmp.inputs["Height"])
            nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])
        return m
    return {
        "plaster": mat("plaster", PLASTER, bump=0.3),
        "brick": mat("brick", BRICK, vary=0.4, bump=0.2),
        "timber": mat("timber", (0.075, 0.05, 0.032), vary=0.3, bump=0.15, bump_scale=90.0),
        "ring": mat("ring", (0.20, 0.19, 0.17), rough=0.9, vary=0.15, bump=0.15, bump_scale=90.0),
        "door": mat("door", (0.012, 0.16, 0.075), rough=0.6, vary=0.25, bump=0.1, bump_scale=120.0),
        "iron": mat("iron", (0.03, 0.03, 0.03), rough=0.5, metal=0.7),
        "brass": mat("brass", (0.80, 0.58, 0.20), rough=0.3, metal=1.0),
        "glass": mat("glass", (0.02, 0.03, 0.04), rough=0.05),
        "green_paint": mat("green_paint", (0.015, 0.14, 0.07), rough=0.55, bump=0.1),
        "stone": mat("stone", STONE, vary=0.15, bump=0.4),
        "terracotta": mat("terracotta", (0.40, 0.14, 0.06), rough=0.8),
        "turf": mat("turf", TURF, rough=0.95, bump=0.4),
    }


# ---------------------------------------------------------------- mesh plumbing

def to_object(name, bm, mat, coll, matrix=None, bevel=0.0, segments=2):
    """Finish a bmesh into an object: bevel its sharp edges, fix normals, link it."""
    if bevel:
        bevel_sharp(bm, bevel, segments)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection(coll).objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    if matrix is not None:
        obj.matrix_world = matrix
    return obj


def bevel_sharp(bm, offset, segments=2, angle=0.6):
    """Round off only the real edges (faces meeting at more than ~35 degrees)."""
    bm.normal_update()      # faces made with bm.faces.new have no normals yet, so no angle either
    edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0.0) > angle]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=offset, segments=segments, profile=0.5,
                        affect="EDGES", clamp_overlap=True)


def wobble(verts, amp, scale, seed):
    """Smooth random displacement: bends long parts and waves edges, like hand-cut work."""
    o = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    for v in verts:
        p = v.co * scale + o
        v.co += Vector((noise.noise(p), noise.noise(p + Vector((31.7, 0, 0))),
                        noise.noise(p + Vector((0, 57.1, 0))))) * amp


def new_verts(bm, build):
    """Run build(bm) and return the vertices it added."""
    before = set(bm.verts)
    build(bm)
    return [v for v in bm.verts if v not in before]


def hexa(bm, front, back):
    vs = [bm.verts.new(p) for p in list(front) + list(back)]
    for q in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in q])
    return vs


def box(bm, centre, size, rot=None):
    m = Matrix.Translation(centre) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*size, 1.0))
    return bmesh.ops.create_cube(bm, size=1.0, matrix=m)["verts"]


def timber(bm, centre, size, rot=None, amp=0.008, seed=0, cuts=6):
    """A box subdivided along its length and gently bent, for posts, beams and planks."""
    def build(b):
        vs = box(b, centre, size, rot)
        longest = max(size)
        long_edges = list({e for v in vs for e in v.link_edges
                           if (e.verts[0].co - e.verts[1].co).length > 0.6 * longest})
        bmesh.ops.subdivide_edges(b, edges=long_edges, cuts=cuts, use_grid_fill=True)
    wobble(new_verts(bm, build), amp, 2.5, seed)


def extrude(bm, outline, v0, v1):
    """Prism from a closed (u, z) outline, between v0 and v1."""
    front = [bm.verts.new((u, v0, z)) for u, z in outline]
    back = [bm.verts.new((u, v1, z)) for u, z in outline]
    n = len(outline)
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    return front + back


def disc(bm, cu, cz, r, v0, v1, seg=48):
    return bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=v1 - v0,
                                 matrix=Matrix.Translation((cu, (v0 + v1) / 2, cz))
                                 @ Matrix.Rotation(math.pi / 2, 4, "X"))["verts"]


def arc_block(bm, cu, cz, r0, r1, a0, a1, v0, v1, seg=8):
    """A curved block: the part of an annulus between angles a0 and a1, from v0 to v1."""
    pts_in = [(cu + r0 * math.cos(a), cz + r0 * math.sin(a)) for a in
              [a0 + (a1 - a0) * i / seg for i in range(seg + 1)]]
    pts_out = [(cu + r1 * math.cos(a), cz + r1 * math.sin(a)) for a in
               [a1 - (a1 - a0) * i / seg for i in range(seg + 1)]]
    return extrude(bm, pts_in + pts_out, v0, v1)


def bake_cuts(obj, cutters):
    """Boolean-subtract throw-away cutter objects from obj and bake the result."""
    for c in cutters:
        mod = obj.modifiers.new("cut", "BOOLEAN")
        mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", c
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    old = obj.data
    name = old.name
    obj.data = mesh
    bpy.data.meshes.remove(old)
    mesh.name = name
    for c in cutters:
        data = c.data
        bpy.data.objects.remove(c)
        bpy.data.meshes.remove(data)


def cylinder_cutter(cu, cz, r, v0, v1, coll, matrix=None):
    bm = bmesh.new()
    disc(bm, cu, cz, r, v0, v1, seg=96)
    obj = to_object("cutter", bm, None, coll, matrix)
    obj.hide_render = True
    return obj


# ---------------------------------------------------------------- parts

def plaster_slab(bm, u0, u1, z0, top, depth, seed, step=0.03, amp=0.012):
    """Wall mass whose face is hand-plastered: a fine grid bulging outward in soft waves.

    The grid's top row follows top(u), so the slab meets the eave line exactly.
    """
    nu = max(2, round((u1 - u0) / step))
    us = [u0 + (u1 - u0) * i / nu for i in range(nu + 1)]
    nz = max(2, round((max(top(u) for u in us) - z0) / step))
    o = Vector((seed * 5.3, 0.0, seed * 2.1))

    def bulge(u, z):
        p = Vector((u, 0.0, z))
        return amp * (0.6 * (0.5 + 0.5 * noise.noise(p * 2.2 + o)) + 0.4 * (0.5 + 0.5 * noise.noise(p * 9.0 + o)))

    fr, bk = [], []
    for j in range(nz + 1):
        row_f, row_b = [], []
        for u in us:
            z = z0 + (top(u) - z0) * j / nz
            row_f.append(bm.verts.new((u, -bulge(u, z), z)))
            row_b.append(bm.verts.new((u, depth, z)))
        fr.append(row_f)
        bk.append(row_b)
    for j in range(nz):
        for i in range(nu):
            bm.faces.new((fr[j][i], fr[j][i + 1], fr[j + 1][i + 1], fr[j + 1][i]))
            bm.faces.new((bk[j][i], bk[j + 1][i], bk[j + 1][i + 1], bk[j][i + 1]))
    edges = ([(fr[0][i], fr[0][i + 1], bk[0][i + 1], bk[0][i]) for i in range(nu)]
             + [(fr[nz][i + 1], fr[nz][i], bk[nz][i], bk[nz][i + 1]) for i in range(nu)]
             + [(fr[j + 1][0], fr[j][0], bk[j][0], bk[j + 1][0]) for j in range(nz)]
             + [(fr[j][nu], fr[j + 1][nu], bk[j + 1][nu], bk[j][nu]) for j in range(nz)])
    for q in edges:
        bm.faces.new(q)


def crescent_bricks(bm, cu, cz, r_in, r_out, lift, pitch, z_min, rng, proud=0.025, mortar=0.014,
                    back=0.08, jitter=0.007):
    """Voussoir bricks between a circle and an upward-shifted outer circle (thick at the crown).

    Every brick is slightly skewed, uneven in depth and size, so the arch looks hand-laid.
    """
    def r_outer(a):
        return lift * math.sin(a) + math.sqrt(max(r_out ** 2 - (lift * math.cos(a)) ** 2, 0.0))
    n = max(8, round(2 * math.pi * (r_in + 0.05) / pitch))
    da = 2 * math.pi / n
    g = mortar / 2 / r_in
    for k in range(n):
        a0, a1 = k * da + g, (k + 1) * da - g
        if r_outer((a0 + a1) / 2) - r_in < 0.035:
            continue
        p = proud + rng.uniform(-0.008, 0.008)
        tilt = rng.uniform(-0.01, 0.01)
        corners = []
        for a, outer in ((a0, False), (a1, False), (a1, True), (a0, True)):
            r = (r_outer(a) - mortar / 2 + rng.uniform(-0.012, 0.004)) if outer else (r_in + mortar / 2)
            corners.append((cu + r * math.cos(a) + rng.uniform(-jitter, jitter),
                            cz + r * math.sin(a) + rng.uniform(-jitter, jitter)))
        if min(z for _, z in corners) < z_min:
            continue
        front = [(u, -p + tilt * (i - 1.5) + rng.uniform(-0.003, 0.003), z) for i, (u, z) in enumerate(corners)]
        hexa(bm, front, [(u, back, z) for u, z in corners])


def brick_row(bm, cu, cz, count, width, height, proud, rng, gap=0.012):
    """A row of soldier bricks (a sill), each a little different."""
    u = cu - count * (width + gap) / 2
    for _ in range(count):
        w = width + rng.uniform(-0.006, 0.006)
        vs = box(bm, (u + w / 2, -proud / 2 + 0.03, cz + rng.uniform(-0.006, 0.006)),
                 (w, proud + 0.06, height + rng.uniform(-0.008, 0.008)),
                 Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, "Y"))
        wobble(vs, 0.004, 9.0, rng.random() * 100)
        u += w + gap


def plank_door(bm, cz, r, front_v, depth, rng, seed):
    """Round planked door: boards of uneven width, slightly bowed and misaligned."""
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

        def zr(uu):
            return math.sqrt(max(r * r - uu * uu, 0.0))
        cols, rows = 3, 14
        fr, bk = [], []
        for j in range(rows + 1):
            t = j / rows
            rf, rb = [], []
            for i in range(cols + 1):
                uu = u0 + (u1 - u0) * i / cols
                z = cz - zr(uu) + 2 * zr(uu) * t
                v = front_v + lean + bow * math.sin(math.pi * t)
                rf.append(bm.verts.new((uu, v, z)))
                rb.append(bm.verts.new((uu, front_v + depth, z)))
            fr.append(rf)
            bk.append(rb)
        for j in range(rows):
            for i in range(cols):
                bm.faces.new((fr[j][i], fr[j][i + 1], fr[j + 1][i + 1], fr[j + 1][i]))
                bm.faces.new((bk[j][i], bk[j + 1][i], bk[j + 1][i + 1], bk[j][i + 1]))
        for i in range(cols):
            bm.faces.new((fr[0][i + 1], fr[0][i], bk[0][i], bk[0][i + 1]))
            bm.faces.new((fr[rows][i], fr[rows][i + 1], bk[rows][i + 1], bk[rows][i]))
        for j in range(rows):
            bm.faces.new((fr[j][0], fr[j + 1][0], bk[j + 1][0], bk[j][0]))
            bm.faces.new((fr[j + 1][cols], fr[j][cols], bk[j][cols], bk[j + 1][cols]))
        wobble([v for row in fr for v in row], 0.003, 6.0, seed + k)


def door_nails(bm, cz, r, front_v, rng):
    """Rows of nail heads where the hidden battens cross the boards."""
    for zrow in (-0.62, -0.32, 0.0, 0.32, 0.62):
        z = cz + zrow * r
        half = math.sqrt(max(r * r - (z - cz) ** 2, 0.0)) - 0.07
        uu = -half
        while uu <= half:
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.017,
                                      matrix=Matrix.Translation((uu + rng.uniform(-0.01, 0.01), front_v,
                                                                 z + rng.uniform(-0.008, 0.008))))
            uu += 0.127


def segmented_ring(bm, cu, cz, r_in, r_out, v0, v1, segments, rng, seed, gap=0.012):
    """A round frame built from curved timber segments with small joints between them."""
    for k in range(segments):
        a0 = 2 * math.pi * k / segments + gap / r_out
        a1 = 2 * math.pi * (k + 1) / segments - gap / r_out
        dr = rng.uniform(-0.008, 0.008)
        vs = arc_block(bm, cu, cz, r_in, r_out + dr, a0, a1, v0 + rng.uniform(-0.004, 0.004), v1, seg=10)
        wobble(vs, 0.004, 4.0, seed + k)


def header_band(bm, us, eave, panels, seed, h_min=0.07, h_dip=0.30, proud=0.035):
    """Timber under the eave whose lower edge arches up over each panel and dips at the posts."""
    top, bot = [], []
    for u in us:
        e = eave(u) - 0.05
        pc, ph = next((c, h) for c, h in panels if abs(u - c) <= h + 1e-9)
        t = (u - pc) / ph
        top.append((u, e))
        bot.append((u, e - h_min - h_dip * t * t))
    vs = extrude(bm, top + list(reversed(bot)), -proud, 0.1)
    wobble(vs, 0.007, 3.0, seed)


def eave_hood(bm_fascia, bm_soffit, us, eave, out, rng, seed):
    """Curved fascia board at the front edge, and uneven soffit boards behind it."""
    top = [(u, eave(u) + 0.01) for u in us]
    low = [(u, eave(u) - 0.14) for u in reversed(us)]
    wobble(extrude(bm_fascia, top + low, -out, -out + 0.06), 0.008, 2.5, seed)
    u, u1 = us[0], us[-1]
    while u < u1 - 0.02:
        w = rng.uniform(0.085, 0.12)
        gap = rng.uniform(0.008, 0.016)
        a, b = u + gap / 2, min(u1, u + w - gap / 2)
        u += w
        if b - a < 0.02:
            continue
        e = eave((a + b) / 2) + rng.uniform(-0.006, 0.004)
        vs = box(bm_soffit, ((a + b) / 2, (-out + 0.11) / 2, e - 0.035), (b - a, out - 0.01, 0.07))
        wobble(vs, 0.004, 5.0, seed + u)


def knee_brace(bm, u, z_top, seed, depth=0.26, rise=0.42, width=0.075, seg=8, grip=0.03):
    """Curved timber bracket filling the corner between a post and the eave above it.

    Its underside is a concave quarter-ellipse from the post out to the eave's front edge; its back
    and top edges sink `grip` into the post and the soffit, so it is one closed, attached solid.
    """
    v0, v1 = -0.06, -0.06 - depth
    z0 = z_top - rise
    ts = [math.pi / 2 * i / seg for i in range(seg + 1)]
    outline = [(v1 + depth * math.cos(t), z0 + rise * math.sin(t)) for t in ts]
    outline += [(v1, z_top + grip), (v0 + grip, z_top + grip), (v0 + grip, z0)]

    def build(b):
        left = [b.verts.new((u - width / 2, v, z)) for v, z in outline]
        right = [b.verts.new((u + width / 2, v, z)) for v, z in outline]
        b.faces.new(left)
        b.faces.new(list(reversed(right)))
        n = len(outline)
        for i in range(n):
            j = (i + 1) % n
            b.faces.new((left[i], left[j], right[j], right[i]))
    wobble(new_verts(bm, build), 0.005, 4.0, seed)


def lantern(bm_iron, bm_glass, u, z_hang, v=-0.13):
    """Hanging lantern on an iron arm; a back strap ties it to the wall so it prints."""
    box(bm_iron, (u, (v + 0.02) / 2, z_hang + 0.02), (0.03, abs(v) + 0.04, 0.03))
    box(bm_iron, (u, v / 2 - 0.01, z_hang - 0.25), (0.03, abs(v) - 0.06, 0.03))
    zb = z_hang - 0.42
    box(bm_iron, (u, v, zb + 0.015), (0.16, 0.16, 0.03))
    for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        box(bm_iron, (u + du * 0.065, v + dv * 0.065, zb + 0.15), (0.02, 0.02, 0.24))
    box(bm_glass, (u, v, zb + 0.15), (0.12, 0.12, 0.23))
    bmesh.ops.create_cone(bm_iron, cap_ends=True, segments=4, radius1=0.13, radius2=0.01, depth=0.11,
                          matrix=Matrix.Translation((u, v, zb + 0.32)) @ Matrix.Rotation(math.pi / 4, 4, "Z"))
    box(bm_iron, (u, v, z_hang - 0.05), (0.02, 0.02, 0.1))


def leaded_glass(bm_glass, bm_came, cu, cz, r, v):
    """Round pane with lead cames: two diagonals and an inner diamond."""
    disc(bm_glass, cu, cz, r, v + 0.005, v + 0.025)
    for a in (45, 135):
        box(bm_came, (cu, v, cz), (0.012, 0.008, 2 * r), Matrix.Rotation(math.radians(a), 4, "Y"))
    for a in (0, 90, 180, 270):
        ang = math.radians(a) + math.pi / 4
        box(bm_came, (cu + 0.42 * r * math.cos(ang), v, cz + 0.42 * r * math.sin(ang)),
            (0.012, 0.008, 0.8 * r), Matrix.Rotation(ang + math.pi / 2, 4, "Y"))


def rough_stone(bm, centre, size, rng, seed, amp=0.012):
    """A worn stone slab: a subdivided block with lumpy faces."""
    def build(b):
        vs = box(b, centre, size)
        bmesh.ops.subdivide_edges(b, edges=list({e for v in vs for e in v.link_edges}), cuts=4, use_grid_fill=True)
    wobble(new_verts(bm, build), amp, 4.0, seed)


def pot(name, mat, coll, matrix):
    """Terracotta pot: a lathed profile with a rim and a soil recess."""
    bm = bmesh.new()
    prof = [(0.001, 0.0), (0.10, 0.0), (0.135, 0.22), (0.16, 0.23), (0.16, 0.27), (0.13, 0.27),
            (0.12, 0.24), (0.001, 0.24)]
    verts = [bm.verts.new((r, 0.0, z)) for r, z in prof]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi,
                   steps=24, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    return to_object(name, bm, mat, coll, matrix)


def sod(bm, us, eave, v0, v1):
    """Turf sitting on a wall mass, so the hill runs down onto the eave."""
    extrude(bm, [(u, eave(u) - 0.02) for u in us] + [(u, eave(u) + 0.14) for u in reversed(us)], v0, v1)

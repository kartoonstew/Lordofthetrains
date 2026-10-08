"""Open the built Bag End and render whole-model views that include the full oak."""
import math, sys
import bpy
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
blend = sys.argv[sys.argv.index("--") + 2]
bpy.ops.wm.open_mainfile(filepath=blend)
s = bpy.context.scene

def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

scene_objs = [o for o in s.objects if o.type in {"MESH", "CURVE"}]
lo, hi = bbox(scene_objs)
print("scene bbox", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
oak = [o for o in s.objects if o.name.startswith("oak_")]
olo, ohi = bbox(oak)
print("oak bbox", tuple(round(v, 2) for v in olo), tuple(round(v, 2) for v in ohi))

def shoot(name, lo, hi, azimuth, elevation, lens=40, margin=1.12):
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    fov = 2 * math.atan(36.0 / 2 / lens) * (930 / 1400)       # the narrower (vertical) angle
    dist = radius * margin / math.sin(fov / 2)
    a, e = math.radians(azimuth), math.radians(elevation)
    loc = centre + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    data = bpy.data.cameras.new(name)
    data.lens, data.sensor_width, data.clip_end = lens, 36.0, dist + 200
    cam = bpy.data.objects.new(name, data)
    s.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (centre - loc).to_track_quat("-Z", "Y").to_euler()
    s.camera = cam
    s.render.filepath = f"{out}/{name}.png"
    bpy.ops.render.render(write_still=True)

shoot("full_front", lo, hi, 0, 8)
shoot("full_threequarter", lo, hi, -35, 18)
shoot("full_above", lo, hi, -20, 40)
shoot("oak_close", olo, ohi, -15, 12, lens=50, margin=1.05)

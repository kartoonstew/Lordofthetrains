"""Clay renders of the built Bag End: one grey material, raking sun, a few cameras."""
import math, sys
import bpy
from mathutils import Vector

out, blend = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
s = bpy.context.scene
clay = bpy.data.materials.new("clay")
b = clay.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.62, 0.62, 0.6, 1)
b.inputs["Roughness"].default_value = 0.9
for o in s.objects:
    if o.type in {"MESH", "CURVE"}:
        o.data.materials.clear()
        o.data.materials.append(clay)
w = bpy.data.worlds.new("grey")
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.27, 0.3, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
s.world = w
for o in [o for o in s.objects if o.type == "LIGHT"]:
    bpy.data.objects.remove(o)
sun = bpy.data.objects.new("rake", bpy.data.lights.new("rake", "SUN"))
sun.data.energy = 4.0
sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(68), 0, math.radians(-40))
s.collection.objects.link(sun)
s.view_settings.view_transform = "Standard"
s.view_settings.exposure = 0.0

def cam(name, loc, target, lens):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_width = 36; d.clip_end = 500
    c = bpy.data.objects.new(name, d); s.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    s.camera = c
    s.render.filepath = f"{out}/clay_{name}.png"
    bpy.ops.render.render(write_still=True)

cam("whole", (-6.0, -17.0, 6.5), (0.0, 0.5, 2.6), 35)
cam("door", (-1.4, -3.6, 0.55), (0.05, 0.0, 1.25), 30)
cam("path", (2.9, -5.4, 0.7), (1.0, -1.5, 0.3), 24)
cam("oak", (-3.0, -10.0, 6.0), (0.3, 2.5, 6.0), 45)

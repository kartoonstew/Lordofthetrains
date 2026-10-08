"""Plain-material Cycles renders from cameras matched to the reference photos."""
import math
from pathlib import Path

import bpy
from mathutils import Vector

from . import parts, scene

# Object name prefix -> base colour (linear RGB). First match wins.
COLOURS = (
    ("hill", parts.TURF),
    ("step_", parts.STONE),
    ("wall_", parts.STONE),
    ("chimney", parts.BRICK),
    ("oak_trunk", (0.18, 0.13, 0.08)),
    ("oak_crown", (0.12, 0.25, 0.08)),
)
TIMBER = (0.33, 0.23, 0.14)

# Cameras matched to the reference photos by eye: (location, look-at, focal length in mm).
# ref01, ref02 and ref03 look at the door front, which is true size, so they line up with their
# photos; ref05 and ref08 show fronts from near where those photos were taken. The hill around the
# fronts is compressed (layout.py), so ref09 and ref10 only frame the same view of it.
CAMERAS = {
    "ref09": ((12.0, -52.0, 3.0), (-5.0, 0.0, 2.6), 90),
    "ref10": ((-16.5, -13.0, -1.3), (-10.0, 0.0, 3.2), 24),
    "ref03": ((2.45, -7.3, 0.1), (0.1, 1.7, 3.8), 24),
    "ref01": ((0.15, -6.0, 1.35), (0.15, 0.0, 1.25), 38),
    "ref02": ((-1.4, -3.6, 0.55), (0.05, 0.0, 1.25), 30),
    "ref05": ((2.9, -5.4, 0.7), (1.0, 0.0, 1.1), 24),
    "ref08": ((-10.2, -4.2, 0.35), (-7.4, 0.0, 2.1), 24),
    "overview": ((-24.0, -30.0, 18.0), (-7.0, 1.0, 0.5), 40),
}


def material(name, colour):
    # Blender 5.0: new materials already carry a node tree with "Principled BSDF",
    # and Material.use_nodes is deprecated, so it is not set here.
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def paint():
    """Plain colours by name prefix, for the garden's plain blocks; detailed parts keep their own.

    The plain materials are named plain_*, so they never reuse a detailed part's material.
    """
    for obj in bpy.data.objects:
        if obj.type != "MESH" or any(obj.data.materials):
            continue
        name, colour = next(((p, c) for p, c in COLOURS if obj.name.startswith(p)), ("timber", TIMBER))
        obj.data.materials.append(material("plain_" + name.rstrip("_"), colour))


def light():
    # Blender 5.0: new worlds already carry a node tree with "Background", and
    # World.use_nodes is deprecated, so it is not set here.
    world = bpy.data.worlds.new("sky")
    nt = world.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(38)
    sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.3
    s = bpy.context.scene
    s.world = world
    s.view_settings.view_transform = "Standard"   # plain colours, as in the photos; AgX washes them out
    s.view_settings.exposure = -2.4
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.5
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-35))
    scene.collection("lights").objects.link(sun)


def add_camera(name, location, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36.0
    data.clip_end = (Vector(target) - Vector(location)).length + 100.0
    cam = bpy.data.objects.new(name, data)
    scene.collection("cameras").objects.link(cam)
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    return cam


def setup():
    paint()
    light()
    for name, (location, target, lens) in CAMERAS.items():
        add_camera(name, location, target, lens)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = 32
    s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = 1400, 930
    s.camera = bpy.data.objects["overview"]


def render_all(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    s = bpy.context.scene
    for name in CAMERAS:
        s.camera = bpy.data.objects[name]
        s.render.filepath = str(out_dir / f"render_{name}.png")
        bpy.ops.render.render(write_still=True)

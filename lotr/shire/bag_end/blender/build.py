"""Build Bag End: tools/blender.sh lotr/shire/bag_end/blender/build.py [--no-render]

Writes lotr/shire/bag_end/bag_end.blend and renders/render_<camera>.png.
"""
import sys
from pathlib import Path

import bpy

from bagend import blockout, doorfront, garden, hill, render, scene

OUT = Path(__file__).resolve().parents[1]


def build_scene():
    scene.reset_scene()
    hill.build()
    blockout.build(exclude=("door",))
    doorfront.build()
    garden.build()
    render.setup()


def main(args):
    build_scene()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bag_end.blend"))
    if "--no-render" not in args:
        render.render_all(OUT / "renders")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

import importlib.util
import pathlib
import re

import bpy
import numpy as np

from bagend import layout as L

BUILD = pathlib.Path(__file__).resolve().parents[1] / "build.py"


def load_build():
    spec = importlib.util.spec_from_file_location("bag_end_build", BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_twice_gives_one_of_each():
    build = load_build()
    build.build_scene()
    build.build_scene()
    names = [o.name for o in bpy.data.objects]
    assert "hill" in names and "doorfront_door_boards" in names and "oak_crown" in names
    assert "round_window_left_window_bars" in names and "lattice_window_window_bars" in names
    garden_parts = {"bench", "gate", "letterbox", "birdhouse", "lamp_0_post", "chimney_pot_0", "bed_0", "step_0",
                    "landing", "chimney_cap_0", "wall_west", "wall_east"}
    assert garden_parts <= set(names), garden_parts - set(names)
    assert not [n for n in names if n.startswith(("front_", "eave_", "window_"))]       # no block-outs left
    dupes = [n for n in names if re.search(r"\.\d{3}$", n)]
    assert not dupes, dupes
    assert not [m.name for m in bpy.data.meshes if m.name.startswith("cutter")]


def test_everything_but_the_oak_fits_on_the_model():
    # The oak is its own print: its crown may overhang the hill's edges, as a real tree's does.
    load_build().build_scene()
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.users_collection[0].name == "oak":
            continue
        co = np.empty(3 * len(obj.data.vertices))
        obj.data.vertices.foreach_get("co", co)
        m = np.array(obj.matrix_world)
        world = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        assert world[:, 0].min() >= L.MODEL_X[0] - 1e-3 and world[:, 0].max() <= L.MODEL_X[1] + 1e-3, obj.name
        assert world[:, 1].min() >= L.LANE_Y - 1e-3 and world[:, 1].max() <= L.BACK_Y + 1e-3, obj.name

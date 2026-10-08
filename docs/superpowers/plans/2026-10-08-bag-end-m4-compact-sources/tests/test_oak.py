import bpy

from bagend import layout as L, oak, scene, terrain


def test_oak_is_a_preview_with_a_spreading_crown_over_its_trunk():
    # Never printed (the hill gets a socket in M5); it should read as a wide, spreading oak.
    scene.reset_scene()
    crown = oak.build()
    trunk = bpy.data.objects["oak_trunk"]
    assert trunk.type == "CURVE" and {trunk.users_collection[0].name, crown.users_collection[0].name} == {"preview"}
    pts = [crown.matrix_world @ v.co for v in crown.data.vertices]
    x, y = L.OAK
    spread = max(max(abs(p.x - x) for p in pts), max(abs(p.y - y) for p in pts))
    height = max(p.z for p in pts) - float(terrain.ground(x, y))
    assert spread >= 3.5 and spread > 0.6 * height, (spread, height)


def test_oak_is_repeatable():
    def crown():
        scene.reset_scene()
        return [tuple(round(c, 5) for c in v.co) for v in oak.build().data.vertices[:500]]
    assert crown() == crown()

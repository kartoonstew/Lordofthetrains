import bmesh
import bpy

from bagend import props, scene, terrain


def is_closed(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        return all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True) > 0
    finally:
        bm.free()


def test_every_prop_is_a_closed_solid_planted_in_the_ground():
    scene.reset_scene()
    props.bench(0.0, -2.0)
    props.gate(2.0, -4.0)
    props.letterbox(1.0, -4.0)
    props.lamp_post("lamp_0", -1.0, -1.5)
    props.birdhouse(3.0, -1.7)
    props.rack(-2.0, -1.0)
    hung = ("_sign", "_lantern", "_glass")            # these hang from a post or the gate
    objs = list(bpy.data.collections["props"].objects)
    assert {"bench", "gate", "gate_sign", "letterbox", "lamp_0_post", "lamp_0_lantern", "birdhouse", "rack"} <= \
        {o.name for o in objs}
    for o in objs:
        assert is_closed(o), o.name
        if not o.name.endswith(hung):
            x, y = o.matrix_world.translation.x, o.matrix_world.translation.y
            low = min((o.matrix_world @ v.co).z for v in o.data.vertices)
            assert low <= float(terrain.ground(x, y)) + 0.01, (o.name, low)


def test_props_are_repeatable():
    def bench():
        scene.reset_scene()
        props.bench(0.0, -2.0)
        return [tuple(round(c, 6) for c in v.co) for v in bpy.data.objects["bench"].data.vertices]
    assert bench() == bench()

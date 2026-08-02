"""Cameras.  Every shot in this build is a real camera object placed in the
room, so a comparison against a reference photograph is repeatable rather than
whatever the viewport happened to be pointing at."""
import bpy, math
from mathutils import Vector
import mlib


def cam(name, loc, look, lens=24.0, roll=0.0, shift=(0.0, 0.0), cname="Cameras"):
    d = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    d.lens = lens
    d.clip_start = 0.02
    d.clip_end = 200.0
    d.shift_x, d.shift_y = shift
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != 'CAMERA':
        ob = bpy.data.objects.new(name, d)
    else:
        ob.data = d
    mlib.put(ob, cname)
    ob.location = Vector(loc)
    aim(ob, look, roll)
    return ob


def aim(ob, target, roll=0.0):
    """A Blender camera looks down its own -Z.  Composing Euler XYZ gives a
    view direction of (-sin rx sin rz, sin rx cos rz, -cos rx), so the pitch is
    atan2(horizontal, -dz) - NOT atan2(horizontal, dz), which mirrors every
    camera about the horizon and quietly points the whole shot at the ceiling
    by exactly the angle it should have been tilted towards the floor."""
    d = Vector(target) - ob.location
    rz = math.atan2(d.y, d.x) - math.pi / 2.0
    rx = math.atan2(math.hypot(d.x, d.y), -d.z)
    ob.rotation_euler = (rx, roll, rz)
    return ob


def look_from(name, loc, yaw, pitch=0.0, lens=24.0, **kw):
    """yaw in degrees measured from +X towards +Y; pitch positive looks up."""
    a = math.radians(yaw)
    p = math.radians(pitch)
    t = (loc[0] + math.cos(a) * math.cos(p) * 4.0,
         loc[1] + math.sin(a) * math.cos(p) * 4.0,
         loc[2] + math.sin(p) * 4.0)
    return cam(name, loc, t, lens=lens, **kw)


def use(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise ValueError("no camera " + name)
    bpy.context.scene.camera = ob
    return ob

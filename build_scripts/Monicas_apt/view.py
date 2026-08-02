import bpy, math
from mathutils import Vector, Quaternion


def areas():
    out = []
    for w in bpy.data.window_managers[0].windows:
        for a in w.screen.areas:
            if a.type == 'VIEW_3D':
                out.append(a)
    return out


def look(loc, target, lens=32.0, shading='SOLID', clip_start=0.02, ortho=False,
         overlays=None, cavity=True):
    l, t = Vector(loc), Vector(target)
    d = l - t
    rot = d.to_track_quat('Z', 'Y')
    for a in areas():
        sp = a.spaces[0]
        r = sp.region_3d
        r.view_perspective = 'ORTHO' if ortho else 'PERSP'
        r.view_rotation = rot
        r.view_location = t
        r.view_distance = d.length
        sp.lens = lens
        sp.clip_start = clip_start
        sp.clip_end = 300.0
        sp.shading.type = shading
        if shading == 'SOLID':
            sp.shading.light = 'STUDIO'
            sp.shading.color_type = 'MATERIAL'
            sp.shading.show_cavity = cavity
            sp.shading.cavity_type = 'BOTH'
        if overlays is not None:
            sp.overlay.show_overlays = overlays
    bpy.context.view_layer.update()


def cam(name, loc, target, lens=28.0, shift=(0, 0)):
    c = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    c.lens = lens
    c.clip_start = 0.02
    c.clip_end = 300
    c.shift_x, c.shift_y = shift
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, c)
        bpy.context.scene.collection.objects.link(ob)
    ob.data = c
    ob.location = Vector(loc)
    d = Vector(loc) - Vector(target)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return ob


def use_cam(name, shading='RENDERED'):
    ob = bpy.data.objects.get(name)
    bpy.context.scene.camera = ob
    for a in areas():
        sp = a.spaces[0]
        sp.region_3d.view_perspective = 'CAMERA'
        sp.shading.type = shading
        sp.overlay.show_overlays = False
    bpy.context.view_layer.update()
    return ob


def hide(names, state=True):
    for n in names:
        o = bpy.data.objects.get(n)
        if o:
            o.hide_set(state)
            o.hide_render = state

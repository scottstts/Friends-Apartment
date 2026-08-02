"""Render and compositing helpers.  EEVEE throughout."""
import bpy, os

NG_BLOOM = "CMP_bloom"


def setup(res=(1600, 900), samples=96):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    ev = sc.eevee
    ev.taa_render_samples = samples
    ev.taa_samples = 16
    ev.use_raytracing = True
    ev.use_shadows = True
    ev.shadow_ray_count = 2
    ev.shadow_step_count = 6
    ev.use_fast_gi = True
    ev.fast_gi_method = 'GLOBAL_ILLUMINATION'
    ev.gi_diffuse_bounces = 4
    try:
        ev.ray_tracing_options.resolution_scale = '1'
        ev.ray_tracing_options.screen_trace_quality = 0.5
        ev.ray_tracing_options.use_denoise = True
    except Exception:
        pass
    sc.view_settings.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'AgX - Base Contrast', 'None'):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
    sc.view_settings.exposure = 0.0
    return sc


def bloom(strength=0.16, threshold=1.0, size=0.55, quality='High'):
    """A slight bloom, in the compositor.

    Blender 5 has no EEVEE bloom pass, and the scene's compositor is a node
    GROUP assigned to `scene.compositing_node_group` rather than a tree hanging
    off the scene - so the tail is a Group Output, and the Glare node's
    settings are sockets rather than properties.

    The head must still be a Render Layers node.  A Group Input looks like the
    obvious source for a node group and links without complaint, but it is
    never fed the render: it sits at its socket default of white and every
    frame comes back blown out.

    Rebuilt from scratch on each call - appending to a live tree would stack a
    fresh Glare node on every rebuild."""
    ng = bpy.data.node_groups.get(NG_BLOOM)
    if ng is None:
        ng = bpy.data.node_groups.new(NG_BLOOM, 'CompositorNodeTree')
    ng.nodes.clear()
    ng.interface.clear()
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers')
    gl = ng.nodes.new('CompositorNodeGlare')
    go = ng.nodes.new('NodeGroupOutput')
    rl.location, gl.location, go.location = (-340, 0), (-80, 0), (260, 0)
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Quality'].default_value = quality
    gl.inputs['Threshold'].default_value = threshold
    gl.inputs['Strength'].default_value = strength
    gl.inputs['Size'].default_value = size
    ng.links.new(rl.outputs['Image'], gl.inputs['Image'])
    ng.links.new(gl.outputs['Image'], go.inputs[0])
    sc = bpy.context.scene
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    return ng


def out_dir():
    base = os.path.dirname(bpy.data.filepath) or os.getcwd()
    d = os.path.join(base, 'renders')
    os.makedirs(d, exist_ok=True)
    return d


HIDE = {
    # A sitcom set has no fourth wall and no ceiling, so the wide "publicity
    # still" angles are shot from where those would be.  This build does have
    # both - the room has to be a closed box for the light to behave - so the
    # shots that stand outside it drop exactly the surfaces the camera would
    # otherwise be buried in.
    'C_full': ('W_South', 'Panel_S_0', 'Panel_S_1', 'Panel_S_2', 'Panel_S_3',
               'Base_02'),
    'C_plan': ('Ceiling', 'Ceiling_Chan', 'Ceiling_Joey', 'Ceiling_Bath',
               'Cornice', 'Cornice_Chan', 'Cornice_Joey'),
    'C_high': ('W_South', 'Panel_S_0', 'Panel_S_1', 'Panel_S_2', 'Panel_S_3',
               'Base_02'),
}


def shot(camname, name=None, pct=40, samples=None, hide=None, exposure=None):
    sc = bpy.context.scene
    cam = bpy.data.objects.get(camname)
    if cam is None:
        raise ValueError("no camera " + camname)
    sc.camera = cam
    old = (sc.render.resolution_percentage, sc.render.filepath,
           sc.eevee.taa_render_samples, sc.view_settings.exposure)
    sc.render.resolution_percentage = pct
    if samples:
        sc.eevee.taa_render_samples = samples
    if exposure is not None:
        sc.view_settings.exposure = exposure
    names = list(HIDE.get(camname, ())) + list(hide or ())
    hidden = []
    for n in names:
        for o in bpy.data.objects:
            if o.name == n or o.name.startswith(n + "."):
                if not o.hide_render:
                    o.hide_render = True
                    hidden.append(o)
    p = os.path.join(out_dir(), (name or camname) + ".png")
    sc.render.filepath = p
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        for o in hidden:
            o.hide_render = False
        (sc.render.resolution_percentage, sc.render.filepath,
         sc.eevee.taa_render_samples, sc.view_settings.exposure) = old
    return p

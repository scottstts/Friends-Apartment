import bpy, os

NG_BLOOM = "CMP_bloom"


def bloom(strength=0.18, threshold=1.0, size=0.5, quality='High'):
    """A slight bloom, done in the compositor.

    Blender 5 has no EEVEE bloom pass, and the scene's compositor is no longer
    a tree hanging off the scene - it is a node group assigned to
    `scene.compositing_node_group`.  So the tail is a Group Output rather than
    the old Composite node, which no longer exists, and the Glare node's
    settings are sockets rather than properties.

    The head is still a Render Layers node.  A Group Input looks like the
    obvious source for a node *group* and connects without complaint, but it is
    never fed the render - it sits at its socket default of white, and every
    frame comes back blown out to pure white.

    `strength` carries the whole effect: 0.18 lifts the bulbs, the opal shades
    and the window without laying a haze over the room.  `threshold` is in
    linear scene units, so at 1.0 only what is genuinely brighter than white
    blooms - which is the difference between a lens and a soft-focus filter.

    Rebuilt from scratch on every call: `go()` runs this on each rebuild, and
    appending to a live tree would stack a new Glare node every time."""
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


def _out():
    """renders/ beside the .blend.  This pointed at a scratch directory from a
    long-dead session, so every shot was being written somewhere nobody would
    look for it."""
    base = os.path.dirname(bpy.data.filepath) or os.getcwd()
    return os.path.join(base, 'renders')


def shot(camname, name=None, pct=34, samples=160):
    # 24 samples is not enough to judge anything by.  EEVEE's ray-traced
    # reflections sparkle badly below about a hundred, and that sparkle reads as
    # a glitter texture on worktops and metalwork - it is easy to spend an
    # afternoon hunting a material bug that is only undersampling.
    OUT = _out()
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    cam = bpy.data.objects.get(camname)
    if cam is None:
        raise ValueError("no camera " + camname)
    sc.camera = cam
    old = (sc.render.resolution_percentage, sc.render.filepath,
           sc.render.image_settings.file_format)
    sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = 'PNG'
    sc.render.film_transparent = False
    if hasattr(sc, 'eevee'):
        sc.eevee.taa_render_samples = samples
    p = os.path.join(OUT, (name or camname) + ".png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    (sc.render.resolution_percentage, sc.render.filepath,
     sc.render.image_settings.file_format) = old
    return p


def stats():
    """Mean/percentile of the last render (linear)."""
    im = bpy.data.images.get('Render Result')
    if im is None:
        return None
    return im.size[:]

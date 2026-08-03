"""Compositing.

The brief asks for slight bloom and nothing else, so that is all this does:
a Glare node in Bloom mode, and its glare-only output added back over the
render at low weight.  No grade, no vignette, no chromatic aberration - the
look is supposed to come from the practicals and from AgX, and anything
added here would be covering for them.

Blender 5 rebuilt the compositor: the scene no longer has a `node_tree` with
RenderLayers and Composite nodes in it, it has a `compositing_node_group` -
an ordinary node group with an Image in and an Image out.  Glare's settings
moved from RNA properties onto input sockets at the same time, and the enum
values became title case ('Bloom', not 'BLOOM').
"""
import bpy

NAME = "CP_Comp"


def _iface(ng, name, in_out):
    for it in ng.interface.items_tree:
        if it.item_type == 'SOCKET' and it.name == name and it.in_out == in_out:
            return it
    return ng.interface.new_socket(name, in_out=in_out,
                                   socket_type='NodeSocketColor')


def build(strength=0.075, threshold=1.0, size=0.62):
    sc = bpy.context.scene
    ng = bpy.data.node_groups.get(NAME)
    if ng is None:
        ng = bpy.data.node_groups.new(NAME, 'CompositorNodeTree')
    ng.nodes.clear()
    _iface(ng, "Image", 'INPUT')
    _iface(ng, "Image", 'OUTPUT')

    # The source is a Render Layers node, NOT the group input.  Wiring it to
    # the group input instead produced a pure white frame in 0.1 s: with
    # nothing in the tree depending on the render layer, Blender skips the
    # render altogether and composites the socket's default colour.  The
    # symptom is alarming - every engine, in and out of process, returns a
    # blank - and none of it is a scene problem.
    gin = ng.nodes.new('CompositorNodeRLayers'); gin.location = (-560, 0)
    gin.scene = sc
    glare = ng.nodes.new('CompositorNodeGlare'); glare.location = (-300, -40)
    for key, val in (('Type', 'Bloom'), ('Quality', 'High'),
                     ('Threshold', threshold), ('Size', size),
                     ('Strength', 1.0), ('Smoothness', 0.2),
                     ('Saturation', 1.0)):
        s = glare.inputs.get(key)
        if s is None:
            continue
        try:
            s.default_value = val
        except (TypeError, AttributeError):
            pass

    add = ng.nodes.new('ShaderNodeMix'); add.location = (-40, 0)
    add.data_type = 'RGBA'
    add.blend_type = 'ADD'
    gout = ng.nodes.new('NodeGroupOutput'); gout.location = (220, 0)

    def sock(coll, key):
        s = coll[key]
        if getattr(s, "enabled", True):
            return s
        for t in coll:
            if t.name == s.name and t.enabled:
                return t
        return s

    sock(add.inputs, 'Factor').default_value = strength
    ng.links.new(gin.outputs['Image'], glare.inputs['Image'])
    ng.links.new(gin.outputs['Image'], sock(add.inputs, 'A'))
    # the Glare output is the bloom ALONE, so adding it never dims the plate
    ng.links.new(glare.outputs['Glare'], sock(add.inputs, 'B'))
    ng.links.new(sock(add.outputs, 'Result'), gout.inputs['Image'])

    sc.use_nodes = True
    sc.compositing_node_group = ng
    print("comp: bloom %.3f" % strength)
    return ng

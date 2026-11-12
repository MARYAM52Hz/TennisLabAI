import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
def wb(o):
    me = o.data; v = np.array([(o.matrix_world @ x.co)[:] for x in me.vertices]); return v
for n in ('Lines', 'Net', 'Court', 'Umpires Chair', 'Plane', 'Barriers', 'Steps'):
    o = bpy.data.objects.get(n)
    if o is None: continue
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); v = np.array([(oe.matrix_world @ x.co)[:] for x in me.vertices])
    print(n, 'loc', tuple(round(x, 3) for x in o.location), 'rot', tuple(round(x, 3) for x in o.rotation_euler), 'scale', tuple(round(x, 3) for x in o.scale), '| world bbox min', v.min(0).round(2), 'max', v.max(0).round(2), 'n', len(v))
    if n == 'Lines':
        xs = np.unique(np.round(v[:, 0], 2)); ys = np.unique(np.round(v[:, 1], 2)); print('  unique x', xs[:60]); print('  unique y', ys[:60]); print('  z range', v[:, 2].min().round(3), v[:, 2].max().round(3))
    oe.to_mesh_clear()
sc = bpy.context.scene
print('camera', [(o.name, tuple(round(x, 2) for x in o.location)) for o in bpy.data.objects if o.type == 'CAMERA'])
print('lights', [(o.name, o.data.type, round(o.data.energy, 1), tuple(round(x, 2) for x in o.location)) for o in bpy.data.objects if o.type == 'LIGHT'])
w = sc.world; print('world', w.name if w else None, 'nodes', [n.type for n in w.node_tree.nodes] if w and w.use_nodes else None)
for n in w.node_tree.nodes:
    if n.type == 'BACKGROUND': print(' bg color', tuple(n.inputs[0].default_value), 'strength', n.inputs[1].default_value)
sk = bpy.data.objects.get('Skydome'); print('skydome mats', [m.name for m in sk.data.materials], 'loc', tuple(sk.location))
for m in bpy.data.materials:
    if m.use_nodes:
        print(m.name, [n.type for n in m.node_tree.nodes][:8])

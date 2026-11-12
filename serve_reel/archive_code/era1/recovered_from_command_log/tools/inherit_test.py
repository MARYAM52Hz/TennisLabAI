import bpy, math, numpy as np
from mathutils import Vector, Matrix
bpy.ops.wm.read_factory_settings(use_empty=True)
arm = bpy.data.armatures.new('a'); ob = bpy.data.objects.new('a', arm); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.objects.active = ob; bpy.ops.object.mode_set(mode='EDIT')
p = arm.edit_bones.new('p'); p.head = (0, 0, 0); p.tail = (0, 1, 0)
c = arm.edit_bones.new('c'); c.head = (0, 1, 0); c.tail = (0, 2, 0); c.parent = p; c.use_connect = True
g = arm.edit_bones.new('g'); g.head = (0, 2, 0); g.tail = (0, 3, 0); g.parent = c; g.use_connect = True
bpy.ops.object.mode_set(mode='POSE')
for mode in ('FULL', 'NONE', 'ALIGNED'):
    for b in ob.pose.bones: b.matrix_basis = Matrix.Identity(4); b.bone.inherit_scale = mode
    ob.pose.bones['p'].scale = (1, 1.5, 1); ob.pose.bones['c'].rotation_mode = 'XYZ'; ob.pose.bones['c'].rotation_euler = (math.radians(40), 0, 0)
    bpy.context.view_layer.update()
    print(mode, 'c.head', tuple(round(x, 3) for x in ob.pose.bones['c'].head), 'c.tail', tuple(round(x, 3) for x in ob.pose.bones['c'].tail), '| g.head', tuple(round(x, 3) for x in ob.pose.bones['g'].head), 'g.tail', tuple(round(x, 3) for x in ob.pose.bones['g'].tail),
          '| c matrix scale', tuple(round(x, 3) for x in ob.pose.bones['c'].matrix.to_scale()))

import sys, bpy, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); sc = bpy.context.scene; out = sys.argv[2]
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x, sc.render.resolution_y = 500, 800
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.render_aa = '8'
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.5, 0.5, 0.55)
for name, loc in (('front', (6, 0, 0.9)), ('side', (0, -6, 0.9)), ('three', (4.2, -4.2, 1.3))):
    cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = 2.3; co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co); co.location = loc
    co.rotation_euler = (Vector((0, 0, 0.9)) - co.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = co; sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)

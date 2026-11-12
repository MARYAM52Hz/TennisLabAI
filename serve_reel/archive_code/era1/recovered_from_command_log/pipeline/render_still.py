import sys, bpy
blend, cam, frame, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; sc.camera = bpy.data.objects[cam]; sc.frame_set(frame)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 50
try: sc.eevee.taa_render_samples = 24
except Exception: pass
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('done', sc.render.engine)

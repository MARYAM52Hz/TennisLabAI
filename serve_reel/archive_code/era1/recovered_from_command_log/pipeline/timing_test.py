import sys, time, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); sc = bpy.context.scene; e = sc.eevee
print('has', [k for k in dir(e) if 'ray' in k or 'taa' in k or 'shadow' in k or 'gi' in k][:30])
variant = sys.argv[2]
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 67
sc.frame_set(74)
if variant == 'a': e.taa_render_samples = 12
if variant == 'b':
    e.taa_render_samples = 12
    try: e.ray_tracing_options.resolution_scale = '4'
    except Exception as ex: print('rto', ex)
    try: e.ray_tracing_method = 'SCREEN'
    except Exception as ex: print('rtm', ex)
if variant == 'c':
    e.taa_render_samples = 12; e.use_raytracing = False
t = time.time(); sc.render.filepath = f'/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad/r3/t_{variant}.png'; bpy.ops.render.render(write_still=True); print('TIME', variant, round(time.time() - t, 1))

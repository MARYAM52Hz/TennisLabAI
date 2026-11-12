import sys, time, numpy as np, bpy
sys.path.insert(0, '/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad/pipeline')
from motion import Motion; import scene_lib as SL
D = '/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad/data'; out = sys.argv[1]; pct = int(sys.argv[2]); spp = int(sys.argv[3])
M = Motion(D, lam_j=0.4, lam_r=0.2); S = SL.build_scene(M); sc = S['sc']; sc.render.resolution_percentage = pct
sc.eevee.taa_render_samples = spp
def on_frame(scene, *a):
    f = scene.frame_current; tau = 70.0 + 0.1 * f; SL.pose(S, tau); SL.set_camera(S, tau, 100 + f, 4, 4.8, 70, [0, 0, 1.0])
bpy.app.handlers.frame_change_pre.append(on_frame)
sc.frame_start, sc.frame_end = 1, 5; sc.render.filepath = out + '/f_'; sc.render.image_settings.file_format = 'PNG'
t0 = time.time(); bpy.ops.render.render(animation=True); print('TIME total', round(time.time() - t0, 1), 'per frame', round((time.time() - t0) / 5, 1))

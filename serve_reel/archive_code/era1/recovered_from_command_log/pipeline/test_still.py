import sys, time, json, numpy as np, bpy
sys.path.insert(0, '/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad/pipeline')
from motion import Motion; import scene_lib as SL
D = '/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad/data'; out = sys.argv[1]; jobs = json.loads(sys.argv[2])
M = Motion(D, lam_j=0.4, lam_r=0.2); S = SL.build_scene(M); sc = S['sc']; sc.render.resolution_percentage = 50
for j in jobs:
    t0 = time.time(); SL.pose(S, j['tau']); SL.set_camera(S, j['tau'], j['az'], j['el'], j['dist'], j.get('lens', 70), j.get('tgt', [0, 0, 1.0]))
    sc.render.filepath = f"{out}/{j['name']}.png"; bpy.ops.render.render(write_still=True); print('TIME', j['name'], round(time.time() - t0, 1))

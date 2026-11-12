import sys, time, json, numpy as np, bpy
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline'); sys.path.insert(0, SP + '/lab2')
import scene_skel as SS
from motion_lab2 import Motion2
from mathutils import Vector
M = Motion2(); S = SS.build(M, SP + '/assets/stadium/Tennis Stadium Update.blend', 100, 4); sc = S['sc']; cam = S['cam']; fr = json.load(open(SP + '/lab3/plan.json'))['frames'][331]
for a, b, o in S['pbones']: o.hide_render = True
for o in S['pjoints'].values(): o.hide_render = True
cam.location = Vector(fr['cam']); cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (Vector(fr['target']) - Vector(fr['cam'])).to_track_quat('-Z', 'Y'); import math; cam.data.lens = 36 / (2 * math.tan(math.radians(fr['fov']) / 2))
print('objects', len(bpy.data.objects), 'meshes', len(bpy.data.meshes), 'polys', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'engine', sc.render.engine, flush=True)
ee = sc.eevee
for k in dir(ee):
    if any(s in k for s in ('shadow', 'raytrac', 'gtao', 'fast_gi', 'volumetric', 'use_', 'light_threshold')) and not k.startswith('_'):
        try: print(k, getattr(ee, k))
        except Exception: pass
for samples, pct in ((4, 100), (1, 100), (4, 50), (1, 50)):
    sc.eevee.taa_render_samples = samples; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 928, 1696, pct; sc.render.filepath = SP + f'/lab3/bench_{samples}_{pct}.png'
    t = time.time(); bpy.ops.render.render(write_still=True); print('BENCH samples', samples, 'pct', pct, round(time.time() - t, 1), flush=True)

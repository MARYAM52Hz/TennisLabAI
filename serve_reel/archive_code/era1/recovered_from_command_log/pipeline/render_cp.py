"""Render checkpoint stills/frames + export 2D projections.  usage: python3 -I render_cp.py scene.blend jobs.json outdir
job = {name, frame(float ok), az, el, dist, lens, tgt:[dx,dy,dz offset from pelvis] , scale(% res)}"""
import sys, json, math, numpy as np, bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
blend, jobs, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
bpy.ops.wm.open_mainfile(filepath=blend); sc = bpy.context.scene
data = '/tmp/claude-0/-home-claude/813f700f-0243-50f8-b2f1-bbd385cfaf4f/scratchpad/data'
pl = np.load(data + '/player3d_joint_ext.npz', allow_pickle=True); X = pl['X']; names = [str(n) for n in pl['names']]; I = {n: i for i, n in enumerate(names)}
hv = X[66, I['right_hip']] - X[66, I['left_hip']]; hv[2] = 0; right0 = hv / np.linalg.norm(hv); fwd0 = np.cross([0, 0, 1], right0)
cd = bpy.data.cameras.new('cpcam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.clip_start = .05; cd.clip_end = 400
co = bpy.data.objects.new('cpcam', cd); sc.collection.objects.link(co); sc.camera = co
try: sc.eevee.taa_render_samples = 24
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
for j in jobs:
    f = j['frame']; sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    t = int(round(f)); pel = (X[t, I['left_hip']] + X[t, I['right_hip']]) / 2
    tgt = Vector(pel + np.array(j.get('tgt', [0, 0, .5]))); az = math.radians(j['az']); el = math.radians(j.get('el', 8)); d = j.get('dist', 5.0)
    dirv = math.cos(az) * fwd0 + math.sin(az) * right0
    pos = tgt + Vector((dirv[0] * math.cos(el), dirv[1] * math.cos(el), math.sin(el))) * d
    co.location = pos; co.rotation_mode = 'QUATERNION'; co.rotation_quaternion = (tgt - pos).to_track_quat('-Z', 'Y'); cd.lens = j.get('lens', 40)
    bpy.context.view_layer.update()
    sc.render.resolution_percentage = j.get('scale', 50); sc.render.filepath = f"{out}/{j['name']}.png"
    if not j.get('noimg'): bpy.ops.render.render(write_still=True)
    # projections (normalised 0..1, origin top-left)
    def pr(p):
        v = world_to_camera_view(sc, co, Vector(p)); return [v.x, 1 - v.y, v.z]
    rk = np.load(data + '/racket3d_joint_ext.npz', allow_pickle=True); rn = [str(n) for n in rk['names']]
    ball = np.load(data + '/ball3d.npz')['P']
    proj = {n: pr(X[t, i]) for n, i in I.items()}
    proj.update({'racket_' + n: pr(rk['P'][t, k]) for k, n in enumerate(rn)}); proj['ball'] = pr(ball[t]); proj['pelvis'] = pr(pel)
    json.dump(proj, open(f"{out}/{j['name']}.json", 'w'))
print('rendered', len(jobs))

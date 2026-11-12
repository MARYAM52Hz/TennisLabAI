"""Layers from the label-driven motion: plate (empty stadium), sk (skeleton), rb (racket + ball), all with the court-calibrated matched camera.
usage: python3 -I scene_lab.py OUTDIR FIRST LAST [--pct 100] [--samples 4]"""
import sys, os, time, math, numpy as np, bpy
from mathutils import Matrix, Vector
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline'); sys.path.insert(0, SP + '/lab2')
import scene_skel as SS
from motion_lab import LabMotion, DT
arg = SS.arg; WIMG, HIMG = 464, 848
out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
M = LabMotion(); S = SS.build(M, SP + '/assets/stadium/Tennis Stadium Update.blend', 100, arg('--samples', 4, int)); sc = S['sc']
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2 * WIMG, 2 * HIMG, arg('--pct', 100, int)
S['cam'].data.lens = M.K[0, 0] * 36.0 / WIMG
for a, b, o in S['pbones']: bpy.data.objects.remove(o)
EDG = [('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'), ('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist'), ('left_shoulder', 'top_spine'), ('right_shoulder', 'top_spine'), ('top_spine', 'bottom_spine'), ('top_spine', 'head'),
       ('left_hip', 'bottom_spine'), ('right_hip', 'bottom_spine'), ('left_hip', 'left_knee'), ('left_knee', 'left_ankle'), ('right_hip', 'right_knee'), ('right_knee', 'right_ankle'),
       ('left_ankle', 'left_heel'), ('left_ankle', 'left_foot_index'), ('left_heel', 'left_foot_index'), ('right_ankle', 'right_heel'), ('right_ankle', 'right_foot_index'), ('right_heel', 'right_foot_index')]
cy = SS.cyl_mesh(); bone_mat = next(m for m in bpy.data.materials if m.name.startswith('bone'))
bones = []
for a, b in EDG:
    o = bpy.data.objects.new(f'b_{a}_{b}', cy.copy()); o.data.materials.clear(); o.data.materials.append(bone_mat); bpy.context.scene.collection.objects.link(o); o.rotation_mode = 'QUATERNION'; bones.append((a, b, o))
skel_objs = [o for a, b, o in bones] + list(S['pjoints'].values()); rb_objs = [S['racket'], S['ball']] + list(S['racket'].children)
def vis(objs, v):
    for o in objs: o.hide_render = not v
V = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
def pose(tau):
    J = M.joints(float(tau))
    for a, b, o in bones:
        pa, pb = J[a], J[b]; d = pb - pa; L = float(np.linalg.norm(d)); o.location = V(pa); o.rotation_quaternion = V(d).to_track_quat('Z', 'Y'); o.scale = (0.017, 0.017, max(L, 1e-4))
    for n, o in S['pjoints'].items(): o.location = V(J[n]); r = 0.075 if n == 'head' else 0.031; o.scale = (r, r, r)
    bR, RR, _ = M.racket(float(tau)); S['racket'].location = V(bR); S['racket'].rotation_quaternion = Matrix(RR.tolist()).to_quaternion()
    S['ball'].location = V(M.ball(float(tau))); S['ball'].scale = (0.0335 * 1.4,) * 3; bpy.context.view_layer.update()
keep = set(skel_objs) | set(rb_objs)
vis(skel_objs, False); vis(rb_objs, False); sc.render.filepath = out + '/plate.png'
if not os.path.exists(out + '/plate.png'): bpy.ops.render.render(write_still=True); print('PLATE done', flush=True)
for o in bpy.data.objects:
    if o.type in ('MESH', 'EMPTY', 'CURVE') and o not in keep: o.hide_render = True
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
for n in range(lo, hi + 1):
    todo = [(k, f'{out}/{k}{n:04d}.png') for k in ('sk', 'rb') if not os.path.exists(f'{out}/{k}{n:04d}.png')]
    if not todo: continue
    pose(n); t0 = time.time()
    for k, png in todo:
        vis(skel_objs, k == 'sk'); vis(rb_objs, k == 'rb'); sc.render.filepath = png; bpy.ops.render.render(write_still=True)
    print('DONE', n, round(time.time() - t0, 1), flush=True)

"""Raw-video reconstruction: white mannequin (fitted to the auto-detected skeleton) + model racket/ball in the stadium, camera from court calibration.
usage: python3 -I scene_auto.py OUTDIR FIRST LAST [--serve B] [--pct 75] [--samples 4] [--key 1000]"""
import sys, os, time, numpy as np, bpy
from mathutils import Matrix, Vector
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline'); sys.path.insert(0, SP + '/auto')
import scene_skel as SS
from rigpose2 import RigPoser2
from auto_motion import AutoMotion, DT
arg = SS.arg; WIMG, HIMG = 464, 848
def build(M, pct, samples):
    S = SS.build(M, SP + '/assets/stadium/Tennis Stadium Update.blend', 100, samples); sc = S['sc']; COLL = sc.collection
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2 * WIMG, 2 * HIMG, pct
    S['cam'].data.lens = M.K[0, 0] * 36.0 / WIMG; S['cam'].data.shift_x = 0; S['cam'].data.shift_y = 0
    for a, b, o in S['pbones']: o.hide_render = True
    for o in S['pjoints'].values(): o.hide_render = True
    with bpy.data.libraries.load(SP + '/char/man_clothed.blend', link=False) as (src, dst): order = list(src.objects); dst.objects = list(order)
    objs = {n: o for n, o in zip(order, dst.objects) if o is not None}
    for o in objs.values(): COLL.objects.link(o)
    pl = M.joint_f('bottom_spine', 160)
    l = bpy.data.lights.new('key', 'AREA'); l.energy = arg('--key', 1000, float); l.size = 5; ko = bpy.data.objects.new('key', l); COLL.objects.link(ko); ko.location = (pl[0] + 3.5, pl[1] - 9.5, 6.0)
    ko.rotation_euler = (Vector((pl[0], pl[1], 1.1)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
    S['arm'] = objs['Armature']; S['arm'].hide_render = True
    for pb in S['arm'].pose.bones: pb.rotation_mode = 'QUATERNION'; pb.bone.inherit_scale = 'NONE'
    f0, f1 = M.f_rel - 20, int(M.tc / DT) + 40
    S['rp'] = rp = RigPoser2(SP + '/rig/rig_info_p.json'); rp.calibrate([M.joints(float(t)) for t in range(max(0, f0), min(M.T, f1))])
    return S
def pose(S, tau):
    M, rp, arm = S['M'], S['rp'], S['arm']; J = M.joints(float(tau)); ball = M.ball(float(tau))
    B = rp.basis_exact(rp.pose_exact(J, look_at=ball if (tau * DT < M.tc and ball[2] > 0) else None))
    for n, pb in arm.pose.bones.items(): pb.matrix_basis = Matrix(B[n].tolist())
    b, RR, _ = M.racket(float(tau)); S['racket'].location = Vector(b.tolist()); S['racket'].rotation_quaternion = Matrix(RR.tolist()).to_quaternion()
    S['ball'].location = Vector(ball.tolist()); S['ball'].scale = (0.0335 * 1.4,) * 3
    bpy.context.view_layer.update()
if __name__ == '__main__':
    out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
    M = AutoMotion(arg('--serve', 'B')); S = build(M, arg('--pct', 75, int), arg('--samples', 4, int)); S['M'] = M; sc = S['sc']
    for n in range(lo, hi + 1):
        png = f'{out}/f{n:04d}.png'
        if os.path.exists(png): continue
        t0 = time.time(); pose(S, float(n)); sc.render.filepath = png; bpy.ops.render.render(write_still=True); print('DONE', n, round(time.time() - t0, 1), flush=True)

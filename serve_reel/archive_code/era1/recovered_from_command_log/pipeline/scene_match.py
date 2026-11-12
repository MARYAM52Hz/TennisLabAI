"""White male mannequin (T-shirt, shorts, shoes) fitted EXACTLY to the labelled skeleton, inside the Tennis Stadium model, matched camera.
usage: python3 -I scene_match.py OUTDIR FIRST LAST [--pct 100] [--samples 6] [--overlay]   (--overlay draws the raw label skeleton on top: proof of fit)"""
import sys, os, time, numpy as np, bpy
from mathutils import Matrix
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, SP + '/pipeline')
import scene_skel as SS
from motion import Motion
from rigpose2 import RigPoser2
arg = SS.arg

def build(M, pct, samples, overlay):
    S = SS.build(M, arg('--stadium', SP + '/assets/stadium/Tennis Stadium Update.blend'), pct, samples); COLL = S['sc'].collection
    if not overlay:
        for a, b, o in S['pbones']: o.hide_render = True
        for o in S['pjoints'].values(): o.hide_render = True
    with bpy.data.libraries.load(SP + '/char/man_clothed.blend', link=False) as (src, dst):
        order = list(src.objects); dst.objects = list(order)
    objs = {n: o for n, o in zip(order, dst.objects) if o is not None}
    for o in objs.values(): COLL.objects.link(o)
    S['arm'] = objs['Armature']; S['arm'].hide_render = True
    for pb in S['arm'].pose.bones: pb.rotation_mode = 'QUATERNION'; pb.bone.inherit_scale = 'NONE'
    S['rp'] = rp = RigPoser2(SP + '/rig/rig_info_p.json'); rp.calibrate([M.straighten_left(M.joints(float(t)), float(t)) for t in range(92)])
    return S

def pose(S, tau, overlay):
    M, rp, arm = S['M'], S['rp'], S['arm']
    SS.pose(S, tau)                                   # racket, ball, (label skeleton)
    J = M.straighten_left(M.joints(float(tau)), float(tau)); ball = M.ball(float(tau))
    B = rp.basis_exact(rp.pose_exact(J, look_at=ball if tau < 76 else None))
    for n, pb in arm.pose.bones.items(): pb.matrix_basis = Matrix(B[n].tolist())
    bpy.context.view_layer.update()

if __name__ == '__main__':
    out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); ov = '--overlay' in sys.argv; os.makedirs(out, exist_ok=True)
    M = Motion(SP + '/data', suffix='_ext3'); S = build(M, arg('--pct', 100, int), arg('--samples', 6, int), ov); sc = S['sc']
    for n in range(lo, hi + 1):
        png = f'{out}/f{n:04d}.png'
        if os.path.exists(png): continue
        t0 = time.time(); pose(S, float(n), ov); sc.render.filepath = png; bpy.ops.render.render(write_still=True); print('DONE', n, round(time.time() - t0, 1), flush=True)

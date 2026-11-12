"""Blender-side check: pose the real armature with RigPoser2 (exact stretch, inherit_scale NONE) and measure bone head/tail vs labels."""
import sys, numpy as np, bpy
from mathutils import Matrix
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline')
from motion import Motion; from rigpose2 import RigPoser2
bpy.ops.wm.open_mainfile(filepath=SP + '/char/man_clothed.blend')
M = Motion(SP + '/data', suffix='_ext3'); rp = RigPoser2(SP + '/rig/rig_info_p.json'); arm = bpy.data.objects['Armature']
print('armature matrix_world identity:', np.allclose(np.array(arm.matrix_world), np.eye(4)))
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.bone.inherit_scale = 'NONE'
pairs = {'Humerus_L': ('head', 'left_shoulder'), 'Forearm_L': ('head', 'left_elbow'), 'Palm_L': ('head', 'left_wrist'), 'Femur_L': ('head', 'left_hip'), 'Tibia_L': ('head', 'left_knee'), 'Heel_L': ('head', 'left_ankle'),
         'Humerus_R': ('head', 'right_shoulder'), 'Forearm_R': ('head', 'right_elbow'), 'Palm_R': ('head', 'right_wrist'), 'Femur_R': ('head', 'right_hip'), 'Tibia_R': ('head', 'right_knee'), 'Heel_R': ('head', 'right_ankle'),
         'Toes_L': ('tail', 'left_foot_index'), 'Toes_R': ('tail', 'right_foot_index'), 'Fingers_L': ('tail', 'left_index'), 'Fingers_R': ('tail', 'right_index'), 'Bone': ('head', 'bottom_spine'), 'Bone.003': ('tail', 'top_spine')}
err = {k: [] for k in pairs}; stretch = {}
for t in range(0, 92, 1):
    J = M.straighten_left(M.joints(float(t)), float(t)); P = rp.pose_exact(J, look_at=None); B = rp.basis_exact(P)
    for n in rp.order: arm.pose.bones[n].matrix_basis = Matrix(B[n].tolist())
    bpy.context.view_layer.update()
    for b, (end, j) in pairs.items():
        pb = arm.pose.bones[b]; p = np.array((arm.matrix_world @ (pb.head if end == 'head' else pb.tail))[:]); err[b].append(np.linalg.norm(p - J[j]) * 100)
    for n, s in rp.last_scale.items(): stretch.setdefault(n, []).append(s)
print('joint error (cm) mean / p95 / max   [Blender pose bones vs labels]')
for b, v in err.items(): v = np.array(v); print(f'{b:10s} {pairs[b][1]:14s} {v.mean():6.2f} {np.percentile(v,95):6.2f} {v.max():6.2f}')
allv = np.concatenate([np.array(v) for v in err.values()]); print('ALL mean %.2f cm  p95 %.2f  max %.2f' % (allv.mean(), np.percentile(allv, 95), allv.max()))
print('Y-stretch per bone (min / mean / max):')
for n, v in stretch.items(): v = np.array(v); print(f'  {n:10s} {v.min():.2f} {v.mean():.2f} {v.max():.2f}')

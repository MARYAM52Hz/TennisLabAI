import sys, numpy as np, bpy
from mathutils import Matrix
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline'); sys.path.insert(0, SP + '/auto')
from rigpose2 import RigPoser2; from auto_motion import AutoMotion, DT
char, rig = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=char); M = AutoMotion('B'); rp = RigPoser2(rig); arm = bpy.data.objects['Armature']
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.bone.inherit_scale = 'NONE'
fr = list(range(135, 226)); rp.calibrate([M.joints(float(t)) for t in fr])
pairs = {'Humerus_L': ('head', 'left_shoulder'), 'Forearm_L': ('head', 'left_elbow'), 'Palm_L': ('head', 'left_wrist'), 'Femur_L': ('head', 'left_hip'), 'Tibia_L': ('head', 'left_knee'), 'Heel_L': ('head', 'left_ankle'),
         'Humerus_R': ('head', 'right_shoulder'), 'Forearm_R': ('head', 'right_elbow'), 'Palm_R': ('head', 'right_wrist'), 'Femur_R': ('head', 'right_hip'), 'Tibia_R': ('head', 'right_knee'), 'Heel_R': ('head', 'right_ankle'),
         'Toes_L': ('tail', 'left_foot_index'), 'Toes_R': ('tail', 'right_foot_index'), 'Fingers_R': ('tail', 'right_index'), 'Bone': ('head', 'bottom_spine'), 'Bone.003': ('tail', 'top_spine')}
err = {k: [] for k in pairs}; st = {}
for t in fr:
    J = M.joints(float(t)); B = rp.basis_exact(rp.pose_exact(J))
    for n in rp.order: arm.pose.bones[n].matrix_basis = Matrix(B[n].tolist())
    bpy.context.view_layer.update()
    for b, (end, j) in pairs.items():
        pb = arm.pose.bones[b]; p = np.array((pb.head if end == 'head' else pb.tail)[:]); err[b].append(np.linalg.norm(p - J[j]) * 100)
    for n, s in rp.last_scale.items(): st.setdefault(n, []).append(s)
allv = np.concatenate([np.array(v) for v in err.values()]); print('joint error vs auto skeleton (cm): mean %.2f p95 %.2f max %.1f' % (allv.mean(), np.percentile(allv, 95), allv.max()))
print({b: round(float(np.mean(v)), 2) for b, v in err.items() if np.mean(v) > 0.3})
print('mean Y-stretch', {n: round(float(np.mean(v)), 2) for n, v in st.items() if n in ('Humerus_L', 'Forearm_L', 'Palm_L', 'Femur_L', 'Tibia_L', 'Sole_L', 'Bone.002', 'Shoulder_L')})

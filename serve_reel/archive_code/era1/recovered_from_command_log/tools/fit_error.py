import sys, numpy as np
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline')
from motion import Motion; from rigpose import RigPoser
M = Motion(SP + '/data', suffix='_ext3'); rp = RigPoser(sys.argv[1] if len(sys.argv) > 1 else SP + '/rig/rig_info_p.json')
pairs = {'Humerus_L': ('head', 'left_shoulder'), 'Forearm_L': ('head', 'left_elbow'), 'Palm_L': ('head', 'left_wrist'), 'Femur_L': ('head', 'left_hip'), 'Tibia_L': ('head', 'left_knee'), 'Heel_L': ('head', 'left_ankle'),
         'Humerus_R': ('head', 'right_shoulder'), 'Forearm_R': ('head', 'right_elbow'), 'Palm_R': ('head', 'right_wrist'), 'Femur_R': ('head', 'right_hip'), 'Tibia_R': ('head', 'right_knee'), 'Heel_R': ('head', 'right_ankle'),
         'Toes_L': ('tail', 'left_foot_index'), 'Toes_R': ('tail', 'right_foot_index'), 'Fingers_L': ('head', 'left_index'), 'Fingers_R': ('head', 'right_index')}
err = {k: [] for k in pairs}
for t in range(0, 92):
    J = M.straighten_left(M.joints(float(t)), float(t)); P = rp.pose(J, look_at=None)
    for b, (end, j) in pairs.items():
        m = P[b]; head = m[:3, 3]; tail = head + m[:3, :3] @ np.array([0, rp.len[b], 0]) if end == 'tail' else head
        err[b].append(np.linalg.norm(tail - J[j]) * 100)
print('joint error mesh-rig vs label (cm): mean / p95 / max')
for b, v in err.items(): v = np.array(v); print(f'{b:10s} {pairs[b][1]:18s} {v.mean():5.1f} {np.percentile(v,95):5.1f} {v.max():5.1f}')
allv = np.concatenate([np.array(v) for v in err.values()]); print('ALL mean %.1f cm  p95 %.1f  max %.1f' % (allv.mean(), np.percentile(allv, 95), allv.max()))
print('rest bone lengths (m):', {k: round(v, 3) for k, v in rp.len.items() if k in ('Humerus_L', 'Forearm_L', 'Femur_L', 'Tibia_L', 'Shoulder_L', 'Pelvic_L')})
J = M.joints(66.0); d = lambda a, b: round(float(np.linalg.norm(J[a] - J[b])), 3)
print('label lengths (m): upper_arm', d('left_shoulder', 'left_elbow'), 'forearm', d('left_elbow', 'left_wrist'), 'thigh', d('left_hip', 'left_knee'), 'shank', d('left_knee', 'left_ankle'), 'shoulder width', d('left_shoulder', 'right_shoulder'), 'hip width', d('left_hip', 'right_hip'))

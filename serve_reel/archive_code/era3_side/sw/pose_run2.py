import cv2, numpy as np, mediapipe as mp, pickle
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
lab = pickle.load(open(SP + '/sw/labels2.pkl', 'rb')); N = 63
pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.3)
L2, L3, VIS = np.full((N, 33, 2), np.nan), np.full((N, 33, 3), np.nan), np.zeros((N, 33)); side = 640; SC = 1.5
for i in range(N):
    im = cv2.imread(SP + '/sw/fr/f%04d.png' % int(lab['S'][i])); P = np.array([lab['skel'][n][i] for n in lab['skel']]); c = P.mean(0)
    x0 = int(np.clip(c[0] - side / 2, 0, 720 - side)); y0 = int(np.clip(c[1] - side / 2 - 60, 0, 1280 - side))
    crop = cv2.resize(im[y0:y0 + side, x0:x0 + side], None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC)
    r = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    if r.pose_landmarks:
        lm = np.array([[l.x, l.y, l.visibility] for l in r.pose_landmarks.landmark]); L2[i] = np.c_[x0 + lm[:, 0] * side, y0 + lm[:, 1] * side]; VIS[i] = lm[:, 2]; L3[i] = np.array([[l.x, l.y, l.z] for l in r.pose_world_landmarks.landmark])
np.savez(SP + '/sw/mp_pose.npz', L2=L2, L3=L3, VIS=VIS); print('detected', int((~np.isnan(L2[:, 0, 0])).sum()), '/', N, 'mean vis', np.nanmean(VIS))
# agreement with the labelled joints (px)
names = {'left_shoulder': 11, 'right_shoulder': 12, 'left_elbow': 13, 'right_elbow': 14, 'left_wrist': 15, 'right_wrist': 16, 'left_hip': 23, 'right_hip': 24, 'left_knee': 25, 'right_knee': 26, 'left_ankle': 27, 'right_ankle': 28}
print({n: round(float(np.nanmedian(np.linalg.norm(L2[:, k] - lab['skel'][n][:N], axis=1))), 1) for n, k in names.items()})

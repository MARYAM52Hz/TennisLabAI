import cv2, numpy as np, mediapipe as mp, json
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
S = np.load(SP + '/auto/stab.npy'); N, H, W, _ = S.shape; boxes = np.load(SP + '/auto/boxes.npy'); sh = np.load(SP + '/auto/shift.npy')
pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=True, min_detection_confidence=0.3)
cx, cy = (boxes[0, 0] + boxes[0, 2]) / 2, (boxes[0, 1] + boxes[0, 3]) / 2; side = 330; SC = 3.0
L2, L3, VIS, SEG = np.full((N, 33, 2), np.nan), np.full((N, 33, 3), np.nan), np.zeros((N, 33)), []
vis = cv2.VideoWriter(SP + '/auto/pose_overlay.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (int(side * 1.6), int(side * 1.6)))
for i in range(N):
    x0, y0 = int(round(cx - side / 2)), int(round(cy - side / 2)); x0 = int(np.clip(x0, 0, W - side)); y0 = int(np.clip(y0, 0, H - side))
    crop = cv2.resize(S[i][y0:y0 + side, x0:x0 + side], None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC)
    r = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)); big = crop.copy()
    if r.pose_landmarks:
        lm = np.array([[l.x, l.y, l.visibility] for l in r.pose_landmarks.landmark]); L2[i] = np.c_[x0 + lm[:, 0] * side, y0 + lm[:, 1] * side]; VIS[i] = lm[:, 2]
        L3[i] = np.array([[l.x, l.y, l.z] for l in r.pose_world_landmarks.landmark])
        hip = (L2[i, 23] + L2[i, 24]) / 2; sho = (L2[i, 11] + L2[i, 12]) / 2; c = (hip + sho) / 2; cx, cy = 0.7 * cx + 0.3 * c[0], 0.7 * cy + 0.3 * c[1]
        for a, b in mp.solutions.pose.POSE_CONNECTIONS: cv2.line(big, tuple(int(v) for v in (L2[i, a] - [x0, y0]) * SC), tuple(int(v) for v in (L2[i, b] - [x0, y0]) * SC), (0, 255, 255), 2)
        for k in range(33): cv2.circle(big, tuple(int(v) for v in (L2[i, k] - [x0, y0]) * SC), 3, (0, 80, 255), -1)
    vis.write(cv2.resize(big, (int(side * 1.6), int(side * 1.6))))
vis.release(); np.savez(SP + '/auto/mp_pose.npz', L2=L2, L3=L3, VIS=VIS)
print('detected', int((~np.isnan(L2[:, 0, 0])).sum()), '/', N, 'mean vis', np.nanmean(VIS))

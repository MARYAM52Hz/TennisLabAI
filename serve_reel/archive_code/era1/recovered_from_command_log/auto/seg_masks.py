import cv2, numpy as np, mediapipe as mp
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
S = np.load(SP + '/auto/stab.npy', mmap_mode='r'); L2 = np.load(SP + '/auto/mp_pose.npz')['L2']; N, H, W, _ = S.shape; bg = cv2.imread(SP + '/auto/background_stab.png')
pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=2, enable_segmentation=True, min_detection_confidence=0.3)
side, SC = 360, 3.0; F0, F1 = 138, 226; M = np.zeros((F1 - F0 + 1, H, W), np.uint8); SEG = np.zeros_like(M)
for k, f in enumerate(range(F0, F1 + 1)):
    pts = L2[f][[0, 11, 12, 23, 24, 27, 28]]; c = np.nanmean(pts, 0); x0 = int(np.clip(c[0] - side / 2, 0, W - side)); y0 = int(np.clip(c[1] - side / 2, 0, H - side))
    crop = cv2.resize(np.array(S[f][y0:y0 + side, x0:x0 + side]), None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC); r = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    seg = np.zeros((H, W), np.float32)
    if r.segmentation_mask is not None: seg[y0:y0 + side, x0:x0 + side] = cv2.resize(r.segmentation_mask, (side, side), interpolation=cv2.INTER_AREA)
    SEG[k] = (np.clip(seg, 0, 1) * 255).astype(np.uint8)
    d = cv2.absdiff(np.array(S[f]), bg).max(2).astype(np.float32); d = cv2.GaussianBlur(d, (0, 0), 1.0); dm = (d > 20).astype(np.uint8); dm = cv2.morphologyEx(dm, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); dm = cv2.dilate(dm, np.ones((5, 5), np.uint8))
    M[k] = (np.clip(seg, 0, 1) * dm * 255).astype(np.uint8)
np.savez_compressed(SP + '/auto/matte_raw.npz', M=M, SEG=SEG, F0=F0)
print('masks', M.shape, 'mean area px', [int((M[i] > 128).sum()) for i in (0, 20, 46, 60, 80)])

"""Segment the player from the raw clip (static camera: median background + difference), then run MediaPipe pose on an upscaled crop."""
import cv2, numpy as np, glob, json, sys, mediapipe as mp
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
files = sorted(glob.glob(SP + '/raw/r*.png')); F = np.stack([cv2.imread(f) for f in files]); N, H, W, _ = F.shape
bg = np.median(F[::3], axis=0).astype(np.uint8); print('frames', N, F.shape)
cv2.imwrite(SP + '/auto/background.png', bg)
boxes = []; masks = []
for i in range(N):
    d = cv2.absdiff(F[i], bg).max(2); m = (d > 38).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    m[:int(H * 0.40)] = 0                                    # ignore sky / trees
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n > 1:
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); x, y, w, h = st[k, :4]; boxes.append((x, y, x + w, y + h)); masks.append(lab == k)
    else: boxes.append(None); masks.append(np.zeros((H, W), bool))
print('missing', sum(b is None for b in boxes)); print('first boxes', boxes[:3], boxes[100], boxes[180])
np.save(SP + '/auto/boxes.npy', np.array([b if b else (0, 0, 0, 0) for b in boxes])); np.save(SP + '/auto/masks.npy', np.packbits(np.stack(masks), axis=-1))

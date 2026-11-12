"""MediaPipe person segmentation on the reference-frame video + background difference, constrained by capsules around the labelled skeleton."""
import numpy as np, cv2, sys, mediapipe as mp
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
from motion_lab import LabMotion
M = LabMotion(); N = 237; f_ = M.K[0, 0]; FR = np.load(SP + '/lab2/frames_ref.npy', mmap_mode='r'); old = np.load(SP + '/lab2/seg_lab.npz')['M']
pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=True, min_detection_confidence=0.3)
exec(open(SP + '/lab2/segment.py').read().split('masks = np.zeros')[0].split('M = LabMotion()')[1].replace('lab = M.lab; H = lab[\'H\']; N = 237; f_ = M.K[0, 0]', ''))      # BONES, caps
side, SC = 380, 3.0; SEG = np.zeros((N, 848, 464), np.uint8); PRI = np.zeros((N, 848, 464), np.uint8); SUR = np.zeros((N, 848, 464), np.uint8); PX = []
for f in range(N):
    J = M.joints(f); px = {n: M.project(J[n])[0][0] for n in J}; z = {n: M.project(J[n])[1][0] for n in J}; pts = np.array([px[n] for n in px if n != 'head']); c = pts.mean(0)
    x0 = int(np.clip(c[0] - side / 2, 0, 464 - 240)); x1 = min(464, x0 + 240); y0 = int(np.clip(c[1] - side / 2, 0, 848 - side)); crop = cv2.resize(np.array(FR[f][y0:y0 + side, x0:x1]), None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC)
    r = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)); seg = np.zeros((848, 464), np.float32)
    if r.segmentation_mask is not None: seg[y0:y0 + side, x0:x1] = cv2.resize(r.segmentation_mask, (x1 - x0, side), interpolation=cv2.INTER_AREA)
    SEG[f] = (np.clip(seg, 0, 1) * 255).astype(np.uint8)
    sure = np.zeros((848, 464), np.uint8); prob = np.zeros((848, 464), np.uint8)
    for a, b, rm in BONES:
        s = f_ / ((z[a] + z[b]) / 2); caps(sure, px[a], px[b], rm * s * 0.6, 255); caps(prob, px[a], px[b], rm * s * 1.9, 255)
    hs = f_ / z['top_spine']; hd = px['head']; caps(sure, px['top_spine'], hd, 0.05 * hs, 255); cv2.circle(prob, tuple(int(v) for v in hd), int(0.17 * hs), 255, -1)
    cv2.fillConvexPoly(prob, np.array([px['left_shoulder'], px['right_shoulder'], px['right_hip'], px['left_hip']], np.int32), 255); PRI[f] = prob; SUR[f] = sure
    if f % 60 == 0: print('mp', f, flush=True)
# background in the reference frame: per-pixel median over the frames where the (dilated) person mask is absent
hole = np.stack([cv2.dilate(((SEG[f] > 60) | (PRI[f] > 0)).astype(np.uint8), np.ones((15, 15), np.uint8)) for f in range(N)]).astype(bool)
bg = np.zeros((848, 464, 3), np.uint8)
for y0 in range(0, 848, 106):
    blk = np.array(FR[:, y0:y0 + 106]).astype(np.float32); hb = hole[:, y0:y0 + 106]; blk[hb] = np.nan; bg[y0:y0 + 106] = np.nan_to_num(np.nanmedian(blk, axis=0), nan=0).astype(np.uint8) if True else 0
cv2.imwrite(SP + '/lab2/bg_ref.png', bg)
A = np.zeros((N, 848, 464), np.uint8)
for f in range(N):
    im = np.array(FR[f]); d = cv2.absdiff(im, bg).max(2).astype(np.float32); d = cv2.GaussianBlur(d, (0, 0), 0.8)
    dm = cv2.morphologyEx((d > 22).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); dm = cv2.dilate(dm, np.ones((3, 3), np.uint8)); dm2 = cv2.dilate((d > 10).astype(np.uint8), np.ones((5, 5), np.uint8))
    seg = SEG[f].astype(np.float32) / 255; a = np.clip((seg - 0.35) / 0.4, 0, 1) * dm * (PRI[f] > 0)
    a = np.maximum(a, (SUR[f] > 0) * dm2 * 1.0); a = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1: a = (lb == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    A[f] = a * 255
np.savez_compressed(SP + '/lab2/seg_lab2.npz', M=A)
sheet = []
for f in (5, 24, 60, 100, 150, 184, 200, 230):
    J = M.joints(f); pts = np.array([M.project(J[n])[0][0] for n in J]); cx, cy = pts.mean(0).astype(int); x0 = int(np.clip(cx - 90, 0, 464 - 180)); y0 = int(np.clip(cy - 130, 0, 848 - 300))
    ov = np.array(FR[f]).copy(); m = A[f] > 0; ov[m] = (0.45 * ov[m] + 0.55 * 255).astype(np.uint8); cv2.drawContours(ov, cv2.findContours(A[f], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], -1, (0, 0, 255), 1)
    sheet.append(cv2.resize(ov[y0:y0 + 300, x0:x0 + 180], None, fx=2, fy=2))
cv2.imwrite(SP + '/lab2/seg_sheet2.png', np.vstack([np.hstack(sheet[:4]), np.hstack(sheet[4:])]))

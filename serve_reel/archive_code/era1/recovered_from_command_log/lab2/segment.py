"""Skeleton-guided segmentation of the real player in the reference camera: raw frame -> warp by H_f -> GrabCut seeded by capsules around the labelled bones."""
import numpy as np, cv2, pickle, sys
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
from motion_lab import LabMotion
M = LabMotion(); lab = M.lab; H = lab['H']; N = 237; f_ = M.K[0, 0]
BONES = [('left_shoulder', 'left_elbow', .045), ('left_elbow', 'left_wrist', .040), ('right_shoulder', 'right_elbow', .045), ('right_elbow', 'right_wrist', .040), ('left_shoulder', 'right_shoulder', .06),
         ('top_spine', 'bottom_spine', .11), ('left_hip', 'right_hip', .07), ('left_shoulder', 'left_hip', .09), ('right_shoulder', 'right_hip', .09),
         ('left_hip', 'left_knee', .075), ('left_knee', 'left_ankle', .055), ('right_hip', 'right_knee', .075), ('right_knee', 'right_ankle', .055),
         ('left_ankle', 'left_heel', .045), ('left_ankle', 'left_foot_index', .045), ('right_ankle', 'right_heel', .045), ('right_ankle', 'right_foot_index', .045)]
def caps(img, p, q, r, v):
    cv2.line(img, tuple(int(round(x)) for x in p), tuple(int(round(x)) for x in q), v, max(1, int(round(2 * r)))); cv2.circle(img, tuple(int(round(x)) for x in p), max(1, int(round(r))), v, -1); cv2.circle(img, tuple(int(round(x)) for x in q), max(1, int(round(r))), v, -1)
masks = np.zeros((N, 848, 464), np.uint8); frames_ref = np.zeros((N, 848, 464, 3), np.uint8)
for f in range(N):
    im = cv2.warpPerspective(cv2.imread(SP + '/raw/r%04d.png' % (f + 1)), H[f], (464, 848), flags=cv2.INTER_CUBIC); frames_ref[f] = im
    J = M.joints(f); px = {n: M.project(J[n])[0][0] for n in J}; z = {n: M.project(J[n])[1][0] for n in J}
    pts = np.array([px[n] for n in px if n != 'head']); x0, y0 = np.floor(pts.min(0) - 55).astype(int); x1, y1 = np.ceil(pts.max(0) + 55).astype(int); x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, 464), min(y1, 848)
    sure = np.zeros((848, 464), np.uint8); prob = np.zeros((848, 464), np.uint8)
    for a, b, rm in BONES:
        s = f_ / ((z[a] + z[b]) / 2); caps(sure, px[a], px[b], rm * s * 0.55, 255); caps(prob, px[a], px[b], rm * s * 1.7, 255)
    # head: above top_spine along the spine direction
    hs = f_ / z['top_spine']; hd = px['head']; caps(sure, px['top_spine'], hd, 0.05 * hs, 255); cv2.circle(prob, tuple(int(v) for v in hd), int(0.16 * hs), 255, -1); cv2.circle(sure, tuple(int(v) for v in hd), int(0.06 * hs), 255, -1)
    torso = np.array([px['left_shoulder'], px['right_shoulder'], px['right_hip'], px['left_hip']], np.int32); cv2.fillConvexPoly(prob, torso, 255); cv2.fillConvexPoly(sure, cv2.erode(np.zeros((848, 464), np.uint8), None) + 0 if False else torso, 255) if False else None
    m = np.full((848, 464), cv2.GC_BGD, np.uint8); m[prob > 0] = cv2.GC_PR_FGD; m[sure > 0] = cv2.GC_FGD
    ring = cv2.dilate(prob, np.ones((25, 25), np.uint8)); m[(ring > 0) & (prob == 0)] = cv2.GC_PR_BGD
    sub = m[y0:y1, x0:x1].copy(); bgd = np.zeros((1, 65)); fgd = np.zeros((1, 65))
    try: cv2.grabCut(im[y0:y1, x0:x1], sub, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
    except cv2.error: pass
    fg = ((sub == cv2.GC_FGD) | (sub == cv2.GC_PR_FGD)).astype(np.uint8); out = np.zeros((848, 464), np.uint8); out[y0:y1, x0:x1] = fg
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); n, lb, st, _ = cv2.connectedComponentsWithStats(out)
    if n > 1: keep = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); out = (lb == keep).astype(np.uint8)
    masks[f] = out * 255
    if f % 40 == 0: print('seg', f, flush=True)
np.savez_compressed(SP + '/lab2/seg_lab.npz', M=masks); np.save(SP + '/lab2/frames_ref.npy', frames_ref)
sheet = []
for f in (5, 24, 60, 100, 150, 184, 200, 230):
    J = M.joints(f); pts = np.array([M.project(J[n])[0][0] for n in J]); cx, cy = pts.mean(0).astype(int); x0 = int(np.clip(cx - 90, 0, 464 - 180)); y0 = int(np.clip(cy - 130, 0, 848 - 300))
    im = frames_ref[f].copy(); ov = im.copy(); ov[masks[f] > 0] = (0.5 * ov[masks[f] > 0] + 0.5 * np.array([255, 255, 255])).astype(np.uint8); cv2.drawContours(ov, cv2.findContours(masks[f], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], -1, (0, 0, 255), 1)
    sheet.append(cv2.resize(ov[y0:y0 + 300, x0:x0 + 180], None, fx=2, fy=2))
cv2.imwrite(SP + '/lab2/seg_sheet.png', np.vstack([np.hstack(sheet[:4]), np.hstack(sheet[4:])]))

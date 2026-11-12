import cv2, numpy as np, glob
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
files = sorted(glob.glob(SP + '/raw/r*.png')); G = [cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in files]; N = len(G); H, W = G[0].shape
win = cv2.createHanningWindow((W, 330 - 150), cv2.CV_32F); ref = G[0][150:330]
# far field (trees / stands / sky) = camera rotation; ECC translation refine on edges of the court region excluding player area is avoided
sh = np.array([cv2.phaseCorrelate(ref, g[150:330], win)[0] for g in G]); from scipy.signal import medfilt
for c in range(2):                                               # reject phase-correlation outliers (birds / foliage), keep the smooth hand-held drift
    ok = np.abs(sh[:, c] - medfilt(sh[:, c], 15)) < 2.5; sh[:, c] = np.interp(np.arange(N), np.where(ok)[0], sh[ok, c])
np.save(SP + '/auto/shift.npy', sh)       # content moves by +sh relative to frame 0
S = []
for i, f in enumerate(files):
    im = cv2.imread(f); A = np.float32([[1, 0, -sh[i, 0]], [0, 1, -sh[i, 1]]]); S.append(cv2.warpAffine(im, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE))
S = np.stack(S); bg = np.median(S[::2], axis=0).astype(np.uint8); cv2.imwrite(SP + '/auto/background_stab.png', bg); np.save(SP + '/auto/stab.npy', S)
print('shift range x', sh[:, 0].min(), sh[:, 0].max(), 'y', sh[:, 1].min(), sh[:, 1].max())
boxes = []; masks = []
for i in range(N):
    d = cv2.absdiff(S[i], bg).max(2).astype(np.float32); d = cv2.GaussianBlur(d, (0, 0), 1.2); m = (d > 30).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8)); m[:int(H * 0.38)] = 0
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n > 1:
        score = st[1:, cv2.CC_STAT_AREA].astype(float)
        if boxes: pc = np.array([(boxes[-1][0] + boxes[-1][2]) / 2, (boxes[-1][1] + boxes[-1][3]) / 2]); score = score / (1 + np.linalg.norm(cen[1:] - pc, axis=1) / 40.0)
        k = 1 + np.argmax(score); x, y, w, h = st[k, :4]; boxes.append((x, y, x + w, y + h)); masks.append(lab == k)
    else: boxes.append((0, 0, 1, 1)); masks.append(np.zeros((H, W), bool))
boxes = np.array(boxes); np.save(SP + '/auto/boxes.npy', boxes); print(boxes[::20].tolist())
vis = [np.hstack([S[i], (S[i] * 0.4 + 0.6 * np.stack([masks[i] * 255] * 3, -1)).astype(np.uint8)])[330:700] for i in (1, 60, 100, 150, 190)]
cv2.imwrite(SP + '/auto/seg_check.png', np.hstack(vis))

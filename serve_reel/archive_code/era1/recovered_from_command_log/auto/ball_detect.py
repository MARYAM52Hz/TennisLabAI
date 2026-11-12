import cv2, numpy as np
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
S = np.load(SP + '/auto/stab.npy'); bg = cv2.imread(SP + '/auto/background_stab.png'); N, H, W, _ = S.shape
cand = []
for i in range(N):
    hsv = cv2.cvtColor(S[i], cv2.COLOR_BGR2HSV); h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    m = ((h >= 24) & (h <= 44) & (s >= 90) & (v >= 130)).astype(np.uint8)          # optic-yellow
    d = cv2.absdiff(S[i], bg).max(2) > 25; m = m & d.astype(np.uint8); m[:5] = 0
    n, lab, st, cen = cv2.connectedComponentsWithStats(m); c = []
    for k in range(1, n):
        a = st[k, cv2.CC_STAT_AREA]
        if 2 <= a <= 90 and max(st[k, 2], st[k, 3]) <= 14: c.append((cen[k][0], cen[k][1], a))
    cand.append(c)
print('frames with candidates', sum(len(c) > 0 for c in cand), '/', N, ' mean cand', np.mean([len(c) for c in cand]))
import pickle; pickle.dump(cand, open(SP + '/auto/ball_cand.pkl', 'wb'))
for i in range(0, N, 6): print(i, [(round(x), round(y), a) for x, y, a in cand[i]][:4])

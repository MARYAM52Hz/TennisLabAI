import numpy as np, pickle
from scipy.optimize import least_squares
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
cand = pickle.load(open(SP + '/auto/ball_cand.pkl', 'rb')); cam = np.load(SP + '/auto/camera_raw.npz'); K, R, C = cam['K'], cam['R'], cam['cam']; G = np.array([0, 0, -9.81]); DT = 1 / 30.
pl = np.load(SP + '/auto/player3d_raw_s+1.npz'); X = pl['X']; names = list(pl['names']); I = {n: i for i, n in enumerate(names)}
def proj(P):
    Xc = (P - C) @ R.T; return np.c_[K[0, 0] * Xc[:, 0] / Xc[:, 2] + K[0, 2], K[1, 1] * Xc[:, 1] / Xc[:, 2] + K[1, 2]]
def fit(f0, f1, name):
    fr = [t for t in range(f0, f1 + 1) if cand[t]]; ts = np.array(fr) * DT; t0 = f0 * DT
    ref = X[f0, I['right_wrist']]                                   # start near the tossing hand (left hand for a right-handed server) -> use mid of wrists
    ref = (X[f0, I['left_wrist']] + X[f0, I['right_wrist']]) / 2
    def traj(p, tt): return p[:3] + p[3:6] * (tt - t0)[:, None] + 0.5 * G * ((tt - t0) ** 2)[:, None]
    def res(p):
        uv = proj(traj(p, ts)); r = []
        for k, t in enumerate(fr):
            c = np.array([[x, y] for x, y, a in cand[t]]); dd = np.linalg.norm(c - uv[k], axis=1); r += list((c[np.argmin(dd)] - uv[k]) / 1.5)
        return np.array(r)
    best = None
    for vz in (3, 6, 9):
        for dy in (-2, 0, 2):
            p0 = np.r_[ref + [0, dy, 0.5], [0, 0, vz]]; s = least_squares(res, p0, loss='soft_l1', f_scale=2.0)
            if best is None or s.cost < best.cost: best = s
    p = best.x; rr = np.abs(res(p)).reshape(-1, 2) * 1.5; print(name, 'frames', fr[0], fr[-1], 'n', len(fr), 'rms px %.2f' % np.sqrt((rr ** 2).mean()), 'start', p[:3].round(2), 'v', p[3:].round(2))
    zap = p[2] + p[5] ** 2 / 19.62 if p[5] > 0 else p[2]; print('  apex height %.2f m' % zap)
    return p, t0, fr
out = {}
for nm, (a, b) in {'A': (0, 28), 'B': (150, 192)}.items(): out[nm] = fit(a, b, nm)
pickle.dump(out, open(SP + '/auto/ball_fit_raw.pkl', 'wb'))

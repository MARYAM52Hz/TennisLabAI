"""Physically-constrained ball path: two ballistic arcs (release->contact, contact->bounce) sharing the contact point.
Time axis: tau_k = k - eps*(k odd) frames (uneven frame timing), physical seconds = kappa * tau / 30.
usage: python3 -I ball_fit.py data_dir [--eps .3] [--kappa 1.45] [--scan]"""
import sys, json, argparse, numpy as np
from scipy.optimize import least_squares
ap = argparse.ArgumentParser(); ap.add_argument('data'); ap.add_argument('--eps', type=float, default=.3); ap.add_argument('--kappa', type=float, default=1.45)
ap.add_argument('--scan', action='store_true'); ap.add_argument('--rel', type=int, default=58); ap.add_argument('--out', default='ball3d_phys.npz'); a = ap.parse_args(); D = a.data
c = np.load(D + '/camera.npz'); K, R, C = c['K'], c['R'], c['cam']; fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
d = np.load(D + '/labels2d.npz'); ball = d['B_ball_center'].astype(float); g = 9.81; RB = 0.0335; N = len(ball)
def proj(P): pc = (P - C) @ R.T; return np.stack([fx * pc[:, 0] / pc[:, 2] + cx, fy * pc[:, 1] / pc[:, 2] + cy], 1)
def ray(p): v = np.array([(p[0] - cx) / fx, (p[1] - cy) / fy, 1.0]); w = R.T @ v; return w / np.linalg.norm(w)
tau = lambda k: (np.asarray(k, float) - np.where(np.asarray(k) % 2 == 1, a.eps, 0.0))
TC, TB = 74, 87
dd = ray(ball[TB]); B87 = C + dd * ((RB - C[2]) / dd[2])
def solve(kappa, rel=a.rel):
    sec = lambda k: kappa * tau(k) / 30.0; tc = sec(TC)
    f1 = np.arange(rel, TC); f2 = np.arange(TC + 1, TB + 1)
    def path(q, k):
        Pc, V1, V2 = q[:3], q[3:6], q[6:9]; k = np.asarray(k); t = sec(k) - tc; V = np.where((k <= TC)[:, None], V1, V2)
        return Pc + V * t[:, None] - 0.5 * g * (t ** 2)[:, None] * np.array([0, 0, 1.0])
    def res(q):
        r1 = (proj(path(q, f1)) - ball[f1]).ravel(); r2 = (proj(path(q, f2)) - ball[f2]).ravel(); rb = (path(q, [TB])[0] - B87) * 40.0
        return np.r_[r1, r2, rb]
    best = None
    for vy in (-1.0, 2.0, 8.0):
        q0 = np.r_[[1.1, -11.7, 2.6], [0, 0, 0], [0, (B87[1] + 11.7) / 0.45, -4]]; q0[3:6] = [0, vy * 0.2, -1.0]
        r = least_squares(res, q0)
        if best is None or r.cost < best.cost: best = r
    n1, n2 = 2 * len(f1), 2 * len(f2)
    return best, path, f1, f2, np.sqrt(np.mean(best.fun[:n1] ** 2)), np.sqrt(np.mean(best.fun[n1:n1 + n2] ** 2))
if a.scan:
    for kp in np.arange(1.0, 1.95, 0.1):
        r, path, f1, f2, e1, e2 = solve(kp); print('kappa %.2f  rms flight1 %.2f flight2 %.2f  contact P %s  V1 %s  apex z %.2f' % (kp, e1, e2, r.x[:3].round(2), r.x[3:6].round(2), path(r.x, np.arange(a.rel, TC)).T[2].max()))
    sys.exit()
r, path, f1, f2, e1, e2 = solve(a.kappa)
print('kappa', a.kappa, 'rms', round(e1, 2), round(e2, 2), 'contact', r.x[:3].round(3), 'V1', r.x[3:6].round(2), 'V2', r.x[6:9].round(2), 'speed after contact %.1f m/s' % np.linalg.norm(r.x[6:9]))
k_all = np.arange(a.rel, TB + 1); P = np.full((N, 3), np.nan); P[a.rel:TB + 1] = path(r.x, k_all)
np.savez(D + '/' + a.out, P=P, q=r.x, kappa=a.kappa, eps=a.eps, rel=a.rel, contact_frame=TC, bounce=B87)

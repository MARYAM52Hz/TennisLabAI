"""Continuous-time version of the label-driven motion (cubic-spline interpolation between the 30 fps samples) for slow motion, with the racket made consistent
at the two contacts: the string bed faces the launch direction, the racket axis is perpendicular to it, and the ball meets the string-bed centre."""
import numpy as np, pickle, sys
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.spatial.transform import Rotation as Rot
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0, SP + '/lab2')
from motion_lab import LabMotion, nrm, DT
import ball_lab as BL
class Motion2(LabMotion):
    def __init__(self):
        super().__init__(); T = self.T; bl = pickle.load(open(SP + '/lab2/ball3d.pkl', 'rb'))
        self.tcs = {'A': bl['A']['f0'] + bl['A']['tc'] / DT, 'B': bl['B2']['f0'] + bl['B2']['tc'] / DT}; self.launch = {'A': nrm(bl['A']['v1']), 'B': nrm(bl['B2']['v1'])}
        butt = self.butt.copy(); Rr = self.Rr.copy(); ball = self.ball3.copy(); ok = self.ball_ok; ball_adj = {}
        for k in 'AB':
            tc = self.tcs[k]; v = self.launch[k]
            for f in range(int(tc) - 8, int(tc) + 10):
                w = np.exp(-((f - tc) / 3.0) ** 4); a = Rr[f][:, 1]; n = Rr[f][:, 2]
                ap = nrm(a - np.dot(a, v) * v); a2 = nrm((1 - w) * a + w * ap)
                nt = nrm(v - np.dot(v, a2) * a2); nt = nt if np.dot(nt, n) >= 0 else -nt; n2 = (1 - w) * n + w * nt; n2 = nrm(n2 - np.dot(n2, a2) * a2); x2 = np.cross(a2, n2)
                Rr[f] = np.column_stack([x2, a2, n2])
            head = lambda f: butt[f] + 0.52 * Rr[f][:, 1]
            ball_adj[k] = (tc, head)
        for f in range(T): butt[f] = self.X[f, self.I['right_wrist']] - 0.05 * Rr[f][:, 1]          # the grip sits in the hand
        self.butt2, self.Rr2, self.ball2 = butt, Rr, ball
        self.butt2, self.Rr2, self.ball2 = butt, Rr, ball; fr = np.arange(T)
        self.sp_J = {n: CubicSpline(fr, self.X[:, i]) for n, i in self.I.items()}
        self.sp_butt = CubicSpline(fr, butt); q = Rot.from_matrix(Rr).as_quat()
        for i in range(1, T):
            if np.dot(q[i], q[i - 1]) < 0: q[i] = -q[i]
        self.sp_q = CubicSpline(fr, q); self.ball_runs = []
        i = 0
        while i < T:
            if ok[i]:
                j = i
                while j + 1 < T and ok[j + 1]: j += 1
                if j - i >= 2: self.ball_runs.append((i, j, PchipInterpolator(fr[i:j + 1], ball[i:j + 1], axis=0)))
                i = j + 1
            else: i += 1
        self.butt, self.Rr = butt, Rr
        for k in 'AB':                                              # ball meets the string-bed centre exactly at the (fractional) contact instant
            tc = self.tcs[k]; delta = self.head_at(tc) - self.ball(tc)
            for f in range(int(tc) - 8, int(tc) + 10):
                if ok[f]: ball[f] = ball[f] + delta * np.exp(-((f - tc) / 3.0) ** 4)
        self.ball_runs = []; i = 0
        while i < T:
            if ok[i]:
                j = i
                while j + 1 < T and ok[j + 1]: j += 1
                if j - i >= 2: self.ball_runs.append((i, j, PchipInterpolator(fr[i:j + 1], ball[i:j + 1], axis=0)))
                i = j + 1
            else: i += 1
        self.head_pts = np.array([butt[f] + 0.52 * Rr[f][:, 1] for f in range(T)])
    def jf(self, n, f):
        f = float(np.clip(f, 0, self.T - 1))
        if n == 'head': ts, bs = self.jf('top_spine', f), self.jf('bottom_spine', f); return ts + 0.21 * nrm(nrm(ts - bs) + np.array([0, 0, 0.6]))
        return self.sp_J[n](f)
    def racket(self, tau):
        f = float(np.clip(tau, 0, self.T - 1)); q = self.sp_q(f); q = q / np.linalg.norm(q); return self.sp_butt(f), Rot.from_quat(q).as_matrix(), None
    def ball(self, tau):
        f = float(tau)
        for a, b, sp in self.ball_runs:
            if a <= f <= b: return sp(f)
        return np.array([0, 0, -50.0])
    def head_at(self, tau): b, R, _ = self.racket(tau); return b + 0.52 * R[:, 1]
if __name__ == '__main__':
    M = Motion2()
    for k in 'AB':
        tc = M.tcs[k]; v = M.launch[k]; b, R, _ = M.racket(tc); print(k, 'tc %.2f' % tc, 'head-ball %.2f' % np.linalg.norm(M.head_at(tc) - M.ball(tc)), 'normal.launch %.2f' % np.dot(R[:, 2], v), 'axis.launch %.2f' % np.dot(R[:, 1], v), 'head', M.head_at(tc).round(2), 'wrist', M.jf('right_wrist', tc).round(2), 'grip-wrist dist %.2f' % np.linalg.norm(b - M.jf('right_wrist', tc)))

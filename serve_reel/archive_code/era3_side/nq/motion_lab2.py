"""Motion2 for IMG_7122 (side view, one serve; 63 unique frames at 30 fps)."""
import numpy as np, pickle, sys, cv2
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.spatial.transform import Rotation as Rot, Slerp
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0, SP + '/sw')
DT = 1 / 30.
def nrm(v): return v / (np.linalg.norm(v) + 1e-12)
def ell_pts(cx, cy, rx, ry, rot, n=24):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); a = np.radians(rot); x = rx * np.cos(t); y = ry * np.sin(t)
    return np.c_[cx + x * np.cos(a) - y * np.sin(a), cy + x * np.sin(a) + y * np.cos(a)]
def cv2_fit(P): P = np.asarray(P, np.float32).reshape(-1, 1, 2); (cx, cy), (w, h), ang = cv2.fitEllipse(P); return (cx, cy), (w, h), ang
def ellipse_dist(e1, e2):
    def pts(e, n=24):
        (cx, cy), (w, h), ang = e; t = np.linspace(0, 2 * np.pi, n, endpoint=False); a = np.radians(ang); x = w / 2 * np.cos(t); y = h / 2 * np.sin(t); return np.c_[cx + x * np.cos(a) - y * np.sin(a), cy + x * np.sin(a) + y * np.cos(a)]
    A, B = pts(e1), pts(e2); d = np.linalg.norm(A[:, None] - B[None], axis=-1); return 0.5 * (d.min(1).mean() + d.min(0).mean())
class LabMotion:
    T = 63; BALL0 = 0; BALL1 = 33
    def __init__(self):
        cam = np.load(SP + '/sw/camera.npz'); self.K, self.R_cam, self.C_cam = cam['K'], cam['R'], cam['cam']; self.rlen = 0.685; self.face_semi = (0.14, 0.165)
        self.lab = pickle.load(open(SP + '/sw/lab2.pkl', 'rb'))
        p = np.load(SP + '/sw/player3d_anch.npz', allow_pickle=True); X = gaussian_filter1d(p['X'], 0.9, axis=0, mode='nearest'); nm = [str(n) for n in p['names']]; self.I = {n: i for i, n in enumerate(nm)}; self.X = X; self.names = nm + ['head']
        try: self.__dict__.update(pickle.load(open(SP + '/nq/motion_nl.pkl', 'rb')))
        except Exception: self.build()
    def ray(self, u, v): return self.R_cam.T @ np.array([(u - self.K[0, 2]) / self.K[0, 0], (v - self.K[1, 2]) / self.K[0, 0], 1.0])
    def project(self, P):
        Xc = (np.atleast_2d(P) - self.C_cam) @ self.R_cam.T; return np.c_[self.K[0, 0] * Xc[:, 0] / Xc[:, 2] + self.K[0, 2], self.K[0, 0] * Xc[:, 1] / Xc[:, 2] + self.K[1, 2]], Xc[:, 2]
    def jf0(self, n, f):
        f = float(np.clip(f, 0, self.T - 1)); a = int(np.floor(f)); b = min(a + 1, self.T - 1); w = f - a
        if n == 'head': ts, bs = self.jf0('top_spine', f), self.jf0('bottom_spine', f); return ts + 0.21 * nrm(nrm(ts - bs) + np.array([0, 0, 0.6]))
        i = self.I[n]; return (1 - w) * self.X[a, i] + w * self.X[b, i]
    def build(self):
        import ball as BL
        T = self.T; lab = self.lab; Kf = self.K[0, 0]; bl = pickle.load(open(SP + '/sw/ball3d.pkl', 'rb'))['S']; self.tc = float(BL.frame_of(BL.T_of(bl['f0']) + bl['tc'])); self.launch_v = nrm(bl['v1'])
        ball3 = np.zeros((T, 3)); ok = np.zeros(T, bool)
        for f in range(self.BALL0, self.BALL1 + 1):
            u, v = lab['ball'][f][0], lab['ball'][f][1]; d = self.ray(u, v)
            W = self.jf0('left_wrist', f); wd = ((W - self.C_cam) @ self.R_cam.T)[2] - 0.03
            if f >= bl['f0']:
                md = BL.project(BL.positions(bl, [f]))[1][0]; s_ = float(np.clip((f - 3) / 4.0, 0, 1)); s_ = s_ * s_ * (3 - 2 * s_); depth = (1 - s_) * wd + s_ * md      # hand depth -> fitted depth after the release
            else: depth = wd
            ball3[f] = self.C_cam + d * depth; ok[f] = True
        fb = np.arange(self.BALL1 + 1, T); Pm = BL.positions(bl, fb); zb = np.where(Pm[:, 2] < 0.06)[0]; last = int(fb[zb[0]]) + 3 if len(zb) else int(fb[-1])             # after the last label the ball has left the picture: model flight up to the bounce
        # (side-view reel: no model flight after the last labelled ball position)
        self.ball3, self.ball_ok = ball3, ok
        D = 0.55; head = np.zeros((T, 3)); axis = np.zeros((T, 3)); prev = None; lams = np.zeros(T); dns = np.zeros((T, 3)); faces = []
        for f in range(T):
            cx, cy, rx, ry, rot = lab['face'][f]; faces.append((cx, cy, rx, ry, rot)); W = self.jf0('right_wrist', f); d = self.ray(cx, cy); dn = d / np.linalg.norm(d)
            w0 = W - self.C_cam; b_ = np.dot(dn, w0); disc = b_ * b_ - (np.dot(w0, w0) - D * D)
            if disc > 0:
                s = np.sqrt(disc); cands = [b_ - s, b_ + s]
                if prev is None: zs = Kf * 0.165 / max(rx, ry); key = lambda l: abs(((self.C_cam + dn * l - self.C_cam) @ self.R_cam.T)[2] - zs)
                else: key = lambda l: np.linalg.norm(self.C_cam + dn * l - prev)
                lam = min(cands, key=key)
            else: lam = b_
            H = self.C_cam + dn * lam; head[f] = H; prev = H; lams[f] = lam; dns[f] = dn; axis[f] = nrm(H - W) if np.linalg.norm(H - W) > 0.05 else np.array([0, 0, 1.0])
        axis = np.array([nrm(v) for v in gaussian_filter1d(axis, 1.0, axis=0, mode='nearest')]); lams = gaussian_filter1d(lams, 1.2, mode='nearest'); head = self.C_cam + dns * lams[:, None]
        NPH = 90; phis = np.arange(NPH) * np.pi / NPH; cost = np.zeros((T, NPH)); sm = np.linspace(0, 2 * np.pi, 20, endpoint=False)
        for f in range(T):
            a = axis[f]; e1 = nrm(np.cross(a, [0, 0, 1.0]) if abs(a[2]) < 0.95 else np.cross(a, [1.0, 0, 0])); e2 = np.cross(a, e1); cx, cy, rx, ry, rot = faces[f]
            (ex, ey), (w_, h_), ang = cv2_fit(ell_pts(cx, cy, rx, ry, rot))
            for k, ph in enumerate(phis):
                bb = np.cos(ph) * e1 + np.sin(ph) * e2; pts = head[f] + self.face_semi[0] * np.cos(sm)[:, None] * bb + self.face_semi[1] * np.sin(sm)[:, None] * a
                uv, _ = self.project(pts); cost[f, k] = ellipse_dist(cv2_fit(uv), ((ex, ey), (w_, h_), ang))
        dp = cost[0].copy(); bp = np.zeros((T, NPH), int); idx = np.arange(NPH); dd = np.abs(idx[:, None] - idx[None, :]); dd = np.minimum(dd, NPH - dd) * (np.pi / NPH); trans = (dd / 0.35) ** 2 * 6.0
        for f in range(1, T): tot = dp[None, :] + trans; bp[f] = tot.argmin(1); dp = cost[f] + tot.min(1)
        path = np.zeros(T, int); path[-1] = int(dp.argmin())
        for f in range(T - 1, 0, -1): path[f - 1] = bp[f][path[f]]
        self.roll_cost = cost[np.arange(T), path]; Rs = []
        for f in range(T):
            a = axis[f]; e1 = nrm(np.cross(a, [0, 0, 1.0]) if abs(a[2]) < 0.95 else np.cross(a, [1.0, 0, 0])); e2 = np.cross(a, e1); ph = phis[path[f]]; bb = np.cos(ph) * e1 + np.sin(ph) * e2; Rs.append([bb, a, nrm(np.cross(bb, a))])
        for f in range(1, T):
            if np.dot(Rs[f][0], Rs[f - 1][0]) + np.dot(Rs[f][2], Rs[f - 1][2]) < 0: Rs[f][0], Rs[f][2] = -Rs[f][0], -Rs[f][2]
        M = np.array([np.column_stack(r) for r in Rs]); q = Rot.from_matrix(M).as_quat()
        for f in range(1, T):
            if np.dot(q[f], q[f - 1]) < 0: q[f] = -q[f]
        q = gaussian_filter1d(q, 0.8, axis=0, mode='nearest'); q /= np.linalg.norm(q, axis=1, keepdims=True); self.Rr = Rot.from_quat(q).as_matrix()
        self.head_c = head; self.axis = axis; self.butt = head - 0.49 * np.array([self.Rr[f][:, 1] for f in range(T)]); self.head_px = np.array([[x[0], x[1]] for x in faces])
        pickle.dump(dict(Rr=self.Rr, butt=self.butt, head_c=self.head_c, axis=self.axis, ball3=ball3, ball_ok=ok, head_px=self.head_px, roll_cost=self.roll_cost, tc=self.tc, launch_v=self.launch_v), open(SP + '/nq/motion_nl.pkl', 'wb'))
class Motion2(LabMotion):
    def __init__(self):
        super().__init__(); T = self.T; self.tcs = {'A': self.tc, 'B': self.tc}; self.launch = {'A': self.launch_v, 'B': self.launch_v}
        butt = self.butt.copy(); Rr = self.Rr.copy(); ball = self.ball3.copy(); ok = self.ball_ok; tc = self.tc; v = self.launch_v
        for f in range(int(tc) - 8, int(tc) + 10):                              # at contact the string bed faces the launch direction, racket axis perpendicular to it
            w = np.exp(-((f - tc) / 0.6) ** 4); a = Rr[f][:, 1]; n = Rr[f][:, 2]; ap = nrm(a - np.dot(a, v) * v); a2 = nrm((1 - w) * a + w * ap)
            nt = nrm(v - np.dot(v, a2) * a2); nt = nt if np.dot(nt, n) >= 0 else -nt; n2 = (1 - w) * n + w * nt; n2 = nrm(n2 - np.dot(n2, a2) * a2); Rr[f] = np.column_stack([np.cross(a2, n2), a2, n2])
        for f in range(T): butt[f] = self.X[f, self.I['right_wrist']] + 0.06 * Rr[f][:, 1]
        fr = np.arange(T); self.sp_J = {n: CubicSpline(fr, self.X[:, i]) for n, i in self.I.items()}; self.sp_butt = CubicSpline(fr, butt); q = Rot.from_matrix(Rr).as_quat()
        for i in range(1, T):
            if np.dot(q[i], q[i - 1]) < 0: q[i] = -q[i]
        self.sp_q = CubicSpline(fr, q); self.butt, self.Rr = butt, Rr
        delta = self.head_at(tc) - self._ball_spline(ball, ok, tc)                                   # ball meets the string-bed centre exactly at the contact instant
        nn = self.racket(tc)[1][:, 2]; delta = np.dot(delta, nn) * nn                                  # only along the string-bed normal: the ball touches the strings, its in-plane offset stays as labelled
        for f in range(int(tc) - 8, int(tc) + 10):
            if ok[f]: ball[f] = ball[f] + delta * np.exp(-((f - tc) / 0.6) ** 4)
        self.ball_runs = self._runs(ball, ok); self.head_pts = np.array([butt[f] + 0.49 * Rr[f][:, 1] for f in range(T)])
    def _runs(self, ball, ok):
        runs = []; i = 0; T = self.T; fr = np.arange(T)
        while i < T:
            if ok[i]:
                j = i
                while j + 1 < T and ok[j + 1]: j += 1
                if j - i >= 2: runs.append((i, j, PchipInterpolator(fr[i:j + 1], ball[i:j + 1], axis=0)))
                i = j + 1
            else: i += 1
        return runs
    def _ball_spline(self, ball, ok, f):
        for a, b, sp in self._runs(ball, ok):
            if a <= f <= b: return sp(f)
        return np.array([0, 0, -50.0])
    def jf(self, n, f):
        f = float(np.clip(f, 0, self.T - 1))
        if n == 'head': ts, bs = self.jf('top_spine', f), self.jf('bottom_spine', f); return ts + 0.21 * nrm(nrm(ts - bs) + np.array([0, 0, 0.6]))
        return self.sp_J[n](f)
    def joints(self, tau): return {n: self.jf(n, tau) for n in self.names}
    def straighten_left(self, J, tau): return J
    def racket(self, tau):
        f = float(np.clip(tau, 0, self.T - 1)); q = self.sp_q(f); q = q / np.linalg.norm(q); return self.sp_butt(f), Rot.from_quat(q).as_matrix(), None
    def ball(self, tau):
        f = float(tau)
        for a, b, sp in self.ball_runs:
            if a <= f <= b: return sp(f)
        return np.array([0, 0, -50.0])
    def head_at(self, tau): b, R, _ = self.racket(tau); return b + 0.49 * R[:, 1]
if __name__ == '__main__':
    M = Motion2(); tc = M.tc
    print('tc %.2f' % tc, 'head-ball %.3f' % np.linalg.norm(M.head_at(tc) - M.ball(tc)), 'normal.launch %.2f' % np.dot(M.racket(tc)[1][:, 2], M.launch_v), 'roll cost mean %.2f max %.2f px' % (M.roll_cost.mean(), M.roll_cost.max()))
    e = [np.linalg.norm(M.project(M.head_pts[f])[0][0] - M.head_px[f]) for f in range(M.T)]; print('racket head reproj mean %.1f max %.1f px' % (np.mean(e), np.max(e)))
    lab = M.lab; eb = []
    for f in range(M.BALL0, M.BALL1 + 1):
        b = M.ball(f)
        if b[2] > -10: eb.append(np.linalg.norm(M.project(b)[0][0] - lab['ball'][f][:2]))
    print('ball reproj mean %.1f max %.1f px' % (np.mean(eb), np.max(eb)))
    for f in (50, 58, 66, 70, 74, 76, 80): print(f, 'ball', M.ball(f).round(2), 'racket head', M.head_at(f).round(2), 'wrist', M.jf('right_wrist', f).round(2))

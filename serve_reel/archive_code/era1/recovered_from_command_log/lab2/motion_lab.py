"""LabMotion: everything the scene/trail code needs, built from the transferred CVAT labels.
joints(tau) -> 3D joints (+derived head); racket(tau) -> (butt, R[x,y=axis,z=normal], None); ball(tau) -> 3D point (z=-50 when hidden); pixel paths for trails."""
import numpy as np, pickle, sys
from scipy.ndimage import gaussian_filter1d
from scipy.spatial.transform import Rotation as Rot, Slerp
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
DT = 1 / 30.
def nrm(v): return v / (np.linalg.norm(v) + 1e-12)
class LabMotion:
    def __init__(self, build=False):
        cam = np.load(SP + '/lab2/camera_lab.npz'); self.K, self.R_cam, self.C_cam = cam['K'], cam['R'], cam['cam']; self.T = 237; self.rlen = 0.685; self.face_semi = (0.14, 0.165)
        self.lab = pickle.load(open(SP + '/lab2/labels_ref.pkl', 'rb'))
        p = np.load(SP + '/lab2/player3d_lab.npz'); X = gaussian_filter1d(p['X'], 0.9, axis=0, mode='nearest'); nm = [str(n) for n in p['names']]; self.I = {n: i for i, n in enumerate(nm)}; self.X = X
        self.names = nm + ['head']
        if build or True:
            try: d = pickle.load(open(SP + '/lab2/motion_lab.pkl', 'rb')); self.__dict__.update(d)
            except Exception: pass
    # ---------- helpers
    def ray(self, u, v): return self.R_cam.T @ np.array([(u - self.K[0, 2]) / self.K[0, 0], (v - self.K[1, 2]) / self.K[0, 0], 1.0])      # world direction with camera-z = 1
    def project(self, P):
        Xc = (np.atleast_2d(P) - self.C_cam) @ self.R_cam.T; return np.c_[self.K[0, 0] * Xc[:, 0] / Xc[:, 2] + self.K[0, 2], self.K[0, 0] * Xc[:, 1] / Xc[:, 2] + self.K[1, 2]], Xc[:, 2]
    def jf(self, n, f):
        f = float(np.clip(f, 0, self.T - 1)); a = int(np.floor(f)); b = min(a + 1, self.T - 1); w = f - a
        if n == 'head':
            ts, bs = self.jf('top_spine', f), self.jf('bottom_spine', f); return ts + 0.21 * nrm(nrm(ts - bs) + np.array([0, 0, 0.6]))
        i = self.I[n]; return (1 - w) * self.X[a, i] + w * self.X[b, i]
    def joints(self, tau): return {n: self.jf(n, tau) for n in self.names}
    def straighten_left(self, J, tau): return J
    def racket(self, tau):
        f = float(np.clip(tau, 0, self.T - 1)); a = int(np.floor(f)); b = min(a + 1, self.T - 1); w = f - a
        Rm = Rot.from_matrix(np.array([self.Rr[a], self.Rr[b]])); R = Slerp([0, 1], Rm)(w).as_matrix() if b > a else self.Rr[a]; return (1 - w) * self.butt[a] + w * self.butt[b], R, None
    def ball(self, tau):
        f = float(np.clip(tau, 0, self.T - 1)); a = int(np.floor(f)); b = min(a + 1, self.T - 1); w = f - a
        if not (self.ball_ok[a] and self.ball_ok[b]): return np.array([0, 0, -50.0])
        return (1 - w) * self.ball3[a] + w * self.ball3[b]
    # ---------- construction
    def build(self):
        import ball_lab as BL
        bl = pickle.load(open(SP + '/lab2/ball3d.pkl', 'rb')); T = self.T; lab = self.lab; Kf = self.K[0, 0]
        ball3 = np.zeros((T, 3)); ok = np.zeros(T, bool); depth = np.full(T, np.nan); px = np.full((T, 2), np.nan)
        import ball_lab as B
        raw = {}                                                   # ball pixel per frame in the reference frame, per track
        for tid, trk in B.trk.items():
            for f in trk:
                h = lab['H'][f] @ np.array([trk[f][1], trk[f][2], 1.0]); raw.setdefault(tid, {})[f] = h[:2] / h[2]
        def model_depth(F, frames):
            P = BL.positions(F, frames); _, z = BL.project(P); return z
        segs = [('175', bl['A'], range(0, 77)), ('0', bl['B1'], range(92, 119)), ('0', bl['B2'], range(150, 237))]
        for tid, F, fr in segs:
            fr = list(fr); z = model_depth(F, fr)
            for f, zz in zip(fr, z): px[f] = raw[tid][f]; depth[f] = zz; ok[f] = True
        # hand-held part (119..149): ball sits in the left hand -> depth of the left wrist along the ball's pixel ray
        for f in range(119, 150):
            px[f] = raw['0'][f]; W = self.jf('left_wrist', f); Wc = (W - self.C_cam) @ self.R_cam.T; depth[f] = Wc[2] - 0.03; ok[f] = True
        for f in range(T):
            if ok[f]: d = self.ray(*px[f]); ball3[f] = self.C_cam + d * depth[f]
        self.ball3, self.ball_ok, self.ball_px = ball3, ok, px
        # ---- racket
        rk = lab['racket']; D = 0.52; head = np.zeros((T, 3)); axis = np.zeros((T, 3)); prev = None
        for f in range(T):
            fc = rk[f]['face']; c = fc['c']; W = self.jf('right_wrist', f); d = self.ray(*c); dn = d / np.linalg.norm(d)
            # head centre on the ray at distance D from the wrist
            w0 = W - self.C_cam; b_ = np.dot(dn, w0); disc = b_ * b_ - (np.dot(w0, w0) - D * D)
            if disc > 0:
                s = np.sqrt(disc); cands = [b_ - s, b_ + s]
                if prev is None: ry = max(fc['axes']); zs = Kf * 0.165 / ry; key = lambda l: abs(l * dn[2] * 1.0 - 0 - 0) if False else abs(((self.C_cam + dn * l - self.C_cam) @ self.R_cam.T)[2] - zs)
                else: key = lambda l: np.linalg.norm(self.C_cam + dn * l - prev)
                lam = min(cands, key=key)
            else: lam = b_
            H = self.C_cam + dn * lam; head[f] = H; prev = H
            axis[f] = nrm(H - W) if np.linalg.norm(H - W) > 0.05 else np.array([0, 0, 1.0])
        axis = np.array([nrm(v) for v in gaussian_filter1d(axis, 1.0, axis=0, mode='nearest')]); head = gaussian_filter1d(head, 0.8, axis=0, mode='nearest')
        # roll: grid search of the in-plane face direction against the labelled ellipse, Viterbi for continuity
        NPH = 90; phis = np.arange(NPH) * np.pi / NPH; cost = np.zeros((T, NPH)); sm = np.linspace(0, 2 * np.pi, 20, endpoint=False)
        for f in range(T):
            a = axis[f]; e1 = nrm(np.cross(a, [0, 0, 1.0]) if abs(a[2]) < 0.95 else np.cross(a, [1.0, 0, 0])); e2 = np.cross(a, e1); fc = rk[f]['face']; P = fc['pts']; cx_, cy_ = fc['c']
            (ex, ey), (w_, h_), ang = cv2_fit(P)
            for k, ph in enumerate(phis):
                bb = np.cos(ph) * e1 + np.sin(ph) * e2; pts = head[f] + self.face_semi[0] * np.cos(sm)[:, None] * bb + self.face_semi[1] * np.sin(sm)[:, None] * a
                uv, _ = self.project(pts); (c2x, c2y), (w2, h2), ang2 = cv2_fit(uv); cost[f, k] = ellipse_dist(((c2x, c2y), (w2, h2), ang2), ((ex, ey), (w_, h_), ang))
        INF = 1e9; dp = cost[0].copy(); bp = np.zeros((T, NPH), int)
        idx = np.arange(NPH); dd = np.abs(idx[:, None] - idx[None, :]); dd = np.minimum(dd, NPH - dd) * (np.pi / NPH); trans = (dd / 0.35) ** 2 * 6.0
        for f in range(1, T): tot = dp[None, :] + trans; bp[f] = tot.argmin(1); dp = cost[f] + tot.min(1)
        path = np.zeros(T, int); path[-1] = int(dp.argmin())
        for f in range(T - 1, 0, -1): path[f - 1] = bp[f][path[f]]
        self.roll_cost = cost[np.arange(T), path]
        # build rotation matrices; face-normal sign: toward +y (away from the camera) at contact, continuity elsewhere
        Rs = []; nprev = None; launch = nrm(bl['A']['v1'])
        for f in range(T):
            a = axis[f]; e1 = nrm(np.cross(a, [0, 0, 1.0]) if abs(a[2]) < 0.95 else np.cross(a, [1.0, 0, 0])); e2 = np.cross(a, e1); ph = phis[path[f]]
            bb = np.cos(ph) * e1 + np.sin(ph) * e2; n = nrm(np.cross(bb, a)); Rs.append([bb, a, n])
        fcA = int(round(bl['A']['f0'] + bl['A']['tc'] / DT)); fcB = int(round(bl['B2']['f0'] + bl['B2']['tc'] / DT)); self.fc = (fcA, fcB)
        # continuity of (b, n) sign across frames (b-> -b, n -> -n is the same face): flip both when it reduces the jump
        for f in range(1, T):
            if np.dot(Rs[f][0], Rs[f - 1][0]) + np.dot(Rs[f][2], Rs[f - 1][2]) < 0: Rs[f][0], Rs[f][2] = -Rs[f][0], -Rs[f][2]
        M = np.array([np.column_stack([r[0], r[1], r[2]]) for r in Rs]); q = Rot.from_matrix(M).as_quat()
        for f in range(1, T):
            if np.dot(q[f], q[f - 1]) < 0: q[f] = -q[f]
        q = gaussian_filter1d(q, 0.8, axis=0, mode='nearest'); q /= np.linalg.norm(q, axis=1, keepdims=True); self.Rr = Rot.from_quat(q).as_matrix()
        self.head_c = head; self.axis = axis; self.butt = head - 0.52 * np.array([self.Rr[f][:, 1] for f in range(T)])
        self.head_px = np.array([rk[f]['face']['c'] for f in range(T)])
        pickle.dump(dict(Rr=self.Rr, butt=self.butt, head_c=self.head_c, axis=self.axis, ball3=ball3, ball_ok=ok, ball_px=px, head_px=self.head_px, fc=self.fc, roll_cost=self.roll_cost), open(SP + '/lab2/motion_lab.pkl', 'wb'))
import cv2
def cv2_fit(P): P = np.asarray(P, np.float32).reshape(-1, 1, 2); (cx, cy), (w, h), ang = cv2.fitEllipse(P); return (cx, cy), (w, h), ang
def ellipse_dist(e1, e2):
    def pts(e, n=24):
        (cx, cy), (w, h), ang = e; t = np.linspace(0, 2 * np.pi, n, endpoint=False); a = np.radians(ang); x = w / 2 * np.cos(t); y = h / 2 * np.sin(t); return np.c_[cx + x * np.cos(a) - y * np.sin(a), cy + x * np.sin(a) + y * np.cos(a)]
    # symmetric nearest-point distance of outlines
    A, B = pts(e1), pts(e2); d = np.linalg.norm(A[:, None] - B[None], axis=-1); return 0.5 * (d.min(1).mean() + d.min(0).mean())
if __name__ == '__main__':
    M = LabMotion(); M.build(); print('contact frames', M.fc, ' roll cost mean %.2f px max %.2f' % (M.roll_cost.mean(), M.roll_cost.max()))
    # QA: project the racket back, compare with labelled face centre / handle centre
    e = []; eh = []
    for f in range(M.T):
        b, Rr, _ = M.racket(f); hc = b + 0.52 * Rr[:, 1]; uv, _ = M.project(hc); e.append(np.linalg.norm(uv[0] - M.head_px[f]))
        g = b + 0.10 * Rr[:, 1]; uv2, _ = M.project(g); eh.append(np.linalg.norm(uv2[0] - M.lab['racket'][f]['handle']['c']))
    print('head-centre reproj mean %.2f max %.2f px;  grip vs labelled handle-box centre: mean %.1f max %.1f px' % (np.mean(e), np.max(e), np.mean(eh), np.max(eh)))
    for f in (24, 100, 184):
        b, Rr, _ = M.racket(f); print(f, 'butt', b.round(2), 'head', (b + .52 * Rr[:, 1]).round(2), 'ball', M.ball(f).round(2), 'wrist', M.jf('right_wrist', f).round(2))

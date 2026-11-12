"""Motion layer: uneven-frame-time correction + smoothing splines + analytic ball path.
tau_k = k - eps*(k odd)  (frame units).  All functions take tau (float or array) and return world-space metres."""
import json, numpy as np
from scipy.interpolate import make_smoothing_spline
from scipy.spatial.transform import Rotation as Rot, Slerp

class Motion:
    def __init__(self, D, suffix='_ext3', eps=0.3, lam_j=None, lam_r=None, ball='ball3d_phys.npz', T=92):
        self.D = D; self.eps = eps
        p = np.load(f'{D}/player3d_joint{suffix}.npz', allow_pickle=True); r = np.load(f'{D}/racket3d_joint{suffix}.npz', allow_pickle=True)
        self.names = [str(n) for n in p['names']]; self.I = {n: i for i, n in enumerate(self.names)}; self.H = float(p['H']); self.lengths = dict(zip([str(g) for g in p['groups']], p['lengths']))
        self.X = p['X'][:T]; self.T = T; self.k = np.arange(T, dtype=float); self.tau0 = self.k - eps * (self.k % 2 == 1)
        self.rn = [str(n) for n in r['names']]; self.Pr = r['P'][:T]; self.Rr = r['R'][:T]; self.br = r['butt'][:T]; self.template = r['template']; self.rlen = float(r['length'])
        self.face_center_local = r['face_center_local']; self.face_semi = r['face_semi']
        bb = np.load(f'{D}/{ball}'); self.ball_q = bb['q']; self.kappa = float(bb['kappa']); self.rel = int(bb['rel']); self.TC = int(bb['contact_frame'])
        c = np.load(f'{D}/camera.npz'); self.K, self.R_cam, self.C_cam = c['K'], c['R'], c['cam']
        # smoothing splines (lam chosen so residual ~ label noise); joints & racket origin
        self.lam_j = lam_j; self.lam_r = lam_r
        self.sp_X = [[make_smoothing_spline(self.tau0, self.X[:, j, c], lam=lam_j) for c in range(3)] for j in range(self.X.shape[1])]
        self.sp_b = [make_smoothing_spline(self.tau0, self.br[:, c], lam=lam_r) for c in range(3)]
        q = Rot.from_matrix(self.Rr).as_quat(); 
        for i in range(1, T):
            if np.dot(q[i], q[i - 1]) < 0: q[i] = -q[i]
        self.sp_q = [make_smoothing_spline(self.tau0, q[:, c], lam=lam_r) for c in range(4)]
    def joint(self, name, tau):
        j = self.I[name]; return np.stack([s(tau) for s in self.sp_X[j]], -1)
    def joints(self, tau):
        return {n: self.joint(n, tau) for n in self.names}
    def racket(self, tau):
        b = np.stack([s(tau) for s in self.sp_b], -1); q = np.stack([s(tau) for s in self.sp_q], -1); q = q / np.linalg.norm(q, axis=-1, keepdims=True)
        R = Rot.from_quat(q).as_matrix(); P = b[..., None, :] + np.einsum('...ij,kj->...ki', R, self.template); return b, R, P
    def ball_ballistic(self, tau):
        g = 9.81; q = self.ball_q; sec = lambda k: self.kappa * (np.asarray(k, float)) / 30.0; tc = sec(self.TC)
        t = sec(tau) - tc; tau = np.asarray(tau, float); V = np.where((tau <= self.TC)[..., None], q[3:6], q[6:9])
        return q[:3] + V * t[..., None] - 0.5 * g * (t ** 2)[..., None] * np.array([0, 0, 1.0])
    def ball(self, tau, t_hold=57.0, t_blend=1.6):
        tau = np.asarray(tau, float); bal = self.ball_ballistic(tau + 0 * tau)
        hand = 0.5 * (self.joint('left_index', tau) + self.joint('left_thumb', tau)) + np.array([0, 0, 0.045])
        w = np.clip((tau - t_hold) / t_blend, 0, 1); w = (w * w * (3 - 2 * w))[..., None]
        return hand * (1 - w) + bal * w
    def tau_of_frame(self, f): return f - self.eps * (f % 2 == 1)
if __name__ == '__main__':
    import sys; D = sys.argv[1]
    for lam in (None, 0.5, 2.0, 8.0):
        m = Motion(D, lam_j=lam, lam_r=lam); res = []
        for j, n in enumerate(m.names):
            fit = np.stack([m.sp_X[j][c](m.tau0) for c in range(3)], -1); res.append(np.linalg.norm(fit - m.X[:, j], axis=-1))
        res = np.array(res); u = np.linspace(55, 82, 600); sp = np.stack([m.joint('right_wrist', u)], 0)[0]; acc = np.linalg.norm(np.diff(sp, 2, axis=0), axis=-1)
        print('lam', lam, 'joint resid rms %.1f mm  max %.0f mm  | wrist 2nd-diff max %.4f (smoothness)' % (1000 * np.sqrt(np.mean(res ** 2)), 1000 * res.max(), acc.max()))

"""Motion API (same calls the scene code uses) built ONLY from the raw video: MediaPipe -> calibrated 3D lift, colour-tracked ball, racket from arm kinematics anchored to the ball at contact."""
import numpy as np, pickle
from scipy.ndimage import gaussian_filter1d
from scipy.spatial.transform import Rotation as Rot, Slerp
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
G = np.array([0, 0, -9.81]); DT = 1 / 30.
def nrm(v): return v / (np.linalg.norm(v) + 1e-12)
class AutoMotion:
    def __init__(self, serve='B', sig=1.0):
        p = np.load(SP + '/auto/player3d_raw_s+1.npz'); cam = np.load(SP + '/auto/camera_raw.npz'); self.K, self.R_cam, self.C_cam = cam['K'], cam['R'], cam['cam']
        X = gaussian_filter1d(p['X'], sig, axis=0, mode='nearest'); nm = [str(n) for n in p['names']]; self.I = {n: i for i, n in enumerate(nm)}; self.X = X; self.T = X.shape[0]
        self.names = nm + ['top_spine', 'bottom_spine']; self.rlen = 0.685; self.face_semi = (0.14, 0.165)
        b = pickle.load(open(SP + '/auto/ball_fit_raw.pkl', 'rb')); self.serve = serve; (pp, t0, fr), q = b[serve], b[serve + '_post']; self.pp, self.t0, self.q = pp, t0, q; self.tc = q[0] * DT
        self.contact = pp[:3] + pp[3:6] * (self.tc - t0) + 0.5 * G * (self.tc - t0) ** 2; self.launch = q[1:4]
        # release: when the free-fall parabola (extrapolated backwards) is closest to the tossing hand
        ts = np.arange(max(0, int(self.tc / DT) - 70), int(self.tc / DT)) ; lh = lambda f: self.joint_f('left_index', f)
        d = [np.linalg.norm(self.traj_pre(f * DT) - lh(f)) for f in ts]; self.f_rel = int(ts[int(np.argmin(d))])
        self._build_racket()
    def traj_pre(self, t): return self.pp[:3] + self.pp[3:6] * (t - self.t0) + 0.5 * G * (t - self.t0) ** 2
    def joint_f(self, n, f):
        if n == 'top_spine': return (self.joint_f('left_shoulder', f) + self.joint_f('right_shoulder', f)) / 2
        if n == 'bottom_spine': return (self.joint_f('left_hip', f) + self.joint_f('right_hip', f)) / 2
        f = float(np.clip(f, 0, self.T - 1)); a = int(np.floor(f)); b = min(a + 1, self.T - 1); w = f - a; i = self.I[n]; return (1 - w) * self.X[a, i] + w * self.X[b, i]
    def joint(self, n, tau): return self.joint_f(n, tau)
    def joints(self, tau): return {n: self.joint_f(n, tau) for n in self.names}
    def straighten_left(self, J, tau): return J
    def _build_racket(self):
        fc = self.tc / DT; self.rk = []; ref_n = None
        for f in range(self.T):
            W, Ix, Th, E = (self.joint_f(n, f) for n in ('right_wrist', 'right_index', 'right_thumb', 'right_elbow'))
            hand = nrm(Ix - W); fore = nrm(W - E); axis0 = nrm(0.5 * hand + 0.5 * fore); grip = W + 0.45 * (Ix - W)
            # blend towards "grip -> ball at contact" over the last 9 frames before contact, hold a short time after
            toward = nrm(self.contact - grip); wgt = np.clip(1 - abs(f - fc) / 9.0, 0, 1) ** 1.2 if f <= fc + 3 else np.clip(1 - (f - fc - 3) / 6.0, 0, 1) ** 1.2
            axis = nrm((1 - wgt) * axis0 + wgt * toward); lat = nrm(Th - Ix); n = np.cross(axis, lat); n = nrm(n - axis * np.dot(n, axis))
            self.rk.append([grip, axis, n])
        # normal sign: make it face the launch direction at contact, keep continuity elsewhere
        fcr = int(round(fc)); s = 1.0 if np.dot(self.rk[fcr][2], nrm(self.launch)) >= 0 else -1.0
        for i in range(self.T):
            if i > 0 and np.dot(s * self.rk[i][2], self.rk[i - 1][2] * 1.0 * (self.rk[i - 1][3] if len(self.rk[i - 1]) > 3 else 1.0)) < 0: pass
        N_ = np.array([r[2] * s for r in self.rk]); 
        for i in range(fcr - 1, -1, -1):
            if np.dot(N_[i], N_[i + 1]) < 0: N_[i] = -N_[i]
        for i in range(fcr + 1, self.T):
            if np.dot(N_[i], N_[i - 1]) < 0: N_[i] = -N_[i]
        Rs = []
        for i in range(self.T):
            grip, axis, _ = self.rk[i]; z = nrm(N_[i] - axis * np.dot(N_[i], axis)); x = np.cross(axis, z); Rs.append(np.column_stack([x, axis, z]))
        # light temporal smoothing of the rotations (slerp-based low-pass) and grips
        q = Rot.from_matrix(np.array(Rs)); qm = q.as_quat(); 
        for i in range(1, self.T):
            if np.dot(qm[i], qm[i - 1]) < 0: qm[i] = -qm[i]
        qm = gaussian_filter1d(qm, 1.2, axis=0, mode='nearest'); qm /= np.linalg.norm(qm, axis=1, keepdims=True); self.Rr = Rot.from_quat(qm).as_matrix()
        self.grip = gaussian_filter1d(np.array([r[0] for r in self.rk]), 0.8, axis=0, mode='nearest')
    def racket(self, tau):
        f = float(np.clip(tau, 0, self.T - 1)); a = int(np.floor(f)); b = min(a + 1, self.T - 1); w = f - a
        Rm = Rot.from_matrix(np.array([self.Rr[a], self.Rr[b]])); R = Slerp([0, 1], Rm)(w).as_matrix() if b > a else self.Rr[a]; g = (1 - w) * self.grip[a] + w * self.grip[b]
        butt = g - 0.12 * R[:, 1]; return butt, R, None
    def ball(self, tau):
        t = tau * DT
        if tau < self.f_rel: return self.joint_f('left_index', tau)
        if t <= self.tc: return self.traj_pre(t)
        dt = t - self.tc; P = self.contact + self.launch * dt + 0.5 * G * dt ** 2
        return P if P[2] > 0.034 else np.array([P[0], P[1], -50.0])
if __name__ == '__main__':
    for sv in 'AB':
        M = AutoMotion(sv); fc = M.tc / DT; b, R, _ = M.racket(round(fc)); head = b + R[:, 1] * 0.52
        print(sv, 'release frame', M.f_rel, 'contact frame %.1f' % fc, 'racket head-centre vs ball at contact: %.3f m' % np.linalg.norm(head - M.contact), 'normal.launch %.2f' % np.dot(R[:, 2], nrm(M.launch)))

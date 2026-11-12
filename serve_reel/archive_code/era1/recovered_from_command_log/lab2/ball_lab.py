"""3D ball from the CVAT ball ellipses (transferred to the reference camera): piecewise ballistic flight with quadratic drag, an impulse at racket contact and
ground bounces; unknowns are fitted to the reprojection of every labelled ball centre (+ ball radius -> depth, ground-contact labels).
Output lab2/ball3d.pkl: dict(A=params, B1=params, B2=params, funcs)"""
import pickle, numpy as np, sys
from scipy.optimize import least_squares
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
import calib_lab as CL
cam = np.load(SP + '/lab2/camera_lab.npz'); K, R, C = cam['K'], cam['R'], cam['cam']; f_ = K[0, 0]; DT = 1 / 30.; G = -9.81; RB = 0.0335; KD = 0.020; E_V, E_H = 0.74, 0.85
lab = pickle.load(open(SP + '/lab2/labels_ref.pkl', 'rb')); raw = pickle.load(open(SP + '/lab2/labels2.pkl', 'rb'))
trk = {}
for tid, f, tag, A in raw['shapes']['B_ball']: trk.setdefault(tid, {})[f] = (f, float(A['cx']), float(A['cy']), 0.5 * (float(A['rx']) + float(A['ry'])))
def ref_obs(tid, f):                                           # transfer the ball centre to the reference frame
    _, x, y, r = trk[tid][f]; return lab['H'][f]; 
Hs = lab['H']
def obs(tid, frames):
    o = []
    for f in frames:
        _, x, y, r = trk[tid][f]; h = Hs[f] @ np.array([x, y, 1.0]); o.append((f, h[0] / h[2], h[1] / h[2], r))
    return np.array(o)
def project(X): Xc = (np.atleast_2d(X) - C) @ R.T; return np.c_[f_ * Xc[:, 0] / Xc[:, 2] + K[0, 2], f_ * Xc[:, 1] / Xc[:, 2] + K[1, 2]], Xc[:, 2]
def sim(p0, v0, t_imp, v1, times, e_v=E_V, dt=1 / 600.):
    """integrate from t=0 (position p0, velocity v0), velocity replaced by v1 at t_imp (None -> no impulse); returns positions at `times`"""
    out = []; p = np.array(p0, float); v = np.array(v0, float); t = 0.0; ti = 0; times = np.asarray(times); done = t_imp is None; T = []
    order = np.argsort(times); res = np.zeros((len(times), 3)); k = 0
    while k < len(order):
        while k < len(order) and times[order[k]] <= t + 1e-12: res[order[k]] = p; k += 1
        if k >= len(order): break
        if not done and t + dt >= t_imp: 
            h = t_imp - t; p = p + v * h + 0.5 * np.array([0, 0, G]) * h * h; v = np.array(v1, float); t = t_imp; done = True; continue
        a = np.array([0, 0, G]) - KD * np.linalg.norm(v) * v; p = p + v * dt + 0.5 * a * dt * dt; v = v + a * dt; t += dt
        if p[2] < RB and v[2] < 0: p[2] = RB; v = np.array([v[0] * E_H, v[1] * E_H, -v[2] * e_v])
    return res
def depth_guess(u, v, r): return f_ * RB / max(r, 1.5)
def ray_point(u, v, z):
    d = R.T @ np.array([(u - K[0, 2]) / f_, (v - K[1, 2]) / f_, 1.0]); return C + d * z
def fit(o, f0, tc0, ground=None, nstart=24, fixed_e=None, seed=0):
    """o: observations (f,u,v,r) starting at frame f0 (t=0).  params: p0(3) v0(3) tc v1(3)  (tc=None -> no impulse: p0 v0 only)"""
    t_obs = (o[:, 0] - f0) * DT; has_imp = tc0 is not None; rng = np.random.default_rng(seed)
    def unpack(x): return x[:3], x[3:6], (x[6] if has_imp else None), (x[7:10] if has_imp else None)
    def res(x):
        p0, v0, tc, v1 = unpack(x); P = sim(p0, v0, tc, v1, t_obs); uv, z = project(P)
        r = ((uv - o[:, 1:3]) / 1.0).ravel().tolist(); r += list(((f_ * RB / z - o[:, 3]) / 0.8) * 0.35)
        if ground is not None:
            gf, gu, gv = ground; i = int(np.argmin(abs(o[:, 0] - gf)))
            if abs(o[i, 0] - gf) < 0.5: r += [(P[i, 2] - RB) / 0.03 * 3.0]
        return np.array(r)
    best = None; d0 = depth_guess(o[0, 1], o[0, 2], o[0, 3])
    for s in range(nstart):
        z0 = d0 * rng.uniform(0.8, 1.2); p0 = ray_point(o[0, 1], o[0, 2], z0); v0 = rng.normal(0, 1.5, 3); v0[2] = rng.uniform(0, 9) if f0 < 60 or f0 > 140 else rng.uniform(-3, 6)
        x0 = np.r_[p0, v0]
        if has_imp: x0 = np.r_[x0, (tc0 - f0) * DT + rng.uniform(-.02, .02), v0 * 0 + [rng.normal(0, 4), rng.uniform(8, 35), rng.uniform(-18, -2)]]
        try: s_ = least_squares(res, x0, loss='soft_l1', f_scale=2.0, max_nfev=120)
        except Exception as ex: continue
        if best is None or s_.cost < best.cost: best = s_
    p0, v0, tc, v1 = unpack(best.x); rr = res(best.x); n = len(o) * 2
    print('  cost %.1f  px-rms %.2f' % (best.cost, np.sqrt((rr[:n] ** 2).mean())), ' p0', p0.round(2), 'v0', v0.round(2), 'tc frame %.2f' % (f0 + tc / DT) if has_imp else '', 'v1', np.round(v1, 1) if has_imp else '')
    return dict(f0=f0, p0=p0, v0=v0, tc=tc, v1=v1, cost=best.cost)
def positions(F, frames): return sim(F['p0'], F['v0'], F['tc'], F['v1'], (np.asarray(frames, float) - F['f0']) * DT)
if __name__ == '__main__':
    out = {}
    print('serve A'); oA = obs('175', range(0, 77)); gA = (39, 0, 0)
    out['A'] = fit(oA, 0, 24, ground=gA, nstart=40)
    print('serve B toss'); oB = obs('0', range(148, 213)); out['B2'] = fit(oB, 148, 184, ground=(201, 0, 0), nstart=40, seed=1)
    print('serve B dribble'); oD = obs('0', range(92, 119)); out['B1'] = fit(oD, 92, None, ground=(111, 0, 0), nstart=60, seed=2)
    pickle.dump(out, open(SP + '/lab2/ball3d.pkl', 'wb'))
    for k, (F, o) in {'A': (out['A'], oA), 'B2': (out['B2'], oB), 'B1': (out['B1'], oD)}.items():
        P = positions(F, o[:, 0]); uv, z = project(P); e = np.linalg.norm(uv - o[:, 1:3], axis=1)
        print(k, 'reproj px: mean %.2f max %.2f at frame %d' % (e.mean(), e.max(), o[e.argmax(), 0]), ' max height %.2f m; first z %.2f' % (P[:, 2].max(), P[0, 2]))
        zz = [(int(o[i, 0]), round(float(P[i, 0]), 1), round(float(P[i, 1]), 1), round(float(P[i, 2]), 2)) for i in range(0, len(o), 6)]; print('  ', zz)

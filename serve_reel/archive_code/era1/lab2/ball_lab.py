"""3D ball from the CVAT ball ellipses (transferred to the reference camera): piecewise ballistic flight with quadratic drag, an impulse at racket contact and
ground bounces; unknowns are fitted to the reprojection of every labelled ball centre (+ ball radius -> depth, ground-contact labels).
Output lab2/ball3d.pkl: dict(A=params, B1=params, B2=params, funcs)"""
import pickle, numpy as np, sys
from scipy.optimize import least_squares
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0, SP + '/lab2')
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
import jax, jax.numpy as jnp
jax.config.update('jax_enable_x64', True)
SUB = 6; HDT = DT / SUB; NF = 100                                    # 6 integration steps per frame, up to 100 frames
Rj_, Cj_ = jnp.array(R), jnp.array(C)
def _sim(p0, v0, t_imp, v1, e_v=E_V):
    """returns (NF*SUB+1, 3) positions on a fixed grid; impulse at t_imp (huge value -> none), bounce on z=RB"""
    g = jnp.array([0, 0, G])
    def step(c, i):
        p, v, t = c; t1 = t + HDT; hit = (t < t_imp) & (t1 >= t_imp); h1 = jnp.where(hit, t_imp - t, HDT)
        a = g - KD * jnp.linalg.norm(v) * v; pm = p + v * h1 + 0.5 * a * h1 * h1; vm = v + a * h1
        vm = jnp.where(hit, v1, vm); h2 = jnp.where(hit, HDT - h1, 0.0); a2 = g - KD * jnp.linalg.norm(vm) * vm
        pn = pm + vm * h2 + 0.5 * a2 * h2 * h2; vn = vm + a2 * h2
        b = (pn[2] < RB) & (vn[2] < 0); pn = jnp.where(b, pn.at[2].set(RB), pn); vn = jnp.where(b, jnp.array([vn[0] * E_H, vn[1] * E_H, -vn[2] * e_v]), vn)
        return (pn, vn, t1), pn
    _, P = jax.lax.scan(step, (p0, v0, 0.0), jnp.arange(NF * SUB)); return jnp.vstack([p0[None], P])
def _proj(X): Xc = (X - Cj_) @ Rj_.T; return jnp.stack([f_ * Xc[:, 0] / Xc[:, 2] + K[0, 2], f_ * Xc[:, 1] / Xc[:, 2] + K[1, 2]], 1), Xc[:, 2]
def sim(p0, v0, t_imp, v1, times, **kw):
    P = np.asarray(_sim(jnp.array(p0, float), jnp.array(v0, float), 1e9 if t_imp is None else float(t_imp), jnp.array(v1 if v1 is not None else [0, 0, 0], float), **kw))
    k = np.asarray(times) / HDT; i0 = np.clip(np.floor(k).astype(int), 0, len(P) - 2); w = (k - i0)[:, None]; return P[i0] * (1 - w) + P[i0 + 1] * w
def depth_guess(u, v, r): return f_ * RB / max(r, 1.5)
def ray_point(u, v, z):
    d = R.T @ np.array([(u - K[0, 2]) / f_, (v - K[1, 2]) / f_, 1.0]); return C + d * z
def fit(o, f0, tc0, ground=None, nstart=24, fixed_e=None, seed=0, prior0=None, vprior=None):
    """o: observations (f,u,v,r) starting at frame f0 (t=0).  params: p0(3) v0(3) tc v1(3)  (tc=None -> no impulse: p0 v0 only)"""
    has_imp = tc0 is not None; rng = np.random.default_rng(seed); idx = jnp.array(((o[:, 0] - f0) * SUB).astype(int)); O = jnp.array(o); gi = None
    if ground is not None:
        gf = ground[0]; gxy = jnp.array(ground[1:3]); ii = np.where(abs(o[:, 0] - gf) < 0.5)[0]; gi = int(ii[0]) if len(ii) else None
    def unpack(x): return x[:3], x[3:6], (x[6] if has_imp else 1e9), (x[7:10] if has_imp else jnp.zeros(3))
    def res_j(x):
        p0, v0, tc, v1 = unpack(x); P = _sim(p0, v0, tc, v1)[idx]; uv, z = _proj(P)
        r = jnp.concatenate([(uv - O[:, 1:3]).ravel(), (f_ * RB / z - O[:, 3]) / 0.8 * 0.35])
        if gi is not None: r = jnp.concatenate([r, jnp.array([(P[gi, 2] - RB) / 0.03 * 3.0]), (P[gi, :2] - gxy) / 0.12])
        if prior0 is not None: r = jnp.concatenate([r, (p0[:2] - prior0[0]) / prior0[1]])
        if vprior is not None and has_imp: r = jnp.concatenate([r, jnp.array([(jnp.linalg.norm(v1) - vprior[0]) / vprior[1]])])
        return r
    resj = jax.jit(res_j); jacj = jax.jit(jax.jacfwd(res_j)); res = lambda x: np.asarray(resj(jnp.array(x))); jac = lambda x: np.asarray(jacj(jnp.array(x)))
    best = None; d0 = depth_guess(o[0, 1], o[0, 2], o[0, 3])
    for s in range(nstart):
        z0 = d0 * rng.uniform(0.8, 1.2); p0 = ray_point(o[0, 1], o[0, 2], z0); v0 = rng.normal(0, 1.5, 3); v0[2] = rng.uniform(0, 9) if f0 < 60 or f0 > 140 else rng.uniform(-3, 6)
        x0 = np.r_[p0, v0]
        if has_imp: x0 = np.r_[x0, (tc0 - f0) * DT + rng.uniform(-.02, .02), v0 * 0 + [rng.normal(0, 4), rng.uniform(8, 35), rng.uniform(-18, -2)]]
        try: s_ = least_squares(res, x0, jac=jac, loss='soft_l1', f_scale=2.0, max_nfev=150)
        except Exception as ex: continue
        if best is None or s_.cost < best.cost: best = s_
    p0, v0, tc, v1 = [np.asarray(v) if not isinstance(v, float) else v for v in unpack(best.x)]; rr = res(best.x); n = len(o) * 2
    print('  cost %.1f  px-rms %.2f' % (best.cost, np.sqrt((rr[:n] ** 2).mean())), ' p0', p0.round(2), 'v0', v0.round(2), 'tc frame %.2f' % (f0 + float(tc) / DT) if has_imp else '', 'v1', np.round(v1, 1) if has_imp else '')
    return dict(f0=f0, p0=np.asarray(p0), v0=np.asarray(v0), tc=(float(tc) if has_imp else None), v1=(np.asarray(v1) if has_imp else None), cost=best.cost)
def positions(F, frames): return sim(F['p0'], F['v0'], F['tc'], F['v1'], (np.asarray(frames, float) - F['f0']) * DT)
def ground_pt(u, v):
    d = R.T @ np.array([(u - K[0, 2]) / f_, (v - K[1, 2]) / f_, 1.0]); lam = (RB - C[2]) / d[2]; return (C + d * lam)[:2]
def foot_xy(f):
    pts = [lab['skel'][n][f][0] for n in ('left_heel', 'right_heel', 'left_foot_index', 'right_foot_index')]; g = np.array([ground_pt(*p) for p in pts]); return np.median(g, 0)
if __name__ == '__main__':
    out = {}; GP = {f: ground_pt(*p) for (_, f, p, o_) in lab['shapes']['B_contact_ground'] if not o_}; print('ground bounce xy', {k: v.round(2) for k, v in GP.items()}, ' feet A', foot_xy(0).round(2), ' feet B', foot_xy(148).round(2), foot_xy(100).round(2))
    print('serve A'); oA = obs('175', range(0, 77)); gA = (39, 0, 0)
    out['A'] = fit(oA, 0, 24, ground=(39, *GP[39]), nstart=40, prior0=(foot_xy(0) + [0.1, 0.45], 0.6), vprior=(33, 10))
    print('serve B toss'); oB = obs('0', range(148, 213)); out['B2'] = fit(oB, 148, 184, ground=(201, *GP[201]), nstart=40, seed=1, prior0=(foot_xy(148) + [0.1, 0.35], 0.6), vprior=(33, 10))
    print('serve B dribble'); oD = obs('0', range(92, 119)); out['B1'] = fit(oD, 92, None, ground=(111, *GP[111]), nstart=60, seed=2, prior0=(foot_xy(92) + [0.0, 0.3], 0.7))
    pickle.dump(out, open(SP + '/lab2/ball3d.pkl', 'wb'))
    for k, (F, o) in {'A': (out['A'], oA), 'B2': (out['B2'], oB), 'B1': (out['B1'], oD)}.items():
        P = positions(F, o[:, 0]); uv, z = project(P); e = np.linalg.norm(uv - o[:, 1:3], axis=1)
        print(k, 'reproj px: mean %.2f max %.2f at frame %d' % (e.mean(), e.max(), o[e.argmax(), 0]), ' max height %.2f m; first z %.2f' % (P[:, 2].max(), P[0, 2]))
        zz = [(int(o[i, 0]), round(float(P[i, 0]), 1), round(float(P[i, 1]), 1), round(float(P[i, 2]), 2)) for i in range(0, len(o), 6)]; print('  ', zz)

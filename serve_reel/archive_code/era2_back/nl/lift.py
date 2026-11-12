"""3D body from the CVAT labels (transferred to the reference camera): constant bone lengths + MediaPipe depth prior + feet on the ground + racket-contact anchors."""
import numpy as np, jax, jax.numpy as jnp, sys, pickle
from scipy.optimize import minimize
from scipy.ndimage import gaussian_filter1d
jax.config.update('jax_enable_x64', True)
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0, SP + '/nl')
mp = np.load(SP + '/nl/mp_pose.npz'); cam = np.load(SP + '/nl/camera.npz'); K, R, C = cam['K'], cam['R'], cam['cam']; lab = pickle.load(open(SP + '/nl/labels.pkl', 'rb'))
import ball as BL
Href = 1.80; T = 92; MODE = sys.argv[1] if len(sys.argv) > 1 else 'free'
MP = {'left_shoulder': 11, 'right_shoulder': 12, 'left_elbow': 13, 'right_elbow': 14, 'left_wrist': 15, 'right_wrist': 16, 'left_hip': 23, 'right_hip': 24, 'left_knee': 25, 'right_knee': 26,
      'left_ankle': 27, 'right_ankle': 28, 'left_heel': 29, 'right_heel': 30, 'left_foot_index': 31, 'right_foot_index': 32}
names = list(MP) + ['top_spine', 'bottom_spine']; I = {n: i for i, n in enumerate(names)}; J = len(names)
uv = np.zeros((T, J, 2))
for n in names:
    uv[:, I[n]] = lab['skel'][n][:T]
uv = gaussian_filter1d(uv, 0.7, axis=0, mode='nearest')                                  # labels are hand-clicked: tiny jitter smoothing
zw = np.zeros((T, J)); L3 = mp['L3']; vis = np.ones((T, J))
for n, k in MP.items(): zw[:, I[n]] = L3[:, k, 2]; vis[:, I[n]] = np.clip(mp['VIS'][:, k], 0.05, 1)
zw[:, I['top_spine']] = (zw[:, I['left_shoulder']] + zw[:, I['right_shoulder']]) / 2; zw[:, I['bottom_spine']] = (zw[:, I['left_hip']] + zw[:, I['right_hip']]) / 2
fx, cx, cy = K[0, 0], K[0, 2], K[1, 2]; ray = np.stack([(uv[..., 0] - cx) / fx, (uv[..., 1] - cy) / fx, np.ones_like(uv[..., 0])], -1)
B = [('upper_arm', 'left_shoulder', 'left_elbow'), ('upper_arm', 'right_shoulder', 'right_elbow'), ('forearm', 'left_elbow', 'left_wrist'), ('forearm', 'right_elbow', 'right_wrist'),
     ('thigh', 'left_hip', 'left_knee'), ('thigh', 'right_hip', 'right_knee'), ('shank', 'left_knee', 'left_ankle'), ('shank', 'right_knee', 'right_ankle'),
     ('ank_heel', 'left_ankle', 'left_heel'), ('ank_heel', 'right_ankle', 'right_heel'), ('ank_toe', 'left_ankle', 'left_foot_index'), ('ank_toe', 'right_ankle', 'right_foot_index'),
     ('heel_toe', 'left_heel', 'left_foot_index'), ('heel_toe', 'right_heel', 'right_foot_index'), ('sh_w', 'left_shoulder', 'right_shoulder'), ('hip_w', 'left_hip', 'right_hip'),
     ('torso', 'left_shoulder', 'left_hip'), ('torso', 'right_shoulder', 'right_hip'), ('x_torso', 'left_shoulder', 'right_hip'), ('x_torso', 'right_shoulder', 'left_hip'),
     ('spine', 'top_spine', 'bottom_spine'), ('ts_sh', 'top_spine', 'left_shoulder'), ('ts_sh', 'top_spine', 'right_shoulder'), ('bs_hip', 'bottom_spine', 'left_hip'), ('bs_hip', 'bottom_spine', 'right_hip')]
groups = list(dict.fromkeys(b[0] for b in B)); Gi = {g: i for i, g in enumerate(groups)}; bi = np.array([I[b[1]] for b in B]); bj = np.array([I[b[2]] for b in B]); bg = np.array([Gi[b[0]] for b in B])
ant = {'upper_arm': .186, 'forearm': .146, 'thigh': .245, 'shank': .246, 'ank_heel': .045, 'ank_toe': .115, 'heel_toe': .14, 'sh_w': .23, 'hip_w': .17, 'torso': .30, 'x_torso': .34, 'spine': .30, 'ts_sh': .115, 'bs_hip': .085}
L0 = np.array([ant[g] * Href for g in groups]); fi = [I[n] for n in ('left_heel', 'right_heel', 'left_foot_index', 'right_foot_index')]
def ground_depth(u, v):
    d = R.T @ np.array([(u - cx) / fx, (v - cy) / fx, 1.0]); return -C[2] / d[2]
Z0 = np.zeros((T, J))
for t in range(T):
    zs = [ground_depth(*uv[t, k]) for k in fi]; zs = [z for z in zs if z > 0]; Z0[t] = np.median(zs) if zs else 20.0
sp = np.linalg.norm(np.gradient(gaussian_filter1d(uv[:, fi], 1.0, axis=0), axis=0), axis=-1); wstat = np.exp(-(sp / 1.5) ** 2)
anch = []; lanch = []
if MODE == 'anch':
    bl = pickle.load(open(SP + '/nl/ball3d.pkl', 'rb')); F = bl['S']; tc_f = float(BL.frame_of(BL.T_of(F['f0']) + F['tc']))
    for f in (int(np.floor(tc_f)), int(np.floor(tc_f)) + 1): anch.append((f, BL.positions(F, [f])[0]))
    lanch = [(f, BL.positions(F, [f])[0]) for f in (58, 59)]
print('anchors', [(a[0], a[1].round(2)) for a in anch])
rayj, Rj, Cj = jnp.array(ray), jnp.array(R), jnp.array(C); zwj = jnp.array(zw); wv = jnp.array(vis); wst = jnp.array(wstat); L0j = jnp.array(L0)
anf = jnp.array([a[0] for a in anch] or [0], dtype=int); anp = jnp.array([a[1] for a in anch] or [[0, 0, 0.0]]); NA = len(anch); lf_ = jnp.array([a[0] for a in lanch] or [0], dtype=int); lp_ = jnp.array([a[1] for a in lanch] or [[0, 0, 0.0]]); NL = len(lanch); LW = I['left_wrist']; RW = I['right_wrist']; hips = [I['left_hip'], I['right_hip']]; fij = jnp.array(fi); bij, bjj, bgj = jnp.array(bi), jnp.array(bj), jnp.array(bg)
def unpack(x): return x[:T * J].reshape(T, J), x[T * J:T * J + len(groups)], x[-1]
def world(Z): return (rayj * Z[..., None]) @ Rj + Cj
def cost(x):
    Z, lg, al = unpack(x); X = world(Z); L = L0j * jnp.exp(lg)
    d = jnp.linalg.norm(X[:, bij] - X[:, bjj], axis=-1) - L[bgj]; c_len = jnp.sum((d / 0.012) ** 2)
    zh = Z[:, hips].mean(1, keepdims=True); c_dep = jnp.sum(wv * ((Z - zh - al * (zwj - zwj[:, hips].mean(1, keepdims=True))) / 0.10) ** 2)
    zf = X[:, fij, 2]; c_gnd = jnp.sum(wst * (zf / 0.03) ** 2) + jnp.sum((jnp.minimum(zf + 0.01, 0.0) / 0.01) ** 2)
    c_sm = jnp.sum(((Z[2:] - 2 * Z[1:-1] + Z[:-2]) / 0.05) ** 2); Xa = X[2:] - 2 * X[1:-1] + X[:-2]; c_sw = jnp.sum((Xa / 0.15) ** 2)
    c_pri = jnp.sum((lg / 0.12) ** 2) + ((al - 1.0) / 0.2) ** 2
    c_anc = jnp.sum(((jnp.linalg.norm(X[anf, RW] - anp, axis=-1) - 0.52) / 0.05) ** 2) if NA else 0.0
    c_la = jnp.sum((jnp.linalg.norm(X[lf_, LW] - lp_, axis=-1) / 0.06) ** 2) if NL else 0.0                 # the tossing hand holds the ball at the release
    return c_len + c_dep + c_gnd + c_sm + c_sw + c_pri + c_anc + c_la
vg = jax.jit(jax.value_and_grad(cost)); x0 = np.concatenate([Z0.ravel(), np.zeros(len(groups)), [1.0]])
res = minimize(lambda x: tuple(np.asarray(v, dtype=np.float64) for v in vg(jnp.array(x))), x0, jac=True, method='L-BFGS-B', options=dict(maxiter=4000, maxfun=6000))
Z, lg, al = unpack(res.x); X = np.asarray(world(jnp.array(Z))); L = L0 * np.exp(lg)
print('cost %.0f iters %d alpha %.2f' % (res.fun, res.nit, al)); print({g: round(float(l), 3) for g, l in zip(groups, L)})
d = np.linalg.norm(X[:, bi] - X[:, bj], axis=-1); print('bone-length std (cm) %.2f' % (100 * d.std(0).mean()), ' min foot z %.3f' % X[:, fi, 2].min(), ' max head-proxy z %.2f' % X[:, I['top_spine'], 2].max())
print('anchor dist', [round(float(np.linalg.norm(X[f, RW] - p_)), 3) for f, p_ in anch]); print('hip y path', X[::30, hips, 1].mean(1).round(2).tolist())
np.savez(SP + '/nl/player3d_%s.npz' % MODE, X=X, names=names, lengths=L, groups=groups)

"""3D body from raw-video MediaPipe landmarks: calibrated pinhole camera + constant bone lengths + MediaPipe depth prior + feet on the ground. Unknown = depth of every joint."""
import numpy as np, jax, jax.numpy as jnp, sys
from scipy.optimize import minimize
jax.config.update('jax_enable_x64', True)
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
mp = np.load(SP + '/auto/mp_pose.npz'); cam = np.load(SP + '/auto/camera_raw.npz'); K, R, C = cam['K'], cam['R'], cam['cam']
sgn = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0; Href = float(sys.argv[2]) if len(sys.argv) > 2 else 1.80
MAP = {'nose': 0, 'left_shoulder': 11, 'right_shoulder': 12, 'left_elbow': 13, 'right_elbow': 14, 'left_wrist': 15, 'right_wrist': 16, 'left_index': 19, 'right_index': 20, 'left_thumb': 21, 'right_thumb': 22,
       'left_hip': 23, 'right_hip': 24, 'left_knee': 25, 'right_knee': 26, 'left_ankle': 27, 'right_ankle': 28, 'left_heel': 29, 'right_heel': 30, 'left_foot_index': 31, 'right_foot_index': 32}
names = list(MAP); I = {n: i for i, n in enumerate(names)}; J = len(names); T = mp['L2'].shape[0]
uv = mp['L2'][:, [MAP[n] for n in names]]; vis = mp['VIS'][:, [MAP[n] for n in names]]; zw = mp['L3'][:, [MAP[n] for n in names]]
fx, cx, cy = K[0, 0], K[0, 2], K[1, 2]; ray = np.stack([(uv[..., 0] - cx) / fx, (uv[..., 1] - cy) / fx, np.ones_like(uv[..., 0])], -1)       # camera-frame direction with unit depth
B = [('upper_arm', 'left_shoulder', 'left_elbow'), ('upper_arm', 'right_shoulder', 'right_elbow'), ('forearm', 'left_elbow', 'left_wrist'), ('forearm', 'right_elbow', 'right_wrist'),
     ('hand_i', 'left_wrist', 'left_index'), ('hand_i', 'right_wrist', 'right_index'), ('hand_t', 'left_wrist', 'left_thumb'), ('hand_t', 'right_wrist', 'right_thumb'),
     ('thigh', 'left_hip', 'left_knee'), ('thigh', 'right_hip', 'right_knee'), ('shank', 'left_knee', 'left_ankle'), ('shank', 'right_knee', 'right_ankle'),
     ('ank_heel', 'left_ankle', 'left_heel'), ('ank_heel', 'right_ankle', 'right_heel'), ('ank_toe', 'left_ankle', 'left_foot_index'), ('ank_toe', 'right_ankle', 'right_foot_index'),
     ('heel_toe', 'left_heel', 'left_foot_index'), ('heel_toe', 'right_heel', 'right_foot_index'), ('sh_w', 'left_shoulder', 'right_shoulder'), ('hip_w', 'left_hip', 'right_hip'),
     ('torso', 'left_shoulder', 'left_hip'), ('torso', 'right_shoulder', 'right_hip'), ('x_torso', 'left_shoulder', 'right_hip'), ('x_torso', 'right_shoulder', 'left_hip'),
     ('head', 'nose', 'left_shoulder'), ('head', 'nose', 'right_shoulder')]
groups = list(dict.fromkeys(b[0] for b in B)); Gi = {g: i for i, g in enumerate(groups)}; bi = np.array([I[b[1]] for b in B]); bj = np.array([I[b[2]] for b in B]); bg = np.array([Gi[b[0]] for b in B])
ant = {'upper_arm': .186, 'forearm': .146, 'hand_i': .10, 'hand_t': .075, 'thigh': .245, 'shank': .246, 'ank_heel': .045, 'ank_toe': .115, 'heel_toe': .14, 'sh_w': .23, 'hip_w': .17, 'torso': .30, 'x_torso': .34, 'head': .20}
L0 = np.array([ant[g] * Href for g in groups])
# feet: ground-intersection depth at the lowest foot point as initial depth; stationarity weights from pixel speed
fi = [I[n] for n in ('left_heel', 'right_heel', 'left_foot_index', 'right_foot_index')]; Cw = C; Rc = R
def ground_depth(u, v):
    d = Rc.T @ np.array([(u - cx) / fx, (v - cy) / fx, 1.0]); lam = -Cw[2] / d[2]; return lam                       # depth (camera z) where the ray meets z=0
Z0 = np.zeros((T, J))
for t in range(T):
    zs = [ground_depth(*uv[t, k]) for k in fi if ground_depth(*uv[t, k]) > 0]; Z0[t] = np.median(zs) if zs else 20.0
from scipy.ndimage import gaussian_filter1d
sp = np.linalg.norm(np.gradient(gaussian_filter1d(uv[:, fi], 1.0, axis=0), axis=0), axis=-1); wstat = np.exp(-(sp / 1.5) ** 2)      # (T,4) 1 when the foot pixel is nearly still
rayj, Rj, Cj = jnp.array(ray), jnp.array(Rc), jnp.array(Cw); zwj = jnp.array(zw) * sgn; wv = jnp.array(np.clip(vis, 0.05, 1.0)); wst = jnp.array(wstat); L0j = jnp.array(L0)
hips = [I['left_hip'], I['right_hip']]; fij = jnp.array(fi); bij, bjj, bgj = jnp.array(bi), jnp.array(bj), jnp.array(bg)
def unpack(x): Z = x[:T * J].reshape(T, J); lg = x[T * J:T * J + len(groups)]; al = x[-1]; return Z, lg, al
def world(Z): Xc = rayj * Z[..., None]; return Xc @ Rj + Cj           # R^T Xc + C   (row-vector form)
def cost(x):
    Z, lg, al = unpack(x); X = world(Z); L = L0j * jnp.exp(lg)
    d = jnp.linalg.norm(X[:, bij] - X[:, bjj], axis=-1) - L[bgj]; c_len = jnp.sum((d / 0.012) ** 2)
    zh = Z[:, hips].mean(1, keepdims=True); c_dep = jnp.sum(wv * ((Z - zh - al * (zwj - zwj[:, hips].mean(1, keepdims=True))) / 0.10) ** 2)
    zf = X[:, fij, 2]; c_gnd = jnp.sum(wst * (zf / 0.03) ** 2) + jnp.sum((jnp.minimum(zf + 0.01, 0.0) / 0.01) ** 2)
    a2 = Z[2:] - 2 * Z[1:-1] + Z[:-2]; c_sm = jnp.sum((a2 / 0.05) ** 2)
    Xa = X[2:] - 2 * X[1:-1] + X[:-2]; c_sw = jnp.sum((Xa / 0.15) ** 2)
    c_pri = jnp.sum((lg / 0.12) ** 2) + ((al - 1.0) / 0.2) ** 2
    return c_len + c_dep + c_gnd + c_sm + c_sw + c_pri
vg = jax.jit(jax.value_and_grad(cost))
x0 = np.concatenate([Z0.ravel(), np.zeros(len(groups)), [1.0]])
f = lambda x: tuple(np.asarray(v, dtype=np.float64) for v in vg(jnp.array(x)))
res = minimize(f, x0, jac=True, method='L-BFGS-B', options=dict(maxiter=4000, maxfun=6000)); Z, lg, al = unpack(res.x)
X = np.asarray(world(jnp.array(Z))); L = L0 * np.exp(lg)
print('sign', sgn, 'cost %.0f' % res.fun, 'iters', res.nit, 'alpha %.2f' % al); print({g: round(float(l), 3) for g, l in zip(groups, L)})
d = np.linalg.norm(X[:, bi] - X[:, bj], axis=-1); print('bone-length std (cm, mean over bones) %.2f' % (100 * d.std(0).mean()))
print('min foot z %.3f' % X[:, fi, 2].min(), ' head(nose) max z %.2f' % X[:, 0, 2].max(), ' player height est (nose+~0.12) %.2f' % (np.median(X[:, 0, 2] - X[:, fi, 2].min(1)) + 0.12))
print('hip world path x', X[::40, hips, 0].mean(1).round(2).tolist(), 'y', X[::40, hips, 1].mean(1).round(2).tolist())
np.savez(SP + '/auto/player3d_raw_s%+d.npz' % sgn, X=X, names=names, lengths=L, groups=groups, H=Href, alpha=al, cost=res.fun)

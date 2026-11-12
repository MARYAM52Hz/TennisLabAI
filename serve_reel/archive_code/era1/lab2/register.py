"""Per-frame court registration: with the camera centre and focal length fixed (from lab2/calib_lab.py), fit each frame's rotation to its labelled
court lines; H_f = K R0 R_f^T K^-1 maps raw frame f -> reference frame 0.  Then transfer every label to the reference frame."""
import pickle, numpy as np, cv2, sys
from scipy.optimize import least_squares
sys.path.insert(0, '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad/lab2')
import calib_lab as CL
SP = CL.SP; d = pickle.load(open(SP + '/lab2/labels2.pkl', 'rb')); cam = np.load(SP + '/lab2/camera_lab.npz'); p0 = cam['p'].copy()
K = cam['K']; Ki = np.linalg.inv(K); N = 237
def res_f(q, f, base):
    p = base.copy(); p[1:4] = q; return CL.residuals(p, f)[:-1]
base = p0.copy(); Q = np.zeros((N, 3)); rms = np.zeros(N); q = p0[1:4].copy()
for f in range(N):
    s = least_squares(res_f, q, args=(f, base), loss='soft_l1', f_scale=2.0); q = s.x; Q[f] = q; rms[f] = np.sqrt((res_f(q, f, base) ** 2).mean())
R0 = CL.rotmat(*Q[0]); Rf = [CL.rotmat(*Q[f]) for f in range(N)]
H = np.array([K @ R0 @ Rf[f].T @ Ki for f in range(N)])
print('rotation range (deg): yaw %.2f..%.2f pitch %.2f..%.2f roll %.2f..%.2f' % tuple(np.degrees([Q[:, 0].min(), Q[:, 0].max(), Q[:, 1].min(), Q[:, 1].max(), Q[:, 2].min(), Q[:, 2].max()])))
print('court-line rms per frame: mean %.2f  max %.2f px (frame %d)' % (rms.mean(), rms.max(), rms.argmax()))
def tf(pts, f): pts = np.atleast_2d(pts).astype(float); h = np.c_[pts, np.ones(len(pts))] @ H[f].T; return h[:, :2] / h[:, 2:3]
# --- transfer
out = dict(H=H, Q=Q, rms=rms, skel={}, racket={}, ball={}, shapes={})
for j, dd in d['skel'].items():
    out['skel'][j] = {f: (tf([v[0], v[1]], f)[0], v[2], v[3]) for f, v in dd.items()}
def ell_pts(cx, cy, rx, ry, rot, n=24):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); a = np.radians(rot); x = rx * np.cos(t); y = ry * np.sin(t)
    return np.c_[cx + x * np.cos(a) - y * np.sin(a), cy + x * np.sin(a) + y * np.cos(a)]
for (tid, f, tag, A) in d['shapes']['R_racket_face']:
    P = tf(ell_pts(float(A['cx']), float(A['cy']), float(A['rx']), float(A['ry']), float(A['rotation'])), f); (cx, cy), (w, h), ang = cv2.fitEllipse(P.astype(np.float32))
    out['racket'].setdefault(f, {})['face'] = dict(c=np.array([cx, cy]), axes=(w / 2, h / 2), ang=ang, outside=A['outside'] == '1', pts=P)
for (tid, f, tag, A) in d['shapes']['R_racket_handle']:
    b = np.array([[float(A['xtl']), float(A['ytl'])], [float(A['xbr']), float(A['ybr'])]]); out['racket'].setdefault(f, {})['handle'] = dict(c=tf(b.mean(0), f)[0], box=tf(np.array([[b[0, 0], b[0, 1]], [b[1, 0], b[0, 1]], [b[1, 0], b[1, 1]], [b[0, 0], b[1, 1]]]), f), outside=A['outside'] == '1')
for (tid, f, tag, A) in d['shapes']['R_racket_bbox']:
    b = np.array([[float(A['xtl']), float(A['ytl'])], [float(A['xbr']), float(A['ybr'])]]); out['racket'].setdefault(f, {})['bbox'] = tf(b, f)
for (tid, f, tag, A) in d['shapes']['B_ball']:
    c = tf([float(A['cx']), float(A['cy'])], f)[0]; out['ball'][f] = dict(c=c, r=0.5 * (float(A['rx']) + float(A['ry'])), outside=A['outside'] == '1', occ=A['occluded'] == '1', trk=tid)
for lab in ('B_contact_racket', 'B_contact_ground'):
    out['shapes'][lab] = [(tid, f, tf([float(v) for v in A['points'].split(',')], f)[0], A['outside'] == '1') for (tid, f, tag, A) in d['shapes'][lab]]
pickle.dump(out, open(SP + '/lab2/labels_ref.pkl', 'wb'))
print('contact_racket', [(t, f, np.round(p, 1), o) for t, f, p, o in out['shapes']['B_contact_racket']])
print('contact_ground', [(t, f, np.round(p, 1), o) for t, f, p, o in out['shapes']['B_contact_ground']])
bf = sorted(f for f, v in out['ball'].items() if not v['outside']); print('ball visible frames', bf[0], bf[-1], len(bf)); 
import itertools
runs = [(g[0][1], g[-1][1]) for g in (list(v) for k, v in itertools.groupby(enumerate(bf), lambda t: t[1] - t[0])) for g in [[(i, x) for i, x in v]]] if False else None
gaps = [(a, b) for a, b in zip(bf[:-1], bf[1:]) if b - a > 1]; print('ball gaps', gaps)
print('racket frames outside:', [f for f in range(N) if out['racket'][f]['face']['outside']][:50])
# QA: the transferred labels warped on the reference-frame stabilised raw frames
for f in (30, 100, 184):
    im = cv2.warpPerspective(cv2.imread(SP + '/raw/r%04d.png' % (f + 1)), H[f], (464, 848))
    for j, dd in out['skel'].items():
        if f in dd: cv2.circle(im, tuple(int(v) for v in dd[f][0]), 2, (0, 255, 255), -1)
    P = out['racket'][f]['face']['pts'].astype(np.int32); cv2.polylines(im, [P.reshape(-1, 1, 2)], True, (255, 0, 255), 1)
    if f in out['ball']: cv2.circle(im, tuple(int(v) for v in out['ball'][f]['c']), 5, (0, 255, 0), 1)
    cv2.imwrite(SP + '/lab2/reg_%d.png' % f, im[200:700])

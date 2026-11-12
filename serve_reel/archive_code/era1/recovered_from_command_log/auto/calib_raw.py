"""Camera from the court itself (hand-held clip, stabilised to frame 0). World: x along net (to the right in the image), y away from camera, z up, origin = net centre on the ground."""
import numpy as np, cv2
from scipy.optimize import least_squares
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
cx0, cy0 = 232.0, 424.0
PTS = [((-4.115, -6.4, 0.0), (47, 499), 2.5), ((-4.115, 0.0, 0.0), (95, 468), 4.0), ((0, -6.4, 0.0), (295, 502), 2.5), ((0, 0, 0.0), (262, 470), 3.0), ((0, 0, 0.914), (262, 431), 2.5)]
BASELINE_Y = 580.5
def rotmat(psi, th, ph):
    f = np.array([np.cos(th) * np.sin(psi), np.cos(th) * np.cos(psi), -np.sin(th)]); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); d = np.cross(f, r)
    c, s = np.cos(ph), np.sin(ph); r2, d2 = c * r + s * d, -s * r + c * d; return np.stack([r2, d2, f])
def project(p, X):
    f, psi, th, ph, Cx, Cy, Cz = p; R = rotmat(psi, th, ph); Xc = (np.atleast_2d(X) - [Cx, Cy, Cz]) @ R.T; return np.c_[f * Xc[:, 0] / Xc[:, 2] + cx0, f * Xc[:, 1] / Xc[:, 2] + cy0]
def res(p):
    r = []
    for X, uv, s in PTS: r += list((project(p, X)[0] - uv) / s)
    r.append((project(p, (0, -11.885, 0))[0, 1] - BASELINE_Y) / 2.5); r.append((p[6] - 1.4) / 0.6); r.append((p[0] - 800) / 400.0); r.append(p[3] / 0.05)
    return np.array(r)
best = None
for f0 in (500, 700, 1000, 1400):
    for d0 in (4, 6, 9):
        p0 = [f0, 0.0, 0.02, 0.0, 0.0, -d0 - 11.885 * 0 - 0.0, 1.4]; p0[5] = -(d0 + 11.885) + 0.0
        s = least_squares(res, p0, loss='soft_l1')
        if best is None or s.cost < best.cost: best = s
p = best.x; print('f %.0f yaw %.2f pitch %.2f roll %.2f deg  C = (%.2f, %.2f, %.2f)' % (p[0], *np.degrees(p[1:4]), *p[4:]), 'cost', round(best.cost, 2))
for X, uv, s in PTS: print(X, uv, np.round(project(p, X)[0], 1))
print('baseline y', project(p, (0, -11.885, 0))[0], 'net top far end', project(p, (5.5, 0, 1.07))[0])
R = rotmat(*p[1:4]); K = np.array([[p[0], 0, cx0], [0, p[0], cy0], [0, 0, 1.0]]); C = p[4:7]
np.savez(SP + '/auto/camera_raw.npz', K=K, R=R, cam=C)
# overlay court model
bg = cv2.imread(SP + '/auto/background_stab.png'); W_, L_ = 4.115, 11.885
segs = [((-W_, -L_), (W_, -L_)), ((-W_, -6.4), (W_, -6.4)), ((0, -6.4), (0, 0)), ((-W_, -L_), (-W_, L_)), ((W_, -L_), (W_, L_)), ((-5.485, -L_), (-5.485, L_)), ((5.485, -L_), (5.485, L_)), ((-W_, 6.4), (W_, 6.4))]
for (a, b) in segs:
    t = np.linspace(0, 1, 40); P = np.array([[a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, 0] for u in t]); uv = project(p, P)
    cv2.polylines(bg, [uv.astype(np.int32).reshape(-1, 1, 2)], False, (0, 255, 255), 1)
net = project(p, np.array([[-6.4, 0, 1.07], [6.4, 0, 1.07], [6.4, 0, 0.0], [-6.4, 0, 0.0]])); cv2.polylines(bg, [net.astype(np.int32).reshape(-1, 1, 2)], True, (255, 255, 0), 1)
cv2.imwrite(SP + '/auto/court_overlay.png', cv2.resize(bg[330:700], None, fx=2, fy=2))

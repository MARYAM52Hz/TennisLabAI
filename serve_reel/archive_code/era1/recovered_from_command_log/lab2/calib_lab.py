"""Camera + per-frame registration from the CVAT court-line labels (our video, 464x848, 237 frames).
Line assignment (world: x along net, y away from camera, z up, origin net centre on the ground):
 C_baseline_top  = near baseline y=-11.885 | C_service_line_right = near service line y=-6.40 | C_service_line_left = far service line y=+6.40 | C_baseline_bottom = far baseline y=+11.885
 C_center_service_line x=0 | C_singles_sideline_left/right x=-/+4.115 | C_doubles_sideline_left/right x=-/+5.485 (all on the ground)"""
import pickle, numpy as np, cv2
from scipy.optimize import least_squares
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
d = pickle.load(open(SP + '/lab2/labels2.pkl', 'rb')); court = d['court']
LINES = {'C_baseline_top': ('y', -11.885), 'C_service_line_right': ('y', -6.40), 'C_service_line_left': ('y', 6.40), 'C_baseline_bottom': ('y', 11.885), 'C_center_service_line': ('x', 0.0),
         'C_singles_sideline_left': ('x', -4.115), 'C_singles_sideline_right': ('x', 4.115), 'C_doubles_sideline_left': ('x', -5.485), 'C_doubles_sideline_right': ('x', 5.485)}
cx0, cy0 = 232.0, 424.0
def rotmat(psi, th, ph):
    f = np.array([np.cos(th) * np.sin(psi), np.cos(th) * np.cos(psi), -np.sin(th)]); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); dn = np.cross(f, r)
    c, s = np.cos(ph), np.sin(ph); return np.stack([c * r + s * dn, -s * r + c * dn, f])
def project(p, X):
    f, psi, th, ph, Cx, Cy, Cz = p[:7]; R = rotmat(psi, th, ph); Xc = (np.atleast_2d(X) - [Cx, Cy, Cz]) @ R.T; return np.c_[f * Xc[:, 0] / Xc[:, 2] + cx0, f * Xc[:, 1] / Xc[:, 2] + cy0]
def line_dist(P, a, b):                                           # distance of points P to the infinite line through a,b
    n = np.array([-(b[1] - a[1]), b[0] - a[0]]); n = n / np.linalg.norm(n); return (P - a) @ n
def world_pts(kind, v, n=40):
    t = np.linspace(-1, 1, n)
    return np.array([[v, 11.885 * s, 0.0] for s in t]) if kind == 'x' else np.array([[5.485 * s, v, 0.0] for s in t])
def residuals(p, f=0, names=None):
    r = []
    for nm, (kind, v) in LINES.items():
        if names and nm not in names: continue
        a, b = dict(court[nm])[f]; W = world_pts(kind, v); uv = project(p, W); ok = (W[:, 1] > -12.5) & (np.abs(W[:, 0]) < 5.6)
        # keep only the part of the world line that lies in front of the camera and inside the image box
        ok &= (uv[:, 0] > -50) & (uv[:, 0] < 520) & (uv[:, 1] > 300) & (uv[:, 1] < 900)
        if ok.sum() >= 3: r += list(line_dist(uv[ok], np.array(a), np.array(b)) / 1.5)
        S = np.array(a) + (np.array(b) - np.array(a)) * np.linspace(0, 1, 12)[:, None]; r.append(0.0)
        # labelled samples back to the projected line: use the two extreme projected points of the world line
        if ok.sum() >= 2: pa, pb = uv[ok][0], uv[ok][-1]; r += list(line_dist(S, pa, pb) / 1.5)
    r.append((p[6] - 1.5) / 1.5); return np.array(r)
if __name__ == '__main__':
    best = None
    for f0 in (600, 800, 1100):
        for d0 in (5, 8):
            p0 = [f0, 0.04, 0.03, 0.0, -1.5, -(d0 + 11.885), 1.6]; s = least_squares(residuals, p0, loss='soft_l1', f_scale=2.0)
            if best is None or s.cost < best.cost: best = s
    p = best.x; print('f %.0f yaw %.2f pitch %.2f roll %.2f deg  C=(%.2f, %.2f, %.2f)  cost %.2f  rms resid %.2f px' % (p[0], *np.degrees(p[1:4]), *p[4:7], best.cost, np.sqrt((residuals(p)[:-1] ** 2).mean()) * 1.5))
    for nm in LINES:
        rr = residuals(p, 0, [nm]); print('  %-26s rms %.2f px' % (nm, np.sqrt((rr[:-1][rr[:-1] != 0] ** 2).mean()) * 1.5))
    R = rotmat(*p[1:4]); K = np.array([[p[0], 0, cx0], [0, p[0], cy0], [0, 0, 1.0]]); np.savez(SP + '/lab2/camera_lab.npz', K=K, R=R, cam=p[4:7], p=p)
    old = np.load(SP + '/auto/camera_raw.npz'); print('previous (hand-picked) camera: f %.0f C=%s' % (old['K'][0, 0], np.round(old['cam'], 2)))
    bg = cv2.imread(SP + '/auto/background_stab.png'); 
    for nm, (kind, v) in LINES.items():
        uv = project(p, world_pts(kind, v, 80)); ok = (uv[:, 0] > 0) & (uv[:, 0] < 464) & (uv[:, 1] > 380) & (uv[:, 1] < 848); cv2.polylines(bg, [uv[ok].astype(np.int32).reshape(-1, 1, 2)], False, (0, 255, 255), 1)
        a, b = dict(court[nm])[0]; cv2.line(bg, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (255, 0, 255), 1)
    net = project(p, np.array([[-6.4, 0, 1.07], [6.4, 0, 1.07], [6.4, 0, 0.0], [-6.4, 0, 0.0]])); cv2.polylines(bg, [net.astype(np.int32).reshape(-1, 1, 2)], True, (255, 255, 0), 1)
    cv2.imwrite(SP + '/lab2/court_overlay_lab.png', cv2.resize(bg[400:640], None, fx=2.2, fy=2.2))

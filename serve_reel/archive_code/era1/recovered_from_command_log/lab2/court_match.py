"""Court-first matching: how far are the CVAT court labels from the court lines actually visible in OUR video?  For each labelled court line, search the best perpendicular offset
in the line-evidence image (top-hat of the stabilised/unstabilised frame) and fit a 2D correction (similarity + full homography) from label coordinates to image coordinates."""
import pickle, numpy as np, cv2
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
d = pickle.load(open(SP + '/lab2/labels2.pkl', 'rb')); court = d['court']
def evidence(f):
    g = cv2.cvtColor(cv2.imread(SP + f'/raw/r{f + 1:04d}.png'), cv2.COLOR_BGR2GRAY).astype(np.float32)
    th = cv2.morphologyEx(g, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))); return cv2.GaussianBlur(th, (0, 0), 1.0)
def sample(img, x, y): return cv2.remap(img, x.astype(np.float32).reshape(1, -1), y.astype(np.float32).reshape(1, -1), cv2.INTER_LINEAR, borderValue=0)[0]
def best_offsets(f, names=('C_baseline_top', 'C_service_line_right', 'C_service_line_left', 'C_center_service_line', 'C_singles_sideline_left', 'C_singles_sideline_right')):
    ev = evidence(f); out = {}
    for nm in names:
        (x1, y1), (x2, y2) = dict(court[nm])[f]; L = np.hypot(x2 - x1, y2 - y1); t = np.linspace(0.08, 0.92, 80); px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t; n = np.array([-(y2 - y1), x2 - x1]) / L
        offs = np.arange(-12, 12.01, 0.5); sc = [sample(ev, px + n[0] * o, py + n[1] * o).mean() for o in offs]; k = int(np.argmax(sc))
        base = np.median(sc); out[nm] = (float(offs[k]), float(sc[k] / (base + 1e-6)), n)
    return out
if __name__ == '__main__':
    for f in (0, 60, 120, 180, 230):
        o = best_offsets(f); print('frame', f, {k[2:]: (round(v[0], 1), round(v[1], 1)) for k, v in o.items()})

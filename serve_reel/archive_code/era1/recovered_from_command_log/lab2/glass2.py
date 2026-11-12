"""Glossy white 'mannequin glass' look for the REAL player: silhouette from the skeleton-guided segmentation, volume from an inflated distance field + the real image's own folds,
key/fill light, Blinn specular, fresnel rim, mirror-like reflection of the stadium, contact shadow and floor reflection."""
import numpy as np, cv2
W2, H2 = 928, 1696
def sstep(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def render(f, plate, mask, im_ref, M, P=None):
    p = dict(R=15.0, bigR=20.0, ks=0.9, kg=0.30); p.update(P or {})
    y0 = 0
    J = M.joints(f); uv = np.array([M.project(J[n])[0][0] for n in J if n != 'head']) * 2.0
    x0, x1 = int(max(0, uv[:, 0].min() - 140)), int(min(W2, uv[:, 0].max() + 140)); y0, y1 = int(max(0, uv[:, 1].min() - 150)), int(min(H2, uv[:, 1].max() + 170))
    sl = (slice(y0, y1), slice(x0, x1)); h, w = y1 - y0, x1 - x0
    m = cv2.resize(mask.astype(np.float32) / 255, (W2, H2), interpolation=cv2.INTER_CUBIC)[sl]; im = cv2.resize(im_ref, (W2, H2), interpolation=cv2.INTER_CUBIC)[sl].astype(np.float32) / 255
    a = sstep(cv2.GaussianBlur(m, (0, 0), 2.0), 0.40, 0.60); a = cv2.GaussianBlur(a, (0, 0), 0.8)
    L = cv2.cvtColor((im * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    b = (a > 0.5).astype(np.uint8); d = cv2.distanceTransform(b, cv2.DIST_L2, 5); t = np.clip(d / p['R'], 0, 1); hh = np.sqrt(1 - (1 - t) ** 2) * p['R']
    big = cv2.GaussianBlur(a, (0, 0), p['bigR']) * 26.0                                       # broad inflation: torso/thighs read rounder than limbs
    det = (cv2.GaussianBlur(L, (0, 0), 1.6) - cv2.GaussianBlur(L, (0, 0), 6.0)) * 18.0 * a    # the player's own folds / muscle shading
    H = cv2.GaussianBlur(hh, (0, 0), 2.2) + 0.55 * big + det
    gx = cv2.Sobel(H, cv2.CV_32F, 1, 0, ksize=3) / 8.0; gy = cv2.Sobel(H, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    nx, ny, nz = -gx * 1.1, -gy * 1.1, np.ones_like(gx); nn = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nn, ny / nn, nz / nn
    Lk = np.array([-0.45, -0.70, 0.55]); Lk /= np.linalg.norm(Lk); Lf = np.array([0.65, -0.15, 0.74]); Lf /= np.linalg.norm(Lf)
    dk = np.clip(nx * Lk[0] + ny * Lk[1] + nz * Lk[2], 0, 1); df = np.clip(nx * Lf[0] + ny * Lf[1] + nz * Lf[2], 0, 1)
    ao = 1 - 0.40 * np.clip(cv2.GaussianBlur(a, (0, 0), 9) - a * 0.55, 0, 1) * 1.5                      # crevices (between legs / under arm) a bit darker
    diff = (0.30 + 0.62 * dk + 0.22 * df) * ao
    base = np.array([0.93, 0.945, 0.97], np.float32)                                              # BGR white, slightly cool
    col = base[None, None, :] * diff[..., None]
    Hk = Lk + np.array([0, 0, 1.0]); Hk /= np.linalg.norm(Hk); Hf = Lf + np.array([0, 0, 1.0]); Hf /= np.linalg.norm(Hf)
    sp1 = np.clip(nx * Hk[0] + ny * Hk[1] + nz * Hk[2], 0, 1) ** 70 * 1.0 + np.clip(nx * Hk[0] + ny * Hk[1] + nz * Hk[2], 0, 1) ** 12 * 0.18
    sp2 = np.clip(nx * Hf[0] + ny * Hf[1] + nz * Hf[2], 0, 1) ** 55 * 0.55
    col += ((sp1 + sp2) * p['ks'])[..., None]
    fres = (1 - nz) ** 2.2; env = cv2.GaussianBlur(plate[sl], (0, 0), 16)
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)); envs = cv2.remap(env, xx + nx * 90, yy + ny * 90 - 25, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    kmix = (0.07 + 0.55 * fres)[..., None]; col = col * (1 - kmix) + envs * 1.25 * kmix + (fres * 0.28)[..., None] * np.array([1.0, 0.98, 0.93], np.float32)
    # glassy inner luminosity: a faint cool-white glow just inside the silhouette
    inner = np.clip(a - cv2.GaussianBlur(a, (0, 0), 10), 0, 1); col += (inner * 0.10)[..., None]
    col = np.clip(col, 0, 1.0)
    full = plate.copy(); acc = full[sl]
    # soft contact shadow + floor reflection (computed on the full frame)
    pel = (J['left_ankle'] + J['right_ankle']) / 2; gpx = M.project(np.array([[pel[0], pel[1], 0.0]]))[0][0] * 2.0; yg = float(gpx[1]); cxg = float(gpx[0])
    sh = np.zeros((H2, W2), np.float32); cv2.ellipse(sh, (int(cxg), int(yg + 6)), (int(70), int(15)), 0, 0, 360, 1.0, -1, cv2.LINE_AA); sh = cv2.GaussianBlur(sh, (0, 0), 9) * 0.42
    full = full * (1 - sh[..., None]) + 0.0 * sh[..., None]
    fig = np.zeros((H2, W2, 3), np.float32); fa = np.zeros((H2, W2), np.float32); fig[sl] = col; fa[sl] = a
    Mf = np.float32([[1, 0, 0], [0, -1, 2 * yg]]); rf = cv2.warpAffine(fig, Mf, (W2, H2), flags=cv2.INTER_LINEAR); ra = cv2.warpAffine(fa, Mf, (W2, H2), flags=cv2.INTER_LINEAR)
    rows = np.arange(H2, dtype=np.float32)[:, None]; fade = np.clip(1 - (rows - yg) / 210.0, 0, 1) ** 1.6 * (rows > yg) * p['kg']; ra = cv2.GaussianBlur(ra, (0, 0), 2.5) * fade
    full = full * (1 - ra[..., None]) + rf * ra[..., None]
    # outer glow + body
    glow = cv2.GaussianBlur(fa, (0, 0), 14) * (1 - fa); full = full + glow[..., None] * np.array([0.10, 0.11, 0.12], np.float32)
    full = full * (1 - fa[..., None]) + fig * fa[..., None]
    return full

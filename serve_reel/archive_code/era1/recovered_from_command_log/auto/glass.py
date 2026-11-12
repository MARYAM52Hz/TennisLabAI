"""White-glass version of the REAL player: matte from the raw video, shading from the real image (own physique), frosted-glass look, composited over the stadium plate (+ racket/ball layer)."""
import numpy as np, cv2, sys, os
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
D = np.load(SP + '/auto/matte_raw.npz'); MM, F0 = D['M'], int(D['F0']); S = np.load(SP + '/auto/stab.npy', mmap_mode='r')
W2, H2 = 928, 1696
def up(a, interp=cv2.INTER_CUBIC): return cv2.resize(a, (W2, H2), interpolation=interp)
def glass_frame(f, plate, rb=None, params=None):
    p = dict(milk=0.66, shade=0.55, rim=0.95, glow=0.55, refr=10.0, detail=0.22); p.update(params or {})
    im = up(np.array(S[f]), cv2.INTER_LANCZOS4).astype(np.float32) / 255; L = cv2.cvtColor((im * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    a0 = up(MM[f - F0].astype(np.float32) / 255, cv2.INTER_CUBIC)
    try: a = cv2.ximgproc.guidedFilter((im * 255).astype(np.uint8), a0, 6, 1e-3 * 255 * 255 / 255.0)
    except Exception: a = cv2.GaussianBlur(a0, (0, 0), 1.0)
    a = np.clip((a - 0.35) / 0.4, 0, 1); a = cv2.GaussianBlur(a, (0, 0), 0.9)                                  # crisp but soft edge
    bg = plate.astype(np.float32) / 255
    # refraction: the background seen through the body is pushed along the matte gradient
    ab = cv2.GaussianBlur(a, (0, 0), 3.0); gx = cv2.Sobel(ab, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(ab, cv2.CV_32F, 0, 1, ksize=3)
    xx, yy = np.meshgrid(np.arange(W2, dtype=np.float32), np.arange(H2, dtype=np.float32)); bgr = cv2.remap(bg, xx + gx * p['refr'] * 4, yy + gy * p['refr'] * 4, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    frost = cv2.GaussianBlur(bgr, (0, 0), 7.0)
    white = np.array([0.97, 0.985, 1.0], np.float32)
    # own physique -> shading (dark shorts / shadows stay a little darker, shirt stays bright) + fine contours from the real image
    Ls = cv2.GaussianBlur(L, (0, 0), 1.4); sh = 1 - p['shade'] * np.clip(1 - (Ls - 0.05) / 0.80, 0, 1) ** 1.2 * 0.55
    lap = cv2.GaussianBlur(L, (0, 0), 1.0) - cv2.GaussianBlur(L, (0, 0), 3.0); det = np.clip(0.5 + lap * 4.0, 0, 1)
    body = (frost * (1 - p['milk']) + white * p['milk']) * sh[..., None] * (1 - p['detail'] + p['detail'] * 2 * det[..., None]).clip(0.6, 1.15)
    # rim light + fresnel-like bright edge + glow
    er = cv2.erode(a, np.ones((5, 5), np.uint8)); rim = np.clip(a - er, 0, 1); rim = cv2.GaussianBlur(rim, (0, 0), 1.2); rim = rim / (rim.max() + 1e-6)
    inner = cv2.GaussianBlur(a, (0, 0), 9.0); fres = np.clip(a - inner, 0, 1) ** 1.3                                       # brighter toward the silhouette
    glow = cv2.GaussianBlur(rim, (0, 0), 9.0) * (1 - a)
    tint = np.array([1.0, 0.97, 0.88], np.float32)[::-1]                                                                  # BGR: cool white
    out = bg + glow[..., None] * p['glow'] * np.array([1.0, 0.92, 0.75], np.float32)                                      # soft cool glow around the figure (BGR)
    ain = (a * 0.93)[..., None]; out = out * (1 - ain) + body * ain
    out = out + (rim * p['rim'])[..., None] * np.array([1.0, 0.99, 0.95], np.float32) + (fres * 0.35)[..., None] * np.array([1.0, 0.97, 0.9], np.float32)
    # specular streaks on the light side
    nx, ny = -gx, -gy; spec = np.clip(nx * -0.6 + ny * -0.8, 0, None); spec = cv2.GaussianBlur(spec, (0, 0), 1.5); spec = (spec / (spec.max() + 1e-6)) ** 2 * (a > 0.3)
    out = out + (spec * 0.55)[..., None]
    if rb is not None:
        rgba = rb.astype(np.float32) / 255; al = rgba[..., 3:4]; out = out * (1 - al) + rgba[..., :3] * al
    return np.clip(out, 0, 1)
if __name__ == '__main__':
    plate = cv2.imread(SP + '/lay/plate.png'); f = int(sys.argv[1]); rbp = SP + f'/lay/rb{f:04d}.png'; rb = cv2.imread(rbp, cv2.IMREAD_UNCHANGED) if os.path.exists(rbp) else None
    o = glass_frame(f, plate, rb); cv2.imwrite(SP + f'/auto/glass_{f}.png', (o * 255).astype(np.uint8)); print('ok', o.shape)

"""Compositor for the two films.  usage: python3 -I compose.py FILM(1|2) OUTDIR [--frames a,b,c] (test: writes only the listed *timeline* indices)
Timeline: play 0..HA, hold A (10 s), play HA+1..236, hold B (10 s); eased stop / restart + a slow push-in during holds."""
import numpy as np, cv2, pickle, sys, os
from scipy.interpolate import CubicSpline
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
W2, H2 = 928, 1696; FPS = 30; HOLD = 300; HA = 76; NF = 237; TRAIL = 60
film = int(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
mot = pickle.load(open(SP + '/lab2/motion_lab.pkl', 'rb')); from motion_lab import LabMotion
M = LabMotion(); M.__dict__.update(mot); LAY = SP + '/lab'
BALL_C = (30, 225, 255); RACK_C = (255, 215, 40)                                       # BGR: neon yellow ball, neon cyan racket
# ---------- paths (output pixel coords)
bpx = mot['ball_px'] * 2.0; bok = mot['ball_ok']; hpx = mot['head_px'] * 2.0
def ball_xy(t):
    i = int(np.floor(t)); j = min(i + 1, NF - 1); w = t - i
    if i < 0 or not (bok[i] and bok[j]): return None
    return (1 - w) * bpx[i] + w * bpx[j]
cs_h = CubicSpline(np.arange(NF), hpx, axis=0)
def rack_xy(t): return cs_h(np.clip(t, 0, NF - 1))
def trail_pts(fn, t0, t1, step=1 / 3.):
    ts = np.arange(t0, t1 + 1e-6, step); P = []; T_ = []
    for t in ts:
        p = fn(t)
        if p is None: P.append(None); T_.append(t)
        else: P.append(p); T_.append(t)
    return P, np.array(T_)
def draw_trail(canvas, P, alpha, color, wmax=7.0, wmin=1.6):
    """P list of points (or None for breaks); alpha per point in [0,1]; draws a glowing ribbon into the float canvas (BGR 0..1, additive core)"""
    core = np.zeros((H2, W2, 3), np.float32); col = np.array(color, np.float32) / 255
    for k in range(1, len(P)):
        if P[k] is None or P[k - 1] is None: continue
        a = 0.5 * (alpha[k] + alpha[k - 1])
        if a <= 0.01: continue
        w = wmin + (wmax - wmin) * a; c = col * a; hot = np.minimum(c * 0.6 + a * 0.55, 1)
        cv2.line(core, tuple(int(round(v * 16)) for v in P[k - 1]), tuple(int(round(v * 16)) for v in P[k]), tuple(float(x) for x in c), int(round(w)), cv2.LINE_AA, shift=4)
        cv2.line(core, tuple(int(round(v * 16)) for v in P[k - 1]), tuple(int(round(v * 16)) for v in P[k]), tuple(float(x) for x in hot), max(1, int(round(w * 0.38))), cv2.LINE_AA, shift=4)
    glow = core + 1.1 * cv2.GaussianBlur(core, (0, 0), 5) + 1.0 * cv2.GaussianBlur(core, (0, 0), 14) + 0.7 * cv2.GaussianBlur(core, (0, 0), 30)
    canvas[:] = 1 - (1 - canvas) * (1 - np.clip(glow, 0, 1))
def trails_for(canvas, tau, mode, hold_k=0):
    """mode 'play': last 2 s of the path (only after `since`); mode 'hold': whole serve path, linear fade over 10 s"""
    if mode == 'play':
        t0 = max(tau - TRAIL, play_since(tau)); 
        for fn, col in ((ball_xy, BALL_C), (rack_xy, RACK_C)):
            P, ts = trail_pts(fn, t0, tau); al = np.clip(1 - (tau - ts) / TRAIL, 0, 1) ** 1.3; draw_trail(canvas, P, al, col)
            if P and P[-1] is not None and al[-1] > 0.05: cv2.circle(canvas, tuple(int(v) for v in P[-1]), 5, (1, 1, 1), -1, cv2.LINE_AA)
    else:
        key, = [hold_k]; fade = max(0.0, 1 - hold_k_t[0] / HOLD); spec = HOLD_SPEC[key]
        for fn, col, (a0, a1) in ((ball_xy, BALL_C, spec['ball']), (rack_xy, RACK_C, spec['rack'])):
            ext = min(1.0, hold_k_t[0] / 14.0); t0 = a1 - (a1 - a0) * ext                                  # the full path draws in over the first 0.45 s
            P, ts = trail_pts(fn, t0, a1); g = 0.40 + 0.60 * (ts - a0) / max(a1 - a0, 1); draw_trail(canvas, P, np.clip(g, 0, 1) * fade, col, wmax=7.0, wmin=2.2)
HOLD_SPEC = {0: dict(ball=(0, 76), rack=(8, 46)), 1: dict(ball=(148, 236), rack=(164, 214))}
SINCE = [0.0]; hold_k_t = [0]
def play_since(tau): return SINCE[0]
# ---------- layers
plate = cv2.imread(LAY + '/plate.png').astype(np.float32) / 255
def over(base, rgba): a = rgba[..., 3:4]; return base * (1 - a) + rgba[..., :3] * a
def load_rgba(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED); return None if im is None else im.astype(np.float32) / 255
_glass_cache = {}
if film == 2:
    import glass2
    SEGM = np.load(SP + '/lab2/seg_lab2.npz')['M']; FR = np.load(SP + '/lab2/frames_ref.npy', mmap_mode='r')
def base_frame(f):
    """plate + player (skeleton | glass) for integer frame f -> float BGR; racket+ball returned separately"""
    rb = load_rgba(f'{LAY}/rb{f:04d}.png')
    if film == 1:
        im = over(plate, load_rgba(f'{LAY}/sk{f:04d}.png'))
    else: im = glass2.render(f, plate, SEGM[f], np.array(FR[f]), M)
    return im, rb
def frame_at(tau):
    f0 = int(np.floor(tau)); f1 = min(f0 + 1, NF - 1); w = tau - f0
    a, ra = base_frame(f0)
    if w > 1e-3 and f1 != f0:
        b, rb_ = base_frame(f1); a = a * (1 - w) + b * w; ra = ra * (1 - w) + rb_ * w if (ra is not None and rb_ is not None) else ra
    return a, ra
def finish(im, rb): return im if rb is None else over(im, rb)
# ---------- timeline
def ease_out(n): s = np.linspace(0, 1, n + 1)[1:]; return np.cumsum((1 - s) ** 1.5) / np.sum((1 - s) ** 1.5)
timeline = []                                                           # (tau, mode, hold_index, hold_t)
def play(a, b, ease_end=False, ease_start=False):
    taus = list(range(a, b + 1))
    if ease_end:                                                       # last 12 frames decelerate into the hold
        k = 12; t0 = b - k; cur = t0 + (b - t0) * np.concatenate([[0], ease_out(k)])[1:]; taus = list(range(a, t0)) + list(cur)
    if ease_start:
        k = 12; cur = a + (b - a) * 0; taus = [a + (np.linspace(0, 1, k + 1)[1:][i] ** 1.4) * 1.0 * (i + 1) * 0 + a + (i + 1) * (0.2 + 0.8 * (i + 1) / k) for i in range(k)] + list(range(a + 12, b + 1))
    for t in taus: timeline.append((float(t), 'play', -1, 0))
play(0, HA, ease_end=True)
for k in range(HOLD): timeline.append((float(HA), 'hold', 0, k))
SINCE_AFTER = {len(timeline): float(HA + 1)}
play(HA + 1, NF - 1, ease_end=True)
for k in range(HOLD): timeline.append((float(NF - 1), 'hold', 1, k))
print('timeline frames', len(timeline), '= %.1f s' % (len(timeline) / FPS), flush=True)
only = None
if '--frames' in sys.argv: only = [int(x) for x in sys.argv[sys.argv.index('--frames') + 1].split(',')]
cache = {}
for n, (tau, mode, hk, ht) in enumerate(timeline):
    if only is not None and n not in only: continue
    png = f'{OUT}/c{n:05d}.png'
    if os.path.exists(png) and only is None: continue
    if n in SINCE_AFTER: SINCE[0] = SINCE_AFTER[n]
    key = (round(tau, 3), mode, hk)
    if mode == 'hold' and key in cache: im, rb = cache[key]
    else:
        im, rb = frame_at(tau)
        if mode == 'hold': cache[key] = (im, rb)
    im = im.copy(); hold_k_t[0] = ht; trails_for(im, tau, mode, hk); out = finish(im, rb)
    if mode == 'hold':                                                  # slow push-in and back out during the 10 s
        z = 1 + 0.05 * np.sin(np.pi * ht / HOLD) ** 1.2; c = np.array([mot['head_px'][int(tau)][0] * 2, mot['head_px'][int(tau)][1] * 2 + 250.0]); A = np.array([[z, 0, c[0] * (1 - z)], [0, z, c[1] * (1 - z)]], np.float32)
        out = cv2.warpAffine(out, A, (W2, H2), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    cv2.imwrite(png, (np.clip(out, 0, 1) * 255).astype(np.uint8))
    if n % 50 == 0: print('frame', n, flush=True)

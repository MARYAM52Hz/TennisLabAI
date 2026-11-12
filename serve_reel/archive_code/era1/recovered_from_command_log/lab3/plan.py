"""Frame plan for the orbit reel: per output frame -> source time tau, camera (position, target, lens), skeleton/racket/ball visibility and the 3D glowing trails."""
import numpy as np, json, sys
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
from motion_lab2 import Motion2, nrm
M = Motion2(); FPS = 30
def smooth(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def lens_from_fov(h): return 36.0 / (2 * np.tan(np.radians(h) / 2))
COL = dict(A_ball=(1.0, 0.86, 0.12), A_rack=(0.10, 0.85, 1.0), B_ball=(1.0, 0.42, 0.08), B_rack=(1.0, 0.18, 0.80), wrist=(1.0, 0.95, 0.85))
def path(fn, t0, t1, step=0.25): ts = np.arange(t0, t1 + 1e-6, step); P = np.array([fn(t) for t in ts]); return ts, P
ballA = path(M.ball, 4.0, 62.0); ballB = path(M.ball, 149.0, 212.0); rackA = path(M.head_at, 6.0, 48.0); rackB = path(M.head_at, 164.0, 214.0)
wristB = lambda t: M.jf('right_wrist', t)
tcB = M.tcs['B']; tcA = M.tcs['A']
frames = []
# ---------------- Part 1: slow-motion orbit around serve B ----------------
N1 = 210; um = 0.55; uu = np.linspace(0, 1, 2001); vel = 0.38 - 0.31 * np.exp(-((uu - um) / 0.17) ** 2); cum = np.concatenate([[0], np.cumsum((vel[1:] + vel[:-1]) / 2 * np.diff(uu))])
K = 27.0 / cum[-1]; tau0 = tcB - K * np.interp(um, uu, cum)
pivot = (M.head_at(tcB) + M.jf('top_spine', tcB)) / 2; pivot = np.array([pivot[0], pivot[1], 2.15])
o0 = M.C_cam - pivot; R0 = np.linalg.norm(o0); phi0 = np.arctan2(o0[0], -o0[1]); e0 = np.arcsin(o0[2] / R0)
TRAIL_SRC = 17.0
def cam_state(u):
    ph = phi0 + np.radians(215) * smooth(u) ** 1.0 * 1.0; ph = phi0 + (np.radians(112) - phi0) * smooth(u / 0.55) if u <= 0.55 else np.radians(112) + np.radians(98) * smooth((u - 0.55) / 0.45)
    e = e0 + (np.radians(17) - e0) * smooth(u / 0.55) if u <= 0.55 else np.radians(17) + np.radians(-4) * smooth((u - 0.55) / 0.45)
    R = R0 + (4.1 - R0) * smooth(u / 0.55) if u <= 0.55 else 4.1 + 1.0 * smooth((u - 0.55) / 0.45)
    fov = 33.0 + (40.0 - 33.0) * smooth(u / 0.55) if u <= 0.55 else 40.0
    d = np.array([np.sin(ph) * np.cos(e), -np.cos(ph) * np.cos(e), np.sin(e)]); return pivot + d * R, pivot, fov
for n in range(N1):
    u = n / (N1 - 1); tau = tau0 + K * np.interp(u, uu, cum); cp, tg, fov = cam_state(u); trails = []
    for (ts, P), col, nm in ((ballB, COL['B_ball'], 'ball'), (rackB, COL['B_rack'], 'racket')):
        sel = (ts <= tau) & (ts >= tau - TRAIL_SRC)
        if sel.sum() >= 2: trails.append(dict(pts=P[sel].tolist(), inten=(1 - (tau - ts[sel]) / TRAIL_SRC).clip(0, 1).tolist(), col=col, head=True, name=nm))
    ts = np.arange(max(tau - TRAIL_SRC * 0.75, 0), tau + 1e-6, 0.25)
    if len(ts) >= 2: trails.append(dict(pts=[wristB(t).tolist() for t in ts], inten=(1 - (tau - ts) / (TRAIL_SRC * 0.75)).clip(0, 1).tolist(), col=COL['wrist'], head=False, name='wrist'))
    frames.append(dict(part=1, tau=float(tau), cam=cp.tolist(), target=tg.tolist(), fov=float(fov), skel='live', live_racket=True, trails=trails, fade=1.0, legend=0))
cpE, tgE, fovE = cam_state(1.0)
# ---------------- Part 2: replay of both serves, paths accumulate for comparison ----------------
def cam2(u, a, b):                                               # glide between two (position, target, fov)
    s = smooth(u); return ((1 - s) * a[0] + s * b[0]), ((1 - s) * a[1] + s * b[1]), (1 - s) * a[2] + s * b[2]
def orb(ph, e, R, tg, fov): d = np.array([np.sin(np.radians(ph)) * np.cos(np.radians(e)), -np.cos(np.radians(ph)) * np.cos(np.radians(e)), np.sin(np.radians(e))]); return (np.array(tg) + d * R, np.array(tg), fov)
V0 = (cpE, tgE, fovE); V1 = orb(28, 25, 21.5, (-1.2, -3.8, 1.2), 40.0); V2 = orb(62, 28, 21.5, (-1.2, -3.8, 1.2), 40.0)
NG, NA, NB, NH = 36, 112, 128, 84; N2 = NG + NA + NB + NH; fade_start = NG + NA + NB + 30
def full_trails(upto_A, upto_B, tauA, tauB, fade):
    tr = []
    for (ts, P), col, nm, lim in ((ballA, COL['A_ball'], 'A_ball', tauA), (rackA, COL['A_rack'], 'A_rack', tauA), (ballB, COL['B_ball'], 'B_ball', tauB), (rackB, COL['B_rack'], 'B_rack', tauB)):
        if lim is None: continue
        sel = ts <= lim
        if sel.sum() < 2: continue
        s = (ts[sel] - ts[sel][0]) / max(ts[sel][-1] - ts[sel][0], 1); tr.append(dict(pts=P[sel].tolist(), inten=((0.45 + 0.55 * s) * fade).tolist(), col=col, head=(lim < ts[-1] - 0.01), name=nm))
    return tr
for n in range(N2):
    if n < NG: u = n / NG; cp, tg, fov = cam2(u, V0, V1); sk, tau, tA, tB, fd = 'none', 0.0, None, None, 1.0; legend = 0
    elif n < NG + NA:
        k = (n - NG) / NA; tau = 4.0 + 56.0 * k; cp, tg, fov = cam2(k, V1, V1); sk = 'liveA'; tA, tB = tau, None; fd = 1.0; legend = 1
    elif n < NG + NA + NB:
        k = (n - NG - NA) / NB; tau = 150.0 + 64.0 * k; cp, tg, fov = cam2(k, V1, V2); sk = 'live'; tA, tB = 1e9, tau; fd = 1.0; legend = 2
    else:
        k = (n - NG - NA - NB) / NH; tau = 214.0; cp, tg, fov = cam2(k, V2, orb(72, 30, 21.5, (-1.2, -3.8, 1.2), 40.0)); sk = 'none'; tA, tB = 1e9, 1e9; fd = float(1 - smooth((n - fade_start) / (N2 - fade_start))) if n >= fade_start else 1.0; legend = 3
    if n < NG: tr = []
    else: tr = full_trails(None, None, tA, tB, fd)
    frames.append(dict(part=2, tau=float(tau), cam=np.asarray(cp).tolist(), target=np.asarray(tg).tolist(), fov=float(fov), skel=sk, live_racket=(sk != 'none'), trails=tr, fade=fd, legend=legend))
json.dump(dict(frames=frames, pivot=pivot.tolist()), open(SP + '/lab3/plan.json', 'w'))
print('frames', len(frames), 'part1', N1, 'part2', N2, ' source window part1 %.1f..%.1f (contact %.1f)' % (frames[0]['tau'], frames[N1 - 1]['tau'], tcB), ' start cam', np.round(frames[0]['cam'], 2), 'end cam', np.round(frames[N1 - 1]['cam'], 2))

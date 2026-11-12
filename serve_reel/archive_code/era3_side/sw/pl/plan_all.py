"""Plans for the IMG_7125 reel: orbit (plan_o.json), key-position freezes (plan_f.json), long shot (plan_l.json)."""
import numpy as np, json, sys
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0, SP + '/sw/pl'); sys.path.insert(0, SP + '/sw')
from motion_sw import Motion2, nrm
M = Motion2(); TC = M.tc; TRAIL_SRC = 17.0
def smooth(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
COL = dict(ball=(1.0, 0.86, 0.12), rack=(0.10, 0.85, 1.0), wrist=(1.0, 0.95, 0.85))
def path(fn, t0, t1, step=0.25): ts = np.arange(t0, t1 + 1e-6, step); return ts, np.array([fn(t) for t in ts])
ball = path(M.ball, 56.0, 89.0); rack = path(M.head_at, 56.0, 84.0); wrist = lambda t: M.jf('right_wrist', t)
EV = dict(trophy=66.0, low=71.0, contact=TC)
def trails_at(tau):
    tr = []
    for (ts, P), col, nm in ((ball, COL['ball'], 'ball'), (rack, COL['rack'], 'racket')):
        sel = (ts <= tau) & (ts >= tau - TRAIL_SRC)
        if sel.sum() >= 2: tr.append(dict(pts=P[sel].tolist(), inten=(1 - (tau - ts[sel]) / TRAIL_SRC).clip(0, 1).tolist(), col=col, head=True, name=nm))
    ts = np.arange(max(tau - TRAIL_SRC * 0.75, 0), tau + 1e-6, 0.25)
    if len(ts) >= 2: tr.append(dict(pts=[wrist(t).tolist() for t in ts], inten=(1 - (tau - ts) / (TRAIL_SRC * 0.75)).clip(0, 1).tolist(), col=COL['wrist'], head=False, name='wrist'))
    return tr
# ---------- orbit
N1 = 150; um = 0.55; uu = np.linspace(0, 1, 2001); vel = 0.38 - 0.31 * np.exp(-((uu - um) / 0.17) ** 2); cum = np.concatenate([[0], np.cumsum((vel[1:] + vel[:-1]) / 2 * np.diff(uu))])
K = 28.0 / cum[-1]; tau0 = TC - K * np.interp(um, uu, cum)
pivot = (M.head_at(TC) + M.jf('top_spine', TC)) / 2; pivot = np.array([pivot[0], pivot[1], 2.15])
o0 = M.C_cam - pivot; R0 = np.linalg.norm(o0); phi0 = np.arctan2(o0[0], -o0[1]); e0 = np.arcsin(o0[2] / R0)
def cam_state(u):
    ph = phi0 + (np.radians(112) - phi0) * smooth(u / 0.55) if u <= 0.55 else np.radians(112) + np.radians(98) * smooth((u - 0.55) / 0.45)
    e = e0 + (np.radians(17) - e0) * smooth(u / 0.55) if u <= 0.55 else np.radians(17) + np.radians(-4) * smooth((u - 0.55) / 0.45)
    R = R0 + (4.1 - R0) * smooth(u / 0.55) if u <= 0.55 else 4.1 + 1.0 * smooth((u - 0.55) / 0.45)
    fov = 33.0 + (40.0 - 33.0) * smooth(u / 0.55) if u <= 0.55 else 40.0
    d = np.array([np.sin(ph) * np.cos(e), -np.cos(ph) * np.cos(e), np.sin(e)]); return pivot + d * R, pivot, fov
fo = []
for n in range(N1):
    u = n / (N1 - 1); tau = tau0 + K * np.interp(u, uu, cum); cp, tg, fov = cam_state(u)
    fo.append(dict(part=1, tau=float(tau), cam=cp.tolist(), target=tg.tolist(), fov=float(fov), skel='live', live_racket=True, trails=trails_at(tau), fade=1.0, legend=0))
json.dump(dict(frames=fo, pivot=pivot.tolist()), open(SP + '/sw/pl/plan_o.json', 'w')); print('orbit', N1, 'tau %.1f..%.1f' % (fo[0]['tau'], fo[-1]['tau']), 'pivot', pivot.round(2))
# ---------- freezes
NF = 48; CAM = dict(trophy=(4, 24, 8, 4.7, 36.0, 1.15, 0.75), low=(28, 52, 8, 4.7, 36.0, 1.2, 0.75), contact=(76, 100, 7, 5.8, 38.0, 2.0, 0.98)); ff = []
for e in ('trophy', 'low', 'contact'):
    te = EV[e]; p0, p1, el, R, fov, pz, dz = CAM[e]
    for k in range(NF):
        u = k / (NF - 1); tau = te + 0.9 * (u - 0.5)
        pv = (M.jf('top_spine', te) + M.jf('bottom_spine', te)) / 2 if e != 'contact' else (M.head_at(te) + M.jf('top_spine', te)) / 2
        pv = np.array([pv[0], pv[1], pz]); ph = np.radians(p0 + (p1 - p0) * smooth(u)); ee = np.radians(el)
        cp = pv + np.array([np.sin(ph) * np.cos(ee), -np.cos(ph) * np.cos(ee), np.sin(ee)]) * R
        ff.append(dict(part=3, tau=float(tau), cam=cp.tolist(), target=(pv - np.array([0, 0, dz])).tolist(), fov=fov, skel='live', live_racket=True, trails=trails_at(tau), fade=1.0, legend=0, serve='A', event=e, k=k))
json.dump(dict(frames=ff), open(SP + '/sw/pl/plan_f.json', 'w')); print('freeze', len(ff))
# ---------- long shot
def orb(ph, e, R, tg, fov): d = np.array([np.sin(np.radians(ph)) * np.cos(np.radians(e)), -np.cos(np.radians(ph)) * np.cos(np.radians(e)), np.sin(np.radians(e))]); return (np.array(tg) + d * R, np.array(tg), fov)
cpE, tgE, fovE = cam_state(1.0); TGT = (0.7, -3.2, 1.0); V0 = (cpE, tgE, fovE); V1 = orb(8, 50, 19.0, TGT, 42.0); V2 = orb(20, 44, 20.0, TGT, 42.0)
def cam2(u, a, b): s = smooth(u); return ((1 - s) * a[0] + s * b[0]), ((1 - s) * a[1] + s * b[1]), (1 - s) * a[2] + s * b[2]
NG, NA, NH = 30, 130, 80; fl = []
def full_trails(lim, fade):
    tr = []
    for (ts, P), col, nm in ((ball, COL['ball'], 'ball'), (rack, COL['rack'], 'racket')):
        sel = ts <= lim
        if sel.sum() < 2: continue
        s = (ts[sel] - ts[sel][0]) / max(ts[sel][-1] - ts[sel][0], 1); tr.append(dict(pts=P[sel].tolist(), inten=((0.45 + 0.55 * s) * fade).tolist(), col=col, head=bool(lim < ts[-1] - 0.01), name=nm))
    return tr
for n in range(NG + NA + NH):
    if n < NG: u = n / NG; cp, tg, fov = cam2(u, V0, V1); sk, tau, tr, fd, lg = 'none', 0.0, [], 1.0, 0
    elif n < NG + NA: k = (n - NG) / NA; tau = 56.0 + 35.0 * k; cp, tg, fov = cam2(k, V1, V2); sk = 'live'; tr = full_trails(tau, 1.0); fd = 1.0; lg = 1
    else: k = (n - NG - NA) / NH; tau = 91.0; cp, tg, fov = cam2(k, V2, orb(25, 40, 21.0, TGT, 42.0)); sk = 'none'; fd = float(1 - smooth((k - 0.6) / 0.4)); tr = full_trails(1e9, fd); lg = 2
    fl.append(dict(part=2, tau=float(tau), cam=np.asarray(cp).tolist(), target=np.asarray(tg).tolist(), fov=float(fov), skel=sk, live_racket=(sk != 'none'), trails=tr, fade=fd, legend=lg))
json.dump(dict(frames=fl), open(SP + '/sw/pl/plan_l.json', 'w')); print('long', len(fl))

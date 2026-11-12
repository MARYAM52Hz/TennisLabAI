import sys, numpy as np, pickle, json
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
from motion_lab2 import Motion2, nrm
M = Motion2(); T = M.T; X = M.X; I = M.I
def J(n, f): return M.jf(n, f)
def ang(a, b, c): u, v = nrm(a - b), nrm(c - b); return float(np.degrees(np.arccos(np.clip(np.dot(u, v), -1, 1))))
def inner(side, joint, f):
    if joint == 'knee': return ang(J(f'{side}_hip', f), J(f'{side}_knee', f), J(f'{side}_ankle', f))
    if joint == 'elbow': return ang(J(f'{side}_shoulder', f), J(f'{side}_elbow', f), J(f'{side}_wrist', f))
    if joint == 'shoulder_abd': return ang(J(f'{side}_hip', f), J(f'{side}_shoulder', f), J(f'{side}_elbow', f))
def yaw(a, b): d = b - a; return float(np.degrees(np.arctan2(d[1], d[0])))               # azimuth of a horizontal line
def tilt(a, b): d = b - a; return float(np.degrees(np.arctan2(d[2], np.hypot(d[0], d[1]))))   # elevation angle of a line above horizontal
res = {}
for key, lo, hi in (('A', 0, 60), ('B', 150, 215)):
    tc = M.tcs[key]; fr = np.arange(lo, hi + 1)
    kneeR = np.array([inner('right', 'knee', f) for f in fr]); kneeL = np.array([inner('left', 'knee', f) for f in fr])
    sel = (fr <= tc); ik = np.argmin((kneeR + kneeL)[sel] / 2 + 0) ; f_knee = int(fr[sel][ik]) if sel.any() else lo
    elb = np.array([inner('right', 'elbow', f) for f in fr]); shoulder_line_tilt = np.array([tilt(J('left_shoulder', f), J('right_shoulder', f)) for f in fr])
    hip_yaw = np.unwrap(np.radians([yaw(J('left_hip', f), J('right_hip', f)) for f in fr])); sh_yaw = np.unwrap(np.radians([yaw(J('left_shoulder', f), J('right_shoulder', f)) for f in fr]))
    hip_yaw, sh_yaw = np.degrees(hip_yaw), np.degrees(sh_yaw); sep = sh_yaw - hip_yaw
    head = np.array([M.head_at(f) for f in fr]); sp = np.linalg.norm(np.gradient(head, axis=0), axis=1) * 30
    ball = np.array([M.ball(f) for f in fr]); okb = ball[:, 2] > -10; ztop = ball[okb, 2].max(); f_top = int(fr[okb][np.argmax(ball[okb, 2])])
    tcI = int(round(tc)); ts = J('top_spine', tc); rs = J('right_shoulder', tc); ls = J('left_shoulder', tc); bc = M.ball(tc)
    zc_foot = min(J('left_ankle', tc)[2], J('right_ankle', tc)[2]); stand = np.median([min(J('left_ankle', f)[2], J('right_ankle', f)[2]) for f in fr])
    # trophy: frame with maximal right-arm abduction & elbow flexion before contact, approx at max knee flexion
    f_trophy = f_knee; f_drop = int(fr[(fr >= f_trophy) & (fr <= tcI)][np.argmin(head[(fr >= f_trophy) & (fr <= tcI), 2])])
    ome_h = np.gradient(hip_yaw) * 30; ome_s = np.gradient(sh_yaw) * 30; ome_e = -np.gradient(elb) * 30                          # deg/s (elbow extension positive)
    res[key] = dict(tc=tc, f_knee=f_knee, f_drop=f_drop, f_top=f_top, knee_min_inner_R=float(kneeR[sel].min()), knee_min_inner_L=float(kneeL[sel].min()), knee_at_trophy=(float(kneeR[fr == f_knee][0]), float(kneeL[fr == f_knee][0])),
        knee_at_contact=(inner('right', 'knee', tc), inner('left', 'knee', tc)), elbow_trophy=float(elb[fr == f_knee][0]), elbow_min_before=float(elb[sel].min()), elbow_contact=inner('right', 'elbow', tc), shoulder_abd_contact=inner('right', 'shoulder_abd', tc),
        shoulder_tilt_trophy=float(shoulder_line_tilt[fr == f_knee][0]), shoulder_tilt_contact=float(tilt(J('left_shoulder', tc), J('right_shoulder', tc))),
        hip_sh_sep_max=float(np.abs(sep[sel]).max()), sep_at_trophy=float(sep[fr == f_knee][0]), sep_at_contact=float(sep[np.argmin(abs(fr - tc))]),
        contact_height=float(bc[2]), contact_vs_shoulder=float(bc[2] - rs[2]), contact_ahead=float(bc[1] - ts[1]), contact_lateral=float(bc[0] - rs[0]), toss_apex=float(ztop), toss_apex_f=f_top,
        racket_head_peak_ms=float(sp.max()), racket_peak_f=int(fr[np.argmax(sp)]), foot_lift_contact=float(zc_foot - stand), ball_speed=float(np.linalg.norm(pickle.load(open(SP + '/lab2/ball3d.pkl', 'rb'))['A' if key == 'A' else 'B2']['v1'])),
        peak_hip_rot=float(np.abs(ome_h[sel]).max()), peak_sh_rot=float(np.abs(ome_s[sel]).max()), f_peak_hip=int(fr[sel][np.argmax(np.abs(ome_h[sel]))]), f_peak_sh=int(fr[sel][np.argmax(np.abs(ome_s[sel]))]), peak_elbow_ext=float(ome_e[sel].max()), f_peak_elb=int(fr[sel][np.argmax(ome_e[sel])]),
        head_height_standing=float(np.median([J('top_spine', f)[2] for f in fr[:8]])))
    res[key]['series'] = dict(fr=fr.tolist(), kneeR=kneeR.tolist(), kneeL=kneeL.tolist(), elb=elb.tolist(), head_speed=sp.tolist(), sep=sep.tolist(), tilt=shoulder_line_tilt.tolist())
for k in 'AB':
    r = res[k]; print(k, {a: (round(b, 2) if isinstance(b, float) else (tuple(round(x, 1) for x in b) if isinstance(b, tuple) else b)) for a, b in r.items() if a != 'series'})
pickle.dump(res, open(SP + '/ana/metrics.pkl', 'wb'))

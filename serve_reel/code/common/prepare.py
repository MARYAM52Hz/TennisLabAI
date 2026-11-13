"""Stage 1: video + CVAT export -> job directory (frames, timestamps, labels.pkl, auto-detected events, job.json)."""
import os, sys, json, subprocess, zipfile, shutil, pickle, re
import numpy as np
import xml.etree.ElementTree as ET

def sh(cmd, **kw): return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout

def read_xml(labels, job):
    """labels: annotations.xml, or the CVAT zip containing it -> path of an xml inside the job dir; returns (path, n_frames)"""
    dst = os.path.join(job, 'labels.xml')
    if labels.lower().endswith('.zip'):
        with zipfile.ZipFile(labels) as z:
            names = [n for n in z.namelist() if n.lower().endswith('annotations.xml')]
            if not names: sys.exit('ERROR: no annotations.xml inside ' + labels + ' (export from CVAT as "CVAT for video 1.1")')
            open(dst, 'wb').write(z.read(names[0]))
    else: shutil.copy(labels, dst)
    r = ET.parse(dst).getroot()
    if r.tag != 'annotations' or not r.findall('track'): sys.exit('ERROR: this is not a CVAT *video* export (need <track> elements; export "CVAT for video 1.1")')
    size = r.find('.//task/size'); n = int(size.text) if size is not None else 1 + max(int(e.get('frame')) for t in r.findall('track') for e in t)
    return dst, n

def probe(video):
    j = json.loads(sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_frames,avg_frame_rate:stream_side_data=rotation', '-of', 'json', video]))
    s = j['streams'][0]; w, h = int(s['width']), int(s['height'])
    rot = 0
    for sd in s.get('side_data_list', []) or []: rot = int(sd.get('rotation', 0))
    if abs(rot) in (90, 270): w, h = h, w
    pts = [float(x.strip(',')) for x in sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'csv=p=0', video]).split() if x.strip()]
    pts = np.array(sorted(pts)); pts -= pts[0]
    return w, h, pts

def gray_diffs(video, w, h):
    """mean absolute difference between consecutive frames (full resolution, grey) -> detects repeated frames of slow-motion exports"""
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', video, '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
    prev = None; out = [0.0]; n = w * h
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        a = np.frombuffer(b, np.uint8).astype(np.float32)
        if prev is not None: out.append(float(np.abs(a - prev).mean()))
        prev = a
    p.wait(); return np.array(out)

def cadence(fd):
    """container frames per distinct picture (slow-motion exports repeat frames, e.g. 10/3); grid search on the difference peaks"""
    n = len(fd); tot = fd.sum() + 1e-9; best = (0, 1.0)
    for r in np.arange(1.0, 8.01, 0.01):
        for ph in np.arange(0, r, 0.25):
            g = np.unique(np.floor(ph + r * np.arange(int((n - ph) / r) + 1)).astype(int)); g = g[(g >= 0) & (g < n)]
            C = fd[g].sum() / tot; P = (fd[g] > 0.5).mean(); F = 2 * C * P / (C + P + 1e-9)
            if F > best[0]: best = (F, r)
    r = best[1]; r = round(r * 3) / 3
    return 1.0 if r < 1.2 else r

def extract_frames(video, frames, outdir, start_number, mirror=False, size=None):
    """frames: container frame numbers (0-based) -> outdir/f%04d.png ; naming: back view f(n+1) (1-based), side view f(n) (0-based)"""
    os.makedirs(outdir, exist_ok=True)
    if len(frames) > 60 and frames == list(range(len(frames))):
        sh(['ffmpeg', '-y', '-v', 'error', '-i', video] + (['-vf', ','.join((['hflip'] if mirror else []) + (['scale=%d:%d:flags=lanczos' % size] if size else []))] if (mirror or size) else []) + ['-vsync', '0', '-start_number', str(start_number), os.path.join(outdir, 'f%04d.png')]); return
    for n in frames:
        sh(['ffmpeg', '-y', '-v', 'error', '-i', video, '-vf', 'select=eq(n\\,%d)%s%s' % (n, ',hflip' if mirror else '', (',scale=%d:%d:flags=lanczos' % size) if size else ''), '-vsync', '0', '-frames:v', '1', os.path.join(outdir, 'f%04d.png' % (n + start_number - 0))])


def swap_lr(n):
    """left/right swap of a label name (left_knee <-> right_knee, far_baseline_singles_left <-> ..._right)"""
    return re.sub(r'left|right', lambda m: 'right' if m.group(0) == 'left' else 'left', n)

def detect_hand(lab, tc_c):
    """racket hand = the wrist nearer to the racket handle at the contact frame -> 'right' or 'left' (left-handers are mirrored so that the whole pipeline sees a right-hander)"""
    try:
        h = np.asarray(lab['rack']['handle_top'][tc_c], float) if 'handle_top' in lab['rack'] else np.asarray(lab['rack']['butt_cap'][tc_c], float)
        dr = np.linalg.norm(np.asarray(lab['skel']['right_wrist'][tc_c], float) - h); dl = np.linalg.norm(np.asarray(lab['skel']['left_wrist'][tc_c], float) - h)
        return ('left' if dl < dr else 'right'), float(dr), float(dl)
    except Exception: return 'right', 0.0, 0.0

def transform_labels(lab, W, k=1.0, mirror=False):
    """canonical coordinates: scale every label by k (long side -> 1280 px) and optionally mirror horizontally (x -> W - x, left/right names swapped, ellipse rotation negated)"""
    X = (lambda x: (W - x) * k) if mirror else (lambda x: x * k); nm = swap_lr if mirror else (lambda n: n)
    def arr(a):
        a = np.asarray(a, float); z = (a == 0).all(axis=1, keepdims=True); o = np.c_[X(a[:, 0]), a[:, 1] * k]; return np.where(z, 0.0, o)
    out = dict(lab)
    out['skel'] = {nm(n): arr(a) for n, a in lab['skel'].items()}
    out['rack'] = {n: arr(a) for n, a in lab['rack'].items()}
    out['court'] = {nm(n): np.array([X(v[0]), v[1] * k]) for n, v in lab['court'].items()}
    out['ball'] = {f: (X(b[0]), b[1] * k, b[2] * k, b[3] * k) + tuple(b[4:]) for f, b in lab['ball'].items()}
    out['face'] = {f: (X(e[0]), e[1] * k, e[2] * k, e[3] * k, ((-e[4]) % 360.0) if mirror else e[4]) for f, e in lab['face'].items()}
    out['contacts'] = [(l, f, [X(p[0]), p[1] * k] + list(p[2:])) for l, f, p in lab['contacts']]
    return out

def release_detect(sk_lw, ball, tc0, view):
    """first frame at which the ball leaves the tossing hand (distance ball-left wrist rises above the hold level)"""
    fs = [f for f in range(max(0, tc0 - 70), tc0 + 1) if f in ball and not ball[f][4]]
    d = {f: float(np.hypot(ball[f][0] - sk_lw[f][0], ball[f][1] - sk_lw[f][1])) for f in fs}
    hold = float(np.percentile(list(d.values()), 10)); thr = 2.0 * hold
    pk = max(range(max(fs[0], tc0 - 40), tc0), key=lambda f: d.get(f, 0)); f = pk
    while f - 1 in d and d[f - 1] > thr: f -= 1
    rise = f; b0 = rise - 1
    while b0 - 1 in d and d[b0 - 1] <= thr: b0 -= 1
    return rise, b0, hold

JOINTS = ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
          'left_heel', 'right_heel', 'left_foot_index', 'right_foot_index', 'top_spine', 'bottom_spine']
COURT = ['far_baseline_singles_left', 'far_baseline_doubles_left', 'far_baseline_center_mark', 'far_baseline_singles_right', 'far_baseline_doubles_right', 'far_service_singles_left', 'far_service_center_T',
         'far_service_singles_right', 'near_service_singles_left', 'near_service_center_T', 'near_service_singles_right', 'near_baseline_doubles_left', 'near_baseline_singles_left', 'near_baseline_center_mark',
         'near_baseline_singles_right', 'near_baseline_doubles_right']

def validate(view, lab, frames, ball_frames, tc_c):
    """check that the CVAT export has everything the pipeline needs; report ALL problems at once"""
    err = []
    for j in JOINTS:
        if j not in lab['skel']: err.append('missing skeleton point "%s" (label P_player_skeleton)' % j); continue
        a = lab['skel'][j]; bad = [f for f in frames if f >= len(a) or abs(a[f]).sum() == 0]
        if bad: err.append('skeleton point "%s" has no position on frames %s' % (j, bad[:6]))
    miss = [f for f in frames if f not in lab['face']]
    if miss: err.append('racket face ellipse (R_racket_face) missing on frames %s (needed on every frame of the serve)' % miss[:8])
    for k in ('string_bed_center',):
        if k not in lab['rack']: err.append('racket skeleton point "%s" missing (R_racket_skeleton)' % k)
    miss = [f for f in ball_frames if f not in lab['ball'] or lab['ball'][f][4]]
    if miss: err.append('ball ellipse (B_ball) missing or marked outside on frames %s (needed from the toss to the end of the clip)' % miss[:8])
    if view == 'back':
        mc = [c for c in COURT if c not in lab['court']]
        if mc: err.append('court points missing at frame 0: %s' % mc)
    if err: sys.exit('LABEL PROBLEMS (fix in CVAT, re-export, re-run):\n  - ' + '\n  - '.join(err))

def prepare(job, video, labels, view, name, height=1.80, overrides=None, hand='auto', mirror_probe=None):
    os.makedirs(job, exist_ok=True); kit = os.environ['REEL_KIT']; py = sys.executable
    xml, T_lab = read_xml(labels, job)
    W, H, pts = probe(video); nvid = len(pts)
    jc = dict(view=view, name=name, W=W, H=H, labels_xml=xml, labels_pkl=os.path.join(job, 'nl' if view == 'back' else 'sw', 'labels.pkl'), T_lab=T_lab, player_h=height,
              ana='nr/ana' if view == 'back' else 'nq/ana', video_frames=nvid)
    os.makedirs(os.path.dirname(jc['labels_pkl']), exist_ok=True); json.dump(jc, open(os.path.join(job, 'job.json'), 'w'))
    env = dict(os.environ, REEL_JOB=job); sh([py, '-I', os.path.join(kit, 'code', 'common', 'parse.py')], env=env)
    lab = pickle.load(open(jc['labels_pkl'], 'rb'))
    ctc = [c for c in lab['contacts'] if c[0] == 'B_contact_racket']
    if len(ctc) != 1: sys.exit('ERROR: need exactly one B_contact_racket point (the racket-ball contact frame); found %d' % len(ctc))
    tc_c = ctc[0][1]
    hd, dr_, dl_ = detect_hand(lab, tc_c); mirror = (hand == 'left') or (hand == 'auto' and hd == 'left' and dl_ < 0.8 * dr_)
    print('racket hand: %s (right wrist %.0f px / left wrist %.0f px from the handle at contact) -> %s' % (hd, dr_, dl_, 'MIRRORING video and labels so the pipeline sees a right-hander' if mirror else 'no mirroring'))
    # canonical working resolution: long side 1280 px (all pixel thresholds of the pipeline were tuned there), so any phone / resolution behaves the same
    k = 1280.0 / max(W, H); size = None
    if abs(k - 1) > 0.01:
        size = (int(round(W * k / 2) * 2), int(round(H * k / 2) * 2)); print('input %dx%d -> working resolution %dx%d (labels and frames scaled by %.3f)' % (W, H, size[0], size[1], k))
    if W > H: print('WARNING: landscape footage is untested (the pipeline was developed on portrait phone video); results may be unreliable. See docs/serve_reel/INPUT_STANDARDS_AND_CALIBRATION.md')
    if mirror or size:
        lab = transform_labels(lab, W, k, mirror); pickle.dump(lab, open(jc['labels_pkl'], 'wb'))
    jc.update(hand_detected=hd, mirrored=bool(mirror), W_src=W, H_src=H, scale_to_working=k, landscape=bool(W > H))
    if size: jc.update(W=size[0], H=size[1]); W, H = size
    json.dump(jc, open(os.path.join(job, 'job.json'), 'w'))
    if view == 'back':
        if not lab['court']: sys.exit('ERROR: back view needs the court track "C_structured_court" (frame 0) in the CVAT labels')
        N = min(nvid, tc_c + 18); frames = list(range(N)); extract_frames(video, frames, os.path.join(job, 'new', 'fr'), 1, mirror, size)
        np.save(os.path.join(job, 'nl', 'pts.npy'), pts[:max(nvid, T_lab)] if nvid >= T_lab else np.r_[pts, pts[-1] + (np.arange(1, T_lab - nvid + 1)) / 30.0])
        tc0 = tc_c; sk, ball = lab['skel'], lab['ball']
        gr = [c for c in lab['contacts'] if c[0] == 'B_contact_ground' and c[1] > tc0]
        bounce = min(c[1] for c in gr) if gr else None
        rise, b0, hold = release_detect(sk['left_wrist'], ball, tc0, view)
        validate(view, lab, frames, list(range(rise, N)), tc_c)
        jc.update(N=N, tc0=tc_c, f0=rise, ball0=b0, bounce_f=bounce, ball1=(bounce + 2 if bounce else tc0 + 8), st0=rise - 2, st1=rise + 3, trophy_w0=rise - 2, trophy_w1=tc0 - 1,
                  focal=None, fps_real=int(round((nvid - 1) / pts[-1])), cadence=None)
    else:
        fd = gray_diffs(video, jc['W_src'], jc['H_src']); r = cadence(fd); K_PRE, N = 32, 63
        S0 = tc_c - int(np.floor(r * K_PRE)); S = np.array([S0 + int(np.floor(r * k)) for k in range(N)])
        if S0 < 0 or S[-1] >= nvid: sys.exit('ERROR: the clip is too short around the contact frame: need %d container frames before and %d after it' % (int(r * K_PRE), int(r * (N - 1 - K_PRE))))
        np.save(os.path.join(job, 'sw', 'S.npy'), S); np.save(os.path.join(job, 'sw', 'pts.npy'), np.arange(N) / 30.0)
        extract_frames(video, [int(s) for s in S], os.path.join(job, 'sw', 'fr'), 0, mirror, size)
        tc0 = K_PRE; assert S[tc0] == tc_c, (S[tc0], tc_c)
        sk = {n: v[S] for n, v in lab['skel'].items()}; ball = {k: lab['ball'][int(S[k])] for k in range(N) if int(S[k]) in lab['ball']}
        rise, b0, hold = release_detect(sk['left_wrist'], ball, tc0, view)
        f0 = rise - 3
        lab2 = dict(skel=sk, face={k: lab['face'][int(S[k])] for k in range(N) if int(S[k]) in lab['face']}, ball=ball, rack=lab['rack'], court=lab['court'])
        validate(view, lab2, list(range(N)), list(range(b0, tc0 + 2)), tc_c)
        jc.update(N=N, tc0=tc0, f0=f0, ball0=b0, bounce_f=None, ball1=tc0 + 1, st0=float(f0 - 3), st1=float(rise - 1), trophy_w0=f0 + 5, trophy_w1=tc0 - 5,
                  focal=round(0.515 * max(W, H), 1), fps_real=30, cadence=r, player_y=-12.4, container_tc=int(tc_c))
    jc.update(overrides or {}); jc['window_note'] = 'auto-detected; edit job.json to override then re-run with --from <stage>'
    json.dump(jc, open(os.path.join(job, 'job.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print('job.json:', {k: v for k, v in jc.items() if k not in ('labels_xml', 'labels_pkl')}); return jc

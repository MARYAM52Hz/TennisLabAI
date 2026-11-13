"""qc.py - reliability ("trust") report for one reel job.   usage:  REEL_JOB=<job> python3 -I qc.py
Reads only files the pipeline already produced (labels, camera, 3D lifts, ball fit, metrics, logs) and writes
  <job>/qc.json   machine-readable (checks, group scores, per-metric trust, grade, warnings, actions)
  <job>/qc.md     human-readable EN + FA report
Every check returns a 0-100 score. Scores are combined into 4 groups (video, labels, scale/calibration, 3D pose),
an overall grade A-D and a trust level (high / medium / low) for each number printed in the reel.
Nothing here changes the reel; it tells you how far to believe it. See docs/INPUT_STANDARDS_AND_CALIBRATION.md."""
import os, re, json, pickle, numpy as np

SP = os.environ['REEL_JOB']; JC = json.load(open(SP + '/job.json')); VIEW = JC['view']
LAB = 'nl' if VIEW == 'back' else 'sw'; ANA = JC['ana']; N = int(JC['N']); H_IMG = JC['H']; W_IMG = JC['W']
lin = lambda x, bad, good: float(np.clip((x - bad) / (good - bad), 0, 1) * 100)     # bad -> 0, good -> 100
CHK = []

def chk(cid, group, score, value, en, fa, w=1.0, critical=False, action_en='', action_fa=''):
    CHK.append(dict(id=cid, group=group, score=round(float(score), 1), value=value, en=en, fa=fa, weight=w, critical=critical, action_en=action_en, action_fa=action_fa))

def load(p, default=None):
    try: return pickle.load(open(p, 'rb'))
    except Exception: return default

def logtext(n):
    try: return open(os.path.join(SP, 'logs', n)).read()
    except Exception: return ''

raw = load(JC['labels_pkl']); lab2 = load(SP + '/sw/lab2.pkl') if VIEW == 'side' else None
L = lab2 or raw                                                       # labels indexed like the 3D arrays (unique frames in the side view)
pts = None
try: pts = np.load(SP + '/%s/pts.npy' % LAB)
except Exception: pass
f0 = int(JC['f0']); w0 = max(0, f0 - 12) if VIEW == 'back' else 0; win = list(range(w0, N))
try: M_ = json.load(open(SP + '/' + ANA + '/metrics.json'))
except Exception: M_ = {}

# ------------------------------------------------------------------ VIDEO
WS, HS = int(JC.get('W_src', W_IMG)), int(JC.get('H_src', H_IMG)); short = min(WS, HS)
chk('V_res', 'video', lin(short, 360, 720), '%dx%d' % (WS, HS), 'Frame size %dx%d (short side %d px; 720+ is the standard).' % (WS, HS, short),
    'اندازه‌ی تصویر %dx%d (ضلع کوتاه %d پیکسل؛ استاندارد ۷۲۰ به بالا).' % (WS, HS, short), 0.7,
    action_en='Film at 1080p or at least 720p.', action_fa='با کیفیت ۱۰۸۰p یا دست‌کم ۷۲۰p فیلم بگیرید.')
if JC.get('landscape'): chk('V_orient', 'video', 50, 'landscape', 'Landscape footage is untested: the pipeline was developed and checked on portrait phone video.', 'ویدیوی افقی تست نشده است: خط لوله روی ویدیوی عمودی گوشی توسعه و بررسی شده.', 0.8, False, 'Film in portrait orientation.', 'ویدیو را عمودی (پرتره) بگیرید.')
if JC.get('mirrored'): chk('V_hand', 'video', 100, 'mirrored', 'Left-handed player detected: video and labels were mirrored so that the analysis sees a right-hander (numbers are symmetric; the avatar in the reel is drawn right-handed).', 'بازیکن چپ‌دست تشخیص داده شد: ویدیو و لیبل‌ها آینه شدند تا تحلیل مثل راست‌دست انجام شود (اعداد متقارن‌اند؛ آواتار ریل راست‌دست رسم می‌شود).', 0.1, False)
fps = float(JC.get('fps_real') or 30)
dts = np.diff(pts[max(0, w0):N]) * 1000 if pts is not None and len(pts) > 3 else None
vfr = '' if dts is None else (' VFR: frame gaps %d-%d ms.' % (dts.min(), dts.max()) if dts.max() > 1.3 * dts.min() else '')
chk('V_fps', 'video', lin(fps, 10, 30), round(fps, 1), 'Real motion sampling %.0f frames/s.%s Timing values (ms) are as coarse as one frame interval (%.0f ms).' % (fps, vfr, 1000 / fps),
    'نرخ واقعی نمونه‌برداری حرکت %s فریم بر ثانیه؛ زمان‌بندی‌ها (ms) در حد یک فریم (%s ms) دقت دارند.' % (round(fps), round(1000 / fps)), 0.8,
    action_en='Use 60 fps (or 120/240 slow-motion) so contact timing is resolved.', action_fa='با ۶۰ فریم بر ثانیه (یا اسلوموشن ۱۲۰/۲۴۰) فیلم بگیرید.')
if pts is None: chk('V_pts', 'video', 30, None, 'No per-frame timestamps found: timing falls back to a constant frame rate.', 'زمان‌بندی فریم‌ها پیدا نشد؛ نرخ ثابت فرض شد.', 0.5, False)
try:
    sk = L['skel']; tcf = int(round(JC['tc0'] if VIEW == 'back' else JC['tc0']))
    ys = [sk[n][tcf][1] for n in ('left_ankle', 'right_ankle')]; ext = (max(ys) - sk['top_spine'][tcf][1]) / H_IMG
    chk('V_size', 'video', lin(ext, 0.12, 0.30), round(float(ext), 3), 'Player (neck to ankles) fills %.0f%% of frame height at contact.' % (ext * 100),
        'بازیکن (گردن تا مچ پا) هنگام تماس %s٪ ارتفاع تصویر را پر می‌کند.' % round(ext * 100), 0.7,
        action_en='Move the camera closer or zoom so the player is at least ~30% of the frame height.', action_fa='دوربین را نزدیک‌تر کنید تا بازیکن حدود ۳۰٪ ارتفاع کادر یا بیشتر باشد.')
except Exception: pass

# ------------------------------------------------------------------ LABELS
def missing_frac(d, names, T):
    miss = 0; tot = 0
    for n in names:
        a = np.asarray(d[n])
        for k in win:
            tot += 1; miss += int(k >= len(a) or (a[k] == 0).all())
    return miss / max(tot, 1)
try:
    mf = missing_frac(L['skel'], list(L['skel']), N)
    chk('L_skel', 'labels', 100 * (1 - mf), round(1 - mf, 3), 'Skeleton: %.1f%% of points labelled in the analysed window.' % (100 * (1 - mf)),
        'اسکلت: %s٪ نقاط در بازه‌ی تحلیل لیبل خورده‌اند.' % round(100 * (1 - mf), 1), 1.5, critical=mf > 0.1,
        action_en='Label all 22 skeleton points on every frame (interpolate between keyframes, then check).', action_fa='هر ۲۲ نقطه‌ی اسکلت را روی همه‌ی فریم‌ها لیبل بزنید (بین کیفریم‌ها درون‌یابی کنید و بعد بازبینی).')
    mr = missing_frac(L['rack'], list(L['rack']), N)
    chk('L_rack', 'labels', 100 * (1 - mr), round(1 - mr, 3), 'Racket: %.1f%% of points labelled.' % (100 * (1 - mr)), 'راکت: %s٪ نقاط لیبل خورده‌اند.' % round(100 * (1 - mr), 1), 0.8, critical=mr > 0.3,
        action_en='Label the 10 racket points every frame.', action_fa='۱۰ نقطه‌ی راکت را روی همه‌ی فریم‌ها لیبل بزنید.')
except Exception as e: chk('L_skel', 'labels', 0, None, 'Skeleton labels unreadable: %s' % e, 'لیبل اسکلت خوانده نشد.', 1.5, True)
try:
    b = L['ball']; a0, a1 = int(JC['ball0']), int(JC['ball1'])
    if VIEW == 'side': a0, a1 = 0, int(JC['ball1'])
    ok = [k for k in range(a0, a1 + 1) if k in b and not (len(b[k]) > 4 and b[k][4])]; fr = len(ok) / max(a1 - a0 + 1, 1)
    chk('L_ball', 'labels', lin(fr, 0.4, 0.95), round(fr, 2), 'Ball ellipse labelled on %.0f%% of frames from release to the end of the ball path.' % (100 * fr),
        'توپ روی %s٪ فریم‌های رهاسازی تا انتهای مسیر لیبل خورده است.' % round(100 * fr), 1.0, critical=fr < 0.5,
        action_en='Label the ball (ellipse) on every frame it is visible; mark "outside" only when it really leaves the frame.', action_fa='توپ (بیضی) را روی هر فریمی که دیده می‌شود لیبل بزنید؛ «outside» فقط وقتی واقعاً از کادر خارج شده.')
except Exception: pass
try:
    cr = [c for c in raw['contacts'] if c[0] == 'B_contact_racket']; tcr = cr[0][1]
    if len(cr) != 1: chk('L_contact', 'labels', 0, len(cr), 'Expected exactly one B_contact_racket, found %d.' % len(cr), 'باید دقیقاً یک B_contact_racket باشد؛ %d پیدا شد.' % len(cr), 2.0, True,
                         'Keep exactly one racket-contact point, on the first frame the ball touches the strings.', 'فقط یک نقطه‌ی تماس راکت بگذارید، روی اولین فریمی که توپ به سیم‌ها می‌خورد.')
    else:
        cx, cy = cr[0][2][:2]; bb = raw['ball'].get(tcr); fc = raw['face'].get(tcr)
        dball = float(np.hypot(bb[0] - cx, bb[1] - cy) / max(np.mean(bb[2:4]), 1)) if bb else 99
        dface = float(np.hypot(fc[0] - cx, fc[1] - cy) / max(np.mean(fc[2:4]), 1)) if fc else 99
        sc = min(lin(dball, 6, 1.5), lin(dface, 3.0, 1.2) if fc else 100)
        chk('L_contact', 'labels', sc, dict(ball_r=round(dball, 1), face_r=round(dface, 2)),
            'Contact point is %.1f ball-radii from the ball centre and %.2f face-radii from the string-bed centre (frame %d).' % (dball, dface, tcr),
            'نقطه‌ی تماس %s شعاع توپ از مرکز توپ و %s شعاع صفحه‌ی راکت از مرکز سیم‌ها فاصله دارد (فریم %d).' % (round(dball, 1), round(dface, 2), tcr), 2.0, sc < 40,
            'Re-check the contact frame: ball, string bed and contact point should coincide. The whole timeline is aligned on it.', 'فریم تماس را دوباره بررسی کنید: توپ، صفحه‌ی راکت و نقطه‌ی تماس باید روی هم بیفتند. کل خط زمانی روی آن تنظیم می‌شود.')
except Exception: chk('L_contact', 'labels', 0, None, 'No B_contact_racket label found.', 'برچسب B_contact_racket پیدا نشد.', 2.0, True, 'Add one B_contact_racket point.', 'یک نقطه‌ی B_contact_racket اضافه کنید.')
# spikes = one-frame excursions of a joint (typical human slip: wrong point clicked / ID jump)
try:
    spikes = []
    for n, a in L['skel'].items():
        a = np.asarray(a, float)
        for k in range(max(1, w0), min(N, len(a)) - 1):
            if (a[k - 1:k + 2] == 0).all(axis=1).any(): continue
            mid = (a[k - 1] + a[k + 1]) / 2; exc = float(np.linalg.norm(a[k] - mid)); span = float(np.linalg.norm(a[k + 1] - a[k - 1]))
            if exc > 14 and exc > 1.6 * max(span, 1): spikes.append((n, int(k), round(exc)))
    ns = len(spikes); sc = 100 * (1 - min(1, ns / 8.0))
    chk('L_spikes', 'labels', sc, spikes[:12], 'Label jumps: %d single-frame spikes%s.' % (ns, (' (e.g. ' + ', '.join('%s@%d' % (s[0], s[1]) for s in spikes[:4]) + ')') if ns else ''),
        'پرش لیبل: %s مورد جهش تک‌فریمی%s.' % (ns, (' (مثلاً ' + '، '.join('%s@%d' % (s[0], s[1]) for s in spikes[:4]) + ')') if ns else ''), 1.0, False,
        'Open the listed joint/frame pairs in CVAT and fix the stray point.', 'جفت مفصل/فریم‌های فهرست‌شده را در CVAT باز و نقطه‌ی اشتباه را اصلاح کنید.')
except Exception: pass
# hand on racket: the racket should be held by one wrist at contact (catches left/right swaps, wrong-track racket labels)
try:
    tcr = [c for c in raw['contacts'] if c[0] == 'B_contact_racket'][0][1]; kk = tcr if VIEW == 'back' else JC['tc0']
    rk = L['rack']; sk = L['skel']; k = int(JC['tc0'])
    ln = float(np.linalg.norm(np.asarray(rk['tip'][k]) - np.asarray(rk['butt_cap'][k])))
    dr = float(np.linalg.norm(np.asarray(sk['right_wrist'][k]) - np.asarray(rk['handle_top'][k]))) / max(ln, 1)
    dl = float(np.linalg.norm(np.asarray(sk['left_wrist'][k]) - np.asarray(rk['handle_top'][k]))) / max(ln, 1)
    near = min(dr, dl); hand = 'right' if dr <= dl else 'left'
    sc = lin(near, 0.9, 0.3) if hand == 'right' else min(60, lin(near, 0.9, 0.3))
    chk('L_hand', 'labels', sc, dict(right=round(dr, 2), left=round(dl, 2)), 'At contact the %s wrist is %.2f racket-lengths from the handle%s.' % (hand, near, '' if hand == 'right' else ' (left-handed player, or left/right labels swapped?)'),
        'هنگام تماس مچ %s به اندازه‌ی %s طول راکت از دسته فاصله دارد%s.' % ('راست' if hand == 'right' else 'چپ', round(near, 2), '' if hand == 'right' else ' (بازیکن چپ‌دست یا جابه‌جایی چپ/راست در لیبل؟)'), 0.8, False,
        'Check that left/right labels are not swapped and that the racket belongs to the player.', 'مطمئن شوید چپ/راست جابه‌جا نشده و راکت مال همین بازیکن است.')
except Exception: pass

# ------------------------------------------------------------------ SCALE / CALIBRATION
H_PL = float(JC.get('player_h', 1.8)); cal = {}
try: cal = json.load(open(SP + '/nl/calib_report.json'))
except Exception: pass
if VIEW == 'back' and cal:
    used = cal['used']; ev = np.array([cal['err_px'][n] for n in used]); med = float(np.median(ev))
    chk('C_court_err', 'scale', lin(med, 12, 2), round(med, 1), 'Court calibration: median reprojection error %.1f px over %d used points (max %.0f px).' % (med, len(used), ev.max()),
        'کالیبراسیون زمین: میانه‌ی خطای بازتاب %s پیکسل روی %s نقطه (بیشینه %s پیکسل).' % (round(med, 1), len(used), round(float(ev.max()))), 2.0, med > 15,
        'Re-click the court points with the largest error (see calib_report.json) at higher zoom.', 'نقاط زمین با بیشترین خطا (calib_report.json) را با بزرگ‌نمایی بیشتر دوباره بزنید.')
    chk('C_court_n', 'scale', lin(len(used), 6, 16), len(used), '%d of %d court points were used.' % (len(used), cal['n_total']), '%s نقطه از %s نقطه‌ی زمین استفاده شد.' % (len(used), cal['n_total']), 1.5, len(used) < 8,
        'Label all 20 court points; points outside the image may be extrapolated but are down-weighted.', 'هر ۲۰ نقطه‌ی زمین را بزنید؛ نقاط بیرون از تصویر وزن کمتری دارند.')
    nr_, nf_ = sum('near' in n for n in used), sum('far' in n for n in used); nn = sum('net' in n for n in used)
    chk('C_court_spread', 'scale', 100 if (nr_ >= 3 and nf_ >= 3 and nn >= 2) else (60 if (nr_ >= 2 and nf_ >= 2) else 20), dict(near=nr_, far=nf_, net=nn),
        'Used points: %d near, %d far, %d net (depth range of the court is what fixes scale).' % (nr_, nf_, nn), 'نقاط استفاده‌شده: %s نزدیک، %s دور، %s تور (گستره‌ی عمق زمین مقیاس را تعیین می‌کند).' % (nr_, nf_, nn), 1.0, False,
        'Keep points at both ends of the court plus the net posts.', 'نقاطی در دو انتهای زمین و پایه‌های تور داشته باشید.')
    nrej = len(cal['rejected'])
    chk('C_court_rej', 'scale', lin(nrej, 8, 1), cal['rejected'], '%d court point(s) rejected as outliers%s.' % (nrej, (': ' + ', '.join(cal['rejected'][:4])) if nrej else ''),
        '%s نقطه‌ی زمین به‌عنوان پرت حذف شد%s.' % (nrej, (': ' + '، '.join(cal['rejected'][:4])) if nrej else ''), 0.8, False,
        'Rejected points are probably mis-clicked or outside the image: re-click or leave them out.', 'نقاط حذف‌شده احتمالاً اشتباه کلیک شده یا بیرون تصویرند: دوباره بزنید یا کنار بگذارید.')
    sn = cal.get('sensitivity')
    if sn: chk('C_court_stab', 'scale', min(lin(sn['noise4px_cam_std_m'], 0.6, 0.1), lin(sn['loo_dcam_max'], 1.0, 0.2)), sn,
               'Human-error test: 4 px click noise moves the camera by %.2f m (f %.1f%%); dropping any single point moves it by at most %.2f m (most influential: %s).' % (sn['noise4px_cam_std_m'], sn['noise4px_f_std_pct'], sn['loo_dcam_max'], sn['most_influential']),
               'آزمون خطای انسانی: نویز ۴ پیکسلی کلیک‌ها دوربین را %s متر جابه‌جا می‌کند (f: %s٪)؛ حذف هر تک‌نقطه حداکثر %s متر (اثرگذارترین: %s).' % (round(sn['noise4px_cam_std_m'], 2), round(sn['noise4px_f_std_pct'], 1), round(sn['loo_dcam_max'], 2), sn['most_influential']), 1.5, False,
               'If one point moves the camera a lot, re-click it carefully (usually a far or out-of-image corner).', 'اگر یک نقطه دوربین را زیاد جابه‌جا می‌کند، با دقت دوباره آن را بزنید (معمولاً گوشه‌ی دور یا بیرون از تصویر).')
    fr_ = cal['f'] / H_IMG; chk('C_focal', 'scale', 100 - lin(abs(fr_ - 0.515), 0.04, 0.16), round(fr_, 3), 'Fitted focal length f=%.0f px = %.3f x image height (phone main cameras: ~0.50-0.55).' % (cal['f'], fr_),
        'فاصله‌ی کانونی برازش‌شده f=%s پیکسل = %s برابر ارتفاع تصویر (گوشی‌های معمول: حدود ۰٫۵۰ تا ۰٫۵۵).' % (round(cal['f']), round(fr_, 3)), 1.2, False,
        'A strange f means the court points are inconsistent (or zoom/ultra-wide lens was used). Check the clicked points.', 'f غیرعادی یعنی نقاط زمین ناسازگارند (یا زوم/لنز واید استفاده شده). نقاط را بررسی کنید.')
    bad = (abs(cal['roll']) > 10) + (not (-14 <= cal['pitch'] <= 8)) + (not (0.7 <= cal['cam'][2] <= 3.0))
    chk('C_pose', 'scale', 100 - 40 * bad, dict(roll=round(cal['roll'], 1), pitch=round(cal['pitch'], 1), cam_z=round(cal['cam'][2], 2)),
        'Camera attitude: roll %.1f°, pitch %.1f°, height %.2f m.' % (cal['roll'], cal['pitch'], cal['cam'][2]), 'وضعیت دوربین: رول %s°، پیچ %s°، ارتفاع %s متر.' % (round(cal['roll'], 1), round(cal['pitch'], 1), round(cal['cam'][2], 2)), 0.8, False,
        'Hand-held roll >10° or a camera below 0.7 m / above 3 m is unusual: re-check court labels.', 'رول بیش از ۱۰° یا ارتفاع دوربین کمتر از ۰٫۷ یا بیشتر از ۳ متر غیرعادی است: لیبل زمین را بازبینی کنید.')
    ne = cal.get('net_err_px', {}); e0, e1 = ne.get('z0.000', 0), ne.get('z0.914', 0)
    chk('C_net', 'scale', 100 if e0 <= e1 else 40, dict(post_base=round(e0, 1), net_top=round(e1, 1)), 'Net-post labels agree with the model at ground level (%.0f px) better than at net-top height (%.0f px).' % (e0, e1) if e0 <= e1 else 'Net labels fit better at net-top height: they may have been clicked at the wrong height.',
        'لیبل پایه‌ی تور با مدل در سطح زمین (%s پیکسل) بهتر از ارتفاع بالای تور (%s پیکسل) سازگار است.' % (round(e0), round(e1)) if e0 <= e1 else 'لیبل تور در ارتفاع بالای تور بهتر جا می‌افتد: شاید ارتفاع اشتباه کلیک شده.', 0.5)
# independent scale test: player height (back: court scale vs stated height; side: scale comes from it, so this is a consistency echo only)
try:
    d3 = np.load(SP + '/%s/player3d_anch.npz' % LAB, allow_pickle=True); X = d3['X']; nm = [str(n) for n in d3['names']]; I = {k: i for i, k in enumerate(nm)}
    neck = X[:, I['top_spine'], 2]; floor = np.minimum(X[:, I['left_ankle'], 2], X[:, I['right_ankle'], 2]); rr = float(np.max(neck - floor) / H_PL)
    hg = bool(JC.get('height_given', False))
    if VIEW == 'back':
        sc = lin(abs(rr - 0.818), 0.12, 0.03) if hg else min(75, lin(abs(rr - 0.818), 0.12, 0.03))
        chk('C_height', 'scale', sc, round(rr, 3), 'Independent scale check: standing neck height / stated height = %.3f (expected 0.818 +/- 0.03)%s.' % (rr, '' if hg else '; height was NOT given, 1.80 m assumed (capped at 75)'),
            'آزمون مستقل مقیاس: نسبت ارتفاع گردن به قد = %s (انتظار ۰٫۸۱۸ ± ۰٫۰۳)%s.' % (round(rr, 3), '' if hg else '؛ قد داده نشد و ۱٫۸۰ فرض شد (سقف ۷۵)'), 2.0, False,
            'Pass the real player height with --height; a ratio far from 0.82 means the court scale or the height is wrong.', 'قد واقعی را با --height بدهید؛ نسبت دور از ۰٫۸۲ یعنی مقیاس زمین یا قد اشتباه است.')
    else:
        chk('C_height', 'scale', 100 if hg else 55, H_PL, 'Scale in the side view comes from the stated height %.2f m%s; +/-5 cm of height = +/-%.1f%% on every length.' % (H_PL, '' if hg else ' (NOT given: 1.80 m assumed)', 100 * 0.05 / H_PL),
            'مقیاس در نمای کنار از قد اعلام‌شده (%s متر) می‌آید%s؛ ±۵ سانتی‌متر خطای قد = ±%s٪ خطا در همه‌ی طول‌ها.' % (H_PL, '' if hg else ' (داده نشد، ۱٫۸۰ فرض شد)', round(100 * 0.05 / H_PL, 1)), 2.0, False,
            'Pass the real height with --height (measure the player barefoot).', 'قد واقعی را با --height بدهید (بدون کفش اندازه بگیرید).')
    tcu = int(round(JC['tc0'])) if VIEW == 'side' else int(round(float(M_.get('events', {}).get('contact', JC['tc0']))))
    es = np.array(L['skel']['right_shoulder'][tcu], float); ee = np.array(L['skel']['right_elbow'][tcu], float); ew = np.array(L['skel']['right_wrist'][tcu], float)
    u, v = es - ee, ew - ee; a2 = float(180 - np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))
    P = lambda n: X[tcu, I[n]]; u3, v3 = P('right_shoulder') - P('right_elbow'), P('right_wrist') - P('right_elbow'); a3 = float(180 - np.degrees(np.arccos(np.clip(u3 @ v3 / np.linalg.norm(u3) / np.linalg.norm(v3), -1, 1))))
    chk('C_elbow', 'pose', lin(abs(a2 - a3), 35, 8), dict(label2d=round(a2), lift3d=round(a3)), 'Contact-elbow angle: labels %d° vs 3D lift %d° (difference %d°; the reel quotes the label value).' % (a2, a3, abs(a2 - a3)),
        'زاویه‌ی آرنج در تماس: لیبل %s° در برابر بازسازی سه‌بعدی %s° (اختلاف %s°؛ ریل عدد لیبل را نشان می‌دهد).' % (round(a2), round(a3), round(abs(a2 - a3))), 0.5, False,
        'A big gap means depth is ambiguous for the arm: trust the 2D label value, not the 3D one.', 'اختلاف زیاد یعنی عمق بازو مبهم است: به عدد لیبل دوبعدی اعتماد کنید نه سه‌بعدی.')
    try:
        df = np.load(SP + '/%s/player3d_free.npz' % LAB, allow_pickle=True)['X']; dist = float(np.mean(np.linalg.norm(df - X, axis=2)))
        chk('C_anchor', 'pose', lin(dist, 0.30, 0.05), round(dist, 3), 'Free vs ball-anchored 3D lift differ by %.0f cm on average (depth ambiguity indicator).' % (dist * 100),
            'اختلاف بازسازی آزاد و لنگردار با توپ به‌طور میانگین %s سانتی‌متر است (شاخص ابهام عمق).' % round(dist * 100), 0.8, False)
    except Exception: pass
    ch = float(M_['contact']['height']); rc = ch / H_PL
    chk('C_contact_h', 'scale', 100 - lin(abs(rc - 1.55), 0.12, 0.30) , round(rc, 2), 'Contact height %.2f m = %.2f x player height (typical serves: 1.3-1.75).' % (ch, rc),
        'ارتفاع تماس %s متر = %s برابر قد (سرو معمولی: ۱٫۳ تا ۱٫۷۵).' % (round(ch, 2), round(rc, 2)), 1.0, abs(rc - 1.55) > 0.5)
except Exception as e: print('qc: height/3D checks skipped:', e)
lt, bt = logtext('lift.log'), logtext('ball.log')
m = re.findall(r'min foot z\s+(-?[\d.]+)', lt)
if m: z = float(m[-1]); chk('C_feet', 'pose', 100 - lin(abs(z), 0.03, 0.12), z, 'Lowest foot point of the 3D lift is %.0f cm from the ground plane.' % (z * 100), 'پایین‌ترین نقطه‌ی پا در بازسازی %s سانتی‌متر از سطح زمین فاصله دارد.' % round(z * 100), 0.8)
m = re.findall(r'px-rms\s+([\d.]+)', bt)
if m: r_ = float(m[-1]); chk('C_ball', 'scale', lin(r_, 8, 1.5), r_, 'Ballistic ball fit (gravity 9.81 m/s2 + drag) matches the ball labels to %.1f px rms: an independent metric-scale and timing check.' % r_,
                              'برازش بالستیک توپ (گرانش ۹٫۸۱ و پسا) با لیبل‌ها %s پیکسل rms اختلاف دارد: آزمون مستقل مقیاس و زمان.' % r_, 1.5, r_ > 12,
                              'Large residual: ball labels are noisy, the time axis is wrong, or the scale is off.', 'باقیمانده‌ی بزرگ: لیبل توپ پرنوسان است، محور زمان اشتباه است یا مقیاس نادرست.')
m = re.findall(r'reproj px: mean ([\d.]+)', bt)

# ------------------------------------------------------------------ AGGREGATE
GW = dict(video=0.10, labels=0.35, scale=0.35, pose=0.20); groups = {}
for g in GW:
    cs = [c for c in CHK if c['group'] == g]
    if cs: groups[g] = round(sum(c['score'] * c['weight'] for c in cs) / sum(c['weight'] for c in cs), 1)
overall = sum(groups[g] * GW[g] for g in groups) / sum(GW[g] for g in groups)
crit = [c['id'] for c in CHK if c['critical'] and c['score'] < 40]
if crit: overall = min(overall, 62 - 6 * (len(crit) - 1))
grade = 'A' if overall >= 85 else 'B' if overall >= 70 else 'C' if overall >= 55 else 'D'
byid = {c['id']: c['score'] for c in CHK}
def dep(ids, cap=1.0):
    v = [byid[i] for i in ids if i in byid]
    return None if not v else round((0.5 * min(v) + 0.5 * float(np.mean(v))) * cap, 1)
# which checks each reported number depends on; cap = extra distrust from the depth axis of that camera (back = depth is behind the player)
back = VIEW == 'back'
MT = {
 'knee_front': (['L_skel', 'L_spikes', 'C_anchor', 'C_height'], 0.95 if back else 1.0), 'knee_back': (['L_skel', 'L_spikes', 'C_anchor', 'C_height'], 0.95 if back else 1.0),
 'trunk': (['L_skel', 'L_spikes', 'C_anchor', 'C_height'], 0.85 if back else 1.0),
 'elbow_low': (['L_skel', 'L_spikes'] if back else ['L_skel', 'L_spikes', 'C_elbow', 'C_anchor'], 1.0 if back else 0.9),      # back quotes the 2D label angle, side the 3D one
 'elbow_ct': (['L_skel', 'L_contact'], 1.0),                                                                                  # always the 2D label angle
 'height': (['L_contact', 'C_height', 'C_contact_h', 'C_ball'] + (['C_court_err', 'C_court_n', 'C_court_spread', 'C_court_stab'] if back else []), 1.0),
 'timing': (['V_fps', 'L_contact'], 1.0), 'toss': (['L_ball', 'C_ball', 'C_height'] + (['C_court_err', 'C_court_stab'] if back else []), 0.85 if back else 1.0)}
if back: MT.update(speed=(['L_ball', 'L_contact', 'C_ball', 'C_court_err', 'C_court_n', 'C_court_spread', 'C_court_stab', 'V_fps'], 1.0), tilt=(['L_skel', 'L_spikes', 'C_anchor'], 0.8))
metric = {}
for k, (ids, cap) in MT.items():
    s = dep(ids, cap)
    if s is not None: metric[k] = dict(score=s, level='high' if s >= 80 else 'medium' if s >= 60 else 'low')
acts = [dict(id=c['id'], score=c['score'], en=c['action_en'], fa=c['action_fa']) for c in sorted(CHK, key=lambda c: c['score']) if c['score'] < 70 and c['action_en']]
out = dict(view=VIEW, name=JC['name'], overall=round(overall, 1), grade=grade, critical_failures=crit, groups=groups, metrics=metric, checks=CHK, actions=acts,
           note='score = 0-100; A>=85, B>=70, C>=55, D<55; a critical check below 40 caps the overall at 62. Metric score = mean of 50% min and 50% mean of the checks it depends on, times a depth factor.')
json.dump(out, open(SP + '/qc.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
GN = dict(video=('Video', 'ویدیو'), labels=('Labels', 'لیبل‌ها'), scale=('Scale & calibration', 'مقیاس و کالیبراسیون'), pose=('3D pose', 'پوز سه‌بعدی'))
LV = dict(high=('high', 'بالا'), medium=('medium', 'متوسط'), low=('low', 'پایین'))
ln = ['# Reliability report / گزارش قابلیت اعتماد - %s (%s view)' % (JC['name'], VIEW), '', '**Overall / کل: %s (%.0f/100)**%s' % (grade, overall, ('  - critical: ' + ', '.join(crit)) if crit else ''), '',
      '| group / گروه | score |', '|---|---|'] + ['| %s / %s | %.0f |' % (GN[g][0], GN[g][1], v) for g, v in groups.items()] + ['', '## Trust per number in the reel / اعتماد به هر عدد', '', '| metric | score | level / سطح |', '|---|---|---|']
ln += ['| %s | %.0f | %s / %s |' % (k, v['score'], LV[v['level']][0], LV[v['level']][1]) for k, v in metric.items()] + ['', '## Checks / بررسی‌ها', '']
for c in sorted(CHK, key=lambda c: c['score']): ln += ['- **%s** [%s] %.0f - %s' % (c['id'], c['group'], c['score'], c['en']), '  %s' % c['fa']]
if acts: ln += ['', '## What to fix first / اول چه چیزی را اصلاح کنیم', ''] + ['- (%s, %.0f) %s / %s' % (a['id'], a['score'], a['en'], a['fa']) for a in acts]
open(SP + '/qc.md', 'w').write('\n'.join(ln) + '\n')
print('QC grade %s  overall %.0f  groups %s' % (grade, overall, groups)); print('metric trust:', {k: v['level'] for k, v in metric.items()})
for c in sorted(CHK, key=lambda c: c['score'])[:6]: print('  %-14s %5.0f  %s' % (c['id'], c['score'], c['en'][:110]))

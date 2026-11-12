"""Automatic reel texts from the measured numbers: strengths, training priorities, serve-type check, verdict, long-shot rows.
Everything here is derived from data.py (MET/X) + metrics.json, so a new video needs no hand-written text."""
import json, os
SP = os.environ['REEL_JOB']; JC = json.load(open(SP + '/job.json'))
from data import MET, X, status
from ui import fa
D = json.load(open(SP + '/' + JC['ana'] + '/metrics.json')); VIEW = JC['view']; A = 'A'
def F(x, p=0): return fa(('%.' + str(p) + 'f') % x)
def V(m): return MET[m][A]
def ok(m): return m in MET and status(m, V(m)) == 'ok'
def zsc(m):
    M = MET[m]; v = V(m)
    return (v / M['mean'] - 1) / 0.1 if M['sd'] is None else (v - M['mean']) / M['sd']
# ---------------- strengths
def strengths():
    out = []
    if ok('knee_front') and ok('knee_back'): out.append(('خمش زانوی جلو و عقب (%s° و %s°) داخل محدوده‌ی حرفه‌ای است.' % (F(V('knee_back') if False else V('knee_front')), F(V('knee_back'))), 'Front and back knee flexion (%d° and %d°) are inside the pro ranges.' % (V('knee_front'), V('knee_back'))))
    elif ok('knee_front'): out.append(('خمش زانوی جلو (%s°) داخل محدوده‌ی حرفه‌ای است.' % F(V('knee_front')), 'Front-knee flexion (%d°) is inside the pro range.' % V('knee_front')))
    elif ok('knee_back'): out.append(('خمش زانوی عقب (%s°) داخل محدوده‌ی حرفه‌ای است.' % F(V('knee_back')), 'Back-knee flexion (%d°) is inside the pro range.' % V('knee_back')))
    if ok('elbow_ct') and V('elbow_ct') <= 25: out.append(('بازو هنگام تماس تقریباً کاملاً کشیده است (حدود %s° خمش).' % F(V('elbow_ct')), 'The arm is almost fully extended at contact (about %d° of flexion).' % V('elbow_ct')))
    if ok('elbow_low'): out.append(('خمش آرنج در پایین‌ترین نقطه‌ی راکت (%s°) داخل محدوده‌ی حرفه‌ای است.' % F(V('elbow_low')), 'Elbow flexion at the racket low point (%d°) is inside the pro range.' % V('elbow_low')))
    if 'tilt' in MET and ok('tilt'): out.append(('شیب شانه‌ها هنگام تماس حدود %s° است؛ نزدیک الگو (حدود %s°).' % (F(V('tilt')), F(MET['tilt']['mean'])), 'Shoulder tilt at contact is about %d°, near the pro value (about %d°).' % (V('tilt'), MET['tilt']['mean'])))
    if X[A].get('toss_apex', 0) >= 3.2: out.append(('اوج پرتاب توپ بالاست: حدود %s m.' % F(X[A]['toss_apex'], 1), 'The toss is high: apex about %.1f m.' % X[A]['toss_apex']))
    if ok('height'): out.append(('ارتفاع تماس (%s m) نزدیک الگوی نخبگان است.' % F(V('height'), 2), 'Contact height (%.2f m) is close to the elite pattern.' % V('height')))
    if ok('trunk'): out.append(('شیب تنه در تروفی (%s°) داخل محدوده‌ی حرفه‌ای است.' % F(V('trunk')), 'Trunk inclination at the trophy (%d°) is inside the pro range.' % V('trunk')))
    if not out: out.append(('هیچ معیاری داخل محدوده‌ی حرفه‌ای نیست؛ اولویت‌ها را ببین.', 'No metric is inside the pro range; see the priorities.'))
    return out[:3]
# ---------------- priorities
def prio_items():
    it = []
    def add(m, fa_s, en_s):
        if m in MET and not ok(m): it.append((abs(zsc(m)), fa_s, en_s))
    add('height', 'تماس را بالاتر ببر: حدود %s m در برابر حدود ۳٫۰ m.' % F(V('height') if 'height' in MET else 0, 2), 'Raise the contact point: about %.2f m vs about 3.0 m.' % (V('height') if 'height' in MET else 0))
    if 'speed' in MET: add('speed', 'سرعت توپ حدود %s km/h است؛ نخبگان حدود ۱۸۳. آن را با زنجیره‌ی پا، تنه و بازو بساز.' % F(V('speed')), 'Ball speed is about %d km/h vs about 183 for elite men. Build it through the leg, trunk and arm chain.' % V('speed'))
    if 'trunk' in MET:
        s = 'view' if VIEW == 'side' else 'back'; extra_fa = '' if VIEW == 'side' else ' (با ویدیوی از کنار تأیید شود)'; extra_en = '' if VIEW == 'side' else ' (confirm with side-on video)'
        add('trunk', 'در تروفی تنه را بیشتر خم کن: %s° در برابر حدود ۲۵°%s.' % (F(V('trunk')), extra_fa), 'Tilt the trunk more at the trophy: %d° vs about 25°%s.' % (V('trunk'), extra_en))
    if 'knee_back' in MET:
        lo = V('knee_back') < MET['knee_back']['mean']
        add('knee_back', ('زانوی عقب را بیشتر خم کن: %s° در برابر حدود ۶۷° (بارگذاری پا کم است).' if lo else 'زانوی عقب بیش از محدوده‌ی حرفه‌ای خم می‌شود: %s° در برابر حدود ۶۷°.') % F(V('knee_back')), ('Bend the back knee more: %d° vs about 67° (the leg load is small).' if lo else 'The back knee bends more than the pro range: %d° vs about 67°.') % V('knee_back'))
    if 'knee_front' in MET:
        lo = V('knee_front') < MET['knee_front']['mean']
        add('knee_front', ('زانوی جلو را بیشتر خم کن: %s° در برابر حدود ۶۵°.' if lo else 'زانوی جلو بیش از محدوده‌ی حرفه‌ای خم می‌شود: %s° در برابر حدود ۶۵°.') % F(V('knee_front')), ('Bend the front knee more: %d° vs about 65°.' if lo else 'The front knee bends more than the pro range: %d° vs about 65°.') % V('knee_front'))
    if 'elbow_ct' in MET and V('elbow_ct') > MET['elbow_ct']['mean']: add('elbow_ct', 'بازو را هنگام تماس بیشتر بکش: %s° خمش در برابر حدود ۳۰°.' % F(V('elbow_ct')), 'Extend the arm more at contact: %d° of flexion vs about 30°.' % V('elbow_ct'))
    if 'elbow_low' in MET: add('elbow_low', 'خمش آرنج در پایین‌ترین نقطه‌ی راکت %s° است؛ الگو حدود ۱۰۴°.' % F(V('elbow_low')), 'Elbow flexion at the racket low point is %d°; the pattern is about 104°.' % V('elbow_low'))
    it.sort(key=lambda t: -t[0]); out = [(a, b) for _, a, b in it][:3]
    if not out: out = [('همه‌ی معیارها داخل محدوده‌اند؛ الگو را حفظ کن و با چند سرو دیگر تأیید کن.', 'All metrics are inside the ranges; keep the pattern and confirm it on more serves.')]
    return out
# ---------------- serve type check (flat vs kick)
def sg(v, kick, flat, hi_is_flat=True):   # returns 'y' (kick-like) / 'n' (flat-like) / 'm' neutral
    if hi_is_flat: return 'n' if v >= flat else ('y' if v <= kick else 'm')
    return 'n' if v <= flat else ('y' if v >= kick else 'm')
def rows():
    R = []
    if VIEW == 'back':
        tx = D['toss']['apex_minus_neck_x'] * 100; cx = D['contact']['ball_minus_neck_x'] * 100; up = D['racket_2d']['head_dy_px_per_frame'] < 0; nc = D['ball']['net_clear']; sp = D['ball']['speed_kmh']
        sgn = lambda v: ('+' if v >= 0 else '−') + '%d' % abs(round(v))
        R.append((('محل پرتاب (جانبی)', 'Toss apex, sideways'), ('کیک: بالای سر یا کمی چپ‌تر', 'Kick: over the head, or just left'), (sgn(tx) + ' cm', sgn(tx) + ' cm', sg(tx, 5, 10))))
        R.append((('محل تماس (جانبی)', 'Contact point, sideways'), ('کیک: ۳۰ تا ۳۵ cm چپ‌تر از فلت', 'Kick: 30–35 cm further left than flat'), (sgn(cx) + ' cm', sgn(cx) + ' cm', sg(cx, -25, -5))))
        R.append((('حرکت راکت در تماس', 'Racket motion at contact'), ('همه‌ی سرو‌ها رو به بالا می‌روند', 'Every serve rises through contact'), ('رو به بالا', 'Upward', 'm') if up else ('افقی یا پایین', 'Level or down', 'u')))
        R.append((('عبور از تور', 'Clearance over the net'), ('کیک: بلندتر از فلت', 'Kick: higher than flat'), ('%s m' % F(nc, 2), '%.2f m' % nc, sg(nc, 1.0, 0.6, False))))
        R.append((('جهش بعد از زمین', 'Bounce after landing'), ('کیک: جهش بلند', 'Kick: bounces high'), ('داده کافی نیست', 'Too few frames', 'u')))
        R.append((('سرعت توپ', 'Ball speed'), ('کیک: کندتر از فلت اول', 'Kick: slower than a flat first serve'), ('%s km/h' % F(sp), '%d km/h' % round(sp), sg(sp, 105, 135))))
    else:
        ta = D['toss']['apex_ahead_of_head'] * 100; ca = D['contact']['ball_ahead_of_head'] * 100; pu = D['racket']['path_up_deg']
        lab = lambda v: ((('%s cm جلوتر از سر' % F(abs(v))) if v >= 0 else ('%s cm عقب‌تر از سر' % F(abs(v)))), (('%d cm ahead of the head' % round(abs(v))) if v >= 0 else ('%d cm behind the head' % round(abs(v)))))
        R.append((('محل اوج پرتاب (جلو/عقب)', 'Toss apex, forward/back'), ('کیک: بالای سر یا کمی عقب‌تر', 'Kick: over the head or slightly behind'), (*lab(ta), sg(ta, 10, 25))))
        R.append((('محل تماس (جلو/عقب)', 'Contact point, forward/back'), ('فلت: جلوی سر · کیک: بالای سر', 'Flat: in front of the head · kick: above it'), (*lab(ca), sg(ca, 0, 30))))
        R.append((('مسیر راکت در تماس', 'Racket path at contact'), ('کیک: برس رو به بالا با زاویه‌ی تند', 'Kick: steep upward brush'), (('%s° رو به بالا' % F(pu)) if pu >= 5 else ('تقریباً افقی (%s°)' % (('+' if pu >= 0 else '−') + F(abs(pu)))), ('%d° upward' % round(pu)) if pu >= 5 else ('Almost level (%s%d°)' % ('+' if pu >= 0 else '−', abs(round(pu)))), sg(pu, 15, 5, False))))
    return R
def verdict(R):
    n = sum(1 for r in R if r[2][2] == 'n'); y = sum(1 for r in R if r[2][2] == 'y')
    if n > y: kind = 'flat'
    elif y > n: kind = 'kick'
    else: kind = 'unsure'
    if kind == 'flat': v = ('فلت — پرتاب، تماس و مسیر راکت با سرو فلت سازگارند', 'Flat: toss, contact and racket path are consistent with a flat serve')
    elif kind == 'kick': v = ('کیک — پرتاب، تماس و مسیر راکت با سرو کیک سازگارند', 'Kick: toss, contact and racket path are consistent with a kick serve')
    else: v = ('نامطمئن — اندازه‌ها فلت را از کیک جدا نمی‌کنند', 'Unsure: the measurements do not separate flat from kick')
    return kind, v
TROWS = rows(); KIND, _v = verdict(TROWS); VER = (_v,)
TYPE = {'A': {'flat': ('سرو فلت', 'FLAT SERVE'), 'kick': ('سرو کیک', 'KICK SERVE'), 'unsure': ('سرو', 'SERVE')}[KIND]}
STR = strengths(); PRI = prio_items()
fps = JC.get('fps_real', 30)
if VIEW == 'back': LIMIT = ('محدودیت: یک دوربین پشت خط، حدود %s fps واقعی (زمان فریم‌ها نایکنواخت و اصلاح‌شده)؛ خطای زاویه ±۱۰ تا ۱۵° و سرعت ±۱۰٪. معیارها از مطالعات ناهمگن‌اند و راهنما هستند، نه حکم.' % fa(str(fps)), 'Limits: one camera behind the baseline, about %s real fps (irregular frame timing, corrected); angle error ±10–15°, speed ±10%%. Reference values come from heterogeneous studies: guidance, not norms.' % fps)
else: LIMIT = ('محدودیت: یک دوربین از کنار و %s fps واقعی؛ عمق دیده نمی‌شود، مقیاس از قد %s m؛ خطای زاویه ±۱۰ تا ۱۵°. معیارها راهنما هستند، نه حکم.' % (fa(str(fps)), fa('%.2f' % JC['player_h'])), 'Limits: one side camera, real %s fps; depth is not seen, scale from a %.2f m height; angle error ±10–15°. Reference values are guidance, not norms.' % (fps, JC['player_h']))
def long_rows():
    x = X[A]; sg_ = lambda v: ('+' if v >= 0 else '−') + '%d cm' % abs(round(v))
    return [('سرعت توپ', 'Ball speed', '%d km/h' % round(D['ball']['speed_kmh'])), ('ارتفاع تماس', 'Contact height', '%.2f m' % V('height')), ('عبور از تور', 'Clearance over the net', '%.2f m' % D['ball']['net_clear']),
            ('تماس نسبت به خط پایه', 'Contact vs baseline', sg_(x['ahead'])), ('تروفی تا تماس', 'Trophy to contact', '%d ms' % x['t_tc']), ('فرود نسبت به خط پایه', 'Landing vs baseline', sg_(x['landing']))]
LONGROWS = long_rows() if VIEW == 'back' else []

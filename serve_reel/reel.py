#!/usr/bin/env python3
"""tennis-reel-kit: serve video + CVAT labels -> Instagram analysis reel (EN + FA).
   python3 reel.py make --view back|side --video clip.MOV --labels cvat.zip --name myserve [--height 1.80] [--draft] [--out DIR]
   python3 reel.py check           # verify the installation
   python3 reel.py make ... --from STAGE   # re-run from a stage (after editing job.json)"""
import os, sys, json, argparse, subprocess, shutil, time, glob
KIT = os.path.dirname(os.path.abspath(__file__)); os.environ['REEL_KIT'] = KIT
sys.path.insert(0, os.path.join(KIT, 'code', 'common'))
PY = sys.executable
def mp_python():
    for c in (os.environ.get('REEL_MPPY'), os.path.join(KIT, 'mpenv', 'bin', 'python')):
        if c and os.path.exists(c): return c
    return PY
STAGES_BACK = ['prepare', 'calib', 'pose', 'lift_free', 'ball', 'lift_anch', 'motion', 'metrics', 'qc', 'plan', 'render', 'build', 'encode']
STAGES_SIDE = ['prepare', 'calib', 'pose', 'lift_free', 'ball', 'lift_anch', 'motion', 'metrics', 'qc', 'plan', 'render', 'build', 'encode']

def run(job, args, log, env_extra=None, py=None, cwd=None):
    env = dict(os.environ, REEL_JOB=job, PYTHONDONTWRITEBYTECODE='1'); env.update(env_extra or {})
    with open(os.path.join(job, 'logs', log), 'a') as f:
        f.write('\n$ ' + ' '.join(map(str, args)) + '\n'); f.flush()
        r = subprocess.run([py or PY, '-I'] + [str(a) for a in args], env=env, stdout=f, stderr=subprocess.STDOUT, cwd=cwd or job)
    if r.returncode != 0:
        tail = open(os.path.join(job, 'logs', log)).read()[-1500:]; sys.exit('FAILED: %s %s\n--- log tail (%s) ---\n%s' % (args[0], ' '.join(map(str, args[1:])), log, tail))

def setup_job(job, view):
    """job dir mirrors the code layout (scripts use REEL_JOB as root)"""
    os.makedirs(os.path.join(job, 'logs'), exist_ok=True); src = os.path.join(KIT, 'code', view)
    for d in os.listdir(src):
        dst = os.path.join(job, d)
        shutil.copytree(os.path.join(src, d), dst, dirs_exist_ok=True)
    ana = os.path.join(job, 'nr' if view == 'back' else 'nq', 'ana')
    for f in ('autotext.py', 'gen_data.py', 'charts_slide.py', 'qc.py', 'data_%s.tpl' % view): shutil.copy(os.path.join(KIT, 'code', 'common', f), ana if f.endswith('.py') else job)
    for lnk, tgt in (('assets', os.path.join(KIT, 'assets')),):
        if not os.path.exists(os.path.join(job, lnk)): os.symlink(tgt, os.path.join(job, lnk))
    ft = os.path.join(job, 'fonts_vz', 'fonts'); os.makedirs(ft, exist_ok=True)
    if not os.path.exists(os.path.join(ft, 'ttf')): os.symlink(os.path.join(KIT, 'fonts'), os.path.join(ft, 'ttf'))

def done(job, st): return os.path.exists(os.path.join(job, '.done', st))
def mark(job, st): os.makedirs(os.path.join(job, '.done'), exist_ok=True); open(os.path.join(job, '.done', st), 'w').write(time.ctime())

def charts_of(job, view):
    """effective chart mode from job.json: back long|both|timeline, side timeline|none"""
    c = json.load(open(os.path.join(job, 'job.json'))).get('charts')
    return c or ('long' if view == 'back' else 'timeline')

def render(job, view, samples, log):
    d = 'nr' if view == 'back' else 'nq'
    plans = [('ro', 'oo', 'plan_o.json', 149, 0), ('rf', 'of', 'plan_f.json', 143, 0)] + ([('rl', 'ol', 'plan_l.json', 239, 1)] if view == 'back' and charts_of(job, view) != 'timeline' else [])
    for rdir, odir, plan, last, fadeout in plans:
        rd = os.path.join(job, d, rdir)
        for attempt in range(6):
            run(job, [os.path.join(d, 'scene_nr.py'), os.path.join(d, rdir), 0, last, '--samples', samples, '--plan', plan], log)
            if len(glob.glob(rd + '/t*.png')) >= last + 1: break
        else: sys.exit('render did not complete for ' + rdir + '; see logs/' + log + ' (re-run the same command to resume)')
        run(job, [os.path.join(d, 'comp.py'), os.path.join(d, rdir), os.path.join(d, odir)], log, env_extra=dict(PLAN=plan, FADEOUT=str(fadeout)))

def encode(job, view, name, outdir):
    d = os.path.join(job, 'nr' if view == 'back' else 'nq'); os.makedirs(outdir, exist_ok=True)
    n = len(glob.glob(d + '/fin_en/f*.png')); dur = n / 30.0
    vb = int(min(4200, 27.0 * 1024 * 1024 * 8 / dur * 0.96 / 1000))            # EN: two-pass, stays below 30 MiB
    en = os.path.join(outdir, '%s_reel_EN.mp4' % name); fa = os.path.join(outdir, '%s_reel_FA.mp4' % name)
    F = ['-framerate', '30', '-i', d + '/fin_en/f%05d.png', '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '%dk' % vb, '-maxrate', '4500k', '-bufsize', '6000k', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + F + ['-pass', '1', '-passlogfile', d + '/pl', '-an', '-f', 'mp4', os.devnull], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + F + ['-pass', '2', '-passlogfile', d + '/pl', en], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', d + '/fin_fa/f%05d.png', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', fa], check=True)
    print('OUTPUT', en, '%.1f MiB' % (os.path.getsize(en) / 2**20), '| FA', fa, '%.1f MiB' % (os.path.getsize(fa) / 2**20), '| %.1f s' % dur)

def make(a):
    view = a.view; job = os.path.abspath(os.path.join(a.work, a.name)); stages = STAGES_BACK if view == 'back' else STAGES_SIDE
    d = 'nr' if view == 'back' else 'nq'; lab = 'nl' if view == 'back' else 'sw'; mpy = mp_python()
    samples = '1' if a.draft else '4'; frm = stages.index(a.from_stage) if a.from_stage else 0
    os.makedirs(job, exist_ok=True)
    def S(name, fn):
        if stages.index(name) < frm or (done(job, name) and not a.from_stage and name != 'build' and name != 'encode'): print('skip', name); return
        if a.until and stages.index(name) > stages.index(a.until): return
        t = time.time(); print('==', name, flush=True); fn(); mark(job, name); print('   %s done in %.0f s' % (name, time.time() - t), flush=True)
    def prep():
        import prepare
        setup_job(job, view); CH = {'back': {'auto': 'long', 'off': 'long', 'add': 'both', 'replace': 'timeline'}, 'side': {'auto': 'timeline', 'add': 'timeline', 'replace': 'timeline', 'off': 'none'}}[view][a.charts]
        prepare.prepare(job, a.video, a.labels, view, a.name, a.height or 1.80, hand=a.hand, overrides=dict(handle=a.handle, charts=CH, height_given=a.height is not None, qc_badge=a.qc_badge))
        setup_job(job, view)
    if frm == 0 or not os.path.exists(os.path.join(job, 'job.json')): S('prepare', prep)
    else:
        setup_job(job, view)
        if a.charts != 'auto' or a.qc_badge:          # changing these later: edit job.json, then re-run with --from build
            jj = json.load(open(os.path.join(job, 'job.json')))
            if a.charts != 'auto': jj['charts'] = {'back': {'off': 'long', 'add': 'both', 'replace': 'timeline'}, 'side': {'off': 'none', 'add': 'timeline', 'replace': 'timeline'}}[view][a.charts]
            if a.qc_badge: jj['qc_badge'] = True
            json.dump(jj, open(os.path.join(job, 'job.json'), 'w'), indent=1)
    py_lab = lambda s: os.path.join(lab, s)
    if view == 'back': S('calib', lambda: run(job, [py_lab('calib.py')], 'calib.log'))
    else: S('calib', lambda: run(job, [py_lab('prep.py')], 'calib.log'))
    S('pose', lambda: run(job, [py_lab('pose_run.py' if view == 'back' else 'pose_run2.py')], 'pose.log', py=mpy))
    S('lift_free', lambda: run(job, [py_lab('lift.py'), 'free'], 'lift.log'))
    S('ball', lambda: run(job, [py_lab('ball.py' if view == 'back' else 'ballrun.py')] + ([] if view == 'back' else ['free']), 'ball.log', env_extra={} if view == 'back' else dict(SAVE='1')))
    S('lift_anch', lambda: run(job, [py_lab('lift.py'), 'anch'], 'lift.log'))
    def motion():
        for f in ('motion_nl.pkl',):
            p = os.path.join(job, d, f)
            if os.path.exists(p): os.remove(p)
        run(job, [os.path.join(d, 'motion_lab2.py')], 'motion.log')
    S('motion', motion)
    def metrics(): run(job, [os.path.join(d, 'ana', 'metrics.py')], 'metrics.log'); run(job, [os.path.join(d, 'ana', 'gen_data.py')], 'metrics.log')
    S('metrics', metrics)
    def qc(): shutil.copy(os.path.join(KIT, 'code', 'common', 'qc.py'), os.path.join(job, 'qc.py')); run(job, [os.path.join(job, 'qc.py')], 'qc.log'); print(open(os.path.join(job, 'logs', 'qc.log')).read().split('$')[-1].split('\n', 1)[-1].rstrip())
    S('qc', qc)
    S('plan', lambda: run(job, [os.path.join(d, 'plan_all.py')], 'plan.log'))
    S('render', lambda: render(job, view, samples, 'render.log'))
    def build():
        ch = charts_of(job, view)
        segs = ['intro', 'model', 'orb', 'freeze'] + ({'long': ['long'], 'both': ['long', 'timeline'], 'timeline': ['timeline']}[ch] if view == 'back' else (['timeline'] if ch != 'none' else [])) + ['stype', 'score', 'verdict', 'sources']
        for s in segs: run(job, [os.path.join(d, 'ana', 'build.py'), s], 'build.log')       # one segment per process: keeps memory low
    S('build', build)
    S('encode', lambda: encode(job, view, a.name, os.path.abspath(a.out)))

def check():
    ok = True
    def t(name, cond, hint=''):
        nonlocal ok; print(('OK   ' if cond else 'FAIL ') + name + ('' if cond else '  -> ' + hint)); ok &= bool(cond)
    t('python >= 3.10', sys.version_info >= (3, 10))
    for m in ('numpy', 'scipy', 'cv2', 'PIL', 'jax', 'bpy'):
        try: __import__(m); t('import ' + m, True)
        except Exception as e: t('import ' + m, False, 'pip install ' + {'cv2': 'opencv-python-headless', 'PIL': 'pillow', 'bpy': 'bpy'}.get(m, m))
    try:
        from PIL import features; t('Pillow with libraqm (Persian text shaping)', features.check('raqm'), 'install libraqm (apt install libraqm0) and a Pillow wheel with raqm')
    except Exception: pass
    for b in ('ffmpeg', 'ffprobe'): t(b, shutil.which(b) is not None, 'install ffmpeg')
    mpy = mp_python(); r = subprocess.run([mpy, '-c', 'import mediapipe as m; m.solutions.pose'], capture_output=True); t('mediapipe pose (%s)' % mpy, r.returncode == 0, 'run ./setup.sh (creates mpenv with mediapipe 0.10.14 on python 3.12)')
    t('assets (stadium/ball/racket)', all(os.path.exists(os.path.join(KIT, 'assets', a)) for a in ('stadium', 'ball', 'racket')), 'copy the three Blender asset folders into assets/ - see assets/README_ASSETS.md')
    t('fonts', len(glob.glob(os.path.join(KIT, 'fonts', '*.ttf'))) >= 4)
    print('\nALL GOOD' if ok else '\nFix the FAIL lines above, then re-run: python3 reel.py check'); return ok

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    m = sp.add_parser('make'); m.add_argument('--view', choices=['back', 'side'], required=True, help='back = camera behind the baseline (court visible), side = camera at the side of the player')
    m.add_argument('--video', required=True); m.add_argument('--labels', required=True, help='CVAT "video 1.1" export (zip or annotations.xml)'); m.add_argument('--name', required=True)
    m.add_argument('--height', type=float, default=None, help='player height in metres (side view scale, back view cross-check); 1.80 is assumed if omitted (and the reliability grade is capped)')
    m.add_argument('--charts', choices=['auto', 'off', 'add', 'replace'], default='auto', help='posture-timeline charts slide. back: auto/off = long shot only, add = long shot + charts, replace = charts instead of the long shot. side: auto/add/replace = charts, off = none')
    m.add_argument('--hand', choices=['auto', 'right', 'left'], default='auto', help="racket hand; auto = the wrist nearest the handle at contact. Left-handers are mirrored (video + labels) so the pipeline sees a right-hander; numbers are symmetric, the avatar in the reel is drawn right-handed")
    m.add_argument('--qc-badge', action='store_true', help='print the reliability grade on the sources slide'); m.add_argument('--handle', default='@tennismad.ai', help='Instagram handle printed on every frame'); m.add_argument('--draft', action='store_true', help='faster, noisier render (1 sample instead of 4)')
    m.add_argument('--work', default=os.path.join(KIT, 'work')); m.add_argument('--out', default=os.path.join(KIT, 'output')); m.add_argument('--from', dest='from_stage', choices=STAGES_BACK); m.add_argument('--until', choices=STAGES_BACK, help='stop after this stage')
    sp.add_parser('check'); a = ap.parse_args()
    if a.cmd == 'check': sys.exit(0 if check() else 1)
    make(a)

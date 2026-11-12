"""Compose the serve-breakdown reel: 3D renders (seq/) + neon HUD (Pillow) -> mp4.
usage: python3 -I reel.py SEQ_DIR OUT.mp4 [--still cpN]   (--still writes a single HUD frame PNG for review)
All text lives in CONFIG below; anchors come from the projection json exported by render_cp.py (normalised 0..1, y down).
"""
import sys, os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
LIME = (166, 255, 20)
WHITE = (245, 247, 250)
FONT = '/usr/share/fonts/opentype/inter/'
def font(w, size): return ImageFont.truetype(FONT + f'Inter-{w}.otf', size)
F_HDR, F_TITLE, F_SUB, F_PILL, F_BIG = font('Bold', 26), font('Black', 104), font('SemiBold', 48), font('ExtraBold', 30), font('Black', 132)

CONFIG = dict(
    series='SERVE BREAKDOWN',
    intro=('SLOW-MO BREAKDOWN', 'THE SERVE', '5 checkpoints to copy'),
    outro_title='ALL 5 · SLOW-MO',
    outro_items=['Straight toss arm', 'Knees bent, racket up', 'Racket drops behind', 'Reach up. Arm long.', 'Swing through. Land left.'],
    cps=[
        dict(key='cp1', frame=59, title='TOSS', sub='Straight arm. Ball goes up.', xf=(1.0, 0, 0), ann=[
            ('line', 'left_shoulder', 'left_wrist'), ('label', 'left_elbow', 'TOSS ARM STRAIGHT', (-300, -120)),
            ('ring', 'ball', 60), ('label', 'ball', 'RELEASE POINT', (110, -90))]),
        dict(key='cp2', frame=67, title='TROPHY', sub='Bend the knees. Racket up.', xf=(1.0, 0, 0), ann=[
            ('ring', 'right_knee', 70), ('ring', 'left_knee', 70), ('label', 'right_knee', 'KNEES BENT', (-330, 40)),
            ('ring', 'racket_string_bed_center', 70), ('label', 'racket_string_bed_center', 'RACKET UP & BACK', (-60, -150)),
            ('label', 'left_wrist', 'TOSS ARM STAYS UP', (90, -80))]),
        dict(key='cp3', frame=71, title='DROP', sub='Racket falls behind. Ball hangs.', xf=(1.0, 0, 0), ann=[
            ('ring', 'racket_string_bed_center', 80), ('label', 'racket_string_bed_center', 'RACKET DROPS BEHIND', (-380, 90)),
            ('hline', 'ball', 'BALL AT THE TOP', (-380, 0))]),
        dict(key='cp4', frame=74, title='CONTACT', sub='Reach up. Arm long.', xf=(1.0, 0, 0), ann=[
            ('line', 'right_shoulder', 'right_wrist'), ('label', 'right_elbow', 'ARM LONG', (-260, 40)),
            ('line', 'left_shoulder', 'right_shoulder'), ('label', 'left_shoulder', 'SHOULDERS TILTED', (-60, 150)),
            ('ring', 'racket_string_bed_center', 80), ('label', 'racket_string_bed_center', 'HIGH POINT', (130, -80))]),
        dict(key='cp5', frame=80, title='FINISH', sub='Swing through. Land left.', xf=(1.0, 0, 0), ann=[
            ('ring', 'left_ankle', 75), ('label', 'left_ankle', 'LAND ON LEFT FOOT', (120, 20)),
            ('ring', 'right_ankle', 75), ('label', 'right_ankle', 'RIGHT LEG KICKS BACK', (-420, -60)),
            ('ring', 'racket_string_bed_center', 80), ('label', 'racket_string_bed_center', 'RACKET LOW ACROSS', (120, 60))]),
    ])

ease = lambda x: 1 - (1 - min(max(x, 0.0), 1.0)) ** 3
def clampi(x, a, b): return max(a, min(b, x))

def load_base(path, xf):
    im = Image.open(path).convert('RGB'); s, ox, oy = xf
    bg = im.getpixel((4, 4)); canvas = Image.new('RGB', (W, H), bg)
    im = im.resize((int(W * s), int(H * s)), Image.LANCZOS); canvas.paste(im, (int(ox), int(oy))); return canvas

def top_shade(img, h=700, a0=150):
    g = Image.new('L', (W, H), 0); d = ImageDraw.Draw(g)
    for y in range(h): d.line([(0, y), (W, y)], fill=int(a0 * (1 - y / h) ** 1.6))
    black = Image.new('RGB', (W, H), (0, 0, 0)); return Image.composite(black, img, g)

def text_spaced(d, xy, s, f, fill, sp=4):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + sp
    return x

class Hud:
    def __init__(self, proj, xf): self.p = proj; self.xf = xf; self.fx = Image.new('RGBA', (W, H), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.fx)
    def pt(self, name):
        x, y, _ = self.p[name]; s, ox, oy = self.xf; return (x * W * s + ox, y * H * s + oy)
    def ring(self, name, r, p):
        c = self.pt(name); box = [c[0] - r, c[1] - r, c[0] + r, c[1] + r]
        if p > 0: self.d.arc(box, -90, -90 + 360 * ease(p), fill=LIME + (255,), width=6)
    def line(self, a, b, p):
        A, B = self.pt(a), self.pt(b); e = ease(p); E = (A[0] + (B[0] - A[0]) * e, A[1] + (B[1] - A[1]) * e)
        self.d.line([A, E], fill=LIME + (255,), width=7)
        for q in (A, E): self.d.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9], fill=LIME + (255,))
    def hline(self, name, p):
        c = self.pt(name); x0 = 40; x1 = x0 + (W - 80) * ease(p); x = x0
        while x < x1: self.d.line([(x, c[1]), (min(x + 26, x1), c[1])], fill=LIME + (230,), width=4); x += 46
    def label(self, name, text, off, p, anchor_dot=True):
        a = self.pt(name); tw = self.d.textlength(text, font=F_PILL); ph, pw = 56, tw + 36
        x = clampi(a[0] + off[0], 36, W - 36 - pw); y = clampi(a[1] + off[1], 330, H - 380 - ph); e = ease(p)
        if e <= 0: return
        c = (x + pw / 2, y + ph / 2); k = ease(min(1, p * 1.6))
        end = (a[0] + (c[0] - a[0]) * k, a[1] + (c[1] - a[1]) * k); self.d.line([a, end], fill=LIME + (255,), width=4)
        if anchor_dot: self.d.ellipse([a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8], fill=LIME + (255,))
        al = int(255 * ease((p - 0.35) / 0.65))
        if al > 0:
            self.d.rounded_rectangle([x, y, x + pw, y + ph], radius=9, fill=LIME + (al,))
            self.d.text((x + 18, y + 11), text, font=F_PILL, fill=(10, 14, 6, al))
    def composite(self, base):
        glow = self.fx.filter(ImageFilter.GaussianBlur(11)); out = base.convert('RGBA')
        out = Image.alpha_composite(out, glow); out = Image.alpha_composite(out, glow); out = Image.alpha_composite(out, self.fx); return out.convert('RGB')

def header(img, idx, t_in):
    d = ImageDraw.Draw(img); a = ease(t_in / 0.25)
    col = tuple(int(c * a + 0 * (1 - a)) for c in (150, 155, 165))
    text_spaced(d, (64, 270), CONFIG['series'], F_HDR, col, 3)
    for i in range(5):                                                       # progress dots
        w = 46 if i == idx else 12; x = W - 64 - (4 - i) * 30 - (34 if idx > i else 0) * 0
    x = W - 64; xs = []
    for i in range(4, -1, -1):
        w = 44 if i == idx else 12; x -= w; xs.append((i, x, w)); x -= 14
    for i, x0, w in xs: d.rounded_rectangle([x0, 276, x0 + w, 288], radius=6, fill=LIME if i == idx else (90, 96, 104))

def title_block(img, idx, title, sub, t_in):
    d = ImageDraw.Draw(img); e = ease(t_in / 0.35); dy = int((1 - e) * 28); a = int(255 * e)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.ellipse([64, 352 + dy, 64 + 78, 352 + 78 + dy], fill=LIME + (a,)); num = str(idx + 1); tw = dl.textlength(num, font=font('Black', 54))
    dl.text((64 + 39 - tw / 2, 363 + dy), num, font=font('Black', 54), fill=(10, 14, 6, a))
    dl.text((166, 316 + dy), title, font=F_TITLE, fill=WHITE + (a,)); dl.text((66, 470 + dy), sub, font=F_SUB, fill=WHITE + (int(a * .92),))
    img.paste(Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB'))

def cross(a, b, x): return Image.blend(a, b, clampi(x, 0, 1))

def zoom(img, z):
    if z <= 1.0001: return img
    w, h = int(W / z), int(H / z); x0, y0 = (W - w) // 2, int((H - h) * 0.55)
    return img.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)

def cp_frame(seq, cp, idx, t, hold_start=0.65, xfade=0.0):
    """t seconds since the start of this checkpoint segment."""
    key, f0 = cp['key'], cp['frame']; files = sorted(f for f in os.listdir(seq) if f.startswith(key + '_f') and f.endswith('.png'))
    lead = max(len(files) - 1, 1)
    if t < hold_start: k = int(clampi(t / hold_start * lead, 0, lead)); path = os.path.join(seq, files[k]); tt = 0.0
    else: path = os.path.join(seq, files[-1]); tt = t - hold_start
    base = top_shade(load_base(path, cp['xf']))
    proj = json.load(open(os.path.join(seq, files[-1].replace('.png', '.json')))); hud = Hud(proj, cp['xf'])
    if t >= hold_start:
        for n, a in enumerate(cp['ann']):
            p = clampi((tt - 0.25 - 0.35 * n) / 0.7, 0, 1)
            if a[0] == 'ring': hud.ring(a[1], a[2], p)
            elif a[0] == 'line': hud.line(a[1], a[2], p)
            elif a[0] == 'hline': hud.hline(a[1], p); hud.label(a[1], a[2], a[3], p, False)
            elif a[0] == 'label': hud.label(a[1], a[2], a[3], p)
    img = hud.composite(base); header(img, idx, t); title_block(img, idx, cp['title'], cp['sub'], t)
    return zoom(img, 1.0 + 0.045 * clampi(tt / 3.0, 0, 1))

def intro_frame(seq, t):
    base = top_shade(load_base(os.path.join(seq, 'intro.png'), (1, 0, 0)), 900, 190); d = ImageDraw.Draw(base)
    e = ease(t / 0.5); dy = int((1 - e) * 36); a = e
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); k1, t1, s1 = CONFIG['intro']
    text_spaced(dl, (64, 300 + dy), k1, F_HDR, LIME + (int(255 * a),), 5)
    dl.text((62, 350 + dy), t1, font=F_BIG, fill=WHITE + (int(255 * a),)); dl.text((64, 500 + dy), s1, font=F_SUB, fill=WHITE + (int(235 * ease((t - 0.2) / 0.5)),))
    base = Image.alpha_composite(base.convert('RGBA'), lay).convert('RGB'); return zoom(base, 1.0 + 0.03 * clampi(t / 2.4, 0, 1))

def outro_frame(seq, last_png, t):
    base = load_base(last_png, CONFIG['cps'][-1]['xf']); dark = Image.new('RGB', (W, H), (4, 6, 10)); base = Image.blend(base, dark, 0.45)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); e = ease(t / 0.4)
    text_spaced(d, (64, 300), CONFIG['outro_title'], F_HDR, LIME + (int(255 * e),), 5)
    for i, s in enumerate(CONFIG['outro_items']):
        ti = clampi((t - 0.35 - 0.38 * i) / 0.35, 0, 1); y = 372 + i * 92; a = int(255 * ease(ti + 0.001 if t > 0.3 else 0))
        d.rounded_rectangle([64, y + 8, 64 + 50, y + 58], radius=10, outline=(170, 175, 185, a), width=4)
        if ti > 0.6:                                                           # tick
            q = ease((ti - 0.6) / 0.4); d.line([(76, y + 34), (86, y + 46)], fill=LIME + (255,), width=8); d.line([(86, y + 46), (76 + 22 * q + 8, y + 46 - 30 * q)], fill=LIME + (255,), width=8)
        d.text((140, y + 6), f'{i + 1}  {s}', font=font('Bold', 44), fill=WHITE + (a,))
    return Image.alpha_composite(base.convert('RGBA'), lay).convert('RGB')

def main():
    seq, out = sys.argv[1], sys.argv[2]; cps = CONFIG['cps']
    if '--still' in sys.argv:
        k = sys.argv[sys.argv.index('--still') + 1]; idx = int(k[2:]) - 1; cp_frame(seq, cps[idx], idx, 2.6).save(out); return
    T_INTRO, T_CP, T_OUT, XF = 2.4, 3.65, 3.4, 0.16
    segs = [('intro', T_INTRO)] + [('cp', T_CP, i) for i in range(5)] + [('outro', T_OUT)]
    last_png = os.path.join(seq, sorted(f for f in os.listdir(seq) if f.startswith('cp5_f') and f.endswith('.png'))[-1])
    def frame_at(seg, t):
        if seg[0] == 'intro': return intro_frame(seq, t)
        if seg[0] == 'cp': return cp_frame(seq, cps[seg[2]], seg[2], t)
        return outro_frame(seq, last_png, t)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '17',
                           '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    n = 0
    for si, seg in enumerate(segs):
        dur = seg[1]; nf = int(round(dur * FPS))
        for i in range(nf):
            t = i / FPS; im = frame_at(seg, t)
            if si + 1 < len(segs) and t > dur - XF: im = cross(im, frame_at(segs[si + 1], 0.0), (t - (dur - XF)) / XF)
            ff.stdin.write(im.tobytes()); n += 1
    ff.stdin.close(); ff.wait(); print('frames', n, 'sec', n / FPS)

if __name__ == '__main__': main()

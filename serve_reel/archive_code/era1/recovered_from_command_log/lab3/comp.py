"""2D finishing of the orbit reel: stadium/body layer + glowing trails (additive with bloom), legend, vignette, fades.  usage: python3 -I comp.py LAYERDIR OUTDIR [frames...]"""
import numpy as np, cv2, sys, os, json
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True); plan = json.load(open(SP + '/lab3/plan.json'))['frames']; NT = len(plan)
only = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else range(NT)
W, H = 928, 1696; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); vig = 1 - 0.28 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2, 0, 1)
LEG = [('SERVE 1  BALL', (30, 220, 255)), ('SERVE 1  RACKET', (255, 217, 26)), ('SERVE 2  BALL', (20, 107, 255)), ('SERVE 2  RACKET', (204, 46, 255))]       # BGR
def legend(im, level, fade):
    rows = {1: 2, 2: 4, 3: 4}[level] if level else 0
    for i in range(rows):
        t, c = LEG[i]; y = H - 150 + i * 34; cv2.circle(im, (60, y - 7), 7, tuple(v / 255 * fade for v in c), -1, cv2.LINE_AA)
        cv2.putText(im, t, (80, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0.92 * fade,) * 3, 1, cv2.LINE_AA)
for n in only:
    fr = plan[n]; b = cv2.imread(f'{src}/b{n:04d}.png').astype(np.float32) / 255; t = cv2.imread(f'{src}/t{n:04d}.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    core = t[..., :3] * t[..., 3:4]; glow = core + 1.0 * cv2.GaussianBlur(core, (0, 0), 5) + 0.9 * cv2.GaussianBlur(core, (0, 0), 14) + 0.6 * cv2.GaussianBlur(core, (0, 0), 32)
    hot = np.clip(core * 1.0, 0, 1); hot = hot * 0.6 + 0.4 * hot.max(2, keepdims=True)                                              # whiter core
    out = 1 - (1 - b) * (1 - np.clip(glow, 0, 1)); out = np.maximum(out, hot * 0.0 + out)
    out = out * vig[..., None]
    if fr['part'] == 2 and fr['legend']: legend(out, fr['legend'], fr['fade'])
    f_in = min(1.0, n / 12.0); f_out = 1.0 if n < NT - 20 else max(0.0, (NT - 1 - n) / 20.0); out = out * min(f_in, f_out)
    cv2.imwrite(f'{dst}/o{n:04d}.png', (np.clip(out, 0, 1) * 255).astype(np.uint8))

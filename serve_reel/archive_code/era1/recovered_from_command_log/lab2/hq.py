"""Quality boost of the ORIGINAL (stabilised) frames: clean background plate (temporal median) super-resolved once with EDSR, per-frame LapSRN x2 for everything that moves,
soft static/moving blend, light denoise + detail/contrast enhancement.  Runs in mpenv (OpenCV 4.11 with dnn_superres)."""
import cv2, numpy as np, os, time
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
FR = np.load(SP + '/lab2/frames_ref.npy', mmap_mode='r'); N = 237
bg = cv2.imread(SP + '/lab2/bg_ref.png'); valid = (bg.sum(2) > 0).astype(np.float32); valid = cv2.erode(valid, np.ones((5, 5), np.uint8))
med = np.median(np.array(FR[::6]), axis=0).astype(np.uint8); bgf = np.where((bg.sum(2) > 0)[..., None], bg, med)
if not os.path.exists(SP + '/hq/bg_hq.png'):
    sr = cv2.dnn_superres.DnnSuperResImpl_create(); sr.readModel(SP + '/sr/EDSR_Tensorflow/models/EDSR_x2.pb'); sr.setModel('edsr', 2); t = time.time(); out = np.zeros((1696, 928, 3), np.uint8)
    for y in range(0, 848, 212):                                       # 4 strips with overlap -> bounded memory
        a, b = max(0, y - 8), min(848, y + 212 + 8); o = sr.upsample(np.ascontiguousarray(bgf[a:b])); out[2 * y:2 * (y + 212)] = o[2 * (y - a):2 * (y - a) + 424]
        print('edsr strip', y, round(time.time() - t), 's', flush=True)
    cv2.imwrite(SP + '/hq/bg_hq.png', out)
bg_hq = cv2.imread(SP + '/hq/bg_hq.png')
lap = cv2.dnn_superres.DnnSuperResImpl_create(); lap.readModel(SP + '/sr/TF-LapSRN/export/LapSRN_x2.pb'); lap.setModel('lapsrn', 2)
def enhance(im):
    f = im.astype(np.float32) / 255; lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB); Lc = lab[..., 0]
    bl = cv2.GaussianBlur(Lc, (0, 0), 1.7); Lc = Lc + 0.55 * (Lc - bl)                                              # unsharp (detail)
    bl2 = cv2.GaussianBlur(Lc, (0, 0), 25); Lc = Lc + 0.18 * (Lc - bl2)                                              # local contrast
    lab[..., 0] = np.clip(Lc, 0, 100); lab[..., 1:] *= 1.07; return np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), 0, 1)
for f in range(N):
    png = SP + '/hq/h%04d.png' % f
    if os.path.exists(png): continue
    im = np.array(FR[f]); dn = cv2.fastNlMeansDenoisingColored(im, None, 2.5, 2.5, 5, 15); up = lap.upsample(dn)
    d = cv2.GaussianBlur(cv2.absdiff(im, bg).max(2).astype(np.float32), (0, 0), 1.0); st = (d < 13).astype(np.float32); st = cv2.erode(st, np.ones((3, 3), np.uint8)) * valid
    w = cv2.GaussianBlur(st, (0, 0), 1.6); w = cv2.resize(w, (928, 1696), interpolation=cv2.INTER_LINEAR)[..., None]
    out = w * bg_hq.astype(np.float32) + (1 - w) * up.astype(np.float32); out = enhance(np.clip(out, 0, 255).astype(np.uint8))
    cv2.imwrite(png, (out * 255).astype(np.uint8))
    if f % 20 == 0: print('hq', f, flush=True)

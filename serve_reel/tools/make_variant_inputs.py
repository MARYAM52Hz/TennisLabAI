"""Make synthetic test inputs from a real clip + its CVAT labels (used by the verification tests, see docs/serve_reel/VERIFICATION.md).

  python3 tools/make_variant_inputs.py mirror  VIDEO LABELS.xml OUTDIR     # a left-hander: video and labels mirrored, left/right names swapped
  python3 tools/make_variant_inputs.py scale   VIDEO LABELS.xml OUTDIR 1.5 # another phone resolution: video and labels scaled
  python3 tools/make_variant_inputs.py rotate  VIDEO LABELS.xml OUTDIR     # landscape clip stored sideways (rotation metadata 90) with labels in the displayed (portrait) frame -> same labels, tests rotation handling
  python3 tools/make_variant_inputs.py canvas  VIDEO LABELS.xml OUTDIR CW CH S  # other aspect ratio / lens: the picture is scaled by S (S<1 = wider lens, S>1 = zoom/tele) and centred on a CW x CH canvas (padded with black or cropped); labels follow
Writes OUTDIR/video.mp4 and OUTDIR/labels.xml.
"""
import sys, os, re, subprocess, json
import xml.etree.ElementTree as ET

def probe(v):
    j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:stream_side_data=rotation', '-of', 'json', v]))['streams'][0]
    w, h = int(j['width']), int(j['height']); rot = 0
    for sd in j.get('side_data_list', []) or []: rot = int(sd.get('rotation', 0))
    return (h, w) if abs(rot) in (90, 270) else (w, h)

def swap_lr(n): return re.sub(r'left|right', lambda m: 'right' if m.group(0) == 'left' else 'left', n)

def fix_xml(src, dst, fx, fy, mirror, W, ox=0.0, oy=0.0):
    t = ET.parse(src); r = t.getroot()
    def tf(s):
        v = [float(a) for a in s.split(',')]; out = []
        for i in range(0, len(v), 2): out += [((W - v[i] * fx) if mirror else v[i] * fx) + ox, v[i + 1] * fy + oy]
        return ','.join('%.2f' % a for a in out)
    for e in r.iter():
        if e.tag == 'points' and e.get('points'):
            e.set('points', tf(e.get('points')))
            if mirror and e.get('label'): e.set('label', swap_lr(e.get('label')))
        if e.tag == 'ellipse':
            cx = float(e.get('cx')) * fx; e.set('cx', '%.2f' % (((W - cx) if mirror else cx) + ox)); e.set('cy', '%.2f' % (float(e.get('cy')) * fy + oy))
            e.set('rx', '%.2f' % (float(e.get('rx')) * fx)); e.set('ry', '%.2f' % (float(e.get('ry')) * fy))
            if mirror and e.get('rotation'): e.set('rotation', '%.2f' % ((-float(e.get('rotation'))) % 360.0))
    t.write(dst)

mode, video, xml, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
W, H = probe(video); dst = os.path.join(out, 'video.mp4')
if mode == 'mirror':
    subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', video, '-vf', 'hflip', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-vsync', 'passthrough', '-an', dst])
    fix_xml(xml, os.path.join(out, 'labels.xml'), 1, 1, True, W)
elif mode == 'scale':
    k = float(sys.argv[5]); w2, h2 = int(round(W * k / 2) * 2), int(round(H * k / 2) * 2)
    subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', video, '-vf', 'scale=%d:%d:flags=lanczos' % (w2, h2), '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-vsync', 'passthrough', '-an', dst])
    fix_xml(xml, os.path.join(out, 'labels.xml'), w2 / W, h2 / H, False, w2)
elif mode == 'rotate':
    # store the picture rotated clockwise by 90 degrees and tell players to rotate it back (display rotation 90 = counter-clockwise) with the rotation tag (like a phone held in landscape)
    tmp = os.path.join(out, 'sideways.mp4')
    subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', video, '-vf', 'transpose=1', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-vsync', 'passthrough', '-an', '-metadata:s:v:0', 'rotate=90', tmp])
    subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-display_rotation:v:0', '90', '-i', tmp, '-c', 'copy', dst])
    fix_xml(xml, os.path.join(out, 'labels.xml'), 1, 1, False, W); os.remove(tmp)
elif mode == 'canvas':
    CW, CH, S = int(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7])
    sw, sh = int(round(W * S / 2) * 2), int(round(H * S / 2) * 2)
    ox, oy = (CW - sw) / 2.0, (CH - sh) / 2.0
    # per axis: pad when the scaled picture is smaller than the canvas, crop when larger
    fx_ = 'pad=%d:ih:%d:0' % (CW, int(ox)) if ox >= 0 else 'crop=%d:ih:%d:0' % (CW, int(-ox))
    fy_ = 'pad=iw:%d:0:%d' % (CH, int(oy)) if oy >= 0 else 'crop=iw:%d:0:%d' % (CH, int(-oy))
    subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', video, '-vf', 'scale=%d:%d:flags=lanczos,%s,%s' % (sw, sh, fx_, fy_), '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-vsync', 'passthrough', '-an', dst])
    fix_xml(xml, os.path.join(out, 'labels.xml'), sw / W, sh / H, False, CW, int(ox), int(oy))
print('wrote', dst, probe(dst))

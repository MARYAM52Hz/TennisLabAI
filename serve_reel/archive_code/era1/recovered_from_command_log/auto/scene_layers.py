"""Layers for the real-player (white glass) version: (1) empty stadium plate, (2) racket+ball RGBA per frame. Same matched camera as the mannequin renders.
usage: python3 -I scene_layers.py OUTDIR FIRST LAST [--pct 100] [--samples 4]"""
import sys, os, time, numpy as np, bpy
from mathutils import Matrix, Vector
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/pipeline'); sys.path.insert(0, SP + '/auto')
import scene_skel as SS
from auto_motion import AutoMotion, DT
arg = SS.arg; WIMG, HIMG = 464, 848
out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
M = AutoMotion('B'); S = SS.build(M, SP + '/assets/stadium/Tennis Stadium Update.blend', 100, arg('--samples', 4, int)); sc = S['sc']
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2 * WIMG, 2 * HIMG, arg('--pct', 100, int)
S['cam'].data.lens = M.K[0, 0] * 36.0 / WIMG
for a, b, o in S['pbones']: o.hide_render = True
for o in S['pjoints'].values(): o.hide_render = True
keep = {S['racket'], S['ball']} | set(S['racket'].children)
S['racket'].hide_render = True; [c.hide_render for c in S['racket'].children]
for c in S['racket'].children: c.hide_render = True
S['ball'].hide_render = True
sc.render.filepath = out + '/plate.png'
if not os.path.exists(out + '/plate.png'): bpy.ops.render.render(write_still=True); print('PLATE done', flush=True)
# racket + ball only, transparent film
for o in bpy.data.objects:
    if o.type in ('MESH', 'EMPTY', 'CURVE') and o not in keep and o is not S['racket']: o.hide_render = True
for c in S['racket'].children: c.hide_render = False
S['racket'].hide_render = False; S['ball'].hide_render = False; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
for n in range(lo, hi + 1):
    png = f'{out}/rb{n:04d}.png'
    if os.path.exists(png): continue
    tau = float(n); b, RR, _ = M.racket(tau); S['racket'].location = Vector(b.tolist()); S['racket'].rotation_quaternion = Matrix(RR.tolist()).to_quaternion()
    bl = M.ball(tau); S['ball'].location = Vector(bl.tolist()); S['ball'].scale = (0.0335 * 1.4,) * 3; bpy.context.view_layer.update()
    t0 = time.time(); sc.render.filepath = png; bpy.ops.render.render(write_still=True); print('DONE', n, round(time.time() - t0, 1), flush=True)

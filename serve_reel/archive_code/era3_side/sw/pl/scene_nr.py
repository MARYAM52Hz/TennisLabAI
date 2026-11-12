"""Blender renderer for the orbit reel.  usage: python3 -I scene_orbit.py OUTDIR FIRST LAST [--samples 4] [--pct 100]
per frame -> bNNNN.png (stadium + skeleton + racket + ball) and tNNNN.png (emissive 3D trails on transparent film, composited with glow in 2D afterwards)"""
import sys, os, time, math, json, numpy as np, bpy
from mathutils import Matrix, Vector
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0, SP + '/pipeline'); sys.path.insert(0, SP + '/sw/pl'); sys.path.insert(0, SP + '/sw')
import scene_skel as SS
from motion_sw import Motion2
arg = SS.arg; out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
plan = json.load(open(SP + '/sw/pl/' + arg('--plan', 'plan_o.json')))['frames']
M = Motion2(); S = SS.build(M, SP + '/assets/stadium/Tennis Stadium Update.blend', 100, arg('--samples', 4, int)); sc = S['sc']
sc.eevee.use_shadows = False; sc.eevee.use_fast_gi = False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 928, 1696, arg('--pct', 100, int); cam = S['cam']; cam.data.sensor_fit = 'HORIZONTAL'
for a, b, o in S['pbones']: bpy.data.objects.remove(o)
EDG = [('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'), ('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist'), ('left_shoulder', 'top_spine'), ('right_shoulder', 'top_spine'), ('top_spine', 'bottom_spine'), ('top_spine', 'head'),
       ('left_hip', 'bottom_spine'), ('right_hip', 'bottom_spine'), ('left_hip', 'left_knee'), ('left_knee', 'left_ankle'), ('right_hip', 'right_knee'), ('right_knee', 'right_ankle'),
       ('left_ankle', 'left_heel'), ('left_ankle', 'left_foot_index'), ('left_heel', 'left_foot_index'), ('right_ankle', 'right_heel'), ('right_ankle', 'right_foot_index'), ('right_heel', 'right_foot_index')]
cyl = SS.cyl_mesh(); bone_mat = next(m for m in bpy.data.materials if m.name.startswith('bone')); hi_mat = SS.emissive('bone_hi', (1.0, 0.72, 0.10, 1.0), 2.6)
ARM = {('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist')}; ARMJ = {'right_shoulder', 'right_elbow', 'right_wrist'}
bones = []
for a, b in EDG:
    o = bpy.data.objects.new(f'b_{a}_{b}', cyl.copy()); o.data.materials.clear(); o.data.materials.append(hi_mat if (a, b) in ARM else bone_mat); sc.collection.objects.link(o); o.rotation_mode = 'QUATERNION'; bones.append((a, b, o))
skel_objs = [o for a, b, o in bones] + list(S['pjoints'].values()); rb_objs = [S['racket'], S['ball']] + list(S['racket'].children)
V = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
# trail material: emission = per-vertex colour attribute
tm = bpy.data.materials.new('trail'); tm.use_nodes = True; nt = tm.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Col'; at.attribute_type = 'GEOMETRY'; em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.1; so = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(at.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs['Emission'], so.inputs['Surface'])
dotm = SS.emissive('dot', (1, 1, 1, 1), 8.0)
def tube(name, P, inten, col, rad, ns=6):
    P = np.asarray(P, float); n = len(P); T = np.gradient(P, axis=0); T /= (np.linalg.norm(T, axis=1, keepdims=True) + 1e-9)
    ref = np.where(np.abs(T[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]])); N1 = np.cross(T, ref); N1 /= (np.linalg.norm(N1, axis=1, keepdims=True) + 1e-9); N2 = np.cross(T, N1)
    ang = np.linspace(0, 2 * np.pi, ns, endpoint=False); rr = rad * (0.55 + 0.45 * np.asarray(inten))[:, None, None]
    ring = P[:, None, :] + rr * (np.cos(ang)[None, :, None] * N1[:, None, :] + np.sin(ang)[None, :, None] * N2[:, None, :]); verts = ring.reshape(-1, 3)
    faces = [(i * ns + j, i * ns + (j + 1) % ns, (i + 1) * ns + (j + 1) % ns, (i + 1) * ns + j) for i in range(n - 1) for j in range(ns)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts.tolist(), [], faces); me.update(); ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    c = np.zeros((n, ns, 4), np.float32); c[..., :3] = (np.asarray(col)[None, None, :] * np.asarray(inten)[:, None, None]); c[..., 3] = 1.0; ca.data.foreach_set('color', c.reshape(-1))
    me.materials.append(tm); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o
dots = [bpy.data.objects.new('dot%d' % i, bpy.data.meshes.new('dm%d' % i)) for i in range(4)]
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8); sph = bpy.context.active_object; sph_me = sph.data; bpy.data.objects.remove(sph)
for d in dots: d.data = sph_me; sc.collection.objects.link(d); d.data.materials.clear(); d.data.materials.append(dotm)
keep = set(skel_objs) | set(rb_objs) | set(dots)
def pose(fr):
    tau = fr['tau']; cp = np.array(fr['cam']); tg = np.array(fr['target']); dist = float(np.linalg.norm(cp - tg)); k = float(np.clip(dist / 7.0, 1.0, 1.6)) if dist <= 8 else float(1.14 - 0.26 * np.clip((dist - 8) / 6.0, 0, 1))          # long shots: skeleton at a finer scale
    if fr['skel'] in ('live', 'liveA'):
        J = M.joints(tau)
        for a, b, o in bones:
            pa, pb = J[a], J[b]; d = pb - pa; L = float(np.linalg.norm(d)); o.location = V(pa); o.rotation_quaternion = V(d).to_track_quat('Z', 'Y'); r = 0.017 * k * (1.45 if (a, b) in ARM else 1.0); o.scale = (r, r, max(L, 1e-4))
        for n, o in S['pjoints'].items(): o.location = V(J[n]); r = (0.075 if n == 'head' else (0.047 if n in ARMJ else 0.031)) * (k if n != 'head' else 1.0 + 0.2 * (k - 1)); o.scale = (r, r, r)
        for o in skel_objs: o.hide_render = False
    else:
        for o in skel_objs: o.hide_render = True
    if fr['live_racket']:
        bR, RR, _ = M.racket(tau); S['racket'].location = V(bR); S['racket'].rotation_quaternion = Matrix(RR.tolist()).to_quaternion(); bl = M.ball(tau); S['ball'].location = V(bl); S['ball'].scale = (0.0335 * (1.5 if dist < 8 else float(1.5 - 0.2 * np.clip((dist - 8) / 6.0, 0, 1))),) * 3
        for o in rb_objs: o.hide_render = False
    else:
        for o in rb_objs: o.hide_render = True
    cam.location = V(cp); cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (V(tg) - V(cp)).to_track_quat('-Z', 'Y'); cam.data.lens = 36.0 / (2 * math.tan(math.radians(fr['fov']) / 2)); bpy.context.view_layer.update(); return dist
allobjs = [o for o in bpy.data.objects if o.type in ('MESH', 'EMPTY', 'CURVE')]
sc.render.film_transparent = False; sc.render.image_settings.color_mode = 'RGBA'
for n in range(lo, hi + 1):
    fr = plan[n]; pb, pt = f'{out}/b{n:04d}.png', f'{out}/t{n:04d}.png'
    if os.path.exists(pb) and os.path.exists(pt): continue
    t0 = time.time(); dist = pose(fr)
    for d in dots: d.hide_render = True
    # ---- base layer (no trails)
    sc.render.film_transparent = False
    for o in allobjs: o.hide_render = o.hide_render if o in keep else False
    for d in dots: d.hide_render = True
    tb = time.time()
    if not os.path.exists(pb): sc.render.filepath = pb; bpy.ops.render.render(write_still=True)
    tb = time.time() - tb
    # ---- trail layer
    objs = []; rad = max(0.012, 0.0042 * dist) if dist <= 8 else 0.0336 - 0.0090 * float(np.clip((dist - 8) / 4.0, 0, 1))         # thinner paths in long shots if dist <= 8 else 0.0336 + 0.0014 * (dist - 8)         # thinner paths in long shots
    for i, tr in enumerate(fr['trails']):
        o = tube(f'tr{i}', tr['pts'], tr['inten'], tr['col'], rad * (0.7 if tr['name'] == 'wrist' else 1.0)); objs.append(o)
        if tr.get('head') and tr['inten'][-1] > 0.05: d = dots[i]; d.location = V(tr['pts'][-1]); d.scale = (rad * (2.6 if dist <= 8 else 2.0),) * 3; d.hide_render = False
    state = {o: o.hide_render for o in allobjs}
    for o in allobjs:
        if o not in dots: o.hide_render = True
    for d in dots: d.hide_render = d.hide_render
    for o in objs: o.hide_render = False
    sc.render.film_transparent = True; sc.render.filepath = pt; bpy.ops.render.render(write_still=True)
    for o in objs: me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
    for o, h in state.items(): o.hide_render = h
    print('DONE', n, round(time.time() - t0, 1), 'base', round(tb, 1), flush=True)

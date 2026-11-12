"""Scene + procedural male mannequin (white, T-shirt, sport shorts, shoes) driven by a Motion object.
build_scene(M) -> S ; pose(S, M, tau) ; set_camera(S, ...) ; render_job(...)
World: metres, x along net, y toward far baseline (= hitting direction), z up."""
import math, numpy as np, bpy
from mathutils import Vector, Matrix, Quaternion
from scipy.interpolate import PchipInterpolator

ACCENT = (1.0, 0.80, 0.02, 1.0)            # tennis-ball yellow (HUD + neon share it)
def V(a): return Vector((float(a[0]), float(a[1]), float(a[2])))
def nrm(v): v = np.asarray(v, float); n = np.linalg.norm(v); return v / n if n > 1e-9 else v

# ------------------------------------------------------------------ materials
def mat(name, base=(1, 1, 1, 1), rough=.4, metal=0.0, emit=None, emit_strength=0.0, alpha=1.0, coat=0.0, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = base; b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit is not None: b.inputs['Emission Color'].default_value = emit; b.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
    for k, v in (('Coat Weight', coat), ('Specular IOR Level', spec)):
        try: b.inputs[k].default_value = v
        except KeyError: pass
    return m

# ------------------------------------------------------------------ meshes
def loft_mesh(name, prof, nseg=36, cap0=True, cap1=True, nring=22):
    """prof: list of (z, rx, ry). Smooth tube along +Z with spherical end caps of radius r0/r1 (cap bulge in world metres)."""
    z = np.array([p[0] for p in prof], float); rx = PchipInterpolator(z, [p[1] for p in prof]); ry = PchipInterpolator(z, [p[2] for p in prof])
    rings = []
    r0x, r0y = float(rx(z[0])), float(ry(z[0])); r1x, r1y = float(rx(z[-1])), float(ry(z[-1]))
    if cap0:
        for th in np.linspace(np.pi / 2 * 0.12, np.pi / 2, 5): rings.append((z[0] - r0x * math.cos(th), r0x * math.sin(th), r0y * math.sin(th)))
    for zz in np.linspace(z[0], z[-1], nring)[(1 if cap0 else 0):(-1 if cap1 else None)]: rings.append((zz, float(rx(zz)), float(ry(zz))))
    if cap1:
        for th in np.linspace(np.pi / 2, np.pi / 2 * 0.12, 5): rings.append((z[-1] + r1x * math.cos(th), r1x * math.sin(th), r1y * math.sin(th)))
    ang = np.linspace(0, 2 * np.pi, nseg, endpoint=False); verts = []
    for zz, a, b in rings: verts += [(a * math.cos(t), b * math.sin(t), zz) for t in ang]
    apex0 = len(verts); verts.append((0, 0, rings[0][0] - (r0x * 0.02 if cap0 else 0))); apex1 = len(verts); verts.append((0, 0, rings[-1][0] + (r1x * 0.02 if cap1 else 0)))
    faces = []
    for i in range(len(rings) - 1):
        for j in range(nseg): a_ = i * nseg + j; b_ = i * nseg + (j + 1) % nseg; faces.append((a_, b_, b_ + nseg, a_ + nseg))
    for j in range(nseg): faces.append((apex0, (j + 1) % nseg, j)); k = (len(rings) - 1) * nseg; faces.append((apex1, k + j, k + (j + 1) % nseg))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    return me

def ellipsoid_mesh(name):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=22, radius=1); o = bpy.context.active_object; me = o.data; me.name = name; bpy.data.objects.remove(o)
    for p in me.polygons: p.use_smooth = True
    return me

def torus_mesh(name, major, minor, nmaj=64, nmin=10):
    verts, faces = [], []
    for i in range(nmaj):
        a = 2 * math.pi * i / nmaj
        for j in range(nmin):
            b = 2 * math.pi * j / nmin; r = major + minor * math.cos(b); verts.append((r * math.cos(a), r * math.sin(a), minor * math.sin(b)))
    for i in range(nmaj):
        for j in range(nmin): a_ = i * nmin + j; b_ = i * nmin + (j + 1) % nmin; c_ = ((i + 1) % nmaj) * nmin + (j + 1) % nmin; d_ = ((i + 1) % nmaj) * nmin + j; faces.append((a_, b_, c_, d_))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    return me

def quat_from_axes(x, y, z):
    return Matrix(((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))).to_quaternion()
def frame(zdir, xhint):
    z = nrm(zdir); x = np.asarray(xhint, float) - z * np.dot(xhint, z); x = nrm(x) if np.linalg.norm(x) > 1e-6 else nrm(np.cross(z, [0, 1, 0])); y = np.cross(z, x); return x, y, z

# ------------------------------------------------------------------ scene
def build_scene(M, res=(1080, 1920)):
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; S = dict(sc=sc, M=M, parts={}); COLL = sc.collection
    sc.render.resolution_x, sc.render.resolution_y = res
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try: sc.render.engine = eng; break
        except TypeError: continue
    names = [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items]; sc.view_settings.view_transform = 'AgX' if 'AgX' in names else 'Filmic'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    try: sc.eevee.taa_render_samples = 16
    except Exception: pass
    k = M.H / 1.75
    S['mat'] = mt = dict(
        skin=mat('skin', (0.93, 0.93, 0.92, 1), .30, coat=0.5), shirt=mat('shirt', (0.95, 0.95, 0.94, 1), .66, spec=0.25), shorts=mat('shorts', (0.88, 0.88, 0.88, 1), .55, spec=0.3),
        shoe=mat('shoe', (0.96, 0.96, 0.96, 1), .42), sole=mat('sole', (0.50, 0.50, 0.52, 1), .8), seam=mat('seam', (0.30, 0.30, 0.32, 1), .8),
        neon=mat('neon', (0.1, 0.08, 0.0, 1), .5, emit=ACCENT, emit_strength=7.0), ball=mat('ball', (0.85, 0.95, 0.1, 1), .7, emit=(0.85, 0.95, 0.1, 1), emit_strength=3.2),
        floor=mat('floor', (0.006, 0.006, 0.008, 1), .09), court=mat('court', (0.012, 0.012, 0.015, 1), .10), line=mat('line', (0.9, 0.9, 0.9, 1), .5, emit=(1, 1, 1, 1), emit_strength=0.25),
        frame=mat('rframe', (0.02, 0.02, 0.02, 1), .3, .6), strings=mat('rstrings', (0.9, 0.85, 0.2, 1), .5, emit=ACCENT, emit_strength=0.9, alpha=0.30), net=mat('net', (0.01, 0.01, 0.012, 1), .8, alpha=0.6))
    def add(name, me, m, parent=None):
        o = bpy.data.objects.new(name, me.copy() if False else me); o.data.materials.clear(); o.data.materials.append(m); COLL.objects.link(o)
        o.rotation_mode = 'QUATERNION'
        if parent is not None: o.parent = parent
        return o
    # ---- court
    Lh, Wd, Ws, Sv = 23.77 / 2, 10.97 / 2, 8.23 / 2, 6.40
    cube = bpy.data.meshes.new('cube'); cube.from_pydata([(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5), (-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)], [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    def cb(name, m, loc, scl): o = add(name, cube, m); o.location = loc; o.scale = scl; return o
    cb('floor', mt['floor'], (0, 0, -0.011), (120, 120, 0.02)); cb('court', mt['court'], (0, 0, -0.0095), (2 * Wd + 6.4, 2 * Lh + 12.8, 0.02))
    def line(a, b, w=0.05):
        a, b = np.array([*a, 0.002]), np.array([*b, 0.002]); mid = (a + b) / 2; d = b - a; o = add('line', cube, mt['line']); o.location = V(mid)
        o.scale = (w, abs(d[1]) + w, 0.004) if abs(d[1]) > abs(d[0]) else (abs(d[0]) + w, w, 0.004)
    for a_, b_ in [((-Wd, -Lh), (Wd, -Lh)), ((-Wd, Lh), (Wd, Lh)), ((-Wd, -Lh), (-Wd, Lh)), ((Wd, -Lh), (Wd, Lh)), ((-Ws, -Lh), (-Ws, Lh)), ((Ws, -Lh), (Ws, Lh)),
                   ((-Ws, -Sv), (Ws, -Sv)), ((-Ws, Sv), (Ws, Sv)), ((0, -Sv), (0, Sv)), ((0, -Lh), (0, -Lh + .1)), ((0, Lh), (0, Lh - .1))]: line(a_, b_)
    cb('net', mt['net'], (0, 0, 0.457), (2 * Wd + 0.9, 0.02, 0.914)); cb('net_tape', mt['line'], (0, 0, 0.914), (2 * Wd + 0.9, 0.03, 0.06))
    # ---- mannequin parts (rest-pose meshes in metres, +Z along the bone)
    Lg = M.lengths; P = S['parts']
    def limb(key, mesh, mname, proximal, distal, L0):
        o = add(key, mesh, mt[mname]); P[key] = dict(o=o, a=proximal, b=distal, L0=L0, kind='limb'); return o
    ua, fa, th, sh = Lg['upper_arm'], Lg['forearm'], Lg['thigh'], Lg['shank']
    me_ua = loft_mesh('ua', [(0, .047 * k, .047 * k), (.35 * ua, .042 * k, .042 * k), (ua, .036 * k, .036 * k)]); me_fa = loft_mesh('fa', [(0, .036 * k, .036 * k), (.3 * fa, .034 * k, .031 * k), (fa, .025 * k, .025 * k)])
    me_th = loft_mesh('th', [(0, .090 * k, .090 * k), (.25 * th, .088 * k, .088 * k), (th, .058 * k, .058 * k)]); me_sh = loft_mesh('sh', [(0, .056 * k, .056 * k), (.28 * sh, .059 * k, .060 * k), (.72 * sh, .042 * k, .042 * k), (sh, .031 * k, .031 * k)])
    me_sl = loft_mesh('sleeve', [(0, .062 * k, .062 * k), (.28 * ua, .059 * k, .059 * k), (.54 * ua, .064 * k, .064 * k)], cap1=False)
    me_sg = loft_mesh('shortleg', [(0, .103 * k, .103 * k), (.30 * th, .104 * k, .104 * k), (.58 * th, .113 * k, .113 * k)], cap1=False)
    for side in ('left', 'right'):
        limb(f'ua_{side}', me_ua, 'skin', f'{side}_shoulder', f'{side}_elbow', ua); limb(f'fa_{side}', me_fa, 'skin', f'{side}_elbow', f'{side}_wrist', fa)
        limb(f'th_{side}', me_th, 'skin', f'{side}_hip', f'{side}_knee', th); limb(f'sh_{side}', me_sh, 'skin', f'{side}_knee', f'{side}_ankle', sh)
        s1 = limb(f'sleeve_{side}', me_sl, 'shirt', f'{side}_shoulder', f'{side}_elbow', ua); s2 = limb(f'shortleg_{side}', me_sg, 'shorts', f'{side}_hip', f'{side}_knee', th)
        for tag, parent, zz, rr in (('hem_s', s1, .54 * ua, .064 * k), ('hem_g', s2, .58 * th, .113 * k)):
            r_ = add(f'{tag}_{side}', torus_mesh(f'{tag}', rr, 0.0055 * k), mt['seam'], parent); r_.location = (0, 0, zz)
    # hands / thumbs
    me_hand = loft_mesh('hand', [(0, .038 * k, .017 * k), (.05, .046 * k, .016 * k), (.10, .040 * k, .012 * k)], nseg=28); me_thumb = loft_mesh('thumb', [(0, .013 * k, .013 * k), (.06, .010 * k, .010 * k)], nseg=16)
    for side in ('left', 'right'):
        o = add(f'hand_{side}', me_hand, mt['skin']); P[f'hand_{side}'] = dict(o=o, kind='hand', side=side)
        o = add(f'thumb_{side}', me_thumb, mt['skin']); P[f'thumb_{side}'] = dict(o=o, kind='thumb', side=side)
    # shoes
    me_el = ellipsoid_mesh('el')
    for side in ('left', 'right'):
        o = add(f'shoe_{side}', me_el, mt['shoe']); P[f'shoe_{side}'] = dict(o=o, kind='shoe', side=side)
        o = add(f'sole_{side}', me_el, mt['sole']); P[f'sole_{side}'] = dict(o=o, kind='sole', side=side)
    # torso: shorts shell + shirt shell + neck + collar + head
    me_pel = loft_mesh('pelvis', [(-0.10, .115 * k, .095 * k), (0.0, .172 * k, .120 * k), (0.12, .168 * k, .118 * k), (0.17, .150 * k, .108 * k)], nseg=44)
    o = add('pelvis', me_pel, mt['shorts']); P['pelvis'] = dict(o=o, kind='pelvis')
    wb = add('waistband', torus_mesh('wb', .150 * k, 0.006 * k, 64, 8), mt['seam'], o); wb.location = (0, 0, 0.165); wb.scale = (1, 0.72, 1)
    me_tor = loft_mesh('torso', [(-0.02, .185 * k, .132 * k), (0.12, .160 * k, .112 * k), (0.28, .180 * k, .122 * k), (0.40, .198 * k, .128 * k), (0.50, .175 * k, .110 * k), (0.56, .120 * k, .085 * k)], nseg=48)
    o = add('torso', me_tor, mt['shirt']); P['torso'] = dict(o=o, kind='torso')
    hm = add('hem', torus_mesh('hem', .185 * k, 0.006 * k, 64, 8), mt['seam'], o); hm.location = (0, 0, -0.02); hm.scale = (1, 0.72, 1)
    me_neck = loft_mesh('neck', [(0, .052 * k, .050 * k), (0.07, .046 * k, .046 * k)]); o = add('neck', me_neck, mt['skin']); P['neck'] = dict(o=o, kind='neck')
    cl = add('collar', torus_mesh('collar', .078 * k, 0.010 * k, 56, 8), mt['seam']); P['collar'] = dict(o=cl, kind='collar')
    hd = add('head', me_el, mt['skin']); P['head'] = dict(o=hd, kind='head')
    jaw = add('jaw', me_el, mt['skin'], hd); jaw.location = (0, 0.20, -0.62); jaw.scale = (0.78, 0.80, 0.66)
    nose = add('nose', me_el, mt['skin'], hd); nose.location = (0, 0.92, -0.10); nose.scale = (0.10, 0.22, 0.22)
    for sgn in (-1, 1): ear = add('ear', me_el, mt['skin'], hd); ear.location = (sgn * 0.97, -0.02, -0.05); ear.scale = (0.10, 0.22, 0.30)
    # ---- racket
    root = bpy.data.objects.new('racket', None); COLL.objects.link(root); root.rotation_mode = 'QUATERNION'; S['racket'] = root
    fc, (sx, sy) = M.face_center_local, M.face_semi; rl = M.rlen
    torus = torus_mesh('hoop', 1.0, 0.09, 64, 10)
    def rpart(name, me, m, loc, scl, rot=None, quat=None):
        o = add(name, me, m, root); o.location = loc; o.scale = scl
        if rot is not None: o.rotation_mode = 'XYZ'; o.rotation_euler = rot
        if quat is not None: o.rotation_quaternion = quat
        return o
    rpart('hoop', torus, mt['frame'], (0, fc[1], 0), (sx, sy, 0.12)); disc = loft_mesh('disc', [(-0.002, 1, 1), (0.002, 1, 1)], nseg=48, cap0=False, cap1=False, nring=2)
    rpart('strings', disc, mt['strings'], (0, fc[1], 0), (sx * .98, sy * .98, 1.0))
    cyl = loft_mesh('cyl1', [(0, 1, 1), (1, 1, 1)], nseg=14, cap0=False, cap1=False, nring=2)
    rpart('shaft', cyl, mt['frame'], (0, 0.0, 0), (0.014, 0.014, 0.40), rot=(-math.pi / 2, 0, 0)); rpart('handle', cyl, mt['frame'], (0, 0.0, 0), (0.021, 0.021, 0.20), rot=(-math.pi / 2, 0, 0))
    for nm, xx in (('throat_l', -.045), ('throat_r', .045)):
        y0, y1 = 0.31, fc[1] - sy * 0.92; a_, b_ = Vector((xx, y0, 0)), Vector((xx * 2.2, y1, 0)); d = b_ - a_
        rpart(nm, cyl, mt['frame'], (a_ + b_) / 2 - d / 2 * 0, (0.008, 0.008, d.length), quat=d.to_track_quat('Z', 'Y')); S['racket_throat'] = True
    # ---- ball + trails
    ball = add('ball', me_el, mt['ball']); ball.scale = (0.0335 * 1.9,) * 3; S['ball'] = ball
    def trail(name, m, width, npts=72):
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY'); sp.points.add(npts - 1)
        cu.bevel_depth = width; cu.bevel_resolution = 3; cu.use_fill_caps = True; cu.materials.append(m); o = bpy.data.objects.new(name, cu); COLL.objects.link(o); return o
    S['trail_racket'] = trail('trail_racket', mt['neon'], 0.012); S['trail_ball'] = trail('trail_ball', mt['neon'], 0.007)
    # ---- world + lights + camera
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.004, 0.005, 0.008, 1); bg.inputs[1].default_value = 1.0
    G = np.array([0.81, -12.2, 1.0])
    def light(name, kind, loc, energy, color=(1, 1, 1), size=1.0, spot=None):
        l = bpy.data.lights.new(name, kind); l.energy = energy; l.color = color
        if kind == 'AREA': l.size = size
        if kind == 'SPOT': l.spot_size = math.radians(spot or 50); l.spot_blend = 0.9; l.shadow_soft_size = 0.4
        o = bpy.data.objects.new(name, l); o.location = loc; COLL.objects.link(o); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(G) - Vector(loc)).to_track_quat('-Z', 'Y')
        try: o.visible_glossy = False
        except Exception: pass
        return o
    light('key', 'SPOT', (G[0] - 0.5, G[1] - 1.5, 8.5), 2300, spot=30); light('rim_l', 'AREA', (G[0] - 4.5, G[1] + 3.5, 3.2), 1800, (0.85, 0.95, 1.0), 3); light('rim_r', 'AREA', (G[0] + 4.5, G[1] + 3.5, 3.2), 1800, (1.0, 0.95, 0.85), 3)
    light('fill', 'AREA', (G[0] + 1.0, G[1] - 4.0, 2.2), 250, (1, 1, 1), 4)
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.clip_start = .05; cd.clip_end = 400
    co = bpy.data.objects.new('cam', cd); COLL.objects.link(co); co.rotation_mode = 'QUATERNION'; sc.camera = co; S['cam'] = co
    hv = M.joint('right_hip', 66.0) - M.joint('left_hip', 66.0); hv[2] = 0; S['right0'] = nrm(hv); S['fwd0'] = np.cross([0, 0, 1], S['right0'])
    return S

# ------------------------------------------------------------------ posing
def _setq(o, loc, q, scl=None):
    o.location = V(loc); o.rotation_quaternion = q
    if scl is not None: o.scale = scl

def pose(S, tau, trail_win=(6.0, 60.0)):
    M = S['M']; P = S['parts']; J = M.joints(float(tau)); k = M.H / 1.75
    for key, p in P.items():
        kd = p['kind']
        if kd == 'limb':
            a, b = J[p['a']], J[p['b']]; d = b - a; L = np.linalg.norm(d); _setq(p['o'], a, V(d).to_track_quat('Z', 'Y'), (1, 1, L / p['L0']))
    # hands / thumbs
    for side in ('left', 'right'):
        w, ix, tb = J[f'{side}_wrist'], J[f'{side}_index'], J[f'{side}_thumb']
        zdir = nrm(ix - w); nn = np.cross(zdir, tb - w); xw = nrm(np.cross(nn, zdir)) if np.linalg.norm(nn) > 1e-6 else nrm(np.cross(zdir, [0, 1, 0])); yw = np.cross(zdir, xw)
        L = max(np.linalg.norm(ix - w), 0.07) + 0.02; _setq(P[f'hand_{side}']['o'], w, quat_from_axes(xw, yw, zdir), (1, 1, L / 0.10))
        d = tb - w; Lt = np.linalg.norm(d); _setq(P[f'thumb_{side}']['o'], w, V(d).to_track_quat('Z', 'Y'), (1, 1, max(Lt, 0.03) / 0.06))
        # shoes
        he, to, an = J[f'{side}_heel'], J[f'{side}_foot_index'], J[f'{side}_ankle']; fwd = to - he; fwd[2] = 0; Lf = np.linalg.norm(fwd) + 0.075; fwdn = nrm(fwd) if np.linalg.norm(fwd) > 1e-6 else S['fwd0']
        up = np.array([0, 0, 1.0]); xs = nrm(np.cross(fwdn, up)); ctr = (he + to) / 2 + np.array([0, 0, 0.040]); q = quat_from_axes(xs, fwdn, np.cross(xs, fwdn))
        _setq(P[f'shoe_{side}']['o'], ctr, q, (0.050 * k, Lf / 2, 0.048 * k)); _setq(P[f'sole_{side}']['o'], ctr - np.array([0, 0, 0.034]), q, (0.052 * k, Lf / 2 * 0.99, 0.013 * k))
    # torso frames
    shL, shR, hL, hR = J['left_shoulder'], J['right_shoulder'], J['left_hip'], J['right_hip']; mid_sh = (shL + shR) / 2; mid_h = (hL + hR) / 2
    up_t = nrm(mid_sh - mid_h); xc = nrm((shR - shL) - up_t * np.dot(shR - shL, up_t)); yc = np.cross(up_t, xc)
    up_p = nrm(J['bottom_spine'] - mid_h + up_t * 0.02); xp = nrm((hR - hL) - up_p * np.dot(hR - hL, up_p)); yp = np.cross(up_p, xp)
    _setq(P['pelvis']['o'], mid_h, quat_from_axes(xp, yp, up_p)); tl = np.linalg.norm(mid_sh - mid_h)
    _setq(P['torso']['o'], mid_h + up_t * 0.04, quat_from_axes(xc, yc, up_t), (1, 1, max(tl - 0.04, 0.2) / 0.56 * 0.0 + 1.0)) if False else _setq(P['torso']['o'], mid_h + up_t * 0.03, quat_from_axes(xc, yc, up_t), (1, 1, (tl - 0.01) / 0.54))
    ts = J['top_spine']; nd = nrm(ts - J['bottom_spine']); nd = nrm(nd * 0.6 + np.array([0, 0, 1.0]) * 0.4)
    _setq(P['neck']['o'], ts - nd * 0.01, V(nd).to_track_quat('Z', 'Y'), (1, 1, 1.0)); _setq(P['collar']['o'], ts - nd * 0.005 - up_t * 0.01, quat_from_axes(xc, yc, up_t), (1, 0.82, 1))
    # head: follows the ball (clamped) like a player tracking the toss
    hc = ts + nd * 0.13; ballp = M.ball(float(tau)); look = nrm(ballp - hc); fc_ = yc
    yaw = math.atan2(np.dot(look, xc), np.dot(look, fc_)); pitch = math.asin(np.clip(np.dot(look, up_t), -1, 1)); yaw = np.clip(yaw, -0.9, 0.9) * 0.75; pitch = np.clip(pitch, -0.7, 1.1) * 0.8
    fh = nrm(math.cos(pitch) * (math.cos(yaw) * fc_ + math.sin(yaw) * xc) + math.sin(pitch) * up_t); xh = nrm(np.cross(fh, up_t)); zh = np.cross(xh, fh); xh = xh
    _setq(P['head']['o'], hc + zh * 0.012, quat_from_axes(xh, fh, zh), (0.080 * k, 0.098 * k, 0.116 * k))
    # racket + ball + trails
    b, R, Pr = M.racket(float(tau)); S['racket'].location = V(b); S['racket'].rotation_quaternion = Matrix(R.tolist()).to_quaternion()
    S['ball'].location = V(ballp)
    sbc = M.rn.index('string_bed_center')
    def set_trail(o, f, t0, t1, win, show_from):
        sp = o.data.splines[0]; n = len(sp.points)
        if tau < show_from or tau > t1 + 40: o.hide_render = True; return
        o.hide_render = False; ts_ = np.linspace(max(tau - win, t0), min(tau, t1), n)
        pts = np.stack([f(t) for t in ts_]);
        for p_, q_ in zip(sp.points, pts): p_.co = (q_[0], q_[1], q_[2], 1.0)
    set_trail(S['trail_racket'], lambda t: M.racket(float(t))[2][sbc], 62.0, 84.0, trail_win[0], 62.0 + 0.2)
    set_trail(S['trail_ball'], lambda t: M.ball(float(t)), 57.5, 75.0, trail_win[1] * 0.5, 57.5 + 0.2)
    bpy.context.view_layer.update()

def set_camera(S, tau, az, el, dist, lens, tgt_off, focus=None):
    M = S['M']; mid = (M.joint('left_hip', tau) + M.joint('right_hip', tau)) / 2 if focus is None else np.asarray(focus)
    tgt = Vector(mid + np.asarray(tgt_off)); a = math.radians(az); e = math.radians(el); dirv = math.cos(a) * S['fwd0'] + math.sin(a) * S['right0']
    pos = tgt + Vector((dirv[0] * math.cos(e), dirv[1] * math.cos(e), math.sin(e))) * dist; co = S['cam']; co.location = pos; co.rotation_quaternion = (tgt - pos).to_track_quat('-Z', 'Y'); co.data.lens = lens
    bpy.context.view_layer.update()

def project(S, pts):
    from bpy_extras.object_utils import world_to_camera_view
    out = {}
    for n, p in pts.items(): v = world_to_camera_view(S['sc'], S['cam'], V(p)); out[n] = [v.x, 1 - v.y, v.z]
    return out

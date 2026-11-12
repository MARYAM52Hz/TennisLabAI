"""Raw-skeleton reconstruction inside the Tennis Stadium model (no mannequin, no text).
Matched camera (K,R,C from the court calibration) -> the skeleton lands exactly where the CVAT labels are.
usage: python3 -I scene_skel.py OUTDIR FIRST LAST [--pct 100] [--samples 8] [--stadium PATH]
World: metres, x along the net, y toward far baseline, z up, origin = net centre on the ground (the stadium is rotated +90 deg about Z to match)."""
import sys, os, json, math, time, numpy as np, bpy
from mathutils import Vector, Matrix
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, SP + '/pipeline')
from motion import Motion

ORANGE = (1.0, 0.36, 0.02, 1.0); ORANGE_J = (1.0, 0.62, 0.20, 1.0); CYAN = (0.05, 0.80, 1.0, 1.0); YELLOW = (1.0, 0.86, 0.05, 1.0); BALL = (0.80, 1.0, 0.05, 1.0)
V = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
EDGES = json.load(open(SP + '/data/skeleton_edges.json'))

def arg(name, default, cast=str):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default

def emissive(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0, 0, 0, 1); b.inputs['Roughness'].default_value = 0.6
    b.inputs['Emission Color'].default_value = color; b.inputs['Emission Strength'].default_value = strength
    return m

def cyl_mesh(n=14):
    verts = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), z) for z in (0.0, 1.0) for i in range(n)]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me = bpy.data.meshes.new('cyl'); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    return me

def sph_mesh():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1); o = bpy.context.active_object; me = o.data; me.name = 'sph'; bpy.data.objects.remove(o)
    for p in me.polygons: p.use_smooth = True
    return me

def build(M, stadium, pct=100, samples=8):
    bpy.ops.wm.open_mainfile(filepath=stadium); sc = bpy.context.scene; COLL = sc.collection
    # stadium: metric, length along X -> rotate +90 deg about Z so length is along my +Y
    root = bpy.data.objects.new('stadium_root', None); COLL.objects.link(root)
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o); continue
        if o is not root and o.parent is None: o.parent = root
    root.rotation_euler = (0, 0, math.pi / 2)
    for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try: sc.render.engine = eng; break
        except TypeError: continue
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, pct
    try: sc.eevee.taa_render_samples = samples
    except Exception: pass
    S = dict(sc=sc, M=M)
    mt = dict(bone=emissive('bone', ORANGE, 6.0), joint=emissive('joint', ORANGE_J, 8.0), rbone=emissive('rbone', CYAN, 6.0), rface=emissive('rface', YELLOW, 7.0), ball=emissive('ball', BALL, 6.0), trail=emissive('trail', YELLOW, 4.0))
    cy, sp = cyl_mesh(), sph_mesh()
    def add(name, me, m):
        me2 = me.copy(); me2.materials.clear(); me2.materials.append(m); o = bpy.data.objects.new(name, me2); COLL.objects.link(o); o.rotation_mode = 'QUATERNION'; return o
    S['pbones'] = [(a, b, add(f'bone_{a}_{b}', cy, mt['bone'])) for a, b in EDGES['P_player_skeleton']]
    S['pjoints'] = {n: add('joint_' + n, sp, mt['joint']) for n in M.names}
    S['rbones'] = [(a, b, add(f'rbone_{a}_{b}', cy, mt['rbone'])) for a, b in EDGES['R_racket_skeleton']]
    S['rjoints'] = {n: add('rjoint_' + n, sp, mt['rbone']) for n in M.rn}
    S['ball'] = add('ball', sp, mt['ball'])
    def curve(name, npts, mat, width, cyclic=False):
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; s = cu.splines.new('POLY'); s.points.add(npts - 1); s.use_cyclic_u = cyclic
        cu.bevel_depth = width; cu.bevel_resolution = 2; cu.use_fill_caps = True; cu.materials.append(mat); o = bpy.data.objects.new(name, cu); COLL.objects.link(o); return o
    S['face'] = curve('racket_face', 48, mt['rface'], 0.008, True); S['trail'] = curve('ball_trail', 40, mt['trail'], 0.006)
    # matched camera
    K, R, C = M.K, M.R_cam, M.C_cam
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0; cd.lens = K[0, 0] * 36.0 / 1080.0; cd.clip_start = 0.05; cd.clip_end = 600
    co = bpy.data.objects.new('cam', cd); COLL.objects.link(co); co.matrix_world = Matrix.Translation(V(C)) @ Matrix((R.T @ np.diag([1, -1, -1])).tolist()).to_4x4(); sc.camera = co; S['cam'] = co
    return S

def pose(S, tau, rj=0.014, jr=0.026):
    M = S['M']; J = M.straighten_left(M.joints(float(tau)), float(tau))
    for a, b, o in S['pbones']:
        pa, pb = J[a], J[b]; d = pb - pa; L = float(np.linalg.norm(d)); o.location = V(pa); o.rotation_quaternion = V(d).to_track_quat('Z', 'Y'); o.scale = (rj, rj, max(L, 1e-4))
    for n, o in S['pjoints'].items(): o.location = V(J[n]); o.scale = (jr, jr, jr)
    bR, RR, Pr = M.racket(float(tau)); P = {n: Pr[i] for i, n in enumerate(M.rn)}
    for a, b, o in S['rbones']:
        pa, pb = P[a], P[b]; d = pb - pa; L = float(np.linalg.norm(d)); o.location = V(pa); o.rotation_quaternion = V(d).to_track_quat('Z', 'Y'); o.scale = (0.010, 0.010, max(L, 1e-4))
    for n, o in S['rjoints'].items(): o.location = V(P[n]); o.scale = (0.016,) * 3
    fc, (sx, sy) = M.face_center_local, M.face_semi; th = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    loc = np.stack([fc[0] + sx * np.cos(th), fc[1] + sy * np.sin(th), np.full_like(th, fc[2] if len(fc) > 2 else 0.0)], -1); W = bR + loc @ RR.T
    for p_, q_ in zip(S['face'].data.splines[0].points, W): p_.co = (q_[0], q_[1], q_[2], 1.0)
    bp = M.ball(float(tau)); S['ball'].location = V(bp); S['ball'].scale = (0.0335 * 1.35,) * 3
    ts = np.linspace(max(tau - 9.0, 0.0), tau, 40); tr = np.stack([M.ball(float(t)) for t in ts]); vis = tau > 57.0
    S['trail'].hide_render = not vis
    for p_, q_ in zip(S['trail'].data.splines[0].points, tr): p_.co = (q_[0], q_[1], q_[2], 1.0)
    bpy.context.view_layer.update()

if __name__ == '__main__':
    out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
    M = Motion(SP + '/data', suffix='_ext3'); S = build(M, arg('--stadium', SP + '/assets/stadium/Tennis Stadium Update.blend'), arg('--pct', 100, int), arg('--samples', 8, int)); sc = S['sc']
    for n in range(lo, hi + 1):
        png = f'{out}/f{n:04d}.png'
        if os.path.exists(png): continue
        t0 = time.time(); pose(S, float(n)); sc.render.filepath = png; bpy.ops.render.render(write_still=True); print('DONE', n, round(time.time() - t0, 1), flush=True)

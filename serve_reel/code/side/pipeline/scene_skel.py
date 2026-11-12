"""Raw-skeleton reconstruction inside the Tennis Stadium model (no mannequin, no text).
Matched camera (K,R,C from the court calibration) -> the skeleton lands exactly where the CVAT labels are.
usage: python3 -I scene_skel.py OUTDIR FIRST LAST [--pct 100] [--samples 8] [--stadium PATH]
World: metres, x along the net, y toward far baseline, z up, origin = net centre on the ground (the stadium is rotated +90 deg about Z to match)."""
import sys, os, json, math, time, numpy as np, bpy
from mathutils import Vector, Matrix
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, SP + '/pipeline')
from motion import Motion

ORANGE = (1.0, 0.30, 0.01, 1.0); ORANGE_J = (1.0, 0.55, 0.12, 1.0); CYAN = (0.05, 0.80, 1.0, 1.0); YELLOW = (1.0, 0.86, 0.05, 1.0); BALL = (0.80, 1.0, 0.05, 1.0)
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
    # lighting: sky-coloured world + soft area lights over the court (the original roof shadows the whole bowl)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.62, 0.70, 0.85, 1); bg.inputs[1].default_value = arg('--world', 0.25, float)
    for i, (x, y) in enumerate(((0, -9), (0, 9))):
        l = bpy.data.lights.new(f'court{i}', 'AREA'); l.energy = arg('--lamp', 900, float); l.size = 14; o = bpy.data.objects.new(f'court{i}', l); COLL.objects.link(o); o.location = (x, y, 14); o.rotation_euler = (0, 0, 0)
    try: sc.view_settings.view_transform = arg('--view', 'Standard')
    except Exception: pass
    S = dict(sc=sc, M=M)
    mt = dict(bone=emissive('bone', ORANGE, 1.6), joint=emissive('joint', ORANGE_J, 2.2), rbone=emissive('rbone', CYAN, 1.6), rface=emissive('rface', YELLOW, 2.0), ball=emissive('ball', BALL, 1.6), trail=emissive('trail', YELLOW, 1.2))
    cy, sp = cyl_mesh(), sph_mesh()
    def add(name, me, m):
        me2 = me.copy(); me2.materials.clear(); me2.materials.append(m); o = bpy.data.objects.new(name, me2); COLL.objects.link(o); o.rotation_mode = 'QUATERNION'; return o
    S['pbones'] = [(a, b, add(f'bone_{a}_{b}', cy, mt['bone'])) for a, b in EDGES['P_player_skeleton']]
    S['pjoints'] = {n: add('joint_' + n, sp, mt['joint']) for n in M.names}
    def pmat(name, base, rough=0.4, metal=0.0, alpha=1.0, emit=None, es=0.0):
        m = bpy.data.materials.new(name); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = base; bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
        if emit is not None: bs.inputs['Emission Color'].default_value = emit; bs.inputs['Emission Strength'].default_value = es
        if alpha < 1.0:
            bs.inputs['Alpha'].default_value = alpha
            try: m.surface_render_method = 'BLENDED'
            except Exception: m.blend_method = 'BLEND'
        return m
    def append_objects(path, names):
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            order = [n for n in src.objects if n in names]; dst.objects = list(order)
        out = {}
        for n, o in zip(order, dst.objects):
            if o is not None: COLL.objects.link(o); out[n] = o
        return out
    assets = SP + '/assets'
    # racket model (CC0, JamieGrant): butt end at origin, long axis +Y, string-bed normal +Z, scaled to the labelled racket length
    R_ = append_objects(assets + '/racket/Tennis_Racquet.blend', {'Circle', 'Cylinder.001', 'Plane', 'Plane.005'})
    root_r = bpy.data.objects.new('racket', None); COLL.objects.link(root_r); root_r.rotation_mode = 'QUATERNION'; S['racket'] = root_r
    sc_r = M.rlen / 20.67; butt_model = Matrix.Translation(Vector((0.0, -15.46, 0.73)))
    rm = {'Circle': pmat('rframe', (0.015, 0.015, 0.02, 1), 0.3, 0.2), 'Cylinder.001': pmat('rstrings', (1.0, 1.0, 0.95, 1), 0.5, 0.0, 0.85), 'Plane': pmat('rgrip', (0.75, 0.05, 0.04, 1), 0.7), 'Plane.005': pmat('rgrip2', (0.75, 0.05, 0.04, 1), 0.7)}
    for k, o in R_.items():
        o.parent = None; mw = o.matrix_basis.copy(); o.parent = root_r; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = Matrix.Scale(sc_r, 4) @ butt_model.inverted() @ mw
        o.data.materials.clear(); o.data.materials.append(rm[k])
        for md in o.modifiers:
            if md.type == 'SUBSURF': md.render_levels = 1; md.levels = 1
        for p_ in o.data.polygons: p_.use_smooth = True
    # ball model (CC0, Jeremiah R): keep mesh + seam/cover materials, drop the hair particles, normalise to unit radius
    B_ = append_objects(assets + '/ball/tennnisball1.blend', {'Sphere.001'}); ball = B_['Sphere.001']
    for md in list(ball.modifiers):
        if md.type == 'PARTICLE_SYSTEM': ball.modifiers.remove(md)
    ball.parent = None; ball.rotation_mode = 'QUATERNION'; ball.location = (0, 0, 0)
    me = ball.data; c = np.array([v.co[:] for v in me.vertices]); ctr = (c.min(0) + c.max(0)) / 2; rad = float(np.linalg.norm(c - ctr, axis=1).mean())
    for v in me.vertices: v.co = (np.array(v.co[:]) - ctr) / rad
    for md in ball.modifiers:
        if md.type == 'SUBSURF': md.render_levels = 2; md.levels = 1
    for slot in ball.material_slots:
        m = slot.material
        if m and m.use_nodes:
            bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if bs is not None:
                try: bs.inputs['Emission Color'].default_value = (0.75, 0.9, 0.1, 1); bs.inputs['Emission Strength'].default_value = 0.5
                except KeyError: pass
    S['ball'] = ball
    # matched camera
    K, R, C = M.K, M.R_cam, M.C_cam
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0; cd.lens = K[0, 0] * 36.0 / 1080.0; cd.clip_start = 0.05; cd.clip_end = 600
    co = bpy.data.objects.new('cam', cd); COLL.objects.link(co); co.matrix_world = Matrix.Translation(V(C)) @ Matrix((R.T @ np.diag([1, -1, -1])).tolist()).to_4x4(); sc.camera = co; S['cam'] = co
    return S

def pose(S, tau, rj=0.017, jr=0.031):
    M = S['M']; J = M.straighten_left(M.joints(float(tau)), float(tau))
    for a, b, o in S['pbones']:
        pa, pb = J[a], J[b]; d = pb - pa; L = float(np.linalg.norm(d)); o.location = V(pa); o.rotation_quaternion = V(d).to_track_quat('Z', 'Y'); o.scale = (rj, rj, max(L, 1e-4))
    for n, o in S['pjoints'].items(): o.location = V(J[n]); o.scale = (jr, jr, jr)
    bR, RR, Pr = M.racket(float(tau)); S['racket'].location = V(bR); S['racket'].rotation_quaternion = Matrix(RR.tolist()).to_quaternion()
    S['ball'].location = V(M.ball(float(tau))); S['ball'].scale = (0.0335 * 1.4,) * 3
    bpy.context.view_layer.update()

if __name__ == '__main__':
    out = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3]); os.makedirs(out, exist_ok=True)
    M = Motion(SP + '/data', suffix='_ext3'); S = build(M, arg('--stadium', SP + '/assets/stadium/Tennis Stadium Update.blend'), arg('--pct', 100, int), arg('--samples', 8, int)); sc = S['sc']
    for n in range(lo, hi + 1):
        png = f'{out}/f{n:04d}.png'
        if os.path.exists(png): continue
        t0 = time.time(); pose(S, float(n)); sc.render.filepath = png; bpy.ops.render.render(write_still=True); print('DONE', n, round(time.time() - t0, 1), flush=True)

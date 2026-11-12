"""MakeHuman/MPFB2 (CC0) athletic male -> weighted mesh + the same 28-bone armature layout as the old mannequin rig (so the exact-fit retargeter works unchanged).
usage: python3 -I build_athlete.py OUT.blend OUT_rig_info.json [--muscle 0.5] [--weight 0.3] [--height 1.76]"""
import sys, json, math, numpy as np, bpy
from mathutils import Vector, Matrix
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/athlete')
import mhmodel as MH
def arg(n, d, c=float): return c(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
OUT, INFO = sys.argv[1], sys.argv[2]
V0, P, F = MH.athlete(muscle=arg('--muscle', 0.5), weight=arg('--weight', 0.3), height=arg('--height_slider', 0.55))
W = MH.to_world(P); NB = 13380
vg = {k: [(int(i), float(w)) for i, w in v] for k, v in json.load(open(MH.MP + '/mesh_metadata/basemesh_vertex_groups.json')).items()}
W[:, 2] -= W[:NB, 2].min(); sc = arg('--height', 1.76) / W[:NB, 2].max(); W *= sc; print('scale', round(sc, 3), 'height', W[:NB, 2].max())
J = lambda n: W[[i for i, _ in vg[n]]].mean(0)
Jm = lambda names: np.mean([J(n) for n in names], 0)
def side(s):                                                             # s = 'l' / 'r'
    j = lambda n: J(f'joint-{s}-{n}'); ytop = float(np.mean([J('joint-spine-1')[0], J('joint-neck')[0]]))
    return j
# foot extents from the mesh (heel point)
def foot_pts(s):
    sg = 1 if s == 'l' else -1; sel = np.where((W[:NB, 1] * sg > 0.03) & (W[:NB, 2] < 0.14) & (W[:NB, 0] > -0.2))[0]; return W[sel]
pel = J('joint-pelvis'); pel[1] = 0.0; s4, s3, s2 = (J(f'joint-spine-{k}') for k in (4, 3, 2)); neck = J('joint-neck'); hd = J('joint-head'); hd2 = J('joint-head-2')
shz = float((J('joint-l-shoulder')[2] + J('joint-r-shoulder')[2]) / 2); top = np.array([(J('joint-spine-1')[0] + neck[0]) / 2, 0.0, shz + 0.01])
for a in (s4, s3, s2, neck, hd, hd2): a[1] = 0.0
R = {}                                                                    # name -> (head, tail, parent, conn)
R['Bone'] = (pel, s4, None, False); R['Bone.001'] = (s4, s3, 'Bone', True); R['Bone.002'] = (s3, s2, 'Bone.001', True); R['Bone.003'] = (s2, top, 'Bone.002', True)
R['Bone.026'] = (top, hd, 'Bone.003', True); R['Bone.027'] = (hd, hd2, 'Bone.026', True)
for s, S in (('l', 'L'), ('r', 'R')):
    sh, el, wr = J(f'joint-{s}-shoulder'), J(f'joint-{s}-elbow'), J(f'joint-{s}-hand'); mcp = Jm([f'joint-{s}-finger-3-1']); tip = Jm([f'joint-{s}-finger-3-4'])
    hip, kn, an = J(f'joint-{s}-upper-leg'), J(f'joint-{s}-knee'), J(f'joint-{s}-ankle'); fp = foot_pts(s); heel = np.array([fp[:, 0].min() + 0.012, an[1], max(0.022, fp[:, 2].min() + 0.025)])
    ball = Jm([f'joint-{s}-toe-{k}-1' for k in (1, 2, 3, 4, 5)]); ball[2] = max(ball[2], 0.02); toe = Jm([f'joint-{s}-toe-{k}-4' for k in (1, 2, 3)]); toe[2] = max(toe[2], 0.02)
    R[f'Shoulder_{S}'] = (top, sh, 'Bone.003', S == 'L'); R[f'Humerus_{S}'] = (sh, el, f'Shoulder_{S}', True); R[f'Forearm_{S}'] = (el, wr, f'Humerus_{S}', True)
    R[f'Palm_{S}'] = (wr, mcp, f'Forearm_{S}', True); R[f'Fingers_{S}'] = (mcp, tip, f'Palm_{S}', True)
    R[f'Pelvic_{S}'] = (pel, hip, None, False); R[f'Femur_{S}'] = (hip, kn, f'Pelvic_{S}', True); R[f'Tibia_{S}'] = (kn, an, f'Femur_{S}', True); R[f'Heel_{S}'] = (an, heel, f'Tibia_{S}', True)
    R[f'Sole_{S}'] = (heel, ball, f'Heel_{S}', True); R[f'Toes_{S}'] = (ball, toe, f'Sole_{S}', True)
old = json.load(open(SP + '/rig/rig_info_p.json'))
# ---------------------------------------------------------------- Blender objects
bpy.ops.wm.read_factory_settings(use_empty=True)
faces = [f for f, g in F if g == 'body']; me = bpy.data.meshes.new('MaleBASE'); me.from_pydata([tuple(v) for v in W[:NB]], [], [tuple(f) for f in faces]); me.update()
for p in me.polygons: p.use_smooth = True
body = bpy.data.objects.new('MaleBASE', me); bpy.context.scene.collection.objects.link(body)
ad = bpy.data.armatures.new('Armature'); arm = bpy.data.objects.new('Armature', ad); bpy.context.scene.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for n in old:                                                              # keep the old creation order (parents first)
    h, t, par, conn = R[n]; eb = ad.edit_bones.new(n); eb.head = Vector(h.tolist()); eb.tail = Vector(t.tolist())
    zref = Vector(np.array(old[n]['M'])[:3, 2].tolist()); y = (eb.tail - eb.head).normalized(); zp = zref - y * zref.dot(y)
    if zp.length > 1e-4: eb.align_roll(zp)
for n in old:
    h, t, par, conn = R[n]
    if par: ad.edit_bones[n].parent = ad.edit_bones[par]; ad.edit_bones[n].use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
# ---------------------------------------------------------------- skin weights: MakeHuman default-rig weights regrouped onto the 28 bones
MW = json.load(open(MH.MP + '/rigs/standard/weights.default.json'))['weights']
def target_of(b):
    base = b.split('.')[0]
    if base in ('spine05', 'root'): return 'Bone'
    if base == 'spine04': return 'Bone.001'
    if base == 'spine03': return 'Bone.002'
    if base in ('spine02', 'spine01'): return 'Bone.003'
    if base.startswith('breast'): return 'Bone.002'
    if base.startswith('neck'): return 'Bone.026'
    S = b[-1] if b.endswith(('.L', '.R')) else None
    if base in ('clavicle', 'shoulder01'): return f'Shoulder_{S}'
    if base in ('upperarm01', 'upperarm02'): return f'Humerus_{S}'
    if base in ('lowerarm01', 'lowerarm02'): return f'Forearm_{S}'
    if base == 'wrist' or base.startswith('metacarpal'): return f'Palm_{S}'
    if base.startswith('finger'): return f'Fingers_{S}'
    if base == 'pelvis': return f'Pelvic_{S}'
    if base in ('upperleg01', 'upperleg02'): return f'Femur_{S}'
    if base in ('lowerleg01', 'lowerleg02'): return f'Tibia_{S}'
    if base == 'foot': return f'FOOT_{S}'
    if base.startswith('toe'): return f'Toes_{S}'
    return 'Bone.027'                                                      # head, jaw, eyes, facial muscles
acc = {}
for b, lst in MW.items():
    tn = target_of(b)
    for i, w in lst:
        if i < NB: acc.setdefault(tn, {}); acc[tn][i] = acc[tn].get(i, 0) + w
for S in ('L', 'R'):                                                       # foot: ankle region follows the shin-side Heel bone, forefoot follows the Sole
    fw = acc.pop(f'FOOT_{S}', {}); h, t = R[f'Heel_{S}'][0], R[f'Toes_{S}'][0]; ax = R[f'Sole_{S}'][1] - R[f'Heel_{S}'][1]
    for i, w in fw.items():
        tt = float(np.clip(np.dot(W[i] - R[f'Heel_{S}'][1], ax) / np.dot(ax, ax) * 1.0 + 0.0, 0, 1)); wh = float(np.clip(1.0 - tt / 0.35, 0, 1)) * float(np.clip((W[i][2] - 0.02) / 0.05, 0, 1))
        for nm, ww in ((f'Heel_{S}', w * wh), (f'Sole_{S}', w * (1 - wh))):
            if ww > 0: acc.setdefault(nm, {}); acc[nm][i] = acc[nm].get(i, 0) + ww
tot = np.zeros(NB)
for n in acc:
    for i, w in acc[n].items(): tot[i] += w
print('unweighted verts', int((tot < 1e-6).sum()))
for n in old:
    g = body.vertex_groups.new(name=n)
    for i, w in acc.get(n, {}).items():
        if tot[i] > 1e-9: g.add([i], w / tot[i], 'REPLACE')
body.parent = arm; am = body.modifiers.new('Armature', 'ARMATURE'); am.object = arm
# ---------------------------------------------------------------- rig info (same schema as rig_info_p.json)
info = {}
for n in old:
    b = ad.bones[n]; M4 = np.array(b.matrix_local); h = np.array(b.head_local); t = np.array(b.tail_local)
    info[n] = dict(M=M4.tolist(), head=h.tolist(), tail=t.tolist(), parent=R[n][2], conn=R[n][3], length=float(np.linalg.norm(t - h)))
json.dump(info, open(INFO, 'w'), indent=0)
for n, v in info.items(): print(f"{n:11s} len {v['length']:.3f}  old {old[n]['length']:.3f}")
bpy.ops.wm.save_as_mainfile(filepath=OUT); print('saved', OUT)

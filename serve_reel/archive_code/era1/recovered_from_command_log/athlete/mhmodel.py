"""MakeHuman (MPFB2, CC0) base mesh + macro targets -> athletic male in my world convention (metres, faces +x, left=+y, up=+z)."""
import numpy as np, gzip, json, os, glob
MP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad/mpfb/mpfb2/src/mpfb/data'
def load_obj():
    V, F, grp, cur = [], [], {}, None
    for ln in open(MP + '/3dobjs/base.obj'):
        if ln.startswith('v '): V.append([float(x) for x in ln.split()[1:4]])
        elif ln.startswith('g '): cur = ln.split()[1]
        elif ln.startswith('f '): F.append(([int(t.split('/')[0]) - 1 for t in ln.split()[1:]], cur))
    return np.array(V), F
def read_target(path):
    out = {}
    with gzip.open(path, 'rt') if path.endswith('.gz') else open(path) as f:
        for ln in f:
            if not ln.strip() or ln.startswith('#'): continue
            p = ln.split()
            if len(p) >= 4: out[int(p[0])] = (float(p[1]), float(p[2]), float(p[3]))
    return out
def tri_w(v, lo=0.5):                     # slider 0..1 -> (min, avg, max) weights (MakeHuman macro convention)
    mn = max(0.0, (lo - v) * 2) if v < lo else 0.0; mx = max(0.0, (v - lo) * 2) if v > lo else 0.0; return mn, 1 - mn - mx, mx
def athlete(muscle=0.5, weight=0.3, height=0.6, age_young=1.0, extra=None):
    V, F = load_obj(); P = V.copy(); mn, av, mx = tri_w(muscle); wmn, wav, wmx = tri_w(weight); n = len(V)
    wm = {'minmuscle': mn, 'averagemuscle': av, 'maxmuscle': mx}; ww = {'minweight': wmn, 'averageweight': wav, 'maxweight': wmx}
    for m, a in wm.items():
        for w, b in ww.items():
            if a * b < 1e-6: continue
            t = read_target(f'{MP}/targets/macrodetails/universal-male-young-{m}-{w}.target.gz')
            for i, d in t.items(): P[i] += a * b * np.array(d)
            if height > 0.5:
                h = read_target(f'{MP}/targets/macrodetails/height/male-young-{m}-{w}-maxheight.target.gz')
                for i, d in h.items(): P[i] += a * b * (height - 0.5) * 2 * np.array(d)
    for path, wgt in (extra or []):
        for i, d in read_target(MP + '/targets/' + path).items(): P[i] += wgt * np.array(d)
    return V, P, F
def to_world(P):                          # MH: x=left, y=up, z=front (dm)  ->  x=front, y=left, z=up (m)
    return np.stack([P[:, 2], P[:, 0], P[:, 1]], 1) * 0.1
if __name__ == '__main__':
    V, P, F = athlete(); W = to_world(P); vg = json.load(open(MP + '/mesh_metadata/basemesh_vertex_groups.json'))
    print('verts', len(V), 'faces', len(F), 'groups sample', list(vg)[:6])
    body = [f for f, g in F if g == 'body']; mx = max(max(f) for f in body); print('body faces', len(body), 'max vertex idx', mx)
    print('height of body verts', W[:mx + 1, 2].min(), W[:mx + 1, 2].max(), ' width x', W[:mx+1,1].min(), W[:mx+1,1].max(), ' depth', W[:mx+1,0].min(), W[:mx+1,0].max())
    for nm in ('joint-pelvis', 'joint-spine-4', 'joint-spine-3', 'joint-spine-2', 'joint-spine-1', 'joint-neck', 'joint-head', 'joint-head-2', 'joint-l-clavicle', 'joint-l-scapula', 'joint-l-shoulder', 'joint-l-elbow', 'joint-l-hand', 'joint-l-hand-3', 'joint-l-upper-leg', 'joint-l-knee', 'joint-l-ankle', 'joint-l-foot-1', 'joint-l-foot-2', 'joint-l-toe-1-1', 'joint-l-toe-2-4', 'joint-ground', 'joint-l-finger-3-1', 'joint-l-finger-3-4'):
        print(nm, W[vg[nm]].mean(0).round(3))

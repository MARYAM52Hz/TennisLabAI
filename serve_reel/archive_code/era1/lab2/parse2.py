import xml.etree.ElementTree as ET, numpy as np, json, pickle
SP = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
r = ET.parse(SP + '/lab2/annotations.xml').getroot(); N = 237
court = {}; skel = {}; ball = {}; shapes = {}
def pts(s): return np.array([[float(v) for v in p.split(',')] for p in s.split(';')])
for t in r.findall('track'):
    lab = t.get('label')
    if lab.startswith('C_'):
        for e in t:                                                    # polyline keyframes (usually one, static court)
            if e.get('outside') == '0': court.setdefault(lab, []).append((int(e.get('frame')), pts(e.get('points'))))
    elif lab == 'J_Skeleton-based':
        for sk in t.findall('skeleton'):                                  # one element per frame, containing sub-points
            f = int(sk.get('frame')); 
            for p in sk.findall('points'):
                skel.setdefault(p.get('label'), {})[f] = (*[float(v) for v in p.get('points').split(',')], int(p.get('outside')), int(p.get('occluded')))
    elif lab in ('B_ball', 'R_racket_face', 'R_racket_handle', 'R_racket_bbox', 'B_contact_racket', 'B_contact_ground', 'T_ball_trajectory', 'T_racket_trajectory', 'T_racket_trajectory2'):
        for e in t: shapes.setdefault(lab, []).append((t.get('id'), int(e.get('frame')), e.tag, dict(e.attrib)))
pickle.dump(dict(court=court, skel=skel, shapes=shapes), open(SP + '/lab2/labels2.pkl', 'wb'))
print('court', {k: [(f, v.shape) for f, v in vv] for k, vv in court.items()})
print('skel joints', len(skel), {k: (min(v), max(v), len(v)) for k, v in list(skel.items())[:4]})
print({k: (len(v), v[0][1], v[-1][1]) for k, v in shapes.items()})

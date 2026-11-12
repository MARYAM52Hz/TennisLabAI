"""metrics.json + job.json -> ana/data.py (numbers only; labels/benchmarks come from the template). usage: python3 gen_data.py"""
import json, os, re
SP = os.environ['REEL_JOB']; JC = json.load(open(SP + '/job.json')); view = JC['view']; ana = JC['ana']
D = json.load(open(SP + '/' + ana + '/metrics.json')); OV = JC.get('override', {})
ev = dict(D['events']); ev.update(OV.get('events', {}))
tpl = open(os.path.dirname(os.path.abspath(__file__)) + '/data_%s.tpl' % view).read() if os.path.exists(os.path.dirname(os.path.abspath(__file__)) + '/data_%s.tpl' % view) else open(SP + '/data_%s.tpl' % view).read()
R = lambda v: int(round(v))
val = dict(TC=round(ev['contact'], 2), TROPHY=float(ev['trophy']), LOW=float(ev['low']), LANDING=float(ev['landing']), ST0=JC['st0'], ST1=JC['st1'],
           knee_front=R(D['trophy']['kneeFront']), knee_back=R(D['trophy']['kneeBack']), trunk=R(D['trophy']['trunkInc']),
           elbow_low=R(D['low']['elbow2D'] if view == 'back' else D['low']['elbow3D']), elbow_ct=R(D['contact']['elbow2D']), tilt=R(D['contact']['shTilt']) if view == 'back' else 0,
           height=round(D['contact']['height'], 2), speed=R(D['ball']['speed_kmh']) if view == 'back' else 0,
           T_TC=D['times_ms']['trophy_to_contact'], T_LOW=D['times_ms']['low_to_contact'], APEX=round(D['toss']['apexZ'], 2))
if view == 'back': val.update(AHEAD=R(D['contact']['ahead'] * 100), LAND=R(D['landing']['into_court'] * 100), LEAN=0)
else: val.update(AHEAD=R(D['contact']['ball_ahead_of_head'] * 100), LAND=R((D['landing']['into_court'] - D['foot_at_toss_y']) * 100), LEAN=R(D['contact']['lean']))
val.update(OV.get('values', {}))
for k, v in val.items(): tpl = tpl.replace('@@%s@@' % k, str(v))
assert '@@' not in tpl, re.findall(r'@@\w+@@', tpl)
open(SP + '/' + ana + '/data.py', 'w').write(tpl); print('data.py written', {k: v for k, v in val.items()})

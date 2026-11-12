"""Parse the CVAT video export (annotations.xml) -> labels.pkl (court, skeleton, racket, ball, racket face, contacts)"""
import xml.etree.ElementTree as ET, numpy as np, pickle
SP = __import__('os').environ['REEL_JOB']; JC = __import__('json').load(open(SP + '/job.json'))
r=ET.parse(JC['labels_xml']).getroot(); T=JC['T_lab']
out=dict(court={},skel={},rack={},ball={},ballc={},face={},contacts=[]); balls={}
for t in r.findall('track'):
    lab=t.get('label'); sk=t.findall('skeleton')
    def per(): 
        for s in sk:
            f=int(s.get('frame'))
            for p in s.findall('points'): yield f,p.get('label'),[float(v) for v in p.get('points').split(',')],int(p.get('outside')),int(p.get('occluded'))
    if lab=='C_structured_court':
        for f,n,p,o,oc in per():
            if f==0: out['court'][n]=np.array(p)
    elif lab=='P_player_skeleton':
        for f,n,p,o,oc in per(): out['skel'].setdefault(n,np.zeros((T,2)))[f]=p
    elif lab=='R_racket_skeleton':
        for f,n,p,o,oc in per(): out['rack'].setdefault(n,np.zeros((T,2)))[f]=p
    elif lab=='B_ball':
        balls[t.get('id')]={int(e.get('frame')):(float(e.get('cx')),float(e.get('cy')),float(e.get('rx')),float(e.get('ry')),int(e.get('outside'))) for e in t.findall('ellipse')}
    elif lab=='R_racket_face':
        for e in t.findall('ellipse'): out['face'][int(e.get('frame'))]=(float(e.get('cx')),float(e.get('cy')),float(e.get('rx')),float(e.get('ry')),float(e.get('rotation')))
    elif lab.startswith('B_contact'):
        for e in t.findall('points'):
            if e.get('outside')=='0': out['contacts'].append((lab,int(e.get('frame')),[float(v) for v in e.get('points').split(',')]))
# the serve ball = the B_ball track that is at the labelled racket-contact point at the contact frame (a scene may contain several B_ball tracks)
ct=[c for c in out['contacts'] if c[0]=='B_contact_racket']
if ct:
    tcf,(cu,cv)=ct[0][1],ct[0][2][:2]; sc={k:float(np.hypot(b[tcf][0]-cu,b[tcf][1]-cv)) for k,b in balls.items() if tcf in b and not b[tcf][4]}
    if sc: kbest=min(sc,key=sc.get); out['ball']=balls[kbest]; print('serve ball track',kbest,'dist to contact point %.1f px'%sc[kbest],'(others: %s)'%{k:round(v) for k,v in sc.items() if k!=kbest})
elif balls: out['ball']=list(balls.values())[0]
pickle.dump(out,open(JC['labels_pkl'],'wb')); print(out['contacts'], len(out['court']), list(out['skel'])[:3], list(out['rack']))

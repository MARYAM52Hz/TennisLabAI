"""Parse the CVAT export of IMG_7125 (720x1280, 133 frames of which 0..91 are real footage) -> nl/labels.pkl"""
import xml.etree.ElementTree as ET, numpy as np, pickle
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
r=ET.parse(SP+'/new/cvat/annotations.xml').getroot(); T=133
out=dict(court={},skel={},rack={},ball={},ballc={},face={},contacts=[])
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
        for e in t.findall('ellipse'): out['ball'][int(e.get('frame'))]=(float(e.get('cx')),float(e.get('cy')),float(e.get('rx')),float(e.get('ry')),int(e.get('outside')))
    elif lab=='R_racket_face':
        for e in t.findall('ellipse'): out['face'][int(e.get('frame'))]=(float(e.get('cx')),float(e.get('cy')),float(e.get('rx')),float(e.get('ry')),float(e.get('rotation')))
    elif lab.startswith('B_contact'):
        for e in t.findall('points'):
            if e.get('outside')=='0': out['contacts'].append((lab,int(e.get('frame')),[float(v) for v in e.get('points').split(',')]))
pickle.dump(out,open(SP+'/nl/labels.pkl','wb')); print(out['contacts'], len(out['court']), list(out['skel'])[:3], list(out['rack']))

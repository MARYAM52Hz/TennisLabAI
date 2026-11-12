"""Assemble the analysis reel frames (fa + en).  usage: python3 -I build.py SEGMENT [SEGMENT...]   (segments: intro model orbA freezeA orbB freezeB long score verdict sources)"""
import sys, os, json, numpy as np, cv2
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/ana')
from slides import *
LANGS=('fa','en')
planB=json.load(open(SP+'/lab3/plan.json'))['frames']; planA=json.load(open(SP+'/lab3/plan_A.json'))['frames']; planF=json.load(open(SP+'/lab3/plan_F.json'))['frames']
for l in LANGS: os.makedirs(f'{SP}/fin_{l}',exist_ok=True)
ORDER=['intro','model','orbA','freezeA','orbB','freezeB','long','score','verdict','sources']
N={'intro':90,'model':150,'orbA':210,'freezeA':144,'orbB':210,'freezeB':144,'long':360,'score':150,'verdict':180,'sources':90}
START={}; t=0
for k in ORDER: START[k]=t; t+=N[k]
def fade(img,i,n,fi=8,fo=8):
    f=min(1.0,(i+1)/fi,(n-i)/fo) if fi else 1.0; return (img.astype(np.float32)*max(0.0,f)).astype(np.uint8) if f<1.0 else img
def bg_slide():
    b=cv2.imread(SP+'/lab3/oA/o0100.png'); b=cv2.GaussianBlur(b,(0,0),16); return (b*0.38).astype(np.uint8)
def tmask(d,i):
    t=cv2.imread(f'{SP}/lab3/{d}/t{i:04d}.png',cv2.IMREAD_UNCHANGED)
    if t is None or t.shape[2]<4: return None
    a=t[...,3].astype(np.float32)/255; a=cv2.GaussianBlur(a,(0,0),16); return np.clip(a*4.0,0,1)
def umask(mk,tm): return mk if tm is None else np.maximum(mk,tm)
def out(lang,idx,img): cv2.imwrite(f'{SP}/fin_{lang}/f{idx:05d}.png',img)
def run(seg):
    n=N[seg]; s0=START[seg]; todo=[i for i in range(n) if not all(os.path.exists(f'{SP}/fin_{l}/f{s0+i:05d}.png') for l in LANGS)]
    if not todo: print(seg,'done already'); return
    if seg in ('intro','model','score','verdict','sources'):
        bg=bg_slide(); fn={'intro':slide_intro,'model':slide_model,'score':slide_score,'verdict':slide_verdict,'sources':slide_sources}[seg]
        for lang in LANGS:
            img=composite(bg,fn(lang))
            for i in todo: out(lang,s0+i,fade(img,i,n,12,12))
    elif seg in ('orbA','orbB'):
        plan=planA if seg=='orbA' else planB; sv='A' if seg=='orbA' else 'B'; dirn='oA' if seg=='orbA' else 'o'
        frames=plan[:210]; h=max(orbit_h(sv,f['tau']) for f in frames); pos=choose_pos(frames,h); print(seg,'card at',pos)
        for i in todo:
            base=cv2.imread(f'{SP}/lab3/{dirn}/o{i:04d}.png'); mk=umask(subject_mask(frames[i]),tmask('rA' if seg=='orbA' else 'r',i))
            for lang in LANGS:
                Lt,La=orbit_overlay(lang,sv,frames[i],i,pos); out(lang,s0+i,fade(composite(base,merge(Lt,La,mk)),i,n,6,10))
    elif seg in ('freezeA','freezeB'):
        off=0 if seg=='freezeA' else 144
        for i in todo:
            fi=off+i; fr=planF[fi]; k=fr['k']; base=cv2.imread(f'{SP}/lab3/oF/o{fi:04d}.png'); mk=umask(subject_mask(fr),tmask('rF',fi))
            for lang in LANGS:
                Lt,La=freeze_overlay(lang,fr,k); out(lang,s0+i,fade(composite(base,merge(Lt,La,mk)),k,48,6,6))
    elif seg=='long':
        for i in todo:
            fi=210+i; fr=planB[fi]; base=cv2.imread(f'{SP}/lab3/o/o{fi:04d}.png'); mk=umask(subject_mask(fr),tmask('r',fi))
            for lang in LANGS:
                Lt=long_overlay(lang,fr); out(lang,s0+i,fade(composite(base,masked(Lt,mk,0.9)),i,n,6,18))
    print(seg,'written',len(todo),flush=True)
if __name__=='__main__':
    for seg in sys.argv[1:]: run(seg)

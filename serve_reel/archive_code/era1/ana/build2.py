"""Reel v2 builder: reading-time-aware timeline, @tennismad.ai watermark, serve-type slide.
usage: python3 -I build2.py plan | SEGMENT... (segments: intro model orbA freezeA orbB freezeB long stype score verdict sources)"""
import sys, os, json, math, numpy as np, cv2
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/ana')
from slides import *
LANGS=('fa','en'); RATE=4.8; FPS=30
def need(words,lo=2.3): return max(lo,1.0+words/RATE)
planB=json.load(open(SP+'/lab3/plan.json'))['frames']; planA=json.load(open(SP+'/lab3/plan_A.json'))['frames']; planF=json.load(open(SP+'/lab3/plan_F.json'))['frames']
OUT={l:f'{SP}/fin2_{l}' for l in LANGS}
for d in OUT.values(): os.makedirs(d,exist_ok=True)
ORDER=['intro','model','orbA','freezeA','orbB','freezeB','long','stype','score','verdict','sources']
# ---------------- time schedules ----------------
def rows_of(serve,tau):
    st=stage_of(serve,tau); return {2:'knees',3:'elbow',4:'tilt',5:'contact',6:'speed',7:'speed'}.get(st,'trunk')
GW={'trunk':3.5,'knees':7,'elbow':6.5,'tilt':6.5,'contact':10,'speed':6.5}
def orbit_sched(serve,frames,fac):
    keys=[rows_of(serve,f['tau']) for f in frames]; sched=[]; i=0
    while i<len(frames):
        j=i
        while j+1<len(frames) and keys[j+1]==keys[i]: j+=1
        ns=j-i+1; no=max(ns,int(round(need(GW[keys[i]])*FPS*fac)))
        for q in range(no): sched.append(float(np.clip(i+(q+0.5)/no*ns-0.5,0,len(frames)-1)))
        i=j+1
    return sched
FW={'trophy':12+3*3.5,'low':12+3.5+3,'contact':12+3*3.5+3}
def freeze_sched(off):
    seq=[]
    for ki,ev in enumerate(('trophy','low','contact')):
        base=off+48*ki; nk=int(round(need(FW[ev])*FPS)); hold=max(0,nk-48)
        seq+= [(base+k,'play',k) for k in range(40)]+[(base+39,'hold',24)]*hold+[(base+k,'play',k) for k in range(40,48)]
    return seq
LONG_LEG=[(0,36),(1,112),(2,128),(3,84)]; LONG_HOLD=159; LONG_KH=308
ST_ROW=int(2.4*FPS); ST_VER=int(5.5*FPS)
VER_B=int(3.0*FPS); VER_L=int(4.5*FPS)
N={}
N['intro']=int(3.6*FPS); N['model']=8*int(1.6*FPS)
N['orbA']=len(orbit_sched('A',planA[:210],1.0)); N['orbB']=len(orbit_sched('B',planB[:210],0.85))
N['freezeA']=len(freeze_sched(0)); N['freezeB']=len(freeze_sched(144))
N['long']=360+LONG_HOLD; N['stype']=6*ST_ROW+ST_VER; N['score']=int(10*FPS); N['verdict']=6*VER_B+VER_L; N['sources']=int(8*FPS)
START={}; t=0
for k in ORDER: START[k]=t; t+=N[k]
TOTAL=t
# ---------------- helpers ----------------
def fade(img,i,n,fi=8,fo=8):
    f=min(1.0,(i+1)/fi,(n-i)/fo) if fi else 1.0; return (img.astype(np.float32)*max(0.0,f)).astype(np.uint8) if f<1.0 else img
def bg_slide():
    b=cv2.imread(SP+'/lab3/oA/o0100.png'); b=cv2.GaussianBlur(b,(0,0),16); return (b*0.38).astype(np.uint8)
def tmask(d,i):
    t=cv2.imread(f'{SP}/lab3/{d}/t{i:04d}.png',cv2.IMREAD_UNCHANGED)
    if t is None or t.shape[2]<4: return None
    a=t[...,3].astype(np.float32)/255; a=cv2.GaussianBlur(a,(0,0),16); return np.clip(a*4.0,0,1)
def umask(mk,tm): return mk if tm is None else np.maximum(mk,tm)
_wm=None
def wm(img,alpha=1.0):                                                    # @tennismad.ai pill, top centre, on every frame
    global _wm
    if _wm is None: L=Layer(); handle_pill(L); _wm=L.result()
    return composite(img,type('X',(),{'result':lambda s:_wm})(),alpha)
def out(lang,idx,img,watermark=True): cv2.imwrite(f'{OUT[lang]}/f{idx:05d}.png',wm(img) if watermark else img)
def exists(seg,i): return all(os.path.exists(f'{OUT[l]}/f{START[seg]+i:05d}.png') for l in LANGS)
def blend(a,b,w): return a if w<=1e-3 else cv2.addWeighted(a,1-w,b,w,0)
def xfade(prev,cur,j,n=6): return cur if prev is None or j>=n else blend(prev,cur,(j+1)/(n+1))
# ---------------- segments ----------------
def run(seg):
    n=N[seg]; s0=START[seg]; todo=[i for i in range(n) if not exists(seg,i)]
    if not todo: print(seg,'done already'); return
    if seg in ('intro','sources','score'):
        bg=bg_slide(); fn={'intro':slide_intro,'score':slide_score,'sources':slide_sources}[seg]
        for lang in LANGS:
            img=composite(bg,fn(lang))
            for i in todo: out(lang,s0+i,fade(img,i,n,12,12))
    elif seg=='model':
        bg=bg_slide(); per=n//8
        for lang in LANGS:
            imgs=[composite(bg,slide_model(lang,hl=h)) for h in range(8)]
            for i in todo: h=i//per; j=i%per; out(lang,s0+i,fade(xfade(imgs[h-1] if h else None,imgs[h],j,6),i,n,12,12))
    elif seg in ('stype','verdict'):
        bg=bg_slide()
        if seg=='stype': states=[(r,False) for r in range(1,7)]+[(6,True)]; dur=[ST_ROW]*6+[ST_VER]
        else: states=[(k,) for k in range(1,8)]; dur=[VER_B]*6+[VER_L]
        edges=np.cumsum([0]+dur)
        for lang in LANGS:
            imgs=[composite(bg,slide_stype(lang,*s_) if seg=='stype' else slide_verdict(lang,*s_)) for s_ in states]
            for i in todo:
                h=int(np.searchsorted(edges,i,side='right')-1); h=min(h,len(imgs)-1); j=i-edges[h]
                out(lang,s0+i,fade(xfade(imgs[h-1] if h else None,imgs[h],j,8),i,n,12,12))
    elif seg in ('orbA','orbB'):
        A=seg=='orbA'; plan=(planA if A else planB)[:210]; sv='A' if A else 'B'; dirn='oA' if A else 'o'; rdir='rA' if A else 'r'
        sched=orbit_sched(sv,plan,1.0 if A else 0.85); h=max(orbit_h(sv,f['tau']) for f in plan); pos=choose_pos(plan,h); print(seg,'card at',pos,'frames',n)
        cache={}
        def ov(lang,si):
            k=(lang,si)
            if k not in cache:
                if len(cache)>6: cache.clear()
                mk=umask(subject_mask(plan[si]),tmask(rdir,si)); Lt,La=orbit_overlay(lang,sv,plan[si],si,pos); cache[k]=merge(Lt,La,mk)
            return cache[k]
        for i in todo:
            s=sched[i]; i0=int(math.floor(s)); i1=min(i0+1,209); w=s-i0
            base=blend(cv2.imread(f'{SP}/lab3/{dirn}/o{i0:04d}.png'),cv2.imread(f'{SP}/lab3/{dirn}/o{i1:04d}.png'),w) if w>1e-3 else cv2.imread(f'{SP}/lab3/{dirn}/o{i0:04d}.png')
            si=int(round(s)); 
            for lang in LANGS: out(lang,s0+i,fade(composite(base,ov(lang,si)),i,n,6,10))
    elif seg in ('freezeA','freezeB'):
        off=0 if seg=='freezeA' else 144; seq=freeze_sched(off); cache={}; nks=[len(freeze_sched(off+48*0))]
        per=[]; 
        for ki in range(3):
            c=sum(1 for q in seq if off+48*ki<=q[0]<off+48*(ki+1)); per.append(c)
        edges=np.cumsum([0]+per)
        for i in todo:
            fi,mode,k=seq[i]; ki=int(np.searchsorted(edges,i,side='right')-1); j=i-edges[ki]; fr=planF[fi]
            base=cv2.imread(f'{SP}/lab3/oF/o{fi:04d}.png'); mk=umask(subject_mask(fr),tmask('rF',fi))
            for lang in LANGS:
                key=(lang,fi,mode)
                if key not in cache:
                    if len(cache)>8: cache.clear()
                    Lt,La=freeze_overlay(lang,fr,fr['k'] if mode=='play' else 24); cache[key]=merge(Lt,La,mk)
                out(lang,s0+i,fade(composite(base,cache[key]),j,per[ki],6,6))
    elif seg=='long':
        for i in todo:
            src=i if i<=LONG_KH else (LONG_KH if i<=LONG_KH+LONG_HOLD else i-LONG_HOLD); fi=210+src; fr=planB[fi]; base=cv2.imread(f'{SP}/lab3/o/o{fi:04d}.png'); mk=umask(subject_mask(fr),tmask('r',fi))
            for lang in LANGS:
                Lt=long_overlay(lang,fr); out(lang,s0+i,fade(composite(base,masked(Lt,mk,0.9)),i,n,6,18))
    print(seg,'written',len(todo),flush=True)
if __name__=='__main__':
    if sys.argv[1]=='plan':
        print({k:(N[k],round(N[k]/FPS,1)) for k in ORDER}); print('TOTAL frames',TOTAL,'= %.1f s'%(TOTAL/FPS))
    else:
        for seg in sys.argv[1:]: run(seg)

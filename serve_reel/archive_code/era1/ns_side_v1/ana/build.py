"""Reel builder for IMG_7125 (one flat serve). usage: python3 -I build.py plan | SEGMENT...   segments: intro model orb freeze long stype score verdict sources"""
import sys, os, json, math, numpy as np, cv2
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/ns/ana'); sys.path.insert(0,SP+'/ns')
from slides import *
LANGS=('fa','en'); RATE=6.2; FPS=30
def need(words,lo=2.0): return max(lo,0.8+words/RATE)
NR=SP+'/ns'; planO=json.load(open(NR+'/plan_o.json'))['frames']; planF=json.load(open(NR+'/plan_f.json'))['frames']; planL=json.load(open(NR+'/plan_l.json'))['frames']
OUT={l:f'{NR}/fin_{l}' for l in LANGS}
for d in OUT.values(): os.makedirs(d,exist_ok=True)
ORDER=['intro','model','orb','freeze','long','stype','score','verdict','sources']
def rows_of(tau): return {2:'knees',3:'elbow',4:'tilt',5:'contact',6:'speed',7:'speed'}.get(stage_of('A',tau),'trunk')
GW={'trunk':3.5,'knees':7,'elbow':3.5,'tilt':3.5,'contact':8,'speed':6.5}
def orbit_sched(frames):
    keys=[rows_of(f['tau']) for f in frames]; sched=[]; i=0
    while i<len(frames):
        j=i
        while j+1<len(frames) and keys[j+1]==keys[i]: j+=1
        ns=j-i+1; no=max(ns,int(round(need(GW[keys[i]])*FPS)))
        for q in range(no): sched.append(float(np.clip(i+(q+0.5)/no*ns-0.5,0,len(frames)-1)))
        i=j+1
    return sched
FW={'trophy':12+3*3.5,'low':12+3.5+3,'contact':12+3*3.5+3}
def freeze_sched():
    seq=[]
    for ki,ev in enumerate(('trophy','low','contact')):
        base=48*ki; nk=int(round(need(FW[ev])*FPS)); hold=max(0,nk-48)
        seq+= [(base+k,'play',k) for k in range(40)]+[(base+39,'hold',24)]*hold+[(base+k,'play',k) for k in range(40,48)]
    return seq
LONG_HOLD=max(0,int(round(need(30)*FPS))-80)
ST_ROW=int(1.8*FPS); ST_VER=int(4.0*FPS); VER_S=int(2.4*FPS); VER_P=int(2.8*FPS); VER_L=int(3.6*FPS)
N={'intro':int(2.8*FPS),'model':8*int(1.1*FPS)}
SCHED_O=orbit_sched(planO); N['orb']=len(SCHED_O); SEQ_F=freeze_sched(); N['freeze']=len(SEQ_F); N['long']=240+LONG_HOLD
N['stype']=6*ST_ROW+ST_VER; N['score']=int(8*FPS); N['verdict']=3*VER_S+3*VER_P+VER_L; N['sources']=int(5.5*FPS)
START={}; t=0
for k in ORDER: START[k]=t; t+=N[k]
TOTAL=t
def fade(img,i,n,fi=8,fo=8):
    f=min(1.0,(i+1)/fi,(n-i)/fo) if fi else 1.0; return (img.astype(np.float32)*max(0.0,f)).astype(np.uint8) if f<1.0 else img
def bg_slide():
    b=cv2.imread(NR+'/oo/o0075.png'); b=cv2.GaussianBlur(b,(0,0),16); return (b*0.38).astype(np.uint8)
def tmask(d,i):
    t=cv2.imread(f'{NR}/{d}/t{i:04d}.png',cv2.IMREAD_UNCHANGED)
    if t is None or t.shape[2]<4: return None
    a=t[...,3].astype(np.float32)/255; a=cv2.GaussianBlur(a,(0,0),16); return np.clip(a*4.0,0,1)
def umask(mk,tm): return mk if tm is None else np.maximum(mk,tm)
_wm=None
def wm(img):
    global _wm
    if _wm is None: L=Layer(); handle_pill(L); _wm=L.result()
    return composite(img,type('X',(),{'result':lambda s:_wm})(),1.0)
def out(lang,idx,img): cv2.imwrite(f'{OUT[lang]}/f{idx:05d}.png',wm(img))
def exists(seg,i): return all(os.path.exists(f'{OUT[l]}/f{START[seg]+i:05d}.png') for l in LANGS)
def blend(a,b,w): return a if w<=1e-3 else cv2.addWeighted(a,1-w,b,w,0)
def xfade(prev,cur,j,n=6): return cur if prev is None or j>=n else blend(prev,cur,(j+1)/(n+1))
def run(seg):
    n=N[seg]; s0=START[seg]; todo=[i for i in range(n) if not exists(seg,i)]
    if not todo: print(seg,'done already'); return
    if seg in ('intro','sources','score'):
        bg=bg_slide(); fn={'intro':slide_intro,'score':slide_score,'sources':slide_sources}[seg]
        for lang in LANGS:
            img=composite(bg,fn(lang))
            for i in todo: out(lang,s0+i,fade(img,i,n,10,10))
    elif seg=='model':
        bg=bg_slide(); per=n//8
        for lang in LANGS:
            imgs=[composite(bg,slide_model(lang,hl=h)) for h in range(8)]
            for i in todo: h=min(i//per,7); j=i-h*per; out(lang,s0+i,fade(xfade(imgs[h-1] if h else None,imgs[h],j,5),i,n,10,10))
    elif seg in ('stype','verdict'):
        bg=bg_slide()
        if seg=='stype': states=[(r,False) for r in range(1,7)]+[(6,True)]; dur=[ST_ROW]*6+[ST_VER]
        else: states=[(k,) for k in range(1,8)]; dur=[VER_S]*3+[VER_P]*3+[VER_L]
        edges=np.cumsum([0]+dur)
        for lang in LANGS:
            imgs=[composite(bg,slide_stype(lang,*s_) if seg=='stype' else slide_verdict(lang,*s_)) for s_ in states]
            for i in todo:
                h=min(int(np.searchsorted(edges,i,side='right')-1),len(imgs)-1); j=i-edges[h]
                out(lang,s0+i,fade(xfade(imgs[h-1] if h else None,imgs[h],j,6),i,n,10,10))
    elif seg=='orb':
        plan=planO; h=max(orbit_h('A',f['tau']) for f in plan); pos=choose_pos(plan,h); print('orbit card at',pos,'frames',n); cache={}
        def ov(lang,si):
            k=(lang,si)
            if k not in cache:
                if len(cache)>600: cache.clear()
                mk=umask(subject_mask(plan[si]),tmask('ro',si)); Lt,La=orbit_overlay(lang,'A',plan[si],si,pos); cache[k]=merge(Lt,La,mk)
            return cache[k]
        rd=lambda i: cv2.imread(f'{NR}/oo/o{i:04d}.png')
        for i in todo:
            s=SCHED_O[i]; i0=int(math.floor(s)); i1=min(i0+1,len(plan)-1); w=s-i0; base=blend(rd(i0),rd(i1),w) if w>1e-3 else rd(i0); si=int(round(s))
            for lang in LANGS: out(lang,s0+i,fade(composite(base,ov(lang,si)),i,n,6,10))
    elif seg=='freeze':
        per=[sum(1 for q in SEQ_F if 48*ki<=q[0]<48*(ki+1)) for ki in range(3)]; edges=np.cumsum([0]+per); cache={}
        for i in todo:
            fi,mode,k=SEQ_F[i]; ki=int(np.searchsorted(edges,i,side='right')-1); j=i-edges[ki]; fr=planF[fi]
            base=cv2.imread(f'{NR}/of/o{fi:04d}.png'); mk=umask(subject_mask(fr),tmask('rf',fi))
            for lang in LANGS:
                key=(lang,fi,mode)
                if key not in cache:
                    if len(cache)>8: cache.clear()
                    Lt,La=freeze_overlay(lang,fr,fr['k'] if mode=='play' else 24); cache[key]=merge(Lt,La,mk)
                out(lang,s0+i,fade(composite(base,cache[key]),j,per[ki],6,6))
    elif seg=='long':
        SEQL=list(range(208))+[207]*LONG_HOLD+list(range(208,240))
        for i in todo:
            fi=SEQL[min(i,len(SEQL)-1)]; fr=planL[fi]; base=cv2.imread(f'{NR}/ol/o{fi:04d}.png'); mk=umask(subject_mask(fr),tmask('rl',fi))
            for lang in LANGS:
                Lt=long_overlay(lang,fr); out(lang,s0+i,fade(composite(base,masked(Lt,mk,0.9)),i,n,6,18))
    print(seg,'written',len(todo),flush=True)
if __name__=='__main__':
    if sys.argv[1]=='plan':
        print({k:(N[k],round(N[k]/FPS,1)) for k in ORDER}); print('TOTAL frames',TOTAL,'= %.1f s'%(TOTAL/FPS))
    else:
        for seg in sys.argv[1:]: run(seg)

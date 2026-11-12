import sys, json, numpy as np, cv2
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/sw/pl/ana'); sys.path.insert(0,SP+'/sw/pl'); sys.path.insert(0,SP+'/sw')
from ui import *; from data import *; from strings import ST; from proj import project
from motion_sw import Motion2
M=Motion2()
def LX(lang): return lang=='fa'
def tx(L,lang,xy_edge,y,t,**kw):                 # text aligned to the reading-start edge: right in fa, left in en
    rtl=LX(lang); x=xy_edge; kw.setdefault('anchor','ra' if rtl else 'la'); L.text((x,y),t,rtl=rtl,**kw)
def num(lang,s): return fa(s) if LX(lang) else str(s)
def vfmt(lang,m,v):
    u=MET[m]['unit']; s=('%g'%v) if m!='height' else '%.2f'%v; return num(lang,s)+u
def edge(lang,side): # side 'start' or 'end' of the reading direction
    L_,R_=52,876
    if LX(lang): return R_ if side=='start' else L_
    return L_ if side=='start' else R_
def ends(lang): return (edge(lang,'start'),edge(lang,'end'))
def put_val(L,lang,y,t,fill=YEL,size=36,a=1.0):
    e=edge(lang,'end'); L.text((e,y),t,w='Bold',size=size,fill=fill,anchor='la' if LX(lang) else 'ra',rtl=False,alpha=a)
TYPE={'A':('سرو فلت','FLAT SERVE')}
def stitle(lang,serve): return TYPE[serve][0 if lang=='fa' else 1]
def header(L,lang,serve,tau,a=1.0):
    l=0 if LX(lang) else 1; s=edge(lang,'start')
    tx(L,lang,s,118,stitle(lang,serve),w='Black',size=70,fill=YEL,alpha=a,stroke=2)
    tx(L,lang,s,208,ST['sub'][lang],w='Medium',size=27,fill=WHT,alpha=0.85*a)
    st=stage_of(serve,tau); sw=96; gap=8; total=8*sw+7*gap; x0=52
    for i in range(8):
        idx=i if not LX(lang) else 7-i; xa=x0+i*(sw+gap)           # in fa the first stage sits at the right
        # chronological index of this slot
        chron=i if not LX(lang) else 7-i
        on=chron==st; done=chron<st
        fill=YEL+(int(255*(0.95 if on else 0.55 if done else 0.22)*a),)
        L.rrect((xa,262,xa+sw,278),r=8,fill=fill)
    nm=ST['stages'][st][0 if LX(lang) else 1]
    label=('%s — %s'%(fa(st+1),nm)) if LX(lang) else '%d — %s'%(st+1,nm)
    tx(L,lang,s,296,label,w='Bold',size=40,fill=WHT,alpha=a)
    if LX(lang): L.text((edge(lang,'end'),306),ST['stages'][st][1],w='Medium',size=28,fill=GRY,alpha=a,anchor='la',rtl=False)
    return st
def bar_row(L,lang,y,m,serve,a=1.0,show_ref=True):
    M_=MET[m]; v=M_[serve]; stt=status(m,v); col=YEL if stt=='ok' else ORG
    lab=ST['metric'][m][0 if LX(lang) else 1]; tx(L,lang,edge(lang,'start'),y,lab,w='Medium',size=32,fill=WHT,alpha=a)
    put_val(L,lang,y-8,vfmt(lang,m,v),fill=col,size=44,a=a)
    x0,x1=52,876; yb=y+58; t=lambda val:x0+(x1-x0)*(np.clip(val,M_['lo'],M_['hi'])-M_['lo'])/(M_['hi']-M_['lo'])
    if LX(lang): t0=t; t=lambda val:x1-(t0(val)-x0)
    L.rrect((x0,yb,x1,yb+12),r=6,fill=(255,255,255,int(55*a)))
    if M_['sd'] is not None:
        xa,xb=sorted([t(M_['mean']-M_['sd']),t(M_['mean']+M_['sd'])]); L.rrect((xa,yb-3,xb,yb+15),r=7,fill=YEL+(int(110*a),))
    xm=t(M_['mean']); L.line([(xm,yb-9),(xm,yb+21)],fill=WHT,width=3,alpha=0.9*a)
    L.circle((t(v),yb+6),12,fill=col,outline=DRK,width=3,alpha=a)
    st_t=ST['status'][stt][0 if LX(lang) else 1]; ref=ST['ref'][m][0 if LX(lang) else 1]
    pre=ST['refl'].get(m,(ST['ref_lbl']['fa'],ST['ref_lbl']['en']))[0 if LX(lang) else 1]; colr=(190,198,210) if stt=='ok' else ORG
    e0=edge(lang,'start'); fs=25
    if LX(lang):
        L.text((e0,yb+26),pre+':',w='Medium',size=fs,fill=(190,198,210),anchor='ra',rtl=True,alpha=a); wd=L.tw(pre+':','Medium',fs,rtl=True)
        L.text((e0-wd-10,yb+26),ref,w='Medium',size=fs,fill=(190,198,210),anchor='ra',rtl=False,alpha=a)
    else:
        L.text((e0,yb+26),pre+': '+ref,w='Medium',size=fs,fill=(190,198,210),anchor='la',rtl=False,alpha=a)
    L.text((edge(lang,'end'),yb+26),st_t,w='Bold',size=fs,fill=colr,anchor='la' if LX(lang) else 'ra',rtl=LX(lang),alpha=a)
    return 126
def chain_chips(L,lang,y,a=1.0):
    words=['پا','تنه','آرنج','راکت'] if LX(lang) else ['Legs','Trunk','Elbow','Racket']; sz=28; pad=14; gap=34
    ws=[L.tw(w_,'Bold',sz,rtl=LX(lang))+2*pad for w_ in words]; total=sum(ws)+gap*3; e=edge(lang,'end'); x=e if LX(lang) is False else e
    # laid out starting at the END edge going back toward the label; chronological order follows the reading direction
    order=list(range(4)) if not LX(lang) else list(range(4))
    if LX(lang):
        x=52                                                   # left edge; the first word (legs) is at the right end of the group
        pos=[]; xx=52+total
        for i in range(4): pos.append((xx-ws[i],xx)); xx-=ws[i]+gap
    else:
        pos=[]; xx=876-total
        for i in range(4): pos.append((xx,xx+ws[i])); xx+=ws[i]+gap
    for i,(a0,a1) in enumerate(pos):
        L.rrect((a0,y-6,a1,y+44),r=14,fill=YEL+(int(46*a),),outline=YEL+(int(200*a),),width=2)
        L.text(((a0+a1)/2,y-1),words[i],w='Bold',size=sz,fill=WHT,anchor='ma',alpha=a,rtl=LX(lang))
        if i<3:
            b0=pos[i+1]; mx=(a0+b0[1])/2 if LX(lang) else (a1+b0[0])/2; d=-1 if LX(lang) else 1
            L.poly([(mx-8*d,y+19-9),(mx+8*d,y+19),(mx-8*d,y+19+9)],YEL+(int(255*a),))
def info_row(L,lang,y,key,val,a=1.0,fill=WHT):
    lab=ST['info'][key][0 if LX(lang) else 1]; tx(L,lang,edge(lang,'start'),y,lab,w='Medium',size=32,fill=WHT,alpha=a)
    if key=='chain': chain_chips(L,lang,y-4,a); return 62
    L.text((edge(lang,'end'),y-4),val,w='Bold',size=38,fill=fill,anchor='la' if LX(lang) else 'ra',rtl=False,alpha=a); return 62
def ahead_txt(lang,v): return (ST['info']['in_court'][0 if LX(lang) else 1].format(v=num(lang,'+%d'%v)) if v>=0 else ST['info']['behind'][0 if LX(lang) else 1].format(v=num(lang,'%d'%-v)))
def land_txt(lang,v): return (ST['info']['in_court'][0 if LX(lang) else 1].format(v=num(lang,'%d'%v)) if v>=0 else ST['info']['behind'][0 if LX(lang) else 1].format(v=num(lang,'%d'%-v)))
def card(L,lang,box,a=1.0): L.rrect(box,r=22,fill=(8,12,20,int(96*a)))
def footer(L,lang,a=1.0): tx(L,lang,edge(lang,'start'),1478,ST['cap'][lang],w='Medium',size=24,fill=(190,198,210),alpha=0.95*a)
# ---------- 3D anchored drawings
def P2(fr,p): uv,z=project(p,fr['cam'],fr['target'],fr['fov']); return uv[0]
def arc3d(L,fr,J,d1,d2,r,label,col=YEL,a=1.0,lang='en',lab_off=1.55,fill=True):
    d1=d1/np.linalg.norm(d1); w=d2-np.dot(d2,d1)*d1; w/=np.linalg.norm(w); ang=np.arccos(np.clip(np.dot(d1,d2/np.linalg.norm(d2)),-1,1))
    ts=np.linspace(0,ang,24); pts=[P2(fr,J+r*(np.cos(t)*d1+np.sin(t)*w)) for t in ts]; c=P2(fr,J)
    if fill: L.poly([tuple(c)]+[tuple(p) for p in pts],fill=col+(int(70*a),))
    L.line([tuple(p) for p in pts],fill=col,width=5,alpha=a)
    L.line([tuple(c),tuple(P2(fr,J+r*1.5*d1))],fill=WHT,width=2.5,alpha=0.8*a,dash=(9,7))
    L.line([tuple(c),tuple(P2(fr,J+r*1.5*(d2/np.linalg.norm(d2))))],fill=col,width=3,alpha=0.9*a)
    mid=(d1*np.cos(ang/2)+w*np.sin(ang/2)); pl=P2(fr,J+lab_off*r*mid)
    L.text((pl[0],pl[1]-28),label,w='Black',size=52,fill=col,anchor='ma',alpha=a,rtl=False,stroke=4)
def dimline(L,fr,p0,p1,label,col=YEL,a=1.0):
    A,B=P2(fr,p0),P2(fr,p1); L.line([tuple(A),tuple(B)],fill=col,width=4,alpha=a,dash=(14,9))
    for q in (A,B): L.line([(q[0]-14,q[1]),(q[0]+14,q[1])],fill=col,width=4,alpha=a)
    m=(A+B)/2; L.text((m[0]+22,m[1]-24),label,w='Black',size=40,fill=col,anchor='la',alpha=a,rtl=False,stroke=3)
# ---------- keep the text away from the subject: per-pixel mask of the player / racket / ball, text fades only where it would cover them
BONES=[('left_shoulder','left_elbow'),('left_elbow','left_wrist'),('right_shoulder','right_elbow'),('right_elbow','right_wrist'),('left_shoulder','top_spine'),('right_shoulder','top_spine'),('top_spine','bottom_spine'),('top_spine','head'),('left_hip','bottom_spine'),('right_hip','bottom_spine'),('left_hip','left_knee'),('left_knee','left_ankle'),('right_hip','right_knee'),('right_knee','right_ankle'),('left_ankle','left_foot_index'),('right_ankle','right_foot_index')]
def subject_mask(fr):
    if fr.get('skel')=='none': return np.zeros((H,W),np.float32)
    tau=fr['tau']; m=np.zeros((H,W),np.uint8); k=float(np.clip(np.linalg.norm(np.array(fr['cam'])-np.array(fr['target']))/5.0,0.5,1.6)); pt=lambda p:tuple(int(round(v)) for v in P2(fr,p))
    for a_,b_ in BONES: cv2.line(m,pt(M.jf(a_,tau)),pt(M.jf(b_,tau)),255,int(64*k))
    cv2.circle(m,pt(M.jf('head',tau)),int(62*k),255,-1)
    bt,Rr,_=M.racket(tau); hd=M.head_at(tau); cv2.line(m,pt(bt),pt(hd),255,int(50*k)); cv2.circle(m,pt(hd),int(78*k),255,-1)
    bl=M.ball(tau)
    if bl[2]>-10: cv2.circle(m,pt(bl),int(48*k),255,-1)
    m=cv2.GaussianBlur(m,(0,0),22); return np.clip(m.astype(np.float32)/255*1.6,0,1)
def choose_pos(frames,h):
    best=None
    for pos,(a,b) in {'top':(380,380+h),'bottom':(1456-h,1456)}.items():
        v=np.mean([subject_mask(f)[a:b].mean() for f in frames[::6]]); best=(v,pos) if best is None or v<best[0] else best
    return best[1]
def masked(L,mask,strength=0.92):
    a=np.array(L.im.getchannel('A'),np.float32)/255.0; mk=cv2.resize(mask,(W*SS,H*SS)); a=a*(1-strength*mk); L.im.putalpha(Image.fromarray((a*255).astype(np.uint8))); return L
def merge(Lt,La,mask):
    masked(Lt,mask); Lt.im.alpha_composite(La.im); return Lt
# ---------- orbit overlay
def orbit_h(serve,tau):
    st=stage_of(serve,tau); rows={2:1,3:1,4:1,5:2,6:1,7:1}.get(st,1)
    if st==2: rows=2
    n_info=1 if st in (3,4,5,6,7) else 0; return 40+126*rows+62*n_info+24
def orbit_overlay(lang,serve,fr,n,pos='bottom',ac=1.0,ah=1.0):
    L=Layer(); La=Layer(); tau=fr['tau']; tc=TC[serve]; st=header(L,lang,serve,tau,ah)
    rows={2:['knee_front','knee_back'],3:['elbow_low'],4:['tilt'],5:['height','elbow_ct'],6:['speed'],7:['speed']}.get(st,['trunk'])
    if serve=='B' and st==2: rows=['knee_front','knee_back']
    n_info=1 if st in (3,4,6,7,5) else 0; h=40+126*len(rows)+62*n_info+24; y0=(1450-h) if pos=='bottom' else 392; card(L,lang,(36,y0-14,892,y0-14+h+16),ac)
    y=y0+14
    for m in rows: y+=bar_row(L,lang,y,m,serve,ac)
    x=X[serve]
    if st==3: info_row(L,lang,y,'low_t','%s ms'%num(lang,x['t_low']) if LX(lang) else '%d ms'%x['t_low'],ac)
    elif st==4: info_row(L,lang,y,'chain',ST['info']['chain_v'][0 if LX(lang) else 1],ac,fill=YEL)
    elif st==5: info_row(L,lang,y,'ahead',ahead_txt(lang,x['ahead']),ac)
    elif st in (6,7): info_row(L,lang,y,'land',land_txt(lang,x['landing']),ac)
    footer(L,lang,ac if pos=='bottom' else 1.0)
    # 3D anchors
    d=abs(tau-tc)
    if d<=0.9:
        a=float(np.clip(1-(d-0.3)/0.6,0,1)); b=M.ball(tau); 
        if b[2]>-10: dimline(La,fr,np.array([b[0]+0.28,b[1],0.0]),np.array([b[0]+0.28,b[1],b[2]]),('%.2f m'%MET['height'][serve]) if lang=='en' else fa('%.2f'%MET['height'][serve])+' m',a=a)
    if tc+0.3<=tau<=tc+6:
        b=M.ball(tau); 
        if b[2]>-10:
            p=P2(fr,b); a=float(np.clip(min((tau-tc-0.3)/0.5,(tc+6-tau)/1.5),0,1)); 
            if 0<p[0]<W and 0<p[1]<H: La.text((p[0]+26 if p[0]<W-400 else p[0]-26,p[1]-18),('≈ %d km/h'%MET['speed'][serve]) if lang=='en' else '≈ '+fa(MET['speed'][serve])+' km/h',w='Black',size=44,fill=YEL,anchor='la' if p[0]<W-400 else 'ra',alpha=a,rtl=False,stroke=3)
    return L,La
# ---------- freeze overlay
def freeze_overlay(lang,fr,k):
    L=Layer(); La=Layer(); s=fr['serve']; e=fr['event']; tau=fr['tau']; a=float(np.clip(min(k/8,(47-k)/8,1.0),0,1)); a=max(a,0.0)
    title,sub=ST['kp'][e]; l=0 if LX(lang) else 1
    L.rrect((30,72,898,292),r=22,fill=(8,12,20,int(96*a)))
    tx(L,lang,edge(lang,'start'),82,stitle(lang,s),w='Black',size=48,fill=YEL,alpha=a,stroke=2)
    tx(L,lang,edge(lang,'start'),160,title[l],w='Bold',size=38,fill=WHT,alpha=a)
    tx(L,lang,edge(lang,'start'),236,sub[l],w='Medium',size=28,fill=(205,212,224),alpha=a)
    rows={'trophy':['knee_front','knee_back','trunk'],'low':['elbow_low'],'contact':['height','elbow_ct','tilt']}[e]
    n_info={'trophy':0,'low':1,'contact':1}[e]; h=40+126*len(rows)+62*n_info+24; y0=1450-h; card(L,lang,(36,y0-14,892,1456),a); y=y0+8
    for m in rows: y+=bar_row(L,lang,y,m,s,a)
    x=X[s]
    if e=='low': info_row(L,lang,y,'low_t',('%s ms'%num(lang,x['t_low'])),a)
    if e=='contact': info_row(L,lang,y,'ahead',ahead_txt(lang,x['ahead']),a)
    footer(L,lang,a)
    J=lambda n_: M.jf(n_,tau); Z=np.array([0,0,1.0]); col=YEL
    if e=='trophy':
        for side,key,m_ in (('left','knee_front','knee_front'),('right','knee_back','knee_back')):
            hip,kn,an=J(side+'_hip'),J(side+'_knee'),J(side+'_ankle'); d1=kn-hip; d2=an-kn
            arc3d(La,fr,kn,d1,d2,0.16,('%g°'%MET[m_][s]) if lang=='en' else fa('%g'%MET[m_][s])+'°',col=YEL if status(m_,MET[m_][s])=='ok' else ORG,a=a)
        bs,ts=J('bottom_spine'),J('top_spine'); arc3d(La,fr,bs,Z,ts-bs,0.30,('%g°'%MET['trunk'][s]) if lang=='en' else fa('%g'%MET['trunk'][s])+'°',col=CYA,a=a,lab_off=1.4)
    elif e=='low':
        sh,el,wr=J('right_shoulder'),J('right_elbow'),J('right_wrist'); arc3d(La,fr,el,el-sh,wr-el,0.17,('%g°'%MET['elbow_low'][s]) if lang=='en' else fa('%g'%MET['elbow_low'][s])+'°',col=YEL,a=a)
        hd=M.head_at(tau); p=P2(fr,hd); La.circle(tuple(p),16,outline=CYA,width=4,alpha=a)
        lab={'fa':'پایین‌ترین نقطه‌ی راکت','en':'Racket low point'}[lang]; La.text((p[0]+(-28 if LX(lang) else 28),p[1]+8),lab,w='Bold',size=30,fill=CYA,anchor='ra' if LX(lang) else 'la',alpha=a,rtl=LX(lang),stroke=3)
    elif e=='contact':
        b=M.ball(tau)
        if b[2]>-10:
            dimline(La,fr,np.array([b[0]+0.3,b[1],0.0]),np.array([b[0]+0.3,b[1],b[2]]),('%.2f m'%MET['height'][s]) if lang=='en' else fa('%.2f'%MET['height'][s])+' m',col=YEL,a=a)
        sh,el,wr=J('right_shoulder'),J('right_elbow'),J('right_wrist'); arc3d(La,fr,el,el-sh,wr-el,0.16,('%g°'%MET['elbow_ct'][s]) if lang=='en' else fa('%g'%MET['elbow_ct'][s])+'°',col=YEL,a=a)
    return L,La


"""Optional posture-timeline slide (both views). exec()d at the end of slides.py so it can use the slide helpers.
Needs: Layer, tx, para, title, edge, LX, num, fa, YEL/CYA/ORG/WHT/DRK, M, EV, TC, JC."""
# ---------- posture timeline (only a side view shows this)
from series import tsec
_TL=None
def tl_data():
    global _TL
    from series import tsec
    if _TL is None:
        from scipy.ndimage import gaussian_filter1d
        ks=np.linspace(0,EV['A']['landing'],153)
        def ang(a,b,c): u=a-b; v=c-b; return np.degrees(np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1)))
        kf=[180-ang(M.jf('left_hip',k),M.jf('left_knee',k),M.jf('left_ankle',k)) for k in ks]
        kb=[180-ang(M.jf('right_hip',k),M.jf('right_knee',k),M.jf('right_ankle',k)) for k in ks]
        ln=[]; pz=[]; inc=[]; lat=[]
        for k in ks:
            v=M.jf('top_spine',k)-M.jf('bottom_spine',k); ln.append(np.degrees(np.arctan2(v[1],v[2]))); pz.append(M.jf('bottom_spine',k)[2])
            u=v/np.linalg.norm(v); inc.append(np.degrees(np.arccos(np.clip(u[2],-1,1)))); lat.append(np.degrees(np.arctan2(-u[0],u[2])))
        sm=lambda a: gaussian_filter1d(np.array(a),3.0,mode='nearest')
        t=np.array([(tsec(k)-tsec(TC['A']))*1000 for k in ks])
        _TL=dict(ks=ks,t=t,kf=sm(kf),kb=sm(kb),ln=sm(ln),pz=sm(pz),inc=sm(inc),lat=sm(lat))
    return _TL
def _tl_sub(lang):
    back=(JC.get('view')=='back')
    if LX(lang): return 'زانو، تنه و لگن · از پشت: شیب جانبی دقیق‌تر است' if back else 'خمش زانو، شیب تنه، ارتفاع لگن'
    return 'Knee, trunk, pelvis · from behind, sideways tilt is the reliable one' if back else 'Knee bend, trunk lean, pelvis height'
def slide_timeline(lang,p=1.0,fd=1.0):
    L=Layer(); l=0 if LX(lang) else 1; D=tl_data(); t=D['t']; n=len(t); ie=int(np.clip(round(p*(n-1)),1,n-1))
    title(L,lang,'خط زمانی پوسچر' if LX(lang) else 'Posture timeline',_tl_sub(lang))
    x0,x1=110,870; tmin,tmax=t[0],t[-1]; X=lambda v: x0+(x1-x0)*(v-tmin)/(tmax-tmin)
    ev=[(EV['A']['trophy'],('تروفی','Trophy'),CYA),(EV['A']['low'],('پایین','Low'),CYA),(EV['A']['contact'],('تماس','Contact'),YEL),(EV['A']['landing'],('فرود','Landing'),CYA)]
    back=(JC.get('view')=='back')
    def rng(keys,lo0,hi0,step):
        v=np.concatenate([D[k] for k in keys]); lo=min(lo0,np.floor((v.min()-1e-6)/step)*step); hi=max(hi0,np.ceil((v.max()+1e-6)/step)*step); hi=lo+np.ceil((hi-lo)/(3*step)-1e-9)*3*step; return lo,hi,[round(float(x),2) for x in np.linspace(lo,hi,4)]
    p1=rng(['kf','kb'],0,90,10)
    if back: p2=rng(['inc','lat'],-10,40,10); ser2=[('inc','تنه از قائم','Trunk from vertical',CYA),('lat','شیب جانبی','Sideways tilt',ORG)]; t2=('شیب تنه (°)','Trunk tilt (°)')
    else: p2=rng(['ln'],-10,40,10); ser2=[('ln','شیب تنه','Trunk',CYA)]; t2=('شیب تنه (°، + رو به جلو)','Trunk lean (°, + forward)')
    p3=rng(['pz'],0.8,1.2,0.1)
    panels=[('خمش زانو (°)','Knee flexion (°)',[('kf','زانوی جلو','Front knee',YEL),('kb','زانوی عقب','Back knee',ORG)],p1[0],p1[1],p1[2]),
            (t2[0],t2[1],ser2,p2[0],p2[1],p2[2]),
            ('ارتفاع لگن (m)','Pelvis height (m)',[('pz','ارتفاع لگن','Pelvis',WHT)],p3[0],p3[1],[round(v,2) for v in p3[2]])]
    y0=380; ph=300; gap=92
    for pi,(fa_t,en_t,ser,lo,hi,ticks) in enumerate(panels):
        ya=y0+pi*(ph+gap); yb=ya+ph; Y=lambda v,ya=ya,lo=lo,hi=hi: ya+ph*(1-(np.clip(v,lo,hi)-lo)/(hi-lo))
        L.rrect((40,ya-8,888,yb+8),r=18,fill=(8,12,20,int(170*fd)))
        tx(L,lang,edge(lang,'start'),ya-74,fa_t if LX(lang) else en_t,w='Bold',size=30,fill=WHT,alpha=fd)
        for tv in ticks:
            yy=Y(tv); L.line([(x0,yy),(x1,yy)],fill=(255,255,255),width=1.5,alpha=0.18*fd)
            L.text((x0-10,yy-14),num(lang,('%g'%round(float(tv),2))),w='Medium',size=22,fill=(190,198,210),anchor='ra',rtl=False,alpha=fd)
        for k_,nm,col in ev:
            xx=X((tsec(k_)-tsec(TC['A']))*1000)
            L.line([(xx,ya),(xx,yb)],fill=col,width=2.5,alpha=0.55*fd,dash=(10,8))
            if pi==0: L.text((xx,ya-(44 if ev.index((k_,nm,col))%2==0 else 20)),nm[l],w='Bold',size=20,fill=col,anchor='ma',rtl=LX(lang),alpha=fd)
        for si,(key,nf,ne,col) in enumerate(ser):
            pts=[(X(t[i]),Y(D[key][i])) for i in range(ie+1)]; L.line(pts,fill=col,width=6,alpha=fd)
            L.circle(pts[-1],9,fill=col,outline=DRK,width=2,alpha=fd)
            if len(ser)>1:
                yy=ya+14+si*34; lx=x0+24
                L.circle((lx,yy+12),7,fill=col,outline=None,alpha=fd)
                L.text((lx+16,yy),nf if LX(lang) else ne,w='Medium',size=24,fill=col,anchor='la',rtl=LX(lang),alpha=fd)
    yl=y0+2*(ph+gap)+ph+26
    for tv in [v for v in (-1500,-1000,-500,0,200,400) if tmin<=v<=tmax]:
        L.text((X(tv),yl),num(lang,'%d'%tv),w='Medium',size=22,fill=(190,198,210),anchor='ma',rtl=False,alpha=fd)
    tx(L,lang,edge(lang,'start'),yl+30,'زمان نسبت به تماس (ms)' if LX(lang) else 'Time relative to contact (ms)',w='Medium',size=22,fill=(190,198,210),alpha=fd)
    nt=timeline_notes(); lt=int(abs(round(nt['t_min'])))
    d_=lambda v,pos,neg: (pos if v>=0 else neg)
    if back:
        if LX(lang): msg='لگن در %s ms آخر %s cm بالا می‌آید. تنه در تروفی %s° و هنگام تماس %s° از قائم فاصله دارد و در تماس %s° به %s کج است.'%(fa('%d'%lt),fa('%d'%round(nt['rise'])),fa('%d'%round(nt['inc_tr'])),fa('%d'%round(nt['inc_ct'])),fa('%d'%round(abs(nt['lat_ct']))),d_(nt['lat_ct'],'چپ (دور از راکت)','راست (سمت راکت)'))
        else: msg='The pelvis rises %d cm in the last %d ms. The trunk is %d° off vertical at the trophy and %d° at contact, tilted %d° to the %s at contact.'%(round(nt['rise']),lt,round(nt['inc_tr']),round(nt['inc_ct']),round(abs(nt['lat_ct'])),d_(nt['lat_ct'],'left (away from the racket)','right (racket side)'))
    elif LX(lang): msg='پا خم می‌شود و بعد باز می‌شود: لگن در %s ms آخر %s cm بالا می‌آید. تنه در تروفی %s° رو به %s است و هنگام تماس %s° رو به %s.'%(fa('%d'%lt),fa('%d'%round(nt['rise'])),fa('%d'%round(abs(nt['lean_tr']))),d_(nt['lean_tr'],'جلو','عقب'),fa('%d'%round(abs(nt['lean_ct']))),d_(nt['lean_ct'],'جلو','عقب'))
    else: msg='Legs bend, then drive: the pelvis rises %d cm in the last %d ms. The trunk leans %s %d° at the trophy and %s %d° at contact.'%(round(nt['rise']),lt,d_(nt['lean_tr'],'forward','back'),round(abs(nt['lean_tr'])),d_(nt['lean_ct'],'forward','back'),round(abs(nt['lean_ct'])))
    para(L,lang,yl+78,msg,size=26,fill=(215,222,232),wmax=800,lh=1.4,a=fd)
    return L
def timeline_notes():
    D=tl_data(); t=D['t']; i_c=int(np.argmin(abs(t))); pz=D['pz']; i_min=int(np.argmin(pz[:i_c])); rise=(pz[i_c]-pz[i_min])*100
    i_tr=int(np.argmin(abs(D['ks']-EV['A']['trophy']))); return dict(rise=float(rise),lean_tr=float(D['ln'][i_tr]),lean_ct=float(D['ln'][i_c]),t_min=float(t[i_min]),inc_tr=float(D['inc'][i_tr]),inc_ct=float(D['inc'][i_c]),lat_ct=float(D['lat'][i_c]))

def qc_badge(L,lang):
    """optional (--qc-badge): reliability grade pill on the sources slide, read from <job>/qc.json"""
    if not JC.get('qc_badge'): return
    try: q=json.load(open(SP+'/qc.json'))
    except Exception: return
    gc={'A':YEL,'B':YEL,'C':ORG,'D':ORG}[q['grade']]; x0,x1=(40,330) if LX(lang) else (W-330,W-40)
    L.rrect((x0,100,x1,176),r=20,fill=(8,12,20,200),outline=gc+(255,),width=3)
    L.text(((x0+x1)/2,108),('اطمینان تحلیل: %s'%q['grade']) if LX(lang) else ('Reliability: %s'%q['grade']),w='Black',size=30,fill=gc,anchor='ma',rtl=LX(lang))
    L.text(((x0+x1)/2,144),(num(lang,'%d'%round(q['overall']))+' / '+num(lang,'100')) if LX(lang) else ('%d / 100'%round(q['overall'])),w='Medium',size=22,fill=(190,198,210),anchor='ma',rtl=False)

# ---------- posture timeline (only a side view shows this)
_TL=None
def tl_data():
    global _TL
    if _TL is None:
        from scipy.ndimage import gaussian_filter1d
        ks=np.linspace(0,38,153)
        def ang(a,b,c): u=a-b; v=c-b; return np.degrees(np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1)))
        kf=[180-ang(M.jf('left_hip',k),M.jf('left_knee',k),M.jf('left_ankle',k)) for k in ks]
        kb=[180-ang(M.jf('right_hip',k),M.jf('right_knee',k),M.jf('right_ankle',k)) for k in ks]
        ln=[]; pz=[]
        for k in ks:
            v=M.jf('top_spine',k)-M.jf('bottom_spine',k); ln.append(np.degrees(np.arctan2(v[1],v[2]))); pz.append(M.jf('bottom_spine',k)[2])
        sm=lambda a: gaussian_filter1d(np.array(a),3.0,mode='nearest')
        t=(ks-TC['A'])/30.0*1000
        _TL=dict(ks=ks,t=t,kf=sm(kf),kb=sm(kb),ln=sm(ln),pz=sm(pz))
    return _TL
def slide_timeline(lang,p=1.0,fd=1.0):
    L=Layer(); l=0 if LX(lang) else 1; D=tl_data(); t=D['t']; n=len(t); ie=int(np.clip(round(p*(n-1)),1,n-1))
    title(L,lang,'خط زمانی پوسچر' if LX(lang) else 'Posture timeline','فقط از نمای کنار دیده می‌شود: خمش زانو، شیب تنه، ارتفاع لگن' if LX(lang) else 'Only a side view shows this: knee bend, trunk lean, pelvis height')
    x0,x1=110,870; tmin,tmax=t[0],t[-1]; X=lambda v: x0+(x1-x0)*(v-tmin)/(tmax-tmin)
    ev=[(EV['A']['trophy'],('تروفی','Trophy'),CYA),(EV['A']['low'],('نقطه‌ی پایین','Low'),CYA),(EV['A']['contact'],('تماس','Contact'),YEL),(EV['A']['landing'],('فرود','Landing'),CYA)]
    panels=[('خمش زانو (°)','Knee flexion (°)',[('kf','زانوی جلو','Front knee',YEL),('kb','زانوی عقب','Back knee',ORG)],0,110,[0,30,60,90]),
            ('شیب تنه (°، + رو به جلو)','Trunk lean (°, + forward)',[('ln','شیب تنه','Trunk',CYA)],-20,50,[-20,0,25,50]),
            ('ارتفاع لگن (m)','Pelvis height (m)',[('pz','ارتفاع لگن','Pelvis',WHT)],0.7,1.3,[0.7,0.9,1.1,1.3])]
    y0=380; ph=300; gap=92
    for pi,(fa_t,en_t,ser,lo,hi,ticks) in enumerate(panels):
        ya=y0+pi*(ph+gap); yb=ya+ph; Y=lambda v,ya=ya,lo=lo,hi=hi: ya+ph*(1-(np.clip(v,lo,hi)-lo)/(hi-lo))
        L.rrect((40,ya-8,888,yb+8),r=18,fill=(8,12,20,int(170*fd)))
        tx(L,lang,edge(lang,'start'),ya-74,fa_t if LX(lang) else en_t,w='Bold',size=30,fill=WHT,alpha=fd)
        for tv in ticks:
            yy=Y(tv); L.line([(x0,yy),(x1,yy)],fill=(255,255,255),width=1.5,alpha=0.18*fd)
            L.text((x0-10,yy-14),num(lang,('%g'%tv)),w='Medium',size=22,fill=(190,198,210),anchor='ra',rtl=False,alpha=fd)
        for k_,nm,col in ev:
            xx=X((k_-TC['A'])/30*1000)
            L.line([(xx,ya),(xx,yb)],fill=col,width=2.5,alpha=0.55*fd,dash=(10,8))
            if pi==0: L.text((xx,ya-40),nm[l],w='Bold',size=22,fill=col,anchor='ma',rtl=LX(lang),alpha=fd)
        for si,(key,nf,ne,col) in enumerate(ser):
            pts=[(X(t[i]),Y(D[key][i])) for i in range(ie+1)]; L.line(pts,fill=col,width=6,alpha=fd)
            L.circle(pts[-1],9,fill=col,outline=DRK,width=2,alpha=fd)
            if len(ser)>1:
                yy=ya+14+si*34; lx=x0+24 if not LX(lang) else x1-24
                L.circle((lx,yy+12),7,fill=col,outline=None,alpha=fd)
                L.text((lx+(16 if not LX(lang) else -16),yy),nf if LX(lang) else ne,w='Medium',size=24,fill=col,anchor='la' if not LX(lang) else 'ra',rtl=LX(lang),alpha=fd)
    yl=y0+2*(ph+gap)+ph+26
    for tv in (-1000,-500,0,200):
        L.text((X(tv),yl),num(lang,'%d'%tv),w='Medium',size=22,fill=(190,198,210),anchor='ma',rtl=False,alpha=fd)
    tx(L,lang,edge(lang,'start'),yl+30,'زمان نسبت به تماس (ms)' if LX(lang) else 'Time relative to contact (ms)',w='Medium',size=22,fill=(190,198,210),alpha=fd)
    return L
def timeline_notes():
    D=tl_data(); t=D['t']; i_c=int(np.argmin(abs(t))); pz=D['pz']; i_min=int(np.argmin(pz[:i_c])); rise=(pz[i_c]-pz[i_min])*100
    i_tr=int(np.argmin(abs(D['ks']-EV['A']['trophy']))); return dict(rise=float(rise),lean_tr=float(D['ln'][i_tr]),lean_ct=float(D['ln'][i_c]),t_min=float(t[i_min]))

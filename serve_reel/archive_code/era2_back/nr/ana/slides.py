import sys, numpy as np, cv2
sys.path.insert(0,'/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad/nr/ana')
from overlay import *
def wrap(L,text,wmax,w,size,rtl):
    words=text.split(' '); lines=[]; cur=''
    for t in words:
        nt=(cur+' '+t).strip()
        if L.tw(nt,w,size,rtl=rtl)<=wmax: cur=nt
        else: lines.append(cur); cur=t
    lines.append(cur); return lines
def para(L,lang,y,text,size=30,w='Medium',fill=WHT,wmax=780,x=None,lh=1.55,a=1.0):
    rtl=LX(lang); x=edge(lang,'start') if x is None else x; lines=wrap(L,text,wmax,w,size,rtl)
    for i,l in enumerate(lines): L.text((x,y+i*size*lh),l,w=w,size=size,fill=fill,anchor='ra' if rtl else 'la',rtl=rtl,alpha=a)
    return len(lines)*size*lh
def bullet(L,lang,y,text,col=YEL,size=29,wmax=740):
    x=edge(lang,'start'); dx=-34 if LX(lang) else 34
    L.circle((x+(-10 if LX(lang) else 10),y+size*0.8),7,fill=col,outline=None)
    return para(L,lang,y,text,size=size,x=x+dx*1.0+(-10 if LX(lang) else 10),wmax=wmax)
def title(L,lang,t,sub=None,y=130):
    tx(L,lang,edge(lang,'start'),y,t,w='Black',size=58,fill=YEL,stroke=2)
    if sub: tx(L,lang,edge(lang,'start'),y+82,sub,w='Medium',size=27,fill=(190,198,210))
def _intro0(lang):
    L=Layer(); c=W/2
    if LX(lang):
        L.text((c,640),'تحلیل علمی',w='Black',size=104,fill=YEL,anchor='ma',stroke=3); L.text((c,770),'سرویس تنیس',w='Black',size=104,fill=WHT,anchor='ma',stroke=3)
        L.text((c,1060),'یک سرو فلت در برابر الگوی حرفه‌ای',w='Bold',size=42,fill=WHT,anchor='ma'); L.text((c,1140),'بازسازی سه‌بعدی از ویدیوی تک‌دوربین · مدل ۸ مرحله‌ای',w='Medium',size=27,fill=(190,198,210),anchor='ma')
    else:
        L.text((c,650),'TENNIS SERVE',w='Black',size=96,fill=YEL,anchor='ma',rtl=False,stroke=3); L.text((c,770),'ANALYSIS',w='Black',size=118,fill=WHT,anchor='ma',rtl=False,stroke=3)
        L.text((c,1060),'One flat serve vs. the pro pattern',w='Bold',size=40,fill=WHT,anchor='ma',rtl=False); L.text((c,1140),'Single-camera 3D reconstruction · 8-stage model',w='Medium',size=27,fill=(190,198,210),anchor='ma',rtl=False)
    L.line([(c-120,1010),(c+120,1010)],fill=YEL,width=5); return L
HANDLE='@tennismad.ai'
def handle_pill(L,a=0.92):
    L.rrect((W/2-150,22,W/2+150,74),r=26,fill=(8,12,20,int(120*a))); L.text((W/2,28),HANDLE,w='Bold',size=31,fill=YEL,anchor='ma',rtl=False,alpha=a,stroke=2)
def slide_intro(lang):
    L=_intro0(lang); L.rrect((W/2-250,1250,W/2+250,1340),r=45,fill=(8,12,20,150),outline=YEL+(255,),width=3); L.text((W/2,1262),HANDLE,w='Black',size=54,fill=YEL,anchor='ma',rtl=False,stroke=2); return L
DESC=[('ایستادن، گریپ و اولین انتقال وزن','Stance, grip and the first weight shift'),('توپ بالا و داخل خط لگن جلو پرتاب می‌شود','The toss goes up, inside the lead-hip line'),('زانوها حدود ۶۵° خم می‌شوند؛ پایان در تروفی','Knees flex ≈65°; ends at the trophy position'),('راکت پایین می‌افتد؛ شانه و آرنج کشیده می‌شوند','Racket drops; shoulder and elbow stretch'),('پا، تنه، بازو و راکت پشت‌سرهم شتاب می‌گیرند','Legs, trunk, arm and racket accelerate in sequence'),('بازو تقریباً کشیده (حدود ۳۰° خمش) و تماس در ارتفاع زیاد','Arm nearly straight (≈30° flexion), high contact'),('بازو و شانه آرام می‌شوند','Arm and shoulder slow down'),('فرود متعادل و ورود به داخل زمین','Balanced landing into the court')]
def slide_model(lang,a=1.0,hl=None):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,('الگوی حرفه‌ای سرویس','The professional serve'),None) if False else title(L,lang,'الگوی حرفه‌ای سرویس' if LX(lang) else 'The professional serve','مدل ۸ مرحله‌ای · Kovacs & Ellenbecker' if LX(lang) else '8-stage model · Kovacs & Ellenbecker')
    y=310
    for i in range(8):
        L.rrect((52,y,876,y+118),r=18,fill=(8,12,20,170),outline=(YEL+(255,)) if hl==i else None,width=4)
        cx=edge(lang,'start')+(-44 if LX(lang) else 44)
        L.circle((cx,y+59),30,fill=YEL,outline=None); L.text((cx,y+27),fa(i+1) if LX(lang) else str(i+1),w='Black',size=36,fill=DRK,anchor='ma',rtl=LX(lang))
        tx(L,lang,edge(lang,'start')+(-96 if LX(lang) else 96),y+14,ST['stages'][i][l]+('   '+ST['stages'][i][1] if LX(lang) and False else ''),w='Bold',size=38,fill=YEL)
        para(L,lang,y+64,DESC[i][l],size=27,fill=WHT,x=edge(lang,'start')+(-96 if LX(lang) else 96),wmax=700,lh=1.2)
        y+=130
    return L
ROWS=['knee_front','knee_back','trunk','elbow_low','elbow_ct','tilt','height','speed']
def slide_score(lang):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,'کارنامه‌ی دو سرو' if LX(lang) else 'Scorecard: two serves','هر ردیف: الگوی علمی در برابر اندازه‌گیری' if LX(lang) else 'Each row: scientific pattern vs. measurement')
    # columns x centres (en layout), mirrored for fa
    def cx(x): return W-x if LX(lang) else x
    cols=dict(lab=52,ref=490,s1=665,s2=800)
    if LX(lang): cols=dict(lab=876,ref=W-490,s1=W-665,s2=W-800)
    y=300; hd={'fa':('الگو','سرو ۱','سرو ۲'),'en':('Pro','Serve 1','Serve 2')}[lang]
    for k,t in zip(('ref','s1','s2'),hd): L.text((cols[k]+ (14 if k=='ref' else 0)*0,y),t,w='Bold',size=30,fill=(190,198,210),anchor='ma',rtl=LX(lang))
    y+=56
    for m in ROWS:
        M_=MET[m]; L.rrect((40,y-8,888,y+92),r=16,fill=(8,12,20,170))
        lab=ST['metric'][m][l]; wmax=340; lines=wrap(L,lab,wmax,'Medium',28,LX(lang))
        for i,t in enumerate(lines[:2]): L.text((cols['lab'],y+8+i*34),t,w='Medium',size=28,fill=WHT,anchor='ra' if LX(lang) else 'la',rtl=LX(lang))
        L.text((cols['ref'],y+26),ST['ref'][m][l] ,w='Medium',size=26,fill=(190,198,210),anchor='ma',rtl=False)
        for k,s_ in (('s1','A'),('s2','B')):
            v=M_[s_]; stt=status(m,v); col=YEL if stt=='ok' else ORG; arrow='' if stt=='ok' else ('▲' if stt=='high' else '▼')
            L.text((cols[k],y+6),(num(lang,('%.2f'%v) if m=='height' else ('%g'%v))+('°' if M_['unit']=='°' else '')),w='Black',size=42,fill=col,anchor='ma',rtl=False)
            L.circle((cols[k],y+80),6,fill=col,outline=None)
        y+=108
    L.circle((edge(lang,'start')+(-10 if LX(lang) else 10),y+22),7,fill=YEL,outline=None); tx(L,lang,edge(lang,'start')+(-30 if LX(lang) else 30),y+4,'زرد: داخل محدوده‌ی حرفه‌ای' if LX(lang) else 'Yellow: inside the pro range',w='Medium',size=24,fill=WHT)
    L.circle((edge(lang,'start')+(-10 if LX(lang) else 10),y+62),7,fill=ORG,outline=None); tx(L,lang,edge(lang,'start')+(-30 if LX(lang) else 30),y+44,'نارنجی: خارج از محدوده' if LX(lang) else 'Orange: outside the range',w='Medium',size=24,fill=WHT)
    return L
STR=[('بارگذاری، افت راکت و آرنج داخل محدوده‌ی حرفه‌ای‌اند.','Loading, racket drop and elbow are inside the pro ranges.'),
     ('زنجیره‌ی پا، تنه، بازو، راکت در هر دو سرو مرتب است.','Clean leg, trunk, arm, racket sequence in both serves.'),
     ('پرتاب توپ تکرارپذیر است: اختلاف اوج کمتر از ۱۳ cm.','Repeatable toss: apex differs by less than 13 cm.')]
PRI=[('تماس را بالاتر ببر: حدود ۲٫۵۵ m در برابر حدود ۳٫۰ m.','Contact higher: about 2.55 m vs about 3.0 m.'),
     ('بیشتر به داخل زمین حرکت کن: فرود ۱۵ تا ۳۰ cm پشت خط است.','Drive into the court: landing is 15 to 30 cm behind the line.'),
     ('برای سرو ۲ (کیک) جهش بلندتر و عمق بیشتر هدف بگیر؛ سرعت کمتر طبیعی است.','For serve 2 (kick), aim for a higher bounce and more depth; lower speed is expected.')]
LIMIT=('محدودیت: یک دوربین پشت خط، حدود ۲۰ fps واقعی (زمان فریم‌ها نایکنواخت و اصلاح‌شده)؛ خطای زاویه ±۱۰ تا ۱۵° و سرعت ±۱۰٪. معیارها از مطالعات ناهمگن‌اند و راهنما هستند، نه حکم.','Limits: one camera behind the baseline, about 20 real fps (irregular frame timing, corrected); angle error ±10–15°, speed ±10%. Reference values come from heterogeneous studies: guidance, not norms.')
def slide_verdict(lang,n=7):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,'جمع‌بندی حرفه‌ای' if LX(lang) else 'Professional verdict',None); y=250
    L.rrect((40,y,888,y+470),r=22,fill=(8,12,20,185)); tx(L,lang,edge(lang,'start'),y+24,'نقاط قوت' if LX(lang) else 'Strengths',w='Black',size=40,fill=YEL); yy=y+100
    for k,t in enumerate(STR):
        h=para_h(L,lang,t[l],31,730)+14
        if n>k: bullet(L,lang,yy,t[l],size=31,wmax=730)
        yy+=h+10
    y2=y+500; L.rrect((40,y2,888,y2+520),r=22,fill=(8,12,20,185)); tx(L,lang,edge(lang,'start'),y2+24,'اولویت‌های تمرین' if LX(lang) else 'Training priorities',w='Black',size=40,fill=ORG); yy=y2+100
    for k,t in enumerate(PRI):
        h=para_h(L,lang,t[l],31,730)+14
        if n>3+k: bullet(L,lang,yy,t[l],col=ORG,size=31,wmax=730)
        yy+=h+10
    if n>=7: para(L,lang,1420,LIMIT[l],size=26,fill=(190,198,210),lh=1.45)
    return L
def para_h(L,lang,text,size,wmax,lh=1.55): return len(wrap(L,text,wmax,'Medium',size,LX(lang)))*size*lh
SRCL=[('Frontiers in Sports and Active Living (2024)','Kinematics of key points during the tennis serve — systematic review & meta-analysis (27 studies)'),
      ('Fleisig, Nicholls, Elliott, Escamilla (2003)','Tennis: kinematics used by world-class players to produce high-velocity serves — Sports Biomechanics'),
      ('Kovacs & Ellenbecker (2011)','An 8-stage model for evaluating the tennis serve — Sports Health'),
      ('Greg Ryan — Researching the Serve','TennisPlayer.net: toss, backswing, foot technique'),
      ('TacticalTennis — Serve mechanics: ball toss','Toss placement and contact height of elite servers'),
      ('Göktepe et al. (2009)','Serve kinematics and racket-speed contributions — Joint Dis Relat Surg'),
      ('LTA — Flat, kick & slice: guide to serve spins','Toss, contact and bounce of each serve type'),
      ('Ball toss kinematics of different service types (pros)','Kick: toss peak ≈18–21 cm and contact ≈30–35 cm further left')]
def slide_sources(lang):
    L=Layer(); title(L,lang,'منابع علمی' if LX(lang) else 'Sources',None,y=110); y=225
    for a_,b_ in SRCL:
        L.rrect((40,y,888,y+126),r=16,fill=(8,12,20,170)); L.text((edge(lang,'start'),y+8),a_,w='Bold',size=25,fill=YEL,anchor='ra' if LX(lang) else 'la',rtl=False)
        for i,t in enumerate(wrap(L,b_,800,'Regular',22,False)[:2]): L.text((edge(lang,'start'),y+48+i*31),t,w='Regular',size=22,fill=WHT,anchor='ra' if LX(lang) else 'la',rtl=False)
        y+=136
    L.rrect((40,y+8,888,y+178),r=26,fill=(8,12,20,190),outline=YEL+(255,),width=3)
    L.text((W/2,y+26),'برای تحلیل‌های بیشتر دنبال کنید' if LX(lang) else 'Follow for more serve analysis',w='Bold',size=32,fill=WHT,anchor='ma',rtl=LX(lang))
    L.text((W/2,y+84),HANDLE,w='Black',size=62,fill=YEL,anchor='ma',rtl=False,stroke=2)
    return L
# ---- long-shot comparison
def long_overlay(lang,fr):
    L=Layer(); l=0 if LX(lang) else 1; lg=fr['legend']; fd=fr['fade']
    if lg==0: return L
    tx(L,lang,edge(lang,'start'),118,'مقایسه‌ی دو سرو' if LX(lang) else 'TWO-SERVE COMPARISON',w='Black',size=52,fill=YEL,alpha=fd,stroke=2)
    if lg in (1,2):
        s='A' if lg==1 else 'B'; x=X[s]; L.rrect((36,230,892,230+440),r=22,fill=(8,12,20,int(105*fd))); y=250
        tx(L,lang,edge(lang,'start'),y,('سرو ۱ – فلت' if s=='A' else 'سرو ۲ – کیک') if LX(lang) else ('Serve 1 · Flat' if s=='A' else 'Serve 2 · Kick'),w='Black',size=44,fill=(30,220,255) if s=='A' else (255,107,20),alpha=fd); y+=76
        for m in ('speed','height'): y+=bar_row(L,lang,y,m,s,fd)
        info_row(L,lang,y,'ahead',ST['info']['in_court'][l].format(v=num(lang,'+%d'%x['ahead'])),fd)
    else:
        L.rrect((36,230,892,230+560),r=22,fill=(8,12,20,int(105*fd))); cols=dict(lab=52,s1=520,s2=650,d=790)
        if LX(lang): cols=dict(lab=876,s1=W-520,s2=W-650,d=W-790)
        y=250; hd={'fa':('سرو ۱','سرو ۲','تفاوت'),'en':('Serve 1','Serve 2','Diff')}[lang]
        for k,t,cc in zip(('s1','s2','d'),hd,((30,220,255),(255,107,20),WHT)): L.text((cols[k],y),t,w='Black',size=26,fill=cc,anchor='ma',rtl=LX(lang),alpha=fd)
        y+=56
        rows=[('سرعت توپ','Ball speed','158','140','−18 km/h',True),('ارتفاع تماس','Contact height','2.56','2.52','−4 cm',False),('تماس نسبت به خط پایه','Contact vs baseline','+47','+12','−35 cm',True),('تروفی تا تماس','Trophy to contact','375','460','+85 ms',True),('فرود نسبت به خط','Landing vs baseline','−15','−30','−15 cm',True)]
        for fa_,en_,a_,b_,d_,flag in rows:
            L.rrect((46,y-6,882,y+80),r=14,fill=(255,255,255,int(18*fd)))
            for i,t in enumerate(wrap(L,fa_ if LX(lang) else en_,300,'Medium',25,LX(lang))[:2]): L.text((cols['lab'],y+4+i*30),t,w='Medium',size=25,fill=WHT,anchor='ra' if LX(lang) else 'la',rtl=LX(lang),alpha=fd)
            for k,t in (('s1',a_),('s2',b_)): L.text((cols[k],y+14),num(lang,t),w='Black',size=30,fill=WHT,anchor='ma',rtl=False,alpha=fd)
            L.text((cols['d'],y+14),num(lang,d_),w='Black',size=28,fill=ORG if flag else YEL,anchor='ma',rtl=False,alpha=fd); y+=92
    return L
# ---- serve-type validation (kick vs flat) -----------------------------------------------------------------
# status codes: 'y' matches the kick pattern, 'm' neutral/partial, 'n' does not match, 'u' not measurable
TROWS=[
 (('محل پرتاب (جانبی)','Toss apex, sideways'),('کیک: بالای سر یا کمی چپ‌تر','Kick: over the head, or just left'),('+۴ cm','+4 cm','y'),('−۶ cm','−6 cm','y')),
 (('محل تماس (جانبی)','Contact point, sideways'),('کیک: ۳۰ تا ۳۵ cm چپ‌تر از فلت','Kick: 30–35 cm further left than flat'),('−۲۰ cm','−20 cm','m'),('−۳۲ cm','−32 cm','y')),
 (('حرکت راکت در تماس','Racket motion at contact'),('کیک: برس رو به بالا (۷ تا ۱)','Kick: brush up the ball (7 to 1)'),('رو به بالا','Upward','y'),('رو به بالا','Upward','y')),
 (('عبور از تور','Clearance over the net'),('کیک: بلندتر از فلت','Kick: higher than flat'),('۰٫۴۴ m','0.44 m','n'),('۰٫۶۶ m','0.66 m','m')),
 (('جهش بعد از زمین','Bounce after landing'),('کیک: جهش بلند','Kick: bounces high'),('۱٫۲ m','1.2 m','n'),('داده کافی نیست','Too few frames','u')),
 (('سرعت توپ','Ball speed'),('کیک: کندتر از فلت اول','Kick: slower than a flat first serve'),('۱۵۸ km/h','158 km/h','m'),('۱۴۰ km/h','140 km/h','y')),
]
SCOL={'y':YEL,'m':(190,198,210),'n':ORG,'u':(120,128,140)}
S1C=(30,220,255); S2C=(255,107,20)
VER=(('سرو ۱: فلت — با داده‌ها سازگار است','Serve 1: flat, consistent with the data'),('سرو ۲: کیک — با داده‌ها سازگار است؛ جهش برای تأیید کافی نیست','Serve 2: kick, consistent with the data; the bounce is too short to confirm'))
def slide_stype(lang,n=6,ver=False):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,'اعتبارسنجی نوع سرویس' if LX(lang) else 'Serve-type check','سرو ۱ فلت، سرو ۲ کیک · مقایسه با الگوی مطالعات' if LX(lang) else 'Serve 1 flat, serve 2 kick · vs the literature')
    cx=lambda x:(W-x) if LX(lang) else x; xs1,xs2=cx(640),cx(790)
    y=268; hd=(('سرو ۱','فلت'),('سرو ۲','کیک')) if LX(lang) else (('Serve 1','Flat'),('Serve 2','Kick'))
    for xs,(h1,h2),cc in ((xs1,hd[0],S1C),(xs2,hd[1],S2C)):
        L.text((xs,y),h1,w='Black',size=27,fill=cc,anchor='ma',rtl=LX(lang)); L.text((xs,y+34),h2,w='Bold',size=25,fill=cc,anchor='ma',rtl=LX(lang))
    y+=86
    for k,(lab,pat,a_,b_) in enumerate(TROWS):
        if k<n:
            L.rrect((40,y,888,y+138),r=16,fill=(8,12,20,185)); tx(L,lang,edge(lang,'start'),y+10,lab[l],w='Bold',size=29,fill=WHT)
            for i,t in enumerate(wrap(L,pat[l],440,'Regular',23,LX(lang))[:2]): tx(L,lang,edge(lang,'start'),y+54+i*32,t,w='Regular',size=23,fill=(190,198,210))
            for xs,(vf,ve,st) in ((xs1,a_),(xs2,b_)):
                v=vf if LX(lang) else ve; sz=27 if len(v)<10 else 21
                L.text((xs,y+24),v,w='Black',size=sz,fill=SCOL[st],anchor='ma',rtl=LX(lang) and any('\u0600'<=c<='\u06ff' and not c.isdigit() and c not in '٫' for c in v)); L.circle((xs,y+100),9,fill=SCOL[st],outline=None)
        y+=148
    if ver:
        L.rrect((40,y+6,888,y+290),r=22,fill=(8,12,20,205),outline=YEL+(255,),width=3); yy=y+22
        yy+=para(L,lang,yy,VER[0][l],size=28,w='Bold',fill=S1C,wmax=800,lh=1.4)+14
        yy+=para(L,lang,yy,VER[1][l],size=28,w='Bold',fill=S2C,wmax=800,lh=1.4)+14
        para(L,lang,yy,'زرد: مطابق الگوی کیک · نارنجی: مغایر · خاکستری: نامطمئن. عمق (جلو و عقب) از دوربین پشت زمین قابل‌اعتماد نیست.' if LX(lang) else 'Yellow: matches kick · orange: matches flat · grey: unsure. Depth (forward/back) from a behind-the-baseline camera is unreliable.',size=21,fill=(170,178,190),lh=1.35,wmax=800)
    return L

# =============== IMG_7125: single flat serve =================
def slide_score(lang):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,'کارنامه‌ی سرو' if LX(lang) else 'Scorecard','هر ردیف: الگوی علمی در برابر اندازه‌گیری' if LX(lang) else 'Each row: scientific pattern vs. measurement')
    cols=dict(lab=52,ref=560,s1=775)
    if LX(lang): cols=dict(lab=876,ref=W-560,s1=W-775)
    y=300; hd={'fa':('الگو','سرو'),'en':('Pro','Serve')}[lang]
    for k,t in zip(('ref','s1'),hd): L.text((cols[k],y),t,w='Bold',size=30,fill=(190,198,210),anchor='ma',rtl=LX(lang))
    y+=56
    for m in ROWS:
        M_=MET[m]; L.rrect((40,y-8,888,y+92),r=16,fill=(8,12,20,170))
        lab=ST['metric'][m][l]; lines=wrap(L,lab,400,'Medium',28,LX(lang))
        for i,t in enumerate(lines[:2]): L.text((cols['lab'],y+8+i*34),t,w='Medium',size=28,fill=WHT,anchor='ra' if LX(lang) else 'la',rtl=LX(lang))
        L.text((cols['ref'],y+26),ST['ref'][m][l],w='Medium',size=26,fill=(190,198,210),anchor='ma',rtl=False)
        v=M_['A']; stt=status(m,v); col=YEL if stt=='ok' else ORG
        L.text((cols['s1'],y+6),(num(lang,('%.2f'%v) if m=='height' else ('%g'%v))+('°' if M_['unit']=='°' else '')),w='Black',size=44,fill=col,anchor='ma',rtl=False); L.circle((cols['s1'],y+80),6,fill=col,outline=None)
        y+=108
    L.circle((edge(lang,'start')+(-10 if LX(lang) else 10),y+22),7,fill=YEL,outline=None); tx(L,lang,edge(lang,'start')+(-30 if LX(lang) else 30),y+4,'زرد: داخل محدوده‌ی حرفه‌ای' if LX(lang) else 'Yellow: inside the pro range',w='Medium',size=24,fill=WHT)
    L.circle((edge(lang,'start')+(-10 if LX(lang) else 10),y+62),7,fill=ORG,outline=None); tx(L,lang,edge(lang,'start')+(-30 if LX(lang) else 30),y+44,'نارنجی: خارج از محدوده' if LX(lang) else 'Orange: outside the range',w='Medium',size=24,fill=WHT)
    return L
STR=[('خمش زانوی جلو و عقب (۵۵° و ۷۲°) داخل محدوده‌ی حرفه‌ای است.','Front and back knee flexion (55° and 72°) are inside the pro ranges.'),
     ('بازو هنگام تماس تقریباً کاملاً کشیده است (حدود ۱۱° خمش).','The arm is almost fully extended at contact (about 11° of flexion).'),
     ('شیب شانه‌ها هنگام تماس حدود ۴۳° است؛ نزدیک الگو (حدود ۴۸°).','Shoulder tilt at contact is about 43°, near the pro value (about 48°).')]
PRI=[('تماس را بالاتر ببر: حدود ۲٫۷۴ m در برابر حدود ۳٫۰ m.','Raise the contact point: about 2.74 m vs about 3.0 m.'),
     ('سرعت توپ حدود ۱۲۰ km/h است؛ نخبگان حدود ۱۸۳. آن را با زنجیره‌ی پا، تنه و بازو بساز.','Ball speed is about 120 km/h vs about 183 for elite men. Build it through the leg, trunk and arm chain.'),
     ('در تروفی تنه را بیشتر خم کن: ۷° در برابر حدود ۲۵° (با ویدیوی از کنار تأیید شود).','Tilt the trunk more at the trophy: 7° vs about 25° (confirm with side-on video).')]
TROWS=[
 (('محل پرتاب (جانبی)','Toss apex, sideways'),('کیک: بالای سر یا کمی چپ‌تر','Kick: over the head, or just left'),('+۱۷ cm','+17 cm','n')),
 (('محل تماس (جانبی)','Contact point, sideways'),('کیک: ۳۰ تا ۳۵ cm چپ‌تر از فلت','Kick: 30–35 cm further left than flat'),('+۶ cm','+6 cm','n')),
 (('حرکت راکت در تماس','Racket motion at contact'),('همه‌ی سرو‌ها رو به بالا می‌روند','Every serve rises through contact'),('رو به بالا','Upward','m')),
 (('عبور از تور','Clearance over the net'),('کیک: بلندتر از فلت','Kick: higher than flat'),('۰٫۴۰ m','0.40 m','n')),
 (('جهش بعد از زمین','Bounce after landing'),('کیک: جهش بلند','Kick: bounces high'),('داده کافی نیست','Too few frames','u')),
 (('سرعت توپ','Ball speed'),('کیک: کندتر از فلت اول','Kick: slower than a flat first serve'),('۱۲۰ km/h','120 km/h','m')),
]
VER=(('فلت — توپ‌اندازی، تماس و عبور از تور نشانه‌ی فلت‌اند؛ سرعت کم قطعی نیست','Flat: toss, contact and net clearance point to flat; the low speed is not decisive'),)
def slide_stype(lang,n=6,ver=False):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,'اعتبارسنجی نوع سرویس' if LX(lang) else 'Serve-type check','کیک یا فلت؟ مقایسه با الگوی مطالعات' if LX(lang) else 'Kick or flat? Measured against the literature')
    xs=W-700 if LX(lang) else 700; y=268
    L.text((xs,y),'سرو' if LX(lang) else 'This serve',w='Black',size=27,fill=YEL,anchor='ma',rtl=LX(lang)); y+=60
    for k,(lab,pat,a_) in enumerate(TROWS):
        if k<n:
            L.rrect((40,y,888,y+138),r=16,fill=(8,12,20,185)); tx(L,lang,edge(lang,'start'),y+10,lab[l],w='Bold',size=29,fill=WHT)
            for i,t in enumerate(wrap(L,pat[l],440,'Regular',23,LX(lang))[:2]): tx(L,lang,edge(lang,'start'),y+54+i*32,t,w='Regular',size=23,fill=(190,198,210))
            vf,ve,st=a_; v=vf if LX(lang) else ve; sz=27 if len(v)<10 else 21
            L.text((xs,y+24),v,w='Black',size=sz,fill=SCOL[st],anchor='ma',rtl=LX(lang) and any('\u0600'<=c<='\u06ff' and not c.isdigit() and c not in '٫' for c in v)); L.circle((xs,y+100),9,fill=SCOL[st],outline=None)
        y+=148
    if ver:
        L.rrect((40,y+6,888,y+226),r=22,fill=(8,12,20,205),outline=YEL+(255,),width=3)
        for i,t in enumerate(wrap(L,VER[0][l],800,'Bold',32,LX(lang))[:2]): tx(L,lang,edge(lang,'start'),y+24+i*46,t,w='Bold',size=32,fill=YEL)
        para(L,lang,y+124,'زرد: مطابق کیک · نارنجی: مطابق فلت · خاکستری: نامطمئن؛ عمق (جلو و عقب) از دوربین پشت زمین قابل‌اعتماد نیست.' if LX(lang) else 'Yellow: matches kick · orange: matches flat · grey: unsure. Depth (forward/back) from a behind-the-baseline camera is unreliable.',size=21,fill=(170,178,190),lh=1.35,wmax=800)
    return L
def long_overlay(lang,fr):
    L=Layer(); l=0 if LX(lang) else 1; lg=fr['legend']; fd=fr['fade']
    if lg==0: return L
    tx(L,lang,edge(lang,'start'),118,'مسیر توپ و راکت' if LX(lang) else 'BALL AND RACKET PATHS',w='Black',size=52,fill=YEL,alpha=fd,stroke=2)
    x=X['A']
    if lg==1:
        L.rrect((36,230,892,230+440),r=22,fill=(8,12,20,int(105*fd))); y=250
        for m in ('speed','height'): y+=bar_row(L,lang,y,m,'A',fd)
        info_row(L,lang,y,'ahead',ahead_txt(lang,x['ahead']),fd)
    else:
        L.rrect((36,230,892,230+560),r=22,fill=(8,12,20,int(105*fd))); y=250
        rows=[('سرعت توپ','Ball speed','120 km/h'),('ارتفاع تماس','Contact height','2.74 m'),('عبور از تور','Clearance over the net','0.40 m'),('تماس نسبت به خط پایه','Contact vs baseline','−9 cm'),('تروفی تا تماس','Trophy to contact','429 ms'),('فرود نسبت به خط پایه','Landing vs baseline','+19 cm')]
        for fa_,en_,v in rows:
            L.rrect((46,y-6,882,y+72),r=14,fill=(255,255,255,int(18*fd)))
            for i,t in enumerate(wrap(L,fa_ if LX(lang) else en_,420,'Medium',26,LX(lang))[:2]): L.text((edge(lang,'start'),y+10+i*30),t,w='Medium',size=26,fill=WHT,anchor='ra' if LX(lang) else 'la',rtl=LX(lang),alpha=fd)
            L.text((edge(lang,'end'),y+8),num(lang,v),w='Black',size=34,fill=YEL,anchor='la' if LX(lang) else 'ra',rtl=False,alpha=fd); y+=84
    return L

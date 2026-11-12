import sys, numpy as np, cv2
sys.path.insert(0,'/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad/ana')
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
def slide_intro(lang):
    L=Layer(); c=W/2
    if LX(lang):
        L.text((c,640),'تحلیل علمی',w='Black',size=104,fill=YEL,anchor='ma',stroke=3); L.text((c,770),'سرویس تنیس',w='Black',size=104,fill=WHT,anchor='ma',stroke=3)
        L.text((c,1060),'دو سرو در برابر الگوی حرفه‌ای',w='Bold',size=42,fill=WHT,anchor='ma'); L.text((c,1140),'بازسازی سه‌بعدی از ویدیوی تک‌دوربین · مدل ۸ مرحله‌ای',w='Medium',size=27,fill=(190,198,210),anchor='ma')
    else:
        L.text((c,650),'TENNIS SERVE',w='Black',size=96,fill=YEL,anchor='ma',rtl=False,stroke=3); L.text((c,770),'ANALYSIS',w='Black',size=118,fill=WHT,anchor='ma',rtl=False,stroke=3)
        L.text((c,1060),'Two serves vs. the professional pattern',w='Bold',size=40,fill=WHT,anchor='ma',rtl=False); L.text((c,1140),'Single-camera 3D reconstruction · 8-stage model',w='Medium',size=27,fill=(190,198,210),anchor='ma',rtl=False)
    L.line([(c-120,1010),(c+120,1010)],fill=YEL,width=5); return L
DESC=[('ایستادن، گریپ و اولین انتقال وزن','Stance, grip and the first weight shift'),('توپ بالا و داخل خط لگن جلو پرتاب می‌شود','The toss goes up, inside the lead-hip line'),('زانوها حدود ۶۵° خم می‌شوند؛ پایان در تروفی','Knees flex ≈65°; ends at the trophy position'),('راکت پایین می‌افتد؛ شانه و آرنج کشیده می‌شوند','Racket drops; shoulder and elbow stretch'),('پا، تنه، بازو و راکت پشت‌سرهم شتاب می‌گیرند','Legs, trunk, arm and racket accelerate in sequence'),('بازو تقریباً کشیده (حدود ۳۰° خمش) و تماس در ارتفاع زیاد','Arm nearly straight (≈30° flexion), high contact'),('بازو و شانه آرام می‌شوند','Arm and shoulder slow down'),('فرود متعادل و ورود به داخل زمین','Balanced landing into the court')]
def slide_model(lang,a=1.0):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,('الگوی حرفه‌ای سرویس','The professional serve'),None) if False else title(L,lang,'الگوی حرفه‌ای سرویس' if LX(lang) else 'The professional serve','مدل ۸ مرحله‌ای · Kovacs & Ellenbecker' if LX(lang) else '8-stage model · Kovacs & Ellenbecker')
    y=310
    for i in range(8):
        L.rrect((52,y,876,y+118),r=18,fill=(8,12,20,170))
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
STR=[('بارگذاری، افت راکت و زاویه‌ی آرنج داخل محدوده‌ی منتشرشده‌اند؛ تنه و شانه‌ها درست شیب می‌گیرند.','Loading, racket drop and elbow angle sit inside the published ranges; trunk and shoulders tilt correctly.'),
     ('زنجیره‌ی حرکت (پا، تنه، بازو، راکت) در هر دو سرو مرتب است.','Clean sequencing in both serves: legs, trunk, arm, then racket.'),
     ('پرتاب توپ تکرارپذیر است: اختلاف اوج کمتر از ۱۳ cm و داخل خط لگن جلو.','Repeatable toss: apex within 13 cm, placed inside the lead-hip line.')]
PRI=[('نقطه‌ی تماس را بالاتر ببر: حدود ۲٫۵۵ m در برابر حدود ۳٫۰ m؛ بازو کامل‌تر و پرش بالا و رو به جلو.','Raise the contact point: ≈2.55 m vs ≈3.0 m — fuller extension and an up-and-forward jump.'),
     ('به داخل زمین حرکت کن: فرود ۱۵–۳۰ cm پشت خط است؛ تماس سرو ۲ حدود ۳۵ cm عقب‌تر از سرو ۱ است.','Drive into the court: landing 15–30 cm behind the line; serve 2 is contacted ≈35 cm further back than serve 1.'),
     ('ریتم سرو ۲ را مثل سرو ۱ نگه دار: ۸۵ ms کندتر و ۱۸ km/h آهسته‌تر؛ زانوی سرو ۲ هم عمیق‌تر خم می‌شود.','Keep the rhythm of serve 2 like serve 1: 85 ms slower and 18 km/h less; knees also load deeper.')]
def slide_verdict(lang):
    L=Layer(); l=0 if LX(lang) else 1
    title(L,lang,'جمع‌بندی حرفه‌ای' if LX(lang) else 'Professional verdict',None); y=250
    L.rrect((40,y,888,y+520),r=22,fill=(8,12,20,185)); tx(L,lang,edge(lang,'start'),y+24,'نقاط قوت' if LX(lang) else 'Strengths',w='Black',size=40,fill=YEL); yy=y+100
    for t in STR: yy+=bullet(L,lang,yy,t[l],size=31,wmax=730)+14
    y2=y+550; L.rrect((40,y2,888,y2+610),r=22,fill=(8,12,20,185)); tx(L,lang,edge(lang,'start'),y2+24,'اولویت‌های تمرین' if LX(lang) else 'Training priorities',w='Black',size=40,fill=ORG); yy=y2+100
    for t in PRI: yy+=bullet(L,lang,yy,t[l],col=ORG,size=31,wmax=730)+14
    para(L,lang,1450,('محدودیت: یک دوربین پشت خط، ۳۰ fps؛ خطای زاویه ±۱۰–۱۵° و سرعت ±۱۰٪. معیارها از مطالعات ناهمگن‌اند و راهنما هستند، نه حکم.' if LX(lang) else 'Limits: one camera behind the baseline, 30 fps; angle error ±10–15°, speed ±10%. Reference values come from heterogeneous studies — guidance, not norms.'),size=22,fill=(170,178,190),lh=1.4)
    return L
SRCL=[('Frontiers in Sports and Active Living (2024)','Kinematics of key points during the tennis serve — systematic review & meta-analysis (27 studies)'),
      ('Fleisig, Nicholls, Elliott, Escamilla (2003)','Tennis: kinematics used by world-class players to produce high-velocity serves — Sports Biomechanics'),
      ('Kovacs & Ellenbecker (2011)','An 8-stage model for evaluating the tennis serve — Sports Health'),
      ('Greg Ryan — Researching the Serve','TennisPlayer.net: toss, backswing, foot technique'),
      ('TacticalTennis — Serve mechanics: ball toss','Toss placement and contact height of elite servers'),
      ('Göktepe et al. (2009)','Serve kinematics and racket-speed contributions — Joint Dis Relat Surg')]
def slide_sources(lang):
    L=Layer(); title(L,lang,'منابع علمی' if LX(lang) else 'Sources',None); y=270
    for a_,b_ in SRCL:
        L.rrect((40,y,888,y+190),r=18,fill=(8,12,20,170)); L.text((edge(lang,'start'),y+16),a_,w='Bold',size=30,fill=YEL,anchor='ra' if LX(lang) else 'la',rtl=False)
        for i,t in enumerate(wrap(L,b_,780,'Regular',25,False)[:3]): L.text((edge(lang,'start'),y+66+i*36),t,w='Regular',size=25,fill=WHT,anchor='ra' if LX(lang) else 'la',rtl=False)
        y+=205
    return L
# ---- long-shot comparison
def long_overlay(lang,fr):
    L=Layer(); l=0 if LX(lang) else 1; lg=fr['legend']; fd=fr['fade']
    if lg==0: return L
    tx(L,lang,edge(lang,'start'),118,'مقایسه‌ی دو سرو' if LX(lang) else 'TWO-SERVE COMPARISON',w='Black',size=52,fill=YEL,alpha=fd,stroke=2)
    if lg in (1,2):
        s='A' if lg==1 else 'B'; x=X[s]; L.rrect((36,230,892,230+440),r=22,fill=(8,12,20,int(105*fd))); y=250
        tx(L,lang,edge(lang,'start'),y,('سرو ۱' if s=='A' else 'سرو ۲') if LX(lang) else ('Serve 1' if s=='A' else 'Serve 2'),w='Black',size=44,fill=(30,220,255) if s=='A' else (255,107,20),alpha=fd); y+=76
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

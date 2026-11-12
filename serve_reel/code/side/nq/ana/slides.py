import sys, numpy as np, cv2
sys.path.insert(0,__import__('os').environ['REEL_JOB']+'/nq/ana')
from overlay import *
from autotext import STR,PRI,TROWS,VER,LIMIT
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
        L.text((c,1060),'پوسچر و تکنیک یک سرو از نمای کنار',w='Bold',size=42,fill=WHT,anchor='ma'); L.text((c,1140),'بازسازی سه‌بعدی از ویدیوی تک‌دوربین · مدل ۸ مرحله‌ای',w='Medium',size=27,fill=(190,198,210),anchor='ma')
    else:
        L.text((c,650),'TENNIS SERVE',w='Black',size=96,fill=YEL,anchor='ma',rtl=False,stroke=3); L.text((c,770),'ANALYSIS',w='Black',size=118,fill=WHT,anchor='ma',rtl=False,stroke=3)
        L.text((c,1060),'Side-view posture and technique',w='Bold',size=40,fill=WHT,anchor='ma',rtl=False); L.text((c,1140),'Single-camera 3D reconstruction · 8-stage model',w='Medium',size=27,fill=(190,198,210),anchor='ma',rtl=False)
    L.line([(c-120,1010),(c+120,1010)],fill=YEL,width=5); return L
HANDLE=JC.get('handle','@tennismad.ai')
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
ROWS=['knee_front','knee_back','trunk','elbow_low','elbow_ct','height']
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
    qc_badge(L,lang)
    return L
SCOL={'y':YEL,'m':(190,198,210),'n':ORG,'u':(120,128,140)}
S1C=(30,220,255); S2C=(255,107,20)
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
        para(L,lang,y+124,'زرد: مطابق کیک · نارنجی: مطابق فلت · خاکستری: نامطمئن؛ عمق (نزدیک/دور از دوربین) از نمای کنار قابل‌اعتماد نیست.' if LX(lang) else 'Yellow: matches kick · orange: matches flat · grey: unsure. Depth (toward/away from the camera) from a side view is unreliable.',size=21,fill=(170,178,190),lh=1.35,wmax=800)
    return L
# optional posture-timeline charts (shared file, copied next to this module by reel.py)
import os as _os
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'charts_slide.py')).read())

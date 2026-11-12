import numpy as np, re
from PIL import Image, ImageDraw, ImageFont
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
FD=SP+'/fonts_vz/fonts/ttf/Vazirmatn-'
SS=2                                                             # supersampling of the overlay layer
W,H=928,1696
_fc={}
def font(w,size):
    k=(w,size)
    if k not in _fc: _fc[k]=ImageFont.truetype(FD+w+'.ttf',int(size*SS),layout_engine=ImageFont.Layout.RAQM)
    return _fc[k]
YEL=(255,214,10); CYA=(40,215,255); WHT=(244,246,250); GRY=(150,160,175); ORG=(255,140,40); DRK=(10,14,22); RED=(255,96,96)
def fa(s):
    s=str(s); t=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'); out=''
    # only digits that are not inside latin words
    return s.translate(t).replace('.','٫') if not re.search(r'[A-Za-z]{3,}',s) else re.sub(r'(?<![A-Za-z])\d+(?:\.\d+)?',lambda m:m.group(0).translate(t).replace('.','٫'),s)
class Layer:
    def __init__(s): s.im=Image.new('RGBA',(W*SS,H*SS),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    def px(s,v): return int(round(v*SS))
    def text(s,xy,t,w='Medium',size=34,fill=WHT,anchor='ra',alpha=1.0,rtl=True,stroke=None):
        stroke=2 if stroke is None else stroke
        f=font(w,size); fl=tuple(fill)+(int(255*alpha),)
        kw=dict(direction='rtl',language='fa') if rtl else dict()
        s.d.text((s.px(xy[0]),s.px(xy[1])),t,font=f,fill=fl,anchor=anchor,stroke_width=s.px(stroke),stroke_fill=(0,0,0,int(200*alpha)),**kw)
    def tw(s,t,w,size,rtl=True):
        f=font(w,size); kw=dict(direction='rtl',language='fa') if rtl else dict(); return s.d.textlength(t,font=f,**kw)/SS
    def rrect(s,box,r=18,fill=(10,14,22,190),outline=None,width=2):
        b=[s.px(v) for v in box]; s.d.rounded_rectangle(b,radius=s.px(r),fill=fill,outline=outline,width=s.px(width) if outline else 0)
    def line(s,pts,fill=YEL,width=3,alpha=1.0,dash=None):
        fl=tuple(fill)+(int(255*alpha),); P=[(s.px(x),s.px(y)) for x,y in pts]
        if dash is None: s.d.line(P,fill=fl,width=s.px(width),joint='curve')
        else:
            on,off=dash; acc=0.0; seg=[]; 
            for (x0,y0),(x1,y1) in zip(pts[:-1],pts[1:]):
                L=np.hypot(x1-x0,y1-y0); n=int(L//(on+off))+1
                for i in range(n):
                    a=i*(on+off)/L; b=min((i*(on+off)+on)/L,1.0)
                    if a<1: s.d.line([(s.px(x0+(x1-x0)*a),s.px(y0+(y1-y0)*a)),(s.px(x0+(x1-x0)*b),s.px(y0+(y1-y0)*b))],fill=fl,width=s.px(width))
    def circle(s,c,r,fill=None,outline=YEL,width=3,alpha=1.0):
        b=[s.px(c[0]-r),s.px(c[1]-r),s.px(c[0]+r),s.px(c[1]+r)]; s.d.ellipse(b,fill=(tuple(fill)+(int(255*alpha),)) if fill else None,outline=(tuple(outline)+(int(255*alpha),)) if outline else None,width=s.px(width))
    def poly(s,pts,fill):
        s.d.polygon([(s.px(x),s.px(y)) for x,y in pts],fill=tuple(fill))
    def result(s): return s.im.resize((W,H),Image.LANCZOS)
def composite(base_bgr,layer,alpha=1.0):
    import cv2
    b=Image.fromarray(cv2.cvtColor(base_bgr,cv2.COLOR_BGR2RGB)).convert('RGBA'); o=layer.result()
    if alpha<1.0:
        a=o.getchannel('A').point(lambda v:int(v*alpha)); o.putalpha(a)
    return cv2.cvtColor(np.array(Image.alpha_composite(b,o).convert('RGB')),cv2.COLOR_RGB2BGR)

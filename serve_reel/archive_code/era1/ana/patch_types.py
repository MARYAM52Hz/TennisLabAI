o=open('overlay.py').read()
o=o.replace("def header(L,lang,serve,tau,a=1.0):","TYPE={'A':('فلت','FLAT'),'B':('کیک','KICK')}\ndef header(L,lang,serve,tau,a=1.0):",1)
old="tx(L,lang,s,118,ST['serve'][lang].format(n=1 if serve=='A' else 2) if lang=='en' else ST['serve']['fa'].format(n='۱' if serve=='A' else '۲'),w='Black',size=70,fill=YEL,alpha=a,stroke=2)"
assert old in o
o=o.replace(old,"tx(L,lang,s,118,(ST['serve'][lang].format(n=1 if serve=='A' else 2) if lang=='en' else ST['serve']['fa'].format(n='۱' if serve=='A' else '۲'))+' · '+TYPE[serve][0 if lang=='fa' else 1],w='Black',size=70,fill=YEL,alpha=a,stroke=2)")
old2="(ST['serve'][lang].format(n='۱' if s=='A' else '۲') if LX(lang) else ST['serve'][lang].format(n=1 if s=='A' else 2)),w='Black',size=48"
assert old2 in o
o=o.replace(old2,"(ST['serve'][lang].format(n='۱' if s=='A' else '۲') if LX(lang) else ST['serve'][lang].format(n=1 if s=='A' else 2))+' · '+TYPE[s][0 if LX(lang) else 1],w='Black',size=48")
open('overlay.py','w').write(o)
s=open('slides.py').read()
old3="('سرو ۱' if s=='A' else 'سرو ۲') if LX(lang) else ('Serve 1' if s=='A' else 'Serve 2')"
assert old3 in s
s=s.replace(old3,"('سرو ۱ · فلت' if s=='A' else 'سرو ۲ · کیک') if LX(lang) else ('Serve 1 · Flat' if s=='A' else 'Serve 2 · Kick')")
s=s.replace("'دو سرو در برابر الگوی حرفه‌ای'","'دو سرو (فلت و کیک) در برابر الگوی حرفه‌ای'").replace("'Two serves vs. the professional pattern'","'Two serves (flat and kick) vs. the pro pattern'")
s=s.replace("hd=('سرو ۱','سرو ۲') if LX(lang) else ('Serve 1','Serve 2')","hd=('سرو ۱ · فلت','سرو ۲ · کیک') if LX(lang) else ('Serve 1 · Flat','Serve 2 · Kick')")
i=s.index("VER=(("); j=s.index("\n",i)
s=s[:i]+"VER=(('سرو ۱ = فلت: داده‌ها تأیید می‌کنند؛ جهش بعد از زمین پایین است','Serve 1 = flat: the data agree; the bounce stays low'),('سرو ۲ = کیک: تماس چپ‌تر از سر و سرعت کمتر؛ جهش برای اثبات کافی نیست','Serve 2 = kick: contact left of the head, lower speed; the bounce is too short to prove it'))"+s[j:]
open('slides.py','w').write(s)
print('patched')

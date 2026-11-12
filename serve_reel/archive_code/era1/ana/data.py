# Final measured numbers (reconstruction from CVAT labels + court calibration) and literature benchmarks.
TC={'A':23.26,'B':183.79}
EV={'A':dict(trophy=12.0,low=20.0,contact=23.26,landing=32.0),'B':dict(trophy=170.0,low=181.0,contact=183.79,landing=193.0)}
STAGES=[('شروع','Start'),('رهاسازی توپ','Release'),('بارگذاری پا','Loading'),('افت راکت','Cocking'),('شتاب‌گیری','Acceleration'),('لحظه‌ی تماس','Contact'),('کاهش سرعت','Deceleration'),('پایان حرکت','Finish')]
def stage_of(s,tau):
    e=EV[s]
    if s=='B':
        if tau<150: return 0
        if tau<158: return 1
    if tau<e['trophy']: return 2
    if tau<e['low']: return 3
    if tau<e['contact']-0.45: return 4
    if tau<=e['contact']+0.45: return 5
    if tau<e['landing']: return 6
    return 7
# metric: (label, unit, player A, player B, ref mean, ref sd (None=no band), axis lo, axis hi, ref text, source key)
MET={
 'knee_front':dict(label='خمش زانوی جلو',unit='°',A=72,B=80,mean=64.5,sd=9.7,lo=20,hi=120,ref='۶۴٫۵ ± ۹٫۷°',src='F24'),
 'knee_back':dict(label='خمش زانوی عقب',unit='°',A=83,B=96,mean=67.4,sd=16.4,lo=20,hi=120,ref='۶۷٫۴ ± ۱۶٫۴°',src='F24'),
 'trunk':dict(label='شیب تنه در تروفی',unit='°',A=25,B=21,mean=25.0,sd=7.1,lo=0,hi=50,ref='۲۵ ± ۷٫۱°',src='F24'),
 'elbow_low':dict(label='خمش آرنج در پایین‌ترین نقطه‌ی راکت',unit='°',A=108,B=120,mean=104,sd=17,lo=60,hi=150,ref='≈ ۱۰۴° (المپیک سیدنی)',src='FL03'),
 'elbow_ct':dict(label='خمش آرنج هنگام تماس',unit='°',A=35,B=33,mean=30.1,sd=15.9,lo=0,hi=90,ref='۳۰٫۱ ± ۱۵٫۹°',src='F24'),
 'tilt':dict(label='شیب خط شانه‌ها هنگام تماس',unit='°',A=45,B=45,mean=48,sd=8,lo=20,hi=70,ref='≈ ۴۸° (المپیک سیدنی)',src='FL03'),
 'height':dict(label='ارتفاع نقطه‌ی تماس',unit=' m',A=2.56,B=2.52,mean=3.0,sd=0.12,lo=2.2,hi=3.3,ref='نخبگان ≈ ۳٫۰ m',src='TT'),
 'speed':dict(label='سرعت توپ پس از تماس',unit=' km/h',A=158,B=140,mean=183,sd=None,lo=100,hi=200,ref='مردان المپیک ≈ ۱۸۳ km/h',src='FL03'),
}
# --- the two serves, extra numbers
X={
 'A':dict(t_tc=375,t_low=109,ahead=47,landing=-15,rise=43,toss_apex=3.55,toss_x=22,toss_y=14,drop=0.99,chain='پا → تنه → آرنج → راکت'),
 'B':dict(t_tc=460,t_low=93,ahead=12,landing=-30,rise=39,toss_apex=3.68,toss_x=28,toss_y=26,drop=1.16,chain='پا → تنه → آرنج → راکت'),
}
def status(m,v):
    M=MET[m]
    if M['sd'] is None: return 'low' if v<M['mean']*0.9 else 'ok'
    z=(v-M['mean'])/M['sd']
    if abs(z)<=1.0: return 'ok'
    return 'high' if z>0 else 'low'
SRC={'F24':'Frontiers 2024 — متاآنالیز ۲۷ مطالعه','FL03':'Fleisig و همکاران 2003 — المپیک سیدنی','TT':'تحلیل مربی‌ها: فدرر/کیریوس (≈۳ m)','KE':'Kovacs & Ellenbecker — مدل ۸ مرحله‌ای'}

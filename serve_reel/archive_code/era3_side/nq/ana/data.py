# IMG_7122 single serve (side view): measured numbers (reconstruction from CVAT labels, scale from the player) and literature benchmarks. Times are in unique-frame units (1/30 s).
TC={'A':32.0}
EV={'A':dict(trophy=20.0,low=27.0,contact=32.0,landing=38.0)}
STAGES=[('شروع','Start'),('رهاسازی توپ','Release'),('بارگذاری پا','Loading'),('افت راکت','Cocking'),('شتاب‌گیری','Acceleration'),('لحظه‌ی تماس','Contact'),('کاهش سرعت','Deceleration'),('پایان حرکت','Finish')]
def stage_of(s,tau):
    e=EV['A']
    if tau<2.0: return 0
    if tau<7.0: return 1
    if tau<e['trophy']: return 2
    if tau<e['low']: return 3
    if tau<e['contact']-0.45: return 4
    if tau<=e['contact']+0.45: return 5
    if tau<e['landing']: return 6
    return 7
MET={
 'knee_front':dict(label='خمش زانوی جلو',unit='°',A=69,B=69,mean=64.5,sd=9.7,lo=20,hi=120,ref='۶۴٫۵ ± ۹٫۷°',src='F24'),
 'knee_back':dict(label='خمش زانوی عقب',unit='°',A=36,B=36,mean=67.4,sd=16.4,lo=20,hi=120,ref='۶۷٫۴ ± ۱۶٫۴°',src='F24'),
 'trunk':dict(label='شیب تنه در تروفی',unit='°',A=11,B=11,mean=25.0,sd=7.1,lo=0,hi=50,ref='۲۵ ± ۷٫۱°',src='F24'),
 'elbow_low':dict(label='خمش آرنج در پایین‌ترین نقطه‌ی راکت',unit='°',A=95,B=95,mean=104,sd=17,lo=60,hi=150,ref='≈ ۱۰۴° (المپیک سیدنی)',src='FL03'),
 'elbow_ct':dict(label='خمش آرنج هنگام تماس',unit='°',A=18,B=18,mean=30.1,sd=15.9,lo=0,hi=90,ref='۳۰٫۱ ± ۱۵٫۹°',src='F24'),
 'height':dict(label='ارتفاع نقطه‌ی تماس',unit=' m',A=2.77,B=2.77,mean=3.0,sd=0.12,lo=2.2,hi=3.3,ref='نخبگان ≈ ۳٫۰ m',src='TT'),
}
X={'A':dict(t_tc=433,t_low=167,ahead=15,landing=44,rise=0,toss_apex=3.26,lean=14,chain='پا → تنه → آرنج → راکت')}
def status(m,v):
    M=MET[m]
    if M['sd'] is None: return 'low' if v<M['mean']*0.9 else 'ok'
    z=(v-M['mean'])/M['sd']
    if abs(z)<=1.0: return 'ok'
    return 'high' if z>0 else 'low'
SRC={}

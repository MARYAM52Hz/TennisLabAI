# bilingual text: every entry is {'fa':..., 'en':...}
ST={
 'stages':[('شروع','Start'),('رهاسازی توپ','Release'),('بارگذاری پا','Loading'),('افت راکت','Cocking'),('شتاب‌گیری','Acceleration'),('لحظه‌ی تماس','Contact'),('کاهش سرعت','Deceleration'),('پایان حرکت','Finish')],
 'sub':{'fa':'تحلیل بیومکانیکی · مدل ۸ مرحله‌ای','en':'BIOMECHANICS · 8-STAGE MODEL'},
 'serve':{'fa':'سرو {n}','en':'SERVE {n}'},
 'stage_lbl':{'fa':'مرحله','en':'Stage'},
 'metric':{
  'knee_front':('خمش زانوی جلو','Front-knee flexion'),
  'knee_back':('خمش زانوی عقب','Back-knee flexion'),
  'trunk':('شیب تنه در تروفی','Trunk inclination at trophy'),
  'elbow_low':('خمش آرنج در پایین‌ترین نقطه‌ی راکت','Elbow flexion at racket low point'),
  'elbow_ct':('خمش آرنج هنگام تماس','Elbow flexion at contact'),
  'tilt':('شیب خط شانه‌ها هنگام تماس','Shoulder-line tilt at contact'),
  'height':('ارتفاع نقطه‌ی تماس','Contact height'),
  'speed':('سرعت توپ پس از تماس','Ball speed after contact')},
 'ref':{
  'knee_front':('۶۴٫۵ ± ۹٫۷°','64.5 ± 9.7°'),'knee_back':('۶۷٫۴ ± ۱۶٫۴°','67.4 ± 16.4°'),'trunk':('۲۵ ± ۷٫۱°','25 ± 7.1°'),
  'elbow_low':('≈ ۱۰۴°','≈ 104°'),'elbow_ct':('۳۰٫۱ ± ۱۵٫۹°','30.1 ± 15.9°'),'tilt':('≈ ۴۸°','≈ 48°'),
  'height':('≈ ۳٫۰ m','≈ 3.0 m'),'speed':('≈ ۱۸۳ km/h','≈ 183 km/h')},
 'refl':{'height':('نخبگان','Elite'),'speed':('مردان المپیک','Olympic men')},
 'status':{'ok':('در محدوده‌ی حرفه‌ای','In pro range'),'high':('بالاتر از الگو','Above pro range'),'low':('پایین‌تر از الگو','Below pro range')},
 'ref_lbl':{'fa':'الگو','en':'Pro'},
 'cap':{'fa':'اندازه‌گیری از ویدیوی تک‌دوربین از کنار · خطای زوایا ±۱۰–۱۵°','en':'Single side-view camera · angle error ±10–15°'},
 # freeze titles
 'kp':{'trophy':(('نقطه‌ی کلیدی ۱ · تروفی','Key position 1 · Trophy'),('پایان بارگذاری: زانوها خم، بازوی توپ‌انداز بالا','End of loading: knees flexed, tossing arm up')),
       'low':(('نقطه‌ی کلیدی ۲ · پایین‌ترین نقطه‌ی راکت','Key position 2 · Racket low point'),('ذخیره‌ی کشسانی در شانه و آرنج پیش از شتاب','Elastic stretch in shoulder and elbow before acceleration')),
       'contact':(('نقطه‌ی کلیدی ۳ · لحظه‌ی تماس','Key position 3 · Contact'),('بازوی تقریباً کشیده و توپ در بالاترین نقطه‌ی دسترس','Arm almost straight, ball at the top of the reach'))},
 'info':{
  'low_t':('زمان تا تماس','Time to contact'),'tc_t':('تروفی تا تماس','Trophy to contact'),'ahead':('تماس نسبت به خط پایه','Contact vs baseline'),
  'in_court':('{v} cm داخل زمین','{v} cm inside the court'),'ms':'ms','chain':('زنجیره‌ی حرکت','Kinetic chain'),
  'chain_v':('پا → تنه → آرنج → راکت','Legs → trunk → elbow → racket'),'tc_t':('تروفی تا تماس','Trophy to contact'),'land':('فرود نسبت به خط پایه','Landing vs baseline'),
  'behind':('{v} cm عقب‌تر از خط','{v} cm behind the line'),'toss':('اوج پرتاب توپ','Toss apex'),'toss_pos':('محل پرتاب','Toss placement'),
  'toss_pos_v':('داخل خط لگن جلو','Inside the lead-hip line')},
}

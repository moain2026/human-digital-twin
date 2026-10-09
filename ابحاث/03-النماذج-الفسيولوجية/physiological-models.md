# النماذج الفسيولوجية للجسم البشري
## Physiological Models for Human Digital Twin

---

## 1. نماذج الجسم الكامل (Whole-Body Models)

### أ) BioGears Engine
- **النوع:** مفتوح المصدر، C++
- **الموقع الرسمي:** https://www.biogearsengine.com/
- **SimTK:** https://simtk.org/projects/biogears
- **الورقة البحثية:** https://www.theoj.org/joss-papers/joss.02645/10.21105.joss.02645.pdf
- **ARA:** https://www.ara.com/biogears/
- **الوصف:** محرك محاكاة شاملة لجسم الإنسان الكامل. يُغطي: القلب والأوعية الدموية، الجهاز التنفسي، الجهاز الهضمي، الغدد الصماء، الجهاز العصبي، التمثيل الغذائي، الكلى، وأكثر.
- **الاستخدام:** تعليم طبي، أبحاث، محاكاة تدخلات علاجية.
- **الترخيص:** Apache 2.0 (حر تمامًا)
- **الميزة:** يعمل في الوقت الفعلي (Real-Time) — نادر في النماذج الشاملة.

### ب) Pulse Physiology Engine
- **الموقع:** https://www.kitware.com/introducing-the-pulse-physiology-engine-open-source-computational-models-for-human-medical-simulation/
- **الورقة:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4106696
- **الوصف:** تطور لنفس قاعدة BioGears، طُوّر بواسطة Kitware. يشمل نماذج بالغين. مقارنة موضوعية مع BioGears وHumMod وMuse متاحة في الرابط أعلاه.
- **GitHub:** https://github.com/BioGearsEngine/core

### ج) HumMod
- **الموقع الرسمي:** https://hummod.org/origin-story/
- **الوصف:** امتداد لنموذج Guyton الشهير (1972) لتنظيم الدورة الدموية الكاملة. يُعالج التوازن الهرموني، ضغط الدم المزمن، دور الكلى. الأكثر دقة في محاكاة التوازن الكلوي والضغط.
- **الورقة المرجعية:** https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002571
- **القيد:** واجهة قديمة، تكامل محدود مع بيانات حديثة.

### د) نموذج Guyton الأصلي
- **نُشر:** 1972، جُدِّد بشكل مستمر
- **يغطي:** تنظيم ضغط الدم، حجم الدم، وظيفة الكلى، دور الجهاز العصبي اللاإرادي
- **الأهمية التاريخية:** أساس كل نماذج الجسم الكامل الحديثة

---

## 2. نماذج التمثيل الغذائي والجلوكوز

### أ) Bergman Minimal Model
- **تاريخ:** 1979 (Bergman & Cobelli)
- **الورقة:** https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2020.583016/full
- **الوصف:** أبسط وأشهر نموذج لتفاعل الجلوكوز والأنسولين. يُقدر مقاومة الأنسولين وحساسية الخلايا.
- **الإنجاز:** أول نموذج يقبله FDA كبديل عن التجارب الحيوانية في محاكاة الجلوكوز.

### ب) Dalla Man Model / UVa-PADOVA Simulator
- **النوع:** محاكي السكري نوع 1 — معتمد من FDA
- **الورقة:** https://journals.sagepub.com/doi/abs/10.1177/19322968211015268 (Cobelli 2022)
- **الأهمية:** المعيار الذهبي لاختبار أنظمة ضخ الأنسولين المغلقة الحلقة
- **المحاكاة:** ديناميكا الجلوكوز-الأنسولين، امتصاص الطعام، التمثيل الغذائي في الأعضاء

### ج) Twin Health Digital Twin (الجلوكوز التجاري)
- **الموقع:** https://usa.twinhealth.com/
- **الورقة (NEJM):** https://usa.twinhealth.com/resources/cleveland-clinic-study
- **النتيجة المُحكَّمة (2024):** 71% من المشتركين حققوا A1C < 6.5% مع التوقف عن الأدوية
- **الرابط PMC:** https://pmc.ncbi.nlm.nih.gov/articles/PMC11513986/

### د) Harvey/Harvetta — النموذج الاستقلابي الكامل
- **الباحث:** Ines Thiele وفريقها (University of Galway / Luxembourg)
- **الورقة:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7285886/ (PMC, Cited 254)
- **phys.org:** https://phys.org/news/2020-06-virtual-metabolic-humans-harvey-harvetta.html
- **الوصف:** نموذج استقلابي كامل للإنسان (ذكر وأنثى) قائم على Flux Balance Analysis. يُغطي التفاعلات في جميع الأعضاء والأنسجة. يمكن تخصيصه بالجينوم والنظام الغذائي.
- **PNAS (2026):** https://www.pnas.org/doi/10.1073/pnas.2516511123

---

## 3. نماذج القلب والأوعية الدموية

### أ) Living Heart Project (Dassault Systèmes)
- **الموقع:** https://www.3ds.com/industries/life-sciences-healthcare/living-heart-project
- **IEEE:** https://spectrum.ieee.org/living-heart-project-virtual-twins
- **الوصف:** أول نموذج فيزيائي ثلاثي الأبعاد للقلب البشري (قائم على العناصر المحدودة FEA). أُطلق 2014. يُستخدم لمحاكاة الأجهزة القلبية وتخطيط الجراحة.

### ب) Siemens Healthineers — Patient Twin
- **الموقع:** https://www.siemens-healthineers.com/perspectives/patient-twin-johns-heart
- **الوصف:** سيناريو مستقبلي لتوأم مريض يكتشف ويحتوي أمراض القلب الوعائية مبكرًا.

### ج) HeartFlow
- **الوصف:** توأم رقمي للشريان التاجي يُنشأ من صور CT لحساب FFR (كسر الاحتياطي الدوراني) — مُعتمد FDA
- **الموقع:** https://www.heartflow.com/

### د) CellML Models — Heart
- **مستودع:** https://models.physiomeproject.org/
- **الوصف:** مئات النماذج الرياضية لخلايا القلب والأوعية مكتوبة بـ CellML

---

## 4. نماذج ضغط الدم والكلى

- **HumMod** (ذُكر أعلاه) — الأقوى في هذا المجال
- **Hall's Body Weight Regulatory Model:** يُغطي تنظيم الوزن وضغط الدم على المدى الطويل (مستوحى من أبحاث Guyton/Hall)
- **CVSim:** محاكي بسيط مفتوح المصدر لنظام القلب والأوعية الدموية

---

## 5. نماذج الكبد والدواء

- **BioGears** يتضمن نموذج الكبد للتمثيل الغذائي الدوائي
- **Hepatokinetics Models:** نماذج PBPK خاصة بالكبد (GastroPlus، Simcyp)
- **Virtual Liver Network (VLN):** مشروع ألماني لنمذجة الكبد

---

## 6. المعادلات الأساسية في النمذجة

### PBPK (الجزء الكبدي):
```
dC_liver/dt = Q_liver*(C_art - C_liver/Kp) - CL_int * C_liver/Kp
```

### Bergman Minimal Model:
```
dG/dt = -(Sg + X)*G + Sg*Gb + D(t)
dX/dt = -p2*X + p3*(I - Ib)
dI/dt = -n*(I - Ib) + γ*(G - h)*t  [إذا G > h]
```

حيث: G = جلوكوز، I = أنسولين، X = تأثير الأنسولين على الجلوكوز


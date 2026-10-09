# أدوات محاكاة الأدوية — PBPK / QSP / ADMET
## Drug Simulation Tools for Human Digital Twin

---

## 1. ما هو PBPK؟

**Physiologically Based Pharmacokinetics** — نمذجة حركة الدواء الفسيولوجية:
يُحاكي كيف يمتص الجسم الدواء، ويوزعه، ويستقلبه، ويُخرجه (ADME) عبر محاكاة فسيولوجية واقعية لكل عضو.

**التطبيق على مشروعنا:**
- ماذا يحدث لمادة طبيعية (كركم، زنجبيل، ثمرة نيجيلا...) عند دخولها الجسم؟
- كيف تتوزع على الأعضاء؟
- أي عضو يُمثّلها أكثر؟
- هل تتفاعل مع أدوية أخرى؟

---

## 2. أدوات PBPK التجارية

### أ) Simcyp (Certara)
- **الموقع:** https://www.certara.com/software/simcyp-pbpk/
- **الوصف:** المنصة الأكثر اعتمادًا في الصناعة الدوائية لنمذجة PBPK. تدعم:
  - نمذجة التفاعلات الدوائية (DDI)
  - السكان الافتراضيين (Virtual Populations)
  - المرضى بأمراض مزمنة (كبد، كلى، قلب)
  - مجموعات خاصة (حوامل، أطفال، كبار)
- **الاعتماد التنظيمي:** مقبول من FDA وEMA في الملفات التنظيمية
- **للمواد الطبيعية:** يمكن إدخال خصائص المادة الطبيعية وتشغيل محاكاة كاملة

### ب) GastroPlus (Simulations Plus)
- **الموقع:** https://www.simulations-plus.com/software/gastroplus/
- **الوصف:** متخصص في امتصاص الأدوية عبر الجهاز الهضمي. الأقوى في محاكاة:
  - تأثير الغذاء على امتصاص الدواء
  - نماذج الامتصاص المعوي
  - صياغات الجرعة المعقدة
- **موقع FDA:** https://www.fda.gov/about-fda/cder-offices-and-divisions/program-physiologically-based-pharmacokinetic-and-pharmacodynamic-modeling-pbpk-program

### ج) PK-Sim / MoBi (Open Systems Pharmacology - مفتوح المصدر)
- **مشروع:** Open Systems Pharmacology Suite
- **الموقع:** https://www.open-systems-pharmacology.org/
- **GitHub:** https://github.com/Open-Systems-Pharmacology
- **المميزة:** مجاني تمامًا، مفتوح المصدر، تدعمه Bayer ومنظمات أكاديمية
- **يشمل:** PK-Sim (بناء النماذج) + MoBi (نمذجة الأنظمة البيولوجية)

---

## 3. ما هو QSP؟

**Quantitative Systems Pharmacology** — يُضيف على PBPK فهمًا ميكانيكيًا لكيف يُحدث الدواء أثره البيولوجي:
- نمذجة مسارات الإشارة الخلوية
- ديناميكا جهاز المناعة
- استجابة الورم للعلاج
- تأثيرات متعددة الأهداف (للمواد الطبيعية التي تؤثر على أهداف متعددة)

**أدوات QSP:**
- **NONMEM** — صناعي، معيار محاسبة PK/PD
- **Monolix** — تجاري
- **COPASI** — مفتوح المصدر: https://copasi.org/
- **Nova In Silico:** https://novainsilico.ai/ (QSP للتجارب السريرية)

---

## 4. أدوات ADMET (التنبؤ بخصائص الجزيء)

### أ) admetSAR 2.0
- **الموقع:** http://lmmd.ecust.edu.cn/admetsar2/
- **الوصف:** يتنبأ بـ 47 خاصية ADMET لأي جزيء كيميائي
- **مجاني:** نعم

### ب) SwissTargetPrediction
- **الموقع:** http://www.swisstargetprediction.ch/
- **الوصف:** يتنبأ بأهداف بروتينية لأي جزيء (مفيد لمعرفة أين تعمل المادة الطبيعية في الجسم)
- **مجاني:** نعم

### ج) SwissADME
- **الموقع:** http://www.swissadme.ch/
- **الوصف:** حساب خصائص ADME، drug-likeness، قواعد Lipinski

### د) ProTox 3.0
- **الموقع:** https://tox.charite.de/
- **الوصف:** توقع سمية الجرعة الدنيا المميتة (LD50) + 40 نوعًا من السمية
- **مجاني:** نعم

### هـ) Tox21 / DSSTox (EPA)
- **الموقع:** https://tox21.gov/
- **الوصف:** قاعدة بيانات حكومية أمريكية لسمية آلاف المواد

### و) OECD QSAR Toolbox
- **الموقع:** https://www.qsartoolbox.org/
- **مجاني:** نعم، من منظمة OECD

---

## 5. أدوات نمذجة التفاعل بين المواد

### أ) DrugBank Interactions
- **الموقع:** https://go.drugbank.com/drug-interaction-checker
- **الوصف:** قاعدة بيانات شاملة للتفاعلات الدوائية، تشمل بعض المواد الطبيعية

### ب) Natural Medicines Database
- **الموقع:** https://naturalmedicines.therapeuticresearch.com/
- **الوصف:** مصدر موثوق للتفاعلات بين المواد الطبيعية والأدوية (اشتراك مدفوع)

### ج) NatMedWeb
- بحث عن التفاعلات الطبيعية-الدوائية عبر قواعد موثقة

---

## 6. مثال تطبيقي: PBPK لمادة طبيعية

**مثال:** نمذجة Curcumin (الكركمين) في PBPK:

الدراسة: https://www.semanticscholar.org/paper/8b828ab34b7146eeadb024f60432cddc8124121c
- نُمذج الكركمين وكيف يُسبب تفاعلات مع أدوية CDK inhibitors
- استخدام Molecular Dynamics + PBPK

**مثال آخر:** Piperine (الفلفل الأسود):
- الورقة: https://www.mdpi.com/1422-0067/25/20/10955 (Cited 27)
- بنى نموذج PBPK للبيبيرين، وتنبأ بتفاعلات دوائية-غذائية

---

## 7. MIDD — نمذجة-مُعلِّمة لتطوير الأدوية

**FDA MIDD Program:**
- الموقع: https://www.fda.gov/drugs/development-resources/model-informed-drug-development-paired-meeting-program
- يتيح للشركات استخدام النماذج الحاسوبية في ملفات تنظيمية للأدوية
- **2024:** أصدرت FDA توجيهًا نهائيًا لـ MIDD — https://www.linkedin.com/posts/fda_today-fda-announced-the-availability-of-activity-7467939017817395200-UCxA

---

## 8. ورقة شاملة: PBPK للمواد الطبيعية

- **Jia et al. (2022)** — "Utilization of PBPK Modeling in Natural Medicine"
  - PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9782767/ (Cited 16)
  - نهج PBPK كأداة جديدة وفعالة لدراسة حركية الأدوية العشبية

- **Chou et al. (2025)** — "Application of PBPK Modeling"
  - Springer: https://link.springer.com/article/10.1007/s40495-025-00427-w (Cited 37)
  - تحسين الجرعة، التنبؤ بتفاعلات الدواء-الدواء، دعم القرارات


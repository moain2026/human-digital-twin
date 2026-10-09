# المعايير التقنية والتنظيمية وقواعد البيانات
## Standards, Regulations & Datasets for Human Digital Twin

---

## 1. المعايير التنظيمية

### أ) FDA — Model-Informed Drug Development (MIDD)
- **البرنامج:** https://www.fda.gov/drugs/development-resources/model-informed-drug-development-paired-meeting-program
- **PDF الذكاء الاصطناعي والتعلم الآلي في FDA:** https://www.fda.gov/media/167973/download
- **توجيه 2024 (نهائي):** https://www.linkedin.com/posts/fda_today-fda-announced-the-availability-of-activity-7467939017817395200-UCxA
- **Applied Clinical Trials:** https://www.appliedclinicaltrialsonline.com/view/understanding-fda-ema-guidance-ai-digital-twin-applications-trials
- **الوصف:** الإطار الذي يسمح باستخدام نماذج PBPK وQSP والتوائم الرقمية في ملفات الأدوية التنظيمية

### ب) ASME V&V40 — التحقق والتصديق للنماذج الطبية الحاسوبية
- **المعيار:** ASME V&V 40-2018 "Assessing Credibility of Computational Modeling through Verification and Validation"
- **الأهمية:** المعيار الذهبي لإثبات موثوقية النماذج الحاسوبية للأجهزة الطبية
- **الجهة:** American Society of Mechanical Engineers

### ج) ISO/IEC 30173 — معيار التوأم الرقمي
- **المعيار:** ISO/IEC 30173:2023 — Digital Twin Concepts and Terminology
- **الأهمية:** يُحدد مصطلحات ومفاهيم التوأم الرقمي بشكل موحد دوليًا

### د) EMA (وكالة الدواء الأوروبية)
- **الرابط:** https://globalforum.diaglobal.org/issue/november-2024/virtual-patients-real-results-how-digital-twins-are-reshaping-drug-development/
- EMA تعمل على سياسات واضحة لقبول التوائم الرقمية في تقديمات الأدوية

---

## 2. معايير تبادل البيانات والقياسات

### أ) HL7 FHIR (Fast Healthcare Interoperability Resources)
- **الموقع:** https://hl7.org/fhir/overview.html
- **الوصف:** معيار تبادل البيانات الصحية الإلكترونية — يُستخدم لمشاركة بيانات المريض بين أنظمة مختلفة
- **الأهمية للتوأم:** تغذية التوأم الرقمي بالبيانات الطبية من السجلات الإلكترونية
- **PMC:** https://pubmed.ncbi.nlm.nih.gov/42394091/ (Abedian 2026 — FHIR Compliant Digital Twin)

### ب) SBML (Systems Biology Markup Language)
- **الموقع:** https://sbml.org/
- **الوصف:** لغة XML لوصف النماذج البيوكيميائية — يدعمها COPASI وكثير من أدوات المحاكاة
- **PMR:** الفيزيوم يستخدم CellML (مشابه لـ SBML)

### ج) CellML
- **الموقع:** https://www.cellml.org/
- **الوصف:** لغة لوصف النماذج الفسيولوجية الرياضية (كل نماذج PMR)

### د) openEHR
- **الوصف:** معيار لبنية السجل الصحي الإلكتروني — يدعم التوثيق الدقيق للبيانات الطبية

### هـ) OMOP CDM (Common Data Model)
- **من:** OHDSI (Observational Health Data Sciences and Informatics)
- **الموقع:** https://ohdsi.org/
- **الاستخدام:** توحيد قواعد البيانات الصحية الضخمة لإجراء دراسات مقارنة

---

## 3. قواعد البيانات الصحية الكبرى (للتدريب والتحقق)

### أ) MIMIC-IV
- **الموقع:** https://physionet.org/content/mimiciv/ (Johnson et al., Cited 794)
- **الوصف:** قاعدة بيانات مجانية لأكثر من 65,000 مريض ICU و200,000 مريض طارئ
- **البيانات:** علامات حيوية، سجلات طبية، نتائج مختبرية، أدوية، إجراءات

### ب) PhysioNet
- **الموقع:** https://physionet.org/
- **الوصف:** أكبر مستودع مفتوح للبيانات الفسيولوجية السريرية
- **يشمل:** إشارات ECG، EEG، الجلوكوز، الضغط، بيانات متعددة الوسائط

### ج) UK Biobank
- **الموقع:** https://www.ukbiobank.ac.uk/
- **الوصف:** 500,000 مشارك بريطاني — بيانات جينوم، تصوير، مختبر، وعادات حياة
- **GenetiQ Digital Twin:** https://www.ukbiobank.ac.uk/projects/genetiq_-digital-twin-platform/

### د) NHANES (National Health and Nutrition Examination Survey)
- **الموقع:** https://www.cdc.gov/nchs/nhanes/
- **الوصف:** بيانات صحية وتغذوية ممثلة لسكان الولايات المتحدة
- **مجاني:** نعم

### هـ) All of Us Research Program (NIH)
- **الموقع:** https://allofus.nih.gov/
- **الوصف:** مليون مشارك أمريكي — جينوم، EHR، نشاط يومي، بيئة

### و) eICU Collaborative Research Database
- **الموقع:** https://physionet.org/content/eicu-crd/
- **الوصف:** 200,000 دخول لوحدات العناية المركزة

### ز) Open Targets
- **الموقع:** https://www.opentargets.org/
- **الوصف:** ربط الجينات بالأمراض والأدوية — مفيد لـ Network Pharmacology

---

## 4. بيانات الأجهزة القابلة للارتداء

| الجهاز | البيانات المُولَّدة | الأهمية للتوأم |
|--------|-----------------|--------------|
| Continuous Glucose Monitor (CGM) | جلوكوز كل 5 دقائق | محور التوأم الاستقلابي |
| Apple Watch / Fitbit | معدل قلب، نشاط، نوم، SpO2 | تغذية مستمرة للتوأم |
| Withings BP Monitor | ضغط الدم | متابعة القلب والأوعية |
| Oura Ring | نوم، HRV، درجة حرارة | صحة استقلابية |
| ECG مكتبي/محمول | إشارة كهرباء القلب | توأم القلب |

---

## 5. الفجوة الحالية في التنظيم

وفق العلماء والمراجعات:
1. لا يوجد حتى الآن تعريف تنظيمي موحد للتوأم الرقمي الطبي
2. FDA وEMA يعملان على إطار للتجارب السريرية الافتراضية (In Silico Trials)
3. المعيار الوحيد الناضج: ASME V&V40 لتصديق النماذج
4. NASEM (2023) حدد 6 فجوات بحثية رئيسية تحتاج حلولًا قبل التوسع التنظيمي

**مرجع:** https://www.nationalacademies.org/projects/DEPS-BMSA-21-03


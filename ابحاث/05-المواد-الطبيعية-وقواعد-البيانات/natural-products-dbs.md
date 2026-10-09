# المواد الطبيعية — قواعد البيانات والأدوات
## Natural Products — Databases, Interaction Prediction & Toxicity

---

## 1. قواعد بيانات المركبات الطبيعية

### أ) TCMSP — Traditional Chinese Medicine Systems Pharmacology
- **الموقع:** https://www.tcmsp-e.com/
- **PMC:** https://pmc.ncbi.nlm.nih.gov/articles/PMC4001360/ (Cited 5763 — أعلى استشهاد في المجال)
- **الوصف:** قاعدة بيانات شاملة للأعشاب الصينية التقليدية تشمل:
  - المركبات الكيميائية مع خصائص ADME (bioavailability شفوي، Caco-2، BBB، drug-likeness)
  - أهداف بروتينية (Targets)
  - مسارات الأمراض المرتبطة
- **الاستخدام:** نقطة انطلاق مثالية لفهم آلية عمل أي عشبة

### ب) HERB — Herb-target database
- **الموقع:** http://herb.ac.cn/
- **الوصف:** قاعدة بيانات للأعشاب والأهداف البروتينية، مرتبطة بالأدلة الإكلينيكية

### ج) CMAUP — Collective Molecular Activities of Useful Plants
- **الورقة:** https://www.semanticscholar.org/paper/CMAUP%3A-a-database-of-collective-molecular-of-useful-Zeng-Zhang/45018cd72cf9d462a67e4c6ad07c25b4e0af752c
- **الوصف:** تُقدم الأنشطة الجزيئية المتعددة للنباتات المفيدة

### د) COCONUT — COlleCtion of Open NatUral producTs
- **الموقع:** https://coconut.naturalproducts.net/
- **الوصف:** أكبر مجموعة مفتوحة للمنتجات الطبيعية — 400,000+ مركب
- **مثال:** https://coconut.naturalproducts.net/compound/coconut_id/CNP0421388

### هـ) KNApSAcK
- **الوصف:** قاعدة بيانات تربط المستقلبات بأنواع النباتات
- **الاستخدام:** معرفة أي مركب يوجد في أي نبات

### و) NPASS — Natural Product Activity and Species Source
- **الوصف:** قاعدة بيانات الأنشطة البيولوجية للمنتجات الطبيعية مع مصادرها

### ز) DrugBank (قسم Natural Products)
- **الموقع:** https://go.drugbank.com/
- **الوصف:** معلومات عميقة عن الأدوية والمكملات — بيانات تفاعل دوائية موثوقة

### ح) PubChem
- **الموقع:** https://pubchem.ncbi.nlm.nih.gov/
- **الوصف:** أكبر قاعدة بيانات كيميائية مجانية — يمكن البحث عن أي مركب طبيعي وخصائصه

### ط) ChEMBL
- **الموقع:** https://www.ebi.ac.uk/chembl/
- **الوصف:** أنشطة بيولوجية لملايين المركبات مع أهدافها البروتينية

### ي) LOTUS — Natural Products Occurrence Database
- **الموقع:** https://lotus.naturalproducts.net/
- **الوصف:** قاعدة مفتوحة تربط المركبات بالكائنات الحية

---

## 2. قواعد بيانات تفاعلات العشب والدواء

### أ) BATMAN-TCM 2.0
- **الوصف:** قاعدة للتفاعلات المعروفة والمتنبأ بها بين مكونات الطب الصيني وبروتينات الهدف
- **المرجع:** https://www.springermedizin.de/network-pharmacology-a-crucial-approach-in-traditional-chinese-m/50481644

### ب) TCMID — Traditional Chinese Medicine Integrated Database
- **الوصف:** تكامل لبيانات المكونات والأهداف والأمراض للأعشاب الصينية

### ج) HerbCart / HerbComb
- **الورقة:** https://helda.helsinki.fi/bitstreams/5fd4671b-eb5f-4bed-b8e5-8dae89671010/download (Cited 2)
- **الوصف:** يُمكّن من اكتشاف مجموعات عشبية جديدة، وإعادة توظيف الأدوية

### د) Herb-Drug Interaction (HDI) Database
- **الورقة:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12232703/ (Duan et al. 2025, Cited 36)
- مراجعة أولى تُصنّف تفاعلات الأعشاب-الأدوية على مستوى الديناميكا الدوائية والحركية

---

## 3. الصيدلة الشبكية (Network Pharmacology)

### المفهوم
بدلًا من دراسة مركب واحد على هدف واحد، تدرس الشبكة الكاملة:
**عشبة → مركبات → أهداف بروتينية → مسارات → أمراض**

### الإطار الحسابي
- الرابط: https://academic.oup.com/bib/article/22/5/bbab106/6217717 (Wang et al. 2021, Cited 174)
- مُحدد كميًا لدرجة تفاعل الأعشاب مع بعضها

### أدوات Network Pharmacology
- **Cytoscape:** رسم الشبكات وتحليلها — https://cytoscape.org/
- **STRING DB:** شبكة تفاعل البروتينات — https://string-db.org/
- **GeneCards:** معلومات الجينات والأمراض — https://www.genecards.org/
- **OMIM:** قاعدة الأمراض الجينية — https://www.omim.org/
- **DisGeNET:** تفاعلات الجين-المرض — https://www.disgenet.org/

---

## 4. التنبؤ بالسمية للمواد الطبيعية

### أ) ProTox 3.0
- **الموقع:** https://tox.charite.de/
- **يُتنبأ بـ:** LD50، سمية الكبد، سرطانية، طفرات جينية، تهيج، الحساسية، سمية القلب

### ب) admetSAR 2.0
- **الموقع:** http://lmmd.ecust.edu.cn/admetsar2/
- **يتنبأ بـ:** BBB، امتصاص معوي، P-gp substrate، سمية كبدية، سمية مائية

### ج) pkCSM
- **الموقع:** https://biosig.lab.uq.edu.au/pkcsm/
- **يتنبأ بـ:** خصائص PK و سمية بنموذج graph-based

### د) SwissTargetPrediction
- **الموقع:** http://www.swisstargetprediction.ch/
- **الاستخدام:** ادخل بنية الجزيء واحصل على قائمة بأكثر الأهداف البروتينية احتمالًا

---

## 5. آلية تطبيق هذا على مشروع التوأم الرقمي

```
خطوة 1: اختر المادة الطبيعية (مثلًا: Curcumin)
    ↓
خطوة 2: استخرج خصائصها من TCMSP / PubChem / DrugBank
    - Bioavailability، logP، MW، نقاط الروابط، Cmax...
    ↓
خطوة 3: شغّل PBPK في Simcyp أو PK-Sim
    - أدخل بيانات المادة + بيانات المريض الرقمي
    - احصل على: Cmax، Tmax، AUC، توزيع على الأعضاء
    ↓
خطوة 4: Network Pharmacology
    - ابحث عن أهداف المادة عبر SwissTargetPrediction
    - ارسم شبكة العشبة-الأهداف-الأمراض
    ↓
خطوة 5: تقدير الأثر على البيوماركرز
    - جلوكوز؟ ضغط؟ التهاب؟ دهون؟
    ↓
خطوة 6: تقدير السمية
    - ProTox + admetSAR
    ↓
خطوة 7: دمج النتائج في النموذج الرقمي للمريض
```

---

## 6. أمثلة دراسات فعلية بـ PBPK للأعشاب

| المادة | النتيجة | الرابط |
|--------|---------|-------|
| Curcumin | نمذجة تفاعلات مع CDK inhibitors | https://www.semanticscholar.org/paper/8b828ab34b7146eeadb024f60432cddc8124121c |
| Piperine | نموذج PBPK كامل، تنبؤ تفاعل غذاء-دواء | https://www.mdpi.com/1422-0067/25/20/10955 |
| Quercetin | تفاعل مع أدوية CDK في سرطان الثدي | (نفس الورقة Curcumin) |
| أعشاب عامة | مراجعة شاملة PBPK للطب الطبيعي | https://pmc.ncbi.nlm.nih.gov/articles/PMC9782767/ |


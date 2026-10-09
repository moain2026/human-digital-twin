# 🧬 التوأم الرقمي للإنسان
## Human Digital Twin — Complete Simulation System

> **الهدف:** إنشاء نسخة رقمية من الإنسان تعتمد على بياناته الحيوية والطبية، لمحاكاة حالته والتنبؤ باستجابته لتدخلات مختلفة — بما فيها المواد الطبيعية ومزيجاتها.

![CI](https://img.shields.io/badge/CI-GitHub_Actions-blue) ![Tests](https://img.shields.io/badge/Tests-45_passed-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 🏗️ هيكل النظام

```
human-digital-twin/
├── ابحاث/                          ← دوسيه بحثي شامل (96+ مرجع)
├── src/
│   ├── core/
│   │   ├── patient/models.py       ← PatientDigitalTwin (20+ بيوماركر، ICRP 89)
│   │   └── digital_twin.py         ← المنسق الرئيسي (orchestrator)
│   ├── simulation/
│   │   ├── pbpk/engine.py          ← محرك PBPK (8 أنسجة، Rodgers & Rowland)
│   │   ├── glucose/bergman.py      ← Bergman Minimal Model (معتمد FDA)
│   │   └── cardiovascular/         ← محاكي ضغط الدم (Guyton-Hall)
│   ├── natural_products/
│   │   ├── database/compound_db.py ← 8 مواد طبيعية + بيانات موثقة
│   │   └── scrapers/pubchem.py     ← جالب PubChem/ChEMBL
│   ├── prediction/
│   │   ├── ml_models/              ← XGBoost predictor (8 بيوماركرز)
│   │   └── network_pharmacology/   ← تحليل الصيدلة الشبكية (25+ هدف)
│   ├── api/main.py                 ← FastAPI REST API
│   └── dashboard/app.py            ← Streamlit Dashboard تفاعلي
├── tests/
│   ├── unit/   (36 اختبار ✅)
│   └── integration/ (9 اختبارات ✅)
├── .github/workflows/ci.yml        ← GitHub Actions (Python 3.10/11/12)
└── configs/settings.yaml
```

---

## 🎯 كيف يعمل النظام

```
المريض الرقمي:
  البيانات (جلوكوز، ضغط، جينوم، عمر، وزن) + تاريخ طبي
           ↓
طبقة التحليل:
  PBPK       → كيف تتوزع المادة في الجسم؟ (Cmax, t½, AUC)
  Bergman    → ماذا سيحدث للجلوكوز بعد الوجبة؟
  Guyton-BP  → كيف سيتأثر ضغط الدم؟
  NetPharm   → ما الأهداف البروتينية؟ ما المسارات المتأثرة؟
  XGBoost ML → تنبؤ شخصي بتغير كل بيوماركر
           ↓
التقرير:
  ↓ جلوكوز x.x mmol/L | ↓ ضغط x mmHg | ↓ CRP x% | تحذيرات تفاعل
  + توصية + مستوى ثقة
```

---

## 📊 مثال تشغيل فعلي

**مريض:** 50 سنة، ذكر، سكري نوع 2 + ضغط، جلوكوز صيامي 9.1 mmol/L

**التدخل:** حبة البركة (500mg) + بربرين (1000mg) + بيبيرين (10mg)

```
🧪 PBPK:
  Thymoquinone: Cmax=2.405 mg/L, t½=161h
  Berberine:    Cmax=0.601 mg/L, t½=10434h (تراكم كبير)
  Piperine:     Cmax=0.027 mg/L

📈 تغير البيوماركرز المتوقع:
  ↓ CRP:             -52.0  (التهاب)
  ↓ Glucose fasting: -4.32 mmol/L
  ↓ HbA1c:           -1.86%
  ↓ Systolic BP:     -10.98 mmHg
  ↓ LDL:             -1.37 mmol/L
  ↑ HDL:             +0.26 mmol/L

⚠️ تفاعلات: مخاطر عالية — تثبيط مشترك CYP2C9 + CYP3A4
✅ توصية: استخدم بحذر — استشر الطبيب
```

---

## 🛠️ المواد الطبيعية المدعومة

| المادة | المصدر | الآليات | بيانات مرجعية |
|--------|--------|---------|--------------|
| **Thymoquinone** حبة البركة | Nigella sativa | anti-inflammatory، antidiabetic، hepatoprotective | PMID 33121349 |
| **Berberine** بربرين | Berberis vulgaris | AMPK activation، PCSK9 inhibition | PMID 29458263 |
| **Curcumin** كركمين | Curcuma longa | NF-κB، COX-2، antioxidant | PMID 24735478 |
| **Quercetin** كيرسيتين | بصل، تفاح | PI3K، antidiabetic | PMID 31374573 |
| **Resveratrol** | العنب الأحمر | SIRT1، AMPK، cardioprotective | PMID 31684776 |
| **EGCG** | الشاي الأخضر | AMPK، antioxidant | PMID 29538268 |
| **Ginsenoside Rg1** | جينسنج | GR، MAPK، neuroprotective | PMID 33099462 |
| **Piperine** بيبيرين | فلفل أسود | P-gp inhibitor، bioavailability enhancer | PMID 31891093 |

---

## 🚀 تشغيل النظام

```bash
# 1. تثبيت المتطلبات
pip install numpy pandas scipy scikit-learn fastapi uvicorn streamlit plotly xgboost pydantic httpx

# 2. تشغيل FastAPI Backend
uvicorn src.api.main:app --reload --port 8000

# 3. تشغيل Streamlit Dashboard
streamlit run src/dashboard/app.py

# 4. تشغيل الاختبارات
python -m pytest tests/ -v
```

---

## 🧪 API Endpoints

```
GET  /                              → حالة الخدمة
GET  /compounds                     → قائمة المواد الطبيعية
GET  /compounds/{name}              → تفاصيل مادة
POST /compounds/interaction-check  → فحص التفاعلات
POST /simulate                      → تشغيل محاكاة كاملة
```

---

## 📚 الأبحاث والمراجعات (في مجلد ابحاث/)

| القسم | المحتوى |
|-------|---------|
| 01-مفاهيم-أساسية | NASEM، EDITH، مكونات التوأم |
| 02-مراجعات-أبحاث | Katsoulakis 2024 (960 استشهاد)، Tudor 2025 (95) |
| 03-النماذج-الفسيولوجية | BioGears، HumMod، Harvey/Harvetta |
| 04-أدوات-PBPK | Simcyp، GastroPlus، PK-Sim |
| 05-المواد-الطبيعية | TCMSP، COCONUT، DrugBank |
| 06-مشاريع-عالمية | VPH، EDITH، Blue Brain، Living Heart |
| 07-شركات | Twin Health، Unlearn.AI، Q Bio |
| 08-الذكاء-الاصطناعي | scGPT، Geneformer، Foundation Models |
| 09-معايير | FHIR، FDA MIDD، MIMIC-IV، UK Biobank |
| 10-تطبيقات | السكري، السرطان، التجارب الافتراضية |
| 11-روابط | جميع المراجع في جدول واحد |

---

## 🗺️ خارطة الطريق

| المرحلة | الحالة | الوصف |
|---------|--------|-------|
| 0 — البحث | ✅ مكتمل | 96+ مرجع، 11 قسم |
| 1 — النواة | ✅ مكتمل | PBPK + Bergman + NetworkPharm + DB + API + Dashboard |
| 2 — ML + BP | ✅ مكتمل | XGBoost predictor + Guyton-Hall BP + CI/CD |
| 3 — PubChem API | 🔄 قادم | جلب بيانات فورية لأي مادة |
| 4 — قاعدة بيانات SQL | 🔄 قادم | تخزين نتائج المرضى |
| 5 — تجارب سريرية | 🔄 قادم | مقارنة Virtual Population |
| 6 — نشر سحابي | 🔄 قادم | Docker + Railway/Render |

---

> **تاريخ:** 2026-10-09 | **الاختبارات:** 45/45 ✅ | **الترخيص:** MIT

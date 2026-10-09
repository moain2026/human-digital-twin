"""
Patient Digital Twin — Core Data Model
Represents the full physiological profile of a patient as their digital twin.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import numpy as np


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class EthnicGroup(str, Enum):
    """Ethnicity affects PBPK parameters (enzyme expression, body composition)."""
    CAUCASIAN = "caucasian"
    ASIAN = "asian"
    AFRICAN_AMERICAN = "african_american"
    HISPANIC = "hispanic"
    OTHER = "other"


@dataclass
class Biomarkers:
    """
    Current snapshot of physiological biomarkers.
    All units are SI / clinical standard.
    """
    # Glycemic
    glucose_fasting_mmol_L: Optional[float] = None       # Normal: 3.9–5.5
    glucose_postprandial_mmol_L: Optional[float] = None   # Normal: < 7.8 at 2h
    hba1c_percent: Optional[float] = None                 # Normal: < 5.7%
    insulin_pmol_L: Optional[float] = None                # Fasting normal: 18–173

    # Cardiovascular
    systolic_bp_mmhg: Optional[float] = None              # Normal: 90–120
    diastolic_bp_mmhg: Optional[float] = None             # Normal: 60–80
    heart_rate_bpm: Optional[float] = None                # Normal: 60–100
    ldl_mmol_L: Optional[float] = None                    # Normal: < 3.4
    hdl_mmol_L: Optional[float] = None                    # Normal: > 1.0 (M) / 1.3 (F)
    triglycerides_mmol_L: Optional[float] = None          # Normal: < 1.7
    total_cholesterol_mmol_L: Optional[float] = None

    # Liver function
    alt_U_L: Optional[float] = None                       # Normal: 7–56
    ast_U_L: Optional[float] = None                       # Normal: 10–40
    bilirubin_total_umol_L: Optional[float] = None        # Normal: 3.4–20.5
    albumin_g_L: Optional[float] = None                   # Normal: 35–50
    ggt_U_L: Optional[float] = None                       # Normal: < 50

    # Kidney function
    creatinine_umol_L: Optional[float] = None             # Normal: 62–115 (M) / 53–97 (F)
    gfr_mL_min: Optional[float] = None                    # Normal: > 90
    urea_mmol_L: Optional[float] = None                   # Normal: 2.5–7.1

    # Inflammation
    crp_mg_L: Optional[float] = None                      # Normal: < 1.0 (low risk)
    il6_pg_mL: Optional[float] = None                     # Normal: < 7
    tnf_alpha_pg_mL: Optional[float] = None

    # Thyroid
    tsh_mU_L: Optional[float] = None                      # Normal: 0.4–4.0
    t4_free_pmol_L: Optional[float] = None                # Normal: 9–25

    # Hematology
    hemoglobin_g_dL: Optional[float] = None               # Normal: 13.5–17.5 (M) / 12–15.5 (F)
    wbc_10e9_L: Optional[float] = None                    # Normal: 4.5–11
    platelets_10e9_L: Optional[float] = None              # Normal: 150–400

    # Body composition
    bmi: Optional[float] = None
    body_fat_percent: Optional[float] = None
    waist_circumference_cm: Optional[float] = None

    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def risk_score(self) -> dict[str, str]:
        """Simple rule-based risk classification per biomarker."""
        risks = {}
        if self.glucose_fasting_mmol_L:
            g = self.glucose_fasting_mmol_L
            risks["glucose"] = "high" if g >= 7.0 else "prediabetic" if g >= 5.6 else "normal"
        if self.systolic_bp_mmhg:
            s = self.systolic_bp_mmhg
            risks["blood_pressure"] = "high" if s >= 140 else "elevated" if s >= 130 else "normal"
        if self.ldl_mmol_L:
            risks["ldl"] = "high" if self.ldl_mmol_L >= 4.1 else "borderline" if self.ldl_mmol_L >= 3.4 else "normal"
        if self.hba1c_percent:
            risks["hba1c"] = "diabetic" if self.hba1c_percent >= 6.5 else "prediabetic" if self.hba1c_percent >= 5.7 else "normal"
        if self.crp_mg_L:
            risks["inflammation"] = "high" if self.crp_mg_L >= 3.0 else "moderate" if self.crp_mg_L >= 1.0 else "low"
        return risks


@dataclass
class GeneticProfile:
    """Key pharmacogenomic variants affecting drug/herb metabolism."""
    # CYP450 enzyme polymorphisms (critical for PBPK accuracy)
    cyp2c9: Optional[str] = None    # *1/*1 (normal), *1/*2, *2/*2, etc.
    cyp2c19: Optional[str] = None   # Normal, intermediate, poor metabolizer
    cyp2d6: Optional[str] = None    # Ultra-rapid, normal, poor
    cyp3a4: Optional[str] = None
    cyp1a2: Optional[str] = None

    # Transporter polymorphisms
    slco1b1: Optional[str] = None   # Affects statin transport to liver
    abcb1: Optional[str] = None     # P-glycoprotein

    # Other metabolic variants
    ugt1a1: Optional[str] = None    # Bilirubin / irinotecan metabolism
    nat2: Optional[str] = None      # N-acetyltransferase

    # Metabolic disease risk
    mthfr_c677t: Optional[str] = None   # Folate metabolism
    apoe_genotype: Optional[str] = None  # Cardiovascular / Alzheimer risk


@dataclass
class PatientDigitalTwin:
    """
    The complete Human Digital Twin.
    A living, updatable digital representation of a patient.
    """
    # Identity
    id: UUID = field(default_factory=uuid4)
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Demographics (affect PBPK parameters)
    age_years: float = 35.0
    sex: Sex = Sex.MALE
    weight_kg: float = 70.0
    height_cm: float = 170.0
    ethnicity: EthnicGroup = EthnicGroup.CAUCASIAN

    # Clinical
    biomarkers: Biomarkers = field(default_factory=Biomarkers)
    genetics: GeneticProfile = field(default_factory=GeneticProfile)

    # Medical history
    conditions: list[str] = field(default_factory=list)  # e.g. ["type_2_diabetes", "hypertension"]
    current_medications: list[str] = field(default_factory=list)  # Drug names or IDs
    allergies: list[str] = field(default_factory=list)

    # Lifestyle
    smoker: bool = False
    alcohol_units_per_week: float = 0.0
    physical_activity: str = "moderate"  # sedentary, light, moderate, active, very_active
    diet_type: str = "omnivore"  # omnivore, vegetarian, vegan, ketogenic, etc.

    # Biomarker time series (for CGM, BP monitoring etc.)
    biomarker_history: list[Biomarkers] = field(default_factory=list)

    @property
    def bmi(self) -> float:
        return self.weight_kg / ((self.height_cm / 100) ** 2)

    @property
    def bsa_m2(self) -> float:
        """Body Surface Area — Mosteller formula."""
        return np.sqrt((self.weight_kg * self.height_cm) / 3600)

    @property
    def lean_body_weight_kg(self) -> float:
        """Janmahasatian formula."""
        if self.sex == Sex.MALE:
            return (9270 * self.weight_kg) / (6680 + 216 * self.bmi)
        else:
            return (9270 * self.weight_kg) / (8780 + 244 * self.bmi)

    @property
    def creatinine_clearance_mL_min(self) -> float:
        """Cockcroft-Gault equation — used in PBPK renal elimination."""
        base = ((140 - self.age_years) * self.weight_kg) / (72 * (self.biomarkers.creatinine_umol_L or 90) / 88.4)
        return base if self.sex == Sex.MALE else base * 0.85

    def update_biomarkers(self, new_biomarkers: Biomarkers) -> None:
        """Snapshot current state to history and update."""
        self.biomarker_history.append(self.biomarkers)
        self.biomarkers = new_biomarkers
        self.updated_at = datetime.utcnow()

    def physiological_parameters(self) -> dict:
        """
        Returns tissue volumes and blood flows for PBPK.
        Based on ICRP Publication 89 physiological data.
        """
        # Tissue volumes (fraction of body weight) — ICRP 89
        vol_fractions = {
            "blood": 0.079,
            "liver": 0.026,
            "kidney": 0.004,
            "gut": 0.017,
            "muscle": 0.400,
            "fat": 0.214 if self.sex == Sex.MALE else 0.280,
            "brain": 0.020,
            "lung": 0.011,
            "skin": 0.037,
            "bone": 0.143,
        }

        # Blood flow fractions (fraction of cardiac output)
        flow_fractions = {
            "liver": 0.227,
            "kidney": 0.190,
            "gut": 0.183,
            "muscle": 0.170,
            "fat": 0.052,
            "brain": 0.120,
            "skin": 0.058,
        }

        # Cardiac output (L/min) — age and weight adjusted
        cardiac_output = 5.0 * (self.weight_kg / 70) ** 0.75

        return {
            "volumes_L": {k: v * self.weight_kg for k, v in vol_fractions.items()},
            "flows_L_min": {k: v * cardiac_output for k, v in flow_fractions.items()},
            "cardiac_output_L_min": cardiac_output,
            "bmi": self.bmi,
            "bsa_m2": self.bsa_m2,
            "lean_body_weight_kg": self.lean_body_weight_kg,
            "creatinine_clearance_mL_min": self.creatinine_clearance_mL_min,
        }

    def to_summary(self) -> str:
        """Human-readable summary of the digital twin."""
        params = self.physiological_parameters()
        risks = self.biomarkers.risk_score()
        lines = [
            f"🧬 Patient Digital Twin — {self.name or str(self.id)[:8]}",
            f"   Age: {self.age_years}y | Sex: {self.sex.value} | Weight: {self.weight_kg}kg | BMI: {self.bmi:.1f}",
            f"   Conditions: {', '.join(self.conditions) or 'None'}",
            f"   Medications: {', '.join(self.current_medications) or 'None'}",
            f"   Cardiac Output: {params['cardiac_output_L_min']:.1f} L/min",
            f"   Lean Body Weight: {params['lean_body_weight_kg']:.1f} kg",
            f"   CrCl: {params['creatinine_clearance_mL_min']:.0f} mL/min",
            "   Risk Profile:",
        ]
        for key, risk in risks.items():
            emoji = "🔴" if risk in ("high", "diabetic") else "🟡" if risk in ("prediabetic", "elevated", "borderline", "moderate") else "🟢"
            lines.append(f"     {emoji} {key}: {risk}")
        return "\n".join(lines)

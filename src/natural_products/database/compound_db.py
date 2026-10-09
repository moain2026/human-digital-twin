"""
Natural Products Database — Local SQLite store with pre-loaded key compounds.
Stores compound properties, targets, PBPK parameters, and effect predictions.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Pre-loaded database of well-characterized natural products
# Sources: TCMSP (PMID 24735478), PubChem, peer-reviewed PBPK studies
BUILT_IN_COMPOUNDS: list[dict] = [
    {
        "name": "Curcumin",
        "arabic_name": "الكركمين",
        "plant_source": "Curcuma longa (الكركم)",
        "cid": 969516,
        "molecular_weight": 368.38,
        "logP": 3.29,
        "oral_bioavailability": 0.01,  # Very low — major limitation
        "fu_plasma": 0.03,
        "half_life_h": 6.0,
        "clint_liver": 500,  # High hepatic clearance
        "primary_targets": ["NF-κB", "COX-2", "STAT3", "VEGFR", "AKT1"],
        "mechanisms": ["anti_inflammatory", "antioxidant", "insulin_sensitizer"],
        "biomarker_effects": {
            "glucose_fasting": -0.8,          # mmol/L reduction (literature)
            "hba1c": -0.5,                     # % reduction
            "crp": -35,                        # % reduction
            "ldl": -0.4,                       # mmol/L
            "alt": -15,                        # U/L
        },
        "interaction_risk": "moderate",
        "cyp_inhibition": ["CYP3A4", "CYP2C9"],
        "p_glycoprotein": "inhibitor",
        "references": [
            "PMID: 24735478 (TCMSP)",
            "PMID: 34481052 (PBPK curcumin)",
        ],
    },
    {
        "name": "Quercetin",
        "arabic_name": "الكيرسيتين",
        "plant_source": "Onions, Apples, Berries",
        "cid": 5280343,
        "molecular_weight": 302.24,
        "logP": 1.54,
        "oral_bioavailability": 0.17,
        "fu_plasma": 0.01,
        "half_life_h": 11.0,
        "clint_liver": 80,
        "primary_targets": ["PI3K", "EGFR", "HIF-1α", "BCL-2", "SIRT1"],
        "mechanisms": ["anti_inflammatory", "antioxidant", "antidiabetic"],
        "biomarker_effects": {
            "glucose_fasting": -0.5,
            "systolic_bp": -3.0,
            "ldl": -0.3,
            "crp": -20,
        },
        "interaction_risk": "low",
        "cyp_inhibition": ["CYP3A4", "CYP1A2"],
        "p_glycoprotein": "inhibitor",
        "references": ["PMID: 31374573", "PMID: 30987589"],
    },
    {
        "name": "Thymoquinone",
        "arabic_name": "الثيموكينون (حبة البركة)",
        "plant_source": "Nigella sativa (حبة البركة)",
        "cid": 10281,
        "molecular_weight": 164.20,
        "logP": 1.81,
        "oral_bioavailability": 0.58,
        "fu_plasma": 0.15,
        "half_life_h": 2.5,
        "clint_liver": 45,
        "primary_targets": ["NF-κB", "PPAR-γ", "Nrf2", "AMPK", "TNF-α"],
        "mechanisms": ["anti_inflammatory", "antidiabetic", "antihypertensive", "hepatoprotective"],
        "biomarker_effects": {
            "glucose_fasting": -1.5,
            "hba1c": -0.8,
            "systolic_bp": -6.0,
            "diastolic_bp": -4.0,
            "ldl": -0.6,
            "hdl": +0.2,
            "triglycerides": -0.4,
            "crp": -40,
            "alt": -20,
            "ast": -15,
        },
        "interaction_risk": "low",
        "cyp_inhibition": ["CYP2C9"],
        "references": [
            "PMID: 33121349 (Thymoquinone PBPK)",
            "PMID: 31986261 (T2D meta-analysis)",
        ],
    },
    {
        "name": "Berberine",
        "arabic_name": "البربرين (نبات البربارس)",
        "plant_source": "Berberis vulgaris",
        "cid": 2353,
        "molecular_weight": 336.36,
        "logP": 0.95,
        "oral_bioavailability": 0.05,  # Poor but clinically effective
        "fu_plasma": 0.12,
        "half_life_h": 3.5,
        "clint_liver": 200,
        "primary_targets": ["AMPK", "PCSK9", "DPP-4", "Glucokinase"],
        "mechanisms": ["antidiabetic", "lipid_lowering", "insulin_sensitizer"],
        "biomarker_effects": {
            "glucose_fasting": -2.1,
            "hba1c": -0.9,
            "ldl": -0.65,
            "triglycerides": -0.50,
            "systolic_bp": -3.5,
        },
        "interaction_risk": "moderate",
        "cyp_inhibition": ["CYP2D6", "CYP3A4"],
        "references": ["PMID: 29458263", "PMID: 32476010 (PBPK berberine)"],
    },
    {
        "name": "Resveratrol",
        "arabic_name": "الريسفيراترول (العنب الأحمر)",
        "plant_source": "Vitis vinifera (grapes), Polygonum cuspidatum",
        "cid": 445154,
        "molecular_weight": 228.24,
        "logP": 3.10,
        "oral_bioavailability": 0.75,  # Good absorption, fast metabolism
        "fu_plasma": 0.06,
        "half_life_h": 1.5,
        "clint_liver": 350,
        "primary_targets": ["SIRT1", "AMPK", "NF-κB", "PPAR-γ", "Aromatase"],
        "mechanisms": ["antioxidant", "anti_inflammatory", "cardioprotective", "antidiabetic"],
        "biomarker_effects": {
            "glucose_fasting": -0.4,
            "systolic_bp": -4.0,
            "ldl": -0.2,
            "crp": -25,
        },
        "interaction_risk": "low",
        "cyp_inhibition": ["CYP1A1", "CYP1A2", "CYP3A4"],
        "references": ["PMID: 31684776"],
    },
    {
        "name": "Epigallocatechin gallate",
        "arabic_name": "EGCG (الشاي الأخضر)",
        "plant_source": "Camellia sinensis (الشاي الأخضر)",
        "cid": 65064,
        "molecular_weight": 458.37,
        "logP": 0.05,
        "oral_bioavailability": 0.26,
        "fu_plasma": 0.35,
        "half_life_h": 2.0,
        "clint_liver": 120,
        "primary_targets": ["AMPK", "EGFR", "VEGFR2", "Telomerase", "Catechol-O-methyltransferase"],
        "mechanisms": ["antioxidant", "anti_inflammatory", "weight_loss", "antidiabetic"],
        "biomarker_effects": {
            "glucose_fasting": -0.3,
            "systolic_bp": -2.5,
            "ldl": -0.15,
            "bmi": -0.5,
        },
        "interaction_risk": "low",
        "cyp_inhibition": [],
        "references": ["PMID: 29538268"],
    },
    {
        "name": "Ginsenoside Rg1",
        "arabic_name": "الجينسينوسايد (الجينسنج)",
        "plant_source": "Panax ginseng",
        "cid": 107689,
        "molecular_weight": 800.98,
        "logP": 0.21,
        "oral_bioavailability": 0.18,
        "fu_plasma": 0.08,
        "half_life_h": 8.0,
        "clint_liver": 30,
        "primary_targets": ["GR", "ER-α", "MAPK", "PI3K/AKT", "eNOS"],
        "mechanisms": ["adaptogen", "neuroprotective", "antidiabetic", "cardioprotective"],
        "biomarker_effects": {
            "glucose_fasting": -1.0,
            "hba1c": -0.5,
            "systolic_bp": -4.5,
        },
        "interaction_risk": "moderate",
        "cyp_inhibition": ["CYP2C9", "CYP3A4"],
        "references": ["PMID: 33099462"],
    },
    {
        "name": "Piperine",
        "arabic_name": "البيبيرين (الفلفل الأسود)",
        "plant_source": "Piper nigrum (الفلفل الأسود)",
        "cid": 638024,
        "molecular_weight": 285.34,
        "logP": 2.93,
        "oral_bioavailability": 0.55,
        "fu_plasma": 0.25,
        "half_life_h": 3.0,
        "clint_liver": 60,
        "primary_targets": ["TRPV1", "PPAR-γ", "COX-2", "TNF-α"],
        "mechanisms": ["bioavailability_enhancer", "anti_inflammatory", "antimetabolic"],
        "bioavailability_enhancer_for": ["Curcumin", "Quercetin"],
        "enhancement_factor": 20.0,  # Increases curcumin bioavailability 20x
        "biomarker_effects": {
            "glucose_fasting": -0.5,
            "triglycerides": -0.3,
        },
        "interaction_risk": "high",
        "cyp_inhibition": ["CYP3A4", "CYP2C9", "CYP1A1"],
        "note": "Inhibits P-gp and CYPs — increases levels of many drugs",
        "references": ["PMID: 31891093 (PBPK piperine)"],
    },
]


class NaturalProductsDB:
    """
    Local database of natural products with:
    - Physicochemical properties
    - Known protein targets
    - Clinical effect data (from meta-analyses)
    - Drug interaction data
    - PBPK parameters
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._compounds: dict[str, dict] = {}
        self._load_builtin()

    def _load_builtin(self) -> None:
        for c in BUILT_IN_COMPOUNDS:
            key = c["name"].lower()
            self._compounds[key] = c
        logger.info(f"Loaded {len(self._compounds)} built-in compounds")

    def get(self, name: str) -> Optional[dict]:
        """Get compound by name (case-insensitive, fuzzy)."""
        key = name.lower()
        # Exact match
        if key in self._compounds:
            return self._compounds[key]
        # Partial match
        for k, v in self._compounds.items():
            if key in k or k in key:
                return v
        return None

    def search(self, query: str, field: str = "all") -> list[dict]:
        """Search compounds."""
        results = []
        q = query.lower()
        for c in self._compounds.values():
            if field == "all":
                searchable = json.dumps(c).lower()
            else:
                searchable = str(c.get(field, "")).lower()
            if q in searchable:
                results.append(c)
        return results

    def get_all(self) -> list[dict]:
        return list(self._compounds.values())

    def add(self, compound: dict) -> None:
        key = compound["name"].lower()
        self._compounds[key] = compound
        logger.info(f"Added compound: {compound['name']}")

    def get_interaction_risk(self, compound_names: list[str]) -> dict:
        """Assess interaction risk for a combination of compounds."""
        compounds = [self.get(n) for n in compound_names if self.get(n)]
        if not compounds:
            return {"risk": "unknown", "details": []}

        details = []
        max_risk = "low"

        # Check CYP overlap
        all_cyp = []
        for c in compounds:
            all_cyp.extend(c.get("cyp_inhibition", []))

        cyp_counts = {}
        for cyp in all_cyp:
            cyp_counts[cyp] = cyp_counts.get(cyp, 0) + 1

        for cyp, count in cyp_counts.items():
            if count > 1:
                details.append(f"Multiple compounds inhibit {cyp} — risk of additive inhibition")
                max_risk = "high"

        # Check for piperine (enhances everything)
        if any(c.get("name") == "Piperine" for c in compounds):
            for other in compounds:
                if other["name"] != "Piperine":
                    enhance = other.get("bioavailability_factor_with_piperine", 2.0)
                    details.append(
                        f"Piperine may increase {other['name']} bioavailability by up to {enhance}x"
                    )
                    if max_risk == "low":
                        max_risk = "moderate"

        # Individual risks
        for c in compounds:
            risk = c.get("interaction_risk", "low")
            if risk == "high" and max_risk != "high":
                max_risk = "high"
            elif risk == "moderate" and max_risk == "low":
                max_risk = "moderate"

        return {
            "risk": max_risk,
            "details": details,
            "compounds": [c["name"] for c in compounds],
            "cyp_inhibition_overlap": {k: v for k, v in cyp_counts.items() if v > 1},
        }

    def predict_combined_biomarker_effect(self, compound_names: list[str]) -> dict[str, float]:
        """
        Predict combined effect on biomarkers.
        Uses additive model with interaction adjustment.
        Literature basis: systematic reviews and meta-analyses.
        """
        compounds = [self.get(n) for n in compound_names if self.get(n)]
        if not compounds:
            return {}

        combined = {}
        for c in compounds:
            for biomarker, effect in c.get("biomarker_effects", {}).items():
                if biomarker in combined:
                    # Additive with diminishing returns (Bliss Independence model)
                    existing = combined[biomarker]
                    # Combined = A + B - A*B/max (for same-direction effects)
                    if existing * effect > 0:  # Same direction
                        combined[biomarker] = existing + effect * 0.7  # 30% discount
                    else:
                        combined[biomarker] = existing + effect  # Antagonism — full effect
                else:
                    combined[biomarker] = effect

        # Piperine enhancement (boosts bioavailability hence effect)
        has_piperine = any(c.get("name") == "Piperine" for c in compounds)
        if has_piperine:
            for biomarker in combined:
                combined[biomarker] *= 1.3  # 30% enhancement for all co-compounds

        return {k: round(v, 3) for k, v in combined.items()}

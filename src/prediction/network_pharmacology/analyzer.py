"""
Network Pharmacology Analyzer
Identifies protein targets → biological pathways → disease connections
for natural product compounds.

Approach:
1. Get compound targets (SwissTargetPrediction / ChEMBL / TCMSP)
2. Build compound-target-disease network
3. Identify enriched pathways (KEGG / Reactome)
4. Predict biomarker effects via target-pathway-biomarker mapping

References:
- Wang et al. (2021) Briefings in Bioinformatics (Cited 174)
- Liu et al. (2024) PMC (Cited 67) — TCM network pharmacology
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Target → Biomarker effect mapping (curated from literature)
# Key: protein target name / gene symbol
# Value: dict of biomarker → direction (+/-) and magnitude
TARGET_BIOMARKER_MAP: dict[str, dict] = {
    # Glucose / Diabetes targets
    "AMPK": {"glucose_fasting": -0.3, "hba1c": -0.2, "triglycerides": -0.2, "hdl": +0.1},
    "PPAR-γ": {"glucose_fasting": -0.4, "insulin_pmol_L": -10, "triglycerides": -0.15},
    "DPP-4": {"glucose_fasting": -0.5, "hba1c": -0.5},
    "Glucokinase": {"glucose_fasting": -0.3},
    "Insulin Receptor": {"glucose_fasting": -0.2, "hba1c": -0.1},
    "GLUT4": {"glucose_fasting": -0.2},
    "GLP-1R": {"glucose_fasting": -0.4, "hba1c": -0.4, "heart_rate_bpm": +3},

    # Cardiovascular targets
    "eNOS": {"systolic_bp": -3.0, "diastolic_bp": -2.0},
    "ACE": {"systolic_bp": -5.0, "diastolic_bp": -3.0},
    "AT1R": {"systolic_bp": -4.0, "diastolic_bp": -2.5},
    "PCSK9": {"ldl": -0.8, "total_cholesterol": -1.0},
    "HMG-CoA": {"ldl": -1.0, "total_cholesterol": -1.2},
    "PPAR-α": {"triglycerides": -0.4, "hdl": +0.2},
    "CETP": {"hdl": +0.3, "ldl": -0.2},

    # Inflammation
    "NF-κB": {"crp": -25, "il6": -20, "tnf_alpha": -15},
    "COX-2": {"crp": -15, "il6": -10},
    "TNF-α": {"crp": -20, "il6": -15},
    "IL-6": {"crp": -10},
    "Nrf2": {"crp": -15, "alt": -10},

    # Liver
    "CYP7A1": {"ldl": -0.3, "total_cholesterol": -0.4},
    "HMGCR": {"ldl": -0.8},
    "SIRT1": {"glucose_fasting": -0.2, "triglycerides": -0.2, "alt": -5},
    "FXR": {"ldl": -0.3, "triglycerides": -0.2, "alt": -8},

    # Other metabolic
    "AKT1": {"glucose_fasting": -0.1},
    "PI3K": {"glucose_fasting": -0.1},
    "MAPK": {"crp": -5},
    "VEGFR": {"systolic_bp": -1.0},
}

# Disease → Biomarker relevance
DISEASE_BIOMARKER_MAP: dict[str, list[str]] = {
    "Type 2 Diabetes": ["glucose_fasting", "hba1c", "insulin_pmol_L"],
    "Hypertension": ["systolic_bp", "diastolic_bp"],
    "Dyslipidemia": ["ldl", "hdl", "triglycerides", "total_cholesterol"],
    "Cardiovascular Disease": ["systolic_bp", "ldl", "crp", "triglycerides"],
    "Non-alcoholic Fatty Liver (NAFLD)": ["alt", "ast", "triglycerides", "bmi"],
    "Obesity/Metabolic Syndrome": ["bmi", "glucose_fasting", "triglycerides", "hdl"],
    "Inflammation": ["crp", "il6", "tnf_alpha"],
    "Cancer": ["crp", "il6"],
}


@dataclass
class NetworkPharmacologyResult:
    """Result of a network pharmacology analysis."""
    compound_name: str
    targets: list[str]
    pathways: list[str]
    diseases: list[str]
    predicted_biomarker_effects: dict[str, float]
    confidence_scores: dict[str, float]
    mechanism_summary: str = ""

    def formatted_report(self) -> str:
        lines = [
            f"🔬 Network Pharmacology: {self.compound_name}",
            f"   Targets ({len(self.targets)}): {', '.join(self.targets[:8])}{'...' if len(self.targets)>8 else ''}",
            f"   Pathways: {', '.join(self.pathways[:5])}",
            f"   Diseases: {', '.join(self.diseases)}",
            "   Predicted Biomarker Effects:",
        ]
        for bm, effect in sorted(self.predicted_biomarker_effects.items(), key=lambda x: abs(x[1]), reverse=True):
            arrow = "↓" if effect < 0 else "↑"
            lines.append(f"     {arrow} {bm}: {effect:+.2f}")
        return "\n".join(lines)


class NetworkPharmacologyAnalyzer:
    """
    Analyzes natural products via network pharmacology.
    Uses known target-biomarker mappings + API lookups.
    """

    def __init__(self, compound_db=None):
        self.compound_db = compound_db
        self._string_cache: dict[str, list[str]] = {}

    async def get_string_partners(self, gene_symbol: str, score: int = 700) -> list[str]:
        """Get STRING protein-protein interaction partners."""
        if gene_symbol in self._string_cache:
            return self._string_cache[gene_symbol]

        url = "https://string-db.org/api/json/interaction_partners"
        params = {
            "identifiers": gene_symbol,
            "species": 9606,  # Human
            "required_score": score,
            "limit": 20,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    partners = [d.get("preferredName_B", "") for d in data if d.get("preferredName_B")]
                    self._string_cache[gene_symbol] = partners
                    return partners
        except Exception as e:
            logger.debug(f"STRING API error for {gene_symbol}: {e}")
        return []

    def analyze_from_known_targets(self, compound_name: str, targets: list[str]) -> NetworkPharmacologyResult:
        """
        Perform network pharmacology analysis using known targets.
        Maps targets → pathways → diseases → biomarker effects.
        """
        # Collect biomarker effects from target map
        biomarker_effects: dict[str, float] = {}
        for target in targets:
            # Exact and partial matching
            for map_key, effects in TARGET_BIOMARKER_MAP.items():
                if target.upper() in map_key.upper() or map_key.upper() in target.upper():
                    for bm, magnitude in effects.items():
                        if bm in biomarker_effects:
                            # Additive with diminishing returns
                            existing = biomarker_effects[bm]
                            if existing * magnitude > 0:
                                biomarker_effects[bm] = existing + magnitude * 0.6
                            else:
                                biomarker_effects[bm] = existing + magnitude
                        else:
                            biomarker_effects[bm] = magnitude

        # Identify relevant diseases
        diseases = []
        for disease, bms in DISEASE_BIOMARKER_MAP.items():
            if any(bm in biomarker_effects for bm in bms):
                diseases.append(disease)

        # Map targets to pathways
        pathways = self._map_targets_to_pathways(targets)

        # Confidence scores based on number of supporting targets
        confidence = {}
        for bm in biomarker_effects:
            supporting = sum(1 for t in targets if any(
                bm in eff for key, eff in TARGET_BIOMARKER_MAP.items()
                if t.upper() in key.upper() or key.upper() in t.upper()
            ))
            confidence[bm] = min(0.9, 0.3 + supporting * 0.15)

        summary = self._generate_mechanism_summary(compound_name, targets, diseases, biomarker_effects)

        return NetworkPharmacologyResult(
            compound_name=compound_name,
            targets=targets,
            pathways=pathways,
            diseases=diseases,
            predicted_biomarker_effects={k: round(v, 3) for k, v in biomarker_effects.items()},
            confidence_scores=confidence,
            mechanism_summary=summary,
        )

    def _map_targets_to_pathways(self, targets: list[str]) -> list[str]:
        """Map protein targets to KEGG pathways."""
        pathway_map = {
            frozenset(["AMPK", "PPAR-γ", "Glucokinase"]): "Insulin Signaling Pathway (hsa04910)",
            frozenset(["NF-κB", "COX-2", "TNF-α", "IL-6"]): "TNF Signaling / NF-κB Pathway (hsa04668)",
            frozenset(["PCSK9", "HMGCR", "HMG-CoA"]): "Cholesterol Biosynthesis (hsa00100)",
            frozenset(["eNOS", "ACE", "AT1R"]): "Renin-Angiotensin / NO Pathway (hsa04614)",
            frozenset(["PI3K", "AKT1", "MAPK"]): "PI3K-AKT Signaling Pathway (hsa04151)",
            frozenset(["SIRT1", "Nrf2"]): "Cellular Response to Oxidative Stress",
            frozenset(["VEGFR", "EGFR"]): "VEGF / ErbB Signaling (hsa04370)",
            frozenset(["PPAR-α", "CETP"]): "PPAR Signaling Pathway (hsa03320)",
            frozenset(["GLP-1R", "DPP-4"]): "Incretin / GLP-1 Signaling",
        }

        found_pathways = []
        targets_upper = {t.upper() for t in targets}
        for pathway_targets, pathway_name in pathway_map.items():
            if any(pt.upper() in targets_upper for pt in pathway_targets):
                found_pathways.append(pathway_name)

        return found_pathways if found_pathways else ["General metabolic regulation"]

    def _generate_mechanism_summary(
        self,
        compound: str,
        targets: list[str],
        diseases: list[str],
        effects: dict[str, float],
    ) -> str:
        """Generate human-readable mechanism summary."""
        top_targets = targets[:3]
        top_effects = sorted(effects.items(), key=lambda x: abs(x[1]), reverse=True)[:3]

        effects_str = ", ".join(
            f"{'reduces' if v < 0 else 'increases'} {k} by {abs(v):.1f}"
            for k, v in top_effects
        )

        return (
            f"{compound} acts primarily via {', '.join(top_targets)}. "
            f"This translates to predicted effects that {effects_str}. "
            f"Relevant to: {', '.join(diseases[:3])}."
        )

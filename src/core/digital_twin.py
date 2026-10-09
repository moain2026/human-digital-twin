"""
HumanDigitalTwin — Main Orchestrator
The central engine that coordinates all simulation layers.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..core.patient.models import PatientDigitalTwin, Biomarkers
from ..natural_products.database.compound_db import NaturalProductsDB
from ..prediction.network_pharmacology.analyzer import NetworkPharmacologyAnalyzer
from ..simulation.pbpk.engine import CompoundProperties, DosingRegimen, PBPKEngine
from ..simulation.glucose.bergman import (
    BergmanParameters,
    BergmanGlucoseSimulator,
    MealInput,
    NaturalProductIntervention,
)

logger = logging.getLogger(__name__)


@dataclass
class InterventionScenario:
    """A scenario to test on the digital twin."""
    compounds: list[str]                           # Compound names to test
    doses_mg: dict[str, float]                     # Compound → dose in mg
    meals: Optional[list[MealInput]] = None        # Meal inputs (for glucose sim)
    simulation_hours: float = 72.0
    include_glucose_simulation: bool = True
    include_pbpk: bool = True
    include_network_pharmacology: bool = True
    include_interaction_check: bool = True


@dataclass
class SimulationReport:
    """Complete simulation report for an intervention scenario."""
    patient_id: str
    scenario_compounds: list[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Results
    pbpk_results: dict = field(default_factory=dict)
    glucose_results: dict = field(default_factory=dict)
    network_pharmacology: dict = field(default_factory=dict)
    biomarker_predictions: dict = field(default_factory=dict)
    interaction_assessment: dict = field(default_factory=dict)
    safety_flags: list[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0

    def to_summary(self) -> str:
        lines = [
            f"📊 Simulation Report — {', '.join(self.scenario_compounds)}",
            f"   Patient: {self.patient_id}",
            f"   Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "🧪 PBPK Results:",
        ]
        for name, r in self.pbpk_results.items():
            lines.append(f"   {name}: Cmax={r.get('Cmax_mg_L',0):.3f} mg/L, t½={r.get('t_half_h','?')}h, AUC={r.get('AUC_mg_L_h',0):.3f}")

        if self.glucose_results:
            lines.extend(["", "🩸 Glucose Impact:"])
            b = self.glucose_results.get("baseline", {})
            t = self.glucose_results.get("treated", {})
            if b and t:
                delta_peak = t.get("peak_glucose_mmol_L", 0) - b.get("peak_glucose_mmol_L", 0)
                delta_auc = t.get("glucose_auc", 0) - b.get("glucose_auc", 0)
                lines.append(f"   Peak glucose change: {delta_peak:+.2f} mmol/L")
                lines.append(f"   Glucose AUC change: {delta_auc:+.1f}")
                lines.append(f"   Time in Range: {t.get('time_in_range_percent',0):.1f}% (vs {b.get('time_in_range_percent',0):.1f}% baseline)")

        lines.extend(["", "📈 Predicted Biomarker Changes:"])
        for bm, effect in sorted(self.biomarker_predictions.items(), key=lambda x: abs(x[1]), reverse=True):
            arrow = "↓" if effect < 0 else "↑"
            lines.append(f"   {arrow} {bm}: {effect:+.2f}")

        if self.interaction_assessment:
            risk = self.interaction_assessment.get("risk", "unknown")
            emoji = "🔴" if risk == "high" else "🟡" if risk == "moderate" else "🟢"
            lines.extend(["", f"⚠️ Interaction Risk: {emoji} {risk.upper()}"])
            for detail in self.interaction_assessment.get("details", []):
                lines.append(f"   • {detail}")

        if self.safety_flags:
            lines.extend(["", "🚨 Safety Flags:"])
            for flag in self.safety_flags:
                lines.append(f"   ⚠️ {flag}")

        lines.extend([
            "",
            f"✅ Recommendation: {self.recommendation}",
            f"   Confidence: {self.confidence:.0%}",
        ])
        return "\n".join(lines)


class HumanDigitalTwin:
    """
    Main orchestrator for the Human Digital Twin system.
    Coordinates PBPK, glucose simulation, network pharmacology,
    and biomarker effect prediction.
    """

    def __init__(
        self,
        patient: PatientDigitalTwin,
        compound_db: Optional[NaturalProductsDB] = None,
    ):
        self.patient = patient
        self.db = compound_db or NaturalProductsDB()
        self.np_analyzer = NetworkPharmacologyAnalyzer(compound_db=self.db)

    def run_intervention(self, scenario: InterventionScenario) -> SimulationReport:
        """
        Run full simulation for a given intervention scenario.
        This is the main entry point.
        """
        logger.info(f"Running simulation for: {scenario.compounds}")
        patient_params = self.patient.physiological_parameters()
        report = SimulationReport(
            patient_id=str(self.patient.id),
            scenario_compounds=scenario.compounds,
        )

        # 1. PBPK simulation for each compound
        if scenario.include_pbpk:
            for compound_name in scenario.compounds:
                compound_data = self.db.get(compound_name)
                if not compound_data:
                    logger.warning(f"No data for {compound_name}, skipping PBPK")
                    continue

                # Build CompoundProperties from DB data
                kp_estimates = {}
                try:
                    props = CompoundProperties(
                        name=compound_data["name"],
                        molecular_weight=compound_data.get("molecular_weight", 300),
                        logP=compound_data.get("logP", 2.0),
                        fu_plasma=compound_data.get("fu_plasma", 0.1),
                        fa=min(compound_data.get("oral_bioavailability", 0.5) * 1.2, 1.0),
                        fg=0.85,
                        clint_liver_uL_min_mg=compound_data.get("clint_liver", 50),
                    )

                    dose_mg = scenario.doses_mg.get(compound_name, 500)
                    engine = PBPKEngine(patient_params, props)
                    regimen = DosingRegimen(dose_mg=dose_mg, n_doses=1)

                    result = engine.simulate(
                        regimen,
                        t_end_h=scenario.simulation_hours,
                        patient_id=str(self.patient.id),
                    )
                    report.pbpk_results[compound_name] = result.summary()

                except Exception as e:
                    logger.error(f"PBPK failed for {compound_name}: {e}")

        # 2. Glucose simulation (for relevant compounds)
        if scenario.include_glucose_simulation and scenario.meals:
            try:
                bergman_params = self._get_bergman_params()
                sim = BergmanGlucoseSimulator(bergman_params)

                # Build aggregate intervention from all compounds
                intervention = self._build_glucose_intervention(scenario.compounds)

                baseline, treated = sim.simulate_with_without_intervention(
                    meals=scenario.meals,
                    intervention=intervention,
                )
                report.glucose_results = {
                    "baseline": baseline.summary(),
                    "treated": treated.summary(),
                }
            except Exception as e:
                logger.error(f"Glucose simulation failed: {e}")

        # 3. Network pharmacology
        if scenario.include_network_pharmacology:
            for compound_name in scenario.compounds:
                compound_data = self.db.get(compound_name)
                if not compound_data:
                    continue
                targets = compound_data.get("primary_targets", [])
                if targets:
                    np_result = self.np_analyzer.analyze_from_known_targets(
                        compound_name, targets
                    )
                    report.network_pharmacology[compound_name] = {
                        "targets": np_result.targets,
                        "pathways": np_result.pathways,
                        "diseases": np_result.diseases,
                        "mechanism": np_result.mechanism_summary,
                    }

        # 4. Combined biomarker prediction
        report.biomarker_predictions = self.db.predict_combined_biomarker_effect(
            scenario.compounds
        )

        # 5. Interaction assessment
        if scenario.include_interaction_check:
            report.interaction_assessment = self.db.get_interaction_risk(
                scenario.compounds
            )

        # 6. Safety flags (patient-specific)
        report.safety_flags = self._check_safety(scenario)

        # 7. Generate recommendation
        report.recommendation, report.confidence = self._generate_recommendation(report)

        return report

    def _get_bergman_params(self):
        """Get Bergman parameters appropriate for patient's condition."""
        conditions = [c.lower() for c in self.patient.conditions]
        bm = self.patient.biomarkers

        if any("type 2" in c or "diabetes" in c for c in conditions) or (
            bm.glucose_fasting_mmol_L and bm.glucose_fasting_mmol_L >= 7.0
        ):
            return BergmanParameters.for_type2_diabetes()
        elif bm.glucose_fasting_mmol_L and bm.glucose_fasting_mmol_L >= 5.6:
            return BergmanParameters.for_prediabetes()
        return BergmanParameters.for_healthy()

    def _build_glucose_intervention(
        self, compound_names: list[str]
    ) -> NaturalProductIntervention:
        """Build aggregate glucose intervention from all compounds."""
        total_gi_reduction = 0.0
        total_insulin_sensitivity = 0.0
        total_glucose_effectiveness = 0.0
        total_insulin_secretion = 0.0

        for name in compound_names:
            c = self.db.get(name)
            if not c:
                continue
            effects = c.get("biomarker_effects", {})
            mechs = c.get("mechanisms", [])

            if "antidiabetic" in mechs or "insulin_sensitizer" in mechs:
                g_effect = abs(effects.get("glucose_fasting", 0))
                total_insulin_sensitivity += min(g_effect / 2.0, 0.5)
                total_glucose_effectiveness += min(g_effect / 4.0, 0.3)

            if "alpha_glucosidase_inhibition" in mechs:
                total_gi_reduction += 0.3

        # Piperine enhancement
        if self.db.get("Piperine") and "Piperine" in compound_names:
            total_insulin_sensitivity *= 1.3
            total_gi_reduction *= 1.2

        return NaturalProductIntervention(
            name="+".join(compound_names),
            mechanism="combined",
            gi_reduction_fraction=min(total_gi_reduction, 0.5),
            insulin_sensitivity_increase=min(total_insulin_sensitivity, 1.0),
            glucose_effectiveness_increase=min(total_glucose_effectiveness, 0.5),
            insulin_secretion_increase=min(total_insulin_secretion, 0.3),
        )

    def _check_safety(self, scenario: InterventionScenario) -> list[str]:
        """Patient-specific safety checks."""
        flags = []
        medications = [m.lower() for m in self.patient.current_medications]

        for name in scenario.compounds:
            c = self.db.get(name)
            if not c:
                continue
            cyp_inhibited = c.get("cyp_inhibition", [])

            # CYP3A4 inhibitors + statins
            if "CYP3A4" in cyp_inhibited and any("statin" in m for m in medications):
                flags.append(f"{name} inhibits CYP3A4 — may increase statin levels (monitor)")

            # CYP2C9 inhibitors + warfarin
            if "CYP2C9" in cyp_inhibited and any("warfarin" in m for m in medications):
                flags.append(f"⚠️ {name} inhibits CYP2C9 — SIGNIFICANT interaction with Warfarin")

            # High-dose piperine with medications
            if name.lower() == "piperine" and medications:
                flags.append("Piperine inhibits P-gp and multiple CYPs — review all drug interactions")

            # Check patient biomarkers
            bm = self.patient.biomarkers
            if c.get("interaction_risk") == "high":
                if bm.alt_U_L and bm.alt_U_L > 40:
                    flags.append(f"{name} marked high-risk — elevated ALT detected, monitor liver function")

        return flags

    def _generate_recommendation(self, report: SimulationReport) -> tuple[str, float]:
        """Generate final recommendation and confidence score."""
        risk = report.interaction_assessment.get("risk", "low")
        n_effects = len(report.biomarker_predictions)
        n_positive = sum(1 for v in report.biomarker_predictions.values() if v < 0)  # Most are reductions (good)

        if risk == "high" and report.safety_flags:
            return (
                "⚠️ Use with caution — significant drug interactions detected. Consult physician.",
                0.85,
            )
        elif n_positive >= 3 and risk == "low":
            return (
                "✅ Favorable profile — multiple positive biomarker effects, low interaction risk.",
                0.75,
            )
        elif n_positive >= 1:
            return (
                "🟡 Moderate benefit expected — monitor biomarkers after initiation.",
                0.60,
            )
        else:
            return (
                "Insufficient data for strong recommendation. Proceed with standard monitoring.",
                0.40,
            )

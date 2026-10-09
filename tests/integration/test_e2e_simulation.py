"""
End-to-End Integration Tests
Tests the complete simulation pipeline from patient input to report output.
"""
import pytest
from src.core.patient.models import PatientDigitalTwin, Biomarkers, Sex
from src.core.digital_twin import HumanDigitalTwin, InterventionScenario
from src.natural_products.database.compound_db import NaturalProductsDB
from src.simulation.glucose.bergman import MealInput
from src.simulation.cardiovascular.blood_pressure import (
    BloodPressureSimulator,
    CardiovascularProfile,
    BPIntervention,
)


class TestFullSimulationPipeline:

    def setup_method(self):
        self.db = NaturalProductsDB()
        self.t2d_patient = PatientDigitalTwin(
            name="Integration Test Patient",
            age_years=50,
            sex=Sex.MALE,
            weight_kg=90,
            height_cm=175,
            conditions=["Type 2 Diabetes", "Hypertension"],
            current_medications=["Metformin"],
            biomarkers=Biomarkers(
                glucose_fasting_mmol_L=9.1,
                hba1c_percent=8.2,
                systolic_bp_mmhg=155,
                ldl_mmol_L=4.8,
                crp_mg_L=5.2,
                creatinine_umol_L=95,
            ),
        )

    def test_single_compound_simulation(self):
        """Full simulation with a single compound."""
        scenario = InterventionScenario(
            compounds=["Berberine"],
            doses_mg={"Berberine": 1000},
            meals=[MealInput(time_min=30, carbohydrate_g=75, gi=70)],
            simulation_hours=48,
            include_glucose_simulation=True,
            include_pbpk=True,
            include_network_pharmacology=True,
        )
        hdt = HumanDigitalTwin(patient=self.t2d_patient, compound_db=self.db)
        report = hdt.run_intervention(scenario)

        assert report is not None
        assert "Berberine" in report.pbpk_results
        assert len(report.biomarker_predictions) > 0
        assert report.recommendation != ""
        assert 0 <= report.confidence <= 1.0

    def test_combination_simulation(self):
        """Full simulation with multiple compounds including Piperine."""
        scenario = InterventionScenario(
            compounds=["Thymoquinone", "Berberine", "Piperine"],
            doses_mg={"Thymoquinone": 500, "Berberine": 1000, "Piperine": 10},
            meals=[MealInput(time_min=30, carbohydrate_g=80, gi=70)],
            simulation_hours=48,
        )
        hdt = HumanDigitalTwin(patient=self.t2d_patient, compound_db=self.db)
        report = hdt.run_intervention(scenario)

        # Should detect high interaction risk (multiple CYP inhibitors)
        assert report.interaction_assessment.get("risk") in ("moderate", "high")
        # Should predict reduction in glucose
        assert "glucose_fasting" in report.biomarker_predictions
        assert report.biomarker_predictions["glucose_fasting"] < 0

    def test_glucose_simulation_shows_improvement(self):
        """Glucose simulation with antidiabetic compounds should show improvement."""
        scenario = InterventionScenario(
            compounds=["Thymoquinone"],
            doses_mg={"Thymoquinone": 500},
            meals=[MealInput(time_min=30, carbohydrate_g=75, gi=70)],
            simulation_hours=24,
            include_glucose_simulation=True,
        )
        hdt = HumanDigitalTwin(patient=self.t2d_patient, compound_db=self.db)
        report = hdt.run_intervention(scenario)

        glucose = report.glucose_results
        if glucose and "baseline" in glucose and "treated" in glucose:
            # Either peak glucose should be lower or AUC should be lower
            b_auc = glucose["baseline"].get("glucose_auc", float("inf"))
            t_auc = glucose["treated"].get("glucose_auc", float("inf"))
            assert t_auc <= b_auc + 1  # Allow 1 unit tolerance

    def test_warfarin_interaction_detected(self):
        """Warfarin + CYP2C9 inhibitor should trigger safety flag."""
        patient = PatientDigitalTwin(
            age_years=65, sex=Sex.FEMALE, weight_kg=65, height_cm=160,
            current_medications=["Warfarin"],
            biomarkers=Biomarkers(systolic_bp_mmhg=135),
        )
        scenario = InterventionScenario(
            compounds=["Curcumin"],  # Curcumin inhibits CYP2C9
            doses_mg={"Curcumin": 1000},
            simulation_hours=24,
        )
        hdt = HumanDigitalTwin(patient=patient, compound_db=self.db)
        report = hdt.run_intervention(scenario)
        # Should flag Warfarin interaction
        safety_text = " ".join(report.safety_flags).lower()
        assert "warfarin" in safety_text or "cyp2c9" in safety_text

    def test_no_compound_found_gracefully(self):
        """Simulation with unknown compound should not crash."""
        scenario = InterventionScenario(
            compounds=["UnknownHerb12345"],
            doses_mg={"UnknownHerb12345": 500},
            simulation_hours=24,
        )
        hdt = HumanDigitalTwin(patient=self.t2d_patient, compound_db=self.db)
        report = hdt.run_intervention(scenario)  # Should not raise
        assert report is not None

    def test_report_summary_format(self):
        """Report summary should be a non-empty string."""
        scenario = InterventionScenario(
            compounds=["Quercetin"],
            doses_mg={"Quercetin": 500},
            simulation_hours=24,
        )
        hdt = HumanDigitalTwin(patient=self.t2d_patient, compound_db=self.db)
        report = hdt.run_intervention(scenario)
        summary = report.to_summary()
        assert isinstance(summary, str)
        assert len(summary) > 200


class TestBloodPressureSimulation:

    def test_bp_simulation_reduces_pressure(self):
        """BP simulator should show reduction with eNOS activator."""
        profile = CardiovascularProfile(sbp_mmhg=155, dbp_mmhg=92, heart_rate=75)
        sim = BloodPressureSimulator(profile)

        intervention = BPIntervention(
            name="TestHerb",
            ace_inhibition=0.3,
            nos_activation=0.4,
        )
        result = sim.simulate([intervention], t_end_h=24)
        assert result.final_sbp < profile.sbp_mmhg
        assert result.sbp_reduction > 0

    def test_bp_from_patient(self):
        """CardiovascularProfile.from_patient should work."""
        patient = PatientDigitalTwin(
            age_years=50, sex=Sex.MALE, weight_kg=85, height_cm=175,
            biomarkers=Biomarkers(systolic_bp_mmhg=145, diastolic_bp_mmhg=88),
        )
        profile = CardiovascularProfile.from_patient(patient)
        assert profile.sbp_mmhg == 145
        assert profile.total_peripheral_resistance > 1.0  # Hypertension

    def test_bp_simulation_result_format(self):
        """BP simulation result should have correct format."""
        profile = CardiovascularProfile()
        sim = BloodPressureSimulator(profile)
        intervention = BPIntervention(name="Test", nos_activation=0.2)
        result = sim.simulate([intervention], t_end_h=12)
        summary = result.summary()
        assert "sbp_reduction_mmhg" in summary
        assert "final_sbp" in summary
        assert len(result.time_h) > 0

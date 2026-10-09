"""
Unit tests for PatientDigitalTwin model.
"""
import pytest
from src.core.patient.models import PatientDigitalTwin, Biomarkers, Sex, GeneticProfile


class TestPatientDigitalTwin:
    def setup_method(self):
        self.patient = PatientDigitalTwin(
            name="Test Patient",
            age_years=45,
            sex=Sex.MALE,
            weight_kg=80,
            height_cm=175,
            conditions=["Type 2 Diabetes", "Hypertension"],
            biomarkers=Biomarkers(
                glucose_fasting_mmol_L=8.2,
                hba1c_percent=7.8,
                systolic_bp_mmhg=145,
                ldl_mmol_L=4.2,
                crp_mg_L=4.1,
                creatinine_umol_L=90,
            ),
        )

    def test_bmi_calculation(self):
        bmi = self.patient.bmi
        assert 20 < bmi < 40, f"BMI {bmi} out of expected range"
        assert abs(bmi - 80 / (1.75 ** 2)) < 0.1

    def test_lean_body_weight(self):
        lbw = self.patient.lean_body_weight_kg
        assert lbw > 0
        assert lbw < self.patient.weight_kg

    def test_bsa(self):
        bsa = self.patient.bsa_m2
        assert 1.5 < bsa < 2.5

    def test_creatinine_clearance(self):
        crcl = self.patient.creatinine_clearance_mL_min
        assert crcl > 0
        # For a 45yo male, 80kg, CrCl ~80-100 mL/min expected
        assert 50 < crcl < 150

    def test_physiological_parameters(self):
        params = self.patient.physiological_parameters()
        assert "volumes_L" in params
        assert "flows_L_min" in params
        assert "cardiac_output_L_min" in params
        assert params["cardiac_output_L_min"] > 3
        assert params["cardiac_output_L_min"] < 10
        assert params["volumes_L"]["liver"] > 0

    def test_biomarker_risk_score(self):
        risks = self.patient.biomarkers.risk_score()
        assert "glucose" in risks
        assert risks["glucose"] in ("high", "prediabetic", "diabetic", "normal")
        # With glucose 8.2 mmol/L, should be high
        assert risks["glucose"] == "high"
        # With BP 145, should be high
        assert risks.get("blood_pressure") == "high"

    def test_summary(self):
        summary = self.patient.to_summary()
        assert "Digital Twin" in summary
        assert "Test Patient" in summary

    def test_update_biomarkers(self):
        original_count = len(self.patient.biomarker_history)
        new_bm = Biomarkers(glucose_fasting_mmol_L=7.0)
        self.patient.update_biomarkers(new_bm)
        assert len(self.patient.biomarker_history) == original_count + 1
        assert self.patient.biomarkers.glucose_fasting_mmol_L == 7.0

    def test_female_patient(self):
        female = PatientDigitalTwin(
            age_years=35, sex=Sex.FEMALE, weight_kg=65, height_cm=160
        )
        # CrCl female should be ~85% of male equivalent
        assert female.creatinine_clearance_mL_min > 0

    def test_empty_biomarkers(self):
        patient = PatientDigitalTwin(age_years=30, sex=Sex.MALE, weight_kg=70, height_cm=175)
        risks = patient.biomarkers.risk_score()
        assert isinstance(risks, dict)
        assert len(risks) == 0  # No biomarkers set, no risks computed

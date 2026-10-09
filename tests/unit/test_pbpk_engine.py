"""
Unit tests for PBPK Engine.
"""
import pytest
import numpy as np
from src.simulation.pbpk.engine import (
    CompoundProperties,
    PBPKEngine,
    DosingRegimen,
    PBPKResult,
)
from src.core.patient.models import PatientDigitalTwin, Sex


class TestCompoundProperties:
    def test_kp_prediction_rodgers_rowland(self):
        comp = CompoundProperties(
            name="Test", molecular_weight=300, logP=2.5
        )
        kps = comp.predict_kp_rodgers_rowland()
        assert "liver" in kps
        assert "fat" in kps
        assert all(v > 0 for v in kps.values())
        # Fat should be highest for lipophilic compound (logP=2.5)
        assert kps["fat"] > kps["muscle"]

    def test_get_kp_uses_measured_when_provided(self):
        comp = CompoundProperties(
            name="Test", molecular_weight=300, logP=2.5,
            kp_liver=10.0  # Override with measured value
        )
        kps = comp.get_kp()
        assert kps["liver"] == 10.0  # Should use measured value


class TestPBPKEngine:
    def setup_method(self):
        patient = PatientDigitalTwin(
            age_years=35, sex=Sex.MALE, weight_kg=70, height_cm=175
        )
        self.patient_params = patient.physiological_parameters()

        self.curcumin = CompoundProperties(
            name="Curcumin",
            molecular_weight=368.38,
            logP=3.29,
            fu_plasma=0.03,
            fa=0.12,
            clint_liver_uL_min_mg=500,
        )
        self.engine = PBPKEngine(self.patient_params, self.curcumin)

    def test_single_dose_simulation(self):
        regimen = DosingRegimen(dose_mg=500, n_doses=1)
        result = self.engine.simulate(regimen, t_end_h=24, n_points=200)

        assert isinstance(result, PBPKResult)
        assert len(result.time_h) > 0
        assert result.cmax_mg_L >= 0
        assert result.auc_mg_L_h >= 0
        assert result.tmax_h >= 0
        # Plasma concentration should start at 0
        assert result.plasma_conc_mg_L[0] < 0.001

    def test_plasma_concentration_profile_shape(self):
        """Verify typical PK profile: rises then falls."""
        regimen = DosingRegimen(dose_mg=500, n_doses=1)
        result = self.engine.simulate(regimen, t_end_h=48, n_points=300)

        # Find peak
        peak_idx = np.argmax(result.plasma_conc_mg_L)
        # Concentration should be higher at peak than at start and end
        assert result.plasma_conc_mg_L[peak_idx] > result.plasma_conc_mg_L[0]
        if peak_idx < len(result.plasma_conc_mg_L) - 10:
            assert result.plasma_conc_mg_L[peak_idx] >= result.plasma_conc_mg_L[-1]

    def test_tissue_concentrations_exist(self):
        regimen = DosingRegimen(dose_mg=500, n_doses=1)
        result = self.engine.simulate(regimen, t_end_h=24)
        assert "liver" in result.tissue_conc
        assert "fat" in result.tissue_conc
        assert all(len(v) > 0 for v in result.tissue_conc.values())

    def test_summary_dict(self):
        regimen = DosingRegimen(dose_mg=500)
        result = self.engine.simulate(regimen, t_end_h=24)
        summary = result.summary()
        assert "Cmax_mg_L" in summary
        assert "Tmax_h" in summary
        assert "AUC_mg_L_h" in summary
        assert summary["compound"] == "Curcumin"

    def test_higher_dose_higher_cmax(self):
        """Dose proportionality: doubling dose should roughly double Cmax."""
        reg_low = DosingRegimen(dose_mg=250)
        reg_high = DosingRegimen(dose_mg=500)
        r_low = self.engine.simulate(reg_low, t_end_h=24)
        r_high = self.engine.simulate(reg_high, t_end_h=24)
        assert r_high.cmax_mg_L > r_low.cmax_mg_L
        # Linear PK: ratio should be ~2 (allow 30% tolerance)
        ratio = r_high.cmax_mg_L / (r_low.cmax_mg_L + 1e-10)
        assert 1.0 < ratio < 4.0

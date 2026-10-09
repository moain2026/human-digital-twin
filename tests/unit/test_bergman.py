"""
Unit tests for Bergman Minimal Model glucose simulator.
"""
import pytest
import numpy as np
from src.simulation.glucose.bergman import (
    BergmanGlucoseSimulator,
    BergmanParameters,
    MealInput,
    NaturalProductIntervention,
)


class TestBergmanSimulator:
    def setup_method(self):
        self.params = BergmanParameters.for_type2_diabetes()
        self.sim = BergmanGlucoseSimulator(self.params)
        self.meal = MealInput(time_min=30, carbohydrate_g=75, gi=70)

    def test_fasting_baseline_stable(self):
        """Without meals, glucose should remain near basal."""
        result = self.sim.simulate(meals=[], t_end_min=120)
        assert abs(result.glucose_mmol_L[-1] - self.params.gb) < 1.0

    def test_meal_raises_glucose(self):
        result = self.sim.simulate(meals=[self.meal], t_end_min=240)
        assert result.peak_glucose > self.params.gb

    def test_glucose_returns_to_baseline(self):
        result = self.sim.simulate(meals=[self.meal], t_end_min=480)
        # After 8 hours, glucose should be back near basal
        assert result.glucose_mmol_L[-1] < result.peak_glucose

    def test_intervention_reduces_peak(self):
        """A glucose-lowering intervention should reduce peak glucose."""
        intervention = NaturalProductIntervention(
            name="TestHerb",
            mechanism="antidiabetic",
            gi_reduction_fraction=0.2,
            insulin_sensitivity_increase=0.3,
        )
        result_baseline = self.sim.simulate(meals=[self.meal], t_end_min=240)
        result_treated = self.sim.simulate(meals=[self.meal], intervention=intervention, t_end_min=240)
        assert result_treated.peak_glucose <= result_baseline.peak_glucose

    def test_summary_dict(self):
        result = self.sim.simulate(meals=[self.meal], t_end_min=240)
        summary = result.summary()
        assert "peak_glucose_mmol_L" in summary
        assert "glucose_auc" in summary
        assert "time_in_range_percent" in summary
        assert 0 <= summary["time_in_range_percent"] <= 100

    def test_with_without_comparison(self):
        intervention = NaturalProductIntervention(
            name="Berberine",
            mechanism="antidiabetic",
            insulin_sensitivity_increase=0.4,
        )
        baseline, treated = self.sim.simulate_with_without_intervention(
            meals=[self.meal],
            intervention=intervention,
        )
        assert baseline.peak_glucose > 0
        assert treated.peak_glucose > 0

    def test_parameters_for_healthy(self):
        healthy_sim = BergmanGlucoseSimulator(BergmanParameters.for_healthy())
        result = healthy_sim.simulate(meals=[self.meal], t_end_min=240)
        # Healthy patient should have lower peak glucose than T2D
        t2d_result = self.sim.simulate(meals=[self.meal], t_end_min=240)
        assert result.peak_glucose < t2d_result.peak_glucose

    def test_meal_input_appearance_rate(self):
        m = MealInput(time_min=0, carbohydrate_g=60, gi=70)
        # Before meal: 0
        assert m.glucose_appearance_rate(-1) == 0
        # After meal window: 0
        assert m.glucose_appearance_rate(100) == 0
        # During absorption: > 0
        assert m.glucose_appearance_rate(30) > 0

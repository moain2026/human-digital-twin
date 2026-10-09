"""
Bergman Minimal Model — Glucose-Insulin Dynamics
The FDA-accepted model for glucose metabolism simulation.

Reference: Bergman & Cobelli (1979, 1980)
           Cobelli et al. (2014) — FDA-approved UVa/PADOVA extension
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp

logger = logging.getLogger(__name__)


@dataclass
class BergmanParameters:
    """
    Bergman Minimal Model parameters.
    Can be estimated from IVGTT or FSIGT data,
    or use population-typical values stratified by condition.
    """
    # Glucose subsystem
    sg: float = 0.028           # Glucose effectiveness (min^-1)
    p2: float = 0.028           # Rate constant for remote insulin (min^-1)
    p3: float = 5.0e-5          # Insulin action on glucose (min^-2 per μU/mL)
    gb: float = 5.0             # Basal glucose (mmol/L)

    # Insulin subsystem
    n: float = 0.142            # Rate constant for insulin decay (min^-1)
    ib: float = 50.0            # Basal insulin (pmol/L → convert to μU/mL: ÷ 6)

    # Beta-cell function (gamma model)
    gamma: float = 0.5          # Beta-cell response to glucose above threshold
    h: float = 5.5              # Glucose threshold for insulin secretion (mmol/L)

    @classmethod
    def for_type2_diabetes(cls) -> "BergmanParameters":
        """Typical parameters for T2D patient."""
        return cls(sg=0.015, p2=0.020, p3=2.5e-5, gb=7.5, n=0.12, gamma=0.2, h=7.0)

    @classmethod
    def for_prediabetes(cls) -> "BergmanParameters":
        return cls(sg=0.022, p2=0.025, p3=4.0e-5, gb=6.0, n=0.13, gamma=0.35, h=6.0)

    @classmethod
    def for_healthy(cls) -> "BergmanParameters":
        return cls()


@dataclass
class MealInput:
    """Glucose appearance from a meal."""
    time_min: float
    carbohydrate_g: float
    gi: float = 70.0    # Glycaemic Index (0–100)

    def glucose_appearance_rate(self, t: float) -> float:
        """
        Triangular meal absorption profile.
        Peak at 30 min post-meal, returns to 0 at 90 min.
        Returns mmol/L/min (for 1 L distribution volume approximation).
        """
        delta = t - self.time_min
        total_glucose_mmol = self.carbohydrate_g * (self.gi / 100) * 1000 / 180.16  # g→mmol
        # Distribute over 90 min absorption window
        if delta < 0 or delta > 90:
            return 0.0
        elif delta <= 30:
            return total_glucose_mmol * (2 * delta / (90 * 30))
        else:
            return total_glucose_mmol * (2 * (90 - delta) / (90 * 60))


@dataclass
class NaturalProductIntervention:
    """
    Models the effect of a natural product on glucose dynamics.
    Based on known mechanisms (alpha-glucosidase inhibition, insulin sensitization, etc.).
    """
    name: str
    mechanism: str   # "alpha_glucosidase_inhibition", "insulin_sensitization", "beta_cell_protection"

    # Effect magnitudes (from PBPK + literature)
    gi_reduction_fraction: float = 0.0          # Reduces GI of meal
    insulin_sensitivity_increase: float = 0.0   # Increases p3 (fraction)
    glucose_effectiveness_increase: float = 0.0  # Increases Sg (fraction)
    insulin_secretion_increase: float = 0.0      # Increases gamma (fraction)

    onset_h: float = 0.5      # Time to onset of effect
    duration_h: float = 4.0   # Duration of effect

    def effect_multiplier(self, t_min: float) -> float:
        """Smooth on/off effect profile (trapezoidal)."""
        t_h = t_min / 60
        if t_h < self.onset_h:
            return t_h / self.onset_h
        elif t_h < self.duration_h:
            return 1.0
        elif t_h < self.duration_h + self.onset_h:
            return (self.duration_h + self.onset_h - t_h) / self.onset_h
        return 0.0


@dataclass
class GlucoseSimResult:
    time_min: np.ndarray
    glucose_mmol_L: np.ndarray
    insulin_pmol_L: np.ndarray
    remote_insulin: np.ndarray

    @property
    def glucose_auc(self) -> float:
        return float(np.trapezoid(self.glucose_mmol_L, self.time_min))

    @property
    def peak_glucose(self) -> float:
        return float(np.max(self.glucose_mmol_L))

    @property
    def peak_time_min(self) -> float:
        return float(self.time_min[np.argmax(self.glucose_mmol_L)])

    @property
    def time_in_range_percent(self) -> float:
        """% time glucose in 3.9–10.0 mmol/L (standard TIR definition)."""
        in_range = (self.glucose_mmol_L >= 3.9) & (self.glucose_mmol_L <= 10.0)
        return 100.0 * np.sum(in_range) / len(in_range)

    def summary(self) -> dict:
        return {
            "peak_glucose_mmol_L": round(self.peak_glucose, 2),
            "peak_time_min": round(self.peak_time_min, 0),
            "glucose_auc": round(self.glucose_auc, 1),
            "time_in_range_percent": round(self.time_in_range_percent, 1),
            "final_glucose_mmol_L": round(float(self.glucose_mmol_L[-1]), 2),
        }


class BergmanGlucoseSimulator:
    """
    Bergman Minimal Model simulator.
    Predicts glucose-insulin dynamics including meal responses
    and the effect of natural product interventions.
    """

    def __init__(self, params: BergmanParameters):
        self.params = params

    def _odes(
        self,
        t: float,
        y: np.ndarray,
        meals: list[MealInput],
        intervention: Optional[NaturalProductIntervention],
    ) -> np.ndarray:
        G, X, I = y  # glucose, remote insulin effect, insulin

        p = self.params
        eff = intervention.effect_multiplier(t) if intervention else 0.0

        # Modified parameters based on natural product effect
        sg_eff = p.sg * (1 + eff * (intervention.glucose_effectiveness_increase if intervention else 0))
        p3_eff = p.p3 * (1 + eff * (intervention.insulin_sensitivity_increase if intervention else 0))
        gamma_eff = p.gamma * (1 + eff * (intervention.insulin_secretion_increase if intervention else 0))

        # Meal glucose appearance
        Ra = sum(m.glucose_appearance_rate(t) for m in meals)
        # GI reduction (e.g., acarbose-like mechanism)
        if intervention:
            Ra *= (1 - eff * intervention.gi_reduction_fraction)

        # ODEs
        dG = -sg_eff * (G - p.gb) - X * G + Ra
        dX = -p2 * X + p3_eff * (I / 6 - p.ib / 6)  # Convert pmol/L to μU/mL (/6)
        # Insulin secretion (simplified linear above threshold)
        insulin_secretion = gamma_eff * max(G - p.h, 0) if G > p.h else 0
        dI = -p.n * (I - p.ib) + insulin_secretion * 6  # Convert to pmol/L (*6)

        p2 = self.params.p2  # Local reference for closure
        return [dG, dX, dI]

    def simulate(
        self,
        meals: list[MealInput],
        intervention: Optional[NaturalProductIntervention] = None,
        t_end_min: float = 480.0,   # 8 hours
        n_points: int = 1000,
    ) -> GlucoseSimResult:
        """Run glucose simulation."""
        p = self.params
        y0 = [p.gb, 0.0, p.ib]
        t_eval = np.linspace(0, t_end_min, n_points)

        p2_local = p.p2  # Capture for ODE closure

        def odes_wrapper(t, y):
            G, X, I = y
            sg_eff = p.sg
            p3_eff = p.p3
            gamma_eff = p.gamma
            eff = 0.0

            if intervention:
                eff = intervention.effect_multiplier(t)
                sg_eff = p.sg * (1 + eff * intervention.glucose_effectiveness_increase)
                p3_eff = p.p3 * (1 + eff * intervention.insulin_sensitivity_increase)
                gamma_eff = p.gamma * (1 + eff * intervention.insulin_secretion_increase)

            Ra = sum(m.glucose_appearance_rate(t) for m in meals)
            if intervention and eff > 0:
                Ra *= (1 - eff * intervention.gi_reduction_fraction)

            dG = -sg_eff * (G - p.gb) - X * G + Ra
            dX = -p2_local * X + p3_eff * (I / 6 - p.ib / 6)
            insulin_sec = gamma_eff * max(G - p.h, 0) if G > p.h else 0
            dI = -p.n * (I - p.ib) + insulin_sec * 6

            return [dG, dX, dI]

        sol = solve_ivp(
            odes_wrapper,
            [0, t_end_min],
            y0,
            t_eval=t_eval,
            method="LSODA",
            rtol=1e-6,
            atol=1e-9,
        )

        if not sol.success:
            raise RuntimeError(f"Glucose simulation failed: {sol.message}")

        return GlucoseSimResult(
            time_min=sol.t,
            glucose_mmol_L=np.clip(sol.y[0], 0, 30),
            insulin_pmol_L=np.clip(sol.y[2], 0, 2000),
            remote_insulin=sol.y[1],
        )

    def simulate_with_without_intervention(
        self,
        meals: list[MealInput],
        intervention: NaturalProductIntervention,
        t_end_min: float = 480.0,
    ) -> tuple[GlucoseSimResult, GlucoseSimResult]:
        """Compare patient response with and without the natural product."""
        baseline = self.simulate(meals, intervention=None, t_end_min=t_end_min)
        treated = self.simulate(meals, intervention=intervention, t_end_min=t_end_min)
        return baseline, treated

"""
Cardiovascular Simulation — Blood Pressure & Hemodynamics
Implements a simplified version of the Guyton-Hall blood pressure regulation model.

Key mechanisms modeled:
1. Renin-Angiotensin-Aldosterone System (RAAS)
2. Sympathetic nervous system
3. Baroreflex
4. Sodium/fluid balance
5. Natural product interventions (e.g., ACE inhibition, eNOS activation)

References:
- Hall (2011) Guyton and Hall Textbook of Medical Physiology 12th ed.
- Moss & Kazmierczak (2012) PLOS Comput Biol doi:10.1371/journal.pcbi.1002571
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp

logger = logging.getLogger(__name__)


@dataclass
class CardiovascularProfile:
    """
    Patient cardiovascular baseline parameters.
    """
    # Baseline pressures
    sbp_mmhg: float = 120.0    # Systolic BP
    dbp_mmhg: float = 80.0     # Diastolic BP

    # Derived
    map_mmhg: float = 93.3     # Mean arterial pressure = DBP + (SBP-DBP)/3

    # Cardiac parameters
    heart_rate: float = 70.0    # bpm
    stroke_volume_mL: float = 70.0
    cardiac_output_L_min: float = 4.9

    # Vascular parameters
    total_peripheral_resistance: float = 1.0  # Normalized (1.0 = normal)
    arterial_compliance: float = 1.0           # Normalized

    # RAAS activity (normalized, 1.0 = normal)
    renin_activity: float = 1.0
    angiotensin_II: float = 1.0
    aldosterone: float = 1.0

    # Sodium/fluid balance
    fluid_volume_L: float = 5.0   # Plasma volume
    sodium_balance: float = 0.0   # Positive = retention

    @classmethod
    def from_patient(cls, patient) -> "CardiovascularProfile":
        """Initialize from patient biomarkers."""
        bm = patient.biomarkers
        sbp = bm.systolic_bp_mmhg or 120
        dbp = bm.diastolic_bp_mmhg or 80
        hr = bm.heart_rate_bpm or 70

        # Hypertension: increased RAAS and TPR
        if sbp >= 140:
            raas = 1.3
            tpr = 1.4
        elif sbp >= 130:
            raas = 1.1
            tpr = 1.2
        else:
            raas = 1.0
            tpr = 1.0

        return cls(
            sbp_mmhg=sbp,
            dbp_mmhg=dbp,
            map_mmhg=dbp + (sbp - dbp) / 3,
            heart_rate=hr,
            total_peripheral_resistance=tpr,
            renin_activity=raas,
            angiotensin_II=raas,
            aldosterone=raas,
        )


@dataclass
class BPIntervention:
    """
    Blood pressure intervention via natural product mechanisms.
    """
    name: str
    # Mechanism effects (0 = no effect, 1 = full effect at max dose)
    ace_inhibition: float = 0.0       # ACE inhibitor-like (reduces Ang II)
    nos_activation: float = 0.0       # eNOS activation (vasodilation → ↓ TPR)
    diuretic_effect: float = 0.0      # Reduces fluid volume
    beta_blockade: float = 0.0        # Reduces heart rate/contractility
    calcium_antagonism: float = 0.0   # Reduces TPR (vasodilation)
    sympatholytic: float = 0.0        # Reduces sympathetic tone

    onset_h: float = 2.0
    peak_effect_h: float = 6.0
    duration_h: float = 24.0

    def effect_at_time(self, t_h: float) -> float:
        """Smooth time-dependent effect profile."""
        if t_h < self.onset_h:
            return (t_h / self.onset_h) ** 2
        elif t_h < self.peak_effect_h:
            return self.onset_h / self.peak_effect_h + (t_h - self.onset_h) / (self.peak_effect_h - self.onset_h) * (1 - self.onset_h / self.peak_effect_h)
        elif t_h < self.duration_h:
            return 1.0 - (t_h - self.peak_effect_h) / (self.duration_h - self.peak_effect_h) * 0.3
        return 0.7  # Sustained partial effect (tachyphylaxis)

    @classmethod
    def from_compound(cls, compound_data: dict, dose_mg: float = 500) -> "BPIntervention":
        """Build intervention from compound database entry."""
        mechanisms = compound_data.get("mechanisms", [])
        targets = compound_data.get("primary_targets", [])
        dose_factor = min(dose_mg / 500, 2.0) / 2.0  # Scale 0–1

        ace_inh = 0.2 * dose_factor if "ACE" in targets else 0.0
        nos_act = 0.3 * dose_factor if "eNOS" in targets else 0.0
        diur = 0.1 * dose_factor if "antihypertensive" in mechanisms else 0.0
        beta = 0.1 * dose_factor if "AT1R" in targets else 0.0
        ca_ant = 0.15 * dose_factor if "antihypertensive" in mechanisms else 0.0

        return cls(
            name=compound_data["name"],
            ace_inhibition=ace_inh,
            nos_activation=nos_act,
            diuretic_effect=diur,
            beta_blockade=beta,
            calcium_antagonism=ca_ant,
        )


@dataclass
class BPSimResult:
    time_h: np.ndarray
    sbp: np.ndarray
    dbp: np.ndarray
    map_p: np.ndarray
    heart_rate: np.ndarray
    cardiac_output: np.ndarray

    @property
    def mean_sbp(self) -> float:
        return float(np.mean(self.sbp))

    @property
    def final_sbp(self) -> float:
        return float(self.sbp[-1])

    @property
    def sbp_reduction(self) -> float:
        return float(self.sbp[0] - self.sbp[-1])

    def summary(self) -> dict:
        return {
            "initial_sbp": round(float(self.sbp[0]), 1),
            "final_sbp": round(self.final_sbp, 1),
            "sbp_reduction_mmhg": round(self.sbp_reduction, 1),
            "initial_dbp": round(float(self.dbp[0]), 1),
            "final_dbp": round(float(self.dbp[-1]), 1),
            "dbp_reduction_mmhg": round(float(self.dbp[0] - self.dbp[-1]), 1),
            "mean_sbp_over_period": round(self.mean_sbp, 1),
        }


class BloodPressureSimulator:
    """
    Simplified Guyton-Hall blood pressure regulation simulator.
    Predicts BP response to natural product interventions over time.
    """

    def __init__(self, profile: CardiovascularProfile):
        self.profile = profile

    def simulate(
        self,
        interventions: list[BPIntervention],
        t_end_h: float = 24.0,
        n_points: int = 200,
    ) -> BPSimResult:
        """Simulate blood pressure response to interventions."""
        p = self.profile

        # Initial state: [MAP, TPR, HR, volume]
        # All normalized: MAP in mmHg, TPR/HR as fractions
        y0 = [
            p.map_mmhg,
            p.total_peripheral_resistance,
            p.heart_rate,
            p.fluid_volume_L,
        ]
        t_eval = np.linspace(0, t_end_h, n_points)

        def odes(t: float, y: list) -> list:
            MAP, TPR, HR, vol = y

            # Combined intervention effect at time t
            total_ace = sum(i.ace_inhibition * i.effect_at_time(t) for i in interventions)
            total_nos = sum(i.nos_activation * i.effect_at_time(t) for i in interventions)
            total_diur = sum(i.diuretic_effect * i.effect_at_time(t) for i in interventions)
            total_beta = sum(i.beta_blockade * i.effect_at_time(t) for i in interventions)
            total_ca = sum(i.calcium_antagonism * i.effect_at_time(t) for i in interventions)

            # Target TPR (reduced by NO and Ca antagonism)
            tpr_target = p.total_peripheral_resistance * (
                1 - 0.4 * total_nos - 0.3 * total_ca - 0.2 * total_ace
            )
            tpr_target = max(0.5, tpr_target)

            # Target HR (reduced by beta blockade)
            hr_target = p.heart_rate * (1 - 0.3 * total_beta)
            hr_target = max(50, hr_target)

            # Target volume (reduced by diuretics)
            vol_target = p.fluid_volume_L * (1 - 0.15 * total_diur)
            vol_target = max(3.0, vol_target)

            # Baroreflex: slow adaptation (tau = 2h)
            tau_tpr = 2.0
            tau_hr = 1.0
            tau_vol = 12.0

            dTPR = (tpr_target - TPR) / tau_tpr
            dHR = (hr_target - HR) / tau_hr
            dVol = (vol_target - vol) / tau_vol

            # MAP = CO × TPR; CO = HR × SV (SV ~ vol)
            sv = vol / p.fluid_volume_L * p.stroke_volume_mL
            CO = HR * sv / 1000  # L/min
            MAP_target = CO * TPR * 20  # Scaling factor
            tau_map = 0.5
            dMAP = (MAP_target - MAP) / tau_map

            return [dMAP, dTPR, dHR, dVol]

        sol = solve_ivp(
            odes, [0, t_end_h], y0, t_eval=t_eval,
            method="LSODA", rtol=1e-4, atol=1e-6,
        )

        if not sol.success:
            logger.warning(f"BP simulation failed: {sol.message}")
            return BPSimResult(
                time_h=t_eval,
                sbp=np.full(n_points, p.sbp_mmhg),
                dbp=np.full(n_points, p.dbp_mmhg),
                map_p=np.full(n_points, p.map_mmhg),
                heart_rate=np.full(n_points, p.heart_rate),
                cardiac_output=np.full(n_points, p.cardiac_output_L_min),
            )

        MAP = sol.y[0]
        TPR = sol.y[1]
        HR = sol.y[2]
        vol = sol.y[3]
        sv = vol / p.fluid_volume_L * p.stroke_volume_mL
        CO = HR * sv / 1000

        # Convert MAP to SBP/DBP (pulse pressure proportional to CO*TPR)
        pp = 40 * (CO / p.cardiac_output_L_min)  # Pulse pressure
        sbp = MAP + pp / 3 * 2
        dbp = MAP - pp / 3

        return BPSimResult(
            time_h=sol.t,
            sbp=np.clip(sbp, 60, 250),
            dbp=np.clip(dbp, 40, 150),
            map_p=np.clip(MAP, 50, 200),
            heart_rate=np.clip(HR, 40, 200),
            cardiac_output=np.clip(CO, 1, 15),
        )

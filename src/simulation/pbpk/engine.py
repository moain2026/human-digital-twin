"""
PBPK Engine — Physiologically Based Pharmacokinetic Simulation
Implements a multi-compartment PBPK model for natural products.

Based on:
- Rowland & Tozer (2011) Clinical Pharmacokinetics and Pharmacodynamics
- ICRP Publication 89 (physiological data)
- FDA MIDD PBPK Guidance (2018)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


@dataclass
class CompoundProperties:
    """
    Physicochemical and ADME properties of a compound.
    These are used to parameterize the PBPK model.
    """
    name: str
    molecular_weight: float          # g/mol
    logP: float                       # Lipophilicity
    pKa: Optional[float] = None       # Acid dissociation constant
    fu_plasma: float = 0.5            # Fraction unbound in plasma (0–1)
    fu_mic: float = 0.5               # Fraction unbound in microsomal assay
    blood_plasma_ratio: float = 1.0   # Cb/Cp ratio
    fa: float = 0.9                   # Fraction absorbed (gut)
    fg: float = 0.8                   # Gut availability (first-pass)

    # Metabolic clearance
    clint_liver_uL_min_mg: float = 10.0   # Intrinsic hepatic clearance
    clint_gut_uL_min_mg: float = 0.0      # Gut wall clearance
    cl_renal_mL_min: float = 0.0          # Renal clearance

    # Tissue partition coefficients (Kp)
    # Predicted using Rodgers & Rowland method if not provided
    kp_liver: Optional[float] = None
    kp_kidney: Optional[float] = None
    kp_gut: Optional[float] = None
    kp_muscle: Optional[float] = None
    kp_fat: Optional[float] = None
    kp_brain: Optional[float] = None
    kp_lung: Optional[float] = None
    kp_skin: Optional[float] = None

    # Bioavailability (calculated or measured)
    bioavailability: Optional[float] = None

    def predict_kp_rodgers_rowland(self) -> dict[str, float]:
        """
        Predict tissue partition coefficients using Rodgers & Rowland (2005) method.
        Simplified implementation for neutral lipophilic compounds.
        """
        # Tissue composition data (fraction water, neutral lipid, phospholipid)
        tissue_comp = {
            "liver":  {"fw": 0.751, "fn": 0.0348, "fp": 0.0252},
            "kidney": {"fw": 0.783, "fn": 0.0123, "fp": 0.0162},
            "gut":    {"fw": 0.718, "fn": 0.0375, "fp": 0.0125},
            "muscle": {"fw": 0.760, "fn": 0.0238, "fp": 0.0072},
            "fat":    {"fw": 0.135, "fn": 0.853,  "fp": 0.0016},
            "brain":  {"fw": 0.771, "fn": 0.0346, "fp": 0.0533},
            "lung":   {"fw": 0.811, "fn": 0.0220, "fp": 0.0128},
            "skin":   {"fw": 0.718, "fn": 0.0284, "fp": 0.0112},
        }
        blood_comp = {"fw": 0.796, "fn": 0.00139, "fp": 0.00162}

        P = 10 ** self.logP  # Partition coefficient

        kps = {}
        for tissue, comp in tissue_comp.items():
            # Simplified Rodgers & Rowland for neutral compounds
            kp_num = comp["fw"] + P * comp["fn"] + 0.3 * P * comp["fp"]
            kp_den = blood_comp["fw"] + P * blood_comp["fn"] + 0.3 * P * blood_comp["fp"]
            kps[tissue] = (kp_num / kp_den) / self.blood_plasma_ratio

        return kps

    def get_kp(self) -> dict[str, float]:
        """Get tissue partition coefficients, predicting if not measured."""
        predicted = self.predict_kp_rodgers_rowland()
        return {
            "liver":  self.kp_liver  or predicted["liver"],
            "kidney": self.kp_kidney or predicted["kidney"],
            "gut":    self.kp_gut    or predicted["gut"],
            "muscle": self.kp_muscle or predicted["muscle"],
            "fat":    self.kp_fat    or predicted["fat"],
            "brain":  self.kp_brain  or predicted["brain"],
            "lung":   self.kp_lung   or predicted["lung"],
            "skin":   self.kp_skin   or predicted["skin"],
        }


@dataclass
class DosingRegimen:
    """Oral dosing regimen."""
    dose_mg: float
    frequency_hours: float = 24.0     # Dosing interval
    n_doses: int = 1                   # Number of doses
    first_dose_time_h: float = 0.0


@dataclass
class PBPKResult:
    """Results of a PBPK simulation."""
    time_h: np.ndarray
    plasma_conc_mg_L: np.ndarray
    tissue_conc: dict[str, np.ndarray]
    compound: str
    patient_id: str

    @property
    def cmax_mg_L(self) -> float:
        return float(np.max(self.plasma_conc_mg_L))

    @property
    def tmax_h(self) -> float:
        return float(self.time_h[np.argmax(self.plasma_conc_mg_L)])

    @property
    def auc_mg_L_h(self) -> float:
        return float(np.trapezoid(self.plasma_conc_mg_L, self.time_h))

    @property
    def half_life_h(self) -> Optional[float]:
        """Estimate from terminal elimination phase."""
        try:
            # Use last 30% of time points for terminal slope
            n = len(self.time_h)
            idx = int(n * 0.7)
            t_term = self.time_h[idx:]
            c_term = self.plasma_conc_mg_L[idx:]
            c_term = np.where(c_term > 0, c_term, 1e-10)
            log_c = np.log(c_term)
            slope, _ = np.polyfit(t_term, log_c, 1)
            return abs(np.log(2) / slope) if slope < 0 else None
        except Exception:
            return None

    def summary(self) -> dict:
        return {
            "compound": self.compound,
            "Cmax_mg_L": round(self.cmax_mg_L, 4),
            "Tmax_h": round(self.tmax_h, 2),
            "AUC_mg_L_h": round(self.auc_mg_L_h, 4),
            "t_half_h": round(self.half_life_h, 2) if self.half_life_h else None,
            "liver_Cmax_mg_L": round(float(np.max(self.tissue_conc.get("liver", [0]))), 4),
        }


class PBPKEngine:
    """
    Multi-compartment PBPK model.
    Compartments: central (blood/plasma) + 8 tissues.
    Oral absorption via first-order process.

    ODE system:
        dA_gut/dt   = -ka * A_gut
        dA_tissue/dt = Qf*(Cp - Ct/Kp) - CLt*Ct/Kp  (for each tissue)
        dA_blood/dt  = Sum(Qt*(Ct/Kp - Cp)) - CLh*fu*Cp - CLr*Cp

    where Qf = tissue blood flow, Cp = plasma conc, Ct = tissue conc,
          Kp = tissue partition, CLh = hepatic clearance, CLr = renal clearance
    """

    TISSUES = ["liver", "kidney", "gut", "muscle", "fat", "brain", "lung", "skin"]

    def __init__(self, patient_params: dict, compound: CompoundProperties):
        self.patient = patient_params
        self.compound = compound
        self.kp = compound.get_kp()

        # Volumes (L)
        self.V = patient_params["volumes_L"]
        self.V["blood"] = self.V.get("blood", 5.0)

        # Flows (L/h) — convert from L/min
        self.Q = {k: v * 60 for k, v in patient_params["flows_L_min"].items()}
        self.Q_total = patient_params["cardiac_output_L_min"] * 60

        # Hepatic clearance (L/h)
        # Wells-Shire model: CLh = Qh * (fu * CLint) / (Qh + fu * CLint)
        Qh = self.Q.get("liver", 90.0)  # L/h
        # Scale CLint from in vitro to in vivo
        # MPPGL (microsomal protein per gram liver) ~ 40 mg/g
        # Liver weight ~ 1.5 kg for 70 kg person
        liver_weight_g = self.V.get("liver", 1.5) * 1000
        MPPGL = 40  # mg/g
        scale_factor = liver_weight_g * MPPGL / 1e6  # mg to kg
        clint_invivo = compound.clint_liver_uL_min_mg * scale_factor * 60 / 1000  # L/h
        self.CLh = Qh * (compound.fu_plasma * clint_invivo) / (Qh + compound.fu_plasma * clint_invivo)

        # Renal clearance (L/h)
        self.CLr = compound.cl_renal_mL_min / 1000 * 60  # convert to L/h

        # Absorption rate constant (h-1) — estimated from compound properties
        self.ka = 1.5  # typical for most oral drugs/herbs

    def _odes(self, t: float, y: np.ndarray, dose_rate_fn) -> np.ndarray:
        """
        ODE system for PBPK model.
        State vector: [A_gut, A_blood, A_liver, A_kidney, A_gut_tissue,
                       A_muscle, A_fat, A_brain, A_lung, A_skin]
        Concentrations in mg/L, amounts in mg.
        """
        A_gut = y[0]
        A_blood = y[1]
        tissues_idx = {t: i + 2 for i, t in enumerate(self.TISSUES)}

        # Plasma concentration (mg/L)
        V_blood = self.V.get("blood", 5.0)
        Cp = A_blood / V_blood * self.compound.blood_plasma_ratio

        # Gut absorption
        abs_rate = self.ka * A_gut * self.compound.fa * self.compound.fg

        # Blood/plasma ODE
        dA_blood_dt = abs_rate
        for tissue in self.TISSUES:
            Q_t = self.Q.get(tissue, 1.0)
            V_t = self.V.get(tissue, 1.0)
            Kp_t = self.kp.get(tissue, 1.0)
            A_t = y[tissues_idx[tissue]]
            Ct = A_t / V_t
            dA_blood_dt += Q_t * (Ct / Kp_t - Cp)

        dA_blood_dt -= (self.CLh + self.CLr) * self.compound.fu_plasma * Cp

        # Gut absorption depletion
        dA_gut_dt = -self.ka * A_gut + dose_rate_fn(t)

        # Tissue ODEs
        dy = np.zeros(len(y))
        dy[0] = dA_gut_dt
        dy[1] = dA_blood_dt

        for tissue in self.TISSUES:
            i = tissues_idx[tissue]
            Q_t = self.Q.get(tissue, 1.0)
            V_t = self.V.get(tissue, 1.0)
            Kp_t = self.kp.get(tissue, 1.0)
            A_t = y[i]
            Ct = A_t / V_t
            dy[i] = Q_t * (Cp - Ct / Kp_t)

        return dy

    def simulate(
        self,
        regimen: DosingRegimen,
        t_end_h: float = 72.0,
        n_points: int = 500,
        patient_id: str = "unknown",
    ) -> PBPKResult:
        """Run PBPK simulation for given dosing regimen."""
        logger.info(f"Running PBPK for {self.compound.name}, {regimen.dose_mg}mg × {regimen.n_doses}")

        t_eval = np.linspace(0, t_end_h, n_points)
        y0 = np.zeros(2 + len(self.TISSUES))

        # Build dose input function
        dose_times = [
            regimen.first_dose_time_h + i * regimen.frequency_hours
            for i in range(regimen.n_doses)
        ]

        def dose_rate_fn(t: float) -> float:
            """Instantaneous dose input — modelled as bolus via delta approximation."""
            return 0.0  # Boluses handled as initial conditions per interval

        # Simulate with multiple doses
        all_t = []
        all_y = []
        y_current = y0.copy()

        dose_idx = 0
        t_start = 0.0

        for segment_end in list(dose_times[1:]) + [t_end_h]:
            if dose_idx < len(dose_times):
                # Add dose to gut compartment
                y_current[0] += regimen.dose_mg

            t_segment = np.linspace(t_start, segment_end, max(int(n_points / regimen.n_doses), 50))

            sol = solve_ivp(
                self._odes,
                [t_start, segment_end],
                y_current,
                t_eval=t_segment,
                args=(dose_rate_fn,),
                method="LSODA",
                rtol=1e-6,
                atol=1e-9,
            )

            if sol.success:
                all_t.extend(sol.t.tolist())
                all_y.extend(sol.y.T.tolist())
                y_current = sol.y[:, -1].copy()
            else:
                logger.warning(f"ODE solver failed at segment {t_start}–{segment_end}: {sol.message}")
                # Use last known state
                y_current = y_current

            t_start = segment_end
            dose_idx += 1

        t_arr = np.array(all_t)
        y_arr = np.array(all_y)

        if len(y_arr) == 0:
            raise RuntimeError("PBPK simulation produced no output")

        V_blood = self.V.get("blood", 5.0)
        plasma_conc = y_arr[:, 1] / V_blood * self.compound.blood_plasma_ratio

        tissue_conc = {}
        for i, tissue in enumerate(self.TISSUES):
            V_t = self.V.get(tissue, 1.0)
            tissue_conc[tissue] = y_arr[:, i + 2] / V_t

        return PBPKResult(
            time_h=t_arr,
            plasma_conc_mg_L=np.clip(plasma_conc, 0, None),
            tissue_conc={k: np.clip(v, 0, None) for k, v in tissue_conc.items()},
            compound=self.compound.name,
            patient_id=patient_id,
        )

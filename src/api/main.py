"""
Human Digital Twin — FastAPI Backend
REST API for the HDT simulation platform.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.patient.models import (
    Biomarkers,
    GeneticProfile,
    PatientDigitalTwin,
    Sex,
    EthnicGroup,
)
from ..core.digital_twin import HumanDigitalTwin, InterventionScenario
from ..natural_products.database.compound_db import NaturalProductsDB
from ..simulation.glucose.bergman import MealInput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Human Digital Twin API",
    description="Simulate the effect of natural products on a patient's physiological biomarkers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global compound database
_compound_db = NaturalProductsDB()


# ─── Request / Response schemas ───────────────────────────────────────────────

class BiomarkersInput(BaseModel):
    glucose_fasting_mmol_L: Optional[float] = None
    hba1c_percent: Optional[float] = None
    systolic_bp_mmhg: Optional[float] = None
    diastolic_bp_mmhg: Optional[float] = None
    ldl_mmol_L: Optional[float] = None
    hdl_mmol_L: Optional[float] = None
    triglycerides_mmol_L: Optional[float] = None
    alt_U_L: Optional[float] = None
    ast_U_L: Optional[float] = None
    crp_mg_L: Optional[float] = None
    creatinine_umol_L: Optional[float] = None
    heart_rate_bpm: Optional[float] = None


class PatientInput(BaseModel):
    name: Optional[str] = None
    age_years: float = Field(default=35, ge=18, le=100)
    sex: str = Field(default="male", pattern="^(male|female)$")
    weight_kg: float = Field(default=70, ge=30, le=250)
    height_cm: float = Field(default=170, ge=100, le=220)
    conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    biomarkers: BiomarkersInput = Field(default_factory=BiomarkersInput)


class MealInputSchema(BaseModel):
    time_min: float = Field(default=0, ge=0)
    carbohydrate_g: float = Field(default=60, ge=0, le=300)
    gi: float = Field(default=70, ge=0, le=100)


class SimulationRequest(BaseModel):
    patient: PatientInput
    compounds: list[str] = Field(..., min_items=1, max_items=5)
    doses_mg: dict[str, float] = Field(default_factory=dict)
    meals: Optional[list[MealInputSchema]] = None
    simulation_hours: float = Field(default=72.0, ge=1, le=720)
    include_pbpk: bool = True
    include_glucose: bool = True
    include_network_pharmacology: bool = True


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Human Digital Twin API",
        "version": "0.1.0",
        "status": "operational",
        "compounds_available": len(_compound_db.get_all()),
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/compounds", tags=["Compounds"])
def list_compounds():
    """List all available natural product compounds."""
    return {
        "count": len(_compound_db.get_all()),
        "compounds": [
            {
                "name": c["name"],
                "arabic_name": c.get("arabic_name", ""),
                "plant_source": c.get("plant_source", ""),
                "mechanisms": c.get("mechanisms", []),
                "interaction_risk": c.get("interaction_risk", "unknown"),
            }
            for c in _compound_db.get_all()
        ],
    }


@app.get("/compounds/{name}", tags=["Compounds"])
def get_compound(name: str):
    """Get detailed information about a specific compound."""
    compound = _compound_db.get(name)
    if not compound:
        raise HTTPException(status_code=404, detail=f"Compound '{name}' not found")
    return compound


@app.post("/compounds/interaction-check", tags=["Compounds"])
def check_interactions(compounds: list[str]):
    """Check interaction risks for a combination of compounds."""
    if len(compounds) < 2:
        raise HTTPException(status_code=400, detail="At least 2 compounds required")
    return _compound_db.get_interaction_risk(compounds)


@app.post("/simulate", tags=["Simulation"])
def simulate(request: SimulationRequest):
    """
    Run a full simulation of natural product effects on the patient's digital twin.

    Returns:
    - PBPK pharmacokinetics (Cmax, Tmax, AUC, t½, tissue distribution)
    - Glucose simulation results (if meals provided)
    - Network pharmacology analysis (targets, pathways, diseases)
    - Predicted biomarker changes
    - Drug interaction assessment
    - Safety flags and recommendation
    """
    # Build patient
    bm_input = request.patient.biomarkers
    biomarkers = Biomarkers(
        glucose_fasting_mmol_L=bm_input.glucose_fasting_mmol_L,
        hba1c_percent=bm_input.hba1c_percent,
        systolic_bp_mmhg=bm_input.systolic_bp_mmhg,
        diastolic_bp_mmhg=bm_input.diastolic_bp_mmhg,
        ldl_mmol_L=bm_input.ldl_mmol_L,
        hdl_mmol_L=bm_input.hdl_mmol_L,
        triglycerides_mmol_L=bm_input.triglycerides_mmol_L,
        alt_U_L=bm_input.alt_U_L,
        ast_U_L=bm_input.ast_U_L,
        crp_mg_L=bm_input.crp_mg_L,
        creatinine_umol_L=bm_input.creatinine_umol_L,
        heart_rate_bpm=bm_input.heart_rate_bpm,
    )

    patient = PatientDigitalTwin(
        name=request.patient.name,
        age_years=request.patient.age_years,
        sex=Sex(request.patient.sex),
        weight_kg=request.patient.weight_kg,
        height_cm=request.patient.height_cm,
        conditions=request.patient.conditions,
        current_medications=request.patient.current_medications,
        biomarkers=biomarkers,
    )

    # Build meals
    meals = None
    if request.meals:
        meals = [
            MealInput(
                time_min=m.time_min,
                carbohydrate_g=m.carbohydrate_g,
                gi=m.gi,
            )
            for m in request.meals
        ]

    # Build scenario
    scenario = InterventionScenario(
        compounds=request.compounds,
        doses_mg=request.doses_mg or {c: 500 for c in request.compounds},
        meals=meals,
        simulation_hours=request.simulation_hours,
        include_glucose_simulation=request.include_glucose and meals is not None,
        include_pbpk=request.include_pbpk,
        include_network_pharmacology=request.include_network_pharmacology,
    )

    # Run simulation
    hdt = HumanDigitalTwin(patient=patient, compound_db=_compound_db)
    try:
        report = hdt.run_intervention(scenario)
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "patient_id": report.patient_id,
        "compounds": report.scenario_compounds,
        "timestamp": report.timestamp.isoformat(),
        "pbpk_results": report.pbpk_results,
        "glucose_results": report.glucose_results,
        "network_pharmacology": report.network_pharmacology,
        "biomarker_predictions": report.biomarker_predictions,
        "interaction_assessment": report.interaction_assessment,
        "safety_flags": report.safety_flags,
        "recommendation": report.recommendation,
        "confidence": report.confidence,
        "patient_summary": {
            "bmi": round(patient.bmi, 1),
            "lean_body_weight_kg": round(patient.lean_body_weight_kg, 1),
            "risk_profile": patient.biomarkers.risk_score(),
        },
    }


@app.get("/compounds/{name}/biomarker-effects", tags=["Compounds"])
def get_biomarker_effects(name: str):
    """Get predicted biomarker effects for a single compound."""
    compound = _compound_db.get(name)
    if not compound:
        raise HTTPException(status_code=404, detail=f"Compound '{name}' not found")
    return {
        "compound": compound["name"],
        "biomarker_effects": compound.get("biomarker_effects", {}),
        "mechanisms": compound.get("mechanisms", []),
        "primary_targets": compound.get("primary_targets", []),
        "evidence": compound.get("references", []),
    }

"""
Human Digital Twin — Interactive Streamlit Dashboard
Visual interface for simulating natural product effects on physiological biomarkers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.patient.models import PatientDigitalTwin, Biomarkers, Sex
from src.core.digital_twin import HumanDigitalTwin, InterventionScenario
from src.natural_products.database.compound_db import NaturalProductsDB
from src.simulation.glucose.bergman import MealInput, BergmanGlucoseSimulator, BergmanParameters
from src.simulation.pbpk.engine import CompoundProperties, DosingRegimen, PBPKEngine

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Human Digital Twin",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Load compound DB ─────────────────────────────────────────────────────────
@st.cache_resource
def load_db():
    return NaturalProductsDB()

db = load_db()

# ─── Sidebar — Patient Profile ────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/Human_Digital_Twin-v0.1.0-blue?style=for-the-badge")
    st.markdown("## 👤 Patient Profile")

    patient_name = st.text_input("Name", value="Patient A", key="patient_name")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 18, 100, 45)
        sex = st.selectbox("Sex", ["male", "female"])
    with col2:
        weight = st.number_input("Weight (kg)", 30.0, 250.0, 80.0)
        height = st.number_input("Height (cm)", 100, 220, 170)

    st.markdown("### 🩸 Biomarkers")
    glucose = st.number_input("Fasting Glucose (mmol/L)", 3.0, 20.0, 7.2, 0.1)
    hba1c = st.number_input("HbA1c (%)", 4.0, 15.0, 7.5, 0.1)
    sys_bp = st.number_input("Systolic BP (mmHg)", 80, 200, 138)
    ldl = st.number_input("LDL (mmol/L)", 0.5, 10.0, 3.8, 0.1)
    crp = st.number_input("CRP (mg/L)", 0.0, 50.0, 3.5, 0.1)
    alt = st.number_input("ALT (U/L)", 0, 500, 35)

    conditions = st.multiselect(
        "Conditions",
        ["Type 2 Diabetes", "Hypertension", "Dyslipidemia", "NAFLD", "Obesity"],
        default=["Type 2 Diabetes", "Hypertension"],
    )
    medications = st.multiselect(
        "Current Medications",
        ["Metformin", "Amlodipine", "Atorvastatin", "Warfarin", "Aspirin"],
        default=["Metformin"],
    )

# ─── Main Area ────────────────────────────────────────────────────────────────
st.title("🧬 Human Digital Twin")
st.markdown("*Simulate the effect of natural products on your patient's physiological biomarkers*")

# Compound selection
st.markdown("---")
st.markdown("## 💊 Natural Product Intervention")

all_compounds = [c["name"] for c in db.get_all()]
selected_compounds = st.multiselect(
    "Select compounds to test",
    all_compounds,
    default=["Thymoquinone", "Berberine"],
    max_selections=4,
)

if selected_compounds:
    # Show compound cards
    cols = st.columns(len(selected_compounds))
    doses = {}
    for i, name in enumerate(selected_compounds):
        with cols[i]:
            c = db.get(name)
            if c:
                st.markdown(f"**{c.get('arabic_name', name)}**")
                st.caption(f"🌿 {c.get('plant_source', '')}")
                risk_color = {"low": "🟢", "moderate": "🟡", "high": "🔴"}.get(c.get("interaction_risk", "low"), "⚪")
                st.caption(f"Risk: {risk_color} {c.get('interaction_risk', '').upper()}")
                doses[name] = st.number_input(f"Dose (mg)", 100, 3000, 500, 100, key=f"dose_{name}")

# Meal inputs
st.markdown("### 🍽️ Meal Input (for glucose simulation)")
col_a, col_b, col_c = st.columns(3)
with col_a:
    meal_carbs = st.number_input("Carbohydrates (g)", 0, 200, 75)
with col_b:
    meal_gi = st.number_input("Glycaemic Index", 0, 100, 70)
with col_c:
    meal_time = st.number_input("Meal at (min)", 0, 480, 30)

sim_hours = st.slider("Simulation duration (hours)", 12, 168, 72)

# Run simulation button
run_btn = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

if run_btn and selected_compounds:
    with st.spinner("Running simulation..."):
        # Build patient
        biomarkers = Biomarkers(
            glucose_fasting_mmol_L=glucose,
            hba1c_percent=hba1c,
            systolic_bp_mmhg=sys_bp,
            ldl_mmol_L=ldl,
            crp_mg_L=crp,
            alt_U_L=alt,
        )
        patient = PatientDigitalTwin(
            name=patient_name,
            age_years=age,
            sex=Sex(sex),
            weight_kg=weight,
            height_cm=height,
            conditions=conditions,
            current_medications=medications,
            biomarkers=biomarkers,
        )

        meals = [MealInput(time_min=meal_time, carbohydrate_g=meal_carbs, gi=meal_gi)]
        scenario = InterventionScenario(
            compounds=selected_compounds,
            doses_mg=doses,
            meals=meals,
            simulation_hours=sim_hours,
            include_glucose_simulation=True,
        )

        hdt = HumanDigitalTwin(patient=patient, compound_db=db)
        report = hdt.run_intervention(scenario)

    # ─── Display Results ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📊 Simulation Results")

    # Patient summary cards
    col1, col2, col3, col4 = st.columns(4)
    risk_profile = patient.biomarkers.risk_score()
    with col1:
        st.metric("BMI", f"{patient.bmi:.1f}")
    with col2:
        g_risk = risk_profile.get("glucose", "?")
        st.metric("Glucose Risk", g_risk.upper(), delta=None)
    with col3:
        bp_risk = risk_profile.get("blood_pressure", "?")
        st.metric("BP Risk", bp_risk.upper())
    with col4:
        conf = report.confidence
        st.metric("Sim Confidence", f"{conf:.0%}")

    # Tabs for different result sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Glucose", "💉 PBPK", "🔬 Network Pharmacology", "⚠️ Interactions", "📋 Full Report"
    ])

    with tab1:
        if report.glucose_results:
            baseline = report.glucose_results.get("baseline", {})
            treated = report.glucose_results.get("treated", {})
            if baseline and treated:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    delta = treated.get("peak_glucose_mmol_L", 0) - baseline.get("peak_glucose_mmol_L", 0)
                    st.metric("Peak Glucose", f"{treated.get('peak_glucose_mmol_L', 0):.2f} mmol/L",
                              delta=f"{delta:+.2f}", delta_color="inverse")
                with col_m2:
                    delta_tir = treated.get("time_in_range_percent", 0) - baseline.get("time_in_range_percent", 0)
                    st.metric("Time in Range", f"{treated.get('time_in_range_percent', 0):.1f}%",
                              delta=f"{delta_tir:+.1f}%")
                with col_m3:
                    delta_auc = treated.get("glucose_auc", 0) - baseline.get("glucose_auc", 0)
                    st.metric("Glucose AUC", f"{treated.get('glucose_auc', 0):.1f}",
                              delta=f"{delta_auc:+.1f}", delta_color="inverse")

                # Re-run simulation to get time series for plotting
                bergman_params = BergmanParameters.for_type2_diabetes() if "Type 2 Diabetes" in conditions else BergmanParameters.for_healthy()
                sim = BergmanGlucoseSimulator(bergman_params)
                intervention = hdt._build_glucose_intervention(selected_compounds)
                base_res, treat_res = sim.simulate_with_without_intervention(meals=meals, intervention=intervention, t_end_min=sim_hours * 60)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=base_res.time_min / 60, y=base_res.glucose_mmol_L,
                    name="Baseline", line=dict(color="#e74c3c", dash="dash")
                ))
                fig.add_trace(go.Scatter(
                    x=treat_res.time_min / 60, y=treat_res.glucose_mmol_L,
                    name=f"With {'+'.join(selected_compounds)}", line=dict(color="#2ecc71")
                ))
                # Normal range band
                fig.add_hrect(y0=3.9, y1=10.0, fillcolor="rgba(46,204,113,0.1)", line_width=0, annotation_text="Normal Range")
                fig.add_hline(y=glucose, line_dash="dot", line_color="orange", annotation_text="Fasting baseline")
                fig.update_layout(
                    title="Glucose Response with and without Intervention",
                    xaxis_title="Time (hours)",
                    yaxis_title="Glucose (mmol/L)",
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No glucose results. Ensure meals are configured.")

    with tab2:
        if report.pbpk_results:
            for cname, res in report.pbpk_results.items():
                st.markdown(f"**{cname}**")
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Cmax (mg/L)", f"{res.get('Cmax_mg_L', 0):.4f}")
                with col_b:
                    st.metric("Tmax (h)", f"{res.get('Tmax_h', 0):.1f}")
                with col_c:
                    st.metric("AUC (mg·h/L)", f"{res.get('AUC_mg_L_h', 0):.4f}")
                with col_d:
                    t_half = res.get('t_half_h')
                    st.metric("t½ (h)", f"{t_half:.1f}" if t_half else "N/A")
                st.markdown(f"Liver Cmax: **{res.get('liver_Cmax_mg_L', 0):.4f} mg/L**")
                st.divider()
        else:
            st.info("PBPK results not available for selected compounds.")

    with tab3:
        for cname, np_res in report.network_pharmacology.items():
            with st.expander(f"🔬 {cname}", expanded=True):
                st.markdown(f"**Mechanism:** {np_res.get('mechanism', '')}")
                col_t, col_p = st.columns(2)
                with col_t:
                    st.markdown("**Primary Targets:**")
                    for t in np_res.get("targets", [])[:6]:
                        st.markdown(f"• {t}")
                with col_p:
                    st.markdown("**Pathways:**")
                    for p in np_res.get("pathways", [])[:4]:
                        st.markdown(f"• {p}")
                st.markdown(f"**Diseases addressed:** {', '.join(np_res.get('diseases', []))}")

    with tab4:
        if report.biomarker_predictions:
            st.markdown("### Predicted Biomarker Changes")
            bm_data = report.biomarker_predictions
            df_bm = pd.DataFrame([
                {"Biomarker": k, "Effect": v, "Direction": "Decrease ✅" if v < 0 else "Increase ⚠️"}
                for k, v in bm_data.items()
            ])
            fig_bm = px.bar(
                df_bm, x="Effect", y="Biomarker", orientation="h",
                color="Direction",
                color_discrete_map={"Decrease ✅": "#2ecc71", "Increase ⚠️": "#e74c3c"},
                title="Predicted Biomarker Changes (Combined)"
            )
            st.plotly_chart(fig_bm, use_container_width=True)

        if report.interaction_assessment:
            risk = report.interaction_assessment.get("risk", "unknown")
            risk_emoji = {"low": "🟢", "moderate": "🟡", "high": "🔴"}.get(risk, "⚪")
            st.markdown(f"### {risk_emoji} Interaction Risk: **{risk.upper()}**")
            details = report.interaction_assessment.get("details", [])
            for d in details:
                st.warning(d)

        if report.safety_flags:
            st.markdown("### 🚨 Safety Flags")
            for flag in report.safety_flags:
                st.error(flag)
        else:
            st.success("✅ No major safety flags detected")

    with tab5:
        st.markdown("### Full Simulation Report")
        st.text(report.to_summary())

        # Download report
        report_text = report.to_summary()
        st.download_button(
            "📥 Download Report",
            data=report_text,
            file_name=f"hdt_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )

elif run_btn:
    st.warning("Please select at least one compound to test.")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small>Human Digital Twin v0.1.0 — Built with BioGears methodology + PBPK (ICRP 89) + Bergman Minimal Model + Network Pharmacology</small></center>",
    unsafe_allow_html=True,
)

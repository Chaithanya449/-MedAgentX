"""
Patient intake form component.

Collects basic demographic and self-reported symptom/history data
via a Streamlit form and sends it to the FastAPI backend.
"""

from typing import Any, Dict, Tuple

# pyrefly: ignore [missing-import]
import httpx
# pyrefly: ignore [missing-import]
import streamlit as st


COMMON_SYMPTOMS = [
    "Fatigue",
    "Headache",
    "Fever",
    "Cough",
    "Shortness of breath",
    "Nausea",
    "Joint pain",
    "Sleep difficulty",
    "Anxiety or low mood",
    "Severe breathing difficulty",
    "Other",
]


def render_patient_form() -> Tuple[Dict[str, Any], bool]:
    """Render the patient intake form."""

    st.subheader("Patient Intake")

    with st.form("patient_intake_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=30,
                step=1,
            )

        with col2:
            sex = st.selectbox(
                "Sex assigned at birth",
                ["Female", "Male", "Intersex", "Prefer not to say"],
            )

        symptoms = st.multiselect(
            "Reported symptoms",
            COMMON_SYMPTOMS,
        )

        other_symptom = ""

        if "Other" in symptoms:
            other_symptom = st.text_input(
                "Please describe the other symptom"
            )

        duration_days = st.slider(
            "Duration of symptoms (days)",
            0,
            90,
            3,
        )

        severity = st.select_slider(
            "Self-rated severity",
            options=["Mild", "Moderate", "Severe"],
            value="Mild",
        )
        progression = st.selectbox(
            "Symptom progression",
            ["Improving", "Stable", "Worsening"]
        )

        history = st.text_area(
            "Relevant medical history (conditions, medications, allergies)",
            placeholder="e.g. Type 2 diabetes, taking metformin, no known allergies",
        )

        consent = st.checkbox(
            "I understand this tool does not provide medical diagnoses "
            "and is intended to help organize information for a clinician."
        )

        submitted = st.form_submit_button(
            "Generate Assessment",
            use_container_width=True,
        )

    patient_data: Dict[str, Any] = {
        "age": age,
        "sex": sex,
        "symptoms": [
            s for s in symptoms if s != "Other"
        ] + ([other_symptom] if other_symptom else []),
        "duration_days": duration_days,
        "severity": severity,
        "progression": progression,
        "history": history.strip(),
        "consent": consent,
    }

    if submitted and not consent:
        st.warning(
            "Please confirm the acknowledgement above before continuing."
        )
        submitted = False

    if submitted and not patient_data["symptoms"]:
        st.warning("Please select at least one symptom.")
        submitted = False

    return patient_data, submitted


patient_data, submitted = render_patient_form()

if submitted:
    try:
        response = httpx.post(
            "http://localhost:8000/intake",
            json=patient_data,
            timeout=300.0,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") == "URGENT":
            st.error("⚠️URGENT MEDICAL ATTENTION REQUIRED")
            st.subheader("Safety Alert")
            st.write(f"**Flag:** {result.get('flag')}")
            st.write(f"**Severity:** {result.get('severity')}")
            st.write(f"**Action:** {result.get('action')}")
            st.warning(result.get("message"))
            if result.get("disclaimer"):
                st.info(result["disclaimer"])
        else:
            assessment = result.get("assessment", {})
            risk = result.get("risk", {})

            st.divider()
            st.title("MedAgentX — Patient Assessment")

            st.subheader("Patient Summary")
            st.write(assessment.get("patient_summary", "No summary available."))

            st.subheader("Symptoms")
            for symptom in assessment.get("symptoms", []):
                st.write(f"- {symptom}")

            st.subheader("Clinical Information")
            st.write(f"**Age:** {assessment.get('age')}")
            st.write(f"**Sex:** {assessment.get('sex')}")
            st.write(f"**Duration:** {assessment.get('duration_days')} days")
            st.write(f"**Severity:** {assessment.get('severity')}")
            st.write(f"**Progression:** {assessment.get('progression')}")

            st.subheader("Possible Conditions")
            for condition in assessment.get("possible_conditions", []):
                st.write(f"**{condition.get('condition')}**")
                st.write(condition.get("explanation"))

            st.subheader("Evidence")
            for evidence in assessment.get("evidence", []):
                st.write(f"**Source:** {evidence.get('source')}")
                st.write(evidence.get("explanation"))

            st.subheader("Risk Assessment")
            st.write(f"**Risk Level:** {risk.get('risk_level')}")
            st.write(f"**Urgency:** {risk.get('urgency')}")

            if "disclaimer" in assessment:
                st.warning(assessment["disclaimer"])

    except httpx.ConnectError:
        st.error("Could not connect to the backend. Please make sure FastAPI is running on port 8000.")
    except Exception as exc:
        st.error(f"Error generating assessment: {exc}")

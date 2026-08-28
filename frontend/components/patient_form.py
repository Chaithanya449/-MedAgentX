"""
Patient intake form component.

Collects basic demographic and self-reported symptom/history data
via a Streamlit form and returns it as a plain dict for downstream
processing by the assessment builder.
"""
from typing import Any, Dict, Tuple

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
    "Other",
]


def render_patient_form() -> Tuple[Dict[str, Any], bool]:
    """
    Render the patient intake form.

    Returns:
        (patient_data, submitted) where patient_data is a dict of the
        collected fields and submitted is True only on the render where
        the form was just submitted.
    """
    st.subheader("Patient Intake")

    with st.form("patient_intake_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
        with col2:
            sex = st.selectbox("Sex assigned at birth", ["Female", "Male", "Intersex", "Prefer not to say"])

        symptoms = st.multiselect("Reported symptoms", COMMON_SYMPTOMS)
        other_symptom = ""
        if "Other" in symptoms:
            other_symptom = st.text_input("Please describe the other symptom")

        duration_days = st.slider("Duration of symptoms (days)", 0, 90, 3)
        severity = st.select_slider(
            "Self-rated severity",
            options=["Mild", "Moderate", "Severe"],
            value="Mild",
        )

        history = st.text_area(
            "Relevant medical history (conditions, medications, allergies)",
            placeholder="e.g. Type 2 diabetes, taking metformin, no known allergies",
        )

        consent = st.checkbox(
            "I understand this tool does not provide medical diagnoses and "
            "is intended to help organize information for a clinician."
        )

        submitted = st.form_submit_button("Generate Assessment", use_container_width=True)

    patient_data: Dict[str, Any] = {
        "age": age,
        "sex": sex,
        "symptoms": [s for s in symptoms if s != "Other"] + ([other_symptom] if other_symptom else []),
        "duration_days": duration_days,
        "severity": severity,
        "history": history.strip(),
        "consent": consent,
    }

    if submitted and not consent:
        st.warning("Please confirm the acknowledgement above before continuing.")
        submitted = False

    if submitted and not patient_data["symptoms"]:
        st.warning("Please select at least one symptom.")
        submitted = False

    return patient_data, submitted
"""
Main Streamlit application entrypoint.

Ties together the patient intake form, the assessment builder logic,
the generated report view, and any safety/disclaimer messaging.
"""
import sys
from pathlib import Path

import streamlit as st

# Make the project root importable so we can reach app/assessment
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.patient_form import render_patient_form
from frontend.components.report_view import render_report
from frontend.components.safety_message import render_safety_banner, render_footer_disclaimer
from app.assessment.assessment_builder import AssessmentBuilder


def configure_page() -> None:
    st.set_page_config(
        page_title="Patient Assessment Tool",
        page_icon="🩺",
        layout="centered",
        initial_sidebar_state="collapsed",
    )


def init_session_state() -> None:
    if "assessment_result" not in st.session_state:
        st.session_state.assessment_result = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False


def main() -> None:
    configure_page()
    init_session_state()

    st.title("🩺 Patient Assessment Tool")
    render_safety_banner()

    st.divider()
    patient_data, submitted = render_patient_form()

    if submitted:
        builder = AssessmentBuilder()
        try:
            result = builder.build(patient_data)
            st.session_state.assessment_result = result
            st.session_state.submitted = True
        except ValueError as exc:
            st.error(f"Could not generate assessment: {exc}")
            st.session_state.submitted = False

    if st.session_state.submitted and st.session_state.assessment_result:
        st.divider()
        render_report(st.session_state.assessment_result)

    render_footer_disclaimer()


if __name__ == "__main__":
    main()
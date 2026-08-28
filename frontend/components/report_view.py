"""
Report view component.

Renders the structured output produced by AssessmentBuilder as a
readable Streamlit report, including flagged urgency level and
suggested next steps (informational, not diagnostic).
"""
from typing import Any, Dict

import streamlit as st

from frontend.components.safety_message import render_urgency_alert

SEVERITY_COLORS = {
    "low": "🟢",
    "moderate": "🟡",
    "high": "🔴",
}


def render_report(result: Dict[str, Any]) -> None:
    st.subheader("Assessment Summary")

    urgency = result.get("urgency_level", "low")
    render_urgency_alert(urgency)

    col1, col2, col3 = st.columns(3)
    col1.metric("Urgency", f"{SEVERITY_COLORS.get(urgency, '⚪')} {urgency.title()}")
    col2.metric("Symptom count", result.get("symptom_count", 0))
    col3.metric("Duration (days)", result.get("duration_days", 0))

    st.markdown("### Reported Symptoms")
    symptoms = result.get("symptoms", [])
    if symptoms:
        st.write(", ".join(symptoms))
    else:
        st.write("No symptoms recorded.")

    st.markdown("### Notes for the Clinician")
    notes = result.get("clinician_notes", [])
    if notes:
        for note in notes:
            st.markdown(f"- {note}")
    else:
        st.write("No additional notes generated.")

    st.markdown("### Suggested Next Steps")
    steps = result.get("suggested_next_steps", [])
    if steps:
        for step in steps:
            st.markdown(f"- {step}")
    else:
        st.write("No specific next steps generated.")

    with st.expander("Raw assessment data"):
        st.json(result)
"""
Safety messaging component.

Centralizes all disclaimer, banner, and urgency-alert copy so that
consistent, non-diagnostic language is used throughout the app.
"""
import streamlit as st

EMERGENCY_TEXT = (
    "If this is a medical emergency (e.g. chest pain, difficulty breathing, "
    "severe bleeding, suicidal thoughts, or loss of consciousness), "
    "**call your local emergency number immediately** "
    "(911 in the US, 112 in the EU) or go to the nearest emergency department."
)


def render_safety_banner() -> None:
    st.info(
        "This tool helps organize self-reported symptoms for discussion with a "
        "licensed clinician. It does **not** diagnose conditions or replace "
        "professional medical advice.",
        icon="ℹ️",
    )
    with st.expander("When to seek emergency care"):
        st.warning(EMERGENCY_TEXT, icon="🚨")


def render_urgency_alert(urgency_level: str) -> None:
    """Render a prominent alert based on the computed urgency level."""
    level = (urgency_level or "low").lower()
    if level == "high":
        st.error(
            "This assessment flagged **high urgency** based on the symptoms and "
            "duration reported. Please seek prompt medical attention.\n\n"
            + EMERGENCY_TEXT,
            icon="🚨",
        )
    elif level == "moderate":
        st.warning(
            "This assessment flagged **moderate urgency**. Consider contacting "
            "a healthcare provider soon to review these symptoms.",
            icon="⚠️",
        )
    else:
        st.success(
            "This assessment flagged **low urgency** based on the information "
            "provided. Continue to monitor symptoms and consult a clinician if "
            "they worsen or persist.",
            icon="✅",
        )


def render_footer_disclaimer() -> None:
    st.divider()
    st.caption(
        "This tool is for informational purposes only and is not a substitute "
        "for professional medical diagnosis, advice, or treatment. Always seek "
        "the advice of a physician or other qualified health provider with any "
        "questions regarding a medical condition."
    )
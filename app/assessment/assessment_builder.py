"""
Assessment builder.

Takes structured patient intake data and produces a structured,
non-diagnostic assessment summary: urgency flag, clinician notes,
and suggested next steps. This is rule-based triage-support logic,
not a diagnostic engine.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List

# Symptoms that warrant elevated attention when combined with other factors.
HIGH_ATTENTION_SYMPTOMS = {
    "shortness of breath",
    "chest pain",
}

MODERATE_ATTENTION_SYMPTOMS = {
    "fever",
    "cough",
    "joint pain",
    "anxiety or low mood",
}

LONG_DURATION_THRESHOLD_DAYS = 14
SEVERE_LABEL = "severe"


@dataclass
class AssessmentBuilder:
    """Builds a structured assessment from patient intake data."""

    high_attention_symptoms: set = field(default_factory=lambda: set(HIGH_ATTENTION_SYMPTOMS))
    moderate_attention_symptoms: set = field(default_factory=lambda: set(MODERATE_ATTENTION_SYMPTOMS))

    def build(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate(patient_data)

        symptoms = [s.strip() for s in patient_data.get("symptoms", []) if s and s.strip()]
        symptoms_lower = {s.lower() for s in symptoms}
        duration_days = int(patient_data.get("duration_days", 0))
        severity = str(patient_data.get("severity", "Mild")).lower()

        urgency_level = self._compute_urgency(symptoms_lower, duration_days, severity)
        clinician_notes = self._build_clinician_notes(patient_data, symptoms)
        next_steps = self._build_next_steps(urgency_level, duration_days)

        return {
            "age": patient_data.get("age"),
            "sex": patient_data.get("sex"),
            "symptoms": symptoms,
            "symptom_count": len(symptoms),
            "duration_days": duration_days,
            "severity": severity,
            "urgency_level": urgency_level,
            "clinician_notes": clinician_notes,
            "suggested_next_steps": next_steps,
        }

    def _validate(self, patient_data: Dict[str, Any]) -> None:
        if not patient_data.get("consent", False):
            raise ValueError("Patient consent/acknowledgement is required.")
        if not patient_data.get("symptoms"):
            raise ValueError("At least one symptom must be provided.")

    def _compute_urgency(self, symptoms_lower: set, duration_days: int, severity: str) -> str:
        if symptoms_lower & self.high_attention_symptoms or severity == SEVERE_LABEL:
            return "high"
        if symptoms_lower & self.moderate_attention_symptoms or duration_days >= LONG_DURATION_THRESHOLD_DAYS:
            return "moderate"
        return "low"

    def _build_clinician_notes(self, patient_data: Dict[str, Any], symptoms: List[str]) -> List[str]:
        notes: List[str] = []
        age = patient_data.get("age")
        if age is not None:
            notes.append(f"Patient is {age} years old, sex assigned at birth: {patient_data.get('sex', 'not specified')}.")
        if symptoms:
            notes.append(f"Reported symptoms: {', '.join(symptoms)}.")
        history = patient_data.get("history")
        if history:
            notes.append(f"Relevant history provided by patient: {history}")
        duration_days = patient_data.get("duration_days")
        if duration_days is not None:
            notes.append(f"Symptoms reported for {duration_days} day(s).")
        return notes

    def _build_next_steps(self, urgency_level: str, duration_days: int) -> List[str]:
        if urgency_level == "high":
            return [
                "Seek prompt evaluation from a healthcare provider or urgent care.",
                "If symptoms are severe or worsening, go to the nearest emergency department.",
            ]
        if urgency_level == "moderate":
            return [
                "Schedule an appointment with a primary care provider in the next few days.",
                "Track symptom changes and note any new or worsening signs.",
            ]
        return [
            "Monitor symptoms and rest as needed.",
            "Contact a healthcare provider if symptoms persist beyond "
            f"{LONG_DURATION_THRESHOLD_DAYS} days or worsen.",
        ]
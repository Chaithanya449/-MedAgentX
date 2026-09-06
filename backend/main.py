import httpx
from fastapi import FastAPI

from app.assessment.builder import AssessmentBuilder
from backend.safety.safety_gate1 import safety_gate1
from backend.schemas import PatientIntake
from backend.risk.risk_engine import risk_engine
from backend.safety.safety_gate2 import safety_gate2


assessment_builder = AssessmentBuilder()

app = FastAPI(title="MedAgentX API")


@app.post("/intake")
async def intake(patient: PatientIntake):
    safety_result = safety_gate1(patient)

    if not safety_result["safe_to_continue"]:
        return safety_result

    patient_data = patient.model_dump()

    response = httpx.post(
        "https://vixen-phonebook-tartness.ngrok-free.dev/assess",
        json=patient_data,
        timeout=300.0,
    )

    print("STATUS:", response.status_code)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print("RESPONSE TEXT:", response.text)

    response.raise_for_status()

    result = response.json()

    risk_result = risk_engine(patient, result)

    assessment = assessment_builder.build(
        patient_data,
        result,
        risk_result,
    )
    gate2_result = safety_gate2(assessment, risk_result)

    return gate2_result

    
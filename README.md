# MedAgentX

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B)
![Status](https://img.shields.io/badge/Status-V1%20Complete-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> A safety-first patient-awareness system combining medical-domain AI, Retrieval-Augmented Generation (RAG), deterministic risk assessment, and layered safety controls.

MedAgentX is my attempt at helping patients **better understand and become more aware of their self-reported symptoms** using evidence-grounded AI. It does **not diagnose patients**. Instead it gives a structured symptom summary, possible explanations for awareness, supporting evidence from a medical knowledge base, a deterministic risk/urgency indication, and guidance on when professional care may be appropriate.

> **Important:** MedAgentX is an experimental prototype for patient awareness and informational support. It does not provide medical diagnosis or treatment and does not replace qualified professional medical advice.

---

## Project Goal

A simple LLM app would do `Patient Symptoms → LLM → Diagnosis`. MedAgentX instead separates model reasoning from deterministic safety logic:

```
Patient Symptoms → Safety Gate 1 → Medical Knowledge Retrieval → MedGemma Reasoning
→ Deterministic Risk Engine → Assessment Builder → Safety Gate 2 → Patient Awareness Report
```

## System Flow

```
Streamlit UI → FastAPI /intake → Pydantic Validation → Safety Gate 1
                                                            │
                                          ┌─── Red Flag ────┴──── Safe ───┐
                                          ▼                               ▼
                                  Urgent Response + STOP        RAG → MedGemma → Risk Engine
                                                                            │
                                                                 Assessment Builder → Safety Gate 2
                                                                            │
                                                              Patient Awareness Final Report
```

## Key Components

**1. Streamlit Patient Intake** — collects age, sex, symptoms, duration, severity, progression, history, and consent as structured JSON.

**2. FastAPI Backend** — validates requests, runs Safety Gate 1, calls the remote model service, runs the Risk Engine, builds the assessment, runs Safety Gate 2, and returns the final result.

**3. Safety Gate 1** — runs before RAG/MedGemma. Checks for red flags (severe breathing difficulty, chest pain, loss of consciousness, severe bleeding, severe allergic reaction, stroke symptoms, severe abdominal pain, poisoning/overdose). A detected flag short-circuits straight to an urgent response — no LLM call.

**4. Medical RAG** — for non-urgent cases, retrieves relevant context from a medical knowledge base (built from Mayo Clinic, WHO, CDC, NIH material) before reasoning.

**5. MedGemma** (`google/medgemma-1.5-4b-it`) — the medical-domain reasoning model. Runs in Google Colab with GPU acceleration; FastAPI talks to it over an ngrok tunnel to a hosted `/assess` endpoint.

**6. Deterministic Risk Engine** — independent of the LLM. Produces LOW / MODERATE / HIGH from severity, progression, and duration:

```
Severe + Worsening        → HIGH
Severe + >= 7 days        → HIGH
Moderate + Worsening      → MODERATE
Moderate + >= 7 days      → MODERATE
Otherwise                 → LOW
```
*Prototype engineering heuristics — not clinically validated triage criteria.*

**7. Assessment Builder** — combines patient data + MedGemma output + risk result into one structured object (summary, possible conditions, evidence, risk level, urgency, disclaimer).

**8. Safety Gate 2** — final check before the patient sees anything: flags definitive diagnostic language, missing disclaimers, and contradictions with the deterministic risk result.

**9. Patient Awareness Report** — the structured assessment rendered in Streamlit as a readable report.

## Engineering Challenges

Honestly, building each piece wasn't the hard part — connecting them was. Colab hosted MedGemma, RAG, and the reasoning agent, tunneled through ngrok to my local FastAPI, which then talked to Streamlit. Keeping all three running and in sync at the same time was its own project.

The one that cost me the most time: `httpx.ReadTimeout`. GPU inference on Colab took a lot longer than a normal local API call, so I had to tune timeouts and rethink how the backend waited on the model. I also learned the hard way that the Colab notebook has to be up and the ngrok tunnel live *before* FastAPI makes a request — order of operations that isn't obvious until it breaks on you mid-demo.

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI, Uvicorn, Pydantic, HTTPX |
| AI/ML | Google MedGemma 1.5 4B IT, Hugging Face Transformers, PyTorch, Accelerate, BitsAndBytes, Colab GPU |
| RAG | FAISS, medical knowledge base, retrieval pipeline |
| Dev/Integration | Python, Colab, Jupyter, ngrok |

## Repository Structure

```
medagentx/
├── app/
│   ├── assessment/builder.py
│   └── rag/
├── backend/
│   ├── main.py
│   ├── schemas.py
│   ├── risk/
│   └── safety/
├── frontend/streamlit_app.py
├── knowledge_base/{raw,vector_store}/
├── notebooks/Medagentx.ipynb
└── requirements.txt
```

## Running the Project

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd medagentx
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

1. Open `notebooks/Medagentx.ipynb` in Colab and run it — starts MedGemma, GPU inference, RAG, the reasoning agent, `/assess`, and the ngrok tunnel. **Never commit API keys, ngrok tokens, or HF tokens.**
2. `uvicorn backend.main:app --reload --port 8000`
3. `streamlit run frontend/streamlit_app.py`

## Example Request

```
Age: 25, Sex: Female
Symptoms: Fatigue, Shortness of breath
Duration: 3 days | Severity: Moderate | Progression: Stable
```
→ travels through all 9 stages above → returns a Patient Awareness Report.

## Team

I built this with a friend as a 2-person team. I focused on the backend — FastAPI, the safety gates, and the deterministic risk engine — while my collaborator worked on the RAG pipeline and model integration on the AI side. We split frontend and system integration between us as it came up. Most of the real work near the end was just getting our two halves to talk to each other correctly.

## Project Status

**MedAgentX V1 — Core End-to-End Prototype Complete ✅**

## Future Development (V2)

Automated testing · expanded red-flag questions · stronger safety validation · improved retrieval evaluation · better observability/logging · improved UI · Docker deployment · more robust model serving · quantitative evaluation · stronger provenance/citation handling.

## Limitations

- Risk rules are prototype heuristics, not clinically validated
- Red-flag detection relies on predefined symptom patterns
- MedGemma inference runs through Colab; ngrok is a temporary dev bridge
- Only a subset of source material is public
- Not designed for production clinical deployment
- AI-generated information may be incomplete or incorrect

## Disclaimer

MedAgentX is an experimental software project for educational and engineering purposes. It supports patient awareness of self-reported symptoms. It does not provide medical diagnosis, treatment, or emergency medical services and should not replace advice from a qualified healthcare professional. **For a medical emergency, contact local emergency services immediately.**

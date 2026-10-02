# MedAgentX

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)
![AWS ECS](https://img.shields.io/badge/AWS-ECS%20%7C%20Fargate-FF9900)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF)
![Status](https://img.shields.io/badge/Status-V1%20Complete-brightgreen)

> A safety-first patient-awareness prototype that combines medical knowledge retrieval, deterministic risk assessment, and layered safety controls.

MedAgentX is designed to help users **better understand and organize self-reported symptoms** using evidence retrieved from a curated medical knowledge base. It does **not diagnose patients**. The current V1 produces a structured patient summary, possible condition matches from retrieved reference material, supporting evidence, a deterministic risk/urgency indication, and safety guidance.

> **Important:** MedAgentX is an experimental prototype for educational and informational use. It does not provide medical diagnosis or treatment and does not replace qualified professional medical advice.

---

## Project Goal

Instead of sending symptoms directly to an LLM, the current V1 separates retrieval, deterministic safety logic, and assessment building:

```
Patient Symptoms
      ↓
Pydantic Validation
      ↓
Safety Gate 1
      ↓
Local RAG Retrieval
      ↓
Deterministic Risk Engine
      ↓
Assessment Builder
      ↓
Safety Gate 2
      ↓
Patient Awareness Report
```

### Current V1 Architecture

```
Streamlit UI
    │
    ▼
FastAPI /intake
    │
    ▼
Pydantic Validation
    │
    ▼
Safety Gate 1 ────── Red Flag ──────► Urgent Response + STOP
    │
    ▼
Local RAG
    │
    ├── SentenceTransformer embeddings
    └── FAISS vector search
    │
    ▼
Deterministic Risk Engine
    │
    ▼
Assessment Builder
    │
    ▼
Safety Gate 2
    │
    ▼
Patient Awareness Report
```

**No external LLM, Colab service, ngrok tunnel, or runtime API key is required by the current V1 deployment.**

---

## Key Components

### 1. Streamlit Patient Intake

Collects structured self-reported information:

- Age
- Sex assigned at birth
- Symptoms
- Duration
- Self-rated severity
- Symptom progression
- Relevant medical history
- User acknowledgement/consent

### 2. FastAPI Backend

The `/intake` endpoint:

1. Validates the patient payload with Pydantic
2. Runs Safety Gate 1
3. Runs the local RAG-based assessment
4. Runs the deterministic Risk Engine
5. Builds the final assessment
6. Runs Safety Gate 2
7. Returns the structured result to Streamlit

### 3. Safety Gate 1

Runs **before retrieval/assessment processing**.

It checks predefined emergency red flags such as:

- Chest pain
- Severe breathing difficulty
- Loss of consciousness
- Severe bleeding
- Severe allergic reaction/anaphylaxis
- Possible stroke symptoms
- Severe abdominal pain
- Poisoning or overdose

When a red flag is detected, the workflow stops and returns an urgent response.

### 4. Medical RAG

The current V1 uses a local Retrieval-Augmented Generation-style retrieval pipeline without an LLM generation step.

Pipeline:

```
Medical source material
        ↓
Cleaning / Chunking
        ↓
SentenceTransformer embeddings
        ↓
FAISS vector store
        ↓
Symptom query
        ↓
Relevant reference passages
```

The embedding model used by the repository is:

```
sentence-transformers/all-MiniLM-L6-v2
```

The knowledge base contains reference material organized from sources including **Mayo Clinic, CDC, NIH, WHO, Cleveland Clinic, MedlinePlus, and NHS**.

### 5. Local Assessment

`app/assessment/local_assessment.py` replaces the previous external model-service call.

It:

- Builds a symptom-based retrieval query
- Retrieves relevant passages from FAISS
- Creates a patient summary
- Groups retrieved matches into possible condition matches
- Attaches supporting evidence and similarity scores

No external service is called at runtime.

### 6. Deterministic Risk Engine

The risk result is calculated independently of any language model.

Current prototype rules:

```
Severe + Worsening        → HIGH
Severe + >= 7 days        → HIGH
Moderate + Worsening      → MODERATE
Moderate + >= 7 days      → MODERATE
Otherwise                 → LOW
```

These are **prototype engineering heuristics, not clinically validated triage criteria**.

### 7. Assessment Builder

Combines patient data, retrieved assessment content, and the risk result into one structured object containing:

- Patient summary
- Symptoms
- Possible conditions
- Evidence
- Risk level
- Urgency
- Disclaimer

### 8. Safety Gate 2

Performs a final safety check before the result is shown.

It checks for:

- Definitive diagnostic wording
- Missing disclaimer text
- Contradictions between generated assessment text and the deterministic risk result

### 9. Patient Awareness Report

The final structured assessment is rendered in Streamlit as a readable patient-awareness report.

---

## Engineering Challenges

The biggest challenge was not building individual components — it was integrating them into one reliable system.

The current V1 had to bring together:

- Streamlit frontend
- FastAPI backend
- Pydantic validation
- Safety gates
- Local RAG retrieval
- FAISS vector search
- Deterministic risk logic
- Docker containerization
- AWS ECS/Fargate deployment
- GitHub Actions CI/CD

A major architectural change was removing the external Colab/ngrok model dependency and replacing it with a **local, in-process RAG-based assessment path**. This made the deployed V1 simpler and removed the need for a separate runtime model service.

---

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI, Uvicorn, Pydantic |
| RAG | SentenceTransformers, FAISS |
| Embeddings | `all-MiniLM-L6-v2` |
| Core Logic | Python |
| Containerization | Docker |
| Cloud | AWS ECS, AWS Fargate, Amazon ECR, CloudWatch |
| CI/CD | GitHub Actions + AWS OIDC |
| Knowledge Base | Medical reference material stored locally |

---

## Repository Structure

```
-MedAgentX/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── app/
│   ├── assessment/
│   │   ├── builder.py
│   │   └── local_assessment.py
│   └── rag/
│       ├── __init__.py
│       ├── chunker.py
│       ├── clean.py
│       ├── embeddings.py
│       ├── ingest.py
│       ├── query.py
│       ├── retriever.py
│       ├── vector_store.py
│       └── metadata/
├── backend/
│   ├── main.py
│   ├── schemas.py
│   ├── risk/
│   │   └── risk_engine.py
│   └── safety/
│       ├── red_flags.py
│       ├── safety_gate1.py
│       ├── safety_gate2.py
│       └── safety_response.py
├── frontend/
│   └── streamlit_app.py
├── knowledge_base/
│   ├── raw/
│   └── vector_store/
│       ├── index.faiss
│       └── metadata.json
├── Dockerfile
├── README.md
└── requirements.txt
```

---

## Run Locally

### Python

```bash
git clone https://github.com/Chaithanya449/-MedAgentX.git
cd -MedAgentX

python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, start Streamlit:

```bash
streamlit run frontend/streamlit_app.py
```

### Docker

Build:

```bash
docker build -t medagentx .
```

Run:

```bash
docker run -p 8501:8501 -p 8000:8000 medagentx
```

Open Streamlit:

```
http://localhost:8501
```

---

## AWS Deployment

The current V1 is containerized and deployed on AWS using:

```
GitHub
   ↓
GitHub Actions
   ↓
Docker Build
   ↓
Amazon ECR
   ↓
Amazon ECS / Fargate
   ↓
MedAgentX Container
   ↓
CloudWatch Logs / Metrics
```

Current deployment components:

- **Amazon ECR** — stores the Docker image
- **Amazon ECS** — runs the container
- **AWS Fargate** — serverless container compute
- **CloudWatch** — logs and metrics
- **IAM** — execution/task permissions
- **AWS OIDC** — GitHub Actions authentication without long-lived AWS access keys

---

## CI/CD

Every push to the `main` branch triggers the GitHub Actions deployment workflow.

```
git push
   ↓
GitHub Actions
   ↓
AWS OIDC authentication
   ↓
Docker build
   ↓
Push image to ECR
   ↓
Force new ECS deployment
   ↓
Wait for ECS service stability
```

The workflow tags the image with the commit SHA and also updates the `latest` tag.

---

## Example Input

```
Age: 25
Sex: Female
Symptoms: Fatigue, Shortness of breath
Duration: 3 days
Severity: Moderate
Progression: Stable
```

The request passes through validation, safety checks, local retrieval, deterministic risk assessment, assessment building, and final safety validation before the report is displayed.

---

## Team

MedAgentX was built as a **2-person project**.

I focused primarily on the backend side, including:

- FastAPI integration
- Safety Gate 1 and Safety Gate 2
- Deterministic risk engine
- Backend/system integration
- Docker and AWS deployment
- CI/CD with GitHub Actions

My collaborator focused primarily on the RAG pipeline and related AI-side work.

We collaborated on frontend and overall system integration.

---

## Project Status

**MedAgentX V1 — Core End-to-End Prototype Complete ✅**

Current V1 includes:

- Structured patient intake
- FastAPI backend
- Local medical RAG retrieval
- FAISS vector store
- Deterministic risk assessment
- Two safety gates
- Streamlit patient-awareness report
- Docker deployment
- AWS ECS/Fargate deployment
- GitHub Actions CI/CD

---

## Limitations

- Risk rules are prototype heuristics and are not clinically validated.
- Red-flag detection uses predefined symptom patterns and can miss conditions outside those patterns.
- Possible condition matches are retrieval-based references, not diagnoses.
- AI/ML-generated or retrieved information may be incomplete, outdated, or incorrect.
- The system is not designed for clinical diagnosis, treatment, or emergency response.
- The current deployment is a demonstration/prototype environment rather than a production clinical system.

---

## Disclaimer

MedAgentX is an experimental software project for educational and engineering purposes. It supports awareness and organization of self-reported symptom information. It does not provide medical diagnosis, treatment, or emergency medical services and should not replace advice from a qualified healthcare professional.

**For a medical emergency, contact local emergency services immediately.**

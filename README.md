# Rumbo

*"Rumbo" — Spanish for "course" or "direction."*

A matching platform between professional profiles and companies, where a
multi-agent system audits real fit between both sides — and neither side
sees the other until there is explicit consent.

**All Things Agentic Hackathon 2026 — Track: The Taskmaster**

---

## What it does

- **The profile** uploads a resume and, as soon as they sign in, sees the
  most relevant job posts with a fit score and a roadmap of what's missing —
  no searching, and without knowing which company posted them.
- **The company** provides its context and job post descriptions, and receives
  a map of matching profiles — without last names or contact details.
- **Reveal is staged**: the company manually invites, the profile accepts,
  and only then are identifying details shared.

---

## Architecture

A **sequential multi-agent system** with two human checkpoints. There is no
model-based coordinator agent: the flow is deterministic, so orchestration is
plain code. Model reasoning is reserved for the three points where semantic
judgment is actually needed.

### The three agents

| Agent | What it does | When it runs |
|---|---|---|
| **Role Classifier** | Decides whether a job post belongs to an existing role or creates a new one | When a job post is created |
| **Requirement Extractor** | Breaks the description into discrete requirements and updates the role's frequency table | When a job post is created |
| **Fit Auditor** | Computes score + quantitative roadmap comparing resume vs. job post vs. market data | Once per candidate job post |

### Two-level retrieval

1. **Level 1** — `find_nearest()` of the profile's embedding against
   `normalized_roles` (small collection: cheap semantic search).
2. **Level 2** — simple filter of `job_posts` by `normalized_role_id`
   (no vectors, no LLM).

Only over that narrowed set does the Auditor run. This avoids comparing a
profile against twenty near-identical "Product Manager" postings.

![Architecture](docs/architecture-diagram-en.png)

---

## Stack

| Component | Technology |
|---|---|
| Model | Gemini 3.5 (Flash / Pro) via Vertex AI |
| Agent framework | Google ADK |
| Database | Firestore (with native vector search) |
| Compute | Cloud Run |
| Async trigger | Pub/Sub |
| API | FastAPI (Python 3.12) |

---

## Local setup

### 1. Prerequisites

- Python 3.12+
- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated

### 2. Clone and install

```bash
git clone <REPO-URL>
cd rumbo

python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Environment variables

```bash
cp .env.example .env
```

Fill in `.env` with your project's values. **The real `.env` is never committed.**

### 4. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR-PROJECT-ID
```

### 5. Enable the required APIs

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com
```

### 6. Run locally

```bash
uvicorn main:app --reload --port 8080
```

Verify: `curl http://localhost:8080/health`

### 7. Seed sample data

```bash
python -m scripts.seed_data
```

---

## Deploying to Cloud Run

```bash
gcloud run deploy rumbo-dev \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-ID
```

Automatic deployment is wired through Cloud Build:
- push to `develop` → deploys to `rumbo-dev`
- push to `main` → deploys to `rumbo-prod`

---

## Project structure

```
rumbo/
├── main.py                  # FastAPI entrypoint
├── agents/                  # the 3 agents that use Gemini
│   ├── clasificador_roles.py
│   ├── extractor_requisitos.py
│   ├── auditor_fit.py
│   └── prompts/             # system prompts, one file per agent
├── pipeline/
│   └── matching_pipeline.py # plain-code orchestration (NOT an agent)
├── services/                # logic with no model reasoning
│   ├── firestore_client.py  # single access point to Firestore
│   ├── embeddings.py
│   ├── retrieval.py         # both retrieval levels
│   ├── normalizacion.py
│   ├── invitaciones.py      # match lifecycle and staged visibility
│   └── cv_generator.py
├── models/                  # one class per collection
├── routes/                  # HTTP endpoints
├── scripts/seed_data.py
├── tests/
└── docs/
```

---

## Team rules

- No one pushes directly to `main` or `develop`. Every change starts on a
  `feature/<task-id>-<description>` branch against `develop`.
- No one calls Firestore outside of `services/firestore_client.py`.
- Field, endpoint, and function names are fixed in the interface contract.
  If a new one is needed, it's added there first and the team is notified.
- No credentials in code or in commits.

See the full team documentation in `docs/` for details.

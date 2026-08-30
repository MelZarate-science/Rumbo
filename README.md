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

## MVP Status (Backend)

✅ **Fully functional backend** — all core flows implemented and tested:

| Feature | Status |
|---|---|
| Auth (password + cookie de sesión HttpOnly, backlog 1.1) | ✅ |
| Profile CRUD + CV data | ✅ |
| Company & job post CRUD | ✅ |
| Role classification (Gemini) | ✅ |
| Requirement extraction (Gemini, catalog reconciliation) | ✅ |
| Fit Auditor (Gemini score + quantitative roadmap) | ✅ |
| Two-level retrieval (`find_nearest()` + filter) | ✅ |
| Match persistence with staged visibility | ✅ |
| Invite / accept / reject lifecycle | ✅ |
| Tests (50) with in-memory fake Firestore + fake Gemini | ✅ |

**Still deferred**: Pub/Sub async trigger on profile registration (matching runs
synchronously from `PUT /perfiles/{id}/cv` instead — backlog 2.11, low priority),
PDF generation, and the Harvard-format CV assistant (backlog Fase 3, low priority).
Everything else in `docs/rumbo-backlog.md` Fases 0–2 and 4 is implemented as
specified, including real model reasoning in the three agents — see `agents/*.py`
and `agents/prompts/*.txt`.

Running the agents/embeddings for real requires a GCP project with Vertex AI
enabled and valid credentials (see `.env.example`); without that, only the
CRUD/state-machine parts are testable live, though everything is covered by
tests via a fake Gemini client (`tests/fakes_gemini.py`).

---

## Architecture

A **sequential multi-agent system** with two human checkpoints. There is no
model-based coordinator agent: the flow is deterministic, so orchestration is
plain code. Model reasoning is reserved for the three points where semantic
judgment is actually needed.

### The three agents (Gemini reasoning)

| Agent | What it does | When it runs |
|---|---|---|
| **Role Classifier** | Decides whether a job post belongs to an existing role or creates a new one, using semantic judgment (not string matching) against `roles_normalizados` | When a job post is created |
| **Requirement Extractor** | Breaks the description into discrete requirements, reconciles synonyms against `requisitos_normalizados` catalog, creates new ones if needed, updates role frequency table | When a job post is created |
| **Fit Auditor** | Computes score + quantitative roadmap comparing resume vs. job post vs. market data (role frequencies) | Once per candidate job post |

### Two-level retrieval

1. **Level 1** — `find_nearest()` (Firestore vector search) of the profile's
   embedding against `roles_normalizados` (`descripcion_consolidada`).
2. **Level 2** — simple filter of `puestos` by `rol_normalizado_id`
   (no vectors, no LLM).

Only over that narrowed set does the Auditor run. This avoids comparing a
profile against twenty near-identical "Product Manager" postings.

![Architecture](docs/architecture-diagram-en.png)

---

## Stack (MVP)

| Component | Technology |
|---|---|
| API | FastAPI (Python 3.12+) |
| Database | Firestore (emulator for local dev) |
| Testing | pytest + httpx + in-memory FakeFirestore |
| Agents | Deterministic Python (no Vertex AI / ADK in MVP) |
| Validation | Pydantic v2 |

> **Nota**: `google-cloud-pubsub` está en `requirements.txt` para el disparo
> asíncrono (backlog 2.11), diferido por prioridad — hoy el matching corre
> síncrono. `google-genai` (Gemini) y los embeddings sí se usan de verdad
> en el MVP — ver `backend/services/gemini_client.py`.

---

## Local setup

### 1. Prerequisites

- Python 3.12+
- (Opcional) `gcloud` CLI si quieres usar el emulador de Firestore local

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

**Para desarrollo SIN credenciales GCP** (usa el emulador de Firestore):

```bash
# Terminal 1: levantar emulador
gcloud emulators firestore start --host-port=localhost:8080

# Terminal 2: exportar variable y correr la app
export FIRESTORE_EMULATOR_HOST=localhost:8080
uvicorn main:app --reload --port 8080
```

El SDK de Firestore detecta `FIRESTORE_EMULATOR_HOST` automáticamente.

**Índices vectoriales requeridos** (contra Firestore real, no el emulador): sin
esto, `find_nearest()` falla con `Missing vector index configuration`. Se crean
una sola vez por proyecto -- uno para el retrieval Nivel 1 (perfil → rol) y
otro para el pre-filtro por embedding que usan los Agentes 1 y 2 al clasificar
un puesto nuevo (ver `Auditoria-Rumbo-Normalizacion.md`, fuera del repo):

```bash
gcloud firestore indexes composite create \
  --project=YOUR-PROJECT-ID \
  --collection-group=roles_normalizados \
  --query-scope=COLLECTION \
  --field-config=field-path=embedding,vector-config='{"dimension":"1536","flat":"{}"}'

gcloud firestore indexes composite create \
  --project=YOUR-PROJECT-ID \
  --collection-group=requisitos_normalizados \
  --query-scope=COLLECTION \
  --field-config=field-path=embedding,vector-config='{"dimension":"1536","flat":"{}"}'
```

Tarda unos minutos en pasar a estado `READY` (`gcloud firestore indexes composite list` para chequear). Si `gcloud` da problemas de quoting en Windows/PowerShell con el JSON de `vector-config`, se puede crear por API en su lugar con `google.cloud.firestore_admin_v1.FirestoreAdminClient().create_index(...)`.

### 4. Run tests (no GCP needed)

```bash
python -m pytest tests/ -v
```

Todos los tests usan `tests/fakes.py` (FakeFirestore en memoria), así que
**no requieren credenciales ni emulador**.

### 5. Seed sample data (requiere emulador o GCP real)

```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080  # o usa tu proyecto GCP real
python -m scripts.seed_data
```

Crea 6 perfiles variados, 4 empresas, 7 puestos y ejecuta matching.

### 6. Verify

```bash
curl http://localhost:8080/health
# {"status":"ok","service":"rumbo"}
```

---

## API Endpoints (MVP)

### Perfiles
| Method | Path | Descripción |
|---|---|---|
| POST | `/perfiles` | Crear perfil |
| GET | `/perfiles/{id}` | Obtener perfil (vista propietario) |
| PUT | `/perfiles/{id}` | Editar datos personales |
| PUT | `/perfiles/{id}/cv` | Cargar/actualizar `cv_data` + **dispara matching** |
| GET | `/perfiles/{id}/matches` | Matches del perfil (empresa oculta si `pendiente`) |

### Empresas
| Method | Path | Descripción |
|---|---|---|
| POST | `/empresas` | Crear empresa |
| GET | `/empresas/{id}` | Obtener empresa |
| PUT | `/empresas/{id}` | Editar empresa |
| POST | `/empresas/{id}/puestos` | Crear puesto + **indexado automático** |
| GET | `/empresas/{id}/puestos` | Listar puestos activos |
| GET | `/empresas/{id}/matches` | Matches de la empresa (perfil filtrado según estado) |

### Puestos
| Method | Path | Descripción |
|---|---|---|
| GET | `/puestos/{id}` | Obtener puesto |
| PUT | `/puestos/{id}` | Editar puesto (re-indexa si cambia título/descripción) |

### Matches (opt-in flow)
| Method | Path | Descripción |
|---|---|---|
| GET | `/matches/{id}` | Match con visibilidad según estado |
| POST | `/matches/{id}/invitar` | **Empresa** invita (`pendiente` → `notificado`) |
| POST | `/matches/{id}/responder` | **Perfil** responde (`notificado` → `confirmado` / `rechazado`) |

**Body `responder`**: `{"aceptar": true|false}`

---

## Visibilidad escalonada (regla del MVP)

| Estado | Perfil ve empresa | Empresa ve apellido/email/teléfono |
|---|---|---|
| `pendiente` | ❌ (solo `empresa_id`) | ❌ |
| `notificado` | ✅ (nombre empresa) | ❌ |
| `confirmado` | ✅ | ✅ |
| `rechazado` | ✅ | ❌ |

La lógica vive en `backend/services/invitaciones.py` (`filtrar_campos_visibles`,
`es_empresa_visible`).

---

## Deploying to Cloud Run

Copiá `.env` a un archivo YAML (mismos nombres de variable, sin comillas de más)
y usá `--env-vars-file` — es más confiable que `--set-env-vars` cuando algún
valor tiene caracteres especiales (ej. `FIRESTORE_DATABASE_ID=(default)`):

```bash
gcloud run deploy rumbo-dev \
  --source . \
  --project=YOUR-PROJECT-ID \
  --region us-central1 \
  --allow-unauthenticated \
  --env-vars-file=env.yaml
```

Variables mínimas que necesita el servicio: `GOOGLE_CLOUD_PROJECT`,
`GOOGLE_GENAI_USE_VERTEXAI=True`, `GOOGLE_CLOUD_LOCATION`,
`FIRESTORE_DATABASE_ID`, `GEMINI_MODEL_FLASH`, `GEMINI_EMBEDDING_MODEL`,
`AUTH_SECRET_KEY`, `UMBRAL_FIT_MINIMO` — ver `.env.example`. `GEMINI_API_KEY`
es opcional y solo hace falta si en algún momento se quiere forzar la capa
gratuita de Google AI Studio en vez de Vertex AI (ver `services/gemini_client.py`);
dejarla vacía es lo esperado en este proyecto. El frontend queda servido en
`<service-url>/app/`.

Deploy automático vía Cloud Build todavía no está configurado (backlog 0.9) —
por ahora el deploy es manual con el comando de arriba, contra la rama `Dev`
en GitHub (que es la rama de integración real del equipo, más allá de que
`develop` exista como nombre en el repo).

---

## Project structure

```
rumbo/
├── main.py                  # FastAPI entrypoint + error handlers
├── agents/                  # 3 agents (Gemini reasoning)
│   ├── clasificador_roles.py
│   ├── extractor_requisitos.py
│   ├── auditor_fit.py
│   └── prompts/             # stubs (not used in MVP)
├── pipeline/
│   └── matching_pipeline.py # plain-code orchestration
├── services/                # logic with no model reasoning
│   ├── firestore_client.py  # single access point to Firestore
│   ├── embeddings.py        # disabled in MVP (logs warning)
│   ├── retrieval.py         # 2-level retrieval (token overlap)
│   ├── normalizacion.py     # text utils + frecuencia helpers
│   ├── invitaciones.py      # match lifecycle + staged visibility
│   └── cv_generator.py      # stub (Fase 3)
├── models/                  # one Pydantic class per collection
├── routes/                  # HTTP endpoints
├── scripts/seed_data.py     # reproducible seed (6 perfiles, 4 empresas)
├── tests/
│   ├── conftest.py          # FakeFirestore + TestClient fixtures
│   ├── fakes.py             # in-memory Firestore implementation
│   ├── test_routes_perfiles.py
│   ├── test_routes_empresas.py
│   ├── test_routes_matches.py
│   └── test_services.py     # invitaciones + auditor_fit
└── docs/
    ├── backend.md           # MVP roadmap (this implementation)
    ├── rumbo-contrato-interfaces.md
    ├── rumbo-schema-bd.md
    ├── rumbo-backlog.md
    ├── rumbo-flujo-trabajo.md
    └── rumbo-spec-tecnico.md
```

---

## Team rules

- No one pushes directly to `main` or `develop`. Every change starts on a
  `feature/<task-id>-<description>` branch against `develop`.
- No one calls Firestore outside of `backend/services/firestore_client.py`.
- Field, endpoint, and function names are fixed in the interface contract.
  If a new one is needed, it's added there first and the team is notified.
- No credentials in code or in commits.

See the full team documentation in `docs/` for details.

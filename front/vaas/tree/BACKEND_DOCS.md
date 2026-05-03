# VaaS — Backend System Documentation

## 1. Project Overview

**VaaS (Verification-as-a-Service)** is a Django-based AI platform for verifying medical doctor credentials. It combines:

- A **REST API** (Django REST Framework) for document upload and decision retrieval
- A **WebSocket server** (Django Channels + Daphne) for real-time AI interview sessions
- An **AI/ML pipeline** (`ia/` package) that runs locally or via Celery workers
- **Redis** as the message broker (Celery tasks + Channel Layers)
- **PostgreSQL** as the primary database (SQLite fallback available)

---

## 2. Directory Structure

```
tree/
├── manage.py                   # Django management entrypoint
├── requirements.txt            # All Python dependencies
├── vaas_test_collection.json   # Postman E2E test collection
├── db.sqlite3                  # SQLite fallback DB
│
├── vaas_project/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py                 # ASGI app (HTTP + WebSocket)
│   ├── celery.py               # Celery app
│   └── wsgi.py
│
├── core/                       # Custom User + API Key auth
│   ├── models.py
│   ├── authentication.py
│   └── admin.py
│
├── verification/               # Phase 1 & 3 — document upload & decision
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── tasks.py                # Celery tasks (OCR, PDF→images)
│
├── interviews/                 # Phase 4 — live AI video interview
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── consumers.py            # WebSocket consumer
│   └── routing.py
│
├── ai_integrations/            # Facade layer over ia/ package
│   └── services.py
│
└── ia/                         # Standalone AI pipeline (local CLI)
    ├── main.py                 # CLI orchestrator (9-step pipeline)
    ├── .env                    # API keys + paths
    ├── pipeline/
    │   ├── pdf_to_images.py    # Step 1
    │   ├── ocr.py              # Step 2
    │   ├── extractor.py        # Step 3 (vision LLM)
    │   ├── web_verifier.py     # Step 4 (Perplexity Sonar)
    │   ├── survey_gen.py       # Step 5
    │   ├── rag.py              # Step 6 (ChromaDB)
    │   ├── expression.py       # Step 7 (DeepFace)
    │   ├── interview.py        # Step 8 (voice interview)
    │   ├── evaluator.py        # Step 9 (final score)
    │   ├── audio_io.py         # STT/TTS adapter
    │   └── runtime_state.py    # File-based turn state
    └── audio/
        ├── stt_whisper/        # Faster-Whisper STT
        └── tts_kokoro/         # Kokoro-ONNX TTS
```

---

## 3. Django Apps

### 3.1 `core` — Authentication & Users

**Models:**

| Model | Purpose |
|---|---|
| `User` | Extends `AbstractUser`; adds `organization_name` field. Set as `AUTH_USER_MODEL`. |
| `ClientAPIKey` | Hashed API keys for programmatic access. Stores only SHA-256 hash; raw key shown once at creation. |

**Authentication (`core/authentication.py`):**

- Custom DRF authenticator: `APIKeyAuthentication`
- Reads key from `X-Api-Key` header or `Authorization: Api-Key <secret>`
- Looks up `ClientAPIKey` by hashing the incoming key, rejects if inactive
- Updates `last_used_at` on each successful auth
- Registered alongside `SessionAuthentication` in `REST_FRAMEWORK` settings

---

### 3.2 `verification` — Document Upload & Decision

**Model: `VerificationJob`**

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | Auto-generated job identifier |
| `user` | FK → User | Owner of the job |
| `subject_external_id` | CharField | The `doctor_id` provided by the client |
| `status` | TextChoices | `queued / processing / succeeded / failed` |
| `celery_task_id` | CharField | Celery task reference |
| `result` | JSONField | Pipeline results + final decision |
| `error_message` | TextField | Populated on failure |

**API Views:**

| View | Method | URL | Description |
|---|---|---|---|
| `HealthView` | GET | `/api/health/` | Auth check — returns `{"status":"ok"}` |
| `VerificationUploadView` | POST | `/api/v1/verification/upload/` | Multipart: `doctor_id` + `file` (PDF). Creates `VerificationJob`, saves PDF to media storage |
| `VerificationDecisionView` | GET | `/api/v1/verification/jobs/<uuid>/decision/` | Returns job status + decision (`pending/approved/rejected`) |

**Celery Tasks (`verification/tasks.py`):**

| Task | Description |
|---|---|
| `pdf_to_images_task` | Wraps `ia.pipeline.pdf_to_images`. Converts PDF to PNG pages. |
| `ocr_images_task` | Wraps `ia.pipeline.ocr.run_ocr`. Sends images to NVIDIA Nemotron-Parse. |

> **Note:** These tasks are defined but not yet wired to `VerificationUploadView`. The upload creates the job and saves the file; Celery dispatch must still be added.

---

### 3.3 `interviews` — Real-Time AI Interview (Phase 4)

**Models:**

| Model | Purpose |
|---|---|
| `InterviewSession` | One live/completed interview. UUID PK, status (`pending/live/completed/failed`), `subject_external_id`, `active_turn_id`, `rag_context`, `metadata`. |
| `QALog` | Append-only transcript rows per interview turn. Fields: `turn_id`, `role` (assistant/user/system), `content`, `sequence`. |
| `ExpressionLog` | One row per DeepFace sample. Fields: `turn_id`, `emotion`, `confidence`, `timestamp_ms`. Replaces the legacy JSONL file. |

**REST View:**

| View | Method | URL | Description |
|---|---|---|---|
| `InterviewSessionCreateView` | POST | `/api/v1/interviews/sessions/` | Creates an `InterviewSession`, returns `session_uuid` for WS connection |

**WebSocket Consumer (`interviews/consumers.py`):**

- Route: `ws/interview/<session_uuid>/`
- Validates UUID, loads `InterviewSession` from DB, joins a Channel group
- **Binary messages** → `_handle_binary_audio()` → STT pipeline (placeholder)
- **Text/JSON messages:**
  - `type: "video_frame"` → `_handle_video_frame_b64()` → DeepFace (placeholder)
  - `type: "ping"` → responds with `{"type":"pong"}`
- Both STT and DeepFace paths are currently **placeholders** — wiring to `ia/` pipeline is the next step

---

### 3.4 `ai_integrations` — Facade Layer

`services.py` provides clean Python callables that import from `ia/pipeline/*` via the `sys.path` insertion in `settings.py`:

| Function | Delegates to |
|---|---|
| `pdf_to_images(...)` | `pipeline.pdf_to_images.pdf_to_images` |
| `run_ocr(...)` | `pipeline.ocr.run_ocr` |
| `stt_whisper_placeholder()` | `audio.stt_whisper.stt` |
| `expression_placeholder()` | `pipeline.expression` |

---

## 4. Project Configuration (`vaas_project/`)

### settings.py — Key Settings

| Setting | Default | Notes |
|---|---|---|
| `AUTH_USER_MODEL` | `core.User` | Custom user model |
| `DATABASE` | PostgreSQL | Env vars: `POSTGRES_DB/USER/PASSWORD/HOST/PORT`. Set `DJANGO_USE_SQLITE=true` for SQLite. |
| `REDIS_HOST/PORT` | `127.0.0.1:6379` | Used for both Channels and Celery |
| `CHANNEL_LAYERS` | Redis backend | `channels_redis.core.RedisChannelLayer` |
| `CELERY_BROKER_URL` | `redis://…/0` | |
| `CELERY_RESULT_BACKEND` | `redis://…/1` | |
| `CELERY_TASK_TIME_LIMIT` | 3600s (1h) | Hard limit for AI jobs |
| `MEDIA_ROOT` | `tree/media/` | Uploaded PDFs stored here |
| `ASGI_APPLICATION` | `vaas_project.asgi.application` | Daphne serves both HTTP + WS |

### asgi.py

```
HTTP  →  Django ASGI app
WS    →  AllowedHostsOriginValidator
            → AuthMiddlewareStack
               → URLRouter → InterviewConsumer
```

### celery.py

Standard Celery setup; `app.autodiscover_tasks()` picks up `verification/tasks.py`.

---

## 5. The `ia/` AI Pipeline (9 Steps)

Run locally with:
```bash
cd ia
python main.py --doctor demo/good_doctor/
```

### Step-by-Step

| Step | Module | What it does |
|---|---|---|
| **1** | `pdf_to_images.py` | Converts each PDF page to PNG at 200 DPI using PyMuPDF |
| **2** | `ocr.py` | Sends PNG images to `nvidia/nemotron-parse` (NVIDIA API); extracts raw text |
| **3** | `extractor.py` | Sends images + OCR text to `meta/llama-3.2-90b-vision-instruct`; returns structured profile JSON |
| **3b** | `extractor.visual_check_documents()` | Per-image stamp/signature/authenticity check with the vision model |
| **4** | `web_verifier.py` | Uses `perplexity/sonar` (via OpenRouter) to confirm university, hospital, professors, 4th-year curriculum |
| **5** | `survey_gen.py` | Uses `meta/llama-3.3-70b-instruct` (NVIDIA) to generate 3 registration survey questions |
| **6** | `rag.py` | Ingests all structured data into ChromaDB (embeddings: `all-MiniLM-L6-v2`) |
| **7** | `expression.py` | Background thread: reads webcam via OpenCV, analyzes emotions with DeepFace per interview turn |
| **8** | `interview.py` | 3-turn voice interview: LLM generates questions → Kokoro TTS speaks → Whisper STT listens |
| **9** | `evaluator.py` | Computes weighted score; returns `VERIFIED / NEEDS_MANUAL_REVIEW / REJECTED` |

### Scoring Formula (Step 9)

```
Final Score = (document_score × 0.50) + (interview_score × 0.35) + (expression_score × 0.15)

Verdict:
  ≥ 0.75 + no anomalies + name match  →  VERIFIED
  ≥ 0.45                               →  NEEDS_MANUAL_REVIEW
  < 0.45                               →  REJECTED
```

**Document score** (up to 1.0):
- Name match: +0.20
- Stamp present: +0.10
- Signature/structure: +0.10
- University confirmed: +0.20
- Hospital confirmed: +0.20
- Dean verified: +0.20

**Interview score**: LLM consistency evaluation (0.0–1.0)

**Expression score**: `max(0, 1 - stress_ratio × 2)` where stress = fear + angry + disgust

---

## 6. AI Models Used

| Model | Provider | Used For |
|---|---|---|
| `nvidia/nemotron-parse` | NVIDIA | OCR — document text extraction |
| `meta/llama-3.2-90b-vision-instruct` | NVIDIA | Profile extraction + visual document check |
| `meta/llama-3.3-70b-instruct` | NVIDIA | Survey generation, interview questions, consistency eval |
| `perplexity/sonar` | OpenRouter | Live web search — university/hospital verification |
| `all-MiniLM-L6-v2` | HuggingFace (local) | ChromaDB embeddings |
| `faster-whisper` | Local | Speech-to-text (STT) |
| `kokoro-onnx` | Local | Text-to-speech (TTS) |
| DeepFace | Local | Facial emotion analysis |

---

## 7. REST API Reference

Base URL: `http://127.0.0.1:8000`

Authentication: All endpoints require either:
- Header: `X-Api-Key: <raw_key>`
- Header: `Authorization: Api-Key <raw_key>`

### Endpoints

#### `GET /api/health/`
```json
{ "status": "ok", "service": "vaas", "authenticated_user": "alice" }
```

#### `POST /api/v1/verification/upload/`
Body: `multipart/form-data` with `doctor_id` (text) + `file` (PDF)

**201 Created:**
```json
{
  "session_uuid": "uuid",
  "job_id": "uuid",
  "subject_external_id": "doc-001",
  "status": "queued",
  "message": "Job created. Wire Celery..."
}
```

#### `GET /api/v1/verification/jobs/<uuid>/decision/`
**200 OK:**
```json
{
  "session_uuid": "uuid",
  "job_status": "succeeded",
  "decision": "approved",
  "result": { ... },
  "error_message": null
}
```

#### `POST /api/v1/interviews/sessions/`
Body: `{"doctor_id": "doc-001"}`

**201 Created:**
```json
{
  "session_uuid": "uuid",
  "subject_external_id": "doc-001",
  "status": "pending"
}
```

#### `WS ws/interview/<session_uuid>/`
- Binary frames → audio chunks (STT pipeline)
- JSON `{"type":"video_frame","data":"<base64>"}` → emotion analysis
- JSON `{"type":"ping"}` → `{"type":"pong"}`

---

## 8. Environment Variables

### Django (`vaas_project/settings.py`)

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure default | Change in production |
| `DJANGO_DEBUG` | `true` | Set `false` in prod |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated |
| `DJANGO_USE_SQLITE` | unset | Set `true` to use SQLite |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | `vaas/vaas/vaas/localhost/5432` | PostgreSQL connection |
| `REDIS_HOST` | `127.0.0.1` | |
| `REDIS_PORT` | `6379` | |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | |
| `CELERY_RESULT_BACKEND` | `redis://127.0.0.1:6379/1` | |

### IA Pipeline (`ia/.env`)

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | For Perplexity Sonar web search |
| `NVIDIA_API_KEY` | For OCR, vision, LLM, evaluator, survey gen |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `CHROMA_DB_PATH` | `./db` — ChromaDB storage |
| `IMAGES_DIR` | `./data/images` |
| `REPORTS_DIR` | `./reports` |
| `TRANSCRIPTS_DIR` | `./transcripts` |

---

## 9. Database Schema Summary

```
core_user                     (extends auth_user + organization_name)
core_client_api_key           (user_fk, name, key_prefix, key_hash, is_active)

verification_job              (id UUID, user_fk, subject_external_id, status,
                               celery_task_id, result JSON, error_message)

interviews_session            (id UUID, user_fk, subject_external_id, status,
                               active_turn_id, rag_context, metadata JSON)
interviews_qa_log             (session_fk, turn_id, role, content, sequence)
interviews_expression_log     (session_fk, turn_id, emotion, confidence, timestamp_ms)
```

---

## 10. Known Limitations & TODOs

> These are documented directly in the source code comments.

1. **`ia/` pipeline uses local files** (`runtime/interview_state.json`, `runtime/expression_log.jsonl`) — not safe for concurrent multi-user production. Must be replaced with DB-backed state using `InterviewSession`, `QALog`, and `ExpressionLog`.

2. **WebSocket consumer STT/DeepFace paths are placeholders** — `_placeholder_stt_from_audio_chunk()` and `_placeholder_expression_from_frame()` need to be wired to the actual `ia/` modules.

3. **Celery tasks not dispatched from upload view** — `pdf_to_images_task` and `ocr_images_task` are defined but not called after `VerificationUploadView` creates the job.

4. **STT module is microphone-oriented** — `ia/audio/stt_whisper/stt.py` reads from a physical mic. It needs a bytes/PCM input path for browser audio streamed over WebSocket.

5. **Expression monitor is process-local** — `ExpressionStream` captures webcam in a thread. In production, browser video frames must be sent via WebSocket and analyzed per-frame.

6. **No JWT/token auth** — only API Key + Session auth is implemented. JWT would be needed for browser clients.

---

## 11. How to Run

### Prerequisites
- Python 3.11+
- PostgreSQL (or set `DJANGO_USE_SQLITE=true`)
- Redis
- (Optional) NVIDIA + OpenRouter API keys for AI features

### Django Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser + API key via admin
python manage.py createsuperuser

# Start server (Daphne auto-selected if installed)
python manage.py runserver
```

### Celery Worker
```bash
celery -A vaas_project worker --loglevel=info
```

### Standalone AI Pipeline (local, no Django)
```bash
cd ia
pip install -r requirements.txt
# Copy and fill .env
python main.py --doctor demo/good_doctor/
```

### Postman Tests
Import `vaas_test_collection.json` into Postman. Set collection variables:
- `base_url` → `http://127.0.0.1:8000`
- `api_key` → raw key from Django admin → ClientAPIKey

Run requests in order: **Auth Check → Phase 1 Upload → Phase 4 Session Setup → Decision Status**

# API Documentation — VaaS Backend

---

## 1. Project Overview

This backend is a **Django + Django REST Framework (DRF)** API for a VaaS (Verification-as-a-Service) workflow, with support for **background processing (Celery)** and **real-time WebSockets (Django Channels)**.

- **HTTP API**: DRF `APIView` endpoints under `/api/…`
- **Auth**: Session auth + custom **API key** auth (`core.authentication.APIKeyAuthentication`)
- **Async / background**: Celery is configured to use **Redis** as broker and result backend (Redis DB 0/1 by default)
- **WebSockets**: Channels is configured with **Redis channel layer**; a live interview socket exists at `ws/interview/<uuid>/`
- **AI modules**: The AI pipeline logic lives in `ia/` (OCR, profile extraction, web verification, RAG, DeepFace expression, Whisper STT, Kokoro TTS, final evaluator). Today, the **full 9-step pipeline is implemented as a CLI orchestrator (`ia/main.py`) and is not fully wired to the Django endpoints** — only Celery wrappers for steps 1–2 exist.

---

## 2. Authentication & Headers

The API is secured by DRF `IsAuthenticated` by default (`vaas_project/settings.py`). Authentication is supported via:

- **SessionAuthentication** (browser / cookie-based sessions)
- **APIKeyAuthentication** (custom API key scheme)

### API Key Authentication (recommended for programmatic clients)

Implemented in `core/authentication.py`. The backend accepts either:

- **Header option A**: `X-Api-Key: <raw_secret>`
  - Also accepts `X-API-Key` casing variant
- **Header option B**: `Authorization: Api-Key <raw_secret>`
  - The keyword must be exactly **`Api-Key`** followed by a space

If an API key is present, it is **SHA-256 hashed** and matched against `core.models.ClientAPIKey.key_hash`. Only active keys (`is_active=True`) authenticate successfully.

### Common Required Headers

| Header | Value | When Required |
|---|---|---|
| `Content-Type` | `application/json` | JSON endpoints |
| `Content-Type` | `multipart/form-data` | File upload endpoints |
| `X-Api-Key` | `<raw_secret>` | All non-browser clients |
| `Authorization` | `Api-Key <raw_secret>` | Alternative to `X-Api-Key` |

---

## 3. REST API Endpoints

**Base prefix:** `/api/`

---

### 3.1 Health Check

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/api/health/` |
| **Description** | Authenticated health check; validates the caller is authenticated (API key or session). |

**Request Payload:** None

**Response — `200 OK`**
```json
{
  "status": "ok",
  "service": "vaas",
  "authenticated_user": "username"
}
```

**Error Responses**

| Status | Body |
|---|---|
| `401 Unauthorized` | `"Invalid API key."` |
| `403 Forbidden` | Not authenticated |

---

### 3.2 Verification — Upload (Phase 1)

| | |
|---|---|
| **Method** | `POST` |
| **Endpoint** | `/api/v1/verification/upload/` |
| **Content-Type** | `multipart/form-data` |
| **Description** | Uploads a PDF and creates a `VerificationJob`. Stores the PDF in Django storage under `verification/<job_uuid>/…`. Returns the created job/session UUID. |

**Request Fields**

| Field | Type | Required | Description |
|---|---|---|---|
| `doctor_id` | string | ✅ | External identifier for the subject |
| `file` | file (PDF) | ✅ | The PDF document to verify |

**Response — `201 Created`**
```json
{
  "session_uuid": "b7c4e3c3-7cbb-4fbb-a329-7d8e54f7d4b7",
  "job_id": "b7c4e3c3-7cbb-4fbb-a329-7d8e54f7d4b7",
  "subject_external_id": "12345",
  "status": "queued",
  "message": "Job created. Wire Celery (pdf_to_images_task / ocr_images_task) to populate decision."
}
```

**Error Responses**

| Status | Condition | Body |
|---|---|---|
| `400 Bad Request` | Missing `doctor_id` | `{ "detail": "doctor_id is required (form field)." }` |
| `400 Bad Request` | Missing `file` | `{ "detail": "file is required (PDF, form field name: file)." }` |
| `401/403` | Not authenticated | — |

---

### 3.3 Verification — Decision / Status

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/api/v1/verification/jobs/<job_id>/decision/` |
| **Description** | Returns the current job status and the computed "decision". Intended to be polled until the async pipeline completes. |

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `job_id` | UUID | The job identifier returned by the upload endpoint |

**Response — `200 OK`**
```json
{
  "session_uuid": "b7c4e3c3-7cbb-4fbb-a329-7d8e54f7d4b7",
  "job_status": "processing",
  "decision": "pending",
  "result": {
    "pdf_storage_path": "verification/b7c4e3c3-7cbb-4fbb-a329-7d8e54f7d4b7/upload.pdf",
    "original_filename": "upload.pdf"
  },
  "error_message": null
}
```

**Decision value logic**

| Condition | `decision` value |
|---|---|
| `result.decision` exists | returned as-is |
| `job_status == failed` | `"rejected"` |
| `job_status == succeeded` | `result.final_decision` or `"approved"` |
| Otherwise | `"pending"` |

**Error Responses**

| Status | Condition | Body |
|---|---|---|
| `400 Bad Request` | Invalid UUID format | `{ "detail": "Invalid job id." }` |
| `404 Not Found` | Job not found for authenticated user | `{ "detail": "Not found." }` |
| `401/403` | Not authenticated | — |

---

### 3.4 Interviews — Create Session

| | |
|---|---|
| **Method** | `POST` |
| **Endpoint** | `/api/v1/interviews/sessions/` |
| **Content-Type** | `application/json` |
| **Description** | Creates an `InterviewSession` (status `pending`) and returns its UUID. This UUID is used by the WebSocket live interview channel. |

**Request Fields** *(at least one required)*

| Field | Type | Required | Description |
|---|---|---|---|
| `doctor_id` | string | ⚠️ | Subject identifier (required unless `subject_external_id` is provided) |
| `subject_external_id` | string | ⚠️ | Alternative subject identifier |

**Response — `201 Created`**
```json
{
  "session_uuid": "5a4c2f2d-5e6e-4c18-a2e7-0c4d56f5878e",
  "subject_external_id": "12345",
  "status": "pending"
}
```

**Error Responses**

| Status | Condition | Body |
|---|---|---|
| `400 Bad Request` | Neither ID provided | `{ "detail": "doctor_id (or subject_external_id) is required." }` |
| `401/403` | Not authenticated | — |

---

## 4. WebSocket — Live Interview

### Connection

```
ws://<host>/ws/interview/<session_id>/
```

`session_id` is the UUID returned by `POST /api/v1/interviews/sessions/`.

### Authentication

The consumer relies on **Channels session/cookie authentication**. There is no API-key-over-WebSocket handling implemented at this time.

### Connection Close Codes

| Code | Meaning |
|---|---|
| `4400` | Invalid UUID format in URL |
| `4404` | `InterviewSession` not found |

---

### Client → Server Events

#### Binary frames (audio chunks)

Send raw audio chunk bytes as a **WebSocket binary frame**.

> ⚠️ The placeholder handler `_handle_binary_audio` exists, but no encoding contract is enforced yet (PCM / Opus / WAV, sample rate, etc.). Frontend and backend must align this separately.

#### Text frames (JSON control messages)

**`video_frame`** — send a base64-encoded image frame
```json
{ "type": "video_frame", "data": "<base64_image>" }
```

**`ping`** — keepalive
```json
{ "type": "ping" }
```

---

### Server → Client Events

**Invalid JSON received**
```json
{ "error": "invalid_json" }
```

**Pong (response to ping)**
```json
{ "type": "pong" }
```

> ⚠️ No additional outbound events (TTS audio, transcription tokens, expression confidence scores, interview prompts) are emitted yet. The consumer does not currently `group_send` any AI pipeline output over the socket.

---

## 5. Core AI Pipeline

### 5.1 Current Integration Status

| Layer | Status |
|---|---|
| Job creation & PDF storage | ✅ Implemented |
| Decision polling | ✅ Implemented |
| Interview session creation | ✅ Implemented |
| WebSocket connection & basic events | ✅ Implemented |
| Celery tasks for steps 1–2 | ✅ Defined (not chained) |
| Full 9-step pipeline triggered from HTTP | ⏳ Pending wiring |
| Real-time AI events over WebSocket | ⏳ Pending wiring |

---

### 5.2 Available Celery Tasks

Configured in `verification/tasks.py`. Redis is used as both broker (DB 0) and result backend (DB 1), with a 1-hour hard task time limit. Both tasks use `ack_late=True` and `bind=True`. No explicit retry policy is currently defined.

#### `pdf_to_images_task(pdf_paths, doctor_id, output_dir)`

Wraps `ia/pipeline/pdf_to_images.py::pdf_to_images`. Converts PDF pages into image files.

#### `ocr_images_task(image_paths)`

Wraps `ia/pipeline/ocr.py::run_ocr`. Runs OCR over image files and returns combined text.

---

### 5.3 Canonical 9-Step VaaS Pipeline

Defined in `ia/main.py::run_pipeline(...)` as a CLI orchestrator. This is the authoritative map of the intended VaaS flow.

---

#### Step 1 — PDF to Images

| | |
|---|---|
| **Module** | `ia/pipeline/pdf_to_images.py` |
| **Engine** | PyMuPDF |
| **Inputs** | PDF paths |
| **Outputs** | PNG image paths written to `data/images/<doctor_id>/` |

---

#### Step 2 — OCR

| | |
|---|---|
| **Module** | `ia/pipeline/ocr.py` |
| **AI** | OpenAI-compatible client (default model: `nvidia/nemotron-parse`) |
| **Inputs** | Image paths |
| **Outputs** | Combined OCR text (with page breaks) |
| **Fallback** | `extract_pdf_text_fallback(pdf_paths)` if OCR output is empty |

---

#### Step 3 — Vision Extraction (Profile Building)

| | |
|---|---|
| **Module** | `ia/pipeline/extractor.py` |
| **AI** | Vision LLM (default: `meta/llama-3.2-90b-vision-instruct`) |
| **Inputs** | Images + OCR text + declared name/specialty |
| **Outputs** | Structured `profile` dict (identity, license, institution, flags/anomalies, etc.) |

#### Step 3b — Visual Document Checks

| | |
|---|---|
| **Module** | `ia/pipeline/visual_checks.py` (`visual_check_documents`) |
| **AI** | Vision model, per-image |
| **Inputs** | Images + profile |
| **Outputs** | `visual_results` — document-level integrity signals (stamp/signature presence) |

---

#### Step 4 — Web Verification

| | |
|---|---|
| **Module** | `ia/pipeline/web_verifier.py` |
| **AI** | `perplexity/sonar` via OpenRouter |
| **Inputs** | Profile (university, hospital, specialty, etc.) |
| **Outputs** | Verification findings, sources, and flags |

---

#### Step 5 — Survey Questions / Answers

| | |
|---|---|
| **Module** | `ia/pipeline/survey_gen.py` |
| **AI** | Chat LLM (default: `meta/llama-3.3-70b-instruct`) |
| **Inputs** | Profile + verification |
| **Outputs** | Survey question set |

> ⚠️ Current CLI behavior: `ia/main.py` loads `survey_qa` from mock data instead of generating inline.

---

#### Step 6 — RAG Ingest

| | |
|---|---|
| **Module** | `ia/pipeline/rag.py` |
| **AI** | Embeddings: `sentence-transformers/all-MiniLM-L6-v2` + ChromaDB |
| **Inputs** | Profile + verification + survey QA + `doctor_id` |
| **Outputs** | Persistent Chroma collection (`doctor_<doctor_id>`); context retrievable via `get_full_context(doctor_id)` |

---

#### Step 7 — Expression Tracking

| | |
|---|---|
| **Module** | `ia/pipeline/expression.py` |
| **AI** | DeepFace (`DeepFace.analyze(actions=["emotion"])`) |
| **Inputs** | Webcam frames (currently via `cv2.VideoCapture(0)`) |
| **Outputs** | Per-turn emotion log + summary metrics (dominant emotion, stress ratio, etc.) |

---

#### Step 8 — Voice Interview

| | |
|---|---|
| **Module** | `ia/pipeline/interview.py` + `ia/pipeline/audio_io.py` |
| **AI — Questions** | Chat LLM (default: `meta/llama-3.3-70b-instruct`) |
| **AI — STT** | Whisper (faster-whisper) under `ia/audio/stt_whisper/` |
| **AI — TTS** | Kokoro (ONNX) under `ia/audio/tts_kokoro/` |
| **Inputs** | RAG context + expression stream + audio IO |
| **Outputs** | Interview transcript dict (saved to `transcripts/<doctor_id>.json` by CLI) |

---

#### Step 9 — Final Evaluation

| | |
|---|---|
| **Module** | `ia/pipeline/evaluator.py` |
| **AI** | LLM (default: `meta/llama-3.3-70b-instruct`) |
| **Inputs** | Profile + web verification + transcript + survey answers + expression summary |
| **Outputs** | Final report dict (saved to `reports/<doctor_id>_report.json` by CLI) |

---

### 5.4 Pending Wiring (What Still Needs to Be Done)

For the VaaS pipeline to be fully operational through the HTTP API, the following work is required:

1. `POST /api/v1/verification/upload/` (or a dedicated "start verification" endpoint) must enqueue a **Celery chain for steps 1 → 9**.
2. Each pipeline step must **persist its outputs back into `VerificationJob.result`** and update `VerificationJob.status` so that `GET …/decision/` reflects real results.
3. The WebSocket consumer must **emit real-time events** (transcription partials, TTS audio frames, expression scores) sourced from Whisper / Kokoro / DeepFace.

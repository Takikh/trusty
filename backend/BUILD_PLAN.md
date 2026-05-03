# Doctor Credential Verification — AI Pipeline Build Plan
## Hackathon | 30h Budget

---

## API Keys

```
OPENROUTER_API_KEY=REDACTED_OPENROUTER_KEY
NVIDIA_API_KEY=REDACTED_NVIDIA_KEY
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

---

## Final Tech Stack

| Job | Tool | API / Source |
|---|---|---|
| PDF → Images | `pymupdf` | local |
| Document Classification | `llama-3.2-90b-vision-instruct` | NVIDIA |
| OCR (raw text) | `nvidia/nemotron-ocr-v1` | NVIDIA |
| Structured Extraction | `llama-3.2-90b-vision-instruct` | NVIDIA |
| Web Verification | `perplexity/sonar` | OpenRouter |
| Question Generation | `nvidia/llama-3.3-70b-instruct` | NVIDIA |
| Interview LLM | `nvidia/llama-3.3-70b-instruct` | NVIDIA |
| Answer Evaluation | `nvidia/llama-3.3-70b-instruct` | NVIDIA |
| Final Evaluation | `nvidia/llama-3.3-70b-instruct` | NVIDIA |
| STT | `faster-whisper` (base, CPU) | local |
| TTS | `kokoro-onnx` | local |
| Face Expressions | `deepface` | local |
| Vector DB | `chromadb` | local |
| Embeddings | `all-MiniLM-L6-v2` | local |

---

## Project Folder Structure

```
hackathon/
├── BUILD_PLAN.md              ← this file
├── .env                       ← API keys
├── requirements.txt
├── main.py                    ← runs everything end-to-end
│
├── pipeline/
│   ├── __init__.py
│   ├── pdf_to_images.py       ← STEP 1
│   ├── ocr.py                 ← STEP 2
│   ├── extractor.py           ← STEP 3
│   ├── web_verifier.py        ← STEP 4
│   ├── question_gen.py        ← STEP 5
│   ├── rag.py                 ← STEP 6
│   ├── expression.py          ← STEP 7
│   ├── interview.py           ← STEP 8
│   └── evaluator.py           ← STEP 9
│
├── data/
│   ├── uploads/               ← doctor puts PDFs here
│   ├── images/                ← converted page PNGs
│   └── profiles/              ← extracted JSON per doctor
│
├── transcripts/               ← interview Q&A saved here
├── reports/                   ← final verdict reports
└── db/                        ← ChromaDB files
```

---

## Full Pipeline Flow

### ─── PHASE 1: REGISTRATION (text, before interview) ───

```
Doctor fills form: name, specialty, experience summary
    +
Doctor uploads PDFs
    │
    ▼ STEP 1
PDF → Images (one PNG per page, 200 DPI)
    │
    ▼ STEP 2
OCR each page → raw text (nemotron-ocr-v1)
    │
    ▼ STEP 3
Vision LLM reads images + OCR text → structured profile JSON
(name, specialty, license, institution, jobs, flags, anomalies)
    │
    ▼ STEP 4
Web Verifier sends profile to Perplexity Sonar (web search)
→ confirms: university real? dean verified? hospital confirmed?
    │
    ▼ STEP 5  ← SURVEY (text, not voice)
LLM generates 3 open-ended survey questions from the profile:
  Q1 — about their specialty expertise (open, descriptive)
  Q2 — about a specific experience at their most recent employer
  Q3 — about their approach / methodology in their field

Doctor reads and answers all 3 IN TEXT (like a form)
Survey Q&A saved as structured data
    │
    ▼ STEP 6
RAG Ingest:
  profile + web verification + survey Q&A answers → ChromaDB
```

### ─── PHASE 2: VOICE INTERVIEW (voice, after registration) ───

```
    ▼ STEP 7 (parallel thread during interview)
DeepFace reads webcam → logs emotion per turn_id
    │
    ▼ STEP 8 — Conversational Voice Interview
AI uses ChromaDB (profile + survey answers) as context:
  Turn 1: Greet doctor → ask them to EXPAND on their survey answer 1
  Turn 2: Probe deeper into their survey answer 2 (experience at employer)
  Turn 3: Ask follow-up on survey answer 3 (methodology/approach)

For each turn:
  - LLM generates spoken utterance referencing what doctor already said
  - TTS speaks it (Kokoro)
  - Doctor answers out loud
  - STT transcribes (Faster-Whisper)
  - Append to transcript
→ NOT testing right/wrong facts — probing elaboration & consistency
→ Save full transcript JSON
```

### ─── PHASE 3: EVALUATION ───

```
    ▼ STEP 9
Evaluation Agent reads:
  - Document profile (STEP 3)
  - Web verification (STEP 4)
  - Interview transcript (STEP 8)
  - Expression log (STEP 7)
→ outputs final verdict JSON + report
```

---

## STEP 0 — Setup
**What I will do:**
Create `.env`, `requirements.txt`, empty pipeline files, and folder structure.

**`.env`:**
```
OPENROUTER_API_KEY=REDACTED_OPENROUTER_KEY
NVIDIA_API_KEY=REDACTED_NVIDIA_KEY
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
CHROMA_DB_PATH=./db
UPLOADS_DIR=./data/uploads
IMAGES_DIR=./data/images
PROFILES_DIR=./data/profiles
TRANSCRIPTS_DIR=./transcripts
REPORTS_DIR=./reports
```

**`requirements.txt`:**
```
pymupdf
pillow
openai
chromadb
sentence-transformers
faster-whisper
sounddevice
numpy
kokoro-onnx
soundfile
deepface
opencv-python
python-dotenv
```

**Output:** All folders and empty files created.

---

## STEP 1 — `pipeline/pdf_to_images.py`
**What I will do:**
Open each PDF with `pymupdf` (fitz). Render every page as a 200 DPI PNG image. Save to `data/images/{doctor_id}/`. Return a list of all image paths grouped by document.

**Input:**
```python
pdf_paths: list[str]   # paths to uploaded PDFs
doctor_id: str
```

**Output:**
```python
[
  {
    "doc_name": "diploma.pdf",
    "pages": ["data/images/doc1/diploma_page_0.png", "data/images/doc1/diploma_page_1.png"]
  },
  ...
]
```

**Key code:**
```python
import fitz  # pymupdf

def pdf_to_images(pdf_path, doctor_id, output_dir):
    doc = fitz.open(pdf_path)
    paths = []
    for i, page in enumerate(doc):
        mat = fitz.Matrix(200/72, 200/72)   # 200 DPI
        pix = page.get_pixmap(matrix=mat)
        out_path = f"{output_dir}/{doc_name}_page_{i}.png"
        pix.save(out_path)
        paths.append(out_path)
    return paths
```

---

## STEP 2 — `pipeline/ocr.py`
**What I will do:**
Send each page image to NVIDIA `nemotron-ocr-v1`. The image is base64-encoded and sent via the OpenAI-compatible API. Returns raw text for that page. All pages of one document are concatenated.

**Input:** `image_path: str`
**Output:** `str` — raw OCR text

**API call:**
```python
import base64
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

with open(image_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="nvidia/nemotron-ocr-v1",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract all text from this document image. Return only the raw text, nothing else."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]
    }],
    max_tokens=4096
)
return response.choices[0].message.content
```

**Error handling:** If API fails → return empty string, log warning. Never block pipeline.

---

## STEP 3 — `pipeline/extractor.py`
**What I will do:**
Send ALL page images (as base64) + the combined OCR text to `llama-3.2-90b-vision-instruct`. The LLM reads both the visual document and the OCR text to produce a structured JSON profile. Also classifies each document type (diploma / job_letter / certificate / other).

**Input:**
```python
image_paths: list[str]
ocr_text: str            # all pages combined
declared_name: str       # what the doctor said their name is
declared_specialty: str  # what the doctor said their specialty is
```

**Output (saved to `profiles/{doctor_id}/profile.json`):**
```json
{
  "full_name": "Ahmed Benali",
  "declared_name_match": true,
  "specialty": "Cardiology",
  "license_number": "DZ-MED-2019-4821",
  "license_issuer": "Conseil National de l'Ordre des Médecins",
  "license_expiry": "2027-12",
  "institution": "Université d'Alger — Faculté de Médecine",
  "graduation_year": 2019,
  "jobs": [
    {"employer": "CHU Mustapha Pacha", "role": "Cardiologue", "start": "2020-01", "end": "present"}
  ],
  "document_types": ["diploma", "job_letter"],
  "document_flags": ["stamp_present", "signature_visible", "structure_match"],
  "anomalies": [],
  "ocr_confidence": 0.91
}
```

**LLM prompt:**
```
You are a document verification expert for a healthcare platform.
You receive multiple medical documents as images, plus their OCR text.

OCR TEXT:
{ocr_text}

Extract this exact JSON (no extra text):
{
  "full_name": "...",
  "declared_name_match": true/false,   <- does name match "{declared_name}"?
  "specialty": "...",
  "license_number": "... or null",
  "license_issuer": "... or null",
  "license_expiry": "YYYY-MM or null",
  "institution": "... or null",
  "graduation_year": integer or null,
  "jobs": [{"employer":"...","role":"...","start":"YYYY-MM","end":"YYYY-MM or present"}],
  "document_types": ["diploma","job_letter","certificate","other"],
  "document_flags": ["stamp_present","signature_visible","structure_match",...],
  "anomalies": ["list any suspicious findings"],
  "ocr_confidence": 0.0 to 1.0
}
```

---

## STEP 4 — `pipeline/web_verifier.py`
**What I will do:**
Take the extracted profile (university, employer names, dean name if found) and send ONE structured query to `perplexity/sonar` via OpenRouter. Perplexity has live web search — it will search university websites, hospital directories, and medical registries automatically.

**Input:** profile JSON from Step 3
**Output:**
```json
{
  "university_confirmed": true,
  "university_is_medical_faculty": true,
  "dean_verified": "true",
  "hospital_confirmed": true,
  "hospital_has_specialty": true,
  "web_sources": ["https://..."],
  "scraper_flags": []
}
```

**API call:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

prompt = f"""
Search the web and verify these medical credentials:

1. University: "{profile['institution']}"
   - Does this university exist?
   - Does it have a medical faculty (faculté de médecine)?
   - Is "{profile.get('dean_name', 'unknown')}" listed as dean/rector?

2. Employer: "{profile['jobs'][0]['employer'] if profile['jobs'] else 'none'}"
   - Is this a real hospital or clinic?
   - Does it have a {profile['specialty']} department?

Return ONLY this JSON:
{{
  "university_confirmed": true/false,
  "university_is_medical_faculty": true/false,
  "dean_verified": "true"/"false"/"unknown",
  "hospital_confirmed": true/false,
  "hospital_has_specialty": true/false,
  "web_sources": ["list of URLs checked"],
  "scraper_flags": ["any anomalies found"]
}}
"""

response = client.chat.completions.create(
    model="perplexity/sonar",
    messages=[{"role": "user", "content": prompt}]
)
```

**Fallback:** If Perplexity fails or times out → return `{"university_confirmed": null, "dean_verified": "unknown", ...}` and continue. Never block pipeline.

---

## STEP 5 — `pipeline/survey_gen.py`
**What I will do:**
Generate 3 open-ended SURVEY questions from the doctor's profile. These questions are shown to the doctor during registration — they answer in TEXT, not voice. The goal is NOT to test clinical knowledge right/wrong, but to get the doctor to describe their experience and specialty in their own words, which the voice interview will later probe.

**Input:** profile JSON + verification JSON
**Output:**
```json
[
  {
    "id": "sq1",
    "text": "Describe your main area of expertise within Cardiology and what you focus on most in your daily practice.",
    "category": "specialty_expertise",
    "purpose": "Get a self-description of expertise to probe during voice interview"
  },
  {
    "id": "sq2",
    "text": "During your time at CHU Mustapha Pacha, what was a challenging case that shaped your approach to patient care?",
    "category": "work_experience",
    "purpose": "Get a specific work story to follow up on during voice interview"
  },
  {
    "id": "sq3",
    "text": "How would you describe your clinical methodology or approach when a patient presents with a complex cardiac condition?",
    "category": "methodology",
    "purpose": "Get a process description to probe consistency in voice interview"
  }
]
```

After the doctor submits text answers, the module stores:
```json
{
  "survey_qa": [
    {"id": "sq1", "question": "...", "answer": "I focus on interventional cardiology, specifically stenting and PCI procedures..."},
    {"id": "sq2", "question": "...", "answer": "We had a 58-year-old with triple vessel disease..."},
    {"id": "sq3", "question": "...", "answer": "My approach starts with a full history..."}
  ]
}
```

**Rules for survey question generation:**
- Q1: Ask them to describe their expertise area in their own words (open-ended)
- Q2: Reference a specific employer from their documents — ask for a real story
- Q3: Ask about their clinical methodology or approach (process-oriented)
- All questions must be answerable by any legitimate doctor — no trick questions
- Questions must create content the voice interview can probe deeper

---

## STEP 6 — `pipeline/rag.py`
**What I will do:**
Take all data from steps 3, 4, and 5. Break into text chunks. Embed each chunk with `all-MiniLM-L6-v2`. Store in ChromaDB collection `doctor_{doctor_id}`.

**Chunks stored (7 total):**
```
chunk "personal":
"Doctor: Ahmed Benali. Specialty: Cardiology. Licensed by: Conseil National
de l'Ordre des Médecins (license #DZ-MED-2019-4821, expires 2027-12).
Graduated from Université d'Alger — Faculté de Médecine in 2019."

chunk "jobs":
"Work history: Cardiologue at CHU Mustapha Pacha (2020-01 to present)."

chunk "document_check":
"Document analysis: Flags: stamp_present, signature_visible, structure_match.
Anomalies: none. OCR confidence: 0.91. Name match: true."

chunk "web_verification":
"Web verification: University Université d'Alger confirmed (medical faculty: yes).
Dean verified: unknown. Hospital CHU Mustapha Pacha confirmed (cardiology: yes)."

chunk "survey_sq1":
"Survey Q1 (specialty_expertise):
Question: Describe your main area of expertise within Cardiology.
Doctor answered: I focus on interventional cardiology, specifically coronary
stenting and PCI. I perform around 15-20 procedures per month..."

chunk "survey_sq2":
"Survey Q2 (work_experience):
Question: During your time at CHU Mustapha Pacha, describe a challenging case.
Doctor answered: We had a 58-year-old with triple vessel disease presenting
with acute NSTEMI..."

chunk "survey_sq3":
"Survey Q3 (methodology):
Question: How do you approach a complex cardiac presentation?
Doctor answered: My approach starts with stabilization, then full history..."
```

**Functions exposed:**
```python
def ingest(profile, verification, questions, doctor_id)
def retrieve(query, doctor_id, n=3) -> list[str]
def get_all_questions(doctor_id) -> list[dict]
def get_profile_context(doctor_id) -> str
```

---

## STEP 7 — `pipeline/expression.py`
**What I will do:**
Wrap DeepFace in a background thread. The thread reads frames from the webcam at ~2fps. Every frame, it detects the dominant emotion and logs it with the current `question_id` and timestamp. Designed to never crash if no face is detected.

**Input:** shared variable `active_question_id: str`
**Output:** `expression_log: list[dict]`

```python
from deepface import DeepFace
import cv2
import threading
import time

class ExpressionStream:
    def __init__(self):
        self.active_question_id = None
        self.log = []
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _loop(self):
        cap = cv2.VideoCapture(0)
        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            try:
                result = DeepFace.analyze(
                    frame,
                    actions=["emotion"],
                    enforce_detection=False,   # ← never crash without face
                    silent=True
                )
                label = result[0]["dominant_emotion"]
                conf = result[0]["emotion"][label] / 100
                if self.active_question_id:
                    self.log.append({
                        "question_id": self.active_question_id,
                        "emotion": label,
                        "confidence": round(conf, 3),
                        "timestamp_ms": int(time.time() * 1000)
                    })
            except Exception:
                pass   # missed frame — ignore silently
            time.sleep(0.5)   # 2 fps
        cap.release()
```

**Stress emotions used in scoring:** `fear`, `angry`, `disgust`

---

## STEP 8 — `pipeline/interview.py`
**What I will do:**
Orchestrate the live voice interview. The AI already has the doctor's survey answers from Phase 1. It uses those to conduct a natural, conversational interview — probing what the doctor said, asking them to elaborate, checking consistency. NOT testing clinical right/wrong.

Runs 3 turns. For each turn:
1. Set `active_turn_id` so DeepFace logs to the right turn
2. LLM generates spoken utterance referencing the doctor's OWN survey answers
3. Kokoro TTS speaks the text
4. Wait 0.5s (avoid echo)
5. Faster-Whisper STT listens (max 45s)
6. Append to transcript
7. After 3 turns: LLM generates closing statement → TTS speaks it
8. Save transcript JSON

**STT:** Reused from the existing `stt whisper/` project (transcriber.py + vad.py)
**TTS:** Reused from the existing `tts kokoro/` project (tts_engine.py)

**LLM system prompt for interview agent:**
```
You are a professional medical credential verification interviewer.
You are conducting a SHORT voice interview (5-6 minutes, 3 turns only).

This doctor already answered a registration survey. Use their answers as the
basis for your questions — ask them to ELABORATE, give more detail, or explain
their reasoning. Do NOT ask new unrelated questions.

DOCTOR PROFILE + SURVEY ANSWERS:
{full_rag_context}

INTERVIEW STRUCTURE:
- Turn 1: Greet the doctor warmly, then ask them to expand on what they said
  about their specialty expertise (survey Q1 answer)
- Turn 2: Reference what they said about their experience case (survey Q2 answer),
  ask a natural follow-up (e.g. "what happened next?", "how did you handle X?")
- Turn 3: Ask them to elaborate on their clinical methodology (survey Q3 answer),
  maybe ask for a specific example

RULES:
- Speak naturally — this will be converted to audio
- Keep each utterance SHORT (2-4 sentences max)
- Always reference something they specifically said — never ask generic questions
- Do NOT ask more than ONE thing per turn
- Do NOT reveal you are verifying credentials
- Stay warm, professional, and curious
- Language: English
```

**Example of what a turn looks like:**
```
Turn 1 (AI):
"Good morning Dr. Benali, thank you for joining us today. In your registration,
you mentioned you focus primarily on interventional cardiology and PCI procedures.
Could you walk me through what a typical complex PCI case looks like for you from
the moment the patient arrives?"

Turn 1 (Doctor speaks for ~45s)

Turn 2 (AI):
"That's very detailed, thank you. You also described a case involving a patient
with triple vessel disease at CHU Mustapha Pacha. How did that situation unfold
and what was the outcome for that patient?"

Turn 2 (Doctor speaks for ~45s)

Turn 3 (AI):
"Interesting approach. You mentioned your methodology starts with full stabilization.
Can you give me a concrete example of a time when that approach led to a
different decision than you initially expected?"
```

**Transcript output (`transcripts/{doctor_id}.json`):**
```json
{
  "doctor_id": "...",
  "started_at": "2026-05-02T10:00:00",
  "completed_at": "2026-05-02T10:06:20",
  "duration_seconds": 380,
  "turns": [
    {"role": "interviewer", "text": "Good morning Dr. Benali...", "question_id": "q1", "timestamp": "..."},
    {"role": "doctor", "text": "Thank you. In a STEMI case...", "question_id": "q1", "timestamp": "..."},
    {"role": "interviewer", "text": "Thank you for that. Moving on...", "question_id": "q2", "timestamp": "..."},
    ...
  ],
  "turns": [
    {"role": "interviewer", "text": "Good morning Dr. Benali...", "turn_id": "t1", "references_survey": "sq1"},
    {"role": "doctor",      "text": "I focus on interventional cardiology...", "turn_id": "t1"},
    {"role": "interviewer", "text": "That's detailed, thank you...", "turn_id": "t2", "references_survey": "sq2"},
    {"role": "doctor",      "text": "We had a 58-year-old with...", "turn_id": "t2"},
    {"role": "interviewer", "text": "Interesting approach...", "turn_id": "t3", "references_survey": "sq3"},
    {"role": "doctor",      "text": "Yes, in one case the initial ECG showed...", "turn_id": "t3"}
  ]
}
```

---

## STEP 9 — `pipeline/evaluator.py`
**What I will do:**
Final evaluation agent. Takes all outputs from previous steps. Sends to `llama-3.3-70b-instruct` with a structured evaluation prompt. Returns a verdict JSON and saves the full report.

**Input:**
- Profile JSON (step 3)
- Web verification JSON (step 4)
- Interview transcript + QA log (step 8)
- Expression log (step 7)

**Scoring logic (computed in Python, not LLM):**
```python
# Document score (50% weight)
doc_score = 0.0
if profile["declared_name_match"]:          doc_score += 0.20
if "stamp_present" in profile["flags"]:     doc_score += 0.10
if "structure_match" in profile["flags"]:   doc_score += 0.10
if verification["university_confirmed"]:    doc_score += 0.20
if verification["hospital_confirmed"]:      doc_score += 0.20
if verification["dean_verified"] == "true": doc_score += 0.20
# max = 1.0

# Interview + Survey score (35% weight)
# LLM evaluates holistically:
# - Does the voice interview EXPAND on the survey answers consistently?
# - Did the doctor contradict themselves between survey text and spoken answers?
# - Is the level of detail plausible for someone with their claimed experience?
# Returns a score 0.0-1.0
interview_score = llm_evaluate_consistency(survey_qa, transcript)

# Expression score (15% weight)
stress_events = [e for e in expression_log
                 if e["emotion"] in {"fear", "angry", "disgust"}
                 and e["confidence"] > 0.6]
stress_ratio = len(stress_events) / max(len(expression_log), 1)
expression_score = max(0.0, 1.0 - stress_ratio * 2)

# Final
final_score = (doc_score * 0.50) + (interview_score * 0.35) + (expression_score * 0.15)
```

**Interview consistency evaluation prompt (for `llm_evaluate_consistency`):**
```
You are evaluating a medical credential interview.

The doctor submitted these SURVEY ANSWERS during registration:
{survey_qa}

During the VOICE INTERVIEW they said:
{transcript}

Evaluate on a scale of 0.0 to 1.0:
- Consistency: Do the voice answers match and expand on the survey answers?
- Plausibility: Is the level of detail consistent with the claimed experience?
- Red flags: Any contradictions between what they wrote and what they said?

Return ONLY JSON:
{"consistency_score": 0.0-1.0, "red_flags": [], "assessment": "strong/weak/inconsistent"}
```

**Verdict rules:**
```python
if final_score >= 0.75 and not profile["anomalies"] and profile["declared_name_match"]:
    verdict = "VERIFIED"
elif final_score >= 0.45:
    verdict = "NEEDS_MANUAL_REVIEW"
else:
    verdict = "REJECTED"
```

**LLM generates the human-readable recommendation paragraph.**

**Report output (`reports/{doctor_id}_report.json`):**
```json
{
  "doctor_id": "...",
  "generated_at": "...",
  "verdict": "VERIFIED",
  "confidence_score": 84,
  "score_breakdown": {
    "document_score": 0.90,
    "interview_score": 1.0,
    "expression_score": 0.85,
    "final_weighted": 0.918
  },
  "document_validity": {
    "name_match": true,
    "license_valid": true,
    "specialty_match": true,
    "university_confirmed": true,
    "hospital_confirmed": true,
    "dean_verified": "unknown",
    "anomalies": []
  },
  "interview_assessment": {
    "clinical_knowledge": "strong",
    "factual_consistency": true,
    "red_flags": [],
    "key_quotes": ["In a STEMI case, first priority is door-to-balloon time..."]
  },
  "expression_summary": {
    "dominant_emotion_during_factual_questions": "neutral",
    "stress_ratio": 0.05
  },
  "recommendation": "Doctor Ahmed Benali demonstrates strong clinical knowledge consistent with claimed specialty of Cardiology. All submitted documents appear authentic with stamps and signatures present. University and employer are verified. Interview responses were accurate and detailed. Recommend APPROVAL."
}
```

---

## STEP 10 — `main.py` (Orchestrator)
**What I will do:**
Single CLI entry point. Runs all 9 steps in order. Prints progress. At the end, prints the verdict.

```bash
python main.py \
  --pdf data/uploads/diploma.pdf data/uploads/license.pdf \
  --name "Dr. Ahmed Benali" \
  --specialty "Cardiology" \
  --doctor_id demo_001
```

**Flow:**
```python
async def run_pipeline(args):
    print("[1/9] Converting PDFs to images...")
    images = pdf_to_images(args.pdf, args.doctor_id)

    print("[2/9] Running OCR...")
    ocr_text = run_ocr(images)

    print("[3/9] Extracting structured profile...")
    profile = extract_profile(images, ocr_text, args.name, args.specialty)

    print("[4/9] Verifying via web search...")
    verification = verify_web(profile)

    print("[5/9] Generating interview questions...")
    questions = generate_questions(profile, verification)

    print("[6/9] Ingesting into ChromaDB...")
    ingest_rag(profile, verification, questions, args.doctor_id)

    print("[7/9] Starting expression stream...")
    expr_stream = ExpressionStream()
    expr_stream.start()

    print("[8/9] Running voice interview...")
    transcript = run_interview(args.doctor_id, expr_stream)
    expr_stream.stop()

    print("[9/9] Evaluating...")
    report = evaluate(profile, verification, transcript, expr_stream.log)

    print(f"\n{'='*50}")
    print(f"VERDICT: {report['verdict']}")
    print(f"Score:   {report['confidence_score']}/100")
    print(f"Report:  reports/{args.doctor_id}_report.json")
    print(f"{'='*50}\n")
```

---

## Build Order & Time Estimates

| # | File | What it does | Est. Time |
|---|---|---|---|
| 0 | Setup | Folders, .env, requirements.txt | 20 min |
| 1 | `pdf_to_images.py` | PDF → PNG pages | 30 min |
| 2 | `ocr.py` | nemotron-ocr-v1 API call | 45 min |
| 3 | `extractor.py` | llama vision → profile JSON | 1h 30min |
| 4 | `web_verifier.py` | Perplexity Sonar web search | 45 min |
| 5 | `question_gen.py` | Generate 3 questions | 30 min |
| 6 | `rag.py` | ChromaDB ingest + retrieval | 1h |
| 7 | `expression.py` | DeepFace webcam thread | 30 min |
| 8 | `interview.py` | STT + LLM + TTS loop | 3h |
| 9 | `evaluator.py` | Scoring + verdict | 1h |
| 10 | `main.py` | Wire everything together | 30 min |
| **Total** | | | **~10h** |

---

## Demo Profiles to Prepare

### ✅ Good Doctor (`demo/good/`)
- Valid diploma PDF with stamp and signature
- License with matching name
- Questions answered correctly
- Calm face during interview
- Expected verdict: **VERIFIED**

### ❌ Fake Doctor (`demo/fake/`)
- Diploma with wrong name (doesn't match declared)
- Missing stamp
- Clinical questions answered incorrectly
- Expected verdict: **REJECTED**

---

## Key Risks & Mitigations

| Risk | Fix |
|---|---|
| nemotron-ocr API format wrong | Test Step 2 in isolation first with a single image |
| STT picks up TTS audio (echo) | Add `time.sleep(0.5)` after TTS ends, before STT starts |
| LLM returns broken JSON | Wrap in `try/except`, use regex to find `{...}` in response |
| DeepFace first-run downloads weights (~600 MB) | Run `from deepface import DeepFace` before demo to pre-download |
| Interview too long | Hard cap: 3 questions max, 45s STT timeout each |
| Perplexity returns mixed language | Add "Return response in English only" to prompt |

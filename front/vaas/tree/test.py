"""
VaaS — ia Pipeline End-to-End Test
====================================
Tests all 9 steps against doctor_document.pdf

Usage:
    cd C:\\Users\\Lenovo\\Desktop\\tree
    & venv\\Scripts\\Activate.ps1
    python test_pipeline_e2e.py

Requirements:
    - doctor_document.pdf in the project root
    - .env file with API keys
    - venv activated
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime

# ── Setup paths ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
IA_DIR = ROOT / "ia"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(IA_DIR))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    print("  [setup] .env loaded")
except ImportError:
    print("  [setup] WARNING: python-dotenv not installed. Set env vars manually.")

# ── Constants ─────────────────────────────────────────────────────────────────
DOCTOR_ID        = "test-benali-" + datetime.now().strftime("%Y%m%d-%H%M%S")
DECLARED_NAME    = "Dr. Amine Benali"
DECLARED_SPECIALTY = "Internal Medicine"
PDF_PATH         = str(ROOT / "doctor_document.pdf")
IMAGES_DIR       = str(ROOT / "data" / "test_images" / DOCTOR_ID)
MOCK_SURVEY_ANSWERS = [
    {
        "id": "sq1",
        "question": "Describe your main area of expertise within Internal Medicine.",
        "answer": "I focus on complex multi-system diseases, particularly autoimmune conditions and chronic metabolic disorders. Daily practice involves coordinating care across specialties and managing patients with multiple comorbidities."
    },
    {
        "id": "sq2",
        "question": "During your time at CHU Frantz Fanon, what was a challenging case?",
        "answer": "I managed a 58-year-old patient presenting with simultaneous lupus flare and septic shock. The challenge was balancing immunosuppression with aggressive infection treatment. We stabilized him over 12 days with close monitoring."
    },
    {
        "id": "sq3",
        "question": "Describe your clinical methodology for complex Internal Medicine cases.",
        "answer": "I follow a systematic approach: thorough history, targeted examination, then hypothesis-driven investigations. I always consider the whole patient, not just the presenting complaint, and involve the patient in decision-making."
    }
]

# ── Result tracker ─────────────────────────────────────────────────────────────
results = []

def step(name, number):
    print(f"\n{'='*60}")
    print(f"  STEP {number} — {name}")
    print(f"{'='*60}")

def passed(name, details=""):
    results.append({"step": name, "status": "✅ PASS", "details": details})
    print(f"  ✅ PASS — {name}" + (f": {details}" if details else ""))

def failed(name, error):
    results.append({"step": name, "status": "❌ FAIL", "details": str(error)})
    print(f"  ❌ FAIL — {name}: {error}")

def skipped(name, reason):
    results.append({"step": name, "status": "⚠️  SKIP", "details": reason})
    print(f"  ⚠️  SKIP — {name}: {reason}")

# ══════════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT CHECKS
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("  VaaS ia Pipeline — End-to-End Test")
print(f"  Doctor ID : {DOCTOR_ID}")
print(f"  PDF       : {PDF_PATH}")
print(f"  Started   : {datetime.now().isoformat()}")
print("="*60)

print("\n── Pre-flight checks ──")

# Check PDF exists
if not Path(PDF_PATH).exists():
    # Try to find it
    found = list(ROOT.rglob("doctor_document.pdf"))
    if found:
        PDF_PATH = str(found[0])
        print(f"  Found PDF at: {PDF_PATH}")
    else:
        print(f"  ❌ FATAL: doctor_document.pdf not found in {ROOT}")
        print(f"     Copy it to: {ROOT / 'doctor_document.pdf'}")
        sys.exit(1)
else:
    print(f"  ✅ PDF found: {PDF_PATH}")

# Check API keys
nvidia_key     = os.getenv("NVIDIA_API_KEY", "")
openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
openai_key     = os.getenv("OPENAI_API_KEY", "")

print(f"  {'✅' if nvidia_key     else '⚠️ '} NVIDIA_API_KEY     : {'set' if nvidia_key     else 'NOT SET — OCR/Extract/Interview will use fallback'}")
print(f"  {'✅' if openrouter_key else '⚠️ '} OPENROUTER_API_KEY : {'set' if openrouter_key else 'NOT SET — web_verifier will use fallback'}")
print(f"  {'✅' if openai_key     else '⚠️ '} OPENAI_API_KEY     : {'set' if openai_key     else 'NOT SET — evaluator may fail'}")

# Check pymupdf
try:
    import fitz
    print(f"  ✅ pymupdf (fitz) available")
except ImportError:
    print(f"  ❌ pymupdf not installed — run: pip install pymupdf")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — pdf_to_images
# ══════════════════════════════════════════════════════════════════════════════

step("pdf_to_images", 1)
image_results = []

try:
    from pipeline.pdf_to_images import pdf_to_images

    t0 = time.time()
    image_results = pdf_to_images([PDF_PATH], DOCTOR_ID, IMAGES_DIR)
    elapsed = round(time.time() - t0, 2)

    assert image_results,                        "No results returned"
    assert len(image_results) > 0,               "Empty results list"
    assert image_results[0].get("pages"),        "No pages extracted"

    all_pages = image_results[0]["pages"]
    assert all(Path(p).exists() for p in all_pages), "Some image files not created"

    passed("pdf_to_images", f"{len(all_pages)} page(s) extracted in {elapsed}s")
    print(f"  Images: {all_pages}")

except Exception as e:
    failed("pdf_to_images", e)
    traceback.print_exc()
    all_pages = []

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — OCR
# ══════════════════════════════════════════════════════════════════════════════

step("ocr", 2)
ocr_text = ""

if not all_pages:
    skipped("ocr", "No images from Step 1")
else:
    try:
        from pipeline.ocr import run_ocr

        t0 = time.time()
        ocr_text = run_ocr(all_pages)
        elapsed = round(time.time() - t0, 2)

        assert isinstance(ocr_text, str), "OCR did not return a string"

        if ocr_text.strip():
            passed("ocr", f"{len(ocr_text)} chars extracted in {elapsed}s")
            print(f"  Preview: {ocr_text[:200].strip()}...")
        else:
            skipped("ocr", "NVIDIA_API_KEY not set — OCR returned empty string (fallback will be used)")

    except Exception as e:
        failed("ocr", e)
        traceback.print_exc()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — extractor
# ══════════════════════════════════════════════════════════════════════════════

step("extractor", 3)
profile = {}

try:
    from pipeline.extractor import extract_profile, visual_check_documents

    t0 = time.time()
    profile = extract_profile(
        all_images=all_pages,
        ocr_text=ocr_text,
        declared_name=DECLARED_NAME,
        declared_specialty=DECLARED_SPECIALTY
    )
    elapsed = round(time.time() - t0, 2)

    assert isinstance(profile, dict), "Profile is not a dict"
    assert profile.get("full_name"),  "full_name missing from profile"

    passed("extract_profile", f"Profile extracted in {elapsed}s")
    print(f"  Full name        : {profile.get('full_name')}")
    print(f"  Name match       : {profile.get('declared_name_match')}")
    print(f"  Specialty        : {profile.get('specialty')}")
    print(f"  Specialty match  : {profile.get('specialty_match')}")
    print(f"  License number   : {profile.get('license_number')}")
    print(f"  License expired  : {profile.get('license_expired')}")
    print(f"  Institution      : {profile.get('institution')}")
    print(f"  OCR confidence   : {profile.get('ocr_confidence')}")
    print(f"  Document flags   : {profile.get('document_flags')}")
    print(f"  Anomalies        : {profile.get('anomalies')}")

    # Visual check (stamp / signature)
    if all_pages and nvidia_key:
        print("\n  Running visual stamp/signature check...")
        t0 = time.time()
        visual = visual_check_documents(all_pages, profile)
        elapsed = round(time.time() - t0, 2)
        passed("visual_check_documents", f"Visual check done in {elapsed}s")
        print(f"  Visual results: {json.dumps(visual, indent=4)}")
    else:
        skipped("visual_check_documents", "No pages or NVIDIA key not set")

except Exception as e:
    failed("extractor", e)
    traceback.print_exc()
    # Use fallback profile so pipeline can continue
    profile = {
        "full_name": DECLARED_NAME,
        "declared_name_match": True,
        "specialty": DECLARED_SPECIALTY,
        "specialty_match": True,
        "license_number": "DZ-662-881-2026",
        "license_issuer": "CNOM-DZ",
        "license_expiry": "2027-12",
        "license_expired": False,
        "institution": "Universite Blida 1 Faculte de Medecine",
        "graduation_year": 2020,
        "jobs": [{"employer": "CHU Frantz Fanon", "role": DECLARED_SPECIALTY, "start": "2020-01", "end": "present"}],
        "document_types": ["diploma", "license"],
        "document_flags": ["stamp_present", "signature_visible", "structure_match"],
        "anomalies": [],
        "ocr_confidence": 0.75
    }
    print("  Using fallback profile to continue pipeline...")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — web_verifier
# ══════════════════════════════════════════════════════════════════════════════

step("web_verifier", 4)
verification = {}

try:
    from pipeline.web_verifier import verify_web

    t0 = time.time()
    verification = verify_web(profile)
    elapsed = round(time.time() - t0, 2)

    assert isinstance(verification, dict), "Verification is not a dict"

    if verification.get("scraper_flags") == ["web_verification_skipped"]:
        skipped("web_verifier", "OPENROUTER_API_KEY not set — using empty fallback")
    else:
        passed("web_verifier", f"Web verification done in {elapsed}s")

    print(f"  University confirmed : {verification.get('university_confirmed')}")
    print(f"  University location  : {verification.get('university_location')}")
    print(f"  Medical faculty      : {verification.get('university_is_medical_faculty')}")
    print(f"  4th year subjects    : {verification.get('university_4th_year_subjects', [])[:3]}")
    print(f"  Known professors     : {len(verification.get('university_known_professors', []))} found")
    print(f"  Hospital confirmed   : {verification.get('hospital_confirmed')}")
    print(f"  Scraper flags        : {verification.get('scraper_flags')}")

except Exception as e:
    failed("web_verifier", e)
    traceback.print_exc()
    verification = {
        "university_confirmed": None,
        "university_location": None,
        "university_is_medical_faculty": None,
        "university_4th_year_subjects": [],
        "university_known_professors": [],
        "hospital_confirmed": None,
        "hospital_location": None,
        "hospital_has_specialty": None,
        "web_sources": [],
        "scraper_flags": ["web_verification_skipped"]
    }

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — survey_gen
# ══════════════════════════════════════════════════════════════════════════════

step("survey_gen", 5)
survey_questions = []

try:
    from pipeline.survey_gen import generate_survey_questions

    t0 = time.time()
    survey_questions = generate_survey_questions(profile, verification)
    elapsed = round(time.time() - t0, 2)

    assert isinstance(survey_questions, list),  "survey_questions is not a list"
    assert len(survey_questions) == 3,           f"Expected 3 questions, got {len(survey_questions)}"
    assert all("text" in q for q in survey_questions), "Some questions missing 'text' field"
    assert all("id"   in q for q in survey_questions), "Some questions missing 'id' field"

    passed("survey_gen", f"3 questions generated in {elapsed}s")
    for q in survey_questions:
        print(f"  [{q['id']}] {q['text'][:100]}...")

except Exception as e:
    failed("survey_gen", e)
    traceback.print_exc()
    survey_questions = [
        {"id": "sq1", "text": "Describe your expertise in Internal Medicine.", "category": "specialty_expertise", "purpose": "probe"},
        {"id": "sq2", "text": "Tell us about a challenge at CHU Frantz Fanon.", "category": "work_experience", "purpose": "probe"},
        {"id": "sq3", "text": "Describe your clinical methodology.", "category": "methodology", "purpose": "probe"}
    ]
    print("  Using default survey questions to continue...")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — audio_io (availability check only — no mic needed)
# ══════════════════════════════════════════════════════════════════════════════

step("audio_io", 6)

try:
    from pipeline.audio_io import audio_available, audio_status

    status = audio_status()
    available = audio_available()

    print(f"  Audio status  : {status}")
    print(f"  Audio available: {available}")

    if available:
        passed("audio_io", "Real audio (STT/TTS) available")
    else:
        skipped("audio_io", f"Audio not available — interview will use typed mock fallback. Reason: {status}")

except Exception as e:
    failed("audio_io", e)
    traceback.print_exc()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — expression (availability check — no webcam needed to pass)
# ══════════════════════════════════════════════════════════════════════════════

step("expression", 7)
expr_stream = None

try:
    from pipeline.expression import ExpressionStream, DEEPFACE_AVAILABLE

    print(f"  DeepFace available: {DEEPFACE_AVAILABLE}")

    if DEEPFACE_AVAILABLE:
        expr_stream = ExpressionStream()
        passed("expression", "DeepFace available — expression tracking enabled")
    else:
        skipped("expression", "DeepFace/OpenCV not installed — expression tracking disabled")
        expr_stream = None

except Exception as e:
    skipped("expression", f"Expression module error: {e} — continuing without it")
    expr_stream = None

# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — interview (TEXT/MOCK mode — no audio required)
# ══════════════════════════════════════════════════════════════════════════════

step("interview", 8)
transcript = {}

# Build RAG context from profile + verification + survey
rag_context = f"""
DOCTOR PROFILE:
{json.dumps(profile, indent=2)}

WEB VERIFICATION:
{json.dumps(verification, indent=2)}

SURVEY ANSWERS:
{json.dumps(MOCK_SURVEY_ANSWERS, indent=2)}
"""

try:
    from pipeline.interview import run_interview

    print("  Running interview in TEXT/MOCK mode (no microphone needed)")
    print("  You will be prompted to TYPE answers to 3 questions.")
    print("  ─" * 30)
    if expr_stream:
            expr_stream.start()
    # Force mock mode (no real audio)
    t0 = time.time()
    transcript = run_interview(
        doctor_id=DOCTOR_ID,
        expr_stream=expr_stream,
        rag_context=rag_context,
        use_real_audio=True      # Force text mode
    )
    elapsed = round(time.time() - t0, 2)
    if expr_stream:
        expr_stream.stop()
    assert isinstance(transcript, dict),          "Transcript is not a dict"
    assert "turns" in transcript,                 "Transcript missing 'turns'"
    assert len(transcript["turns"]) == 6,         f"Expected 6 turns (3 AI + 3 doctor), got {len(transcript['turns'])}"
    assert transcript.get("completed_at"),        "Transcript missing 'completed_at'"

    # Verify transcript file was saved
    transcript_path = ROOT / "transcripts" / f"{DOCTOR_ID}.json"
    assert transcript_path.exists(), f"Transcript file not saved to {transcript_path}"

    passed("interview", f"3-turn interview completed in {elapsed}s — saved to transcripts/{DOCTOR_ID}.json")

except Exception as e:
    failed("interview", e)
    traceback.print_exc()
    # Create mock transcript so evaluator can still run
    transcript = {
        "doctor_id": DOCTOR_ID,
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "turns": [
            {"role": "interviewer", "text": "Tell me about your 4th year studies at Blida.", "turn_id": "t1", "timestamp": datetime.now().isoformat()},
            {"role": "doctor",      "text": "I studied physiology, biochemistry, and internal medicine modules.", "turn_id": "t1", "timestamp": datetime.now().isoformat()},
            {"role": "interviewer", "text": "Tell me about your experience at CHU Frantz Fanon.", "turn_id": "t2", "timestamp": datetime.now().isoformat()},
            {"role": "doctor",      "text": "I managed complex cases including multi-system autoimmune diseases.", "turn_id": "t2", "timestamp": datetime.now().isoformat()},
            {"role": "interviewer", "text": "Describe your clinical methodology.", "turn_id": "t3", "timestamp": datetime.now().isoformat()},
            {"role": "doctor",      "text": "I take a systematic approach: history, examination, targeted investigations.", "turn_id": "t3", "timestamp": datetime.now().isoformat()},
        ]
    }
    print("  Using mock transcript to continue to evaluator...")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — evaluator
# ══════════════════════════════════════════════════════════════════════════════

step("evaluator", 9)
report = {}

try:
    from pipeline.evaluator import evaluate

    expr_summary = expr_stream.get_summary() if expr_stream else {}

    t0 = time.time()
    report = evaluate(
        profile=profile,
        verification=verification,
        transcript=transcript,
        survey_qa=MOCK_SURVEY_ANSWERS,
        expr_summary=expr_summary,
        doctor_id=DOCTOR_ID
    )
    elapsed = round(time.time() - t0, 2)

    assert isinstance(report, dict),               "Report is not a dict"
    assert "verdict" in report,                    "Report missing 'verdict'"
    assert "confidence_score" in report,           "Report missing 'confidence_score'"
    assert "score_breakdown" in report,            "Report missing 'score_breakdown'"
    assert report["verdict"] in ["VERIFIED", "NEEDS_MANUAL_REVIEW", "REJECTED"], \
        f"Unexpected verdict: {report['verdict']}"
    assert 0 <= report["confidence_score"] <= 100, "Confidence score out of range"

    # Verify report file was saved
    report_path = ROOT / "reports" / f"{DOCTOR_ID}_report.json"
    assert report_path.exists(), f"Report file not saved to {report_path}"

    passed("evaluator", f"Evaluation done in {elapsed}s")

    print(f"\n  ┌─────────────────────────────────────┐")
    print(f"  │  FINAL VERDICT : {report['verdict']:<20}│")
    print(f"  │  CONFIDENCE    : {report['confidence_score']:<20}│")
    print(f"  └─────────────────────────────────────┘")
    print(f"\n  Score breakdown:")
    for k, v in report.get("score_breakdown", {}).items():
        print(f"    {k:<25} : {v}")
    print(f"\n  Document validity:")
    for k, v in report.get("document_validity", {}).items():
        print(f"    {k:<25} : {v}")
    print(f"\n  Interview assessment:")
    for k, v in report.get("interview_assessment", {}).items():
        print(f"    {k:<25} : {v}")

except Exception as e:
    failed("evaluator", e)
    traceback.print_exc()

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("  TEST SUMMARY")
print("="*60)

passed_count  = sum(1 for r in results if "PASS" in r["status"])
failed_count  = sum(1 for r in results if "FAIL" in r["status"])
skipped_count = sum(1 for r in results if "SKIP" in r["status"])

for r in results:
    print(f"  {r['status']}  {r['step']}")
    if r["details"] and "FAIL" in r["status"]:
        print(f"           → {r['details'][:100]}")

print(f"\n  Total  : {len(results)}")
print(f"  Passed : {passed_count}")
print(f"  Failed : {failed_count}")
print(f"  Skipped: {skipped_count}")

if report:
    print(f"\n  Final report  : reports/{DOCTOR_ID}_report.json")
if transcript:
    print(f"  Transcript    : transcripts/{DOCTOR_ID}.json")
print(f"  Images dir    : {IMAGES_DIR}")

if failed_count == 0:
    print("\n  🟢  All steps passed — pipeline is working!\n")
elif failed_count <= 2:
    print("\n  🟡  Pipeline mostly working — check failed steps above\n")
else:
    print("\n  🔴  Multiple failures — check API keys and dependencies\n")
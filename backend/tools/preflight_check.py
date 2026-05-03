"""
Project preflight check.

Runs non-interactive checks for the local parts of the demo before running the
full API/audio/webcam interview flow.
"""
import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from pipeline.audio_io import audio_status
from pipeline.pdf_to_images import pdf_to_images
from pipeline.rag import get_full_context, ingest


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def check_file(path: str) -> bool:
    if os.path.exists(path):
        ok(f"Found {path}")
        return True
    fail(f"Missing {path}")
    return False


def load_doctor(doctor_dir: str) -> dict:
    info_path = os.path.join(doctor_dir, "info.json")
    with open(info_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_imports() -> bool:
    modules = [
        "fitz",
        "openai",
        "chromadb",
        "sentence_transformers",
        "sounddevice",
        "kokoro_onnx",
        "cv2",
        "deepface",
        "tf_keras",
    ]
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            ok(f"Import {module}")
        except Exception as exc:
            all_ok = False
            fail(f"Import {module}: {type(exc).__name__}: {exc}")
    return all_ok


def check_env() -> None:
    for name in ["NVIDIA_API_KEY", "OPENROUTER_API_KEY"]:
        if os.getenv(name):
            ok(f"{name} is set")
        else:
            warn(f"{name} is not set; external API steps will use fallbacks or fail")


def check_pdf_conversion(data: dict) -> bool:
    doctor_id = data["doctor_id"]
    output_dir = os.path.join("runtime", "preflight_images", doctor_id)
    results = pdf_to_images(data.get("document_paths", []), doctor_id, output_dir)
    pages = [page for doc in results for page in doc.get("pages", [])]
    if pages:
        ok(f"PDF conversion produced {len(pages)} image(s)")
        return True
    fail("PDF conversion produced no images")
    return False


def check_rag(data: dict) -> bool:
    doctor_id = f"preflight_{data['doctor_id']}"
    profile = {
        "full_name": data.get("declared_name"),
        "declared_name_match": True,
        "specialty": data.get("declared_specialty"),
        "specialty_match": True,
        "license_number": "PRE-FLIGHT",
        "license_issuer": "preflight",
        "license_expiry": "2099-12",
        "license_expired": False,
        "institution": data.get("declared_institution"),
        "graduation_year": 2020,
        "jobs": [
            {
                "employer": data.get("declared_employer", "unknown"),
                "role": data.get("declared_specialty", "doctor"),
                "start": "2020-01",
                "end": "present",
            }
        ],
        "document_flags": ["stamp_present", "signature_visible"],
        "anomalies": [],
        "ocr_confidence": 1.0,
    }
    verification = {
        "university_confirmed": True,
        "university_is_medical_faculty": True,
        "hospital_confirmed": True,
        "hospital_has_specialty": True,
        "scraper_flags": [],
    }
    ingest(profile, verification, data.get("survey_qa", []), doctor_id)
    context = get_full_context(doctor_id)
    if context:
        ok(f"RAG context length: {len(context)} characters")
        return True
    fail("RAG context is empty")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local project preflight checks.")
    parser.add_argument("--doctor", default="demo/good_doctor", help="Doctor demo folder.")
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    load_dotenv()
    os.environ.setdefault("DEEPFACE_HOME", str(PROJECT_ROOT / "runtime" / "deepface_home"))
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    print("=" * 70)
    print(" HACKATHON PROJECT PREFLIGHT")
    print("=" * 70)

    check_file("main.py")
    check_file("requirements.txt")
    check_file(os.path.join(args.doctor, "info.json"))

    data = load_doctor(args.doctor)

    print("\n[1] Imports")
    imports_ok = check_imports()

    print("\n[2] Environment")
    check_env()

    print("\n[3] Audio")
    ok(audio_status())

    print("\n[4] PDF Conversion")
    pdf_ok = check_pdf_conversion(data)

    print("\n[5] RAG/ChromaDB")
    rag_ok = check_rag(data)

    print("\n" + "=" * 70)
    if imports_ok and pdf_ok and rag_ok:
        ok("Local preflight passed")
    else:
        fail("Local preflight found issues")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

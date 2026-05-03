"""
Main Orchestrator for Doctor Credential Verification AI Pipeline
Run with: python main.py --doctor demo/good_doctor/
"""
import os
import sys
import json
import argparse
from collections import Counter
from dotenv import load_dotenv
import fitz

# Import pipeline steps
from pipeline.pdf_to_images import pdf_to_images
from pipeline.ocr import run_ocr
from pipeline.extractor import extract_profile, visual_check_documents
from pipeline.web_verifier import verify_web
from pipeline.survey_gen import generate_survey_questions
from pipeline.rag import ingest, get_full_context
from pipeline.interview import run_interview
from pipeline.evaluator import evaluate

def summarize_expression_jsonl(path: str) -> dict:
    if not os.path.exists(path):
        return {}

    turns = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            turn_id = entry.get("turn_id")
            emotion = entry.get("emotion")
            if not turn_id or not emotion:
                continue
            turns.setdefault(turn_id, []).append(emotion)

    summary = {}
    for turn_id, emotions in turns.items():
        counts = Counter(emotions)
        dominant = counts.most_common(1)[0][0]
        stress_count = sum(counts.get(e, 0) for e in ["fear", "angry", "disgust"])
        total = len(emotions)
        summary[turn_id] = {
            "dominant_emotion": dominant,
            "stress_ratio": round(stress_count / total, 3) if total else 0.0,
            "sample_count": total,
        }
    return summary

def load_mock_data(doctor_dir: str) -> dict:
    info_path = os.path.join(doctor_dir, "info.json")
    if not os.path.exists(info_path):
        print(f"ERROR: Could not find {info_path}")
        sys.exit(1)
    with open(info_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_pdf_text_fallback(pdf_paths: list[str]) -> str:
    chunks = []
    for pdf_path in pdf_paths:
        try:
            doc = fitz.open(pdf_path)
            text = "\n".join(page.get_text() for page in doc)
            if text.strip():
                chunks.append(f"--- {os.path.basename(pdf_path)} ---\n{text}")
        except Exception as e:
            print(f"  [local_pdf_text] Failed to read {pdf_path}: {e}")
    return "\n\n".join(chunks)

def run_pipeline(doctor_dir: str, external_expression: bool = False):
    print("="*60)
    print(" AI DOCTOR VERIFICATION PIPELINE ")
    print("="*60)
    
    # 0. Load Data
    data = load_mock_data(doctor_dir)
    doctor_id = data["doctor_id"]
    declared_name = data["declared_name"]
    declared_specialty = data["declared_specialty"]
    pdf_paths = data.get("document_paths", [])
    
    print(f"\nProcessing Doctor: {declared_name} ({doctor_id})")
    
    # 1. PDF to Images
    print("\n[1/9] Converting PDFs to images...")
    images_output_dir = os.path.join("data", "images", doctor_id)
    doc_images = pdf_to_images(pdf_paths, doctor_id, images_output_dir)
    # Flatten image paths for OCR/Extractor
    all_image_paths = []
    for d in doc_images:
        all_image_paths.extend(d["pages"])
        
    # 2. OCR
    print("\n[2/9] Running OCR...")
    ocr_text = run_ocr(all_image_paths)
    if not ocr_text.strip():
        print("  [run_ocr] OCR API returned no text. Using local PDF text fallback.")
        ocr_text = extract_pdf_text_fallback(pdf_paths)
    
    # 3. Vision Extraction
    print("\n[3/9] Extracting structured profile...")
    profile = extract_profile(all_image_paths, ocr_text, declared_name, declared_specialty)

    # 3b. Visual Stamp / Signature Check (per image, vision model)
    print("\n[3b/9] Running visual stamp & signature check on each document image...")
    visual_results = visual_check_documents(all_image_paths, profile)
    
    os.makedirs(os.path.join("data", "profiles"), exist_ok=True)
    with open(os.path.join("data", "profiles", f"{doctor_id}.json"), "w") as f:
        json.dump(profile, f, indent=2)
    if visual_results:
        with open(os.path.join("data", "profiles", f"{doctor_id}_visual.json"), "w") as f:
            json.dump(visual_results, f, indent=2)
    print(f"  [visual] document_flags now: {profile.get('document_flags', [])}")
    print(f"  [visual] anomalies now:      {profile.get('anomalies', [])}")
        
    # 4. Web Verification
    print("\n[4/9] Verifying via web search...")
    verification = verify_web(profile)
    
    # 5. Survey Questions (Mock Text Answers)
    # The pipeline generates questions, but since this is mock data,
    # the doctor has "already" answered them in info.json.
    print("\n[5/9] Fetching pre-answered survey Q&A...")
    survey_qa = data.get("survey_qa", [])
    
    # 6. RAG Ingest
    print("\n[6/9] Ingesting into ChromaDB...")
    ingest(profile, verification, survey_qa, doctor_id)
    rag_context = get_full_context(doctor_id)
    
    # 7. Expression Stream (Background)
    print("\n[7/9] Starting expression stream...")
    expr_stream = None
    if external_expression:
        print("  [expression] External expression monitor mode enabled.")
        print("  [expression] Start run_expression_monitor.cmd in another CMD window.")
    else:
        from pipeline.expression import ExpressionStream
        expr_stream = ExpressionStream()
        expr_stream.start()
    
    # 8. Voice Interview
    print("\n[8/9] Orchestrating voice interview...")
    transcript = run_interview(doctor_id, expr_stream, rag_context)
    
    # Stop Expression Stream
    if expr_stream:
        expr_stream.stop()
        expr_summary = expr_stream.get_summary()
    else:
        expr_summary = summarize_expression_jsonl(os.path.join("runtime", "expression_log.jsonl"))
        print(f"  [expression] Loaded external expression summary: {expr_summary}")
    
    # 9. Final Evaluation
    print("\n[9/9] Evaluating final verdict...")
    report = evaluate(profile, verification, transcript, survey_qa, expr_summary, doctor_id)
    
    # Final Output
    print("\n" + "="*60)
    print(f" FINAL VERDICT: {report['verdict']} ")
    print(f" Confidence Score: {report['confidence_score']}/100")
    print("\n Breakdown:")
    print(f"   - Document Validity: {report['score_breakdown']['document_score']}")
    print(f"   - Interview Consistency: {report['score_breakdown']['interview_score']}")
    print(f"   - Expression Stability: {report['score_breakdown']['expression_score']}")
    print(f"\n Full report saved to: reports/{doctor_id}_report.json")
    print("="*60 + "\n")


if __name__ == "__main__":
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run the AI verification pipeline.")
    parser.add_argument("--doctor", type=str, required=True, help="Path to doctor mock data folder (e.g. demo/good_doctor/)")
    parser.add_argument(
        "--external-expression",
        action="store_true",
        help="Use the separate CMD expression monitor instead of the in-process webcam stream.",
    )
    args = parser.parse_args()
    
    run_pipeline(args.doctor, external_expression=args.external_expression)

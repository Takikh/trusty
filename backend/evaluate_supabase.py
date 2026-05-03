import os
import json
from dotenv import load_dotenv

from pipeline.evaluator import evaluate
from supabase_client import supabase_request, update_doctor_status

load_dotenv()

def fetch_interview_done_doctor():
    res = supabase_request("GET", "doctors?status=eq.interview_done&select=*&limit=1")
    if res and len(res) > 0:
        return res[0]
    return None

def fetch_all_data(doctor_id):
    docs = supabase_request("GET", f"documents_analysis?doctor_id=eq.{doctor_id}&select=*")
    web = supabase_request("GET", f"web_verification?doctor_id=eq.{doctor_id}&select=*")
    interviews = supabase_request("GET", f"interviews?doctor_id=eq.{doctor_id}&select=*")
    
    return (
        docs[0] if docs else {},
        web[0] if web else {},
        interviews[0] if interviews else {}
    )

def run_evaluation_worker():
    print("="*60)
    print(" SUPABASE AI EVALUATION WORKER ")
    print("="*60)
    
    doctor = fetch_interview_done_doctor()
    if not doctor:
        print("No doctors are ready for evaluation right now.")
        return
        
    doc_id = doctor["id"]
    print(f"\n[+] Found doctor ready for evaluation: {doctor['name']} ({doc_id})")
    
    print("[+] Fetching all data streams from Supabase...")
    doc_data, web_data, int_data = fetch_all_data(doc_id)
    
    # Extract pieces needed for evaluator
    profile = doc_data.get("structured_profile", {})
    # Add flags/anomalies back into profile dict for the evaluator logic
    profile["document_flags"] = doc_data.get("document_flags", [])
    profile["anomalies"] = doc_data.get("anomalies", [])
    profile["declared_name_match"] = profile.get("declared_name_match", True)
    
    verification = {
        "university_confirmed": web_data.get("university_confirmed"),
        "hospital_confirmed": web_data.get("hospital_confirmed"),
        "dean_verified": web_data.get("dean_verified")
    }
    
    transcript = {
        "completed_at": int_data.get("completed_at"),
        "turns": int_data.get("transcript_json", [])
    }
    
    survey_qa = int_data.get("survey_qa", [])
    expr_summary = int_data.get("expression_log", {})
    
    print("[+] Running LLM Consistency Checker & Scoring Engine...")
    report = evaluate(profile, verification, transcript, survey_qa, expr_summary, doc_id)
    
    print("\n[+] Saving final verdict to Supabase 'doctors' table...")
    supabase_request("PATCH", f"doctors?id=eq.{doc_id}", {
        "verdict": report["verdict"],
        "final_score": report["confidence_score"] / 100.0, # Store as 0.0 - 1.0 float
        "report_json": report,
        "status": "verdict_ready"
    })
    
    print(f"\n[+] SUCCESS! Final Verdict: {report['verdict']} (Score: {report['confidence_score']}/100)")

if __name__ == "__main__":
    run_evaluation_worker()

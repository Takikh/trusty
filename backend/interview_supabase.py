import os
import json
from dotenv import load_dotenv

# Import the interview module
from pipeline.interview import run_interview
from pipeline.expression import ExpressionStream
from supabase_client import supabase_request, update_doctor_status

load_dotenv()

def fetch_ready_doctor():
    """Finds a doctor with status='ready_for_interview'"""
    res = supabase_request("GET", "doctors?status=eq.ready_for_interview&select=*&limit=1")
    if res and len(res) > 0:
        return res[0]
    return None

def fetch_doctor_context(doctor_id):
    """Gathers the extracted document data and web verification data to feed to the LLM"""
    docs = supabase_request("GET", f"documents_analysis?doctor_id=eq.{doctor_id}&select=*")
    web = supabase_request("GET", f"web_verification?doctor_id=eq.{doctor_id}&select=*")
    
    doc_data = docs[0] if docs else {}
    web_data = web[0] if web else {}
    
    # Construct a comprehensive "Intelligence Report" string for the LLM
    context = f"""
    INTELLIGENCE REPORT:
    --------------------
    DOCUMENT ANALYSIS:
    - Structured Profile: {json.dumps(doc_data.get('structured_profile', {}))}
    - Document Flags: {doc_data.get('document_flags', [])}
    - Anomalies: {doc_data.get('anomalies', [])}
    
    WEB VERIFICATION:
    - University Confirmed: {web_data.get('university_confirmed')}
    - Hospital Confirmed: {web_data.get('hospital_confirmed')}
    - Dean Verified: {web_data.get('dean_verified')}
    - Known Web Sources: {json.dumps(web_data.get('web_sources', []))}
    """
    return context

def run_interview_worker():
    print("="*60)
    print(" SUPABASE AI INTERVIEW WORKER ")
    print("="*60)
    
    doctor = fetch_ready_doctor()
    if not doctor:
        print("No doctors are ready for an interview right now.")
        return
        
    doc_id = doctor["id"]
    print(f"\n[+] Found doctor ready for interview: {doctor['name']} ({doc_id})")
    
    # 1. Gather context from Supabase
    print("[+] Fetching intelligence report from Supabase...")
    rag_context = fetch_doctor_context(doc_id)
    
    # 2. Run the Interview!
    # For now, we set use_real_audio=False so you can type the answers in the terminal
    # instead of needing a microphone setup.
    print("[+] Starting conversational agent with Emotion Tracking...")
    
    expr = ExpressionStream()
    expr.start()
    
    try:
        transcript = run_interview(
            doctor_id=doc_id, 
            expr_stream=expr, 
            rag_context=rag_context,
            use_real_audio=True 
        )
    finally:
        expr.stop()
    
    # 3. Save transcript to Supabase
    print("\n[+] Saving interview transcript to Supabase 'interviews' table...")
    supabase_request("POST", "interviews", {
        "doctor_id": doc_id,
        "started_at": transcript["started_at"],
        "completed_at": transcript["completed_at"],
        "transcript_json": transcript["turns"],
        "expression_log": expr.get_summary()
    })
    
    # 4. Update status
    update_doctor_status(doc_id, "interview_done")
    print("\n[+] SUCCESS! Interview complete and logged.")
    print("    Ready for final evaluation!")

if __name__ == "__main__":
    run_interview_worker()

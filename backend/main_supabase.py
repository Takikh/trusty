import os
import json
import urllib.request
import urllib.error
import argparse
from dotenv import load_dotenv

# Import pipeline steps
from pipeline.pdf_to_images import pdf_to_images
from pipeline.ocr import run_ocr
from pipeline.extractor import extract_profile
from pipeline.web_verifier import verify_web

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def supabase_request(method, endpoint, data=None):
    """Helper to make HTTP requests to Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status in (200, 201):
                res_body = response.read()
                return json.loads(res_body) if res_body else None
    except urllib.error.HTTPError as e:
        print(f"Supabase API Error ({method} {endpoint}): {e.code} - {e.read().decode('utf-8')}")
        raise e
    except Exception as e:
        print(f"Request Error: {e}")
        raise e

def download_file_from_storage(bucket, file_path, download_dest):
    """Downloads a file from Supabase Storage"""
    url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"
    print(f"Downloading {url} to {download_dest}")
    try:
        urllib.request.urlretrieve(url, download_dest)
        return True
    except Exception as e:
        print(f"Failed to download {file_path}: {e}")
        return False

def fetch_pending_doctor():
    """Finds a doctor with status='pending'"""
    res = supabase_request("GET", "doctors?status=eq.pending&select=*&limit=1")
    if res and len(res) > 0:
        return res[0]
    return None

def update_doctor_status(doctor_id, new_status):
    """Updates the status column for a doctor"""
    print(f"Updating doctor {doctor_id} status to '{new_status}'...")
    supabase_request("PATCH", f"doctors?id=eq.{doctor_id}", {"status": new_status})

def save_document_analysis(doctor_id, ocr_text, profile, flags, anomalies, confidence):
    """Saves the pipeline A and B results to Supabase"""
    data = {
        "doctor_id": doctor_id,
        "ocr_text": ocr_text,
        "structured_profile": profile,
        "document_flags": flags,
        "anomalies": anomalies,
        "ocr_confidence": confidence
    }
    supabase_request("POST", "documents_analysis", data)

def run_supabase_pipeline():
    print("="*60)
    print(" SUPABASE AI WORKER POLLING FOR JOBS ")
    print("="*60)
    
    doctor = fetch_pending_doctor()
    if not doctor:
        print("No pending doctors found in Supabase. Waiting...")
        return
        
    doc_id = doctor["id"]
    print(f"\n[+] Found pending doctor: {doctor['name']} ({doc_id})")
    
    # 1. Claim the job so other workers don't grab it
    update_doctor_status(doc_id, "processing_a")
    
    # 2. Download their documents
    os.makedirs(f"data/downloads/{doc_id}", exist_ok=True)
    local_pdf_paths = []
    
    for doc_path in doctor.get("document_paths", []):
        # Use the actual saved local path (api_server saves uploads to data/downloads/)
        if os.path.isfile(doc_path):
            local_pdf_paths.append(doc_path)
            print(f"Using uploaded document: {doc_path}")
        else:
            # Fallback: try relative path inside data/downloads/
            local_path = f"data/downloads/{doc_id}/{os.path.basename(doc_path)}"
            if os.path.isfile(local_path):
                local_pdf_paths.append(local_path)
                print(f"Found document at: {local_path}")
            else:
                print(f"WARNING: Document not found at '{doc_path}' or '{local_path}', skipping.")
            
    if not local_pdf_paths:
        print("[-] No valid documents found to process. Failing job.")
        update_doctor_status(doc_id, "failed")
        return
        
    print("\n[+] 1/4 Converting PDFs to images...")
    images_output_dir = os.path.join("data", "images", doc_id)
    doc_images = pdf_to_images(local_pdf_paths, doc_id, images_output_dir)
    
    all_image_paths = []
    for d in doc_images:
        all_image_paths.extend(d["pages"])
        
    print("\n[+] 2/4 Running OCR...")
    ocr_text = run_ocr(all_image_paths)
    
    print("\n[+] 3/4 Extracting structured profile...")
    declared_name = doctor.get("name", "")
    declared_specialty = doctor.get("specialty", "")
    profile = extract_profile(all_image_paths, ocr_text, declared_name, declared_specialty)
    
    flags = profile.get("document_flags", [])
    anomalies = profile.get("anomalies", [])
    confidence = profile.get("ocr_confidence", 1.0)
    
    print("\n[+] Saving extraction results to Supabase documents_analysis...")
    save_document_analysis(doc_id, ocr_text, profile, flags, anomalies, confidence)
    
    print("\n[+] 4/4 Verifying via web search...")
    verification = verify_web(profile)
    
    print("\n[+] Saving verification results to Supabase web_verification...")
    supabase_request("POST", "web_verification", {
        "doctor_id": doc_id,
        "university_confirmed": verification.get("university_confirmed"),
        "university_location": verification.get("university_location"),
        "university_is_medical_faculty": verification.get("university_is_medical_faculty"),
        "university_4th_year_subjects": verification.get("university_4th_year_subjects", []),
        "university_known_professors": verification.get("university_known_professors", []),
        "hospital_confirmed": verification.get("hospital_confirmed"),
        "hospital_location": verification.get("hospital_location"),
        "hospital_has_specialty": verification.get("hospital_has_specialty"),
        "web_sources": verification.get("web_sources", []),
        "scraper_flags": verification.get("scraper_flags", []),
    })

    # Mark ready for interview
    update_doctor_status(doc_id, "ready_for_interview")
    print(f"\n[+] SUCCESS! Doctor {doctor.get('name', 'N/A')} is ready for interview.")
    print(f"    Interview Token: {doctor.get('interview_token', 'N/A')}")
    
    # Trigger Email
    try:
        from mailer import send_interview_email
        # We use the requested email to demonstrate SMTP, or fallback to the doctor's email.
        send_interview_email(doc_id, to_email="yassine.alikacem@gmail.com")
    except Exception as e:
        print(f"[-] Could not send interview email: {e}")

if __name__ == "__main__":
    run_supabase_pipeline()

import os
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

def upload_file(local_path, remote_name):
    print(f"Uploading {local_path} to storage...")
    url = f"{SUPABASE_URL}/storage/v1/object/documents/{remote_name}"
    
    with open(local_path, "rb") as f:
        data = f.read()
        
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    req.add_header("Content-Type", "application/pdf")
    
    try:
        with urllib.request.urlopen(req) as res:
            print(f"Upload successful: {res.status}")
    except urllib.error.HTTPError as e:
        # Ignore 400s if it already exists
        print(f"Upload returned {e.code}: {e.read().decode('utf-8')}")

def seed_doctor():
    print("Inserting test doctor...")
    url = f"{SUPABASE_URL}/rest/v1/doctors"
    data = {
        "name": "Dr. Sarah Jenkins",
        "email": "sarah@example.com",
        "specialty": "Cardiology",
        "declared_univ": "Harvard University",
        "document_paths": ["test_diploma.pdf"],
        "status": "pending"
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), method="POST")
    req.add_header("apikey", SUPABASE_KEY)
    req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "return=representation")
    
    try:
        with urllib.request.urlopen(req) as res:
            print(f"Inserted doctor successfully!")
            print(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Insert failed {e.code}: {e.read().decode('utf-8')}")

if __name__ == "__main__":
    upload_file("demo/good_doctor/documents/diploma.pdf", "test_diploma.pdf")
    seed_doctor()

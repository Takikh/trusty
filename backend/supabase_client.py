import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

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

def update_doctor_status(doctor_id, new_status):
    """Updates the status column for a doctor"""
    print(f"Updating doctor {doctor_id} status to '{new_status}'...")
    supabase_request("PATCH", f"doctors?id=eq.{doctor_id}", {"status": new_status})

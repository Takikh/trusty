import os
import json
import base64
import tempfile
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import uuid
import shutil
import urllib.request
from dotenv import load_dotenv

load_dotenv()

from supabase_client import supabase_request, update_doctor_status
from pipeline.interview import fallback_interview_question
from pipeline.rag import get_full_context as rag_get_full_context
from openai import AsyncOpenAI
import asyncio
from faster_whisper import WhisperModel

import imageio_ffmpeg
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

print("Loading Whisper Model...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

try:
    from deepface import DeepFace
    HAS_DEEPFACE = True
except ImportError:
    print("Warning: DeepFace not installed. Mocking emotion data.")
    HAS_DEEPFACE = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload_document(
    name: str = Form(...),
    email: str = Form(...),
    diploma: UploadFile = File(...)
):
    # Generate unique doctor ID
    doctor_id = str(uuid.uuid4())
    
    # Save the file locally to bypass Supabase Storage issues
    dest_dir = f"data/downloads/{doctor_id}"
    os.makedirs(dest_dir, exist_ok=True)
    local_path = os.path.join(dest_dir, diploma.filename)
    
    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(diploma.file, buffer)
        
    print(f"Saved uploaded file to {local_path}")
    
    # Insert into Supabase
    data = {
        "id": doctor_id,
        "name": name,
        "email": email,
        "specialty": "General",
        "declared_univ": "Unknown",
        "document_paths": [local_path], # main_supabase.py will check if file exists
        "status": "pending"
    }
    
    # Use headers without Bearer for apikey
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    req = urllib.request.Request(
        f"{os.getenv('SUPABASE_URL')}/rest/v1/doctors",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        method="POST"
    )
    
    try:
        urllib.request.urlopen(req)
        print("Successfully seeded doctor into Supabase!")
        return {"status": "success", "doctor_id": doctor_id}
    except Exception as e:
        print(f"Error seeding Supabase: {e}")
        return {"status": "error", "message": str(e)}

def fetch_doctor_context(doctor_id):
    """Build full intelligence brief from Supabase + ChromaDB RAG."""
    docs = supabase_request("GET", f"documents_analysis?doctor_id=eq.{doctor_id}&select=*")
    web  = supabase_request("GET", f"web_verification?doctor_id=eq.{doctor_id}&select=*")
    doc_data = docs[0] if docs else {}
    web_data = web[0] if web else {}

    profile   = doc_data.get("structured_profile", {}) or {}
    flags     = doc_data.get("document_flags", []) or []
    anomalies = doc_data.get("anomalies", []) or []

    # Pull rich data from ChromaDB RAG (always has professors/curriculum from simulation)
    try:
        rag_text = rag_get_full_context(doctor_id)
    except Exception:
        rag_text = ""

    # Parse professors from RAG text if Supabase doesn't have extended columns yet
    professors = web_data.get("university_known_professors", []) or []
    subjects   = web_data.get("university_4th_year_subjects", []) or []

    # Extract professors section from RAG text if not in Supabase
    if not professors and "Known professors" in rag_text:
        start = rag_text.find("Known professors")
        end   = rag_text.find("\n\n", start)
        prof_lines = rag_text[start:end].strip() if end != -1 else rag_text[start:].strip()
    elif professors:
        prof_lines = "\n".join(
            f"  - {p.get('name','?')}: {p.get('role','?')}, Dept of {p.get('department','?')} (confidence: {p.get('confidence','?')})"
            for p in professors
        )
    else:
        prof_lines = "  - None found"

    # Extract curriculum from RAG text if not in Supabase
    if not subjects and "4th-year medicine curriculum" in rag_text:
        start = rag_text.find("4th-year medicine curriculum")
        end   = rag_text.find("\n\n", start)
        curriculum = rag_text[start:end].strip() if end != -1 else rag_text[start:].strip()
    elif subjects:
        curriculum = "\n".join(f"  - {s}" for s in subjects)
    else:
        curriculum = "  - Not available"

    # Flags/anomalies
    all_flags = flags + anomalies + (web_data.get("scraper_flags", []) or [])
    flags_str = "\n".join(f"  ⚠ {f}" for f in all_flags) if all_flags else "  - None detected"

    # Work history
    jobs = profile.get("jobs", []) or []
    jobs_str = "\n".join(
        f"  - {j.get('role','?')} at {j.get('employer','?')} ({j.get('start','?')} → {j.get('end','?')})"
        for j in jobs
    ) or "  - Not provided"

    return f"""╔══════════════════════════════════════════════════════════╗
║         CONFIDENTIAL INTELLIGENCE BRIEF                 ║
╚══════════════════════════════════════════════════════════╝

IDENTITY:
  Full name on document : {profile.get('full_name', 'Unknown')}
  Declared specialty    : {profile.get('specialty', 'Unknown')}
  Specialty match       : {profile.get('specialty_match', 'Unknown')}
  Name match            : {profile.get('declared_name_match', 'Unknown')}
  License number        : {profile.get('license_number', 'None')}
  License expiry        : {profile.get('license_expiry', 'Unknown')}

EDUCATION:
  Institution           : {profile.get('institution', 'Unknown')}
  Graduation year       : {profile.get('graduation_year', 'Unknown')}
  University confirmed  : {web_data.get('university_confirmed', 'Unknown')}
  University location   : {web_data.get('university_location', 'Unknown')}

{prof_lines}

{curriculum}

EMPLOYMENT:
{jobs_str}
  Hospital confirmed    : {web_data.get('hospital_confirmed', 'Unknown')}
  Hospital location     : {web_data.get('hospital_location', 'Unknown')}

FLAGS & ANOMALIES:
{flags_str}
"""


async def generate_and_send_tts(websocket: WebSocket, text: str):
    """Generate TTS audio and send it via WebSocket."""
    print(f"[TTS] Generating audio for: {text}", flush=True)
    import soundfile as sf
    from kokoro_onnx import Kokoro
    
    try:
        # Load kokoro ONNX model
        kokoro = Kokoro("audio/tts_kokoro/kokoro-v1.0.onnx", "audio/tts_kokoro/voices-v1.0.bin")
        samples, sample_rate = kokoro.create(text, voice="af_heart", speed=1.0, lang="en-us")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, samples, sample_rate)
            f.close()
            with open(f.name, "rb") as wav_file:
                wav_data = wav_file.read()
            os.unlink(f.name)
            
        await websocket.send_bytes(wav_data)
        await websocket.send_text(json.dumps({"type": "status", "message": "done_speaking"}))
    except Exception as e:
        print(f"TTS Error: {e}")
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))

@app.websocket("/ws/interview/{doctor_id}")
async def websocket_interview(websocket: WebSocket, doctor_id: str):
    await websocket.accept()
    print(f"Client connected for doctor: {doctor_id}")
    
    try:
        # Wait for the client to say "START"
        msg = await websocket.receive_text()
        
        # Fetch Context
        await websocket.send_text(json.dumps({"type": "status", "message": "Fetching intelligence report..."}))
        rag_context = fetch_doctor_context(doctor_id)
        
        api_key = os.getenv("NVIDIA_API_KEY")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        client = AsyncOpenAI(base_url=base_url, api_key=api_key) if api_key else None
        
        transcript = {
            "doctor_id": doctor_id,
            "started_at": datetime.now().isoformat(),
            "turns": []
        }
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a forensic medical credential verification officer. You have an INTELLIGENCE REPORT on this doctor.
Your mission: conduct a 7-turn interview asking questions that ONLY a real doctor with genuine credentials can answer correctly.

QUESTION DESIGN RULES — READ CAREFULLY:
1. NEVER embed the answer in your question. Do NOT say "Is your name X?", "Did you go to Y?", "Is your specialty Z?"
2. Each question forces the doctor to VOLUNTEER specific facts you silently verify against the report.
3. Ask exactly ONE question per turn. Keep it SHORT: 1-2 sentences max.
4. Do NOT reveal what the intelligence report says. Ever.

TURN-BY-TURN PLAN:
- Turn 1 (IDENTITY)     : Ask them to state their full legal name and current medical specialty.
- Turn 2 (LICENSE)      : Ask them to provide their medical license number and the issuing authority.
- Turn 3 (EDUCATION)    : Ask them to name the university and faculty where they completed their medical degree, and the year of graduation.
- Turn 4 (PROFESSOR)    : The report lists real professors at their university. Ask the doctor to name ONE professor or department head they remember from their faculty — without naming any yourself.
- Turn 5 (CURRICULUM)   : Ask them to list at least 3 subjects or clinical rotations they studied in their final year of medical school.
- Turn 6 (CLINICAL SCENARIO 1) : Present a realistic emergency or diagnostic scenario relevant to their declared specialty. The scenario must require specific medical knowledge only a trained specialist in that field would have. Example for Neurology: "A 67-year-old patient presents with sudden onset of left-sided weakness and slurred speech, symptoms started 90 minutes ago — walk me through your immediate management." Tailor the scenario to the INTELLIGENCE REPORT's declared specialty. Do NOT give away the answer or hint at the expected steps.
- Turn 7 (CLINICAL SCENARIO 2) : Present a second, different clinical scenario or a follow-up complication from Turn 6. This should test deeper knowledge, such as a complication management, a differential diagnosis, or a decision-making moment. Example: "The patient's CT shows no hemorrhage. What is your next step and what are the contraindications you must check before proceeding?" Again, tailor to the doctor's specialty from the report.

After each answer, silently compare what the doctor said to the intelligence report. Do NOT comment on whether their answer was correct or wrong.

INTELLIGENCE REPORT (STRICTLY CONFIDENTIAL — DO NOT SHARE WITH DOCTOR):
{rag_context}"""
            },
            {
                "role": "user",
                "content": "I am ready for the interview."
            }
        ]
        
        turn_mappings = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
        expression_log = {}
        
        # Define local robust fallbacks directly here
        def robust_fallback(t_id, context):
            fallbacks = {
                "t1": "Can you please state your full legal name and the medical specialty you currently practice?",
                "t2": "Thank you. Could you provide your medical license number and the authority that issued it?",
                "t3": "Where did you complete your medical education, and what year did you graduate?",
                "t4": "Could you name one professor or department head you remember from your time at the medical faculty?",
                "t5": "Please list a few of the core subjects or clinical rotations you completed during your final year of medical school.",
                "t6": "Describe your current clinical role, the name of your hospital, and your main daily responsibilities.",
                "t7": "Finally, could you describe a complex clinical scenario you recently managed in your specialty, and the diagnostic steps you took?"
            }
            return fallbacks.get(t_id, "Could you elaborate on your last point?")
        
        for turn_id in turn_mappings:
            await websocket.send_text(json.dumps({"type": "status", "message": f"Generating question for {turn_id}..."}))
            
            # Generate AI Question
            ai_text = None
            
            # Tell the LLM which turn we are currently on
            turn_msg = {"role": "system", "content": f"We are now on {turn_id.upper()}. Generate the question for this turn based on the TURN-BY-TURN PLAN."}
            current_messages = messages + [turn_msg]

            if client:
                try:
                    response = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=os.getenv("NVIDIA_INTERVIEW_MODEL", "meta/llama-3.3-70b-instruct"),
                            messages=current_messages,
                            max_tokens=150,
                            temperature=0.7
                        ),
                        timeout=15.0  # Prevent hanging if API is slow
                    )
                    ai_text = response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"[!] NVIDIA API Error or Timeout: {e}. Using fallback.")
            
            if not ai_text:
                ai_text = robust_fallback(turn_id, rag_context)
            
            messages.append({"role": "assistant", "content": ai_text})
            transcript["turns"].append({"role": "interviewer", "text": ai_text, "turn_id": turn_id})
            
            # Send question text to chat UI first, then TTS audio
            await websocket.send_text(json.dumps({"type": "question", "text": ai_text}))
            await generate_and_send_tts(websocket, ai_text)
            
            # Enable the text input on frontend
            await websocket.send_text(json.dumps({"type": "status", "message": "listening"}))
            
            # Wait for typed answer; also collect expression samples in background
            doctor_audio_text = ""
            while True:
                data = await websocket.receive()
                if "bytes" in data:
                    continue  # ignore stray binary
                elif "text" in data:
                    msg = json.loads(data["text"])

                    # Accumulate expression samples
                    if msg.get("type") == "expression":
                        t = msg.get("turn_id")
                        e = msg.get("emotion", "neutral")
                        if t:
                            expression_log.setdefault(t, []).append(e)
                        continue
                    
                    # Accept typed answer from the text input
                    if msg.get("type") == "answer":
                        doctor_audio_text = msg.get("text", "").strip()
                        print(f"Doctor answered: '{doctor_audio_text}'", flush=True)
                        
                        if not doctor_audio_text:
                            retry_text = "Please type your answer to continue."
                            await websocket.send_text(json.dumps({"type": "question", "text": retry_text}))
                            await generate_and_send_tts(websocket, retry_text)
                            await websocket.send_text(json.dumps({"type": "status", "message": "listening"}))
                            continue
                        
                        break
                    # Ignore anything else
            
            messages.append({"role": "user", "content": doctor_audio_text})
            transcript["turns"].append({"role": "doctor", "text": doctor_audio_text, "turn_id": turn_id})

        # Build expression summary
        from collections import Counter
        expr_summary = {}
        for t, emotions in expression_log.items():
            counts = Counter(emotions)
            dominant = counts.most_common(1)[0][0]
            stress = sum(counts.get(e, 0) for e in ["fearful", "angry", "disgusted"])
            total = len(emotions)
            expr_summary[t] = {
                "sample_count": total,
                "stress_ratio": round(stress / total, 3) if total else 0.0,
                "dominant_emotion": dominant,
            }
        
        print("\n=== EXPRESSION LOG ===", flush=True)
        print(json.dumps(expr_summary, indent=2), flush=True)
        print("=====================\n", flush=True)

        # Wrap up
        transcript["completed_at"] = datetime.now().isoformat()
        await websocket.send_text(json.dumps({"type": "status", "message": "interview_complete"}))
        
        # Save transcript to Supabase
        print("Saving to Supabase...")
        supabase_request("POST", "interviews", {
            "doctor_id": doctor_id,
            "started_at": transcript["started_at"],
            "completed_at": transcript["completed_at"],
            "transcript_json": transcript["turns"],
            "expression_log": expression_log
        })
        update_doctor_status(doctor_id, "interview_done")
        await websocket.close()
        
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        import traceback
        print(f"Error: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8001, reload=True)

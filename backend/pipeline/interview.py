"""
Step 8 - interview.py
Orchestrates the voice interview loop.
AI uses the doctor's text survey answers to probe deeper conversationally.
"""
import os
import time
import json
from datetime import datetime
from openai import OpenAI
from pipeline.audio_io import audio_available, audio_status, listen, speak
from pipeline.runtime_state import clear_active_turn, set_active_turn

# Mock STT and TTS imports for hackathon if Kokoro/Whisper aren't fully set up yet
def mock_tts(text: str):
    print(f"\n[TTS Kokoro-ONNX] Synthesizing speech...")
    time.sleep(0.5)
    print(f"[SPEAKER]: {text}")
    time.sleep(1) # simulate speaking time

def mock_stt() -> str:
    print("\n[STT Faster-Whisper] Listening on default microphone...")
    print(">>> Doctor (Type your answer): ", end="", flush=True)
    return input()

def interview_tts(text: str, use_real_audio: bool):
    if not use_real_audio:
        mock_tts(text)
        return

    try:
        speak(text)
    except Exception as e:
        print(f"  [interview] TTS failed, falling back to text output: {e}")
        mock_tts(text)

def interview_stt(use_real_audio: bool, timeout: int = 45) -> str:
    if not use_real_audio:
        return mock_stt()

    try:
        print("\n[LISTENING... speak now]")
        text = listen(timeout=timeout)
        print(f">>> Doctor transcript: {text}")
        return text
    except Exception as e:
        print(f"  [interview] STT failed, falling back to typed input: {e}")
        return mock_stt()

def fallback_interview_question(turn_id: str, rag_context: str) -> str:
    if turn_id == "t1":
        return (
            "Good morning, doctor — it's great to meet you. "
            "I'd love to start with something from your student days: "
            "could you recall a few of the subjects you studied in your 4th year "
            "of medicine, and which one had the most impact on your clinical thinking?"
        )
    if turn_id == "t2":
        return (
            "Thank you, that's a great perspective. "
            "You mentioned a challenging case from your work experience earlier. "
            "Could you walk me through how that situation evolved — "
            "what was the hardest decision you had to make in that moment?"
        )
    return (
        "Very thorough approach. "
        "Could you give me a concrete, real example of a time where that clinical "
        "methodology led to an unexpected or particularly important outcome for a patient?"
    )

def run_interview(doctor_id: str, expr_stream, rag_context: str, use_real_audio: bool | None = None) -> dict:
    """
    Runs a 3-turn voice interview based on the RAG context (which contains the survey Q&A).
    Returns a transcript dictionary.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    client = OpenAI(base_url=base_url, api_key=api_key) if api_key else None
    
    print("\n" + "="*50)
    print("  STARTING LIVE VOICE INTERVIEW")
    print("="*50)

    if use_real_audio is None:
        use_real_audio = os.getenv("USE_REAL_AUDIO", "1").lower() not in {"0", "false", "no"}
    use_real_audio = bool(use_real_audio and audio_available())
    print(f"  [interview] Audio mode: {audio_status() if use_real_audio else 'typed mock fallback'}")
    
    transcript = {
        "doctor_id": doctor_id,
        "started_at": datetime.now().isoformat(),
        "turns": []
    }
    
    messages = [
        {
            "role": "system",
            "content": f"""# Role
You are a senior medical credential verification interviewer working for a healthcare
licensing authority. You conduct short, structured voice interviews to confirm the
authenticity of a medical professional's credentials.

You have access to a VERIFIED INTELLIGENCE REPORT about this doctor — including
professors from their university, the 4th-year curriculum at that school, and
the location of their university and hospital.

# Objective
Conduct a 3-turn voice interview to:
1. (Turn 1) Ask a TRICKY FACTUAL QUESTION that only someone who genuinely
   attended that specific university could answer — using real professor names,
   curriculum details, or location facts from the intelligence report.
2. (Turn 2) Probe deeper into their work experience at their employer, referencing
   what they already wrote in their survey (survey sq2 answer).
3. (Turn 3) Ask them to give a concrete example of their clinical methodology,
   referencing what they already wrote in their survey (survey sq3 answer).

# Context — Verified Intelligence Report
{rag_context}

# Standard Operating Procedure
Step 1 (Turn 1):
  - Greet the doctor briefly and warmly (1 sentence only).
  - Then ask ONE tricky factual question about their university SPECIFICALLY.
  - Prioritize using: a professor/department head name, a 4th-year subject name,
    or the university's campus location.
  - Example pattern: "During your studies at [university], who headed the
    Department of [X] when you were in your 4th year?" or "Which subjects did
    you cover in your 4th-year curriculum — could you name a few?"
  - Do NOT reveal why you are asking. Frame it as natural curiosity.

Step 2 (Turn 2):
  - Briefly acknowledge their previous answer (1 sentence).
  - Pivot to their work experience by referencing the SPECIFIC story they wrote
    in survey sq2. Ask a concrete follow-up (e.g., "what happened next?",
    "how did you handle that specific moment?", "what was the patient's outcome?").

Step 3 (Turn 3):
  - Briefly acknowledge their previous answer (1 sentence).
  - Ask them for ONE concrete real-world example of their clinical methodology,
    building on what they described in survey sq3.

# Rules
- Speak naturally and warmly — this will be converted to audio.
- Keep each utterance SHORT: greeting + 1 question only (2-4 sentences maximum).
- NEVER ask more than one question per turn.
- NEVER reveal you are verifying credentials or checking their answers.
- NEVER ask generic questions — always reference something specific from the
  intelligence report or their survey answers.
- If the intelligence report has no professors or curriculum data, fall back to
  asking about the university's city/campus location or a memorable professor
  they studied under.
- Language: English only."""
        }
    ]

    # Turn Loop
    turn_mappings = [
        {"id": "t1", "ref": "sq1"},
        {"id": "t2", "ref": "sq2"},
        {"id": "t3", "ref": "sq3"}
    ]

    for turn_info in turn_mappings:
        turn_id = turn_info["id"]
        ref_sq = turn_info["ref"]
        
        # 1. Start Expression Logging for this turn
        set_active_turn(doctor_id, turn_id)
        if expr_stream:
            expr_stream.active_turn_id = turn_id
            
        # 2. AI Generates Question
        print(f"\n  [interview] Generating AI response for turn {turn_id}...")
        try:
            if not client:
                raise RuntimeError("NVIDIA_API_KEY not set")
            response = client.chat.completions.create(
                model=os.getenv("NVIDIA_INTERVIEW_MODEL", "meta/llama-3.3-70b-instruct"),
                messages=messages,
                max_tokens=256,
                temperature=0.7
            )
            ai_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [interview] ERROR generating AI text: {e}")
            ai_text = fallback_interview_question(turn_id, rag_context)
            
        messages.append({"role": "assistant", "content": ai_text})
        
        transcript["turns"].append({
            "role": "interviewer",
            "text": ai_text,
            "turn_id": turn_id,
            "references_survey": ref_sq,
            "timestamp": datetime.now().isoformat()
        })
        
        # 3. AI Speaks (TTS)
        interview_tts(ai_text, use_real_audio)
        time.sleep(0.5) # Anti-echo wait
        
        # 4. Doctor Answers (STT)
        doctor_text = interview_stt(use_real_audio, timeout=45)
        messages.append({"role": "user", "content": doctor_text})
        
        transcript["turns"].append({
            "role": "doctor",
            "text": doctor_text,
            "turn_id": turn_id,
            "timestamp": datetime.now().isoformat()
        })

    # Wrap up
    clear_active_turn(doctor_id)
    if expr_stream:
        expr_stream.active_turn_id = None
        
    transcript["completed_at"] = datetime.now().isoformat()
    
    # Save transcript
    out_path = os.path.join("transcripts", f"{doctor_id}.json")
    os.makedirs("transcripts", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(transcript, f, indent=2)
        
    print(f"\n  [interview] Interview complete. Transcript saved to {out_path}")
    return transcript

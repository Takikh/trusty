"""
Step 5 - survey_gen.py
Generates 3 open-ended text survey questions from the doctor's profile.
These are answered in TEXT during registration — not voice.
The voice interview will later probe those answers.
"""
import json
import os
import re
from openai import OpenAI


def _parse_json_response(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


def generate_survey_questions(profile: dict, verification: dict) -> list:
    """
    Returns a list of 3 survey question dicts:
    [{"id":"sq1","text":"...","category":"...","purpose":"..."}]
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    specialty  = profile.get("specialty") or "Medicine"
    employer   = (profile.get("jobs") or [{}])[0].get("employer") or "their workplace"
    name       = profile.get("full_name") or "the doctor"

    if not api_key:
        print("  [survey_gen] WARNING: NVIDIA_API_KEY not set. Returning defaults.")
        return _default_questions(specialty, employer)

    client = OpenAI(base_url=base_url, api_key=api_key)

    prompt = f"""You are designing a credential verification survey for a medical platform.
A doctor has just registered with the following profile:

Name: {name}
Specialty: {specialty}
Employer: {employer}

Generate exactly 3 open-ended survey questions to present to this doctor during registration.
They will answer IN TEXT. The questions should:
- Q1 (specialty_expertise): Ask them to describe their main area of expertise and daily focus WITHIN their specialty. Must be open and descriptive.
- Q2 (work_experience): Reference their specific employer "{employer}". Ask for a real story or challenge they faced there.
- Q3 (methodology): Ask about their clinical approach or methodology when facing a complex case in {specialty}.

Rules:
- All questions must be answerable by any real {specialty} doctor
- Do NOT ask trick or trick questions — just open, professional questions
- Keep each question to 1-2 sentences maximum
- English only

Return ONLY a JSON array (no markdown):
[
  {{"id": "sq1", "text": "...", "category": "specialty_expertise", "purpose": "..."}},
  {{"id": "sq2", "text": "...", "category": "work_experience", "purpose": "..."}},
  {{"id": "sq3", "text": "...", "category": "methodology", "purpose": "..."}}
]"""

    print("  [survey_gen] Generating survey questions ...")
    try:
        response = client.chat.completions.create(
            model=os.getenv("NVIDIA_SURVEY_MODEL", "meta/llama-3.3-70b-instruct"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.5
        )
        raw = response.choices[0].message.content
        print(f"  [survey_gen] Raw response (first 200 chars): {raw[:200]}")
        result = _parse_json_response(raw)

        if not result or len(result) < 3:
            print("  [survey_gen] WARNING: Could not parse questions. Using defaults.")
            return _default_questions(specialty, employer)

        return result[:3]

    except Exception as e:
        print(f"  [survey_gen] ERROR: {e}")
        return _default_questions(specialty, employer)


def _default_questions(specialty: str, employer: str) -> list:
    return [
        {
            "id": "sq1",
            "text": f"Describe your main area of expertise within {specialty} and what you focus on most in your daily practice.",
            "category": "specialty_expertise",
            "purpose": "Self-description of expertise to probe during voice interview"
        },
        {
            "id": "sq2",
            "text": f"During your time at {employer}, what was a challenging case that shaped your approach to patient care?",
            "category": "work_experience",
            "purpose": "A specific work story to follow up on during voice interview"
        },
        {
            "id": "sq3",
            "text": f"How would you describe your clinical methodology when a patient presents with a complex {specialty} condition?",
            "category": "methodology",
            "purpose": "Process description to probe consistency in voice interview"
        }
    ]

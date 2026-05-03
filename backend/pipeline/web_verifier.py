"""
Step 4 - web_verifier.py
Agent: Perplexity Sonar (live web search via OpenRouter)

Searches for:
  1. University existence + location + medical faculty
  2. 4th-year curriculum (subjects/modules taught in Year 4 of Medicine)
  3. Known professors/department heads at that faculty
  4. Employer/hospital existence + specialty department
  5. Any red flags or contradictions

Returns all findings as structured JSON for RAG storage + interview question generation.
"""
import json
import os
import re
from openai import OpenAI


def _parse_json_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
# Role
You are a specialized medical credential research agent with access to live web search.
Your mission is to gather factual, verifiable intelligence about a medical professional's
claimed educational background and work history.

# Objective
Given a doctor's profile, search the web deeply to produce a structured intelligence
report that will be used to:
  1. Confirm whether the university and hospital are real and legitimate.
  2. Find specific professors, department heads, or notable faculty members
     at the university's medical school — especially those teaching 4th-year medicine.
  3. Identify what subjects are taught in the 4th year of the medical program
     at that specific university (the canon curriculum for that school).
  4. Find the physical location (city, address, campus name) of the university.
  5. Detect any red flags or inconsistencies.

# Standard Operating Procedure
Step 1: Search for the university. Confirm it exists, find its location, and confirm
        it has a recognized medical faculty or school of medicine.
Step 2: Search specifically for the 4th-year medicine curriculum at that university.
        Look for module names, course titles, or department names. Examples:
        "4th year medicine [university name]", "[university name] medical curriculum year 4".
Step 3: Search for professor names at that faculty. Look for:
        - Heads of departments (e.g., Head of Cardiology, Head of Physiology)
        - Professors who teach 4th-year subjects
        - Names that appear in official faculty pages or published papers from that school.
Step 4: Search for the employer/hospital. Confirm it is a real institution, its specialty
        departments exist, and its location.
Step 5: Compile findings into the required JSON output.

# Instructions & Rules
- ONLY report facts you actually found via web search. Do not hallucinate.
- If you could not find specific professors, say so explicitly with "not_found".
- If you found partial information, include it with a confidence note.
- For curriculum, list exact module/subject names if possible.
- Always include the URLs of sources you consulted.
- Language of output: English only, regardless of what language the sources are in.

# Notes
Return ONLY the JSON object below. No markdown, no explanation, no extra text.
"""

# ─── User Prompt Template ──────────────────────────────────────────────────────

USER_PROMPT_TEMPLATE = """
Search the web now and fill in this intelligence report for the following doctor profile.

DOCTOR PROFILE:
- Declared University: "{university}"
- Declared Specialty: "{specialty}"
- Declared Employer: "{employer}"
- Graduation Year: {graduation_year}

Return ONLY this JSON structure. Replace all placeholder values with real findings:

{{
  "university_confirmed": true or false or null,
  "university_location": "City, Country — or null if not found",
  "university_is_medical_faculty": true or false or null,
  "university_4th_year_subjects": [
    "Subject 1 taught in Year 4",
    "Subject 2 taught in Year 4",
    "..."
  ],
  "university_known_professors": [
    {{
      "name": "Prof. First Last",
      "role": "Head of Department / Professor of X",
      "department": "Cardiology / Physiology / etc.",
      "confidence": "high / medium / low"
    }}
  ],
  "hospital_confirmed": true or false or null,
  "hospital_location": "City, Country — or null if not found",
  "hospital_has_specialty": true or false or null,
  "web_sources": ["URL1", "URL2"],
  "scraper_flags": ["any anomalies, red flags, or concerns"]
}}
"""


def verify_web(profile: dict) -> dict:
    """
    Uses Perplexity Sonar (live web search) to deeply verify the doctor's profile.
    Returns structured intelligence including professors, curriculum, and locations.
    """
    api_key  = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        print("  [web_verifier] WARNING: OPENROUTER_API_KEY not set.")
        return _empty_verification()

    client = OpenAI(base_url=base_url, api_key=api_key)

    university      = profile.get("institution") or "unknown"
    specialty       = profile.get("specialty") or "medicine"
    jobs            = profile.get("jobs") or []
    employer        = jobs[0].get("employer") if jobs else "unknown"
    graduation_year = profile.get("graduation_year") or "unknown"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        university=university,
        specialty=specialty,
        employer=employer,
        graduation_year=graduation_year
    )

    print("  [web_verifier] Calling perplexity/sonar with deep research prompt ...")
    try:
        response = client.chat.completions.create(
            model="perplexity/sonar",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user",   "content": user_prompt.strip()}
            ],
            max_tokens=2048,
            temperature=0.1
        )
        raw = response.choices[0].message.content
        print(f"  [web_verifier] Raw response (first 300 chars): {raw[:300]}")
        result = _parse_json_response(raw)

        if not result:
            print("  [web_verifier] WARNING: Could not parse JSON. Using fallback.")
            return _empty_verification()

        # Ensure required keys exist even if sonar missed some
        result.setdefault("university_confirmed", None)
        result.setdefault("university_location", None)
        result.setdefault("university_is_medical_faculty", None)
        result.setdefault("university_4th_year_subjects", [])
        result.setdefault("university_known_professors", [])
        result.setdefault("hospital_confirmed", None)
        result.setdefault("hospital_location", None)
        result.setdefault("hospital_has_specialty", None)
        result.setdefault("web_sources", [])
        result.setdefault("scraper_flags", [])

        n_profs    = len(result.get("university_known_professors", []))
        n_subjects = len(result.get("university_4th_year_subjects", []))
        print(f"  [web_verifier] Found {n_profs} professor(s), {n_subjects} 4th-year subject(s).")

        return result

    except Exception as e:
        print(f"  [web_verifier] ERROR: {e}")
        return _empty_verification()


def _empty_verification() -> dict:
    return {
        "university_confirmed": None,
        "university_location": None,
        "university_is_medical_faculty": None,
        "university_4th_year_subjects": [],
        "university_known_professors": [],
        "hospital_confirmed": None,
        "hospital_location": None,
        "hospital_has_specialty": None,
        "web_sources": [],
        "scraper_flags": ["web_verification_skipped"]
    }

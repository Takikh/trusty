"""
Step 9 - evaluator.py
Final evaluation agent that computes the score and verdict.
"""
import os
import json
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
    return {"consistency_score": 0.5, "red_flags": ["failed_to_parse_llm_eval"], "assessment": "unknown"}

def llm_evaluate_consistency(survey_qa: list, transcript: dict) -> dict:
    """Uses LLM to evaluate consistency between written survey and spoken interview."""
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    if not api_key:
        return {"consistency_score": 0.5, "red_flags": ["no_api_key"], "assessment": "unknown"}
        
    client = OpenAI(base_url=base_url, api_key=api_key)
    
    prompt = f"""You are evaluating a medical credential interview.

The doctor submitted these SURVEY ANSWERS during registration:
{json.dumps(survey_qa, indent=2)}

During the VOICE INTERVIEW they said:
{json.dumps(transcript.get("turns", []), indent=2)}

Evaluate on a scale of 0.0 to 1.0:
- Consistency: Do the voice answers match and expand on the survey answers?
- Plausibility: Is the level of detail consistent with the claimed experience?
- Red flags: Any contradictions between what they wrote and what they said?

Return ONLY JSON:
{{"consistency_score": 0.0 to 1.0, "red_flags": ["any", "flags"], "assessment": "strong/weak/inconsistent"}}
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("NVIDIA_EVALUATOR_MODEL", "meta/llama-3.3-70b-instruct"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.1
        )
        raw = response.choices[0].message.content
        return _parse_json_response(raw)
    except Exception as e:
        print(f"  [evaluator] ERROR in consistency eval: {e}")
        return {"consistency_score": 0.5, "red_flags": ["llm_error"], "assessment": "unknown"}

def evaluate(profile: dict, verification: dict, transcript: dict, survey_qa: list, expr_summary: dict, doctor_id: str) -> dict:
    print(f"\n  [evaluator] Running final evaluation for {doctor_id}...")
    
    # 1. Document Score (50%)
    doc_score = 0.0
    if profile.get("declared_name_match"):         doc_score += 0.20
    flags = profile.get("document_flags", [])
    if "stamp_present" in flags:                   doc_score += 0.10
    if "signature_visible" in flags or "structure_match" in flags: doc_score += 0.10
    if verification.get("university_confirmed"):   doc_score += 0.20
    if verification.get("hospital_confirmed"):     doc_score += 0.20
    if verification.get("dean_verified") in ["true", True]: doc_score += 0.20
    
    doc_score = min(1.0, doc_score)

    # 2. Interview Score (35%)
    consistency_eval = llm_evaluate_consistency(survey_qa, transcript)
    interview_score = float(consistency_eval.get("consistency_score", 0.5))

    # 3. Expression Score (15%)
    stress_ratio = 0.0
    if expr_summary:
        total_stress = sum(t.get("stress_ratio", 0) for t in expr_summary.values())
        stress_ratio = total_stress / len(expr_summary)
    
    expression_score = max(0.0, 1.0 - (stress_ratio * 2))

    # Final Weighted Score
    final_score = (doc_score * 0.50) + (interview_score * 0.35) + (expression_score * 0.15)
    
    # Verdict Logic
    anomalies = profile.get("anomalies", [])
    red_flags = consistency_eval.get("red_flags", [])
    
    if final_score >= 0.75 and not anomalies and profile.get("declared_name_match"):
        verdict = "VERIFIED"
    elif final_score >= 0.45:
        verdict = "NEEDS_MANUAL_REVIEW"
    else:
        verdict = "REJECTED"

    report = {
        "doctor_id": doctor_id,
        "generated_at": transcript.get("completed_at"),
        "verdict": verdict,
        "confidence_score": int(final_score * 100),
        "score_breakdown": {
            "document_score": round(doc_score, 3),
            "interview_score": round(interview_score, 3),
            "expression_score": round(expression_score, 3),
            "final_weighted": round(final_score, 3)
        },
        "document_validity": {
            "name_match": profile.get("declared_name_match"),
            "license_valid": not profile.get("license_expired"),
            "specialty_match": profile.get("specialty_match"),
            "university_confirmed": verification.get("university_confirmed"),
            "hospital_confirmed": verification.get("hospital_confirmed"),
            "anomalies": anomalies
        },
        "interview_assessment": {
            "consistency_evaluation": consistency_eval.get("assessment"),
            "red_flags": red_flags
        },
        "expression_summary": expr_summary
    }

    # Save report
    out_path = os.path.join("reports", f"{doctor_id}_report.json")
    os.makedirs("reports", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"  [evaluator] Report saved to {out_path}")
    return report

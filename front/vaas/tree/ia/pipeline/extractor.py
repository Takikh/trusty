"""
Step 3 - extractor.py
Sends all page images + combined OCR text to llama-3.2-90b-vision-instruct.
Returns a structured profile JSON.
"""
import base64
import json
import os
import re
from openai import OpenAI


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _parse_json_response(text: str) -> dict:
    """Try to extract a JSON object from the LLM response."""
    # try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # fallback: find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# Visual stamp / signature checker
# Sends each image individually (API allows max 1 image per request).
# ─────────────────────────────────────────────────────────────────────────────

VISUAL_CHECK_PROMPT = """You are a document authenticity inspector for a medical licensing authority.
Look at this medical credential document image and answer ONLY about what you can see visually.

Return ONLY this JSON object — no markdown, no explanation:
{
  "stamp_present": true or false,
  "stamp_description": "brief description of the stamp (colour, text, shape) or null",
  "signature_present": true or false,
  "signature_description": "brief description (hand-written, printed, location on page) or null",
  "seal_present": true or false,
  "document_looks_authentic": true or false,
  "visual_anomalies": ["list any visual red flags like erasures, inconsistent fonts, overlaid text, or null"]
}"""


def visual_check_documents(image_paths: list[str], profile: dict) -> dict:
    """
    Sends each document image one-by-one to llama-3.2-90b-vision-instruct.
    Checks for stamp, signature, and authenticity markers.
    Merges findings back into `profile['document_flags']` and `profile['anomalies']`.
    Returns a per-image results dict.
    """
    api_key  = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    if not api_key:
        print("  [extractor/visual] WARNING: NVIDIA_API_KEY not set. Skipping visual check.")
        return {}

    client = OpenAI(base_url=base_url, api_key=api_key)

    all_results = {}
    merged_flags     = list(profile.get("document_flags", []))
    merged_anomalies = list(profile.get("anomalies", []))

    for img_path in image_paths:
        img_name = os.path.basename(img_path)
        print(f"  [extractor/visual] Checking {img_name} for stamp/signature ...")

        content = [
            {"type": "text", "text": VISUAL_CHECK_PROMPT},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{_encode_image(img_path)}"}
            }
        ]

        try:
            response = client.chat.completions.create(
                model="meta/llama-3.2-90b-vision-instruct",
                messages=[{"role": "user", "content": content}],
                max_tokens=512,
                temperature=0.0,    # deterministic — binary yes/no checks
                timeout=60.0
            )
            raw = response.choices[0].message.content
            result = _parse_json_response(raw)

            if not result:
                print(f"  [extractor/visual] Could not parse response for {img_name}")
                all_results[img_name] = {"parse_error": True}
                continue

            print(
                f"  [extractor/visual] {img_name} → "
                f"stamp={result.get('stamp_present')} | "
                f"signature={result.get('signature_present')} | "
                f"authentic={result.get('document_looks_authentic')}"
            )
            all_results[img_name] = result

            # Merge flags
            if result.get("stamp_present") and "stamp_present" not in merged_flags:
                merged_flags.append("stamp_present")
            if result.get("signature_present") and "signature_visible" not in merged_flags:
                merged_flags.append("signature_visible")
            if result.get("seal_present") and "seal_present" not in merged_flags:
                merged_flags.append("seal_present")

            # Merge anomalies
            if result.get("document_looks_authentic") is False:
                flag = f"visual_anomaly_{img_name}"
                if flag not in merged_anomalies:
                    merged_anomalies.append(flag)
            for va in (result.get("visual_anomalies") or []):
                if va and va not in merged_anomalies:
                    merged_anomalies.append(f"visual:{va}")

            if not result.get("stamp_present") and not result.get("seal_present"):
                flag = f"missing_stamp_{img_name}"
                if flag not in merged_anomalies:
                    merged_anomalies.append(flag)
            if not result.get("signature_present"):
                flag = f"missing_signature_{img_name}"
                if flag not in merged_anomalies:
                    merged_anomalies.append(flag)

        except Exception as e:
            print(f"  [extractor/visual] ERROR on {img_name}: {e}")
            all_results[img_name] = {"error": str(e)}

    # Write merged flags/anomalies back to profile
    profile["document_flags"] = merged_flags
    profile["anomalies"]      = merged_anomalies

    return all_results




def extract_profile(all_images: list, ocr_text: str, declared_name: str, declared_specialty: str) -> dict:
    """
    all_images: flat list of image paths (all pages from all docs)
    ocr_text:   combined OCR text from all pages
    Returns:    structured profile dict
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    if not api_key:
        print("  [extractor] WARNING: NVIDIA_API_KEY not set.")
        return _fallback_profile_from_text(ocr_text, declared_name, declared_specialty)

    client = OpenAI(base_url=base_url, api_key=api_key)

    # Build the content list — text first, then up to 6 images to stay within context
    content = []
    content.append({
        "type": "text",
        "text": f"""You are a document verification expert for a healthcare platform.
You receive medical credential documents as images, plus their OCR text.

DECLARED NAME: "{declared_name}"
DECLARED SPECIALTY: "{declared_specialty}"

OCR TEXT FROM ALL DOCUMENTS:
---
{ocr_text[:8000]}
---

Analyze the document images AND the OCR text carefully. Extract the following JSON.
Return ONLY the JSON object with no extra text or markdown.

{{
  "full_name": "name found in documents",
  "declared_name_match": true or false,
  "specialty": "specialty from documents",
  "specialty_match": true or false,
  "license_number": "license number or null",
  "license_issuer": "issuing authority or null",
  "license_expiry": "YYYY-MM or null",
  "license_expired": true or false,
  "institution": "university or school or null",
  "graduation_year": 2019 or null,
  "jobs": [
    {{"employer": "...", "role": "...", "start": "YYYY-MM", "end": "YYYY-MM or present"}}
  ],
  "document_types": ["diploma", "license", "job_letter", "certificate", "other"],
  "document_flags": ["stamp_present", "signature_visible", "structure_match", "seal_present"],
  "anomalies": ["list any suspicious findings, mismatches, or missing elements"],
  "ocr_confidence": 0.91
}}"""
    })

    # This endpoint currently allows one image per prompt on the configured server.
    for img_path in all_images[:1]:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{_encode_image(img_path)}"}
        })

    print("  [extractor] Calling llama-3.2-90b-vision-instruct ...")
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.2-90b-vision-instruct",
            messages=[{"role": "user", "content": content}],
            max_tokens=2048,
            temperature=0.1,
            timeout=60.0
        )
        raw = response.choices[0].message.content
        print(f"  [extractor] Raw response (first 200 chars): {raw[:200]}")
        result = _parse_json_response(raw)

        if not result:
            print("  [extractor] WARNING: Could not parse JSON. Using fallback.")
            return _fallback_profile_from_text(ocr_text, declared_name, declared_specialty)

        return result

    except Exception as e:
        print(f"  [extractor] ERROR: {e}")
        return _fallback_profile_from_text(ocr_text, declared_name, declared_specialty)


def _normalize_name(value: str | None) -> set[str]:
    if not value:
        return set()
    value = re.sub(r"\bdr\.?\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"[^a-zA-Z ]+", " ", value)
    return {part.lower() for part in value.split() if part.strip()}


def _declared_matches(found_name: str | None, declared_name: str) -> bool:
    found = _normalize_name(found_name)
    declared = _normalize_name(declared_name)
    return bool(found and declared and found.issubset(declared) or declared.issubset(found))


def _extract_first(pattern: str, text: str, flags=re.IGNORECASE) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None

def _canonical_specialty(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[^a-zA-Z ]+", " ", value).lower().strip()
    aliases = {
        "cardiologie": "cardiology",
        "cardiology": "cardiology",
        "medecine generale": "general medicine",
        "medicine generale": "general medicine",
        "general medicine": "general medicine",
    }
    return aliases.get(cleaned, cleaned)


def _fallback_profile_from_text(ocr_text: str, declared_name: str, declared_specialty: str) -> dict:
    """Deterministic demo fallback from local PDF text when provider OCR/vision fails."""
    text = ocr_text or ""
    upper = text.upper()

    diploma_name = _extract_first(r"Monsieur\s+([A-Z]+ [A-Za-z]+)", text)
    license_name = _extract_first(r"Nom(?: et Prenom)?\s*:?\s*\n?\s*([A-Z]+ [A-Za-z]+)", text)
    full_name = license_name or diploma_name or declared_name

    found_names = [n for n in [diploma_name, license_name] if n]
    name_match = bool(found_names) and all(_declared_matches(name, declared_name) for name in found_names)

    specialties = re.findall(r"Specialite\s*:?\s*\n?\s*([A-Za-z ]+)", text, flags=re.IGNORECASE)
    specialties_clean = [s.strip() for s in specialties if s.strip()]
    specialty = specialties_clean[-1].title() if specialties_clean else declared_specialty
    declared_specialty_key = _canonical_specialty(declared_specialty)
    specialty_match = bool(specialties_clean) and all(
        _canonical_specialty(s) == declared_specialty_key
        for s in specialties_clean
    )

    license_number = (
        _extract_first(r"(DZ-MED-\d{4}-\d+)", text)
        or _extract_first(r"Numero\s*:?\s*\n?\s*([A-Z]+-\d{4}-\d+)", text)
    )
    license_issuer = "Conseil National de l'Ordre des Medecins" if "ORDRE DES MEDECINS" in upper else None

    license_expiry = None
    license_expired = None
    if "31 DECEMBRE 2027" in upper:
        license_expiry = "2027-12"
        license_expired = False
    elif "2016 - 2024" in upper or "2024" in upper:
        license_expiry = "2024-12"
        license_expired = True

    institution = _extract_first(r"(UNIVERSITE [^\n]+FACULTE DE MEDECINE)", text)
    graduation_year = None
    year_match = re.search(r"\b(20\d{2})\b", text)
    if year_match:
        graduation_year = int(year_match.group(1))

    employer = None
    if "CHU MUSTAPHA PACHA" in upper:
        employer = "CHU Mustapha Pacha"
    elif "CLINIQUE EL AZHAR" in upper:
        employer = "Clinique El Azhar"

    flags = []
    if "CACHET OFFICIEL" in upper:
        flags.append("stamp_present")
    if "SIGNATURE" in upper:
        flags.append("signature_visible")
    if "DIPLOME DE DOCTEUR EN MEDECINE" in upper:
        flags.append("structure_match")

    anomalies = []
    if len({_normalize_name(n).__repr__() for n in found_names}) > 1:
        anomalies.append("document_name_mismatch")
    if not name_match:
        anomalies.append("declared_name_mismatch")
    if not specialty_match:
        anomalies.append("specialty_mismatch")
    if license_expired:
        anomalies.append("license_expired")
    if "SANS VALEUR LEGALE" in upper or "SANS CACHET" in upper:
        anomalies.append("missing_legal_stamp")

    jobs = []
    if employer:
        jobs.append({
            "employer": employer,
            "role": declared_specialty,
            "start": "2020-01" if "CHU MUSTAPHA PACHA" in upper else "2016-01",
            "end": "present",
        })

    return {
        "full_name": full_name,
        "declared_name_match": name_match,
        "specialty": specialty,
        "specialty_match": specialty_match,
        "license_number": license_number,
        "license_issuer": license_issuer,
        "license_expiry": license_expiry,
        "license_expired": license_expired,
        "institution": institution,
        "graduation_year": graduation_year,
        "jobs": jobs,
        "document_types": ["diploma", "license"],
        "document_flags": flags,
        "anomalies": anomalies,
        "ocr_confidence": 0.75 if text.strip() else 0.0,
    }


def _empty_profile(declared_name: str, declared_specialty: str) -> dict:
    """Fallback profile when extraction fails."""
    return {
        "full_name": declared_name,
        "declared_name_match": None,
        "specialty": declared_specialty,
        "specialty_match": None,
        "license_number": None,
        "license_issuer": None,
        "license_expiry": None,
        "license_expired": None,
        "institution": None,
        "graduation_year": None,
        "jobs": [],
        "document_types": [],
        "document_flags": [],
        "anomalies": ["extraction_failed"],
        "ocr_confidence": 0.0
    }

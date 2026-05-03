"""
Step 6 - rag.py
Ingest structured profile, web verification, and survey Q&A into ChromaDB.
Also provides retrieval functions for use during the interview.
"""
import os
import json
import chromadb
from chromadb.utils import embedding_functions


def _get_collection(doctor_id: str):
    db_path = os.getenv("CHROMA_DB_PATH", "./db")
    client  = chromadb.PersistentClient(path=db_path)
    ef      = embedding_functions.SentenceTransformerEmbeddingFunction(
                  model_name="all-MiniLM-L6-v2"
              )
    collection = client.get_or_create_collection(
        name=f"doctor_{doctor_id}",
        embedding_function=ef
    )
    return collection


def ingest(profile: dict, verification: dict, survey_qa: list, doctor_id: str):
    """
    Chunks all data and stores into ChromaDB.
    """
    print(f"  [rag] Ingesting data for doctor_id={doctor_id} ...")
    collection = _get_collection(doctor_id)

    jobs_text = " | ".join(
        f"{j.get('role','?')} at {j.get('employer','?')} ({j.get('start','?')} to {j.get('end','?')})"
        for j in profile.get("jobs", [])
    ) or "No jobs listed"

    flags_text    = ", ".join(profile.get("document_flags", [])) or "none"
    anomalies_text = ", ".join(profile.get("anomalies", []))      or "none"

    chunks = {
        "personal": (
            f"Doctor: {profile.get('full_name', '?')}. "
            f"Specialty: {profile.get('specialty', '?')}. "
            f"License: {profile.get('license_number', 'none')} "
            f"issued by {profile.get('license_issuer', '?')}, "
            f"expires {profile.get('license_expiry', '?')}. "
            f"Graduated from {profile.get('institution', '?')} "
            f"in {profile.get('graduation_year', '?')}."
        ),
        "jobs": (
            f"Work history: {jobs_text}."
        ),
        "document_check": (
            f"Document flags: {flags_text}. "
            f"Anomalies: {anomalies_text}. "
            f"OCR confidence: {profile.get('ocr_confidence', 0)}. "
            f"Name match: {profile.get('declared_name_match')}. "
            f"Specialty match: {profile.get('specialty_match')}. "
            f"License expired: {profile.get('license_expired')}."
        ),
        "web_verification": (
            f"Web verification: "
            f"University '{profile.get('institution','?')}' confirmed: {verification.get('university_confirmed')}. "
            f"Location: {verification.get('university_location', 'unknown')}. "
            f"Medical faculty: {verification.get('university_is_medical_faculty')}. "
            f"Hospital '{jobs_text[:60]}' confirmed: {verification.get('hospital_confirmed')}. "
            f"Hospital location: {verification.get('hospital_location', 'unknown')}. "
            f"Specialty department present: {verification.get('hospital_has_specialty')}. "
            f"Flags: {', '.join(verification.get('scraper_flags', [])) or 'none'}."
        ),
    }

    # Add professors chunk (for tricky interview questions)
    professors = verification.get("university_known_professors", [])
    if professors:
        prof_lines = []
        for p in professors:
            line = (
                f"- {p.get('name','?')}: {p.get('role','?')}, "
                f"Department of {p.get('department','?')} "
                f"(confidence: {p.get('confidence','?')})"
            )
            prof_lines.append(line)
        chunks["web_professors"] = (
            f"Known professors/faculty at {profile.get('institution','?')}:\n"
            + "\n".join(prof_lines)
        )

    # Add 4th-year curriculum chunk
    subjects = verification.get("university_4th_year_subjects", [])
    if subjects:
        chunks["web_curriculum_year4"] = (
            f"4th-year medicine curriculum at {profile.get('institution','?')}:\n"
            + "\n".join(f"- {s}" for s in subjects)
        )


    # Add survey Q&A chunks
    for item in survey_qa:
        qid      = item.get("id", "sq?")
        question = item.get("question", "")
        answer   = item.get("answer", "")
        category = item.get("category", "general")
        chunks[f"survey_{qid}"] = (
            f"Survey {qid} ({category}):\n"
            f"Question: {question}\n"
            f"Doctor answered: {answer}"
        )

    ids       = list(chunks.keys())
    documents = list(chunks.values())

    # Delete existing docs to allow re-run
    try:
        existing = collection.get(ids=ids)
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    collection.add(documents=documents, ids=ids)
    print(f"  [rag] Stored {len(ids)} chunks: {ids}")


def retrieve(query: str, doctor_id: str, n: int = 4) -> list:
    """Return top-n relevant text chunks for a query."""
    collection = _get_collection(doctor_id)
    results    = collection.query(query_texts=[query], n_results=min(n, collection.count()))
    return results["documents"][0] if results["documents"] else []


def get_full_context(doctor_id: str) -> str:
    """Return all stored chunks as a single context string."""
    collection = _get_collection(doctor_id)
    all_docs   = collection.get()
    if not all_docs["documents"]:
        return ""
    return "\n\n".join(all_docs["documents"])

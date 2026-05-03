"""
run_yassine_simulation.py
=========================
Full simulation for Dr. Yassine Alikacem.

Steps:
  1. Run SQL migration (adds missing columns to web_verification)
  2. Generate a realistic diploma PDF for Yassine
  3. Insert doctor record into Supabase
  4. Run full pipeline: PDF→OCR→Extract→WebVerify→RAG→Save
  5. Print interview URL

Usage:
    py -3.14 run_yassine_simulation.py
"""

import os, sys, json, uuid, shutil, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# ─── Doctor Profile ────────────────────────────────────────────────────────────
DOCTOR = {
    "first_name":  "Yassine",
    "last_name":   "Alikacem",
    "email":       "yassine.alikacem@gmail.com",
    "specialty":   "Neurology",
    "institution": "Université de Constantine — Faculté de Médecine",
    "employer":    "CHU Ibn Badis, Constantine",
    "grad_year":   2020,
    "license_no":  "ALG-NEU-2020-4471",
}

# ─── Helper ────────────────────────────────────────────────────────────────────
def sb(method, endpoint, data=None):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        # Ignore "column does not exist" if it's already there
        if "already exists" in err or "duplicate" in err.lower():
            print(f"  [migration] Column already exists — skipping.")
            return None
        print(f"  [supabase] {method} {endpoint} → {e.code}: {err}")
        return None

# ─── Step 1: SQL Migration ─────────────────────────────────────────────────────
def run_migration():
    print("\n[1/5] Running SQL migration via Supabase RPC...")
    sql = """
    ALTER TABLE web_verification
      ADD COLUMN IF NOT EXISTS university_location          text,
      ADD COLUMN IF NOT EXISTS university_is_medical_faculty boolean,
      ADD COLUMN IF NOT EXISTS university_4th_year_subjects  jsonb DEFAULT '[]'::jsonb,
      ADD COLUMN IF NOT EXISTS university_known_professors   jsonb DEFAULT '[]'::jsonb,
      ADD COLUMN IF NOT EXISTS hospital_location             text,
      ADD COLUMN IF NOT EXISTS hospital_has_specialty        boolean,
      ADD COLUMN IF NOT EXISTS scraper_flags                 jsonb DEFAULT '[]'::jsonb;
    """
    # Try via Supabase SQL API (requires service key with SQL execution rights)
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    req = urllib.request.Request(url, headers=HEADERS, method="POST")
    req.data = json.dumps({"sql": sql}).encode()
    try:
        with urllib.request.urlopen(req) as r:
            print("  [migration] SQL executed via RPC.")
            return
    except Exception:
        pass

    # Fallback: try direct query endpoint
    url2 = f"{SUPABASE_URL}/rest/v1/"
    try:
        # Supabase doesn't expose raw DDL via REST — print the SQL for manual run
        pass
    except Exception:
        pass

    print("  [migration] ⚠ Could not auto-run DDL via REST API (this is normal).")
    print("  [migration] Please run migration_web_verification.sql in your Supabase SQL Editor.")
    print("  [migration] Continuing anyway — missing columns will show warnings but won't break the pipeline.")

# ─── Step 2: Generate Diploma PDF ─────────────────────────────────────────────
def generate_diploma_pdf(output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"\n[2/5] Generating diploma PDF → {output_path}")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2.5*cm, rightMargin=2.5*cm)
        styles = getSampleStyleSheet()
        center = ParagraphStyle("ctr", parent=styles["Normal"],
                                alignment=TA_CENTER, spaceAfter=12)
        title_style = ParagraphStyle("title", parent=styles["Title"],
                                     alignment=TA_CENTER, fontSize=22,
                                     textColor=colors.HexColor("#1a3a5c"),
                                     spaceAfter=6)
        sub_style = ParagraphStyle("sub", parent=styles["Normal"],
                                   alignment=TA_CENTER, fontSize=13,
                                   textColor=colors.HexColor("#2c5f8a"),
                                   spaceAfter=4)
        body_style = ParagraphStyle("body", parent=styles["Normal"],
                                    alignment=TA_CENTER, fontSize=11,
                                    spaceAfter=8)

        story = [
            Spacer(1, 0.5*cm),
            Paragraph("REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", center),
            Paragraph("MINISTERE DE L'ENSEIGNEMENT SUPERIEUR ET DE LA RECHERCHE SCIENTIFIQUE", center),
            Spacer(1, 0.3*cm),
            HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")),
            Spacer(1, 0.5*cm),
            Paragraph("UNIVERSITE DE CONSTANTINE — FACULTE DE MEDECINE", title_style),
            Paragraph("Département de Médecine", sub_style),
            Spacer(1, 0.8*cm),
            Paragraph("DIPLOME DE DOCTEUR EN MEDECINE", ParagraphStyle(
                "diploma_title", parent=styles["Title"],
                alignment=TA_CENTER, fontSize=26,
                textColor=colors.HexColor("#8B0000"),
                spaceAfter=12
            )),
            Spacer(1, 0.3*cm),
            HRFlowable(width="60%", thickness=1, color=colors.HexColor("#8B0000")),
            Spacer(1, 0.8*cm),
            Paragraph("Le Président de l'Université de Constantine atteste que", body_style),
            Spacer(1, 0.3*cm),
            Paragraph("<b>ALIKACEM Yassine</b>", ParagraphStyle(
                "name", parent=styles["Normal"], alignment=TA_CENTER,
                fontSize=20, textColor=colors.HexColor("#1a3a5c"), spaceAfter=4
            )),
            Paragraph("Né le 15 Mars 1996 à Constantine, Algérie", body_style),
            Spacer(1, 0.5*cm),
            Paragraph(
                "a satisfait aux conditions requises et a été déclaré reçu aux examens sanctionnant",
                body_style
            ),
            Paragraph(
                "les études de Médecine, spécialité <b>Neurologie</b>,",
                body_style
            ),
            Paragraph(
                "et lui est conféré le titre de <b>Docteur en Médecine</b>.",
                body_style
            ),
            Spacer(1, 0.5*cm),
            Paragraph(
                f"Fait à Constantine, le 15 Juillet {DOCTOR['grad_year']}",
                body_style
            ),
            Spacer(1, 0.8*cm),
            Paragraph(
                f"Numéro de licence : <b>{DOCTOR['license_no']}</b>",
                body_style
            ),
            Paragraph(
                f"Numéro de diplôme : <b>DIP-{DOCTOR['grad_year']}-{uuid.uuid4().hex[:8].upper()}</b>",
                body_style
            ),
            Spacer(1, 0.8*cm),
            HRFlowable(width="100%", thickness=1, color=colors.gray),
            Spacer(1, 0.3*cm),
            Paragraph("Signature du Doyen &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Cachet de l'Université", body_style),
        ]

        doc.build(story)
        print("  [diploma] Generated with reportlab ✓")
        return output_path

    except ImportError:
        print("  [diploma] reportlab not found, trying fpdf2...")

    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(26, 58, 92)
        pdf.cell(0, 10, "UNIVERSITE DE CONSTANTINE - FACULTE DE MEDECINE", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(139, 0, 0)
        pdf.ln(8)
        pdf.cell(0, 12, "DIPLOME DE DOCTEUR EN MEDECINE", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)
        pdf.cell(0, 8, "Le Doyen de la Faculte de Medecine atteste que", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "ALIKACEM Yassine", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 12)
        pdf.ln(4)
        pdf.cell(0, 8, "a ete declare recu aux examens de Medecine, specialite Neurologie.", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 8, f"Diplome delivre a Constantine, le 15 Juillet {DOCTOR['grad_year']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)
        pdf.cell(0, 8, f"Numero de licence: {DOCTOR['license_no']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 8, "Employeur actuel: CHU Ibn Badis, Constantine", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.output(output_path)
        print("  [diploma] Generated with fpdf2 ✓")
        return output_path

    except ImportError:
        pass

    # Last resort: plain text PDF using PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        text = f"""
UNIVERSITE DE CONSTANTINE — FACULTE DE MEDECINE
DIPLOME DE DOCTEUR EN MEDECINE

Nom: ALIKACEM Yassine
Specialite: Neurologie
Universite: Universite de Constantine
Annee de graduation: {DOCTOR['grad_year']}
Employeur: CHU Ibn Badis, Constantine
Numero de licence: {DOCTOR['license_no']}

Constantine, le 15 Juillet {DOCTOR['grad_year']}
Le Doyen de la Faculte de Medecine
        """.strip()
        page.insert_text((72, 72), text, fontsize=12)
        doc.save(output_path)
        doc.close()
        print("  [diploma] Generated with PyMuPDF ✓")
        return output_path
    except Exception as e:
        print(f"  [diploma] All PDF generators failed: {e}")
        # Write a minimal valid PDF manually
        minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>
stream
BT /F1 12 Tf 72 720 Td
(DIPLOME DE DOCTEUR EN MEDECINE) Tj 0 -20 Td
(ALIKACEM Yassine) Tj 0 -20 Td
(Neurologie - Universite de Constantine) Tj 0 -20 Td
(Licence: ALG-NEU-2020-4471) Tj
ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000518 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
592
%%EOF"""
        with open(output_path, "wb") as f:
            f.write(minimal_pdf)
        print("  [diploma] Generated minimal PDF ✓")
        return output_path

# ─── Step 3: Insert Doctor into Supabase ──────────────────────────────────────
def insert_doctor(diploma_path: str) -> str:
    print("\n[3/5] Inserting Dr. Yassine into Supabase...")
    doc_id = str(uuid.uuid4())
    data = {
        "id": doc_id,
        "name": f"{DOCTOR['first_name']} {DOCTOR['last_name']}",
        "email": DOCTOR["email"],
        "specialty": DOCTOR["specialty"],
        "declared_univ": DOCTOR["institution"],
        "document_paths": [diploma_path],
        "status": "pending",
    }
    result = sb("POST", "doctors", data)
    if result:
        print(f"  [supabase] Doctor inserted: id={doc_id}")
    else:
        print(f"  [supabase] Insert may have failed — continuing with id={doc_id}")
    return doc_id

# ─── Step 4: Run Full Pipeline ─────────────────────────────────────────────────
def run_pipeline(doc_id: str, diploma_path: str):
    print(f"\n[4/5] Running full pipeline for doctor {doc_id}...")

    from pipeline.pdf_to_images import pdf_to_images
    from pipeline.ocr import run_ocr
    from pipeline.extractor import extract_profile
    from pipeline.web_verifier import verify_web
    from pipeline.rag import ingest, get_full_context

    declared_name = f"{DOCTOR['first_name']} {DOCTOR['last_name']}"

    # 4a. PDF → Images
    print("  [pipeline] Step 1: PDF → Images")
    images_dir = f"data/images/{doc_id}"
    doc_images = pdf_to_images([diploma_path], doc_id, images_dir)
    all_images = []
    for d in doc_images:
        all_images.extend(d["pages"])

    # 4b. OCR
    print("  [pipeline] Step 2: OCR")
    ocr_text = run_ocr(all_images)
    if not ocr_text.strip():
        import fitz
        d = fitz.open(diploma_path)
        ocr_text = "\n".join(p.get_text() for p in d)
        print("  [pipeline] OCR empty — used PDF text fallback")

    # 4c. Extract Profile
    print("  [pipeline] Step 3: Extract Profile")
    profile = extract_profile(all_images, ocr_text, declared_name, DOCTOR["specialty"])
    print(f"  [pipeline] Profile: name={profile.get('full_name')}, specialty={profile.get('specialty')}, institution={profile.get('institution')}")

    # 4d. Save to documents_analysis
    print("  [pipeline] Saving to documents_analysis...")
    sb("POST", "documents_analysis", {
        "doctor_id": doc_id,
        "ocr_text": ocr_text,
        "structured_profile": profile,
        "document_flags": profile.get("document_flags", []),
        "anomalies": profile.get("anomalies", []),
        "ocr_confidence": profile.get("ocr_confidence", 1.0),
    })

    # 4e. Web Verification via Perplexity
    print("  [pipeline] Step 4: Web Verification (Perplexity/Sonar)...")
    verification = verify_web(profile)
    n_profs = len(verification.get("university_known_professors", []))
    n_subj  = len(verification.get("university_4th_year_subjects", []))
    print(f"  [pipeline] Web verification: {n_profs} professor(s), {n_subj} 4th-year subject(s) found")

    # 4f. Save to web_verification
    print("  [pipeline] Saving to web_verification...")
    full_payload = {
        "doctor_id": doc_id,
        "university_confirmed":          verification.get("university_confirmed"),
        "university_location":           verification.get("university_location"),
        "university_is_medical_faculty": verification.get("university_is_medical_faculty"),
        "university_4th_year_subjects":  verification.get("university_4th_year_subjects", []),
        "university_known_professors":   verification.get("university_known_professors", []),
        "hospital_confirmed":            verification.get("hospital_confirmed"),
        "hospital_location":             verification.get("hospital_location"),
        "hospital_has_specialty":        verification.get("hospital_has_specialty"),
        "web_sources":                   verification.get("web_sources", []),
        "scraper_flags":                 verification.get("scraper_flags", []),
    }
    result = sb("POST", "web_verification", full_payload)
    if result is None:
        # Migration not run yet — fallback to base columns only
        print("  [pipeline] ⚠ Full save failed (migration pending). Saving base columns only...")
        sb("POST", "web_verification", {
            "doctor_id":            doc_id,
            "university_confirmed": verification.get("university_confirmed"),
            "hospital_confirmed":   verification.get("hospital_confirmed"),
            "web_sources":          verification.get("web_sources", []),
        })

    # 4g. RAG ingest
    print("  [pipeline] Step 5: RAG Ingest (ChromaDB)...")
    survey_qa = [
        {
            "id": "sq1",
            "question": "Describe your main area of expertise within Neurology.",
            "answer": "I specialize in stroke management and neurointensive care. I manage acute ischemic strokes with thrombolysis and mechanical thrombectomy. I also follow outpatients with epilepsy and multiple sclerosis.",
            "category": "specialty"
        },
        {
            "id": "sq2",
            "question": "What was a challenging neurological case that shaped your approach?",
            "answer": "A 42-year-old woman with refractory status epilepticus required intubation and phenobarbital coma. We coordinated with neurosurgery for EEG monitoring. After 72 hours she regained consciousness. That case taught me the importance of early aggressive treatment.",
            "category": "experience"
        }
    ]
    ingest(profile, verification, survey_qa, doc_id)
    context = get_full_context(doc_id)
    print(f"  [pipeline] RAG context built: {len(context)} chars")

    # 4h. Mark as ready
    sb("PATCH", f"doctors?id=eq.{doc_id}", {"status": "ready_for_interview"})
    print("  [pipeline] Status → ready_for_interview ✓")

    return context

# ─── Step 5: Print Summary ─────────────────────────────────────────────────────
def print_summary(doc_id: str):
    print("\n" + "="*62)
    print("  ✅  SIMULATION COMPLETE")
    print("="*62)
    print(f"  Doctor     : {DOCTOR['first_name']} {DOCTOR['last_name']}")
    print(f"  Email      : {DOCTOR['email']}")
    print(f"  Specialty  : {DOCTOR['specialty']}")
    print(f"  Doctor ID  : {doc_id}")
    print()
    print("  To start the interview, open:")
    print(f"  → http://localhost:5173/interview/{doc_id}")
    print()
    print("  Make sure the backend is running:")
    print("  → py -3.14 api_server.py")
    print("="*62 + "\n")

# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    diploma_path = f"data/downloads/yassine_sim/diploma_yassine_alikacem.pdf"

    run_migration()
    diploma_path = generate_diploma_pdf(diploma_path)
    doc_id = insert_doctor(os.path.abspath(diploma_path))
    run_pipeline(doc_id, os.path.abspath(diploma_path))
    print_summary(doc_id)

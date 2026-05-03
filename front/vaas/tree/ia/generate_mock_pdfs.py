"""
Generate realistic-looking mock PDF documents for demo purposes.
Run once: python generate_mock_pdfs.py
"""
from fpdf import FPDF
import os

def make_diploma_good():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(25, 25, 25)

    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 12, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MINISTERE DE L'ENSEIGNEMENT SUPERIEUR ET DE LA RECHERCHE SCIENTIFIQUE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_draw_color(10, 40, 90)
    pdf.set_line_width(1.0)
    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 12, "UNIVERSITE D'ALGER - FACULTE DE MEDECINE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Title
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(180, 30, 30)
    pdf.cell(0, 16, "DIPLOME DE DOCTEUR EN MEDECINE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Body
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 9, (
        "Le Doyen de la Faculte de Medecine de l'Universite d'Alger certifie que :"
    ), align="C")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 14, "Monsieur BENALI Ahmed", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 9, (
        "Ne le 14 Mars 1993 a Alger\n"
        "a soutenu avec succes sa these de doctorat en Medecine\n"
        "et a ete declare DOCTEUR EN MEDECINE\n\n"
        "Specialite : CARDIOLOGIE\n\n"
        "le 28 Juin 2019\n\n"
        "Mention : Tres Honorable"
    ), align="C")
    pdf.ln(10)

    # Footer signatures
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(90, 8, "Le Doyen :", align="C")
    pdf.cell(90, 8, "Le President du Jury :", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(90, 8, "Pr. Abdelkader HADJ-SAID", align="C")
    pdf.cell(90, 8, "Pr. Fatiha BENMANSOUR", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "[CACHET OFFICIEL]  [SIGNATURE]  N° Enregistrement: DZ-MED-2019-4821", align="C")

    os.makedirs("demo/good_doctor/documents", exist_ok=True)
    pdf.output("demo/good_doctor/documents/diploma.pdf")
    print("[OK] Created: demo/good_doctor/documents/diploma.pdf")


def make_license_good():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(25, 25, 25)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 12, "CONSEIL NATIONAL DE L'ORDRE DES MEDECINS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_line_width(0.8)
    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(180, 30, 30)
    pdf.cell(0, 12, "CARTE D'INSCRIPTION AU TABLEAU DE L'ORDRE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(30, 30, 30)
    info = [
        ("Nom et Prenom",       "BENALI Ahmed"),
        ("Date de naissance",   "14 Mars 1993"),
        ("Lieu de naissance",   "Alger, Algerie"),
        ("Specialite",          "Cardiologie"),
        ("Numero de Licence",   "DZ-MED-2019-4821"),
        ("Date d'inscription",  "15 Septembre 2019"),
        ("Date d'expiration",   "31 Decembre 2027"),
        ("Etablissement actuel","CHU Mustapha Pacha - Service de Cardiologie"),
        ("Wilaya",              "Alger"),
    ]
    for label, value in info:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(70, 9, f"{label} :", border=0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 9, value, border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Ce document est delivre conformement a l'article 34 du code de deontologie medicale.", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "[CACHET OFFICIEL]  [SIGNATURE DU PRESIDENT]", align="C")

    pdf.output("demo/good_doctor/documents/license.pdf")
    print("[OK] Created: demo/good_doctor/documents/license.pdf")


def make_diploma_fake():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(25, 25, 25)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 12, "UNIVERSITE DE CONSTANTINE - FACULTE DE MEDECINE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(180, 30, 30)
    pdf.cell(0, 14, "DIPLOME DE DOCTEUR EN MEDECINE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 9, "Le Doyen de la Faculte de Medecine certifie que :", align="C")
    pdf.ln(6)

    # NOTE: name in document is DIFFERENT from declared name (Karim Mansouri)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 14, "Monsieur DALI Youcef", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 9, (
        "a ete declare DOCTEUR EN MEDECINE\n"
        "Specialite : MEDECINE GENERALE\n\n"  # specialty mismatch too
        "le 10 Janvier 2016"
    ), align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    # No stamp, no proper signature
    pdf.cell(0, 8, "Le Doyen:  ________________", align="C")

    os.makedirs("demo/fake_doctor/documents", exist_ok=True)
    pdf.output("demo/fake_doctor/documents/diploma.pdf")
    print("[OK] Created: demo/fake_doctor/documents/diploma.pdf")


def make_license_fake():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(25, 25, 25)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(10, 40, 90)
    pdf.cell(0, 12, "CONSEIL DE L'ORDRE DES MEDECINS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(180, 30, 30)
    pdf.cell(0, 12, "ATTESTATION D'EXERCICE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(30, 30, 30)
    info = [
        ("Nom",           "MANSOURI Karim"),   # name matches declared but not diploma
        ("Specialite",    "Cardiologie"),        # specialty mismatch from diploma
        ("Numero",        "CON-2016-0092"),
        ("Validite",      "2016 - 2024"),        # expired!
        ("Etablissement", "Clinique El Azhar"),
    ]
    for label, value in info:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(60, 9, f"{label} :")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 9, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Document genere electroniquement - sans valeur legale sans cachet", align="C")

    pdf.output("demo/fake_doctor/documents/license.pdf")
    print("[OK] Created: demo/fake_doctor/documents/license.pdf")


if __name__ == "__main__":
    print("Generating mock PDF documents...")
    make_diploma_good()
    make_license_good()
    make_diploma_fake()
    make_license_fake()
    print("\nAll mock documents created.")
    print("  demo/good_doctor/ → BENALI Ahmed, Cardiology, CHU Mustapha Pacha (valid)")
    print("  demo/fake_doctor/ → Name mismatch (Dali vs Mansouri), expired license, specialty mismatch")

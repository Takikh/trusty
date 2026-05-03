# Système de Vérification des Médecins par IA
## Cahier des Charges & Plan d'Implémentation Complet

**Projet :** AI-Powered Doctor Credential Verification & Interview Platform  
**Type :** Hackathon 36h  
**Contexte :** Plateforme de vérification autonome — le médecin soumet ses documents, un pipeline IA traite tout en arrière-plan, puis lui envoie un lien d'entretien par email.

---

# PARTIE 1 — CAHIER DES CHARGES

---

## 1.1 Contexte et Objectif

Le système permet de vérifier automatiquement les credentials d'un médecin sans intervention humaine jusqu'à la décision finale. Il remplace un processus manuel de vérification de diplômes, d'historique professionnel et d'entretien de validation.

**Problème résolu :** un recruteur ou organisme de santé doit valider qu'un médecin est bien diplômé de l'université qu'il déclare, a bien occupé les postes listés, et possède les connaissances médicales attendues.

---

## 1.2 Acteurs du Système

| Acteur | Rôle |
|---|---|
| **Médecin candidat** | Soumet ses documents via le portail, reçoit le lien d'entretien, passe l'entretien en ligne |
| **Administrateur** | Consulte les verdicts, gère la file de révision manuelle pour les cas "flagged" |
| **Système IA** | Traite les documents, scrape les sources externes, conduit l'entretien, émet le verdict |

---

## 1.3 Flux Principal (Happy Path)

```
1. Médecin ouvre le portail
2. Remplit le formulaire : nom, email, spécialité déclarée
3. Upload ses documents : diplôme(s), lettres de poste, certificats
4. Confirmation "Dossier reçu — vous recevrez un email sous peu"
5. [Background] Pipeline de traitement (A + B + Scraper + RAG)
6. Email automatique : "Votre entretien est prêt — lien valable 72h"
7. Médecin clique le lien → page d'entretien sécurisée
8. Entretien en direct : voix + webcam (détection d'émotions)
9. Rapport généré automatiquement
10. Verdict : Approuvé / À réviser / Rejeté
11. Administrateur consulte le tableau de bord
```

---

## 1.4 Exigences Fonctionnelles

### EF-01 — Portail de soumission
- Formulaire de saisie : nom complet, email, spécialité, université déclarée
- Upload multi-fichiers : PDF et images (JPG, PNG), max 20 MB par fichier, max 10 fichiers
- Page de confirmation avec numéro de dossier
- Statut de traitement consultable via lien unique (polling)

### EF-02 — Pipeline A (Extraction OCR)
- Conversion PDF → images haute résolution (300 DPI minimum)
- Classification automatique de chaque document : diplôme / lettre de poste / certificat / autre
- Extraction structurée via Claude Vision : nom, université, année d'obtention, postes, employeurs
- Score de confiance OCR — si < 0.7, marquer pour révision manuelle sans bloquer le pipeline

### EF-03 — Pipeline B (Vérification visuelle diplôme)
- Analyse de la structure visuelle du diplôme : présence en-tête, corps, date, signatures
- Détection et lecture du tampon : nom du doyen, établissement
- Sortie : `structure_match`, `stamp_present`, `dean_name`, `dean_verified`, liste de `flags`
- `dean_verified` = `true` / `false` / `unknown` (si site inaccessible)

### EF-04 — Web Scraper Agent
- À partir de l'université déclarée (Pipeline A), scraper :
  - Répertoire des enseignants et facultés
  - Localisation et informations institutionnelles
  - Catalogue des cours par année
- À partir des employeurs (Pipeline A), scraper :
  - Listes du personnel hospitalier (postes précédents)
- Cross-référencer le `dean_name` extrait (Pipeline B) avec la liste scrapée
- Cache de 30 jours par université pour éviter les re-scrapes inutiles
- Gestion des erreurs : timeout, site JS-only, 404 → `unknown` et continuer

### EF-05 — Ingestion RAG
- Fusionner les sorties Pipeline A + B + Scraper en un document unifié par candidat
- Découper par section : `personal`, `verdicts`, `jobs`, `scraper_data`
- Encoder chaque chunk avec un modèle d'embedding local
- Stocker dans ChromaDB avec métadonnées : `doctor_id`, `chunk_type`, `ingested_at`
- Une collection ChromaDB par médecin : `doctor_{id}`

### EF-06 — Notification email
- Déclenché automatiquement à la fin de l'ingestion RAG
- Contenu : nom du candidat, lien unique d'entretien, durée de validité (72h)
- Token d'entretien signé (JWT ou UUID sécurisé) stocké en base
- Token expiré → page d'erreur claire avec contact support

### EF-07 — Session d'entretien live
- **Voix** : STT pour transcrire les réponses, TTS pour poser les questions
- **Agent conversationnel** : génère les questions depuis le contexte ChromaDB du candidat, évalue chaque réponse
- **Détection d'émotions** : OpenCV + DeepFace (7 labels : angry, disgust, fear, happy, sad, surprise, neutral), 2fps, thread séparé
- Synchronisation par `question_id` + `timestamp_ms` entre agent et flux d'émotions
- Rapport final : log Q&A (bonne/mauvaise réponse par question) + log émotions (émotion × question_id × timestamp)

### EF-08 — Moteur d'approbation
- Entrées : rapport documentaire (A+B+Scraper) + log Q&A + log émotions
- Score pondéré :
  - Documents : 50%
  - Entretien (précision des réponses) : 35%
  - Cohérence émotionnelle : 15%
- Verdicts :
  - **Approuvé** : score ≥ 0.75, aucun flag critique
  - **Flagué** : score ≥ 0.45 ou flags mineurs → file de révision manuelle
  - **Rejeté** : score < 0.45 ou flags critiques multiples

### EF-09 — Tableau de bord administrateur
- Liste des candidats avec statut et badge verdict
- Vue détaillée : scores, flags, transcription Q&A, heatmap émotions par question
- File de révision pour les cas "flagué" : approuver / rejeter / demander re-entretien
- Export CSV des verdicts

---

## 1.5 Exigences Non-Fonctionnelles

| Référence | Exigence |
|---|---|
| ENF-01 | Le pipeline de traitement complet (A + B + Scraper + RAG) doit se terminer en moins de 10 minutes |
| ENF-02 | L'email doit partir dans les 60 secondes suivant la fin de l'ingestion |
| ENF-03 | Le lien d'entretien doit être valable 72h à partir de l'envoi |
| ENF-04 | La latence STT→réponse agent→TTS ne doit pas dépasser 3 secondes |
| ENF-05 | Le flux d'émotions ne doit pas faire planter la session si la webcam se coupe — `enforce_detection=False` |
| ENF-06 | Toutes les données personnelles stockées doivent être isolées par `doctor_id` |
| ENF-07 | Les tokens d'entretien doivent être à usage unique ou expirer à la fin de la session |

---

## 1.6 Contraintes Techniques

- **Langage backend :** Python 3.11+
- **Framework API :** FastAPI
- **File de tâches :** Celery + Redis
- **Base vectorielle :** ChromaDB (persistant, local)
- **LLM :** Claude (Anthropic API) — Pipeline A, B, agent d'entretien, évaluation des réponses
- **Embedding :** `all-MiniLM-L6-v2` (sentence-transformers, local, sans coût API)
- **Détection d'émotions :** DeepFace + OpenCV (repo GitHub fourni)
- **STT/TTS :** module existant (déjà développé, à intégrer)
- **Email :** SMTP ou service transactionnel (SendGrid, Mailgun)
- **Frontend :** React + Tailwind

---

## 1.7 Hors Périmètre (pour ce hackathon)

- Authentification des administrateurs (auth basique suffit pour la démo)
- Multi-langue dans l'entretien (une seule langue par session)
- Application mobile
- Intégration avec des systèmes RH externes
- Archivage légal des enregistrements vidéo

---

---

# PARTIE 2 — PLAN D'IMPLÉMENTATION

---

## 2.1 Architecture Globale

```
┌─────────────────────────────────────────────────────────┐
│                    DOCTOR PORTAL (React)                 │
│   Submission Form → Status Page → Interview Page        │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────┐
│                   FASTAPI (main.py)                      │
│   /submit  /status/{id}  /interview/{token}  /verdict   │
└──────┬──────────────────────────────────────────────────┘
       │ Celery task
┌──────▼──────────────────────────────────────────────────┐
│              BACKGROUND PIPELINE WORKER                  │
│                                                         │
│  [Pipeline A] → [Pipeline B] → [Scraper] → [RAG Ingest]│
│        ↓              ↓            ↓             ↓      │
│   OCR JSON      Stamp verdict   Web data    ChromaDB    │
│                                                         │
│                   → Email sent                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              INTERVIEW SESSION (on demand)               │
│                                                         │
│  ChromaDB retrieval → Question generation               │
│       ↓                                                 │
│  [STT] ← doctor voice      [Expression thread]          │
│  [TTS] → question audio    OpenCV + DeepFace            │
│       ↓                          ↓                      │
│   QA log ←────────────── Expression log                 │
│       ↓                                                 │
│  [Approval Engine] → verdict                            │
└─────────────────────────────────────────────────────────┘
```

---

## 2.2 Structure du Projet

```
/project
│
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── schemas.py               # All Pydantic models
│   ├── database.py              # SQLite for job/token tracking
│   ├── email_service.py         # Email sending logic
│   │
│   ├── pipelines/
│   │   ├── pdf_converter.py     # PDF → images (pdf2image)
│   │   ├── classifier.py        # Document type classification
│   │   ├── pipeline_a.py        # OCR extraction via Claude Vision
│   │   └── pipeline_b.py        # Diploma visual check via Claude Vision
│   │
│   ├── scraper/
│   │   └── scraper_agent.py     # Playwright + BeautifulSoup web scraper
│   │
│   ├── rag/
│   │   ├── ingestor.py          # Merge → chunk → embed → ChromaDB
│   │   └── retriever.py         # ChromaDB query wrapper
│   │
│   ├── interview/
│   │   ├── session.py           # Agent conversation loop
│   │   ├── question_generator.py # Generate questions from context
│   │   ├── answer_grader.py     # Grade responses via Claude
│   │   └── expression_wrapper.py # DeepFace thread adapter
│   │
│   ├── approval/
│   │   └── engine.py            # Weighted scoring + verdict
│   │
│   └── worker/
│       └── tasks.py             # Celery task definitions
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── SubmissionForm.jsx
    │   │   ├── StatusPage.jsx
    │   │   ├── InterviewPage.jsx
    │   │   └── AdminDashboard.jsx
    │   └── components/
    │       ├── VerdictCard.jsx
    │       ├── EmotionChart.jsx
    │       └── QATranscript.jsx
```

---

## 2.3 Schémas de Données (Contrats Inter-Modules)

Tous les échanges entre modules sont typés. Aucun module ne passe un `dict` brut à un autre.

### Candidat (entrée portail)
```
DoctorSubmission
  ├── doctor_id       : UUID (généré à la soumission)
  ├── name            : str
  ├── email           : str
  ├── specialty       : str
  ├── declared_univ   : str
  └── document_paths  : list[str]
```

### Sortie Pipeline A
```
PipelineAResult
  ├── doctor_id       : str
  ├── name            : str
  ├── university      : str | None
  ├── graduation_year : int | None
  ├── jobs            : list[JobEntry]
  │     ├── employer  : str
  │     ├── role      : str
  │     ├── start     : str (YYYY-MM)
  │     └── end       : str (YYYY-MM | "present")
  ├── raw_text        : str
  └── ocr_confidence  : float (0–1)
```

### Sortie Pipeline B
```
PipelineBResult
  ├── doctor_id       : str
  ├── structure_match : bool
  ├── stamp_present   : bool
  ├── dean_name       : str | None
  ├── dean_verified   : "true" | "false" | "unknown"
  └── flags           : list[str]
```

### Rapport Scraper
```
ScraperReport
  ├── doctor_id               : str
  ├── university_confirmed    : bool
  ├── faculty_names           : list[str]
  ├── hospital_staff_confirmed: bool
  ├── course_catalogue_match  : bool | None
  └── scraper_flags           : list[str]
```

### Entrée Q&A Log
```
QAEntry
  ├── question_id   : str
  ├── question_text : str
  ├── answer_text   : str
  ├── correct       : bool
  ├── category      : "factual" | "experiential" | "knowledge"
  └── timestamp_ms  : int
```

### Entrée Expression Log
```
ExpressionEntry
  ├── question_id : str
  ├── label       : str  (angry|disgust|fear|happy|sad|surprise|neutral)
  ├── confidence  : float
  └── timestamp_ms: int
```

### Verdict Final
```
ApprovalVerdict
  ├── doctor_id    : str
  ├── verdict      : "approved" | "flagged" | "rejected"
  ├── score        : float
  ├── breakdown    : { doc: float, interview: float, expression: float }
  ├── flags        : list[str]
  └── reviewed_by  : str | None
```

---

## 2.4 Module par Module

---

### MODULE 1 — Portail de Soumission

**Responsabilité :** Recevoir les données et documents du médecin, déclencher le pipeline, retourner un ID de suivi.

**Endpoints FastAPI :**
```
POST  /submit           → reçoit form + fichiers, crée doctor_id, lance Celery task
GET   /status/{id}      → retourne l'état courant du pipeline pour ce doctor_id
```

**États du pipeline (stockés en SQLite) :**
```
pending → processing_a → processing_b → scraping → ingesting → ready_for_interview → interview_done → verdict_ready
```

**Décisions de conception :**
- Les fichiers uploadés sont sauvegardés dans `/uploads/{doctor_id}/` sur le serveur
- Le `doctor_id` est un UUID v4 généré à la soumission
- La page de statut fait un polling toutes les 5 secondes sur `GET /status/{id}`

---

### MODULE 2 — Pipeline A (Extraction OCR)

**Responsabilité :** Lire le contenu textuel de chaque document et extraire les champs structurés.

**Étapes internes :**
1. Si PDF → convertir chaque page en image JPEG 300 DPI via `pdf2image`
2. Classifier le document (diplôme / lettre / certificat / autre) en envoyant l'image à Claude Vision
3. Pour chaque document, envoyer l'image à Claude Vision avec le prompt d'extraction structurée
4. Parser la réponse JSON, valider avec Pydantic, calculer `ocr_confidence`
5. Si `ocr_confidence < 0.7` : ajouter flag `low_confidence_ocr` mais continuer

**Prompt Claude (Pipeline A) :**
```
Analyse cette image de document médical.
Extrais les informations suivantes en JSON strict, sans texte autour :
{
  "name": "...",
  "university": "... ou null",
  "graduation_year": ... ou null,
  "jobs": [{"employer":"...","role":"...","start":"YYYY-MM","end":"YYYY-MM ou present"}],
  "document_type": "diploma|job_letter|certificate|other",
  "raw_text": "texte intégral du document",
  "extraction_quality": 0.0 à 1.0
}
```

**Sortie :** `PipelineAResult` sauvegardée dans `/data/{doctor_id}/pipeline_a.json`

---

### MODULE 3 — Pipeline B (Vérification Visuelle Diplôme)

**Responsabilité :** Vérifier l'authenticité visuelle du diplôme — structure, tampon, doyen.

**Déclenché uniquement sur les documents classifiés `diploma` par Pipeline A.**

**Prompt Claude (Pipeline B) :**
```
Analyse ce diplôme pour des signaux d'authenticité.
Retourne un JSON strict :
{
  "structure_match": true/false,
  "stamp_present": true/false,
  "stamp_legible": true/false,
  "dean_name": "nom extrait du tampon ou null",
  "flags": ["liste d'anomalies : ex. low_contrast_stamp, missing_signature, font_inconsistency"]
}

Critères pour structure_match=true : présence d'un en-tête institutionnel,
corps avec nom du diplômé et spécialité, date d'obtention, zone de signatures.
```

**Règle `dean_verified` :**
- `true` → `dean_name` matche à 85%+ un nom de la liste scrapée avec rôle doyen/recteur
- `false` → nom trouvé mais pas dans ce rôle, ou complètement absent
- `unknown` → scraper n'a pas pu accéder au répertoire de l'université

**Sortie :** `PipelineBResult` sauvegardée dans `/data/{doctor_id}/pipeline_b.json`

---

### MODULE 4 — Scraper Agent

**Responsabilité :** Vérifier l'existence de l'université, récupérer les noms de la faculté, valider les employeurs hospitaliers.

**Déclenchement :** après Pipeline A (nécessite `university` et `jobs`)

**Sources scrapées :**
- Site officiel de l'université déclarée → répertoire enseignants/faculté
- Pages institutionnelles → localisation, informations société
- Catalogue des cours par année académique
- Sites des hôpitaux employeurs → listes du personnel

**Gestion des erreurs :**
- Timeout 30s par URL → `unknown`, continuer
- Site nécessitant JS → `playwright` headless
- 404 ou CAPTCHA → flag `scraper_failed`, `unknown`

**Cache :** résultats stockés 30 jours dans `/cache/scraper/{university_slug}.json`

**Fuzzy matching doyen :**
```python
from rapidfuzz import fuzz
match_score = fuzz.token_sort_ratio(dean_name_from_stamp, faculty_name)
# dean_verified = "true" si score > 85 ET rôle contient "doyen|recteur|dean"
```

**Sortie :** `ScraperReport` sauvegardée dans `/data/{doctor_id}/scraper.json`

---

### MODULE 5 — Ingestion RAG

**Responsabilité :** Fusionner toutes les données, chunker, encoder, stocker dans ChromaDB.

**Étapes :**
1. Charger `pipeline_a.json` + `pipeline_b.json` + `scraper.json`
2. Construire 4 chunks textuels :
   - `personal` : nom, université, année, spécialité
   - `verdicts` : structure_match, stamp, dean_verified, flags
   - `jobs` : liste formatée des postes
   - `scraper_data` : noms de faculté, confirmation uni/hôpital, catalogue
3. Encoder chaque chunk avec `all-MiniLM-L6-v2`
4. Insérer dans ChromaDB, collection `doctor_{id}`
5. Marquer le statut `ready_for_interview` en base
6. **Déclencher l'envoi d'email**

**Structure ChromaDB :**
```
Collection: doctor_{id}
Documents:
  id: "doctor_{id}::personal"    → chunk personal
  id: "doctor_{id}::verdicts"    → chunk verdicts
  id: "doctor_{id}::jobs"        → chunk jobs
  id: "doctor_{id}::scraper"     → chunk scraper_data
Metadata sur chaque doc:
  doctor_id, chunk_type, ingested_at
```

---

### MODULE 6 — Email de Notification

**Responsabilité :** Envoyer l'email avec le lien d'entretien unique et sécurisé.

**Token d'entretien :**
- UUID v4 stocké en base avec : `doctor_id`, `created_at`, `expires_at` (+72h), `used: false`
- Lien : `https://app.example.com/interview/{token}`

**Contenu email :**
```
Objet : Votre entretien de vérification est prêt

Bonjour [Nom],

Votre dossier a été traité. Vous pouvez maintenant passer votre entretien
de vérification en cliquant sur le lien ci-dessous :

[Lien d'entretien]

Ce lien est valable 72 heures. Assurez-vous d'être dans un endroit calme
avec une bonne connexion internet et votre webcam activée.

Durée estimée : 15-20 minutes.
```

---

### MODULE 7 — Session d'Entretien

**Responsabilité :** Conduire l'entretien en temps réel avec voix + détection d'émotions.

**Trois threads parallèles, synchronisés par `active_question_id` :**

#### Thread Principal — Agent Conversation
```
1. Charger tous les chunks ChromaDB du candidat
2. Générer une banque de 10 questions via Claude :
   - 4 questions factuelles (qui était votre doyen, cours suivis)
   - 3 questions expérientielles (décrivez votre stage à [hôpital])
   - 3 questions de connaissance médicale (selon spécialité déclarée)
3. Pour chaque question :
   a. Mettre à jour active_question_id
   b. TTS → poser la question à voix haute
   c. STT → écouter et transcrire la réponse
   d. Claude → évaluer si la réponse est correcte (avec contexte ChromaDB)
   e. Logger dans qa_log
4. À la fin → générer le rapport d'entretien
```

#### Thread Expression — Adaptateur DeepFace
```python
# Adaptation directe du repo GitHub
# Changements par rapport à l'original :
# 1. Ne pas afficher la fenêtre OpenCV (headless)
# 2. Lire active_question_id depuis variable partagée
# 3. Appender dans expression_log au lieu d'afficher

class ExpressionStream:
    def __init__(self):
        self.active_question_id = None
        self.log = []
        self._running = False

    def _loop(self):
        cap = cv2.VideoCapture(0)
        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            try:
                result = DeepFace.analyze(
                    frame,
                    actions=["emotion"],
                    enforce_detection=False,  # CRITIQUE : ne pas crasher si pas de visage
                    silent=True
                )
                label = result[0]["dominant_emotion"]
                conf = result[0]["emotion"][label] / 100
                if self.active_question_id:
                    self.log.append(ExpressionEntry(
                        question_id=self.active_question_id,
                        label=label,
                        confidence=conf,
                        timestamp_ms=int(time.time() * 1000)
                    ))
            except Exception:
                pass  # Frame ratée → ignorer silencieusement
            time.sleep(0.5)  # 2 fps suffisent
        cap.release()
```

**Labels "stress" pour le moteur d'approbation :** `fear`, `angry`, `disgust`

#### Rapport d'Entretien (sortie)
```
InterviewReport
  ├── doctor_id      : str
  ├── qa_log         : list[QAEntry]
  ├── expression_log : list[ExpressionEntry]
  ├── accuracy_score : float  (bonnes réponses / total)
  └── completed_at   : datetime
```

---

### MODULE 8 — Moteur d'Approbation

**Responsabilité :** Calculer le verdict final à partir des trois signaux.

#### Calcul du score documentaire (50% du total)

| Critère | Points |
|---|---|
| `structure_match = true` | 0.30 |
| `dean_verified = true` | 0.20 |
| `dean_verified = unknown` | 0.10 |
| `university_confirmed = true` | 0.20 |
| `hospital_staff_confirmed = true` | 0.20 |
| `course_catalogue_match = true` | 0.10 |

#### Calcul du score d'entretien (35% du total)
```
interview_score = nombre_correctes / nombre_total_questions
```

#### Calcul du score émotionnel (15% du total)
```
questions_factuelles = {q.question_id for q in qa_log if q.category == "factual"}
events_stress = [e for e in expression_log
                 if e.question_id in questions_factuelles
                 and e.label in {"fear", "angry", "disgust"}
                 and e.confidence > 0.6]

ratio_stress = len(events_stress) / max(len(questions_factuelles) * 4, 1)
expression_score = max(0.0, 1.0 - ratio_stress * 2)
```

#### Règles de verdict

```
score_final = (doc_score × 0.50) + (interview_score × 0.35) + (expression_score × 0.15)

flags_critiques = {"dean_not_verified", "multiple_structure_failures", "forged_stamp_suspected"}

SI score_final ≥ 0.75 ET aucun flag_critique → APPROUVÉ
SI score_final ≥ 0.45 OU (score_final ≥ 0.35 ET len(flags) ≤ 2) → FLAGUÉ
SINON → REJETÉ
```

---

### MODULE 9 — Tableau de Bord Admin

**Pages :**

1. **Liste candidats** — tableau avec colonnes : nom, date soumission, statut pipeline, verdict, score
2. **Détail candidat** — vue complète :
   - Résumé scores (3 barres : doc / entretien / émotions)
   - Liste des flags avec explication
   - Transcription Q&A avec indicateur correct/incorrect
   - Graphique d'émotions : axe X = questions, axe Y = % stress
3. **File de révision** — pour les cas "flagué" uniquement :
   - Boutons : Approuver / Rejeter / Demander re-entretien
   - Champ commentaire obligatoire

---

## 2.5 Endpoints API Complets

```
POST  /submit                      → Soumission dossier + upload fichiers
GET   /status/{doctor_id}          → État pipeline (polling)

GET   /interview/{token}           → Valider le token, retourner doctor_id
POST  /interview/{token}/start     → Démarrer la session
POST  /interview/{token}/answer    → Recevoir une réponse STT transcrite
GET   /interview/{token}/question  → Récupérer la prochaine question (texte + audio)

GET   /admin/doctors               → Liste tous les candidats
GET   /admin/doctors/{id}          → Détail d'un candidat
GET   /admin/review                → File de révision (flagués seulement)
POST  /admin/review/{id}/decision  → Décision manuelle (approved/rejected/re-interview)
GET   /admin/export/csv            → Export CSV verdicts
```

---

## 2.6 Plan de Sprint 36h

### H0 → H3 : Fondations
- Créer la structure du projet
- Écrire `schemas.py` (tous les modèles Pydantic)
- Setup FastAPI + SQLite + ChromaDB
- Setup Celery + Redis
- Vérifier que l'API Anthropic répond

### H3 → H7 : Pipeline A + B
- `pdf_converter.py` — conversion PDF → images
- `pipeline_a.py` — prompt Claude Vision + parsing JSON
- `pipeline_b.py` — prompt Claude Vision diplôme
- Test avec de vrais documents

### H7 → H10 : Scraper + RAG
- `scraper_agent.py` — Playwright, 3 sources prioritaires
- `ingestor.py` — fusion, chunking, embedding, ChromaDB
- Test end-to-end pipeline complet

### H10 → H11 : Email
- `email_service.py` — génération token + envoi email
- Test du lien reçu

### H11 → H18 : Session d'entretien (bloc le plus long)
- `question_generator.py` — prompt Claude depuis ChromaDB
- `answer_grader.py` — évaluation réponse via Claude
- `expression_wrapper.py` — adapter le repo GitHub
- `session.py` — orchestration 3 threads
- Intégrer le module STT/TTS existant
- Test session complète

### H18 → H21 : Moteur d'approbation
- `engine.py` — scoring complet
- Tests avec différents scénarios (bon candidat, candidat frauduleux)

### H21 → H27 : Frontend React
- Page soumission
- Page statut (polling)
- Page entretien (webcam + question audio)
- Dashboard admin (liste + détail + verdict)

### H27 → H32 : Intégration et bugs
- Wirer tous les modules ensemble
- Fixer les bugs d'intégration
- Données de démo seed

### H32 → H34 : Polish démo
- Préparer un dossier médecin fictif complet
- S'assurer que le flux de bout en bout tourne sans erreur
- Page verdict visuellement propre

### H34 → H36 : Buffer + README + pitch

---

## 2.7 Risques et Mitigations

| Risque | Probabilité | Mitigation |
|---|---|---|
| DeepFace télécharge 500 MB au premier run | Haute | Pré-télécharger avant le hackathon |
| Scraper bloqué par anti-bot | Moyenne | Fallback `unknown`, ne pas bloquer le pipeline |
| Latence STT/TTS trop haute | Moyenne | Tester le module existant isolément en H0 |
| Claude Vision retourne du JSON malformé | Faible | Wrapper try/catch + retry une fois |
| ChromaDB corrompu après crash | Faible | Sauvegarder après chaque ingestion |

---

## 2.8 Ordre de Coupures si Retard

Si le temps manque, couper dans cet ordre (du moins impactant au plus) :

1. **Couper le scraper** → remplacer par `ScraperReport` mockée avec `university_confirmed: true`
2. **Couper la détection d'émotions** → `expression_score` fixé à 0.8 par défaut, mentionner "module disponible"
3. **Couper la voix** → entretien texte uniquement dans le UI
4. **Couper le dashboard admin** → montrer les résultats via `GET /admin/doctors/{id}` en JSON brut
5. **Ne jamais couper** → la page de soumission + la page de verdict. C'est la démo.

---

*Document produit pour hackathon 36h — Dr. Verification Platform*

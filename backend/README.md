# Trusty - Doctor Credential Verification Pipeline

End-to-end AI pipeline that verifies doctor credentials from uploaded documents, runs web verification, and conducts a short voice interview with expression monitoring. Designed for hackathon/demo workflows with Supabase-backed orchestration.

## What It Does
- Converts PDFs to images, runs OCR, and extracts structured profile data
- Verifies claims via web research (Perplexity Sonar through OpenRouter)
- Generates survey questions and runs a 3-turn interview (NVIDIA API)
- Logs facial expressions during interview (DeepFace + webcam)
- Writes final verdict reports and optionally syncs to Supabase

## Quickstart (Local Demo)
1) Activate a bundled virtual environment if you want (optional):
   - PowerShell: .\.venv\Scripts\Activate.ps1
2) Install dependencies (if not already installed in the venv):
   - pip install -r requirements.txt
3) Ensure .env is present (this repo includes it). Update keys if needed.
4) Run a preflight check:
   - run_preflight_check.cmd
5) Run the demo pipeline:
   - run_pipeline_good.cmd

## Supabase Mode (Backend Worker)
- Run document extraction worker:
  - python main_supabase.py
- Run interview worker:
  - python interview_supabase.py
- Run full worker loop:
  - python supabase_worker.py

Supabase requires the schema in supabase_schema.sql and a public storage bucket named "documents".

## Key Scripts
- main.py: end-to-end local pipeline
- main_supabase.py: Supabase polling for document analysis jobs
- interview_supabase.py: Supabase polling for interview jobs
- supabase_worker.py: combined loop for extraction + evaluation
- tools\preflight_check.py: local environment readiness check
- tools\expression_monitor.py: standalone webcam expression monitor
- test_apis.py: quick API connectivity checks (update keys if needed)

## Environment Variables
The pipeline reads these keys from .env:
- NVIDIA_API_KEY
- NVIDIA_BASE_URL
- OPENROUTER_API_KEY
- OPENROUTER_BASE_URL
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_SERVICE_KEY
- CHROMA_DB_PATH, IMAGES_DIR, PROFILES_DIR, TRANSCRIPTS_DIR, REPORTS_DIR

## API Setup Guide
See API_SETUP.md for step-by-step instructions for NVIDIA, OpenRouter, and Supabase.

## Notes
- DeepFace downloads model weights on first run and may take several minutes.
- The interview uses real audio when available; otherwise it falls back to typed input.
- This project is intended for demos/hackathons, not production.

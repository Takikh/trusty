# API Setup Guide

This guide walks through getting all external APIs configured for this project.

## 1) NVIDIA API (LLM + OCR)
Used in:
- OCR and document extraction
- Survey question generation
- Live interview question generation

Steps:
1. Create an NVIDIA developer account.
2. Go to the NVIDIA API catalog and generate an API key for NVIDIA Inference.
3. Set these values in .env:
   - NVIDIA_API_KEY=your_key
   - NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
4. Optional model overrides in .env:
   - NVIDIA_SURVEY_MODEL=meta/llama-3.3-70b-instruct
   - NVIDIA_INTERVIEW_MODEL=meta/llama-3.3-70b-instruct

Common models used:
- nvidia/nemotron-ocr-v1 (OCR)
- meta/llama-3.3-70b-instruct (survey + interview)

## 2) OpenRouter (Perplexity Sonar Web Search)
Used in:
- pipeline/web_verifier.py for live web verification

Steps:
1. Create an OpenRouter account and add credits.
2. Generate an API key.
3. Set these values in .env:
   - OPENROUTER_API_KEY=your_key
   - OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
4. The model used is:
   - perplexity/sonar

## 3) Supabase (Storage + REST API)
Used in:
- main_supabase.py, interview_supabase.py, supabase_worker.py

Steps:
1. Create a new Supabase project.
2. Copy the project URL and keys:
   - SUPABASE_URL=https://<project-ref>.supabase.co
   - SUPABASE_KEY=anon_key
   - SUPABASE_SERVICE_KEY=service_role_key
3. Open the Supabase SQL editor and run supabase_schema.sql.
4. Create a public storage bucket named documents.
5. (Optional) Upload documents to storage and insert doctors into the doctors table.

## 4) Local Models and Hardware
These are not external APIs, but required for a full demo:
- faster-whisper will download the model on first run.
- DeepFace will download face model weights on first run.
- Kokoro-ONNX model is included in audio/tts_kokoro/kokoro-v1.0.onnx.
- Webcam and microphone access are required for expression monitoring and live audio.

## 5) Quick API Connectivity Test
Update keys in test_apis.py if needed, then run:
- python test_apis.py

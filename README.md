# Trusty 🩺 — AI-Powered Doctor Verification Pipeline

![Trusty Banner](assets/banner.png)

> **Trusty** is a state-of-the-art, end-to-end verification platform designed to validate medical credentials using advanced Vision AI, real-time web search, and voice-driven behavioral analysis.

---

## 🌟 Key Features

- **📄 Intelligent Document Processing**: Automatic classification and OCR of diplomas, licenses, and job letters using **Llama 3.2 Vision** and **Nemotron OCR**.
- **🌐 Real-time Web Verification**: Live verification of universities and hospitals through **Perplexity Sonar** (Web Search LLM).
- **🎙️ Conversational Voice Interview**: An AI-led interview that probes doctor's expertise and consistency using **Faster-Whisper** (STT) and **Kokoro** (TTS).
- **🎭 Behavioral Stress Detection**: Real-time analysis of facial expressions during interviews using **DeepFace** to detect stress or anomalies.
- **📊 Unified Verification Score**: A weighted scoring system that combines document validity, interview performance, and behavioral signals into a final report.

---

## 🏗️ Architecture & Tech Stack

### Backend
- **Framework**: Python / FastAPI
- **Database**: Supabase (User Auth & Data)
- **Vector DB**: ChromaDB (RAG for interview context)
- **AI Models**:
  - `llama-3.2-90b-vision-instruct` (Extraction)
  - `nemotron-ocr-v1` (OCR)
  - `perplexity/sonar` (Web Verification)
  - `faster-whisper` (STT)
  - `kokoro-onnx` (TTS)
  - `deepface` (Emotion Analysis)

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS
- **Interactions**: Framer Motion for premium animations

---

## 📂 Project Structure

```text
hackathon/
├── backend/                # FastAPI logic & AI Pipeline
│   ├── pipeline/           # Individual pipeline steps (OCR, Extractor, etc.)
│   ├── api_server.py       # Main API entry point
│   └── main.py             # Pipeline Orchestrator
├── front/                  # React + Vite Frontend
│   └── vaas/               # Identity Verification as a Service (VaaS)
├── assets/                 # Brand assets & documentation images
└── README.md               # You are here
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- NVIDIA API Key
- OpenRouter API Key

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd front/vaas
npm install
npm run dev
```

### 4. Configuration
Create a `.env` file in the `backend/` directory based on the `BUILD_PLAN.md`:
```env
OPENROUTER_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

---

## 🛠️ Verification Workflow

1. **Upload**: Doctor uploads PDF credentials.
2. **Scan**: Pipeline extracts structured data and flags anomalies.
3. **Verify**: System searches the web to confirm institution legitimacy.
4. **Interview**: Doctor undergoes a 3-minute voice interview.
5. **Report**: A final JSON/PDF report is generated with a "VERIFIED" or "REJECTED" status.

---

## 🛡️ Security & Privacy
- All API keys are managed via environment variables.
- PII is handled securely and can be purged upon request.
- Models like Whisper and Kokoro are run locally to ensure voice data privacy.

---

## 👥 Contributors
Developed with ❤️ during the **Hackathon 2026**.

---
*Built by Takikh & the Trusty Team.*

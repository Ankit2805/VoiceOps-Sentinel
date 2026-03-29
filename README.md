# 🎙️ VoiceOps Sentinel

> **Real-Time Call Intelligence System** — Automatically transcribe, diarize, redact PII, and extract actionable insights from customer support calls using state-of-the-art AI.

---

## 📌 Overview

**VoiceOps Sentinel** is a production-grade AI pipeline built to transform raw call center audio into structured, actionable intelligence — in real time.

Customer support teams struggle with low QA coverage, PII compliance risks, and slow agent feedback loops. VoiceOps Sentinel solves all three by automatically:

- 🎙️ **Transcribing** calls using OpenAI Whisper (ASR)
- 👥 **Separating** Agent and Customer voices via speaker diarization
- 🔒 **Redacting** sensitive PII (names, phone numbers, credit cards) before storage
- 🧠 **Analyzing** each call for summary, sentiment shifts, and follow-up action items
- 📊 **Presenting** everything in an interactive Streamlit dashboard

Built with **Python · FastAPI · Whisper · Pyannote · SpaCy · Presidio · Streamlit**.

---

## ✨ Features

| Feature | Technology | Description |
|--------|-----------|-------------|
| 🎙️ Speech-to-Text | OpenAI Whisper | High-accuracy ASR with word-level timestamps |
| 👥 Speaker Diarization | Pyannote Audio 3.1 | Labels Agent (A) vs Customer (B) turns |
| 🔒 PII Redaction | Microsoft Presidio + SpaCy | Auto-scrubs names, phones, cards, emails |
| 🧠 Call Intelligence | GPT-4o-mini | Summary, sentiment, action items, agent score |
| 📊 Dashboard | Streamlit | Dark UI with audio player + synced transcript |
| ⚡ Async Pipeline | FastAPI | Background job queue with real-time progress |

---

## 🗂️ Project Structure

```
voiceops_sentinel/
├── backend/
│   ├── main.py                  # FastAPI app + async job queue
│   └── pipeline/
│       ├── transcriber.py       # Week 1: Whisper ASR
│       ├── intelligence.py      # Week 2: GPT summarization + sentiment
│       ├── diarizer.py          # Week 3: Pyannote diarization
│       └── pii_redactor.py      # Week 3: Presidio PII redaction
├── frontend/
│   └── dashboard.py             # Week 4: Streamlit dashboard
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- [ffmpeg](https://ffmpeg.org/) installed on your system

Install ffmpeg on Windows:
```bash
winget install ffmpeg
```

---

### Step 1 — Clone the repository
```bash
git clone https://github.com/your-username/voiceops-sentinel.git
cd voiceops-sentinel
```

---

### Step 2 — Create and activate a virtual environment
```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

> ✅ You should see `(venv)` at the start of your terminal line.

---

### Step 3 — Upgrade pip and core tools
```bash
python -m pip install --upgrade pip setuptools wheel
```

---

### Step 4 — Install dependencies
```bash
pip install fastapi uvicorn python-multipart streamlit requests openai python-dotenv spacy
```

Then download the SpaCy language model:
```bash
python -m spacy download en_core_web_sm
```

---

### Step 5 — Set up environment variables
```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```env
OPENAI_API_KEY=sk-your-openai-key-here
HF_TOKEN=hf_your-huggingface-token-here
```

> 💡 **No keys? No problem.** The system runs in **demo mode** with realistic mock data if no keys are provided — great for testing the UI.

---

## ▶️ Running the App

You need **two terminals** — both with the virtual environment activated.

### Terminal 1 — Start the FastAPI Backend
```bash
venv\Scripts\activate        # Windows
cd backend
uvicorn main:app --reload --port 8000
```
Backend will be live at: `http://localhost:8000`

---

### Terminal 2 — Start the Streamlit Dashboard
```bash
venv\Scripts\activate        # Windows
cd frontend
streamlit run dashboard.py
```
Dashboard will open at: `http://localhost:8501`

---

## 🔑 API Keys

| Key | Required For | Where to Get It |
|-----|-------------|-----------------|
| `OPENAI_API_KEY` | LLM summarization & sentiment | [platform.openai.com](https://platform.openai.com) |
| `HF_TOKEN` | Pyannote speaker diarization | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

> After getting your HuggingFace token, accept the model terms at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload audio file and start pipeline |
| `GET` | `/api/job/{job_id}` | Poll job status and get results |
| `GET` | `/api/jobs` | List all analyzed calls |
| `GET` | `/` | Health check |

---

## 📅 Weekly Milestones

| Week | Feature | Status |
|------|---------|--------|
| Week 1 | Whisper transcription pipeline (mp3 / wav / flac) | ✅ Done |
| Week 2 | LLM intelligence — summary, sentiment, action items | ✅ Done |
| Week 3 | Pyannote diarization + Presidio PII redaction | ✅ Done |
| Week 4 | Streamlit dashboard with audio + transcript sync | ✅ Done |

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| Speech-to-Text | OpenAI Whisper |
| Speaker Diarization | Pyannote Audio 3.1 |
| PII Redaction | Microsoft Presidio + SpaCy |
| LLM Analysis | OpenAI GPT-4o-mini |
| Dashboard | Streamlit |
| Audio Processing | ffmpeg-python |

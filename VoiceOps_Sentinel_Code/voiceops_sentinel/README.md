# 🎙️ VoiceOps Sentinel
### Real-Time Call Intelligence System — Project 4

> **Product Brand:** VoiceOps Sentinel  
> **Stack:** Python · FastAPI · OpenAI Whisper · Pyannote · SpaCy/Presidio · Streamlit

---

## 📁 Project Structure

```
voiceops_sentinel/
├── backend/
│   ├── main.py                  # FastAPI app + job queue
│   └── pipeline/
│       ├── transcriber.py       # Week 1: Whisper ASR
│       ├── diarizer.py          # Week 3: Pyannote diarization
│       ├── pii_redactor.py      # Week 3: Presidio PII redaction
│       └── intelligence.py      # Week 2: GPT summarization + sentiment
├── frontend/
│   └── dashboard.py             # Week 4: Streamlit dashboard
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Set environment variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start the FastAPI backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start the Streamlit dashboard (new terminal)
```bash
cd frontend
streamlit run dashboard.py
```

Open: **http://localhost:8501**

---

## 🔑 API Keys Required

| Key | Purpose | Get It |
|-----|---------|--------|
| `OPENAI_API_KEY` | GPT summarization & sentiment | [platform.openai.com](https://platform.openai.com) |
| `HF_TOKEN` | Pyannote diarization | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

> **Note:** Without these keys, the system runs in **demo mode** with mock data.  
> All core pipeline code is fully functional once keys are provided.

---

## 🏗️ Architecture

```
Audio File (mp3/wav/flac)
        │
        ▼
┌─────────────────────┐
│   FastAPI Backend   │  POST /api/analyze
│   (main.py)         │  GET  /api/job/{id}
└────────┬────────────┘
         │
   Background Task
         │
    ┌────▼────┐
    │ Week 1  │  Whisper ASR → raw transcript + timestamps
    └────┬────┘
    ┌────▼────┐
    │ Week 3a │  Pyannote → Speaker A (Agent) / B (Customer)
    └────┬────┘
    ┌────▼────┐
    │ Week 3b │  Presidio/SpaCy → PII redaction
    └────┬────┘
    ┌────▼────┐
    │ Week 2  │  GPT-4o-mini → Summary + Sentiment + Actions
    └────┬────┘
         │
    ┌────▼────────────────┐
    │  Streamlit Dashboard│  Week 4
    │  (dashboard.py)     │
    └─────────────────────┘
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload audio, start pipeline |
| `GET` | `/api/job/{job_id}` | Poll job status + result |
| `GET` | `/api/jobs` | List all jobs |
| `GET` | `/` | Health check |

---

## 🧪 Testing

```bash
# Test transcription only
python -c "
from backend.pipeline.transcriber import transcribe_audio
transcript, segments = transcribe_audio('sample.wav', model_size='base')
print(transcript)
"

# Test PII redaction only  
python -c "
from backend.pipeline.pii_redactor import redact_pii
segments = [{'text': 'Call John Smith at 555-1234 with card 4111-1111-1111-1111', 'speaker': 'Agent', 'start': 0, 'end': 5}]
redacted, report = redact_pii(segments)
print(redacted[0]['text'])
print(report)
"
```

---

## 📅 Weekly Milestones

| Week | Feature | Status |
|------|---------|--------|
| 1 | Whisper transcription pipeline (mp3/wav/flac) | ✅ |
| 2 | LLM intelligence: summary, sentiment, actions | ✅ |
| 3 | Pyannote diarization + Presidio PII redaction | ✅ |
| 4 | Streamlit dashboard with audio + transcript sync | ✅ |

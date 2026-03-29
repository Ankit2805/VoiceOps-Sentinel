"""
VoiceOps Sentinel - Real-Time Call Intelligence System
FastAPI Backend
"""

import os
import uuid
import json
import time
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pipeline.transcriber import transcribe_audio
from pipeline.diarizer import diarize_audio
from pipeline.pii_redactor import redact_pii
from pipeline.intelligence import analyze_transcript

app = FastAPI(
    title="VoiceOps Sentinel API",
    description="Real-Time Call Intelligence System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (use Redis/DB in production)
job_store: dict = {}


class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | processing | done | error
    progress: int  # 0-100
    result: Optional[dict] = None
    error: Optional[str] = None


@app.get("/")
def root():
    return {"service": "VoiceOps Sentinel", "version": "1.0.0", "status": "running"}


@app.post("/api/analyze", response_model=JobStatus)
async def analyze_call(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload an audio file and start the analysis pipeline."""
    allowed_types = {"audio/mpeg", "audio/wav", "audio/flac", "audio/x-wav", "audio/mp3"}
    allowed_exts = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}

    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use mp3, wav, or flac.")

    job_id = str(uuid.uuid4())

    # Save uploaded file to temp location
    tmp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(tmp_dir, f"call_{job_id}{ext}")
    with open(audio_path, "wb") as f:
        content = await file.read()
        f.write(content)

    job_store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "result": None,
        "error": None,
        "audio_path": audio_path,
    }

    background_tasks.add_task(run_pipeline, job_id, audio_path)

    return JobStatus(**{k: v for k, v in job_store[job_id].items() if k != "audio_path"})


@app.get("/api/job/{job_id}", response_model=JobStatus)
def get_job(job_id: str):
    """Poll job status and result."""
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    job = job_store[job_id]
    return JobStatus(**{k: v for k, v in job.items() if k != "audio_path"})


@app.get("/api/jobs")
def list_jobs():
    """List all jobs."""
    return [
        {k: v for k, v in job.items() if k != "audio_path"}
        for job in job_store.values()
    ]


def run_pipeline(job_id: str, audio_path: str):
    """Full analysis pipeline: Transcribe → Diarize → Redact PII → Analyze."""
    try:
        job_store[job_id]["status"] = "processing"

        # Step 1: Transcription (Whisper)
        job_store[job_id]["progress"] = 10
        raw_transcript, segments = transcribe_audio(audio_path)

        # Step 2: Diarization (Pyannote)
        job_store[job_id]["progress"] = 35
        diarized_segments = diarize_audio(audio_path, segments)

        # Step 3: PII Redaction (SpaCy / Presidio)
        job_store[job_id]["progress"] = 55
        redacted_transcript, pii_report = redact_pii(diarized_segments)

        # Step 4: Intelligence Layer (LLM)
        job_store[job_id]["progress"] = 75
        intelligence = analyze_transcript(redacted_transcript)

        # Step 5: Package results
        job_store[job_id]["progress"] = 95
        result = {
            "job_id": job_id,
            "audio_file": os.path.basename(audio_path),
            "raw_transcript": raw_transcript,
            "diarized_segments": diarized_segments,
            "redacted_transcript": redacted_transcript,
            "pii_report": pii_report,
            "intelligence": intelligence,
        }

        job_store[job_id]["status"] = "done"
        job_store[job_id]["progress"] = 100
        job_store[job_id]["result"] = result

    except Exception as e:
        job_store[job_id]["status"] = "error"
        job_store[job_id]["error"] = str(e)
        raise

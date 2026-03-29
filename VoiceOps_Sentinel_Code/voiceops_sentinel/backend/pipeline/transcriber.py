"""
Week 1 - Transcription Pipeline
Uses OpenAI Whisper for robust ASR.
Handles mp3, wav, flac input formats.
"""

import whisper
import numpy as np
from typing import Tuple, List, Dict


def transcribe_audio(audio_path: str, model_size: str = "base") -> Tuple[str, List[Dict]]:
    """
    Transcribe audio file using OpenAI Whisper.

    Args:
        audio_path: Path to audio file (mp3, wav, flac)
        model_size: Whisper model size - tiny | base | small | medium | large
                    Use 'large' for best accuracy (slower).
                    Use 'base' for faster processing with acceptable WER.

    Returns:
        raw_transcript: Full transcript string
        segments: List of {start, end, text} dicts with timestamps
    """
    print(f"[Transcriber] Loading Whisper model: {model_size}")
    model = whisper.load_model(model_size)

    print(f"[Transcriber] Transcribing: {audio_path}")
    result = model.transcribe(
        audio_path,
        verbose=False,
        word_timestamps=True,   # needed for fine-grained diarization sync
        task="transcribe",
        language="en",
    )

    raw_transcript = result["text"].strip()

    segments = []
    for seg in result["segments"]:
        segments.append({
            "id": seg["id"],
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
            "words": seg.get("words", []),
            "avg_logprob": seg.get("avg_logprob", 0),   # confidence metric → WER proxy
            "no_speech_prob": seg.get("no_speech_prob", 0),
        })

    print(f"[Transcriber] Done. {len(segments)} segments, {len(raw_transcript.split())} words.")
    return raw_transcript, segments


def compute_wer_estimate(segments: List[Dict]) -> Dict:
    """
    Estimate Word Error Rate (WER) proxy using Whisper's avg_logprob.
    A logprob > -0.3 is high confidence; < -1.0 suggests poor audio quality.

    Returns a quality report dict.
    """
    if not segments:
        return {"estimated_quality": "unknown", "avg_logprob": None}

    probs = [s["avg_logprob"] for s in segments if s["avg_logprob"] is not None]
    avg = np.mean(probs) if probs else -999

    if avg > -0.3:
        quality = "excellent"
    elif avg > -0.5:
        quality = "good"
    elif avg > -0.8:
        quality = "fair"
    else:
        quality = "poor"

    return {
        "estimated_quality": quality,
        "avg_logprob": round(float(avg), 4),
        "num_segments": len(segments),
        "note": "Use Whisper 'large' model for noisy calls to improve WER."
    }

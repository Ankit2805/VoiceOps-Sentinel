"""
Week 3 - Diarization Pipeline
Uses Pyannote.audio to label Speaker A (Agent) and Speaker B (Customer).
Merges Whisper segments with Pyannote speaker turns.
"""

from typing import List, Dict, Tuple
import os


def diarize_audio(audio_path: str, whisper_segments: List[Dict]) -> List[Dict]:
    """
    Perform speaker diarization using Pyannote.audio.

    Labels each transcript segment as:
      - SPEAKER_A → "Agent"
      - SPEAKER_B → "Customer"

    Args:
        audio_path:       Path to audio file
        whisper_segments: Segments from transcriber.py

    Returns:
        diarized_segments: Each segment enriched with 'speaker' field.

    NOTE:
        Pyannote requires a HuggingFace token with access to:
        pyannote/speaker-diarization-3.1
        Set HF_TOKEN environment variable before running.
    """
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("[Diarizer] WARNING: HF_TOKEN not set. Using mock diarization.")
        return _mock_diarize(whisper_segments)

    try:
        from pyannote.audio import Pipeline
        import torch

        print("[Diarizer] Loading pyannote speaker-diarization-3.1 ...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipeline = pipeline.to(torch.device(device))
        print(f"[Diarizer] Running on: {device}")

        diarization = pipeline(audio_path, num_speakers=2)

        # Build speaker turn timeline
        speaker_turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_turns.append({
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
                "speaker_raw": speaker,
            })

        # Map pyannote speaker IDs → Agent / Customer
        speaker_map = _build_speaker_map(speaker_turns)

        # Merge: assign speaker to each Whisper segment
        diarized = []
        for seg in whisper_segments:
            seg_mid = (seg["start"] + seg["end"]) / 2
            speaker_raw = _find_speaker_at(seg_mid, speaker_turns)
            speaker_label = speaker_map.get(speaker_raw, "Unknown")
            diarized.append({**seg, "speaker": speaker_label})

        print(f"[Diarizer] Diarization complete. {len(diarized)} segments labeled.")
        return diarized

    except ImportError:
        print("[Diarizer] pyannote.audio not installed. Using mock diarization.")
        return _mock_diarize(whisper_segments)
    except Exception as e:
        print(f"[Diarizer] Error: {e}. Falling back to mock diarization.")
        return _mock_diarize(whisper_segments)


def _build_speaker_map(speaker_turns: List[Dict]) -> Dict[str, str]:
    """
    Heuristic: The speaker with the first turn is the Agent.
    Second speaker is the Customer.
    """
    seen = []
    for turn in speaker_turns:
        s = turn["speaker_raw"]
        if s not in seen:
            seen.append(s)
        if len(seen) == 2:
            break

    mapping = {}
    if len(seen) >= 1:
        mapping[seen[0]] = "Agent"
    if len(seen) >= 2:
        mapping[seen[1]] = "Customer"
    return mapping


def _find_speaker_at(timestamp: float, speaker_turns: List[Dict]) -> str:
    """Find which speaker was talking at a given timestamp."""
    for turn in speaker_turns:
        if turn["start"] <= timestamp <= turn["end"]:
            return turn["speaker_raw"]
    # Fallback: nearest turn
    if speaker_turns:
        nearest = min(speaker_turns, key=lambda t: abs(t["start"] - timestamp))
        return nearest["speaker_raw"]
    return "SPEAKER_A"


def _mock_diarize(whisper_segments: List[Dict]) -> List[Dict]:
    """
    Mock diarization for demo/testing without HF_TOKEN.
    Alternates Agent / Customer every ~3 segments.
    """
    print("[Diarizer] Using MOCK diarization (demo mode).")
    speakers = ["Agent", "Customer"]
    diarized = []
    block_size = 3
    for i, seg in enumerate(whisper_segments):
        speaker = speakers[(i // block_size) % 2]
        diarized.append({**seg, "speaker": speaker})
    return diarized


def format_transcript_with_speakers(diarized_segments: List[Dict]) -> str:
    """Format diarized segments into readable transcript with speaker labels."""
    lines = []
    current_speaker = None
    buffer = []

    for seg in diarized_segments:
        if seg["speaker"] != current_speaker:
            if buffer and current_speaker:
                ts_start = buffer[0]["start"]
                ts_end = buffer[-1]["end"]
                text = " ".join(s["text"] for s in buffer)
                lines.append(f"[{ts_start:.1f}s] {current_speaker}: {text}")
            current_speaker = seg["speaker"]
            buffer = [seg]
        else:
            buffer.append(seg)

    if buffer and current_speaker:
        ts_start = buffer[0]["start"]
        ts_end = buffer[-1]["end"]
        text = " ".join(s["text"] for s in buffer)
        lines.append(f"[{ts_start:.1f}s] {current_speaker}: {text}")

    return "\n".join(lines)

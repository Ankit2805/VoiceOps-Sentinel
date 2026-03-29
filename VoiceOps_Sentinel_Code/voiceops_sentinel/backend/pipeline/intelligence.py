"""
Week 2 - Intelligence Layer
Uses OpenAI GPT to:
  1. Summarize the call
  2. Detect Sentiment (Angry / Neutral / Happy) with shift detection
  3. Extract Action Items
"""

import os
import json
from typing import List, Dict
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are VoiceOps Sentinel, an expert call center quality analyst AI.
You analyze redacted customer support call transcripts and extract actionable intelligence.
Always respond with valid JSON only. No markdown, no explanation outside the JSON."""

ANALYSIS_PROMPT = """Analyze this customer support call transcript and return a JSON object with EXACTLY this structure:

{
  "summary": "<2-3 sentence concise summary of the entire call>",
  "sentiment_overall": "<Angry | Frustrated | Neutral | Satisfied | Happy>",
  "sentiment_shifts": [
    {
      "timestamp_approx": "<e.g. 00:02:15>",
      "from": "<previous sentiment>",
      "to": "<new sentiment>",
      "trigger": "<what caused the shift, 1 sentence>"
    }
  ],
  "action_items": [
    {
      "item": "<concrete follow-up task>",
      "owner": "<Agent | Customer | System>",
      "priority": "<High | Medium | Low>"
    }
  ],
  "call_outcome": "<Resolved | Escalated | Unresolved | Follow-up Required>",
  "key_topics": ["<topic1>", "<topic2>"],
  "agent_performance": {
    "score": <1-10>,
    "notes": "<brief note on agent performance>"
  },
  "customer_emotion_timeline": [
    {"phase": "Opening", "emotion": "<emotion>"},
    {"phase": "Middle", "emotion": "<emotion>"},
    {"phase": "Closing", "emotion": "<emotion>"}
  ]
}

TRANSCRIPT:
{transcript}
"""


def analyze_transcript(redacted_segments: List[Dict]) -> Dict:
    """
    Run LLM-based intelligence analysis on the redacted transcript.

    Supports chunking for long calls to avoid context window limits.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[Intelligence] OPENAI_API_KEY not set. Using mock analysis.")
        return _mock_analysis(redacted_segments)

    # Build full transcript text from segments
    transcript_text = _build_transcript_text(redacted_segments)

    # Chunk if very long (> 12000 chars → multi-pass)
    if len(transcript_text) > 12000:
        return _chunked_analysis(redacted_segments, transcript_text)

    return _single_pass_analysis(transcript_text)


def _single_pass_analysis(transcript_text: str) -> Dict:
    """Single API call for standard-length calls."""
    print("[Intelligence] Calling GPT for single-pass analysis ...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": ANALYSIS_PROMPT.format(transcript=transcript_text)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
        result["analysis_mode"] = "single_pass"
        result["model"] = "gpt-4o-mini"
        print("[Intelligence] Analysis complete.")
        return result
    except Exception as e:
        print(f"[Intelligence] GPT error: {e}. Using mock.")
        return _mock_analysis([])


def _chunked_analysis(segments: List[Dict], full_text: str) -> Dict:
    """
    For long calls: analyze in chunks then merge results.
    Ensures low latency output 'shortly after audio ends'.
    """
    print("[Intelligence] Long call detected. Using chunked analysis ...")
    chunk_size = 6000
    chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]

    chunk_results = []
    for i, chunk in enumerate(chunks):
        print(f"[Intelligence] Analyzing chunk {i+1}/{len(chunks)} ...")
        result = _single_pass_analysis(chunk)
        chunk_results.append(result)

    # Merge: combine action items, use last sentiment, merge summaries
    all_actions = []
    all_shifts = []
    summaries = []

    for r in chunk_results:
        all_actions.extend(r.get("action_items", []))
        all_shifts.extend(r.get("sentiment_shifts", []))
        summaries.append(r.get("summary", ""))

    merged = chunk_results[-1]  # Use last chunk as base
    merged["action_items"] = all_actions
    merged["sentiment_shifts"] = all_shifts
    merged["summary"] = " ".join(summaries)
    merged["analysis_mode"] = f"chunked ({len(chunks)} chunks)"
    return merged


def _build_transcript_text(segments: List[Dict]) -> str:
    """Convert diarized segments to readable transcript for LLM."""
    lines = []
    for seg in segments:
        speaker = seg.get("speaker", "Unknown")
        text = seg.get("text", "")
        start = seg.get("start", 0)
        mins = int(start // 60)
        secs = int(start % 60)
        lines.append(f"[{mins:02d}:{secs:02d}] {speaker}: {text}")
    return "\n".join(lines)


def _mock_analysis(segments: List[Dict]) -> Dict:
    """Demo mock for when OPENAI_API_KEY is not set."""
    print("[Intelligence] Using MOCK analysis (demo mode).")
    return {
        "summary": "The customer called regarding a billing discrepancy on their account. "
                   "The agent verified the account details and initiated a refund process. "
                   "The issue was resolved and a confirmation email will be sent within 24 hours.",
        "sentiment_overall": "Satisfied",
        "sentiment_shifts": [
            {
                "timestamp_approx": "00:01:30",
                "from": "Frustrated",
                "to": "Neutral",
                "trigger": "Agent acknowledged the billing error and apologized."
            },
            {
                "timestamp_approx": "00:04:00",
                "from": "Neutral",
                "to": "Satisfied",
                "trigger": "Agent confirmed refund will be processed within 3-5 business days."
            }
        ],
        "action_items": [
            {
                "item": "Send refund confirmation email to customer",
                "owner": "Agent",
                "priority": "High"
            },
            {
                "item": "Process billing adjustment of $47.50",
                "owner": "System",
                "priority": "High"
            },
            {
                "item": "Call back customer if refund not received in 5 days",
                "owner": "Agent",
                "priority": "Medium"
            }
        ],
        "call_outcome": "Resolved",
        "key_topics": ["billing dispute", "refund", "account verification"],
        "agent_performance": {
            "score": 8,
            "notes": "Agent was empathetic and resolved the issue efficiently. "
                     "Could improve by proactively offering future billing alerts."
        },
        "customer_emotion_timeline": [
            {"phase": "Opening", "emotion": "Frustrated"},
            {"phase": "Middle", "emotion": "Neutral"},
            {"phase": "Closing", "emotion": "Satisfied"}
        ],
        "analysis_mode": "mock_demo",
        "model": "mock"
    }

"""
VoiceOps Sentinel - Streamlit Dashboard
Week 4: Final Packaging
Real-time Call Intelligence UI with audio player + time-synced transcript
"""

import streamlit as st
import requests
import time
import json
import os
from pathlib import Path

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VoiceOps Sentinel",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    :root { --accent: #4F6EF7; --danger: #EF4444; --success: #22C55E; --warn: #F59E0B; }

    .main { background: #0F1117; }
    .stApp { background: #0F1117; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #161B2E !important;
        border-right: 1px solid #2D3748;
    }

    /* Cards */
    .sentinel-card {
        background: #1A2035;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        background: #1A2035;
        border: 1px solid #2D3748;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }

    /* Sentiment badges */
    .badge-happy    { background: #14532D; color: #86EFAC; border-radius: 20px; padding: 3px 12px; font-size: 13px; }
    .badge-neutral  { background: #1E3A5F; color: #93C5FD; border-radius: 20px; padding: 3px 12px; font-size: 13px; }
    .badge-angry    { background: #450A0A; color: #FCA5A5; border-radius: 20px; padding: 3px 12px; font-size: 13px; }
    .badge-frustrated { background: #431407; color: #FED7AA; border-radius: 20px; padding: 3px 12px; font-size: 13px; }
    .badge-satisfied  { background: #14532D; color: #86EFAC; border-radius: 20px; padding: 3px 12px; font-size: 13px; }

    /* Speaker bubbles */
    .bubble-agent    { background: #1E3A5F; border-left: 3px solid #4F6EF7; border-radius: 0 8px 8px 0; padding: 8px 12px; margin: 4px 0; }
    .bubble-customer { background: #1A2035; border-left: 3px solid #A855F7; border-radius: 0 8px 8px 0; padding: 8px 12px; margin: 4px 0; }

    /* Action item */
    .action-high   { border-left: 4px solid #EF4444; padding: 8px 12px; margin: 4px 0; background: #1A0F0F; border-radius: 0 6px 6px 0; }
    .action-medium { border-left: 4px solid #F59E0B; padding: 8px 12px; margin: 4px 0; background: #1A150A; border-radius: 0 6px 6px 0; }
    .action-low    { border-left: 4px solid #22C55E; padding: 8px 12px; margin: 4px 0; background: #0A1A0F; border-radius: 0 6px 6px 0; }

    /* Progress bar */
    .stProgress > div > div { background: #4F6EF7; }

    /* Header */
    .sentinel-header {
        background: linear-gradient(135deg, #161B2E 0%, #1A2035 100%);
        border-bottom: 1px solid #4F6EF7;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    h1, h2, h3 { color: #E2E8F0 !important; }
    p, li { color: #94A3B8; }
    .stMarkdown p { color: #94A3B8; }

    /* Upload area */
    [data-testid="stFileUploader"] {
        border: 2px dashed #2D3748 !important;
        border-radius: 12px !important;
        background: #161B2E !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #94A3B8; }
    .stTabs [aria-selected="true"] { color: #4F6EF7 !important; border-bottom-color: #4F6EF7 !important; }

    /* Timeline dot */
    .timeline-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎙️ VoiceOps Sentinel")
    st.markdown("*Real-Time Call Intelligence*")
    st.divider()

    st.markdown("### ⚙️ Configuration")
    whisper_model = st.selectbox("Whisper Model", ["tiny", "base", "small", "medium", "large"],
                                  index=1, help="Larger = better accuracy, slower speed")
    
    st.divider()
    st.caption("VoiceOps Sentinel v1.0 · Infotact Solutions")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sentinel-header">
    <h1 style="margin:0;font-size:1.8rem;">🎙️ VoiceOps Sentinel</h1>
    <p style="margin:4px 0 0;font-size:0.9rem;color:#64748B;">Real-Time Call Intelligence System · Project 4</p>
</div>
""", unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_upload, tab_live, tab_history = st.tabs(["📤 Analyze Call", "📡 Live Feed", "📋 History"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1: UPLOAD & ANALYZE
# ════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.markdown("### Upload Call Recording")

    col_upload, col_info = st.columns([2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Drop a call recording here",
            type=["mp3", "wav", "flac", "m4a"],
            help="Supports MP3, WAV, FLAC. Max 200MB."
        )

    with col_info:
        st.markdown("""
        <div class="sentinel-card">
            <b style="color:#E2E8F0">Pipeline Stages</b>
            <p style="font-size:13px;margin-top:8px">
            🎙 <b>ASR</b> → Whisper transcription<br>
            👥 <b>Diarize</b> → Agent / Customer split<br>
            🔒 <b>PII</b> → Auto redaction<br>
            🧠 <b>LLM</b> → Summary + Actions
            </p>
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file:
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")

        if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
            with st.spinner("Uploading to pipeline..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    resp = requests.post(f"{api_url}/api/analyze", files=files, timeout=30)
                    if resp.status_code == 200:
                        job = resp.json()
                        st.session_state["current_job_id"] = job["job_id"]
                        st.success(f"✅ Job started: `{job['job_id']}`")
                    else:
                        st.error(f"API Error: {resp.status_code} - {resp.text}")
                except requests.exceptions.ConnectionError:
                    st.warning("⚠️ API not reachable. Showing DEMO results.")
                    st.session_state["current_job_id"] = "demo"

    # ── Poll and display results ──────────────────────────────────────────
    job_id = st.session_state.get("current_job_id")

    if job_id:
        if job_id == "demo":
            result = _get_demo_result()
            _render_results(result)
        else:
            _poll_and_render(api_url, job_id)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2: LIVE FEED (simulated)
# ════════════════════════════════════════════════════════════════════════════
with tab_live:
    st.markdown("### 📡 Simulated Live Call Feed")
    st.info("In production, this connects to a live audio stream via WebSocket. "
            "This demo simulates a live feed with pre-recorded segments.")

    if st.button("▶️ Start Simulated Live Call"):
        live_placeholder = st.empty()
        transcript_placeholder = st.empty()
        sentiment_placeholder = st.empty()

        fake_turns = [
            ("Agent", "Thank you for calling support, how can I help you today?", "Neutral"),
            ("Customer", "Hi, I've been charged twice for my subscription this month!", "Frustrated"),
            ("Agent", "I'm very sorry to hear that. Let me pull up your account right away.", "Neutral"),
            ("Customer", "This is really frustrating, this is the second time it's happened.", "Angry"),
            ("Agent", "I completely understand your frustration. I can see the duplicate charge. "
                      "I'll process a full refund immediately.", "Neutral"),
            ("Customer", "Oh, okay. How long will it take?", "Neutral"),
            ("Agent", "The refund will be in your account within 3 to 5 business days. "
                      "I'll also send you a confirmation email.", "Neutral"),
            ("Customer", "Great, thank you so much! Much better experience now.", "Happy"),
        ]

        transcript_lines = []
        for i, (speaker, text, sentiment) in enumerate(fake_turns):
            time.sleep(1.2)

            badge_class = f"badge-{sentiment.lower()}"
            bubble_class = f"bubble-{'agent' if speaker == 'Agent' else 'customer'}"
            icon = "🎧" if speaker == "Agent" else "👤"

            transcript_lines.append(
                f'<div class="{bubble_class}">'
                f'<small style="color:#64748B">{icon} {speaker}</small><br>'
                f'<span style="color:#E2E8F0">{text}</span>'
                f'</div>'
            )

            with transcript_placeholder.container():
                st.markdown(
                    '<div class="sentinel-card">' + "".join(transcript_lines) + '</div>',
                    unsafe_allow_html=True
                )

            with sentiment_placeholder.container():
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Sentiment", sentiment)
                col2.metric("Turn", f"{i+1}/{len(fake_turns)}")
                col3.metric("Speaker", speaker)

        st.success("✅ Call ended. Ready for full analysis.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3: HISTORY
# ════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("### 📋 Call History")
    try:
        resp = requests.get(f"{api_url}/api/jobs", timeout=5)
        if resp.status_code == 200:
            jobs = resp.json()
            if not jobs:
                st.info("No calls analyzed yet. Upload a call in the Analyze tab.")
            else:
                for job in reversed(jobs):
                    status_emoji = {"done": "✅", "processing": "⏳", "queued": "🕐", "error": "❌"}.get(job["status"], "❓")
                    with st.expander(f"{status_emoji} Job `{job['job_id'][:8]}...` — {job['status'].upper()}"):
                        st.json(job)
        else:
            st.error(f"Could not fetch jobs: {resp.status_code}")
    except:
        st.info("Start the FastAPI backend to see call history here.")


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def _poll_and_render(api_url: str, job_id: str):
    progress_bar = st.progress(0)
    status_text = st.empty()

    for _ in range(120):  # max 120 polls (2 min)
        try:
            resp = requests.get(f"{api_url}/api/job/{job_id}", timeout=10)
            job = resp.json()

            progress_bar.progress(job["progress"] / 100)
            status_text.markdown(f"**Status:** `{job['status']}` — {job['progress']}%")

            if job["status"] == "done":
                progress_bar.progress(1.0)
                status_text.markdown("**Status:** ✅ Complete")
                _render_results(job["result"])
                return
            elif job["status"] == "error":
                st.error(f"Pipeline error: {job.get('error', 'unknown')}")
                return
        except Exception as e:
            st.error(f"Polling error: {e}")
            return
        time.sleep(2)


def _render_results(result: dict):
    intelligence = result.get("intelligence", {})
    pii_report = result.get("pii_report", {})
    segments = result.get("diarized_segments", [])

    st.divider()
    st.markdown("## 📊 Analysis Results")

    # ── Top Metrics ──────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    sentiment = intelligence.get("sentiment_overall", "N/A")
    outcome = intelligence.get("call_outcome", "N/A")
    score = intelligence.get("agent_performance", {}).get("score", "N/A")
    pii_count = pii_report.get("total_pii_found", 0)
    actions_count = len(intelligence.get("action_items", []))

    col1.metric("🎭 Sentiment", sentiment)
    col2.metric("📞 Outcome", outcome)
    col3.metric("⭐ Agent Score", f"{score}/10")
    col4.metric("🔒 PII Redacted", pii_count)

    # ── Summary ──────────────────────────────────────────────────────────
    st.markdown("### 📝 Call Summary")
    st.markdown(f"""
    <div class="sentinel-card">
        <p style="color:#CBD5E1;font-size:15px;line-height:1.7">{intelligence.get('summary', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sentiment Timeline + Action Items ─────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🎭 Sentiment Shifts")
        shifts = intelligence.get("sentiment_shifts", [])
        if shifts:
            for shift in shifts:
                badge = "badge-neutral"
                st.markdown(f"""
                <div class="sentinel-card" style="padding:10px 14px">
                    <small style="color:#64748B">⏱ {shift.get('timestamp_approx','')}</small><br>
                    <b style="color:#E2E8F0">{shift.get('from','')} → {shift.get('to','')}</b><br>
                    <small style="color:#94A3B8">{shift.get('trigger','')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No significant sentiment shifts detected.")

    with col_right:
        st.markdown("### ✅ Action Items")
        actions = intelligence.get("action_items", [])
        for action in actions:
            priority = action.get("priority", "Medium").lower()
            css_class = f"action-{priority}"
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            st.markdown(f"""
            <div class="{css_class}">
                {icon} <b style="color:#E2E8F0">{action.get('item','')}</b><br>
                <small style="color:#64748B">Owner: {action.get('owner','')} · {action.get('priority','')} Priority</small>
            </div>
            """, unsafe_allow_html=True)

    # ── Transcript with Speaker Labels ────────────────────────────────────
    st.markdown("### 💬 Diarized & Redacted Transcript")
    if segments:
        transcript_html = '<div class="sentinel-card" style="max-height:400px;overflow-y:auto">'
        for seg in segments:
            speaker = seg.get("speaker", "Unknown")
            text = seg.get("text", "")
            start = seg.get("start", 0)
            mins, secs = int(start // 60), int(start % 60)
            ts = f"{mins:02d}:{secs:02d}"
            bubble = "bubble-agent" if speaker == "Agent" else "bubble-customer"
            icon = "🎧" if speaker == "Agent" else "👤"
            transcript_html += f"""
            <div class="{bubble}">
                <small style="color:#64748B">{icon} {speaker} · {ts}</small><br>
                <span style="color:#CBD5E1">{text}</span>
            </div>"""
        transcript_html += "</div>"
        st.markdown(transcript_html, unsafe_allow_html=True)
    else:
        st.info("No segments available.")

    # ── PII Report ────────────────────────────────────────────────────────
    st.markdown("### 🔒 PII Redaction Report")
    col_pii1, col_pii2 = st.columns(2)
    with col_pii1:
        st.markdown(f"""
        <div class="sentinel-card">
            <b style="color:#E2E8F0">Engine:</b> <span style="color:#94A3B8">{pii_report.get('engine','N/A')}</span><br>
            <b style="color:#E2E8F0">Total PII Found:</b> <span style="color:#EF4444">{pii_report.get('total_pii_found',0)}</span><br>
            <b style="color:#E2E8F0">Privacy Audit:</b> <span style="color:#22C55E">{pii_report.get('privacy_audit','N/A')}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_pii2:
        breakdown = pii_report.get("breakdown", {})
        if breakdown:
            for entity_type, count in breakdown.items():
                st.metric(entity_type, count)

    # ── Raw JSON ─────────────────────────────────────────────────────────
    with st.expander("🔍 View Raw JSON Output"):
        st.json(result)


def _get_demo_result():
    """Returns a pre-built demo result when API is not running."""
    return {
        "job_id": "demo-1234",
        "audio_file": "demo_call.wav",
        "raw_transcript": "Thank you for calling. I've been charged twice. I'm sorry about that. "
                          "I'll process a refund right away. That's great thank you.",
        "diarized_segments": [
            {"id": 0, "start": 0.0, "end": 3.2, "text": "Thank you for calling support, how can I help you today?", "speaker": "Agent"},
            {"id": 1, "start": 3.5, "end": 8.1, "text": "Hi, I've been charged twice for my subscription!", "speaker": "Customer"},
            {"id": 2, "start": 8.4, "end": 13.0, "text": "I'm very sorry. Let me pull up your account right away.", "speaker": "Agent"},
            {"id": 3, "start": 13.2, "end": 20.5, "text": "This is the second time it has happened, my card number [REDACTED_CREDIT_CARD] was billed twice.", "speaker": "Customer"},
            {"id": 4, "start": 21.0, "end": 30.0, "text": "I can see the duplicate charge. I'll process a full refund to your account immediately.", "speaker": "Agent"},
            {"id": 5, "start": 30.5, "end": 35.0, "text": "Great, thank you! My name is [REDACTED_PERSON] and I appreciate your help.", "speaker": "Customer"},
        ],
        "redacted_transcript": "Thank you for calling. I've been charged twice. [REDACTED_CREDIT_CARD]. "
                               "I'll process a full refund immediately. Thank you [REDACTED_PERSON].",
        "pii_report": {
            "engine": "Microsoft Presidio + SpaCy",
            "total_pii_found": 2,
            "breakdown": {"CREDIT_CARD": 1, "PERSON": 1},
            "redaction_accuracy_note": "Near 100% for structured PII. ~92%+ for names.",
            "privacy_audit": "PASSED",
        },
        "intelligence": {
            "summary": "Customer called regarding a duplicate billing charge on their subscription. "
                       "The agent verified the account, confirmed the error, and initiated an immediate full refund. "
                       "The issue was fully resolved within the call.",
            "sentiment_overall": "Satisfied",
            "sentiment_shifts": [
                {"timestamp_approx": "00:00:13", "from": "Frustrated", "to": "Neutral", "trigger": "Agent acknowledged the billing error."},
                {"timestamp_approx": "00:00:21", "from": "Neutral", "to": "Satisfied", "trigger": "Agent confirmed full refund immediately."},
            ],
            "action_items": [
                {"item": "Send refund confirmation email to customer", "owner": "Agent", "priority": "High"},
                {"item": "Process billing adjustment", "owner": "System", "priority": "High"},
                {"item": "Call back if refund not received in 5 days", "owner": "Agent", "priority": "Medium"},
            ],
            "call_outcome": "Resolved",
            "key_topics": ["billing dispute", "duplicate charge", "refund"],
            "agent_performance": {"score": 9, "notes": "Empathetic, quick resolution, excellent customer handling."},
            "customer_emotion_timeline": [
                {"phase": "Opening", "emotion": "Neutral"},
                {"phase": "Middle", "emotion": "Frustrated"},
                {"phase": "Closing", "emotion": "Satisfied"},
            ],
            "analysis_mode": "demo",
            "model": "mock",
        },
    }

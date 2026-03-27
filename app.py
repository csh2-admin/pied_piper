"""
app.py — Hardware Test Voice Memo Logger (Streamlit)
=====================================================
Run locally:   streamlit run app.py
Deploy:        push to GitHub → connect on share.streamlit.io
"""

import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from config import TEAM_MEMBERS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weebo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

/* ── Root colours ── */
:root {
    --gold:    #c9a84c;
    --gold-dim:#8a6f2e;
    --bg:      #0b0c0e;
    --bg2:     #111318;
    --bg3:     #181b21;
    --border:  #2a2d35;
    --text:    #c8cdd8;
    --muted:   #5a6070;
    --success: #4a7c59;
    --danger:  #7c3a3a;
}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] h3 {
    color: var(--gold) !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 0.08em;
    font-size: 0.95rem !important;
    text-transform: uppercase;
}

/* ── Radio nav items ── */
[data-testid="stSidebar"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.1em !important;
    color: var(--muted) !important;
    text-transform: uppercase;
    padding: 4px 0 !important;
}
[data-testid="stSidebar"] label:hover {
    color: var(--gold) !important;
}
/* selected nav item */
[data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="true"] + div label,
[data-testid="stSidebar"] [aria-checked="true"] ~ div {
    color: var(--gold) !important;
}

/* ── Main headers ── */
h1, h2 {
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--gold) !important;
    letter-spacing: 0.15em !important;
    font-weight: 400 !important;
    border-bottom: 1px solid var(--gold-dim);
    padding-bottom: 0.4em;
}
h3, h4 {
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--text) !important;
    letter-spacing: 0.1em !important;
    font-weight: 400 !important;
}

/* ── Metric cards — corner bracket style ── */
[data-testid="stMetric"] {
    background-color: var(--bg3) !important;
    padding: 16px 20px !important;
    position: relative;
}
[data-testid="stMetric"]::before,
[data-testid="stMetric"]::after {
    content: '';
    position: absolute;
    width: 10px; height: 10px;
    border-color: var(--gold);
    border-style: solid;
}
[data-testid="stMetric"]::before {
    top: 4px; left: 4px;
    border-width: 1px 0 0 1px;
}
[data-testid="stMetric"]::after {
    bottom: 4px; right: 4px;
    border-width: 0 1px 1px 0;
}
[data-testid="stMetricLabel"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.15em !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 1.8rem !important;
    color: var(--text) !important;
    font-weight: 400 !important;
}

/* ── Containers / borders ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border: 1px solid var(--border) !important;
    background-color: var(--bg2) !important;
    border-radius: 0 !important;
}

/* ── Inputs ── */
input, textarea, [data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background-color: var(--bg3) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
}
input:focus, textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 1px var(--gold-dim) !important;
}

/* ── Select / combobox ── */
[data-baseweb="select"] > div {
    background-color: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    color: var(--text) !important;
}
[data-baseweb="popover"] {
    background-color: var(--bg2) !important;
    border: 1px solid var(--gold-dim) !important;
}

/* ── Buttons ── */
button[kind="primary"], [data-testid="baseButton-primary"] {
    background-color: transparent !important;
    color: var(--gold) !important;
    border: 1px solid var(--gold) !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 0.1em !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
}
button[kind="primary"]:hover {
    background-color: var(--gold) !important;
    color: var(--bg) !important;
}
button[kind="secondary"], [data-testid="baseButton-secondary"] {
    background-color: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 0.08em !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
}
button[kind="secondary"]:hover {
    border-color: var(--muted) !important;
    color: var(--text) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    background-color: var(--bg2) !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.06em !important;
    color: var(--text) !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--gold) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
}

/* ── Success / error / info banners ── */
[data-testid="stAlert"] {
    border-radius: 0 !important;
    border-left: 3px solid var(--gold) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
}

/* ── Dividers ── */
hr {
    border-color: var(--border) !important;
}

/* ── Caption / small text ── */
[data-testid="stCaptionContainer"] p,
small, .stCaption {
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
}

/* ── Markdown body text ── */
p, li {
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--text) !important;
    font-size: 1rem !important;
}

/* ── Code blocks (SQL display) ── */
code, pre {
    background-color: var(--bg3) !important;
    color: var(--gold) !important;
    font-family: 'Share Tech Mono', monospace !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); }
::-webkit-scrollbar-thumb:hover { background: var(--gold-dim); }
</style>
""", unsafe_allow_html=True)


SEV_BADGE = {
    "Critical": "🔴", "High": "🟠",
    "Medium":   "🟡", "Low":  "🟢", "None": "⚪",
}
SEVERITY_OPTIONS = ["Critical", "High", "Medium", "Low", "None"]
STATUS_OPTIONS   = ["Not Started", "In Progress", "Complete"]
STATUS_BADGE     = {"Not Started": "⬜", "In Progress": "🔵", "Complete": "✅"}

ACTIVITY_OPTIONS = [
    "Regular Maintenance",
    "Unplanned Maintenance",
    "Technical Milestone",
    "Logistics",
    "Other",
]

# ── Pinocchio loading animation (Ask Weebo) ───────────────────────────────────
PINOCCHIO_HTML = """
<div style="display:flex;align-items:center;padding:24px 0 16px 0;gap:0;">
<style>
@keyframes grow-nose {
  0%   { width: 8px; }
  100% { width: min(580px, 55vw); }
}
@keyframes blink {
  0%,88%,100% { transform:scaleY(1); }
  93%         { transform:scaleY(0.08); }
}
@keyframes label-pulse {
  0%,100% { opacity:0.3; } 50% { opacity:1; }
}
.pin-face {
  position:relative; width:52px; height:52px;
  background:#111318; border-radius:50%;
  border:1.5px solid #c9a84c; flex-shrink:0; z-index:2;
}
.pin-eye {
  position:absolute; width:5px; height:5px;
  background:#c9a84c; border-radius:50%; top:14px;
  animation:blink 3.2s ease-in-out infinite;
  transform-origin:center 2.5px;
}
.pin-eye.l { left:12px; } .pin-eye.r { left:30px; }
.pin-mouth {
  position:absolute; bottom:10px; left:50%;
  transform:translateX(-50%);
  width:16px; height:5px;
  border-bottom:2px solid #c9a84c;
  border-radius:0 0 8px 8px;
}
.pin-nose-row {
  display:flex; align-items:center; flex:1; height:12px; margin-top:-1px;
}
.pin-nose {
  height:4px;
  background:linear-gradient(90deg,#6b4f1a,#c9a84c);
  animation:grow-nose 2.8s cubic-bezier(.4,0,.2,1) infinite alternate;
  box-shadow:0 0 8px #c9a84c44;
}
.pin-tip {
  width:9px; height:9px; background:#c9a84c;
  border-radius:50%; flex-shrink:0; margin-left:-1px;
  box-shadow:0 0 10px #c9a84c99;
}
.pin-label {
  font-family:'Share Tech Mono',monospace; font-size:0.68rem;
  letter-spacing:0.14em; color:#5a6070; margin-left:18px;
  flex-shrink:0; animation:label-pulse 1.4s ease-in-out infinite;
}
</style>
<div class="pin-face">
  <div class="pin-eye l"></div>
  <div class="pin-eye r"></div>
  <div class="pin-mouth"></div>
</div>
<div class="pin-nose-row">
  <div class="pin-nose"></div>
  <div class="pin-tip"></div>
</div>
<div class="pin-label">QUERYING DATABASE...</div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "transcript":   "",
    "insights":     {},
    "source_label": "",
    "audio_bytes":  None,
    "audio_suffix": ".wav",
    "chat_history": [],   # list of {"role": "user"|"assistant", "content": str, "sql": str|None, "rows": list|None}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner="Loading records…")
def _load_records(eng, act, sev, search, d_from, d_to):
    from db_logger import fetch_filtered_rows
    return fetch_filtered_rows(
        engineer      = "" if eng == "All engineers"  else eng,
        activity_type = "" if act == "All types"      else act,
        severity      = "" if sev == "All severities" else sev,
        search        = search or "",
        date_from     = str(d_from) if d_from else "",
        date_to       = str(d_to)   if d_to   else "",
    )


@st.cache_data(ttl=30, show_spinner=False)
def _db_ping() -> bool:
    try:
        from db_logger import test_connection
        return test_connection() == "ok"
    except Exception:
        return False


@st.cache_data(ttl=30, show_spinner="Loading actions…")
def _load_actions(eng, status, search):
    from db_logger import fetch_action_items
    return fetch_action_items(
        engineer = "" if eng    == "All engineers" else eng,
        status   = "" if status == "All statuses"  else status,
        search   = search or "",
    )


def _clear_entry():
    st.session_state.transcript   = ""
    st.session_state.insights     = {}
    st.session_state.audio_bytes  = None
    st.session_state.source_label = ""


def _edit_row(row: dict):
    """Editable form rendered inside a st.expander for one DB record."""
    row_id = row["id"]
    ts     = row.get("logged_at")
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(ts, "strftime") else str(ts)

    st.caption(f"ID: {row_id}  ·  {ts_str}  ·  Source: {row.get('source_file') or '—'}")

    with st.form(key=f"form_{row_id}"):
        c1, c2 = st.columns(2)

        with c1:
            cur_eng = row.get("engineer", "") or ""
            eng_idx = TEAM_MEMBERS.index(cur_eng) if cur_eng in TEAM_MEMBERS else 0
            f_eng   = st.selectbox("Engineer", TEAM_MEMBERS, index=eng_idx)
            cur_act2 = row.get("activity_type","Other") or "Other"
            act_idx2 = ACTIVITY_OPTIONS.index(cur_act2) if cur_act2 in ACTIVITY_OPTIONS else 4
            f_act2  = st.selectbox("Activity Type", ACTIVITY_OPTIONS, index=act_idx2)
            f_sum   = st.text_area("Summary",            value=row.get("summary","") or "",            height=75)
            f_sp    = st.text_area("System Performance", value=row.get("system_performance","") or "", height=75)
            f_md    = st.text_area("Maintenance Done",   value=row.get("maintenance_done","") or "",   height=75)
            f_if    = st.text_area("Issues Found",       value=row.get("issues_found","") or "",       height=75)

        with c2:
            f_ai  = st.text_area("Action Items",        value=row.get("action_items","") or "",        height=75)
            f_ca  = st.text_input("Components Affected", value=row.get("components_affected","") or "")
            f_dur = st.text_input("Duration (hrs)",      value=str(row.get("duration_hours","") or ""))
            cur_sev = row.get("severity","None") or "None"
            sev_idx = SEVERITY_OPTIONS.index(cur_sev) if cur_sev in SEVERITY_OPTIONS else 4
            f_sev = st.selectbox("Severity", SEVERITY_OPTIONS, index=sev_idx)
            f_an  = st.text_area("Additional Notes",    value=row.get("additional_notes","") or "",    height=75)

        f_rt = st.text_area("Raw Transcript", value=row.get("raw_transcript","") or "", height=100)

        cs, cd, _ = st.columns([1, 1, 5])
        do_save   = cs.form_submit_button("💾  Save",   type="primary",    use_container_width=True)
        do_delete = cd.form_submit_button("🗑  Delete", type="secondary",   use_container_width=True)

    if do_save:
        try:
            from db_logger import update_entry
            update_entry(row_id, {
                "engineer": f_eng, "activity_type": f_act2, "summary": f_sum,
                "system_performance": f_sp, "maintenance_done": f_md,
                "issues_found": f_if, "action_items": f_ai,
                "components_affected": f_ca, "duration_hours": f_dur,
                "severity": f_sev, "additional_notes": f_an,
                "raw_transcript": f_rt,
            })
            st.success(f"Record {row_id} updated.")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Save error: {e}")

    if do_delete:
        try:
            from db_logger import delete_entry
            delete_entry(row_id)
            st.warning(f"Record {row_id} deleted.")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Delete error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### WEEBO")
    st.caption("Hardware Test Programme")
    st.divider()

    page = st.radio(
        "Navigate",
        ["New Entry", "Records", "Actions", "Gantt", "Sensor View", "Ask Weebo"],
        label_visibility="collapsed",
    )

    st.divider()
    engineer = st.selectbox("ENGINEER", TEAM_MEMBERS)

    st.divider()
    db_ok = _db_ping()
    if db_ok:
        st.success("DB connected", icon="🟢")
    else:
        st.error("DB offline — check secrets", icon="🔴")
    st.caption("TimescaleDB")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: NEW ENTRY
# ─────────────────────────────────────────────────────────────────────────────
if page == "New Entry":

    st.header("NEW ENTRY")

    # ── Step 1: Audio ─────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("STEP 1 — AUDIO")
        mode = st.radio("Source", ["📂  Upload file", "🎙  Record now"],
                        horizontal=True, label_visibility="collapsed")

        if "Upload" in mode:
            uploaded = st.file_uploader(
                "Upload voice memo",
                type=["m4a","mp3","wav","ogg","flac","aac","mp4"],
                label_visibility="collapsed",
            )
            if uploaded:
                st.session_state.audio_bytes  = uploaded.read()
                st.session_state.audio_suffix = Path(uploaded.name).suffix or ".m4a"
                st.session_state.source_label = uploaded.name
                st.audio(st.session_state.audio_bytes)
                st.success(f"Loaded: **{uploaded.name}**")
        else:
            st.info("Click the mic to start, click stop when done.", icon="ℹ️")
            recorded = st.audio_input("Record", label_visibility="collapsed")
            if recorded:
                st.session_state.audio_bytes  = recorded.read()
                st.session_state.audio_suffix = ".wav"
                st.session_state.source_label = "Live Recording"
                st.success("Recording captured — ready to transcribe.")

    # ── Step 2: Transcribe ────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("STEP 2 — TRANSCRIBE")

        if st.button("🔤  Transcribe Audio",
                     disabled=not st.session_state.audio_bytes,
                     type="primary"):
            with st.spinner("Transcribing with Whisper — this takes ~30 seconds on first run…"):
                try:
                    from transcriber import transcribe_file
                    text = transcribe_file(
                        st.session_state.audio_bytes,
                        st.session_state.audio_suffix,
                    )
                    st.session_state.transcript = text
                    st.success(f"Done — {len(text):,} characters.")
                except Exception as e:
                    st.error(f"Transcription error: {e}")

        # Always-visible editable text area
        new_transcript = st.text_area(
            "Transcript — edit before extracting",
            value=st.session_state.transcript,
            height=200,
            placeholder="Transcript appears here after transcribing. You can also paste text directly.",
        )
        if new_transcript != st.session_state.transcript:
            st.session_state.transcript = new_transcript

        st.caption(f"{len(st.session_state.transcript):,} characters")

    # ── Step 3: Extract ───────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("STEP 3 — EXTRACT WITH WEEBO")

        if st.button("✨  Extract Insights",
                     disabled=not st.session_state.transcript.strip(),
                     type="primary"):
            with st.spinner("Sending to Weebo…"):
                try:
                    from extractor import extract_insights
                    st.session_state.insights = extract_insights(st.session_state.transcript)
                    st.success("Extraction complete — review below.")
                except Exception as e:
                    st.error(f"Extraction error: {e}")

        if st.session_state.insights:
            st.success("Extraction complete — review and edit fields below before saving.")

    # ── Step 4: Review, Edit & Save ───────────────────────────────────────────
    with st.container(border=True):
        st.subheader("STEP 4 — REVIEW, EDIT & SAVE")

        if not st.session_state.insights:
            st.caption("Extract insights first to unlock this section.")
        else:
            ins = st.session_state.insights

            # ── Editable fields form ──────────────────────────────────────────
            with st.form("edit_insights_form"):
                st.markdown("##### Review extracted fields — edit anything before saving")

                # Row 1: Activity type + Severity side by side (dropdowns)
                r1c1, r1c2 = st.columns(2)
                cur_act = ins.get("activity_type","Other") or "Other"
                act_idx = ACTIVITY_OPTIONS.index(cur_act) if cur_act in ACTIVITY_OPTIONS else 4
                f_activity = r1c1.selectbox("Activity Type", ACTIVITY_OPTIONS, index=act_idx)

                cur_sev = ins.get("severity","None") or "None"
                sev_idx = SEVERITY_OPTIONS.index(cur_sev) if cur_sev in SEVERITY_OPTIONS else 4
                f_severity = r1c2.selectbox("Severity", SEVERITY_OPTIONS, index=sev_idx)

                # Summary — full width
                f_summary = st.text_area("Summary",
                    value=ins.get("summary","") or "", height=75)

                # Row 2: two-column text areas
                c1, c2 = st.columns(2)
                f_sp   = c1.text_area("System Performance",
                    value=ins.get("system_performance","") or "", height=100)
                f_md   = c1.text_area("Maintenance Done",
                    value=ins.get("maintenance_done","") or "", height=100)
                f_if   = c1.text_area("Issues Found",
                    value=ins.get("issues_found","") or "", height=100)
                f_ai   = c2.text_area("Action Items",
                    value=ins.get("action_items","") or "", height=100)
                f_ca   = c2.text_input("Components Affected",
                    value=ins.get("components_affected","") or "")
                f_dur  = c2.text_input("Duration (hrs)",
                    value=str(ins.get("duration_hours","") or ""))
                f_an   = st.text_area("Additional Notes",
                    value=ins.get("additional_notes","") or "", height=75)

                st.divider()
                dc1, dc2 = st.columns([1, 2])
                f_date_recorded = dc1.date_input(
                    "Date Recorded",
                    value=None,
                    help="Leave blank to use today's date. Set a past date to log a historical entry.",
                    key="date_recorded",
                )
                dc2.caption("Leave blank to record as today. Set a past date for historical entries.")
                sc1, sc2 = st.columns([1, 1])
                do_save  = sc1.form_submit_button("💾  Save to Database",
                                                  type="primary",
                                                  use_container_width=True)
                do_clear = sc2.form_submit_button("🗑  Clear all",
                                                  use_container_width=True)

            if do_save:
                # Write edited values back to session state before saving
                edited = {
                    "activity_type":       f_activity,
                    "summary":             f_summary,
                    "system_performance":  f_sp,
                    "maintenance_done":    f_md,
                    "issues_found":        f_if,
                    "action_items":        f_ai,
                    "components_affected": f_ca,
                    "duration_hours":      f_dur,
                    "severity":            f_severity,
                    "additional_notes":    f_an,
                }
                with st.spinner("Saving…"):
                    try:
                        from db_logger import append_entry, ensure_schema
                        ensure_schema()
                        result = append_entry(
                            edited,
                            st.session_state.transcript,
                            st.session_state.source_label or "Unknown",
                            engineer,
                            logged_at=f_date_recorded,  # None → NOW() in DB
                        )
                        ts = result["logged_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
                        # Auto-create individual action item rows
                        n_actions = 0
                        if f_ai.strip():
                            from db_logger import create_action_items_from_memo
                            created = create_action_items_from_memo(
                                result["id"], f_ai, engineer
                            )
                            n_actions = len(created)
                        action_msg = f" + **{n_actions}** action item{'s' if n_actions != 1 else ''} created." if n_actions else ""
                        st.success(f"✅  Saved! Row ID **{result['id']}** — {ts}{action_msg}")
                        _clear_entry()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database error: {e}")

            if do_clear:
                _clear_entry()
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RECORDS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Records":
    st.header("RECORDS")

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("FILTERS")
        fc1, fc2, fc3, fc4 = st.columns(4)
        f_eng  = fc1.selectbox("Engineer", ["All engineers"] + TEAM_MEMBERS)
        f_act  = fc2.selectbox("Activity Type", ["All types"] + ACTIVITY_OPTIONS)
        f_sev  = fc3.selectbox("Severity",  ["All severities"] + SEVERITY_OPTIONS)
        f_srch = fc4.text_input("Keyword search",
                                placeholder="summary, issues, components…")

        fd1, fd2, fd3 = st.columns(3)
        f_from = fd1.date_input("From", value=None)
        f_to   = fd2.date_input("To",   value=None)
        with fd3:
            st.write("")
            st.write("")
            ac1, ac2 = st.columns(2)
            do_apply = ac1.button("Apply",  type="primary",   use_container_width=True)
            do_clear = ac2.button("Clear filters",            use_container_width=True)

    if do_clear:
        st.cache_data.clear()
        st.rerun()
    if do_apply:
        st.cache_data.clear()

    # ── Fetch ─────────────────────────────────────────────────────────────────
    try:
        rows = _load_records(f_eng, f_act, f_sev, f_srch, f_from, f_to)
    except Exception as e:
        st.error(f"Could not load records: {e}")
        rows = []

    # ── Toolbar ───────────────────────────────────────────────────────────────
    tc1, tc2 = st.columns([4, 1])
    tc1.caption(f"**{len(rows)}** record{'s' if len(rows) != 1 else ''}")

    if tc2.button("📊  Export Excel", use_container_width=True):
        if not rows:
            st.warning("No records to export.")
        else:
            try:
                from excel_export import export_to_excel
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    export_to_excel(rows, tmp.name)
                    excel_bytes = open(tmp.name, "rb").read()
                fname = f"memo_log_{datetime.now():%Y%m%d_%H%M}.xlsx"
                st.download_button(
                    "⬇️  Download Excel",
                    data=excel_bytes, file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"Export error: {e}")

    # ── Records list ──────────────────────────────────────────────────────────
    st.divider()
    if not rows:
        st.info("No records match your filters.", icon="ℹ️")
    else:
        for row in rows:
            ts    = row.get("logged_at")
            ts_str= ts.strftime("%Y-%m-%d  %H:%M UTC") if hasattr(ts,"strftime") else str(ts)
            sev   = row.get("severity","") or ""
            badge = SEV_BADGE.get(sev,"⚪")
            summary_preview = (row.get("summary") or "")[:90]

            act_label = row.get("activity_type","") or ""
            with st.expander(
                f"{badge}  **{ts_str}**  ·  {row.get('engineer','')}  ·  {act_label}  ·  {summary_preview}"
            ):
                _edit_row(row)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ACTIONS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Actions":

    st.header("ACTION ITEMS")
    st.caption("Action items extracted from log entries. Update status as work progresses.")

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.container(border=True):
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 3])
        f_a_eng    = fc1.selectbox("Engineer",  ["All engineers"] + TEAM_MEMBERS, key="af_eng")
        f_a_status = fc2.selectbox("Status",    ["All statuses"]  + STATUS_OPTIONS, key="af_sta")
        f_a_search = fc3.text_input("Search",   placeholder="keyword…", key="af_srch")
        with fc4:
            st.write("")
            ac1, ac2, ac3 = st.columns(3)
            do_refresh = ac1.button("↻ Refresh",    use_container_width=True, key="af_ref")
            do_add_new = ac2.button("＋ Add Manual", use_container_width=True, key="af_add",
                                    type="primary")

    if do_refresh:
        st.cache_data.clear()
        st.rerun()

    # ── Manual add form ───────────────────────────────────────────────────────
    if do_add_new or st.session_state.get("show_add_form"):
        st.session_state["show_add_form"] = True
        with st.container(border=True):
            st.subheader("ADD ACTION ITEM")
            with st.form("manual_action_form"):
                ma_text = st.text_area("Action Item", height=75,
                    placeholder="Describe the action that needs to be done…")
                mc1, mc2, mc3, mc4 = st.columns(4)
                ma_eng   = mc1.selectbox("Assigned To", TEAM_MEMBERS, key="ma_eng")
                ma_resp  = mc2.selectbox("Responsible", TEAM_MEMBERS, key="ma_resp")
                ma_due   = mc3.date_input("Due Date", value=None, key="ma_due")
                ma_notes = mc4.text_input("Notes (optional)")
                ms1, ms2 = st.columns([1, 4])
                do_submit = ms1.form_submit_button("Add", type="primary",
                                                   use_container_width=True)
                do_cancel = ms2.form_submit_button("Cancel")
            if do_submit:
                if not ma_text.strip():
                    st.warning("Enter an action item first.")
                else:
                    try:
                        from db_logger import create_action_items_from_memo
                        created = create_action_items_from_memo(
                            memo_id=None, action_text=ma_text, engineer=ma_eng,
                            responsible=ma_resp, due_date=ma_due,
                        )
                        st.success(f"Action item added.")
                        st.session_state["show_add_form"] = False
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            if do_cancel:
                st.session_state["show_add_form"] = False
                st.rerun()

    # ── Load and display action items ─────────────────────────────────────────
    try:
        actions = _load_actions(f_a_eng, f_a_status, f_a_search)
    except Exception as e:
        st.error(f"Could not load actions: {e}")
        actions = []

    # Summary counts
    if actions:
        total     = len(actions)
        n_ns      = sum(1 for a in actions if a.get("status") == "Not Started")
        n_ip      = sum(1 for a in actions if a.get("status") == "In Progress")
        n_done    = sum(1 for a in actions if a.get("status") == "Complete")

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total",       total)
        mc2.metric("⬜ Not Started", n_ns)
        mc3.metric("🔵 In Progress", n_ip)
        mc4.metric("✅ Complete",    n_done)
        st.divider()

    if not actions:
        st.info("No action items found. Action items are auto-created when you save a new entry, "
                "or you can add them manually above.", icon="ℹ️")
    else:
        # Group by status for visual clarity
        groups = [
            ("🔵  In Progress",  "In Progress"),
            ("⬜  Not Started",  "Not Started"),
            ("✅  Complete",     "Complete"),
        ]

        for group_label, group_status in groups:
            group_items = [a for a in actions if a.get("status") == group_status]
            if not group_items:
                continue

            st.subheader(f"{group_label}  ({len(group_items)})")

            for action in group_items:
                item_id    = action["id"]
                act_text   = action.get("action_text", "")
                cur_status = action.get("status", "Not Started")
                cur_notes  = action.get("notes", "") or ""
                eng_name   = action.get("engineer", "") or "—"
                upd        = action.get("updated_at")
                upd_str    = upd.strftime("%Y-%m-%d %H:%M") if hasattr(upd, "strftime") else str(upd or "")
                memo_sum   = (action.get("memo_summary") or "")[:60]
                memo_id    = action.get("memo_id")
                badge      = STATUS_BADGE.get(cur_status, "⬜")

                cur_resp_label = action.get("responsible","") or ""
                cur_due_label  = action.get("due_date")
                due_label_str  = f"  ·  due {cur_due_label.strftime('%b %d')}" if hasattr(cur_due_label,"strftime") else ""
                exp_label = (f"{badge}  {act_text[:70]}{'…' if len(act_text) > 70 else ''}"
                             f"  ·  *{eng_name}*{due_label_str}")
                if cur_resp_label and cur_resp_label != eng_name:
                    exp_label += f"  ·  resp: {cur_resp_label}"
                if memo_sum:
                    exp_label += f"  ·  _{memo_sum[:50]}_"

                with st.expander(exp_label):
                    # Full action text (read-only display, editable below)
                    st.markdown(f"**Action:** {act_text}")
                    ic1, ic2, ic3, ic4 = st.columns(4)
                    ic1.caption(f"Assigned to: **{eng_name}**")
                    cur_resp = action.get("responsible","") or "—"
                    ic2.caption(f"Responsible: **{cur_resp}**")
                    cur_due  = action.get("due_date")
                    due_str  = cur_due.strftime("%Y-%m-%d") if hasattr(cur_due,"strftime") else (str(cur_due) if cur_due else "—")
                    ic3.caption(f"Due: **{due_str}**")
                    ic4.caption(f"Updated: {upd_str}")
                    if memo_id:
                        st.caption(f"From memo ID: {memo_id}" +
                                   (f" — {memo_sum}" if memo_sum else ""))
                    st.write("")

                    # Inline status update form
                    with st.form(key=f"action_form_{item_id}"):
                        sf1, sf2, sf3, sf4 = st.columns([1, 2, 2, 2])
                        new_status = sf1.selectbox(
                            "Status",
                            STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(cur_status)
                                  if cur_status in STATUS_OPTIONS else 0,
                            key=f"sel_{item_id}",
                        )
                        resp_idx = TEAM_MEMBERS.index(cur_resp) if cur_resp in TEAM_MEMBERS else 0
                        new_resp = sf2.selectbox(
                            "Responsible",
                            TEAM_MEMBERS,
                            index=resp_idx,
                            key=f"resp_{item_id}",
                        )
                        new_due = sf3.date_input(
                            "Due Date",
                            value=cur_due if cur_due else None,
                            key=f"due_{item_id}",
                        )
                        new_notes = sf4.text_input(
                            "Notes",
                            value=cur_notes,
                            placeholder="Progress notes, blockers…",
                            key=f"notes_{item_id}",
                        )
                        bf1, bf2, _ = st.columns([1, 1, 4])
                        do_update = bf1.form_submit_button(
                            "💾  Save", type="primary", use_container_width=True)
                        do_del    = bf2.form_submit_button(
                            "🗑  Delete", use_container_width=True)

                    if do_update:
                        try:
                            from db_logger import update_action_item
                            update_action_item(item_id, new_status, new_notes,
                                               new_resp, new_due)
                            st.success("Updated.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                    if do_del:
                        try:
                            from db_logger import delete_action_item
                            delete_action_item(item_id)
                            st.warning("Action item deleted.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ASK CLAUDE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Ask Weebo":

    import json
    import anthropic
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

    st.header("ASK WEEBO")
    st.caption("Ask Weebo anything about your log database.")

    # ── Example prompts ───────────────────────────────────────────────────────
    with st.expander("💡  Example questions", expanded=False):
        examples = [
            "What day did we first observe oscillations?",
            "Summarise all records where we received a hydrogen delivery",
            "Which engineer has logged the most Critical or High severity entries?",
            "List all unplanned maintenance events in the last 30 days",
            "What action items are overdue?",
            "Show me every entry that mentions the pressure sensor",
            "How many hours of maintenance did we log in total?",
            "What were the most common components affected across all entries?",
        ]
        cols = st.columns(2)
        for i, ex in enumerate(examples):
            if cols[i % 2].button(ex, key=f"ex_{i}", use_container_width=True):
                st.session_state["prefill_question"] = ex
                st.rerun()

    st.divider()

    # ── Chat history display ──────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(msg["content"])
                # Show the SQL in an expander if present
                if msg.get("sql"):
                    with st.expander("🔍  SQL query used", expanded=False):
                        st.code(msg["sql"], language="sql")
                # Show raw results table if present and not too large
                if msg.get("rows") is not None:
                    rows = msg["rows"]
                    if rows:
                        with st.expander(f"📋  Raw results ({len(rows)} row{'s' if len(rows)!=1 else ''})", expanded=False):
                            st.dataframe(rows, use_container_width=True)
                    else:
                        st.caption("_Query returned no rows._")

    # ── Input ─────────────────────────────────────────────────────────────────
    prefill = st.session_state.pop("prefill_question", "")
    question = st.chat_input("Ask anything about your records…")

    # Use prefill if no direct input
    if prefill and not question:
        question = prefill

    if question:
        # Add user message to history and display immediately
        st.session_state.chat_history.append({
            "role": "user", "content": question, "sql": None, "rows": None
        })

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant", avatar="🤖"):
            with st.status("", expanded=True) as _status:
                st.markdown(PINOCCHIO_HTML, unsafe_allow_html=True)
            try:
                from db_logger import DB_SCHEMA, run_read_query

                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

                # ── Step 1: Ask Claude to write a SQL query ───────────────
                sql_system = f"""You are a SQL expert assistant for a hardware test team.
Your job is to translate natural language questions into PostgreSQL SELECT queries.

{DB_SCHEMA}

Rules:
- Return ONLY a valid PostgreSQL SELECT query — no explanation, no markdown, no code fences.
- Use only SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, etc.
- Use ILIKE for case-insensitive text search.
- Dates are stored as TIMESTAMPTZ in UTC. Use NOW() for current time.
- When searching free-text fields (summary, raw_transcript, issues_found, etc.), 
  search across all relevant text columns using OR.
- Limit results to 200 rows maximum unless the question asks for aggregates.
- For "recent" without a specific timeframe, use the last 90 days.
- Return only the SQL query, nothing else."""

                sql_response = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=512,
                    system=sql_system,
                    messages=[{"role": "user", "content": question}],
                )
                raw_sql = sql_response.content[0].text.strip()

                # Strip markdown fences if Claude added them anyway
                if raw_sql.startswith("```"):
                    raw_sql = raw_sql.split("```")[1]
                    if raw_sql.lower().startswith("sql"):
                        raw_sql = raw_sql[3:]
                    raw_sql = raw_sql.strip()

                # ── Step 2: Run the query ─────────────────────────────────
                rows = run_read_query(raw_sql)

                # ── Step 3: Ask Claude to summarise the results ───────────
                # Serialize rows for Claude — truncate very large result sets
                MAX_ROWS_FOR_SUMMARY = 50
                rows_for_summary = rows[:MAX_ROWS_FOR_SUMMARY]

                # Convert dates/datetimes to strings for JSON serialisation
                def _serialise(obj):
                    if hasattr(obj, "isoformat"):
                        return obj.isoformat()
                    return str(obj)

                rows_json = json.dumps(rows_for_summary, default=_serialise, indent=2)
                truncation_note = (
                    f"\n(Showing first {MAX_ROWS_FOR_SUMMARY} of {len(rows)} total rows.)"
                    if len(rows) > MAX_ROWS_FOR_SUMMARY else ""
                )

                summary_system = """You are a helpful assistant summarising database query results 
for a hardware test engineering team. Be concise and specific. 
Highlight the most important findings. Use bullet points for lists of items.
If the result is empty, say so clearly and suggest why the search may have returned nothing.
Do not mention SQL or databases in your response — just answer the question naturally."""

                summary_prompt = (
                    f"The engineer asked: \"{question}\"\n\n"
                    f"The query returned {len(rows)} result(s){truncation_note}:\n\n"
                    f"{rows_json if rows else '(no results)'}\n\n"
                    f"Please answer the engineer's question based on these results."
                )

                summary_response = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=1024,
                    system=summary_system,
                    messages=[{"role": "user", "content": summary_prompt}],
                )
                answer = summary_response.content[0].text.strip()

                # Collapse the loading animation, show answer
                _status.update(state="complete", expanded=False)
                st.write(answer)
                if raw_sql:
                    with st.expander("🔍  SQL query used", expanded=False):
                        st.code(raw_sql, language="sql")
                if rows:
                    with st.expander(f"📋  Raw results ({len(rows)} row{'s' if len(rows)!=1 else ''})", expanded=False):
                        import pandas as pd
                        st.dataframe(pd.DataFrame(rows), use_container_width=True)
                elif rows is not None:
                    st.caption("_Query returned no rows._")

                # Save to history
                st.session_state.chat_history.append({
                    "role":    "assistant",
                    "content": answer,
                    "sql":     raw_sql,
                    "rows":    rows,
                })

            except ValueError as e:
                _status.update(state="error", expanded=False)
                # SQL safety rejection
                msg = f"I wasn't able to run that query safely: {e}"
                st.warning(msg)
                st.session_state.chat_history.append({
                    "role": "assistant", "content": msg, "sql": None, "rows": None
                })
            except Exception as e:
                _status.update(state="error", expanded=False)
                msg = f"Something went wrong: {e}"
                st.error(msg)
                st.session_state.chat_history.append({
                    "role": "assistant", "content": msg, "sql": None, "rows": None
                })

    # ── Clear chat ────────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        st.divider()
        if st.button("🗑  Clear conversation", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: GANTT
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Gantt":
    import json
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import date, timedelta
    import anthropic
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
    from db_logger import (fetch_gantt_tasks, create_gantt_task,
                            update_gantt_task, delete_gantt_task,
                            bulk_insert_gantt_tasks, ensure_gantt_schema,
                            fetch_action_items)

    ensure_gantt_schema()

    st.header("GANTT CHART")
    st.caption("Project schedule with dependencies. Edit tasks inline or sync from action items.")

    # ── Status colours matching theme ─────────────────────────────────────────
    GANTT_STATUS_COLOUR = {
        "Not Started": "#2a2d35",
        "In Progress":  "#5a7a9a",
        "Complete":     "#4a7c59",
        "Blocked":      "#7c3a3a",
    }
    GANTT_STATUS_OPTIONS = ["Not Started", "In Progress", "Complete", "Blocked"]

    # ── Load tasks ────────────────────────────────────────────────────────────
    @st.cache_data(ttl=15, show_spinner=False)
    def _load_gantt():
        return fetch_gantt_tasks()

    tasks = _load_gantt()

    # ─────────────────────────────────────────────────────────────────────────
    # CHART
    # ─────────────────────────────────────────────────────────────────────────
    if tasks:
        df = pd.DataFrame(tasks)

        # Ensure date columns are proper dates
        df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
        df["end_date"]   = pd.to_datetime(df["end_date"]).dt.date

        # Plotly needs datetime for timeline
        df["start_dt"] = pd.to_datetime(df["start_date"])
        df["end_dt"]   = pd.to_datetime(df["end_date"]) + pd.Timedelta(days=1)

        df["colour"] = df["status"].map(GANTT_STATUS_COLOUR).fillna("#2a2d35")
        df["label"]  = df.apply(
            lambda r: f"{r['title']}" + (f" [{r['assignee']}]" if r.get("assignee") else ""),
            axis=1
        )
        # Category swimlane — fall back to assignee then "General"
        df["swim"] = df["category"].fillna("").replace("", None)
        df["swim"] = df["swim"].fillna(df["assignee"].fillna("").replace("", None))
        df["swim"] = df["swim"].fillna("General")

        fig = px.timeline(
            df,
            x_start="start_dt",
            x_end="end_dt",
            y="label",
            color="status",
            color_discrete_map=GANTT_STATUS_COLOUR,
            custom_data=["id", "assignee", "status", "notes", "dependencies"],
        )

        # Draw dependency arrows
        id_to_row = {int(r["id"]): r for _, r in df.iterrows()}
        shapes, annotations = [], []
        for _, row in df.iterrows():
            deps_str = str(row.get("dependencies") or "")
            if not deps_str.strip():
                continue
            for dep_id_str in deps_str.split(","):
                dep_id_str = dep_id_str.strip()
                if not dep_id_str.isdigit():
                    continue
                dep_id = int(dep_id_str)
                if dep_id not in id_to_row:
                    continue
                dep_row = id_to_row[dep_id]
                shapes.append(dict(
                    type="line",
                    x0=dep_row["end_dt"], y0=dep_row["label"],
                    x1=row["start_dt"],   y1=row["label"],
                    line=dict(color="#c9a84c", width=1, dash="dot"),
                    xref="x", yref="y",
                ))

        fig.update_layout(
            plot_bgcolor  ="#0b0c0e",
            paper_bgcolor ="#0b0c0e",
            font=dict(family="Share Tech Mono, monospace", color="#c8cdd8", size=11),
            xaxis=dict(
                showgrid=True, gridcolor="#1e2128", gridwidth=1,
                tickfont=dict(color="#5a6070", size=10),
                title=None,
                rangeselector=dict(
                    bgcolor="#111318", activecolor="#c9a84c",
                    font=dict(color="#c8cdd8"),
                    buttons=[
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(step="all", label="ALL"),
                    ],
                ),
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(color="#c8cdd8", size=10),
                title=None,
                autorange="reversed",
            ),
            legend=dict(
                bgcolor="#111318", bordercolor="#2a2d35", borderwidth=1,
                font=dict(color="#c8cdd8", size=10),
                title=dict(text="STATUS", font=dict(color="#c9a84c")),
            ),
            shapes=shapes,
            margin=dict(l=20, r=20, t=20, b=20),
            height=max(300, len(df) * 38 + 80),
            hoverlabel=dict(bgcolor="#111318", font=dict(family="Share Tech Mono")),
        )
        fig.update_traces(
            marker_line_color="#0b0c0e",
            marker_line_width=1,
        )
        # Today marker — add_vline annotation is broken in newer Plotly,
        # use add_shape + add_annotation instead
        today_str = date.today().isoformat()
        fig.add_shape(
            type="line",
            x0=today_str, x1=today_str, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="#c9a84c", width=1, dash="dash"),
        )
        fig.add_annotation(
            x=today_str, y=1, xref="x", yref="paper",
            text="TODAY", showarrow=False,
            font=dict(color="#c9a84c", size=9, family="Share Tech Mono"),
            yanchor="bottom",
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No tasks yet. Add tasks below or sync from your action items.", icon="ℹ️")

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # SYNC FROM ACTION ITEMS (Weebo)
    # ─────────────────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("SYNC FROM ACTION ITEMS")
        st.caption("Weebo reads your open action items and proposes Gantt tasks with estimated dates and dependencies.")

        sc1, sc2 = st.columns([3, 1])
        anchor_date = sc1.date_input(
            "Schedule anchor (project start or today)",
            value=date.today(),
            key="gantt_anchor",
        )
        do_sync = sc2.button("Generate Plan", type="primary",
                             use_container_width=True, key="gantt_sync")

        if do_sync:
            with st.spinner("Weebo is reading your action items and building a schedule…"):
                try:
                    action_rows = fetch_action_items()
                    open_items  = [a for a in action_rows
                                   if a.get("status") != "Complete"]

                    if not open_items:
                        st.warning("No open action items found — mark some as Not Started or In Progress first.")
                    else:
                        def _s(obj):
                            return obj.isoformat() if hasattr(obj, "isoformat") else str(obj or "")

                        items_text = "\n".join(
                            f"- ID {a['id']}: {a['action_text']} "
                            f"[responsible: {a.get('responsible') or 'unassigned'}, "
                            f"due: {_s(a.get('due_date'))}, "
                            f"status: {a.get('status')}]"
                            for a in open_items
                        )

                        existing_tasks_text = ""
                        if tasks:
                            existing_tasks_text = "\n\nExisting Gantt tasks (avoid duplicating):\n" + "\n".join(
                                f"- ID {t['id']}: {t['title']} "
                                f"({_s(t.get('start_date'))} → {_s(t.get('end_date'))})"
                                for t in tasks
                            )

                        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

                        system = f"""You are a project planning assistant for a hardware test engineering team.
Your job is to convert a list of action items into a structured Gantt chart schedule.

Today is {date.today().isoformat()}.
Schedule anchor (project start): {anchor_date.isoformat()}.

Rules:
- Return ONLY a valid JSON array, no markdown, no explanation.
- Each element is a task object with these exact keys:
  {{
    "title":         string  (concise task name, max 60 chars),
    "assignee":      string  (person's name, or "" if unassigned),
    "start_date":    string  (YYYY-MM-DD),
    "end_date":      string  (YYYY-MM-DD, must be >= start_date),
    "status":        string  ("Not Started" | "In Progress" | "Complete" | "Blocked"),
    "dependencies":  string  (comma-separated task INDEX values from THIS array, e.g. "0,2", or ""),
    "action_item_id": number | null  (the source action item ID if derived from one),
    "category":      string  (logical group, e.g. "Procurement", "Testing", "Infrastructure"),
    "notes":         string
  }}
- Group related items into logical categories.
- Estimate durations based on complexity — simple tasks 1-3 days, complex 1-2 weeks.
- Sequence tasks logically — prerequisites before dependents.
- If an action item has a due_date, try to end the task by that date.
- dependencies references the 0-based INDEX of other tasks in the array you return.
- Return between 1 and 30 tasks.
"""

                        prompt = f"""Convert these open action items into a Gantt schedule:

{items_text}{existing_tasks_text}

Return only the JSON array of task objects."""

                        response = client.messages.create(
                            model=CLAUDE_MODEL,
                            max_tokens=2048,
                            system=system,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        raw = response.content[0].text.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.lower().startswith("json"):
                                raw = raw[4:]
                            raw = raw.strip()

                        proposed = json.loads(raw)

                        # Convert dependency indices to actual IDs after insert
                        # First insert all tasks, then update dependencies
                        # We'll resolve indices → IDs post-insert
                        id_map = {}   # index → db id
                        for idx, task in enumerate(proposed):
                            # Temporarily clear dependencies — resolve after
                            task_copy = dict(task)
                            task_copy["dependencies"] = ""
                            result = create_gantt_task(task_copy)
                            id_map[idx] = result["id"]

                        # Second pass: update dependencies using real IDs
                        for idx, task in enumerate(proposed):
                            dep_str = str(task.get("dependencies") or "").strip()
                            if dep_str:
                                real_deps = []
                                for d in dep_str.split(","):
                                    d = d.strip()
                                    if d.isdigit() and int(d) in id_map:
                                        real_deps.append(str(id_map[int(d)]))
                                if real_deps:
                                    update_gantt_task(id_map[idx], {
                                        **{k: task.get(k) for k in
                                           ["title","assignee","start_date","end_date",
                                            "status","notes","category"]},
                                        "dependencies": ",".join(real_deps),
                                    })

                        st.success(f"✅ {len(proposed)} tasks added to Gantt.")
                        st.cache_data.clear()
                        st.rerun()

                except json.JSONDecodeError as e:
                    st.error(f"Weebo returned invalid JSON: {e}\n\nTry again.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # ADD TASK MANUALLY
    # ─────────────────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("ADD TASK")
        with st.form("add_gantt_form"):
            gc1, gc2 = st.columns(2)
            g_title    = gc1.text_input("Title *", placeholder="Task name")
            g_category = gc2.text_input("Category", placeholder="e.g. Testing, Procurement")

            gc3, gc4, gc5 = st.columns(3)
            g_assignee = gc3.selectbox("Assignee", [""] + TEAM_MEMBERS, key="g_assignee")
            g_start    = gc4.date_input("Start Date *", value=date.today(), key="g_start")
            g_end      = gc5.date_input("End Date *",   value=date.today() + timedelta(days=7), key="g_end")

            gc6, gc7 = st.columns(2)
            g_status = gc6.selectbox("Status", GANTT_STATUS_OPTIONS, key="g_status")

            # Build dependency options from existing tasks
            dep_options = {str(t["id"]): f"#{t['id']} — {t['title'][:50]}" for t in tasks}
            g_deps = gc7.multiselect(
                "Depends on",
                options=list(dep_options.keys()),
                format_func=lambda x: dep_options.get(x, x),
                key="g_deps",
            )
            g_notes = st.text_area("Notes", height=60, key="g_notes")

            do_add = st.form_submit_button("Add Task", type="primary")

        if do_add:
            if not g_title.strip():
                st.warning("Title is required.")
            elif g_end < g_start:
                st.warning("End date must be on or after start date.")
            else:
                try:
                    create_gantt_task({
                        "title":       g_title,
                        "assignee":    g_assignee,
                        "start_date":  g_start,
                        "end_date":    g_end,
                        "status":      g_status,
                        "dependencies": ",".join(g_deps),
                        "category":    g_category,
                        "notes":       g_notes,
                    })
                    st.success(f"Task '{g_title}' added.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # EDIT / DELETE EXISTING TASKS
    # ─────────────────────────────────────────────────────────────────────────
    if tasks:
        with st.container(border=True):
            st.subheader("EDIT TASKS")

            for t in tasks:
                tid      = t["id"]
                t_start  = t["start_date"] if isinstance(t["start_date"], date) else pd.to_datetime(t["start_date"]).date()
                t_end    = t["end_date"]   if isinstance(t["end_date"],   date) else pd.to_datetime(t["end_date"]).date()
                t_status = t.get("status","Not Started")
                colour   = GANTT_STATUS_COLOUR.get(t_status, "#2a2d35")

                # Compact header line
                dep_preview = f" ← {t['dependencies']}" if t.get("dependencies") else ""
                with st.expander(
                    f"#{tid}  {t['title']}  ·  {t_start} → {t_end}  ·  {t_status}{dep_preview}"
                ):
                    with st.form(key=f"gantt_form_{tid}"):
                        fe1, fe2 = st.columns(2)
                        fe_title    = fe1.text_input("Title", value=t["title"], key=f"gt_{tid}")
                        fe_category = fe2.text_input("Category", value=t.get("category","") or "", key=f"gcat_{tid}")

                        fe3, fe4, fe5 = st.columns(3)
                        cur_assignee = t.get("assignee","") or ""
                        a_opts = [""] + TEAM_MEMBERS
                        a_idx  = a_opts.index(cur_assignee) if cur_assignee in a_opts else 0
                        fe_assignee = fe3.selectbox("Assignee", a_opts, index=a_idx, key=f"ga_{tid}")
                        fe_start    = fe4.date_input("Start", value=t_start, key=f"gs_{tid}")
                        fe_end      = fe5.date_input("End",   value=t_end,   key=f"ge_{tid}")

                        fe6, fe7 = st.columns(2)
                        s_idx  = GANTT_STATUS_OPTIONS.index(t_status) if t_status in GANTT_STATUS_OPTIONS else 0
                        fe_status = fe6.selectbox("Status", GANTT_STATUS_OPTIONS, index=s_idx, key=f"gst_{tid}")

                        # Dependency multiselect — exclude self
                        dep_opts  = {str(x["id"]): f"#{x['id']} — {x['title'][:45]}"
                                     for x in tasks if x["id"] != tid}
                        cur_deps  = [d.strip() for d in str(t.get("dependencies") or "").split(",") if d.strip()]
                        valid_cur_deps = [d for d in cur_deps if d in dep_opts]
                        fe_deps   = fe7.multiselect(
                            "Depends on",
                            options=list(dep_opts.keys()),
                            default=valid_cur_deps,
                            format_func=lambda x: dep_opts.get(x, x),
                            key=f"gdep_{tid}",
                        )
                        fe_notes = st.text_area("Notes", value=t.get("notes","") or "", height=60, key=f"gn_{tid}")

                        bf1, bf2, _ = st.columns([1, 1, 4])
                        do_save_t = bf1.form_submit_button("Save",   type="primary", use_container_width=True)
                        do_del_t  = bf2.form_submit_button("Delete", type="secondary", use_container_width=True)

                    if do_save_t:
                        if fe_end < fe_start:
                            st.warning("End date must be on or after start date.")
                        else:
                            try:
                                update_gantt_task(tid, {
                                    "title":        fe_title,
                                    "assignee":     fe_assignee,
                                    "start_date":   fe_start,
                                    "end_date":     fe_end,
                                    "status":       fe_status,
                                    "dependencies": ",".join(fe_deps),
                                    "category":     fe_category,
                                    "notes":        fe_notes,
                                })
                                st.success(f"Task #{tid} updated.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                    if do_del_t:
                        try:
                            delete_gantt_task(tid)
                            st.warning(f"Task #{tid} deleted.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SENSOR VIEW
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Sensor View":
    import pandas as pd
    import plotly.graph_objects as go
    from datetime import datetime, timedelta, timezone
    from db_logger import fetch_sensor_data, fetch_observations_in_window

    st.header("SENSOR VIEW")
    st.caption("Process tag data with qualitative observation overlays from voice memos.")

    # ── Time window ───────────────────────────────────────────────────────────
    now_utc = datetime.now(timezone.utc)
    default_start = now_utc - timedelta(hours=4)

    with st.container(border=True):
        st.subheader("TIME WINDOW  (UTC)")
        tc1, tc2, tc3, tc4 = st.columns(4)
        sv_sd = tc1.date_input("Start Date", value=default_start.date(), key="sv_sd")
        sv_st = tc2.time_input("Start Time", value=default_start.replace(second=0, microsecond=0).time(), key="sv_st")
        sv_ed = tc3.date_input("End Date",   value=now_utc.date(), key="sv_ed")
        sv_et = tc4.time_input("End Time",   value=now_utc.replace(second=0, microsecond=0).time(), key="sv_et")

    start_dt = datetime(sv_sd.year, sv_sd.month, sv_sd.day,
                        sv_st.hour, sv_st.minute, tzinfo=timezone.utc)
    end_dt   = datetime(sv_ed.year, sv_ed.month, sv_ed.day,
                        sv_et.hour, sv_et.minute, tzinfo=timezone.utc)

    duration = end_dt - start_dt
    if duration.total_seconds() > 0:
        if duration > timedelta(hours=4):
            res_label = "15-sec aggregates"
        elif duration >= timedelta(minutes=31):
            res_label = "1-sec aggregates"
        else:
            res_label = "raw data"
        st.caption(f"Window: {duration}  ·  Resolution: {res_label}")

    # ── Tag configuration ─────────────────────────────────────────────────────
    if "sv_tags" not in st.session_state:
        st.session_state.sv_tags = [
            {"db_name": "M130_RefFreq", "display": "MC130_SP",  "scale": round(5.0 / 3, 4)},
            {"db_name": "AO_AOV140",    "display": "AOV140_SP", "scale": 1.0},
        ]

    with st.container(border=True):
        st.subheader("TAGS")
        st.caption("DB Tag Name  ·  Display Label  ·  Scale Factor")

        # Column headers
        hc1, hc2, hc3, hc4 = st.columns([3, 3, 2, 1])
        hc1.markdown("**DB Tag Name**")
        hc2.markdown("**Display Label**")
        hc3.markdown("**Scale Factor**")

        tags_to_remove = []
        for i, tag in enumerate(st.session_state.sv_tags):
            rc1, rc2, rc3, rc4 = st.columns([3, 3, 2, 1])
            new_db    = rc1.text_input("db",    value=tag["db_name"], key=f"sv_db_{i}",    label_visibility="collapsed")
            new_disp  = rc2.text_input("disp",  value=tag["display"],  key=f"sv_disp_{i}",  label_visibility="collapsed")
            new_scale = rc3.number_input("scale", value=float(tag["scale"]), key=f"sv_scale_{i}",
                                         step=0.0001, format="%.4f", label_visibility="collapsed")
            if rc4.button("✕", key=f"sv_rm_{i}", use_container_width=True):
                tags_to_remove.append(i)
            st.session_state.sv_tags[i] = {"db_name": new_db, "display": new_disp, "scale": new_scale}

        for idx in sorted(tags_to_remove, reverse=True):
            st.session_state.sv_tags.pop(idx)
            st.rerun()

        if st.button("＋  Add Tag", key="sv_add"):
            st.session_state.sv_tags.append({"db_name": "", "display": "", "scale": 1.0})
            st.rerun()

    # ── Fetch button ──────────────────────────────────────────────────────────
    sv_fetch = st.button("FETCH DATA", type="primary", key="sv_fetch")

    if "sv_result" not in st.session_state:
        st.session_state.sv_result = None
        st.session_state.sv_obs    = None

    if sv_fetch:
        if end_dt <= start_dt:
            st.error("End time must be after start time.")
        else:
            valid_tags = [t for t in st.session_state.sv_tags if t["db_name"].strip()]
            if not valid_tags:
                st.warning("Add at least one tag with a DB Tag Name.")
            else:
                with st.spinner("Fetching sensor data…"):
                    try:
                        db_names = [t["db_name"].strip() for t in valid_tags]
                        rows     = fetch_sensor_data(start_dt, end_dt, db_names)
                        obs      = fetch_observations_in_window(start_dt, end_dt)
                        st.session_state.sv_result = {"rows": rows, "tags": valid_tags}
                        st.session_state.sv_obs    = obs
                    except Exception as e:
                        st.error(f"Error fetching data: {e}")
                        st.session_state.sv_result = None

    # ── Chart ─────────────────────────────────────────────────────────────────
    sv_result = st.session_state.get("sv_result")
    sv_obs    = st.session_state.get("sv_obs") or []

    if sv_result is not None:
        rows = sv_result["rows"]
        tags = sv_result["tags"]

        if not rows:
            st.info("No sensor data found for the selected tags and time window.", icon="ℹ️")
        else:
            df = pd.DataFrame(rows)
            df["time"] = pd.to_datetime(df["time"], utc=True)
            df["val"]  = pd.to_numeric(df["val"], errors="coerce")

            # Apply scale factors
            scale_map   = {t["db_name"]: t["scale"]   for t in tags}
            display_map = {t["db_name"]: t["display"]  for t in tags}
            df["scaled"] = df.apply(lambda r: r["val"] * scale_map.get(r["tagname"], 1.0), axis=1)
            df["label"]  = df["tagname"].map(display_map)

            # Pivot to one column per tag
            pivot = (df.pivot_table(index="time", columns="label", values="scaled", aggfunc="mean")
                       .reset_index())

            TRACE_COLOURS = ["#c9a84c", "#5a9abf", "#7c6a9a", "#4a9a6a", "#bf5a5a", "#9abf5a"]
            fig = go.Figure()

            display_cols = [t["display"] for t in tags if t["display"] in pivot.columns]
            for idx, col in enumerate(display_cols):
                colour  = TRACE_COLOURS[idx % len(TRACE_COLOURS)]
                col_df  = pivot[["time", col]].dropna()
                fig.add_trace(go.Scatter(
                    x=col_df["time"],
                    y=col_df[col],
                    mode="lines",
                    name=col,
                    line=dict(color=colour, width=1.5),
                    hovertemplate=f"<b>{col}</b>  %{{y:.3f}}<extra></extra>",
                ))

            # Observation overlays
            if sv_obs:
                for obs in sv_obs:
                    fig.add_shape(
                        type="line",
                        x0=obs["logged_at"], x1=obs["logged_at"],
                        y0=0, y1=1,
                        xref="x", yref="paper",
                        line=dict(color="#c9a84c", width=1, dash="dot"),
                    )

                obs_hover = [
                    (f"<b>[{o.get('severity', '')}]</b> {o.get('engineer', '')}<br>"
                     f"{(o.get('summary') or o.get('issues_found') or '').replace(chr(10), ' ')[:200]}")
                    for o in sv_obs
                ]
                fig.add_trace(go.Scatter(
                    x=[o["logged_at"] for o in sv_obs],
                    y=[0.97] * len(sv_obs),
                    yaxis="y2",
                    mode="markers",
                    name="Observations",
                    marker=dict(symbol="diamond", size=10, color="#c9a84c",
                                line=dict(color="#0b0c0e", width=1)),
                    text=obs_hover,
                    hovertemplate="<b>Observation</b>  %{x}<br>%{text}<extra></extra>",
                    hoverlabel=dict(
                        bgcolor="#111318",
                        font=dict(family="Share Tech Mono", size=11, color="#c9a84c"),
                        align="left",
                    ),
                ))

            fig.update_layout(
                plot_bgcolor="#0b0c0e",
                paper_bgcolor="#0b0c0e",
                font=dict(family="Share Tech Mono, monospace", color="#c8cdd8", size=11),
                xaxis=dict(
                    showgrid=True, gridcolor="#1e2128", gridwidth=1,
                    tickfont=dict(color="#5a6070", size=10),
                    title=None,
                    rangeslider=dict(visible=True, bgcolor="#111318", thickness=0.06),
                ),
                yaxis=dict(
                    showgrid=True, gridcolor="#1e2128", gridwidth=1,
                    tickfont=dict(color="#c8cdd8", size=10),
                    title="Value",
                    titlefont=dict(color="#5a6070"),
                    zeroline=False,
                ),
                yaxis2=dict(
                    overlaying="y",
                    range=[0, 1],
                    visible=False,
                    fixedrange=True,
                ),
                legend=dict(
                    bgcolor="#111318", bordercolor="#2a2d35", borderwidth=1,
                    font=dict(color="#c8cdd8", size=10),
                ),
                hovermode="x unified",
                margin=dict(l=20, r=20, t=20, b=80),
                height=500,
                hoverlabel=dict(bgcolor="#111318", font=dict(family="Share Tech Mono")),
            )

            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"{len(rows):,} data points  ·  {len(display_cols)} tag(s)  ·  {len(sv_obs)} observation(s)")

        # ── Observations table ─────────────────────────────────────────────────
        st.divider()
        st.subheader("OBSERVATIONS LOG")

        if sv_obs:
            obs_df = pd.DataFrame([{
                "Timestamp (UTC)": (o["logged_at"].strftime("%Y-%m-%d %H:%M:%S")
                                    if hasattr(o["logged_at"], "strftime") else str(o["logged_at"])),
                "Engineer":        o.get("engineer", ""),
                "Activity":        o.get("activity_type", ""),
                "Severity":        o.get("severity", ""),
                "Summary":         o.get("summary", ""),
                "Issues Found":    o.get("issues_found", ""),
                "Maintenance":     o.get("maintenance_done", ""),
            } for o in sv_obs])
            st.dataframe(obs_df, use_container_width=True, hide_index=True)
        else:
            st.info("No observations logged in this time window.", icon="ℹ️")

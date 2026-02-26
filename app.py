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
    "structured_insights": None,   # output from extract_structured()
    "review_items": [],         # flat list of items for Step 4 review
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




REVIEW_CATEGORIES = ["Maintenance", "Observation", "Performance", "Action Item"]

def _to_flat_items(structured):
    """Flatten the 4-category structured dict into a single list for review."""
    items = []
    for r in structured.get("maintenance_performed", []):
        items.append({**r, "_category": "Maintenance",
                      "_text": r.get("activity_performed", "")})
    for r in structured.get("qualitative_observations", []):
        items.append({**r, "_category": "Observation",
                      "_text": r.get("observation", "")})
    for r in structured.get("system_performance", []):
        label = r.get("metric_name", "")
        if r.get("metric_value") is not None:
            label += f" = {r['metric_value']} {r.get('metric_unit') or ''}".rstrip()
        elif r.get("metric_narrative"):
            label = r["metric_narrative"]
        items.append({**r, "_category": "Performance", "_text": label})
    for r in structured.get("action_items", []):
        items.append({**r, "_category": "Action Item",
                      "_text": r.get("action_text", "")})
    return items


def _from_flat_items(items):
    """Re-assemble flat review list back into structured dict for process_transcript."""
    out = {
        "maintenance_performed":    [],
        "qualitative_observations": [],
        "system_performance":       [],
        "action_items":             [],
    }
    for item in items:
        cat = item.get("_category", "Observation")
        # Strip internal keys before storing
        r = {k: v for k, v in item.items() if not k.startswith("_")}
        if cat == "Maintenance":
            # Ensure required field present
            if "_text" in item:
                r["activity_performed"] = r.get("activity_performed") or item["_text"]
            out["maintenance_performed"].append(r)
        elif cat == "Observation":
            if "_text" in item:
                r["observation"] = r.get("observation") or item["_text"]
            out["qualitative_observations"].append(r)
        elif cat == "Performance":
            out["system_performance"].append(r)
        elif cat == "Action Item":
            if "_text" in item:
                r["action_text"] = r.get("action_text") or item["_text"]
            out["action_items"].append(r)
    return out

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
        ["New Entry", "Records", "Actions", "Gantt", "Ask Weebo", "Components"],
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

        if st.button("✨  Extract & Structure",
                     disabled=not st.session_state.transcript.strip(),
                     type="primary"):
            with st.spinner("Sending to Weebo…"):
                try:
                    from extractor import extract_structured
                    structured = extract_structured(st.session_state.transcript)
                    st.session_state.structured_insights = structured
                    st.session_state.review_items = _to_flat_items(structured)
                    st.success("Extraction complete — review and edit below before saving.")
                except Exception as e:
                    st.error(f"Extraction error: {e}")

        if st.session_state.review_items:
            items = st.session_state.review_items
            counts = {c: sum(1 for x in items if x["_category"] == c) for c in REVIEW_CATEGORIES}
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Maintenance",  counts["Maintenance"])
            mc2.metric("Observations", counts["Observation"])
            mc3.metric("Performance",  counts["Performance"])
            mc4.metric("Action Items", counts["Action Item"])
            s = st.session_state.structured_insights or {}
            if s.get("unmatched_components"):
                st.warning(
                    "⚠️ Unmatched components: "
                    + ", ".join(s["unmatched_components"])
                    + " — go to Components page to register them.",
                    icon="⚠️",
                )

    # ── Step 4: Review, Edit & Save ───────────────────────────────────────────
    with st.container(border=True):
        st.subheader("STEP 4 — REVIEW, EDIT & SAVE")

        if not st.session_state.review_items:
            st.caption("Extract insights first to unlock this section.")
        else:
            # Load component list once for all dropdowns
            try:
                from db_logger import fetch_components
                _comp_rows = fetch_components()
                _comp_names = [""] + [r["canonical_name"] for r in _comp_rows]
            except Exception:
                _comp_rows  = []
                _comp_names = [""]

            # Date + save controls
            s4c1, s4c2, s4c3 = st.columns([2, 1, 1])
            f_date_recorded = s4c1.date_input(
                "Date Recorded",
                value=None,
                help="Leave blank for today. Set a past date for historical entries.",
                key="date_recorded",
            )
            do_save  = s4c2.button("💾  Save All", type="primary", use_container_width=True, key="do_save_s4")
            do_clear = s4c3.button("🗑  Clear",    use_container_width=True, key="do_clear_s4")

            st.divider()

            # ── Per-item review cards ─────────────────────────────────────────
            items = st.session_state.review_items
            to_delete = []

            for idx, item in enumerate(items):
                cat    = item.get("_category", "Observation")
                text   = item.get("_text", "")
                comp_c = item.get("component_canonical") or ""
                comp_r = item.get("component_raw") or ""
                comp_display = comp_c or comp_r or "—"

                CAT_ICON = {
                    "Maintenance": "🔧",
                    "Observation": "👁",
                    "Performance": "📊",
                    "Action Item": "✅",
                }
                icon = CAT_ICON.get(cat, "•")
                exp_label = f"{icon}  **[{cat}]**  {text[:80]}{'…' if len(text)>80 else ''}  ·  _{comp_display}_"

                with st.expander(exp_label, expanded=False):
                    col_cat, col_comp = st.columns([1, 2])

                    # Category selector
                    cat_idx = REVIEW_CATEGORIES.index(cat) if cat in REVIEW_CATEGORIES else 0
                    new_cat = col_cat.selectbox(
                        "Category",
                        REVIEW_CATEGORIES,
                        index=cat_idx,
                        key=f"cat_{idx}",
                    )
                    item["_category"] = new_cat

                    # Component selector
                    # Show canonical list; if current value not in list, add it as option
                    comp_opts = list(_comp_names)
                    cur_comp_val = comp_c  # use canonical if set
                    if cur_comp_val and cur_comp_val not in comp_opts:
                        comp_opts.append(cur_comp_val)
                    comp_idx = comp_opts.index(cur_comp_val) if cur_comp_val in comp_opts else 0
                    new_comp = col_comp.selectbox(
                        "Component",
                        comp_opts,
                        index=comp_idx,
                        key=f"comp_{idx}",
                    )
                    item["component_canonical"] = new_comp or None
                    # Preserve raw if no canonical selected
                    if not new_comp and comp_r:
                        item["component_raw"] = comp_r

                    # ── Category-specific fields ──────────────────────────────
                    if new_cat == "Maintenance":
                        f1, f2, f3 = st.columns([3, 1, 1])
                        item["activity_performed"] = f1.text_area(
                            "Activity Performed",
                            value=item.get("activity_performed") or text,
                            height=70,
                            key=f"mact_{idx}",
                        )
                        item["_text"] = item["activity_performed"]
                        sev_opts = SEVERITY_OPTIONS
                        sev_i = sev_opts.index(item.get("severity","None")) if item.get("severity") in sev_opts else 4
                        item["severity"] = f2.selectbox("Severity", sev_opts, index=sev_i, key=f"msev_{idx}")
                        item["duration_hours"] = f3.number_input(
                            "Hours", value=float(item.get("duration_hours") or 0),
                            min_value=0.0, step=0.25, key=f"mdur_{idx}"
                        ) or None
                        out_opts = ["", "resolved", "monitoring", "escalated"]
                        out_i = out_opts.index(item.get("outcome") or "") if (item.get("outcome") or "") in out_opts else 0
                        item["outcome"] = st.selectbox("Outcome", out_opts, index=out_i, key=f"mout_{idx}") or None

                    elif new_cat == "Observation":
                        item["observation"] = st.text_area(
                            "Observation",
                            value=item.get("observation") or text,
                            height=70,
                            key=f"oobs_{idx}",
                        )
                        item["_text"] = item["observation"]
                        oc1, oc2, oc3 = st.columns(3)
                        type_opts = ["anomaly","degradation","normal","informational","concern"]
                        type_i = type_opts.index(item.get("observation_type","informational")) if item.get("observation_type") in type_opts else 3
                        item["observation_type"] = oc1.selectbox("Type", type_opts, index=type_i, key=f"otyp_{idx}")
                        sev_i = SEVERITY_OPTIONS.index(item.get("severity","None")) if item.get("severity") in SEVERITY_OPTIONS else 4
                        item["severity"] = oc2.selectbox("Severity", SEVERITY_OPTIONS, index=sev_i, key=f"osev_{idx}")
                        item["follow_up_required"] = oc3.checkbox("Follow Up Required",
                            value=bool(item.get("follow_up_required", False)), key=f"ofu_{idx}")

                    elif new_cat == "Performance":
                        pc1, pc2, pc3 = st.columns([2, 1, 1])
                        item["metric_name"] = pc1.text_input(
                            "Metric",
                            value=item.get("metric_name",""),
                            key=f"pmn_{idx}",
                        )
                        item["_text"] = item["metric_name"]
                        item["metric_value"] = pc2.number_input(
                            "Value",
                            value=float(item.get("metric_value") or 0),
                            key=f"pmv_{idx}",
                        ) or None
                        item["metric_unit"] = pc3.text_input(
                            "Unit",
                            value=item.get("metric_unit") or "",
                            key=f"pmu_{idx}",
                        ) or None
                        pc4, pc5, pc6 = st.columns(3)
                        item["metric_narrative"] = pc4.text_input(
                            "Narrative (if no numeric)",
                            value=item.get("metric_narrative") or "",
                            key=f"pnar_{idx}",
                        ) or None
                        item["within_spec"] = pc5.selectbox(
                            "Within Spec",
                            [None, True, False],
                            index=[None, True, False].index(item.get("within_spec")),
                            format_func=lambda x: "Unknown" if x is None else ("Yes" if x else "No"),
                            key=f"pws_{idx}",
                        )
                        item["anomaly_flag"] = pc6.checkbox(
                            "Anomaly", value=bool(item.get("anomaly_flag", False)), key=f"pan_{idx}"
                        )

                    elif new_cat == "Action Item":
                        item["action_text"] = st.text_area(
                            "Action",
                            value=item.get("action_text") or text,
                            height=70,
                            key=f"aat_{idx}",
                        )
                        item["_text"] = item["action_text"]
                        ac1, ac2 = st.columns(2)
                        resp_opts = [""] + TEAM_MEMBERS
                        resp_i = resp_opts.index(item.get("responsible") or "") if (item.get("responsible") or "") in resp_opts else 0
                        item["responsible"] = ac1.selectbox("Responsible", resp_opts, index=resp_i, key=f"aresp_{idx}") or None
                        item["due_date"] = ac2.date_input("Due Date", value=item.get("due_date"), key=f"adue_{idx}")
                        if item.get("time_reference"):
                            st.caption(f"Time reference: _{item['time_reference']}_")

                    # Delete button
                    if st.button("🗑  Remove this item", key=f"del_{idx}", use_container_width=False):
                        to_delete.append(idx)

            # Process deletions
            if to_delete:
                st.session_state.review_items = [
                    x for i, x in enumerate(items) if i not in to_delete
                ]
                st.rerun()

            # ── Save ─────────────────────────────────────────────────────────
            if do_save:
                with st.spinner("Saving to all tables…"):
                    try:
                        from db_logger import process_transcript
                        # Re-assemble structured from current review state
                        final_structured = _from_flat_items(st.session_state.review_items)
                        # Preserve unmatched from original extraction
                        final_structured["unmatched_components"] = (
                            st.session_state.structured_insights or {}
                        ).get("unmatched_components", [])

                        result = process_transcript(
                            structured    = final_structured,
                            raw_transcript= st.session_state.transcript,
                            source_file   = st.session_state.source_label or "Unknown",
                            engineer      = engineer,
                            date_recorded = f_date_recorded,
                        )
                        msg = (
                            f"✅  Saved! Memo ID **{result['memo_id']}** — "
                            f"{result['n_maintenance']} maintenance · "
                            f"{result['n_observations']} observations · "
                            f"{result['n_performance']} metrics · "
                            f"{result['n_actions']} action items"
                        )
                        st.success(msg)
                        if result.get("unmatched_components"):
                            st.warning(
                                "Unmatched components saved without canonical link: "
                                + ", ".join(result["unmatched_components"])
                            )
                        st.session_state.structured_insights = None
                        st.session_state.review_items = []
                        _clear_entry()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database error: {e}")

            if do_clear:
                st.session_state.structured_insights = None
                st.session_state.review_items = []
                _clear_entry()
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RECORDS# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RECORDS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Records":
    import pandas as pd
    from db_logger import (fetch_maintenance_logs, fetch_observation_logs,
                           fetch_performance_logs)

    st.header("RECORDS")

    # ── Shared filters ────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("FILTERS")
        fc1, fc2, fc3 = st.columns(3)
        f_eng  = fc1.selectbox("Engineer", ["All engineers"] + TEAM_MEMBERS, key="rec_eng")
        f_srch = fc2.text_input("Keyword search", placeholder="component, activity, metric…", key="rec_srch")
        f_log_type = fc3.selectbox(
            "Log Type",
            ["Maintenance", "Observations", "Performance", "Legacy (memo_log)"],
            key="rec_logtype",
        )
        fd1, fd2, fd3 = st.columns(3)
        f_from = fd1.date_input("From", value=None, key="rec_from")
        f_to   = fd2.date_input("To",   value=None, key="rec_to")
        with fd3:
            st.write(""); st.write("")
            rc1, rc2 = st.columns(2)
            do_apply = rc1.button("Apply",         type="primary", use_container_width=True, key="rec_apply")
            do_clear = rc2.button("Clear filters",                 use_container_width=True, key="rec_clear")

    if do_clear:
        st.cache_data.clear()
        st.rerun()
    if do_apply:
        st.cache_data.clear()

    eng_filter  = "" if f_eng  == "All engineers" else f_eng
    srch_filter = f_srch or ""
    from_str    = str(f_from) if f_from else ""
    to_str      = str(f_to)   if f_to   else ""

    # ── MAINTENANCE ───────────────────────────────────────────────────────────
    if f_log_type == "Maintenance":
        try:
            rows = fetch_maintenance_logs(eng_filter, srch_filter, from_str, to_str)
        except Exception as e:
            st.error(f"Could not load maintenance logs: {e}"); rows = []

        st.caption(f"**{len(rows)}** maintenance record{'s' if len(rows)!=1 else ''}")
        st.divider()
        if not rows:
            st.info("No maintenance records match your filters.", icon="ℹ️")
        else:
            for row in rows:
                ts     = row.get("date_recorded")
                ts_str = ts.strftime("%Y-%m-%d  %H:%M") if hasattr(ts,"strftime") else str(ts)
                sev    = row.get("severity","") or ""
                badge  = SEV_BADGE.get(sev,"⚪")
                comp   = row.get("component_canonical") or row.get("component_raw","—")
                act    = (row.get("activity_performed") or "")[:80]
                with st.expander(f"{badge}  **{ts_str}**  ·  {row.get('engineer','')}  ·  {comp}  ·  {act}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Component:** {comp}")
                    c1.markdown(f"**Activity:** {row.get('activity_performed','')}")
                    c1.markdown(f"**Duration:** {row.get('duration_hours') or '—'} hrs")
                    c2.markdown(f"**Severity:** {sev or '—'}")
                    c2.markdown(f"**Outcome:** {row.get('outcome') or '—'}")
                    c2.markdown(f"**Engineer:** {row.get('engineer','')}")

    # ── OBSERVATIONS ──────────────────────────────────────────────────────────
    elif f_log_type == "Observations":
        try:
            rows = fetch_observation_logs(eng_filter, srch_filter, from_str, to_str)
        except Exception as e:
            st.error(f"Could not load observation logs: {e}"); rows = []

        st.caption(f"**{len(rows)}** observation record{'s' if len(rows)!=1 else ''}")
        st.divider()
        if not rows:
            st.info("No observations match your filters.", icon="ℹ️")
        else:
            for row in rows:
                ts     = row.get("date_recorded")
                ts_str = ts.strftime("%Y-%m-%d  %H:%M") if hasattr(ts,"strftime") else str(ts)
                sev    = row.get("severity","") or ""
                badge  = SEV_BADGE.get(sev,"⚪")
                comp   = row.get("component_canonical") or row.get("component_raw","—")
                obs    = (row.get("observation") or "")[:80]
                fu     = "⚠️ Follow-up required" if row.get("follow_up_required") else ""
                with st.expander(f"{badge}  **{ts_str}**  ·  {row.get('engineer','')}  ·  {comp}  ·  {obs}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Component:** {comp}")
                    c1.markdown(f"**Observation:** {row.get('observation','')}")
                    c1.markdown(f"**Type:** {row.get('observation_type','—')}")
                    c2.markdown(f"**Severity:** {sev or '—'}")
                    c2.markdown(f"**Engineer:** {row.get('engineer','')}")
                    if fu:
                        c2.warning(fu)

    # ── PERFORMANCE ───────────────────────────────────────────────────────────
    elif f_log_type == "Performance":
        try:
            rows = fetch_performance_logs(eng_filter, srch_filter, from_str, to_str)
        except Exception as e:
            st.error(f"Could not load performance logs: {e}"); rows = []

        st.caption(f"**{len(rows)}** performance record{'s' if len(rows)!=1 else ''}")

        # Summary dataframe at top for quick scanning
        if rows:
            pdf = pd.DataFrame([{
                "date":      r.get("date_recorded").strftime("%Y-%m-%d") if hasattr(r.get("date_recorded"),"strftime") else str(r.get("date_recorded","")),
                "engineer":  r.get("engineer",""),
                "component": r.get("component_canonical") or r.get("component_raw",""),
                "metric":    r.get("metric_name",""),
                "value":     r.get("metric_value"),
                "unit":      r.get("metric_unit",""),
                "anomaly":   "⚠️" if r.get("anomaly_flag") else "",
                "in_spec":   "✅" if r.get("within_spec") == True else ("❌" if r.get("within_spec") == False else "—"),
            } for r in rows])
            st.dataframe(pdf, use_container_width=True, hide_index=True,
                         column_config={
                             "value": st.column_config.NumberColumn("Value"),
                             "anomaly": st.column_config.TextColumn("⚠️"),
                             "in_spec": st.column_config.TextColumn("In Spec"),
                         })
        else:
            st.info("No performance records match your filters.", icon="ℹ️")

    # ── LEGACY (memo_log) ─────────────────────────────────────────────────────
    elif f_log_type == "Legacy (memo_log)":
        try:
            rows = _load_records(
                "" if f_eng == "All engineers" else f_eng,
                "", "",  # no activity_type or severity filter
                srch_filter, f_from, f_to,
            )
        except Exception as e:
            st.error(f"Could not load records: {e}"); rows = []

        tc1, tc2 = st.columns([4, 1])
        tc1.caption(f"**{len(rows)}** record{'s' if len(rows)!=1 else ''}")
        if tc2.button("📊  Export Excel", use_container_width=True, key="rec_export"):
            if not rows:
                st.warning("No records to export.")
            else:
                try:
                    from excel_export import export_to_excel
                    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                        export_to_excel(rows, tmp.name)
                        excel_bytes = open(tmp.name, "rb").read()
                    fname = f"memo_log_{datetime.now():%Y%m%d_%H%M}.xlsx"
                    st.download_button("⬇️  Download Excel", data=excel_bytes, file_name=fname,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(f"Export error: {e}")

        st.divider()
        if not rows:
            st.info("No records match your filters.", icon="ℹ️")
        else:
            for row in rows:
                ts     = row.get("logged_at")
                ts_str = ts.strftime("%Y-%m-%d  %H:%M UTC") if hasattr(ts,"strftime") else str(ts)
                sev    = row.get("severity","") or ""
                badge  = SEV_BADGE.get(sev,"⚪")
                summary_preview = (row.get("summary") or "")[:90]
                with st.expander(
                    f"{badge}  **{ts_str}**  ·  {row.get('engineer','')}  ·  {summary_preview}"
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
# PAGE: COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Components":
    import pandas as pd
    from db_logger import fetch_components, upsert_component, fetch_unmatched_components

    st.header("COMPONENTS")
    st.caption("Canonical component registry. Add aliases so Weebo can recognise every name engineers use for the same part.")

    # ── Unmatched components alert ────────────────────────────────────────────
    try:
        unmatched = fetch_unmatched_components()
        if unmatched:
            st.warning(
                f"**{len(unmatched)} unmatched component string{'s' if len(unmatched)>1 else ''}** "
                "found in logs — not linked to any canonical component. "
                "Add them below or add aliases to existing components.",
                icon="⚠️"
            )
            with st.expander("Show unmatched strings"):
                um_df = pd.DataFrame(unmatched)
                st.dataframe(um_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.caption(f"Could not load unmatched components: {e}")

    # ── Component list ────────────────────────────────────────────────────────
    try:
        components = fetch_components(include_inactive=True)
    except Exception as e:
        st.error(f"Could not load components: {e}")
        components = []

    st.subheader(f"REGISTRY  ({len(components)} components)")

    for comp in components:
        cid      = comp["id"]
        active   = comp.get("active", True)
        inactive_label = "" if active else "  [INACTIVE]"
        aliases_str = ", ".join(comp.get("aliases") or [])

        with st.expander(
            f"**{comp['canonical_name']}**{inactive_label}  ·  "
            f"{comp.get('part_number') or 'no part#'}  ·  "
            f"{comp.get('category') or '—'}  ·  aliases: {aliases_str[:60] or 'none'}"
        ):
            with st.form(key=f"comp_form_{cid}"):
                cf1, cf2 = st.columns(2)
                fc_name  = cf1.text_input("Canonical Name *", value=comp["canonical_name"], key=f"cn_{cid}")
                fc_part  = cf2.text_input("Part Number", value=comp.get("part_number") or "", key=f"pn_{cid}")
                cf3, cf4 = st.columns(2)
                fc_cat   = cf3.text_input("Category", value=comp.get("category") or "", key=f"cat_{cid}")
                fc_sub   = cf4.text_input("Subsystem", value=comp.get("subsystem") or "", key=f"sub_{cid}")
                # Aliases as comma-separated string for editing
                aliases_edit = st.text_input(
                    "Aliases (comma-separated — every name engineers might say)",
                    value=", ".join(comp.get("aliases") or []),
                    placeholder="hp pump, pump #3, HPP-03, high pressure pump",
                    key=f"al_{cid}",
                )
                fc_notes  = st.text_input("Notes", value=comp.get("notes") or "", key=f"nt_{cid}")
                fc_active = st.checkbox("Active", value=bool(active), key=f"act_{cid}")

                bf1, bf2, _ = st.columns([1, 1, 4])
                do_save_c = bf1.form_submit_button("Save", type="primary", use_container_width=True)

            if do_save_c:
                if not fc_name.strip():
                    st.warning("Canonical name is required.")
                else:
                    try:
                        new_aliases = [a.strip().lower() for a in aliases_edit.split(",") if a.strip()]
                        upsert_component({
                            "id":             cid,
                            "canonical_name": fc_name.strip(),
                            "part_number":    fc_part.strip() or None,
                            "category":       fc_cat.strip() or None,
                            "subsystem":      fc_sub.strip() or None,
                            "aliases":        new_aliases,
                            "notes":          fc_notes.strip() or None,
                            "active":         fc_active,
                        })
                        # Force extractor to rebuild its alias cache
                        from extractor import refresh_component_cache
                        refresh_component_cache()
                        st.success(f"Component '{fc_name}' saved.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── Add new component ─────────────────────────────────────────────────────
    st.divider()
    with st.container(border=True):
        st.subheader("ADD COMPONENT")
        with st.form("add_component_form"):
            nc1, nc2 = st.columns(2)
            new_name  = nc1.text_input("Canonical Name *", placeholder="High Pressure Pump 3")
            new_part  = nc2.text_input("Part Number",      placeholder="HPP-03")
            nc3, nc4  = st.columns(2)
            new_cat   = nc3.text_input("Category",   placeholder="Pump")
            new_sub   = nc4.text_input("Subsystem",  placeholder="Hydraulics")
            new_aliases = st.text_input(
                "Aliases (comma-separated)",
                placeholder="hp pump, pump #3, high pressure pump, hpp03",
            )
            new_notes = st.text_input("Notes")
            do_add_c  = st.form_submit_button("Add Component", type="primary")

        if do_add_c:
            if not new_name.strip():
                st.warning("Canonical name is required.")
            else:
                try:
                    aliases_list = [a.strip().lower() for a in new_aliases.split(",") if a.strip()]
                    upsert_component({
                        "canonical_name": new_name.strip(),
                        "part_number":    new_part.strip() or None,
                        "category":       new_cat.strip() or None,
                        "subsystem":      new_sub.strip() or None,
                        "aliases":        aliases_list,
                        "notes":          new_notes.strip() or None,
                        "active":         True,
                    })
                    from extractor import refresh_component_cache
                    refresh_component_cache()
                    st.success(f"Component '{new_name}' added.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

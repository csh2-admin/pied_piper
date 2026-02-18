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
    page_title="Voice Memo Logger",
    page_icon="🎙",
    layout="wide",
    initial_sidebar_state="expanded",
)

SEV_BADGE = {
    "Critical": "🔴", "High": "🟠",
    "Medium":   "🟡", "Low":  "🟢", "None": "⚪",
}
SEVERITY_OPTIONS = ["Critical", "High", "Medium", "Low", "None"]


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "transcript":   "",
    "insights":     {},
    "source_label": "",
    "audio_bytes":  None,
    "audio_suffix": ".wav",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner="Loading records…")
def _load_records(eng, sev, search, d_from, d_to):
    from db_logger import fetch_filtered_rows
    return fetch_filtered_rows(
        engineer  = "" if eng == "All engineers"   else eng,
        severity  = "" if sev == "All severities"  else sev,
        search    = search or "",
        date_from = str(d_from) if d_from else "",
        date_to   = str(d_to)   if d_to   else "",
    )


@st.cache_data(ttl=30, show_spinner=False)
def _db_ping() -> bool:
    try:
        from db_logger import test_connection
        return test_connection() == "ok"
    except Exception:
        return False


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
                "engineer": f_eng, "summary": f_sum,
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
    st.title("🎙 Voice Memo Logger")
    st.caption("Hardware Test — Daily Log")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📝  New Entry", "🗄  Records"],
        label_visibility="collapsed",
    )

    st.divider()
    engineer = st.selectbox("👤  Engineer", TEAM_MEMBERS)

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
if "New Entry" in page:

    st.header("📝  New Entry")

    # ── Step 1: Audio ─────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("Step 1 — Audio")
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
        st.subheader("Step 2 — Transcribe")

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
        st.subheader("Step 3 — Extract with Claude")

        if st.button("✨  Extract Insights",
                     disabled=not st.session_state.transcript.strip(),
                     type="primary"):
            with st.spinner("Sending to Claude…"):
                try:
                    from extractor import extract_insights
                    st.session_state.insights = extract_insights(st.session_state.transcript)
                    st.success("Extraction complete — review below.")
                except Exception as e:
                    st.error(f"Extraction error: {e}")

        if st.session_state.insights:
            ins = st.session_state.insights
            sev = ins.get("severity","None") or "None"
            badge = SEV_BADGE.get(sev,"⚪")

            # Summary + severity header
            hc1, hc2 = st.columns([4, 1])
            hc1.markdown(f"**Summary:** {ins.get('summary','—')}")
            hc2.markdown(f"**Severity:** {badge} {sev}")
            st.divider()

            # Field grid
            gc1, gc2 = st.columns(2)
            for label, key, col in [
                ("System Performance",  "system_performance",  gc1),
                ("Maintenance Done",    "maintenance_done",    gc1),
                ("Issues Found",        "issues_found",        gc1),
                ("Action Items",        "action_items",        gc2),
                ("Components Affected", "components_affected", gc2),
                ("Duration (hrs)",      "duration_hours",      gc2),
            ]:
                v = ins.get(key,"")
                if v:
                    col.markdown(f"**{label}**")
                    col.write(v)

            if ins.get("additional_notes"):
                st.markdown("**Additional Notes**")
                st.write(ins["additional_notes"])

    # ── Step 4: Save ──────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("Step 4 — Save to Database")

        bc1, bc2 = st.columns([1, 1])
        do_save  = bc1.button("💾  Save to Database",
                              disabled=not st.session_state.insights,
                              type="primary", use_container_width=True)
        do_clear = bc2.button("🗑  Clear all",
                              use_container_width=True)

        if do_save:
            with st.spinner("Saving…"):
                try:
                    from db_logger import append_entry, ensure_schema
                    ensure_schema()
                    result = append_entry(
                        st.session_state.insights,
                        st.session_state.transcript,
                        st.session_state.source_label or "Unknown",
                        engineer,
                    )
                    ts = result["logged_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
                    st.success(f"✅  Saved! Row ID **{result['id']}** — {ts}")
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
else:
    st.header("🗄  Records")

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("Filters")
        fc1, fc2, fc3 = st.columns(3)
        f_eng  = fc1.selectbox("Engineer", ["All engineers"] + TEAM_MEMBERS)
        f_sev  = fc2.selectbox("Severity",  ["All severities"] + SEVERITY_OPTIONS)
        f_srch = fc3.text_input("Keyword search",
                                placeholder="summary, issues, components, transcript…")

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
        rows = _load_records(f_eng, f_sev, f_srch, f_from, f_to)
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

            with st.expander(
                f"{badge}  **{ts_str}**  ·  {row.get('engineer','')}  ·  {summary_preview}"
            ):
                _edit_row(row)

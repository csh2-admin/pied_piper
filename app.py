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
STATUS_OPTIONS   = ["Not Started", "In Progress", "Complete"]
STATUS_BADGE     = {"Not Started": "⬜", "In Progress": "🔵", "Complete": "✅"}

ACTIVITY_OPTIONS = [
    "Regular Maintenance",
    "Unplanned Maintenance",
    "Technical Milestone",
    "Logistics",
    "Other",
]


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
    st.title("🎙 Voice Memo Logger")
    st.caption("Hardware Test — Daily Log")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📝  New Entry", "🗄  Records", "✅  Actions"],
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
            st.success("Extraction complete — review and edit fields below before saving.")

    # ── Step 4: Review, Edit & Save ───────────────────────────────────────────
    with st.container(border=True):
        st.subheader("Step 4 — Review, Edit & Save")

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
elif "Records" in page:
    st.header("🗄  Records")

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("Filters")
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
elif "Actions" in page:

    st.header("✅  Action Items")
    st.caption("Tracks all action items extracted from memo entries. Update status as work progresses.")

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
            st.subheader("Add Action Item Manually")
            with st.form("manual_action_form"):
                ma_text = st.text_area("Action Item", height=75,
                    placeholder="Describe the action that needs to be done…")
                mc1, mc2 = st.columns(2)
                ma_eng   = mc1.selectbox("Assigned To", TEAM_MEMBERS, key="ma_eng")
                ma_notes = mc2.text_input("Notes (optional)")
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
                            memo_id=None, action_text=ma_text, engineer=ma_eng
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

                exp_label = f"{badge}  {act_text[:80]}{'…' if len(act_text) > 80 else ''}  ·  *{eng_name}*"
                if memo_sum:
                    exp_label += f"  ·  from: _{memo_sum}_"

                with st.expander(exp_label):
                    # Full action text (read-only display, editable below)
                    st.markdown(f"**Action:** {act_text}")
                    ic1, ic2 = st.columns(2)
                    ic1.caption(f"Assigned to: **{eng_name}**")
                    ic2.caption(f"Last updated: {upd_str}")
                    if memo_id:
                        st.caption(f"From memo ID: {memo_id}" +
                                   (f" — {memo_sum}" if memo_sum else ""))
                    st.write("")

                    # Inline status update form
                    with st.form(key=f"action_form_{item_id}"):
                        sf1, sf2 = st.columns([1, 3])
                        new_status = sf1.selectbox(
                            "Status",
                            STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(cur_status)
                                  if cur_status in STATUS_OPTIONS else 0,
                            key=f"sel_{item_id}",
                        )
                        new_notes = sf2.text_input(
                            "Notes",
                            value=cur_notes,
                            placeholder="Progress notes, blockers, context…",
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
                            update_action_item(item_id, new_status, new_notes)
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

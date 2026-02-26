"""
extractor.py — Multi-category structured extraction from voice memo transcripts.

Extraction flow:
  1. Load canonical components from DB (cached per session)
  2. Build prompt with component list injected
  3. Single Claude API call -> structured JSON with 4 categories
  4. Validate + normalise against canonical component list
  5. Return structured dict ready for process_transcript()
"""

import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PRODUCT_DESCRIPTION

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


# ── Component alias map (module-level cache) ──────────────────────────────────

_alias_map: dict = {}        # lowercase alias -> component_id
_canonical_map: dict = {}    # component_id -> canonical_name
_alias_map_built = False


def refresh_component_cache():
    """Force-rebuild the alias map. Call after adding/editing components."""
    global _alias_map_built
    _alias_map_built = False
    _build_alias_map()


def _build_alias_map():
    global _alias_map, _canonical_map, _alias_map_built
    try:
        from db_logger import fetch_components
        rows = fetch_components()
        _alias_map = {}
        _canonical_map = {}
        for row in rows:
            cid  = row["id"]
            name = row["canonical_name"]
            _canonical_map[cid] = name
            _alias_map[name.lower().strip()] = cid
            if row.get("part_number"):
                _alias_map[row["part_number"].lower().strip()] = cid
            for alias in (row.get("aliases") or []):
                if alias:
                    _alias_map[alias.lower().strip()] = cid
        _alias_map_built = True
    except Exception:
        _alias_map_built = True   # mark done even on failure so we don't retry every call


def _normalise_component(raw):
    """Return canonical_name string for raw component text, or None."""
    if not raw or not str(raw).strip():
        return None
    if not _alias_map_built:
        _build_alias_map()

    raw_clean = raw.lower().strip()

    if raw_clean in _alias_map:
        return _canonical_map[_alias_map[raw_clean]]

    simplified = re.sub(r"[^\w\s]", "", raw_clean).rstrip("s").strip()
    if simplified in _alias_map:
        return _canonical_map[_alias_map[simplified]]

    stripped = re.sub(r"\b(the|a|an|our|main|primary|secondary)\b", "", raw_clean).strip()
    if stripped in _alias_map:
        return _canonical_map[_alias_map[stripped]]

    return None


def get_canonical_components_text():
    """Formatted component list for prompt injection."""
    if not _alias_map_built:
        _build_alias_map()
    try:
        from db_logger import fetch_components
        rows = fetch_components()
        if not rows:
            return "(No canonical components registered — set component_canonical to null for all entries)"
        lines = []
        for row in rows:
            aliases_str = ", ".join(row.get("aliases") or [])
            line = f"  - {row['canonical_name']} (part: {row.get('part_number') or 'N/A'})"
            if aliases_str:
                line += f" — aliases: {aliases_str}"
            lines.append(line)
        return "\n".join(lines)
    except Exception:
        return "(Component list unavailable)"


# ── Extraction prompt ─────────────────────────────────────────────────────────

def _build_system_prompt(canonical_components_text):
    return f"""You are a structured data extraction engine for a hardware test engineering team.
The engineer has recorded a voice memo about {PRODUCT_DESCRIPTION}.
Extract ALL events from the transcript into four categories and return ONLY valid JSON.
No markdown, no explanation — just the JSON object.

CANONICAL COMPONENTS (use ONLY these exact strings for component_canonical):
{canonical_components_text}

If a component does not match any canonical name, set component_canonical to null
and preserve the raw text in component_raw.

Return a JSON object with exactly these four top-level keys:

{{
  "maintenance_performed": [
    {{
      "component_canonical": "exact canonical name from list, or null",
      "component_raw":       "original wording from transcript",
      "activity_performed":  "what was done",
      "duration_hours":      1.5,
      "severity":            "Critical | High | Medium | Low | None",
      "outcome":             "resolved | monitoring | escalated | null",
      "time_reference":      "relative time if mentioned, else null"
    }}
  ],
  "action_items": [
    {{
      "action_text":         "what needs to happen",
      "responsible":         "person name or null",
      "due_date":            null,
      "time_reference":      "relative time if mentioned, else null",
      "component_canonical": "exact canonical name or null",
      "component_raw":       "original wording or null"
    }}
  ],
  "qualitative_observations": [
    {{
      "component_canonical": "exact canonical name or null",
      "component_raw":       "original wording",
      "observation":         "what was observed",
      "observation_type":    "anomaly | degradation | normal | informational | concern",
      "severity":            "Critical | High | Medium | Low | None",
      "follow_up_required":  true,
      "time_reference":      null
    }}
  ],
  "system_performance": [
    {{
      "component_canonical": "exact canonical name or null",
      "component_raw":       "original wording",
      "metric_name":         "pressure | temperature | flow_rate | vibration | rpm | voltage | current | general_condition | other",
      "metric_value":        443.0,
      "metric_unit":         "bar | degC | L/min | rpm | V | A | null",
      "metric_narrative":    "free text if no clean numeric, else null",
      "within_spec":         true,
      "anomaly_flag":        false,
      "time_reference":      null
    }}
  ]
}}

RULES:
- One object per discrete event. A single sentence may produce entries in multiple categories.
- duration_hours: number or null (never a string).
- metric_value: number or null (never a string).
- Use null for any field not mentioned — never invent values.
- Return all four arrays even if empty.
- Do NOT invent dates. Preserve relative references in time_reference.
"""


# ── Public interface ──────────────────────────────────────────────────────────

def extract_structured(transcript):
    """
    Main extraction entry point.
    Returns dict with keys:
      maintenance_performed, action_items, qualitative_observations,
      system_performance, unmatched_components
    """
    canonical_text = get_canonical_components_text()
    system_prompt  = _build_system_prompt(canonical_text)

    client = _get_client()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Transcript:\n\n{transcript}"}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "maintenance_performed":    [],
            "action_items":             [],
            "qualitative_observations": [],
            "system_performance":       [],
            "_parse_error":             raw[:500],
        }

    # Ensure all four keys exist
    for key in ("maintenance_performed", "action_items",
                "qualitative_observations", "system_performance"):
        if key not in data or not isinstance(data[key], list):
            data[key] = []

    # Validate component_canonical values against real canonicals
    if not _alias_map_built:
        _build_alias_map()
    valid_canonicals = set(_canonical_map.values())
    unmatched = set()

    for record_list in (data["maintenance_performed"], data["action_items"],
                        data["qualitative_observations"], data["system_performance"]):
        for record in record_list:
            cc = record.get("component_canonical")
            if cc and cc not in valid_canonicals:
                # LLM hallucinated a canonical — fall back to normalise from raw
                record["component_raw"] = record.get("component_raw") or cc
                record["component_canonical"] = _normalise_component(cc)
            elif cc is None and record.get("component_raw"):
                record["component_canonical"] = _normalise_component(record["component_raw"])

            if record.get("component_raw") and not record.get("component_canonical"):
                unmatched.add(record["component_raw"])

    data["unmatched_components"] = sorted(unmatched)
    return data


# ── Legacy shim — populates memo_log during migration ────────────────────────

ACTIVITY_OPTIONS = [
    "Regular Maintenance", "Unplanned Maintenance",
    "Technical Milestone", "Logistics", "Other",
]


def extract_insights(transcript):
    """
    Calls extract_structured then synthesises legacy memo_log fields.
    Returns a dict compatible with the old format PLUS '_structured' key.
    """
    structured = extract_structured(transcript)

    maint_texts = [r.get("activity_performed","") for r in structured["maintenance_performed"]]
    obs_texts   = [r.get("observation","")         for r in structured["qualitative_observations"]]
    perf_texts  = []
    for r in structured["system_performance"]:
        if r.get("metric_value") is not None:
            perf_texts.append(
                f"{r.get('component_raw') or r.get('component_canonical','')}: "
                f"{r['metric_name']} = {r['metric_value']} {r.get('metric_unit') or ''}".strip()
            )
        elif r.get("metric_narrative"):
            perf_texts.append(r["metric_narrative"])
    action_texts = [r.get("action_text","") for r in structured["action_items"]]

    components = sorted({
        r.get("component_canonical") or r.get("component_raw","")
        for cat in (structured["maintenance_performed"],
                    structured["qualitative_observations"],
                    structured["system_performance"])
        for r in cat
        if r.get("component_canonical") or r.get("component_raw")
    })

    sev_rank = {"Critical":5,"High":4,"Medium":3,"Low":2,"None":1,"":0, None:0}
    all_sevs = (
        [r.get("severity") for r in structured["maintenance_performed"]] +
        [r.get("severity") for r in structured["qualitative_observations"]]
    )
    top_sev = max(all_sevs, key=lambda s: sev_rank.get(s,0), default="None") or "None"
    if top_sev not in ("Critical","High","Medium","Low","None"):
        top_sev = "None"

    total_dur = sum(
        float(r["duration_hours"])
        for r in structured["maintenance_performed"]
        if r.get("duration_hours") is not None
    ) or None

    n_m = len(structured["maintenance_performed"])
    n_o = len(structured["qualitative_observations"])
    n_p = len(structured["system_performance"])
    n_a = len(structured["action_items"])
    parts = []
    if n_m: parts.append(f"{n_m} maintenance activit{'ies' if n_m>1 else 'y'}")
    if n_o: parts.append(f"{n_o} observation{'s' if n_o>1 else ''}")
    if n_p: parts.append(f"{n_p} performance metric{'s' if n_p>1 else ''}")
    if n_a: parts.append(f"{n_a} action item{'s' if n_a>1 else ''}")
    summary = ("Recorded: " + ", ".join(parts) + ".") if parts else "No structured events extracted."

    return {
        "activity_type":       _infer_activity_type(structured),
        "summary":             summary,
        "system_performance":  "\n".join(perf_texts),
        "maintenance_done":    "\n".join(maint_texts),
        "issues_found":        "\n".join(obs_texts),
        "action_items":        "\n".join(action_texts),
        "components_affected": ", ".join(components),
        "duration_hours":      str(total_dur) if total_dur else "",
        "severity":            top_sev,
        "additional_notes":    "",
        "_structured":         structured,
    }


def _infer_activity_type(structured):
    if structured.get("maintenance_performed"):
        return "Regular Maintenance"
    if structured.get("qualitative_observations"):
        return "Other"
    if structured.get("action_items"):
        return "Logistics"
    return "Other"

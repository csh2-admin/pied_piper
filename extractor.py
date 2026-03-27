"""
extractor.py — Uses the Claude API to parse a raw transcript into structured fields.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PRODUCT_DESCRIPTION

_client = None

ACTIVITY_OPTIONS = [
    "Regular Maintenance",
    "Unplanned Maintenance",
    "Technical Milestone",
    "Logistics",
    "Other",
]


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = f"""You are a technical data extraction assistant for a hardware testing team.
The engineer has recorded a voice memo about {PRODUCT_DESCRIPTION}.
Your job is to extract structured information from the transcript and return ONLY valid JSON.

Return a JSON object with exactly these keys (use empty string "" if a field is not mentioned):

{{
  "activity_type":     "Classify the primary activity: Regular Maintenance | Unplanned Maintenance | Technical Milestone | Logistics | Other",
  "summary":             "1-2 sentence plain-English summary of the entry",
  "system_performance":  "Any observations about how the system/hardware performed (metrics, behaviour, anomalies, sensor readings, etc.)",
  "maintenance_done":    "Maintenance or repair activities completed today",
  "issues_found":        "Problems, failures, or unexpected behaviours observed",
  "action_items":        "Follow-up tasks or things that need to happen next",
  "components_affected": "Specific components, subsystems, or parts mentioned",
  "duration_hours":      "Total time spent (numeric string, e.g. '2.5', or '' if not mentioned)",
  "severity":            "Overall severity: Critical | High | Medium | Low | None (pick one)",
  "additional_notes":    "Any other relevant details not captured above"
}}

For activity_type, use these definitions:
- Regular Maintenance: Scheduled, routine upkeep or inspection
- Unplanned Maintenance: Unexpected repairs or emergency interventions
- Technical Milestone: A notable achievement, test completion, or system qualification event
- Logistics: Transport, procurement, setup, teardown, or coordination activities
- Other: Anything that doesn't fit the above

Return ONLY the JSON object. No markdown, no commentary."""


def extract_insights(transcript: str) -> dict:
    client = _get_client()

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Transcript:\n\n{transcript}"}],
    )

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "activity_type":      "Other",
            "summary":             "Parse error — see raw transcript",
            "system_performance":  "",
            "maintenance_done":    "",
            "issues_found":        "",
            "action_items":        "",
            "components_affected": "",
            "duration_hours":      "",
            "severity":            "",
            "additional_notes":    raw,
        }

    # Normalise activity_type to match our options exactly
    raw_act = data.get("activity_type", "").strip()
    matched = next(
        (o for o in ACTIVITY_OPTIONS if o.lower() == raw_act.lower()),
        "Other"
    )
    data["activity_type"] = matched

    return data

"""
extractor.py — Uses the Claude API to parse a raw transcript into structured fields.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PRODUCT_DESCRIPTION

_client = None

ACTIVITY_OPTIONS = [
    "Action Item",
    "Qualitative Observation",
    "System Maintenance",
    "Performance - Quantitative",
    "Hypothesis",
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
  "activity_type":             "Classify the primary activity: Action Item | Qualitative Observation | System Maintenance | Performance - Quantitative | Hypothesis | Other",
  "summary":                   "1-2 sentence plain-English summary of the entry",
  "system_performance":        "Any narrative observations about how the system/hardware performed",
  "action_items":              "Follow-up tasks or things that need to happen next",
  "components_affected":       "Specific components, subsystems, or parts mentioned",
  "duration_hours":            "Total time spent (numeric string, e.g. '2.5', or '' if not mentioned)",
  "additional_notes":          "Any other relevant details not captured above",
  "trigger_simulation_update": true or false (boolean — see rules below)
}}

For activity_type, use these definitions:
- Action Item: A follow-up task or to-do item that needs to be completed.
- Qualitative Observation: A narrative description of system behaviour, anomalies, or what was seen — without specific metrics or numerical readings.
- System Maintenance: Any maintenance, repair, replacement, calibration, or upkeep activity (planned or unplanned).
- Performance - Quantitative: A report citing specific numerical metrics, sensor readings, or measured values describing system performance. (Note: these numbers are usually redundant with the dedicated sensor data set, so they are tagged for review and not used in decision-making.)
- Hypothesis: An engineer-proposed theory about cause, behaviour, or expected outcome — even if untested.
- Other: Anything that does not clearly fit the above (e.g. logistics, procurement, coordination).

For trigger_simulation_update, set true when the entry is likely to require an update to the simulation model:
- Always true if activity_type is "Hypothesis".
- Often true for "System Maintenance" entries that change physical configuration, replace components, or recalibrate (i.e. anything that would shift simulation parameters).
- Otherwise default to false.

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
            "activity_type":             "Other",
            "summary":                   "Parse error — see raw transcript",
            "system_performance":        "",
            "action_items":              "",
            "components_affected":       "",
            "duration_hours":            "",
            "additional_notes":          raw,
            "trigger_simulation_update": False,
        }

    # Normalise activity_type to match our options exactly
    raw_act = data.get("activity_type", "").strip()
    matched = next(
        (o for o in ACTIVITY_OPTIONS if o.lower() == raw_act.lower()),
        "Other"
    )
    data["activity_type"] = matched

    # Normalise trigger_simulation_update to a real bool
    tsu = data.get("trigger_simulation_update", False)
    if isinstance(tsu, str):
        tsu = tsu.strip().lower() in ("true", "yes", "y", "1")
    data["trigger_simulation_update"] = bool(tsu)

    return data

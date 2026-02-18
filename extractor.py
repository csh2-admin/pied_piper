"""
extractor.py — Uses the Claude API to parse a raw transcript into structured fields.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PRODUCT_DESCRIPTION

_client = None


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

Return ONLY the JSON object. No markdown, no commentary."""


def extract_insights(transcript: str) -> dict:
    """
    Send the transcript to Claude and return a dict of structured fields.
    """
    client = _get_client()
    print("[Claude] Extracting insights from transcript…")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Transcript:\n\n{transcript}",
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[Claude] Warning: could not parse JSON response — {e}")
        print(f"[Claude] Raw response:\n{raw}\n")
        data = {
            "summary": "Parse error — see raw transcript",
            "system_performance": "",
            "maintenance_done": "",
            "issues_found": "",
            "action_items": "",
            "components_affected": "",
            "duration_hours": "",
            "severity": "",
            "additional_notes": raw,
        }

    print("[Claude] Extraction complete.")
    return data

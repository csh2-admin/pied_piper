"""
config.py — reads secrets from Streamlit's secrets manager when deployed,
falls back to environment variables or hardcoded values for local dev.
"""

import os

def _get(key: str, fallback: str = "") -> str:
    """Read from st.secrets first, then env vars, then fallback."""
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, fallback)

# ── Team ──────────────────────────────────────────────────────────────────────
TEAM_MEMBERS = [
    "Jimmy Li",
    "Edward Youn",
    "PJ Callahan",
    "Anthony Ku",
    "Thomas Todaro",
]

# ── Anthropic ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = _get("ANTHROPIC_API_KEY", "YOUR_KEY_HERE")
CLAUDE_MODEL       = "claude-sonnet-4-6"

# ── Whisper ───────────────────────────────────────────────────────────────────
WHISPER_MODEL_SIZE = "base"   # tiny | base | small | medium | large

# ── Database ──────────────────────────────────────────────────────────────────
DB_URI = _get("DB_URI", "postgres://user:password@host:5432/dbname")

# ── Product context ───────────────────────────────────────────────────────────
PRODUCT_DESCRIPTION = (
    "a hardware product under test; entries describe daily system performance "
    "observations and maintenance activities performed by test engineers."
)

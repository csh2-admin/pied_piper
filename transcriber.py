"""
transcriber.py — Whisper transcription for the Streamlit server.
The model is loaded once and cached; ffmpeg must be installed on the server
(handled automatically by packages.txt on Streamlit Community Cloud).
"""

import tempfile
import io
import numpy as np
import whisper
import streamlit as st
from config import WHISPER_MODEL_SIZE


@st.cache_resource(show_spinner="Loading Whisper model…")
def _get_model():
    return whisper.load_model(WHISPER_MODEL_SIZE)


def transcribe_file(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """
    Transcribe raw audio bytes (from st.file_uploader or st.audio_input).
    suffix: file extension hint, e.g. '.m4a', '.wav', '.mp3'
    """
    model = _get_model()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    result = model.transcribe(tmp_path, fp16=False)
    return result["text"].strip()

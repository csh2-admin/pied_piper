"""
recorder.py — Record audio directly from the system microphone.
Press Enter to stop recording.
"""

import threading
import tempfile
import os
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from config import RECORDING_SAMPLE_RATE, RECORDING_CHANNELS


def record_until_enter() -> str:
    """
    Record from the default microphone until the user presses Enter.
    Returns the path to a temporary .wav file.
    """
    print("\n[Recorder] Recording… Press Enter to stop.\n")

    chunks = []
    stop_event = threading.Event()

    def _callback(indata, frames, time_info, status):
        if not stop_event.is_set():
            chunks.append(indata.copy())

    stream = sd.InputStream(
        samplerate=RECORDING_SAMPLE_RATE,
        channels=RECORDING_CHANNELS,
        dtype="float32",
        callback=_callback,
    )

    with stream:
        input()  # block until Enter
        stop_event.set()

    if not chunks:
        raise RuntimeError("No audio was captured.")

    audio = np.concatenate(chunks, axis=0)
    audio_int16 = (audio * 32767).astype(np.int16)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_write(tmp.name, RECORDING_SAMPLE_RATE, audio_int16)
    print(f"[Recorder] Saved to temp file: {tmp.name}")
    return tmp.name


def cleanup_temp(path: str):
    """Remove a temporary recording file."""
    try:
        os.remove(path)
    except OSError:
        pass

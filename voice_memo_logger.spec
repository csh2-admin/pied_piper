# voice_memo_logger.spec
# PyInstaller spec file — run with:  pyinstaller voice_memo_logger.spec

import sys
import os
from pathlib import Path
import whisper

block_cipher = None

from PyInstaller.utils.hooks import collect_dynamic_libs
import sys

# Bundle the VC++ runtime DLLs
a_binaries_extra = collect_dynamic_libs('numpy')  # forces VCRUNTIME inclusion

# ── Locate Whisper's bundled assets (mel filterbank, vocab files, etc.) ───────
whisper_pkg_dir = Path(whisper.__file__).parent
whisper_assets  = [
    (str(whisper_pkg_dir / "assets"), "whisper/assets"),
]

# ── Main analysis ─────────────────────────────────────────────────────────────
a = Analysis(
    ["gui.py"],
    pathex=["."],
    binaries=a_binaries_extra,
    datas=whisper_assets,
    hiddenimports=[
        # Whisper / torch
        "whisper",
        "whisper.audio",
        "whisper.decoding",
        "whisper.model",
        "whisper.tokenizer",
        "whisper.transcribe",
        "whisper.utils",
        "torch",
        "torch.nn",
        "torch.nn.functional",
        # Audio I/O
        "sounddevice",
        "scipy.io.wavfile",
        "scipy.signal",
        "numpy",
        # DB
        "psycopg2",
        "psycopg2.extras",
        "psycopg2._psycopg",
        # Excel
        "openpyxl",
        "openpyxl.styles",
        "openpyxl.utils",
        # Anthropic SDK
        "anthropic",
        "httpx",
        "httpcore",
        "certifi",
        # Stdlib bits PyInstaller sometimes misses
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "json",
        "threading",
        "pathlib",
        "datetime",
    ],
    hookspath=["."],          # picks up hook-whisper.py in same folder
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "IPython", "notebook", "PIL",
        "cv2", "sklearn", "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VoiceMemoLogger",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # no console window — pure GUI app
    icon="app_icon.ico",    # optional; remove this line if you have no .ico file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VoiceMemoLogger",  # output folder name inside dist/
)

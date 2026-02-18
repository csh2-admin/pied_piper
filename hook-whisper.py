# hook-whisper.py
# Tells PyInstaller where to find Whisper's data files and dependencies.

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas   = collect_data_files("whisper")
binaries = collect_dynamic_libs("whisper")

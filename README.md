# 🎙 Hardware Test — Voice Memo Logger (Streamlit)

A shared web app for the hardware test team to log daily voice memos,
extract structured insights with Claude, and store everything in TimescaleDB.

---

## Quick start — local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set secrets in `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
DB_URI            = "postgres://tsdbadmin:PASSWORD@YOUR_HOST.tsdb.cloud:PORT/tsdb"
```

---

## Deploy on Streamlit Community Cloud (free, 5 minutes)

1. Push this folder to a GitHub repo (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Pick your repo, branch `main`, file `app.py`
4. Click **Advanced settings → Secrets** and paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   DB_URI            = "postgres://tsdbadmin:PASSWORD@YOUR_HOST.tsdb.cloud:PORT/tsdb"
   ```
5. Click **Deploy** — URL is ready in ~2 minutes
6. Share the URL with your team — no installs needed

---

## File structure

```
├── app.py              ← Streamlit UI (single file)
├── config.py           ← Settings — reads from st.secrets automatically
├── transcriber.py      ← Whisper transcription (server-side)
├── extractor.py        ← Claude API insight extraction
├── db_logger.py        ← TimescaleDB read/write
├── excel_export.py     ← On-demand Excel generation
├── packages.txt        ← System packages (ffmpeg) for Streamlit Cloud
├── requirements.txt    ← Python packages
└── .streamlit/
    ├── config.toml     ← Theme + upload size settings
    └── secrets.toml    ← API keys (local only, never commit)
```

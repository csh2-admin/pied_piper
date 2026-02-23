"""
db_logger.py — PostgreSQL / TimescaleDB backend.

Compatible with any standard PostgreSQL connection string, including
TimescaleDB Cloud (tsdb.cloud) and self-hosted TimescaleDB.

Example DB_URI formats:
  TimescaleDB Cloud: postgres://tsdbadmin:password@host.tsdb.cloud:12345/tsdb
  Self-hosted:       postgresql://user:password@localhost:5432/mydb
  commenting
"""

import json
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from config import DB_URI

# ── Schema ────────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS memo_log (
    id                  BIGSERIAL,
    logged_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    engineer            TEXT         NOT NULL,
    source_file         TEXT,
    summary             TEXT,
    system_performance  TEXT,
    maintenance_done    TEXT,
    issues_found        TEXT,
    action_items        TEXT,
    components_affected TEXT,
    duration_hours      NUMERIC,
    severity            TEXT,
    additional_notes    TEXT,
    raw_transcript      TEXT,
    raw_insights_json   JSONB,
    PRIMARY KEY (id, logged_at)
);
"""

# Silently enables TimescaleDB hypertable if the extension is present
HYPERTABLE_SQL = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable(
            'memo_log', 'logged_at',
            if_not_exists => TRUE,
            migrate_data   => TRUE
        );
    END IF;
END;
$$;
"""

INSERT_SQL = """
INSERT INTO memo_log (
    engineer, source_file, activity_type,
    summary, system_performance, maintenance_done,
    issues_found, action_items, components_affected,
    duration_hours, severity, additional_notes,
    raw_transcript, raw_insights_json
) VALUES (
    %(engineer)s, %(source_file)s, %(activity_type)s,
    %(summary)s, %(system_performance)s, %(maintenance_done)s,
    %(issues_found)s, %(action_items)s, %(components_affected)s,
    %(duration_hours)s, %(severity)s, %(additional_notes)s,
    %(raw_transcript)s, %(raw_insights_json)s
)
RETURNING id, logged_at;
"""

UPDATE_SQL = """
UPDATE memo_log SET
    engineer            = %(engineer)s,
    activity_type       = %(activity_type)s,
    summary             = %(summary)s,
    system_performance  = %(system_performance)s,
    maintenance_done    = %(maintenance_done)s,
    issues_found        = %(issues_found)s,
    action_items        = %(action_items)s,
    components_affected = %(components_affected)s,
    duration_hours      = %(duration_hours)s,
    severity            = %(severity)s,
    additional_notes    = %(additional_notes)s,
    raw_transcript      = %(raw_transcript)s
WHERE id = %(id)s
RETURNING id, logged_at;
"""

FETCH_ALL_SQL = """
SELECT
    id, logged_at, engineer, source_file, activity_type,
    summary, system_performance, maintenance_done,
    issues_found, action_items, components_affected,
    duration_hours, severity, additional_notes, raw_transcript
FROM memo_log
ORDER BY logged_at DESC;
"""

FETCH_FILTERED_SQL = """
SELECT
    id, logged_at, engineer, source_file, activity_type,
    summary, system_performance, maintenance_done,
    issues_found, action_items, components_affected,
    duration_hours, severity, additional_notes, raw_transcript
FROM memo_log
WHERE
    (%(engineer)s      = '' OR engineer      = %(engineer)s)
    AND (%(activity_type)s = '' OR activity_type = %(activity_type)s)
    AND (%(severity)s   = '' OR severity   = %(severity)s)
    AND (%(search)s     = '' OR
         summary             ILIKE %(search_like)s OR
         issues_found        ILIKE %(search_like)s OR
         maintenance_done    ILIKE %(search_like)s OR
         components_affected ILIKE %(search_like)s OR
         raw_transcript      ILIKE %(search_like)s)
    AND (%(date_from)s  = '' OR logged_at::date >= %(date_from)s::date)
    AND (%(date_to)s    = '' OR logged_at::date <= %(date_to)s::date)
ORDER BY logged_at DESC
LIMIT 500;
"""

DELETE_SQL = "DELETE FROM memo_log WHERE id = %(id)s;"
# ── Action Items table ────────────────────────────────────────────────────────

CREATE_ACTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS action_items (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    memo_id     BIGINT,
    engineer    TEXT,
    action_text TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'Not Started',
    responsible TEXT,
    due_date    DATE,
    notes       TEXT
);
"""

INSERT_ACTION_SQL = """
INSERT INTO action_items (memo_id, engineer, action_text, status, responsible, due_date)
VALUES (%(memo_id)s, %(engineer)s, %(action_text)s, 'Not Started', %(responsible)s, %(due_date)s)
RETURNING id, created_at;
"""

UPDATE_ACTION_STATUS_SQL = """
UPDATE action_items
SET status      = %(status)s,
    notes       = %(notes)s,
    responsible = %(responsible)s,
    due_date    = %(due_date)s,
    updated_at  = NOW()
WHERE id = %(id)s
RETURNING id, updated_at;
"""

DELETE_ACTION_SQL = "DELETE FROM action_items WHERE id = %(id)s;"

FETCH_ACTIONS_SQL = """
SELECT
    a.id, a.created_at, a.updated_at,
    a.memo_id, a.engineer, a.action_text, a.status, a.notes,
    a.responsible, a.due_date,
    m.logged_at AS memo_logged_at,
    m.summary   AS memo_summary,
    m.activity_type AS memo_activity_type
FROM action_items a
LEFT JOIN memo_log m ON m.id = a.memo_id
WHERE
    (%(engineer)s = '' OR a.engineer = %(engineer)s)
    AND (%(status)s   = '' OR a.status   = %(status)s)
    AND (%(search)s   = '' OR a.action_text ILIKE %(search_like)s
                            OR a.notes      ILIKE %(search_like)s)
ORDER BY
    CASE a.status
        WHEN 'In Progress'  THEN 1
        WHEN 'Not Started'  THEN 2
        WHEN 'Complete'     THEN 3
    END,
    a.updated_at DESC;
"""



FETCH_ENGINEERS_SQL = "SELECT DISTINCT engineer FROM memo_log ORDER BY engineer;"


# ── Connection ────────────────────────────────────────────────────────────────

def _connect():
    if not PSYCOPG2_AVAILABLE:
        raise RuntimeError(
            "psycopg2 is not installed.\nRun:  pip install psycopg2-binary"
        )
    # Strip ?sslmode=... from URI and pass SSL as an explicit arg instead.
    # psycopg2 is more reliable this way, especially on Streamlit Cloud.
    uri = DB_URI
    ssl_arg = {}
    if "?" in uri:
        base, params = uri.split("?", 1)
        # If sslmode=require is present, use psycopg2 sslmode kwarg directly
        if "sslmode" in params:
            uri = base
            ssl_arg = {"sslmode": "require"}
    return psycopg2.connect(uri, **ssl_arg)


def ensure_schema():
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
                cur.execute(HYPERTABLE_SQL)
                cur.execute(CREATE_ACTIONS_TABLE_SQL)
    finally:
        conn.close()


# ── Write ─────────────────────────────────────────────────────────────────────

def _parse_duration(raw) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    try:
        return float(s) if s else None
    except ValueError:
        return None


def append_entry(insights: dict, raw_transcript: str,
                 source_file: str, engineer: str) -> dict:
    row = {
        "engineer":            engineer,
        "source_file":         source_file,
        "activity_type":       insights.get("activity_type", ""),
        "summary":             insights.get("summary", ""),
        "system_performance":  insights.get("system_performance", ""),
        "maintenance_done":    insights.get("maintenance_done", ""),
        "issues_found":        insights.get("issues_found", ""),
        "action_items":        insights.get("action_items", ""),
        "components_affected": insights.get("components_affected", ""),
        "duration_hours":      _parse_duration(insights.get("duration_hours")),
        "severity":            insights.get("severity", ""),
        "additional_notes":    insights.get("additional_notes", ""),
        "raw_transcript":      raw_transcript,
        "raw_insights_json":   json.dumps(insights),
    }
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(INSERT_SQL, row)
                row_id, logged_at = cur.fetchone()
        return {"id": row_id, "logged_at": logged_at}
    finally:
        conn.close()


def update_entry(row_id: int, fields: dict) -> dict:
    """
    Update an existing record. `fields` is a flat dict of column->value.
    Returns {'id': ..., 'logged_at': ...}.
    """
    params = {
        "id":                  row_id,
        "engineer":            fields.get("engineer", ""),
        "activity_type":       fields.get("activity_type", ""),
        "summary":             fields.get("summary", ""),
        "system_performance":  fields.get("system_performance", ""),
        "maintenance_done":    fields.get("maintenance_done", ""),
        "issues_found":        fields.get("issues_found", ""),
        "action_items":        fields.get("action_items", ""),
        "components_affected": fields.get("components_affected", ""),
        "duration_hours":      _parse_duration(fields.get("duration_hours")),
        "severity":            fields.get("severity", ""),
        "additional_notes":    fields.get("additional_notes", ""),
        "raw_transcript":      fields.get("raw_transcript", ""),
    }
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(UPDATE_SQL, params)
                row_id_out, logged_at = cur.fetchone()
        return {"id": row_id_out, "logged_at": logged_at}
    finally:
        conn.close()


def delete_entry(row_id: int):
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(DELETE_SQL, {"id": row_id})
    finally:
        conn.close()


# ── Read ──────────────────────────────────────────────────────────────────────

def fetch_all_rows() -> list[dict]:
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_ALL_SQL)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_filtered_rows(engineer="", activity_type="", severity="",
                        search="", date_from="", date_to="") -> list[dict]:
    params = {
        "engineer":      engineer,
        "activity_type": activity_type,
        "severity":      severity,
        "search":        search,
        "search_like":   f"%{search}%",
        "date_from":     date_from,
        "date_to":       date_to,
    }
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_FILTERED_SQL, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_engineers() -> list[str]:
    """Return list of distinct engineer names in the DB."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(FETCH_ENGINEERS_SQL)
            return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def test_connection() -> str:
    try:
        conn = _connect()
        conn.close()
        return "ok"
    except Exception as e:
        return str(e)


# ── Action Items CRUD ─────────────────────────────────────────────────────────

def parse_action_items(action_text: str) -> list[str]:
    """
    Split a multi-line or bullet-separated action_items string into
    individual action item strings. Filters out empty lines.
    """
    import re
    if not action_text or not action_text.strip():
        return []
    lines = re.split(r"[\n;]", action_text)
    cleaned = []
    for line in lines:
        # Strip leading bullet/dash/number markers
        line = re.sub(r"^\s*[-•*\d\.]+\s*", "", line).strip()
        if line:
            cleaned.append(line)
    return cleaned


def create_action_items_from_memo(memo_id, action_text: str,
                                   engineer: str, responsible: str = "",
                                   due_date=None) -> list[dict]:
    """
    Parse action_text and insert one row per action item.
    Returns list of created rows with id and created_at.
    """
    items = parse_action_items(action_text)
    if not items:
        return []

    conn = _connect()
    created = []
    try:
        with conn:
            with conn.cursor() as cur:
                for text in items:
                    cur.execute(INSERT_ACTION_SQL, {
                        "memo_id":     memo_id,
                        "engineer":    engineer,
                        "action_text": text,
                        "responsible": responsible or "",
                        "due_date":    due_date,
                    })
                    row_id, created_at = cur.fetchone()
                    created.append({"id": row_id, "created_at": created_at,
                                    "action_text": text})
    finally:
        conn.close()
    return created


def update_action_item(item_id: int, status: str, notes: str = "",
                         responsible: str = "", due_date=None) -> dict:
    """Update the status, notes, responsible, and due_date of an action item."""
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(UPDATE_ACTION_STATUS_SQL, {
                    "id":          item_id,
                    "status":      status,
                    "notes":       notes or "",
                    "responsible": responsible or "",
                    "due_date":    due_date,
                })
                row_id, updated_at = cur.fetchone()
        return {"id": row_id, "updated_at": updated_at}
    finally:
        conn.close()


def delete_action_item(item_id: int):
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(DELETE_ACTION_SQL, {"id": item_id})
    finally:
        conn.close()


def fetch_action_items(engineer="", status="", search="") -> list[dict]:
    """Fetch action items with optional filters."""
    params = {
        "engineer":    engineer,
        "status":      status,
        "search":      search,
        "search_like": f"%{search}%",
    }
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_ACTIONS_SQL, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

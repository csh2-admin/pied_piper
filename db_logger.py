"""
db_logger.py — PostgreSQL / TimescaleDB backend.

Compatible with any standard PostgreSQL connection string, including
TimescaleDB Cloud (tsdb.cloud) and self-hosted TimescaleDB.

Example DB_URI formats:
  TimescaleDB Cloud: postgres://tsdbadmin:password@host.tsdb.cloud:12345/tsdb
  Self-hosted:       postgresql://user:password@localhost:5432/mydb
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


def _json_serial(obj):
    """JSON serialiser for types not handled by default (date, datetime, Decimal)."""
    import datetime as _dt
    import decimal as _dec
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    if isinstance(obj, _dec.Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not JSON serialisable")


def _parse_duration(raw) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    try:
        return float(s) if s else None
    except ValueError:
        return None


def append_entry(insights: dict, raw_transcript: str,
                 source_file: str, engineer: str,
                 logged_at=None) -> dict:
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
        "logged_at":           logged_at,  # None → COALESCE to NOW()
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


# ── Natural language query support ───────────────────────────────────────────

# Schema description passed to Claude so it can write accurate SQL
DB_SCHEMA = """
You have access to these PostgreSQL (TimescaleDB) tables:

TABLE: maintenance_logs  (primary structured log of work performed)
  id                  BIGINT
  date_recorded       TIMESTAMPTZ
  engineer            TEXT
  component_raw       TEXT            -- component name as spoken by engineer
  activity_performed  TEXT            -- what maintenance was done
  duration_hours      NUMERIC
  severity            TEXT            -- 'Critical'|'High'|'Medium'|'Low'|'None'
  outcome             TEXT            -- 'resolved'|'monitoring'|'escalated'
  component_canonical TEXT            -- via JOIN to components

TABLE: observation_logs  (qualitative observations, anomalies, concerns)
  id                  BIGINT
  date_recorded       TIMESTAMPTZ
  engineer            TEXT
  component_raw       TEXT
  observation         TEXT            -- what was observed
  observation_type    TEXT            -- 'anomaly'|'degradation'|'normal'|'informational'|'concern'
  severity            TEXT
  follow_up_required  BOOLEAN
  component_canonical TEXT            -- via JOIN to components

TABLE: system_performance_logs  (numeric metrics and readings)
  id                  BIGINT
  date_recorded       TIMESTAMPTZ
  engineer            TEXT
  component_raw       TEXT
  metric_name         TEXT            -- e.g. 'pressure','temperature','flow_rate','vibration'
  metric_value        NUMERIC
  metric_unit         TEXT            -- e.g. 'bar','degC','L/min'
  metric_narrative    TEXT            -- free text when no clean numeric
  within_spec         BOOLEAN
  anomaly_flag        BOOLEAN
  component_canonical TEXT            -- via JOIN to components

TABLE: action_items
  id           BIGINT
  created_at   TIMESTAMPTZ
  updated_at   TIMESTAMPTZ
  memo_id      BIGINT
  engineer     TEXT
  action_text  TEXT
  status       TEXT                   -- 'Not Started'|'In Progress'|'Complete'
  responsible  TEXT
  due_date     DATE
  notes        TEXT

TABLE: components  (canonical component registry)
  id             BIGINT
  part_number    TEXT
  canonical_name TEXT
  category       TEXT
  subsystem      TEXT
  aliases        TEXT[]

TABLE: memo_log  (legacy summary table, kept for historical records)
  id            BIGINT
  logged_at     TIMESTAMPTZ
  engineer      TEXT
  summary       TEXT
  raw_transcript TEXT

JOIN HINT: maintenance_logs/observation_logs/system_performance_logs all have a
component_id foreign key. To get canonical names:
  LEFT JOIN components c ON c.id = ml.component_id
"""

def run_read_query(sql: str) -> list[dict]:
    """
    Execute a read-only SELECT query and return results as list of dicts.
    Raises ValueError if the SQL contains write operations.
    """
    # Safety: only allow SELECT statements
    normalised = sql.strip().lstrip("(").upper()
    if not normalised.startswith("SELECT") and not normalised.startswith("WITH"):
        raise ValueError("Only SELECT queries are permitted.")
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
                 "CREATE", "GRANT", "REVOKE"]
    for word in forbidden:
        if word in normalised:
            raise ValueError(f"Query contains forbidden keyword: {word}")

    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Gantt Tasks ───────────────────────────────────────────────────────────────

CREATE_GANTT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS gantt_tasks (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    title           TEXT NOT NULL,
    assignee        TEXT,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Not Started',
    dependencies    TEXT,        -- comma-separated task IDs, e.g. '1,3'
    action_item_id  BIGINT,      -- optional soft-link to action_items.id
    notes           TEXT,
    category        TEXT         -- swimlane / grouping label
);
"""

INSERT_GANTT_SQL = """
INSERT INTO gantt_tasks
    (title, assignee, start_date, end_date, status, dependencies,
     action_item_id, notes, category)
VALUES
    (%(title)s, %(assignee)s, %(start_date)s, %(end_date)s, %(status)s,
     %(dependencies)s, %(action_item_id)s, %(notes)s, %(category)s)
RETURNING id, created_at;
"""

UPDATE_GANTT_SQL = """
UPDATE gantt_tasks SET
    title          = %(title)s,
    assignee       = %(assignee)s,
    start_date     = %(start_date)s,
    end_date       = %(end_date)s,
    status         = %(status)s,
    dependencies   = %(dependencies)s,
    notes          = %(notes)s,
    category       = %(category)s,
    updated_at     = NOW()
WHERE id = %(id)s
RETURNING id, updated_at;
"""

DELETE_GANTT_SQL = "DELETE FROM gantt_tasks WHERE id = %(id)s;"

FETCH_GANTT_SQL = """
SELECT id, created_at, updated_at, title, assignee,
       start_date, end_date, status, dependencies,
       action_item_id, notes, category
FROM gantt_tasks
ORDER BY start_date ASC, id ASC;
"""


def ensure_gantt_schema():
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_GANTT_TABLE_SQL)
    finally:
        conn.close()


def fetch_gantt_tasks() -> list[dict]:
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_GANTT_SQL)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def _gantt_params(fields: dict) -> dict:
    return {
        "title":          fields.get("title", "").strip(),
        "assignee":       fields.get("assignee", "") or "",
        "start_date":     fields.get("start_date"),
        "end_date":       fields.get("end_date"),
        "status":         fields.get("status", "Not Started"),
        "dependencies":   fields.get("dependencies", "") or "",
        "action_item_id": fields.get("action_item_id") or None,
        "notes":          fields.get("notes", "") or "",
        "category":       fields.get("category", "") or "",
    }


def create_gantt_task(fields: dict) -> dict:
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(INSERT_GANTT_SQL, _gantt_params(fields))
                row_id, created_at = cur.fetchone()
        return {"id": row_id, "created_at": created_at}
    finally:
        conn.close()


def update_gantt_task(task_id: int, fields: dict) -> dict:
    params = _gantt_params(fields)
    params["id"] = task_id
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(UPDATE_GANTT_SQL, params)
                row_id, updated_at = cur.fetchone()
        return {"id": row_id, "updated_at": updated_at}
    finally:
        conn.close()


def delete_gantt_task(task_id: int):
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(DELETE_GANTT_SQL, {"id": task_id})
    finally:
        conn.close()


def bulk_insert_gantt_tasks(task_list: list[dict]) -> list[dict]:
    """Insert multiple tasks at once, used when Claude generates a plan."""
    conn = _connect()
    created = []
    try:
        with conn:
            with conn.cursor() as cur:
                for fields in task_list:
                    cur.execute(INSERT_GANTT_SQL, _gantt_params(fields))
                    row_id, created_at = cur.fetchone()
                    created.append({"id": row_id, "title": fields.get("title")})
    finally:
        conn.close()
    return created


# ── Components master table ───────────────────────────────────────────────────

FETCH_COMPONENTS_SQL = """
SELECT id, part_number, canonical_name, category, subsystem, aliases, active, notes
FROM components
WHERE active = TRUE
ORDER BY canonical_name;
"""

FETCH_ALL_COMPONENTS_SQL = """
SELECT id, part_number, canonical_name, category, subsystem, aliases, active, notes
FROM components
ORDER BY canonical_name;
"""

INSERT_COMPONENT_SQL = """
INSERT INTO components (part_number, canonical_name, category, subsystem, aliases, notes)
VALUES (%(part_number)s, %(canonical_name)s, %(category)s, %(subsystem)s,
        %(aliases)s, %(notes)s)
RETURNING id;
"""

UPDATE_COMPONENT_SQL = """
UPDATE components SET
    part_number    = %(part_number)s,
    canonical_name = %(canonical_name)s,
    category       = %(category)s,
    subsystem      = %(subsystem)s,
    aliases        = %(aliases)s,
    notes          = %(notes)s,
    active         = %(active)s
WHERE id = %(id)s;
"""


def fetch_components(include_inactive=False):
    """Return list of component dicts. aliases is a Python list."""
    sql = FETCH_ALL_COMPONENTS_SQL if include_inactive else FETCH_COMPONENTS_SQL
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = []
            for r in cur.fetchall():
                d = dict(r)
                # psycopg2 returns arrays as Python lists already
                if d["aliases"] is None:
                    d["aliases"] = []
                rows.append(d)
        return rows
    finally:
        conn.close()


def upsert_component(fields: dict) -> int:
    """Insert or update a component. Returns id."""
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                if fields.get("id"):
                    cur.execute(UPDATE_COMPONENT_SQL, {
                        "id":            fields["id"],
                        "part_number":   fields.get("part_number") or None,
                        "canonical_name":fields["canonical_name"],
                        "category":      fields.get("category") or None,
                        "subsystem":     fields.get("subsystem") or None,
                        "aliases":       fields.get("aliases") or [],
                        "notes":         fields.get("notes") or None,
                        "active":        fields.get("active", True),
                    })
                    return fields["id"]
                else:
                    cur.execute(INSERT_COMPONENT_SQL, {
                        "part_number":   fields.get("part_number") or None,
                        "canonical_name":fields["canonical_name"],
                        "category":      fields.get("category") or None,
                        "subsystem":     fields.get("subsystem") or None,
                        "aliases":       fields.get("aliases") or [],
                        "notes":         fields.get("notes") or None,
                    })
                    return cur.fetchone()[0]
    finally:
        conn.close()


def add_alias_to_component(component_id: int, new_alias: str):
    """Append a new alias to a component's alias array."""
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE components
                    SET aliases = array_append(aliases, %(alias)s)
                    WHERE id = %(id)s
                      AND NOT (%(alias)s = ANY(aliases));
                """, {"id": component_id, "alias": new_alias.lower().strip()})
    finally:
        conn.close()


# ── New structured tables — CRUD ──────────────────────────────────────────────

INSERT_MAINTENANCE_SQL = """
INSERT INTO maintenance_logs
    (date_recorded, engineer, component_id, component_raw,
     activity_performed, duration_hours, severity, outcome, source_memo_id)
VALUES
    (COALESCE(%(date_recorded)s::timestamptz, NOW()),
     %(engineer)s, %(component_id)s, %(component_raw)s,
     %(activity_performed)s, %(duration_hours)s, %(severity)s,
     %(outcome)s, %(source_memo_id)s)
RETURNING id, date_recorded;
"""

INSERT_OBSERVATION_SQL = """
INSERT INTO observation_logs
    (date_recorded, engineer, component_id, component_raw,
     observation, observation_type, severity, follow_up_required, source_memo_id)
VALUES
    (COALESCE(%(date_recorded)s::timestamptz, NOW()),
     %(engineer)s, %(component_id)s, %(component_raw)s,
     %(observation)s, %(observation_type)s, %(severity)s,
     %(follow_up_required)s, %(source_memo_id)s)
RETURNING id, date_recorded;
"""

INSERT_PERFORMANCE_SQL = """
INSERT INTO system_performance_logs
    (date_recorded, engineer, component_id, component_raw,
     metric_name, metric_value, metric_unit, metric_narrative,
     within_spec, anomaly_flag, source_memo_id)
VALUES
    (COALESCE(%(date_recorded)s::timestamptz, NOW()),
     %(engineer)s, %(component_id)s, %(component_raw)s,
     %(metric_name)s, %(metric_value)s, %(metric_unit)s, %(metric_narrative)s,
     %(within_spec)s, %(anomaly_flag)s, %(source_memo_id)s)
RETURNING id, date_recorded;
"""

FETCH_MAINTENANCE_SQL = """
SELECT ml.id, ml.date_recorded, ml.engineer, ml.component_raw,
       ml.activity_performed, ml.duration_hours, ml.severity, ml.outcome,
       c.canonical_name AS component_canonical
FROM maintenance_logs ml
LEFT JOIN components c ON c.id = ml.component_id
WHERE
    (%(engineer)s  = '' OR ml.engineer = %(engineer)s)
    AND (%(search)s = '' OR ml.activity_performed ILIKE %(search_like)s
                         OR ml.component_raw ILIKE %(search_like)s)
    AND (%(date_from)s = '' OR ml.date_recorded::date >= %(date_from)s::date)
    AND (%(date_to)s   = '' OR ml.date_recorded::date <= %(date_to)s::date)
ORDER BY ml.date_recorded DESC
LIMIT 500;
"""

FETCH_OBSERVATIONS_SQL = """
SELECT ol.id, ol.date_recorded, ol.engineer, ol.component_raw,
       ol.observation, ol.observation_type, ol.severity, ol.follow_up_required,
       c.canonical_name AS component_canonical
FROM observation_logs ol
LEFT JOIN components c ON c.id = ol.component_id
WHERE
    (%(engineer)s  = '' OR ol.engineer = %(engineer)s)
    AND (%(search)s = '' OR ol.observation ILIKE %(search_like)s
                         OR ol.component_raw ILIKE %(search_like)s)
    AND (%(date_from)s = '' OR ol.date_recorded::date >= %(date_from)s::date)
    AND (%(date_to)s   = '' OR ol.date_recorded::date <= %(date_to)s::date)
ORDER BY ol.date_recorded DESC
LIMIT 500;
"""

FETCH_PERFORMANCE_SQL = """
SELECT pl.id, pl.date_recorded, pl.engineer, pl.component_raw,
       pl.metric_name, pl.metric_value, pl.metric_unit,
       pl.metric_narrative, pl.within_spec, pl.anomaly_flag,
       c.canonical_name AS component_canonical
FROM system_performance_logs pl
LEFT JOIN components c ON c.id = pl.component_id
WHERE
    (%(engineer)s  = '' OR pl.engineer = %(engineer)s)
    AND (%(search)s = '' OR pl.metric_name ILIKE %(search_like)s
                         OR pl.component_raw ILIKE %(search_like)s
                         OR pl.metric_narrative ILIKE %(search_like)s)
    AND (%(date_from)s = '' OR pl.date_recorded::date >= %(date_from)s::date)
    AND (%(date_to)s   = '' OR pl.date_recorded::date <= %(date_to)s::date)
ORDER BY pl.date_recorded DESC
LIMIT 500;
"""

FETCH_UNMATCHED_SQL = """
SELECT component_raw, COUNT(*) AS occurrences FROM (
    SELECT component_raw FROM maintenance_logs    WHERE component_id IS NULL AND component_raw IS NOT NULL
    UNION ALL
    SELECT component_raw FROM observation_logs    WHERE component_id IS NULL AND component_raw IS NOT NULL
    UNION ALL
    SELECT component_raw FROM system_performance_logs WHERE component_id IS NULL AND component_raw IS NOT NULL
) t
GROUP BY component_raw
ORDER BY occurrences DESC;
"""


def _resolve_component_id(canonical_name, alias_map_lookup):
    """Given a canonical name string, return the DB component id or None."""
    if not canonical_name:
        return None
    return alias_map_lookup.get(canonical_name.lower().strip())


def _parse_num(val):
    """Convert value to float or None."""
    if val is None or val == "" or val != val:  # nan check
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def process_transcript(structured: dict, raw_transcript: str,
                       source_file: str, engineer: str,
                       date_recorded=None) -> dict:
    """
    Write a fully structured extraction to all four tables plus memo_log.
    Everything in one transaction — rolls back on any failure.

    structured: output from extractor.extract_structured()
    Returns: {
        memo_id, n_maintenance, n_observations, n_performance, n_actions,
        unmatched_components: [str]
    }
    """
    # Build alias->id lookup for component resolution
    try:
        comp_rows = fetch_components()
        name_to_id = {}
        for row in comp_rows:
            name_to_id[row["canonical_name"].lower().strip()] = row["id"]
            if row.get("part_number"):
                name_to_id[row["part_number"].lower().strip()] = row["id"]
            for alias in (row.get("aliases") or []):
                if alias:
                    name_to_id[alias.lower().strip()] = row["id"]
    except Exception:
        name_to_id = {}

    def _comp_id(record):
        cc = record.get("component_canonical")
        if cc:
            return name_to_id.get(cc.lower().strip())
        return None

    conn = _connect()
    result = {
        "memo_id": None, "n_maintenance": 0, "n_observations": 0,
        "n_performance": 0, "n_actions": 0, "unmatched_components": []
    }

    try:
        with conn:   # single transaction
            with conn.cursor() as cur:

                # ── 1. Write legacy memo_log row ─────────────────────────────
                # Build summary from structured data
                n_m = len(structured.get("maintenance_performed", []))
                n_o = len(structured.get("qualitative_observations", []))
                n_p = len(structured.get("system_performance", []))
                n_a = len(structured.get("action_items", []))
                parts = []
                if n_m: parts.append(f"{n_m} maintenance activit{'ies' if n_m>1 else 'y'}")
                if n_o: parts.append(f"{n_o} observation{'s' if n_o>1 else ''}")
                if n_p: parts.append(f"{n_p} performance metric{'s' if n_p>1 else ''}")
                if n_a: parts.append(f"{n_a} action item{'s' if n_a>1 else ''}")
                summary = ("Recorded: " + ", ".join(parts) + ".") if parts else "Entry saved."

                sev_rank = {"Critical":5,"High":4,"Medium":3,"Low":2,"None":1,"":0,None:0}
                all_sevs = (
                    [r.get("severity") for r in structured.get("maintenance_performed",[])] +
                    [r.get("severity") for r in structured.get("qualitative_observations",[])]
                )
                top_sev = max(all_sevs, key=lambda s: sev_rank.get(s,0), default="None") or "None"
                if top_sev not in ("Critical","High","Medium","Low","None"):
                    top_sev = "None"

                memo_row = {
                    "engineer":            engineer,
                    "source_file":         source_file,
                    "activity_type":       "Other",
                    "summary":             summary,
                    "system_performance":  "",
                    "maintenance_done":    "",
                    "issues_found":        "",
                    "action_items":        "",
                    "components_affected": "",
                    "duration_hours":      None,
                    "severity":            top_sev,
                    "additional_notes":    "",
                    "raw_transcript":      raw_transcript,
                    "raw_insights_json":   json.dumps(structured, default=_json_serial),
                    "logged_at":           date_recorded,
                }
                cur.execute(INSERT_SQL, memo_row)
                memo_id, _ = cur.fetchone()
                result["memo_id"] = memo_id

                # ── 2. Maintenance logs ───────────────────────────────────────
                for r in structured.get("maintenance_performed", []):
                    cid = _comp_id(r)
                    if not r.get("component_canonical") and not cid:
                        result["unmatched_components"].append(r.get("component_raw",""))
                    cur.execute(INSERT_MAINTENANCE_SQL, {
                        "date_recorded":     date_recorded,
                        "engineer":          engineer,
                        "component_id":      cid,
                        "component_raw":     r.get("component_raw") or "",
                        "activity_performed":r.get("activity_performed",""),
                        "duration_hours":    _parse_num(r.get("duration_hours")),
                        "severity":          r.get("severity") or "None",
                        "outcome":           r.get("outcome") or None,
                        "source_memo_id":    memo_id,
                    })
                    result["n_maintenance"] += 1

                # ── 3. Observation logs ───────────────────────────────────────
                for r in structured.get("qualitative_observations", []):
                    cid = _comp_id(r)
                    if not r.get("component_canonical") and not cid:
                        result["unmatched_components"].append(r.get("component_raw",""))
                    cur.execute(INSERT_OBSERVATION_SQL, {
                        "date_recorded":    date_recorded,
                        "engineer":         engineer,
                        "component_id":     cid,
                        "component_raw":    r.get("component_raw") or "",
                        "observation":      r.get("observation",""),
                        "observation_type": r.get("observation_type") or "informational",
                        "severity":         r.get("severity") or "None",
                        "follow_up_required": bool(r.get("follow_up_required", False)),
                        "source_memo_id":   memo_id,
                    })
                    result["n_observations"] += 1

                # ── 4. System performance logs ────────────────────────────────
                for r in structured.get("system_performance", []):
                    cid = _comp_id(r)
                    if not r.get("component_canonical") and not cid:
                        result["unmatched_components"].append(r.get("component_raw",""))
                    cur.execute(INSERT_PERFORMANCE_SQL, {
                        "date_recorded":   date_recorded,
                        "engineer":        engineer,
                        "component_id":    cid,
                        "component_raw":   r.get("component_raw") or "",
                        "metric_name":     r.get("metric_name","other"),
                        "metric_value":    _parse_num(r.get("metric_value")),
                        "metric_unit":     r.get("metric_unit") or None,
                        "metric_narrative":r.get("metric_narrative") or None,
                        "within_spec":     r.get("within_spec"),
                        "anomaly_flag":    bool(r.get("anomaly_flag", False)),
                        "source_memo_id":  memo_id,
                    })
                    result["n_performance"] += 1

                # ── 5. Action items ───────────────────────────────────────────
                for r in structured.get("action_items", []):
                    if not r.get("action_text","").strip():
                        continue
                    cur.execute(INSERT_ACTION_SQL, {
                        "memo_id":     memo_id,
                        "engineer":    engineer,
                        "action_text": r["action_text"],
                        "responsible": r.get("responsible") or "",
                        "due_date":    r.get("due_date") or None,
                    })
                    result["n_actions"] += 1

        # Deduplicate unmatched list
        seen = set()
        result["unmatched_components"] = [
            x for x in result["unmatched_components"]
            if x and not (x in seen or seen.add(x))
        ]
        return result

    finally:
        conn.close()


def fetch_maintenance_logs(engineer="", search="", date_from="", date_to=""):
    params = {"engineer": engineer, "search": search,
              "search_like": f"%{search}%", "date_from": date_from, "date_to": date_to}
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_MAINTENANCE_SQL, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_observation_logs(engineer="", search="", date_from="", date_to=""):
    params = {"engineer": engineer, "search": search,
              "search_like": f"%{search}%", "date_from": date_from, "date_to": date_to}
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_OBSERVATIONS_SQL, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_performance_logs(engineer="", search="", date_from="", date_to=""):
    params = {"engineer": engineer, "search": search,
              "search_like": f"%{search}%", "date_from": date_from, "date_to": date_to}
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_PERFORMANCE_SQL, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_unmatched_components():
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(FETCH_UNMATCHED_SQL)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

import sqlite3
from datetime import datetime


def get_connection(path="opspilot.db"):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_no INTEGER,
            timestamp TEXT,
            level TEXT,
            service TEXT,
            message TEXT,
            raw TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(timestamp)")
    return conn


def save_records(conn, records):
    """Replace the stored logs with the given records."""
    conn.execute("DELETE FROM logs")
    conn.executemany(
        "INSERT INTO logs (line_no, timestamp, level, service, message, raw) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(r["line_no"], r["timestamp"].isoformat(), r["level"],
          r["service"], r["message"], r["raw"]) for r in records],
    )
    conn.commit()


def load_records(conn):
    rows = conn.execute(
        "SELECT line_no, timestamp, level, service, message, raw "
        "FROM logs ORDER BY timestamp"
    ).fetchall()
    return [
        {"line_no": ln, "timestamp": datetime.fromisoformat(ts), "level": lvl,
         "service": svc, "message": msg, "raw": raw}
        for ln, ts, lvl, svc, msg, raw in rows
    ]
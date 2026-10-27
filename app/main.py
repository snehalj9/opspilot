import os

from fastapi import FastAPI, HTTPException

from app.analyzer import analyze
from app.db import get_connection, load_records, save_records
from app.parser import parse_file

app = FastAPI(title="OpsPilot", description="Log incident triage tool")

LOG_DIR = "sample_logs"
DB_PATH = "opspilot.db"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(filename: str = "app.log"):
    """Parse a log file from the sample_logs folder and store it in SQLite."""
    path = os.path.join(LOG_DIR, os.path.basename(filename))  # basename blocks path tricks
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"{path} not found")
    records, skipped = parse_file(path)
    conn = get_connection(DB_PATH)
    try:
        save_records(conn, records)
    finally:
        conn.close()
    return {"file": path, "parsed": len(records), "skipped": skipped}


@app.get("/analysis")
def get_analysis(k: float = 3.0):
    """Analyze the stored logs. k controls spike sensitivity (higher = fewer alerts)."""
    conn = get_connection(DB_PATH)
    try:
        records = load_records(conn)
    finally:
        conn.close()
    if not records:
        raise HTTPException(status_code=400, detail="No logs stored. Call POST /ingest first.")
    return analyze(records, k)
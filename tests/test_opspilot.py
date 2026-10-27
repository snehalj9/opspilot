import random

import generate_logs
from app.analyzer import analyze, group_errors
from app.db import get_connection, load_records, save_records
from app.normalizer import normalize
from app.parser import parse_file, parse_line

GOOD_LINE = ("2026-10-27 10:36:12,345 ERROR payment-service - "
             "Payment P48213 failed: could not acquire DB connection")


def make_records(tmp_path, **kwargs):
    random.seed(1)
    path = str(tmp_path / "app.log")
    generate_logs.generate(path=path, **kwargs)
    records, skipped = parse_file(path)
    return records, skipped


def test_parse_valid_line():
    r = parse_line(GOOD_LINE)
    assert r["level"] == "ERROR"
    assert r["service"] == "payment-service"
    assert r["timestamp"].minute == 36
    assert r["message"].startswith("Payment P48213")


def test_parse_invalid_line_returns_none():
    assert parse_line("this is not a log line") is None


def test_normalize_ids_make_messages_identical():
    a = normalize("Payment P48213 failed: could not acquire DB connection")
    b = normalize("Payment P91002 failed: could not acquire DB connection")
    assert a == b == "Payment <ID> failed: could not acquire DB connection"


def test_normalize_numbers():
    assert normalize("Database connection timeout after 30000ms") == \
        "Database connection timeout after <NUM>ms"


def test_group_errors_counts_templates():
    lines = [
        "2026-10-27 10:00:01,000 ERROR a - Payment P11111 failed",
        "2026-10-27 10:00:02,000 ERROR a - Payment P22222 failed",
        "2026-10-27 10:00:03,000 ERROR a - Disk full",
        "2026-10-27 10:00:04,000 INFO a - all good",
    ]
    records = [parse_line(l, i) for i, l in enumerate(lines)]
    groups = group_errors(records)
    assert groups[0]["count"] == 2
    assert groups[0]["template"] == "Payment <ID> failed"
    assert len(groups) == 2  # INFO line ignored


def test_all_generated_lines_parse(tmp_path):
    records, skipped = make_records(tmp_path)
    assert skipped == 0
    assert len(records) > 1000


def test_planted_incident_is_detected_exactly(tmp_path):
    records, _ = make_records(tmp_path)
    incidents = analyze(records)["incidents"]
    assert len(incidents) == 1
    assert incidents[0]["start"] == "10:35"
    assert incidents[0]["end"] == "10:44"


def test_incident_evidence_points_to_payment_service(tmp_path):
    records, _ = make_records(tmp_path)
    incident = analyze(records)["incidents"][0]
    assert any(g["service"] == "payment-service" for g in incident["top_templates"])
    assert len(incident["evidence_first_lines"]) > 0


def test_no_false_alarm_on_quiet_logs(tmp_path):
    records, _ = make_records(tmp_path, incident_start=0, incident_end=0)
    assert analyze(records)["incidents"] == []


def test_database_roundtrip(tmp_path):
    records, _ = make_records(tmp_path)
    conn = get_connection(str(tmp_path / "test.db"))
    save_records(conn, records)
    loaded = load_records(conn)
    conn.close()
    assert len(loaded) == len(records)
    assert loaded[0]["timestamp"] == records[0]["timestamp"]
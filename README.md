# OpsPilot: Log Incident Triage Tool

A Python tool that parses application logs, groups recurring errors, detects
error-rate spikes, and shows the log lines that support each finding.

## What it does
- Parses log lines with a regular expression into structured records
- Normalizes messages (replaces IDs and numbers) so similar errors share one template
- Groups errors by service and template and counts them
- Detects error spikes per minute using median + MAD (robust to long incidents)
- Returns evidence lines and top error templates for each detected incident
- Stores logs in SQLite and exposes results through a FastAPI REST API

## Run it
```bash
pip install -r requirements.txt
python generate_logs.py
python run_analysis.py
uvicorn app.main:app --reload     # then open http://127.0.0.1:8000/docs
python -m pytest -v
```

## Testing
Logs are synthetic with a planted incident (10:35 to 10:44, database failure in
payment-service). Tests check that the detector finds exactly that window and
raises no alert on logs without an incident.
Result: 10 passed.

## Limitations (honest)
- Logs are synthetic; results show the method works, not that it works on real systems.
- Spike detection is simple statistics, not machine learning.
- It reports correlation and evidence, not proven root causes.
- Only one log format is supported.

## Roadmap (not built yet)
- ML-based error clustering and Isolation Forest comparison
- Spring Boot service that emits real logs
- Dependency graph between services
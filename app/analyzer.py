from collections import Counter
from datetime import timedelta
from statistics import median

from app.normalizer import normalize


def minute_of(ts):
    return ts.replace(second=0, microsecond=0)


def group_errors(records, max_examples=3):
    """Count ERROR lines by (service, template). Most frequent first."""
    groups = {}
    for r in records:
        if r["level"] != "ERROR":
            continue
        key = (r["service"], normalize(r["message"]))
        ts = r["timestamp"].isoformat(timespec="milliseconds")
        if key not in groups:
            groups[key] = {
                "service": r["service"],
                "template": key[1],
                "count": 0,
                "first_seen": ts,
                "last_seen": ts,
                "examples": [],
            }
        g = groups[key]
        g["count"] += 1
        g["first_seen"] = min(g["first_seen"], ts)
        g["last_seen"] = max(g["last_seen"], ts)
        if len(g["examples"]) < max_examples:
            g["examples"].append(r["raw"])
    return sorted(groups.values(), key=lambda g: g["count"], reverse=True)


def errors_per_minute(records):
    """List of (minute, error_count), including minutes with zero errors."""
    if not records:
        return []
    counts = Counter(minute_of(r["timestamp"]) for r in records if r["level"] == "ERROR")
    first = min(minute_of(r["timestamp"]) for r in records)
    last = max(minute_of(r["timestamp"]) for r in records)
    series, t = [], first
    while t <= last:
        series.append((t, counts.get(t, 0)))
        t += timedelta(minutes=1)
    return series


def detect_spikes(series, k=3.0):
    """
    Flag minutes whose error count is far above normal.

    We use the MEDIAN and MAD (median absolute deviation) instead of mean and
    standard deviation. A long incident drags the mean and std upwards and can
    hide itself; the median barely moves.
    threshold = median + k * (1.4826 * MAD), with a minimum spread of 1.
    """
    if len(series) < 5:
        return {"median": 0, "mad": 0, "threshold": 0, "windows": []}

    values = [c for _, c in series]
    med = median(values)
    mad = median(abs(v - med) for v in values)
    sigma = max(1.4826 * mad, 1.0)
    threshold = med + k * sigma

    flagged = [(t, c) for t, c in series if c > threshold]

    # Merge consecutive flagged minutes into windows
    windows = []
    for t, c in flagged:
        if windows and t - windows[-1]["end"] == timedelta(minutes=1):
            w = windows[-1]
            w["end"] = t
            w["total_errors"] += c
            w["peak_per_minute"] = max(w["peak_per_minute"], c)
        else:
            windows.append({"start": t, "end": t, "total_errors": c, "peak_per_minute": c})

    return {"median": med, "mad": mad, "threshold": round(threshold, 2), "windows": windows}


def analyze(records, k=3.0):
    """Run the full analysis and return a JSON-friendly dict."""
    series = errors_per_minute(records)
    spikes = detect_spikes(series, k)

    incidents = []
    for w in spikes["windows"]:
        window_end = w["end"] + timedelta(minutes=1)
        in_window = sorted(
            (r for r in records
             if r["level"] == "ERROR" and w["start"] <= r["timestamp"] < window_end),
            key=lambda r: r["timestamp"],
        )
        incidents.append({
            "start": w["start"].strftime("%H:%M"),
            "end": w["end"].strftime("%H:%M"),
            "total_errors": w["total_errors"],
            "peak_errors_per_minute": w["peak_per_minute"],
            "top_templates": group_errors(in_window)[:3],
            "evidence_first_lines": [r["raw"] for r in in_window[:5]],
            "note": "Shows what failed and when. It does not prove the root cause.",
        })

    return {
        "summary": {
            "total_lines": len(records),
            "error_lines": sum(1 for r in records if r["level"] == "ERROR"),
            "services": sorted({r["service"] for r in records}),
            "baseline_median_errors_per_minute": spikes["median"],
            "spike_threshold": spikes["threshold"],
        },
        "top_error_groups": group_errors(records)[:5],
        "incidents": incidents,
    }
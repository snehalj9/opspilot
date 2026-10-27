import sys

from app.parser import parse_file
from app.analyzer import analyze

path = sys.argv[1] if len(sys.argv) > 1 else "sample_logs/app.log"
records, skipped = parse_file(path)
result = analyze(records)
s = result["summary"]

print(f"File: {path}")
print(f"Parsed {s['total_lines']} lines (skipped {skipped}), {s['error_lines']} errors")
print(f"Normal errors/minute (median): {s['baseline_median_errors_per_minute']}, "
      f"spike threshold: {s['spike_threshold']}")

print("\nTop error templates overall:")
for g in result["top_error_groups"]:
    print(f"  {g['count']:4d}x  [{g['service']}] {g['template']}")

print(f"\nIncidents detected: {len(result['incidents'])}")
for inc in result["incidents"]:
    print(f"\n  Window {inc['start']} - {inc['end']}  "
          f"({inc['total_errors']} errors, peak {inc['peak_errors_per_minute']}/min)")
    print("  Most frequent errors in this window:")
    for g in inc["top_templates"]:
        print(f"    {g['count']:4d}x  [{g['service']}] {g['template']}")
    print("  Evidence (first lines):")
    for line in inc["evidence_first_lines"]:
        print(f"    {line}")
    print(f"  Note: {inc['note']}")
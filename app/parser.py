import re
from datetime import datetime

LOG_PATTERN = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
    r"(?P<level>[A-Z]+) "
    r"(?P<service>\S+) - "
    r"(?P<message>.*)$"
)


def parse_line(line, line_no=0):
    """Return a dict for a valid log line, or None if the line doesn't match."""
    line = line.rstrip("\n")
    match = LOG_PATTERN.match(line)
    if match is None:
        return None
    return {
        "line_no": line_no,
        "timestamp": datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S,%f"),
        "level": match.group("level"),
        "service": match.group("service"),
        "message": match.group("message"),
        "raw": line,
    }


def parse_file(path):
    """Parse a whole file. Returns (records, number_of_skipped_lines)."""
    records, skipped = [], 0
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            record = parse_line(line, line_no)
            if record is None:
                skipped += 1
            else:
                records.append(record)
    return records, skipped
import os
import random
from datetime import datetime, timedelta

random.seed(42)  # same seed = same logs every run, so tests are repeatable

NORMAL_MESSAGES = {
    "api-gateway": ["Request received GET /orders/{id}",
                    "Request completed in {ms}ms status=200"],
    "auth-service": ["User {uid} logged in successfully",
                     "Token validated for user {uid}"],
    "payment-service": ["Payment {pid} processed for order {oid}",
                        "Payment gateway responded in {ms}ms"],
    "order-service": ["Order {oid} created",
                      "Order {oid} status updated to SHIPPED"],
}

BACKGROUND_ERRORS = [
    ("auth-service", "WARN", "Login failed for user {uid}: wrong password"),
    ("order-service", "ERROR", "Order {oid} validation failed: missing address"),
]

INCIDENT_ERRORS = [
    ("payment-service", "ERROR", "Database connection timeout after 30000ms (pool exhausted)"),
    ("payment-service", "ERROR", "Payment {pid} failed: could not acquire DB connection"),
    ("order-service", "ERROR", "Order {oid} failed: payment-service returned 503"),
]


def fill(template):
    return template.format(
        id=random.randint(1000, 9999),
        uid=random.randint(100, 999),
        pid=f"P{random.randint(10000, 99999)}",
        oid=f"O{random.randint(10000, 99999)}",
        ms=random.randint(20, 400),
    )


def format_line(ts, level, service, message):
    millis = ts.microsecond // 1000
    return f"{ts.strftime('%Y-%m-%d %H:%M:%S')},{millis:03d} {level} {service} - {message}"


def generate(path="sample_logs/app.log", minutes=60, incident_start=35, incident_end=45):
    start = datetime(2026, 10, 27, 10, 0, 0)
    entries = []

    for m in range(minutes):
        minute_start = start + timedelta(minutes=m)

        def random_ts():
            return minute_start + timedelta(milliseconds=random.randint(0, 59999))

        for _ in range(random.randint(20, 30)):
            service = random.choice(list(NORMAL_MESSAGES))
            message = fill(random.choice(NORMAL_MESSAGES[service]))
            entries.append((random_ts(), "INFO", service, message))

        for _ in range(random.randint(0, 2)):
            service, level, template = random.choice(BACKGROUND_ERRORS)
            entries.append((random_ts(), level, service, fill(template)))

        if incident_start <= m < incident_end:
            for _ in range(random.randint(15, 25)):
                service, level, template = random.choice(INCIDENT_ERRORS)
                entries.append((random_ts(), level, service, fill(template)))

    entries.sort(key=lambda e: e[0])

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ts, level, service, message in entries:
            f.write(format_line(ts, level, service, message) + "\n")

    errors = sum(1 for e in entries if e[1] == "ERROR")
    print(f"Wrote {len(entries)} lines to {path}")
    print(f"ERROR lines: {errors}")
    print(f"Planted incident window: 10:{incident_start:02d} to 10:{incident_end - 1:02d}")


if __name__ == "__main__":
    generate()
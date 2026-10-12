"""Correlate structured service events to one request."""

import json
from pathlib import Path

from diagnosis.models import Evidence


def correlate_logs(log_path: str | Path, request_id: str) -> list[Evidence]:
    """Return only JSON log events matching the requested ID."""
    path = Path(log_path)
    records = []

    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        start = line.find("{")
        if start == -1:
            continue

        try:
            event = json.loads(line[start:])
        except json.JSONDecodeError:
            continue

        if event.get("request_id") != request_id:
            continue

        records.append(
            Evidence(
                evidence_id=f"L{len(records) + 1:03d}",
                category="application_log",
                signal=event["event"],
                value=event,
                source=f"{path}:{line_number}",
                request_id=request_id,
                timestamp=event.get("timestamp"),
            )
        )

    return records

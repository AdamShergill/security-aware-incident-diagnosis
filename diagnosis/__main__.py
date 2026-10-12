"""Command-line entry point for incident diagnosis."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from diagnosis.correlation import correlate_logs
from diagnosis.engine import diagnose
from diagnosis.evidence import load_evidence


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose incidents using collected evidence."
    )
    parser.add_argument("incident_dir", type=Path)
    args = parser.parse_args()

    incident_dir = args.incident_dir
    evidence = load_evidence(incident_dir)

    request_ids = [
        item.value for item in evidence
        if item.signal == "request_id"
    ]

    if request_ids:
        log_file = incident_dir / "service-logs-complete.txt"
        if not log_file.exists():
            log_file = incident_dir / "service-logs.txt"

        if log_file.exists():
            evidence.extend(
                correlate_logs(log_file, request_ids[0])
            )

    report = diagnose(incident_dir.name, evidence)

    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()

"""Normalize observed incident artifacts into typed evidence."""

import json
from pathlib import Path

from diagnosis.containers import container_state
from diagnosis.firewall import firewall_drop_delta
from diagnosis.models import Evidence


def load_evidence(incident_dir: str | Path) -> list[Evidence]:
    """Read available artifacts without assuming missing values are zero."""
    root = Path(incident_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)

    records: list[Evidence] = []

    def add(category: str, signal: str, value: object, source: Path):
        records.append(
            Evidence(
                evidence_id=f"E{len(records) + 1:03d}",
                category=category,
                signal=signal,
                value=value,
                source=str(source),
            )
        )

    status_file = root / "upstream-request-status.txt"
    if status_file.exists():
        add(
            "application",
            "upstream_http_status",
            int(status_file.read_text().strip()),
            status_file,
        )

    request_file = root / "upstream-request.json"
    if request_file.exists():
        request = json.loads(request_file.read_text())
        request_id = request.get("request_id")
        if request_id is not None:
            records.append(
                Evidence(
                    evidence_id=f"E{len(records) + 1:03d}",
                    category="application",
                    signal="request_id",
                    value=request_id,
                    source=str(request_file),
                    request_id=request_id,
                )
            )

    backend_file = root / "backend-health.json"
    if backend_file.exists():
        health = json.loads(backend_file.read_text())
        add(
            "service_health",
            "backend_healthy",
            health.get("status") == "healthy",
            backend_file,
        )

    probe_file = root / "backend-health-status.txt"
    if probe_file.exists():
        status = probe_file.read_text().strip()
        add(
            "service_health",
            "backend_probe_http_status",
            status,
            probe_file,
        )

    container_file = root / "containers-during-fault.txt"
    state = container_state(container_file)
    if state is not None:
        add("container", "backend_container_state", state, container_file)

    before_file = root / "iptables-before-request.txt"
    after_file = root / "iptables-after-request.txt"
    delta = firewall_drop_delta(before_file, after_file)

    if delta is not None:
        add("network", "firewall_drop_delta", delta, after_file)

    return records

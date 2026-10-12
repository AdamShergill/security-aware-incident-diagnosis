"""Deterministic, evidence-grounded incident diagnosis."""

from diagnosis.models import DiagnosisReport, Evidence, Hypothesis


def diagnose(incident_id: str, evidence: list[Evidence]) -> DiagnosisReport:
    """Rank candidate explanations using observed evidence."""

    signals = {item.signal: item for item in evidence}
    candidates = [
        Hypothesis(cause="backend_unavailable"),
        Hypothesis(cause="network_policy_denial"),
    ]

    backend = candidates[0]
    network = candidates[1]

    def support(candidate: Hypothesis, signal: str, points: int):
        item = signals.get(signal)
        if item is not None:
            candidate.score += points
            candidate.supporting_evidence.append(item.evidence_id)

    def contradict(candidate: Hypothesis, signal: str):
        item = signals.get(signal)
        if item is not None:
            candidate.contradicting_evidence.append(item.evidence_id)

    container = signals.get("backend_container_state")
    probe = signals.get("backend_probe_http_status")
    health = signals.get("backend_healthy")
    drops = signals.get("firewall_drop_delta")

    if container is not None and container.value == "exited":
        support(backend, "backend_container_state", 70)
        contradict(network, "backend_container_state")

    if probe is not None and probe.value == "000":
        support(backend, "backend_probe_http_status", 20)

    if health is not None and health.value is False:
        support(backend, "backend_healthy", 20)

    if health is not None and health.value is True:
        support(network, "backend_healthy", 20)
        contradict(backend, "backend_healthy")

    if drops is not None and isinstance(drops.value, int):
        if drops.value > 0:
            support(network, "firewall_drop_delta", 70)

    candidates.sort(key=lambda item: item.score, reverse=True)

    limitations = []

    if "firewall_drop_delta" not in signals:
        limitations.append("Firewall enforcement evidence was not collected.")

    if "backend_healthy" not in signals and (
        "backend_probe_http_status" not in signals
    ):
        limitations.append("Backend health evidence is unavailable.")

    if candidates[0].score < 50:
        limitations.append(
            "Insufficient evidence to identify a primary root cause."
        )
        candidates.insert(
            0,
            Hypothesis(cause="insufficient_evidence"),
        )

    return DiagnosisReport(
        incident_id=incident_id,
        hypotheses=candidates,
        evidence=evidence,
        limitations=limitations,
    )

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    """A normalized observation from an incident evidence source."""

    evidence_id: str
    category: str
    signal: str
    value: Any
    source: str
    request_id: str | None = None
    timestamp: str | None = None


@dataclass
class Hypothesis:
    """A candidate explanation with supporting and opposing evidence."""

    cause: str
    score: int = 0
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)


@dataclass
class DiagnosisReport:
    """Evidence and ranked hypotheses for a diagnosed incident."""

    incident_id: str
    hypotheses: list[Hypothesis]
    evidence: list[Evidence]
    limitations: list[str] = field(default_factory=list)

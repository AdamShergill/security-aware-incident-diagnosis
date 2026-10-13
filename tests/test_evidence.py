import unittest
from pathlib import Path
from diagnosis.evidence import load_evidence

ROOT = Path(__file__).resolve().parents[1]


class EvidenceReaderTests(unittest.TestCase):
    def test_operational_incident(self):
        evidence = load_evidence(ROOT / "tests/fixtures/operational")
        signals = {e.signal: e.value for e in evidence}

        self.assertEqual(signals["upstream_http_status"], 502)
        self.assertEqual(signals["backend_probe_http_status"], "000")
        self.assertEqual(signals["backend_container_state"], "exited")
        self.assertNotIn("firewall_drop_delta", signals)

    def test_security_incident(self):
        evidence = load_evidence(ROOT / "tests/fixtures/security")
        signals = {e.signal: e.value for e in evidence}

        self.assertEqual(signals["upstream_http_status"], 502)
        self.assertIs(signals["backend_healthy"], True)
        self.assertEqual(signals["firewall_drop_delta"], 2)


if __name__ == "__main__":
    unittest.main()

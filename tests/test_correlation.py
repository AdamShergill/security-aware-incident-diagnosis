import json
import unittest
from pathlib import Path
from diagnosis.correlation import correlate_logs

ROOT = Path(__file__).resolve().parent / "fixtures"


class CorrelationTests(unittest.TestCase):
    def check_incident(self, name):
        folder = ROOT / name
        request_id = json.loads((folder / "upstream-request.json").read_text())["request_id"]
        events = correlate_logs(folder / "service-logs.txt", request_id)
        self.assertEqual([e.signal for e in events], ["dependency_request_started", "dependency_request_failed"])
        self.assertTrue(all(e.request_id == request_id for e in events))
        self.assertTrue(all(e.timestamp for e in events))

    def test_operational(self):
        self.check_incident("operational")

    def test_security(self):
        self.check_incident("security")

    def test_unrelated_request(self):
        events = correlate_logs(ROOT / "security/service-logs.txt", "unrelated-request")
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()

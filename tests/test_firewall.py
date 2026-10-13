import tempfile
import unittest
from pathlib import Path

from diagnosis.firewall import firewall_drop_delta


FIXTURE = Path(__file__).resolve().parent / "fixtures/security"


class FirewallTests(unittest.TestCase):
    def compare(self, before, after):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "before.txt"
            second = root / "after.txt"
            first.write_text(before)
            second.write_text(after)
            return firewall_drop_delta(first, second)

    def snapshot(self, packets, destination="172.18.0.2", comment="arbitrary"):
        return (
            "Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination\n"
            f"1 {packets} 0 DROP 6 -- * * 0.0.0.0/0 {destination} "
            f"tcp dpt:8080 /* {comment} */\n"
        )

    def test_recorded_incident(self):
        self.assertEqual(
            firewall_drop_delta(
                FIXTURE / "iptables-before-request.txt",
                FIXTURE / "iptables-after-request.txt",
            ),
            2,
        )

    def test_comment_does_not_affect_match(self):
        self.assertEqual(
            self.compare(self.snapshot(0, comment="alpha"),
                         self.snapshot(3, comment="beta")),
            3,
        )

    def test_unchanged_counter(self):
        self.assertEqual(
            self.compare(self.snapshot(0), self.snapshot(0)),
            0,
        )

    def test_different_destination(self):
        self.assertIsNone(
            self.compare(self.snapshot(0, destination="172.18.0.2"),
                         self.snapshot(2, destination="172.18.0.99"))
        )

    def test_counter_reset(self):
        self.assertIsNone(
            self.compare(self.snapshot(5), self.snapshot(1))
        )

    def test_duplicate_rules(self):
        before = self.snapshot(0)
        after = self.snapshot(2)
        self.assertIsNone(self.compare(before + before.splitlines()[-1] + "\n", after))

    def test_missing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(
                firewall_drop_delta(root / "missing.txt",
                                    FIXTURE / "iptables-after-request.txt")
            )


if __name__ == "__main__":
    unittest.main()

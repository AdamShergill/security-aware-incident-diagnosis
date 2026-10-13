import tempfile
import unittest
from pathlib import Path
from diagnosis.containers import container_state

FIXTURE = Path(__file__).resolve().parent / "fixtures/operational/containers-during-fault.txt"

class ContainerTests(unittest.TestCase):
    def parse(self, content, service="backend"):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "containers.txt"
            path.write_text(content)
            return container_state(path, service)

    def test_recorded_incident(self):
        self.assertEqual(container_state(FIXTURE), "exited")

    def test_renamed_container(self):
        data = FIXTURE.read_text().replace("incident-prototype-backend-1", "custom-project-backend-1")
        self.assertEqual(self.parse(data), "exited")

    def test_running_backend(self):
        data = FIXTURE.read_text().replace("Exited (137) About a minute ago", "Up 14 minutes")
        self.assertEqual(self.parse(data), "running")

    def test_missing_service(self):
        data = FIXTURE.read_text().replace("   backend   ", "   other     ")
        self.assertIsNone(self.parse(data))

    def test_missing_file(self):
        self.assertIsNone(container_state(Path("/nonexistent/incident-containers.txt")))


    def test_duplicate_backend(self):
        data = FIXTURE.read_text()
        backend_line = data.splitlines()[1]
        self.assertIsNone(self.parse(data + backend_line + "\n"))

    def test_missing_columns(self):
        self.assertIsNone(self.parse("NAME IMAGE STATUS\nexample image Up\n"))

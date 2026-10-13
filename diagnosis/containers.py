from pathlib import Path
import re

def container_state(path: Path, service: str = "backend") -> str | None:
    if not path.is_file():
        return None

    lines = path.read_text().splitlines()
    if not lines:
        return None

    header = re.split(r"\s{2,}", lines[0].strip())
    if "SERVICE" not in header or "STATUS" not in header:
        return None

    service_index = header.index("SERVICE")
    status_index = header.index("STATUS")
    states = []

    for line in lines[1:]:
        columns = re.split(r"\s{2,}", line.strip())
        if len(columns) <= max(service_index, status_index):
            continue
        if columns[service_index] != service:
            continue

        status = columns[status_index]
        if status.startswith("Exited"):
            states.append("exited")
        elif status.startswith("Up"):
            states.append("running")
        else:
            states.append("unknown")

    return states[0] if len(states) == 1 else None

"""Compare firewall DROP counters for matching TCP rules."""

import re
from pathlib import Path


def read_rules(path: Path) -> dict[tuple, int] | None:
    if not path.is_file():
        return None

    rules = {}
    in_output = False

    for line in path.read_text().splitlines():
        if line.startswith("Chain "):
            in_output = line.startswith("Chain OUTPUT ")
            continue

        if not in_output:
            continue

        columns = line.split()
        if len(columns) < 11:
            continue

        if columns[3] != "DROP" or columns[4] not in ("6", "tcp"):
            continue

        if not re.search(r"\bdpt:8080\b", line):
            continue

        try:
            packets = int(columns[1])
        except ValueError:
            return None

        if packets < 0:
            return None

        identity = tuple(columns[3:10]) + ("dpt:8080",)
        if identity in rules:
            return None

        rules[identity] = packets

    return rules


def firewall_drop_delta(before: Path, after: Path) -> int | None:
    earlier = read_rules(before)
    later = read_rules(after)

    if earlier is None or later is None:
        return None

    if len(earlier) != 1 or set(earlier) != set(later):
        return None

    identity = next(iter(earlier))
    delta = later[identity] - earlier[identity]

    return delta if delta >= 0 else None

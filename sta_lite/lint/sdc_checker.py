from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SdcClock:
    name: str | None
    port: str
    line: int


def parse_create_clocks(path: Path) -> list[SdcClock]:
    if not path.is_file():
        return []
    clocks: list[SdcClock] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "create_clock" not in stripped:
            continue
        name_match = re.search(r"-name\s+([A-Za-z_][A-Za-z0-9_$]*)", stripped)
        port_match = re.search(r"\[get_ports\s+\{?([A-Za-z_][A-Za-z0-9_$]*)\}?\]", stripped)
        if not port_match:
            parts = stripped.split()
            port = parts[-1].strip("{}") if parts else ""
        else:
            port = port_match.group(1)
        if port:
            clocks.append(SdcClock(name=name_match.group(1) if name_match else None, port=port, line=line_no))
    return clocks


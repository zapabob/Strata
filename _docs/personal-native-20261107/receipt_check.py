"""Validate the additive native memory receipt against actual pre-READY output."""
from __future__ import annotations

import re
from pathlib import Path


def check(stdout: Path, mode: str) -> dict[str, str]:
    lines = stdout.read_text(encoding="utf-8").splitlines()
    ready = [i for i, line in enumerate(lines) if line.startswith("READY ")]
    receipts = [(i, line) for i, line in enumerate(lines) if line.startswith("INFO q36_memory_mode=")]
    assert len(ready) == 1 and len(receipts) == 1, "Exactly one actual memory INFO and READY required"
    index, line = receipts[0]
    assert index < ready[0], "Memory receipt arrived after READY"
    fields = dict(part.split("=", 1) for part in line.split()[1:])
    assert len(fields) == len(line.split()) - 1 == 6, "Duplicate or additional memory fields"
    assert fields["q36_memory_mode"] == mode
    assert fields["q36_memory_scope"] == "expert-working-storage"
    assert fields["q36_memory_total_process_bound"] == "0"
    for name in ("cpu_stage", "h2d_stage", "io_scratch"):
        assert re.fullmatch(r"0|[1-9][0-9]*", fields["q36_memory_" + name + "_bytes"])
    return fields

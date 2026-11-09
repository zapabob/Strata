"""Strict, CPU-only checks for the native Q36 serial protocol (not an input hash proof)."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field

CAPACITY = 4096
MAX_NEW = 128
MTP_HEADROOM = 3  # two drafts plus the verifier's next cell
EXPECTED = {"begin": "ALPHA7K", "middle": "BRAVO9M", "end": "CHARLIE4P"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def ids_sha(ids: list[int]) -> str:
    """SHA-256 of ordered IDs as compact ASCII JSON, no newline."""
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode("ascii")).hexdigest()


def validate_input(ids: list[int], declared: int, max_new: int = MAX_NEW) -> None:
    require(bool(ids) and all(type(t) is int and t >= 0 for t in ids), "invalid input IDs")
    require(len(ids) == declared, "input count changed/truncated")
    require(max_new == MAX_NEW, "output budget must remain explicitly 128")
    require(len(ids) + max_new + MTP_HEADROOM <= CAPACITY, "input/output/MTP capacity overflow")


def roundtrip(tok: object, text: str) -> list[int]:
    ids = tok.encode(text, parse_special=True)
    require(tok.decode(ids, errors="strict") == text, "text roundtrip failed")
    require(tok.encode(tok.decode(ids, errors="strict"), parse_special=True) == ids, "re-encoded ordered IDs changed")
    validate_input(ids, len(ids))
    return ids


def exact_answer(text: str, eos: str) -> bool:
    """No reasoning/substring extraction: one JSON object with exactly three correct pairs."""
    text = text.strip()
    if eos and text.endswith(eos):
        text = text[: -len(eos)].strip()

    def pairs(items: list[tuple[str, str]]) -> dict:
        require(len({k for k, _ in items}) == len(items), "duplicate answer keys")
        return dict(items)

    try:
        answer = json.loads(text, object_pairs_hook=pairs)
    except (ValueError, TypeError):
        return False
    return answer == EXPECTED


def finite(value: str) -> float:
    number = float(value)
    require(math.isfinite(number) and number >= 0, "nonfinite/negative telemetry")
    return number


def natural(value: str) -> int:
    require(re.fullmatch(r"0|[1-9][0-9]*", value) is not None, "invalid count")
    return int(value)


@dataclass
class Exchange:
    """Parse actual T/PP/DONE, preserving raw lines in the separate transcript."""

    submitted: int
    reuse_min: int = 0
    reuse_max: int = 0
    cancel: bool = False
    generated: list[int] = field(default_factory=list)
    progress: list[dict] = field(default_factory=list)
    done: dict | None = None

    def feed(self, line: str) -> None:
        require(self.done is None, "protocol data after DONE")
        f = line.split()
        require(bool(f), "empty protocol line")
        if f[0] == "ERR":
            raise ValueError("native ERR: " + line)
        if f[0] == "T":
            require(len(f) == 2, "malformed T")
            self.generated.append(natural(f[1]))
            require(len(self.generated) <= MAX_NEW, "generation exceeds requested budget")
        elif f[0] == "PP":
            require(len(f) == 5, "malformed Q36 PP")
            row = dict(read=natural(f[1]), total=natural(f[2]), ms=finite(f[3]), rate=finite(f[4]))
            require(row["read"] <= row["total"] <= self.submitted, "PP count overflow")
            if self.progress:
                require(
                    row["total"] == self.progress[-1]["total"] and row["read"] >= self.progress[-1]["read"],
                    "PP regression",
                )
            self.progress.append(row)
        elif f[0] == "DONE":
            require(len(f) == 16, "wrong signed-r3 Q36 DONE schema")
            for i in (1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 15):
                natural(f[i])
            for i in (3, 4, 13):
                finite(f[i])
            self.done = dict(
                generatedCount=int(f[1]),
                nativePromptCount=int(f[2]),
                promptMs=float(f[3]),
                decodeMs=float(f[4]),
                finish=f[5],
                nativeReuseCount=int(f[8]),
                nativeFreshReadCount=int(f[14]),
                raw=line,
            )
        else:
            raise ValueError("unexpected request protocol: " + line)

    def finish(self) -> dict:
        require(self.done is not None, "missing DONE")
        d = self.done
        require(
            d["finish"] == "cancel" if self.cancel else d["finish"] in ("length", "stop"),
            "unexpected finish (including nonfinite)",
        )
        require(d["nativePromptCount"] == self.submitted, "native input truncated/count mismatch")
        require(self.reuse_min <= d["nativeReuseCount"] <= self.reuse_max, "owner/cache reuse boundary")
        require(
            d["nativeFreshReadCount"] + d["nativeReuseCount"] == self.submitted,
            "fresh + reuse does not account for all submitted IDs",
        )
        require(d["generatedCount"] == len(self.generated) and bool(self.generated), "empty/missing generated IDs")
        fresh = d["nativeFreshReadCount"]
        require(
            bool(self.progress)
            and self.progress[-1]["read"] == fresh
            and all(p["total"] == fresh for p in self.progress),
            "PP does not account for fresh input",
        )
        return {
            **d,
            "submittedCount": self.submitted,
            "generatedIds": self.generated,
            "progress": self.progress,
            "protocolCountReceipt": True,
            "cryptographicConsumedInputProof": False,
        }

"""Compare raw native Qwen3.8 logits on identical forced prefixes."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

LOGGER = logging.getLogger(__name__)
VOCABULARY = 248_320
LogitRow = NDArray[np.float64]


def read_case(path: Path) -> tuple[list[str], dict[str, object]]:
    """Read receipt, engine fields and resource minima for a completed case."""
    process = json.loads((path / "process.json").read_text(encoding="utf-8"))
    if process["status"] != "exited" or process["child_exit_code"] != 0:
        raise ValueError(f"Case did not complete: {path.name}")
    text = (path / "engine.log").read_text(encoding="utf-8-sig")
    samples = [
        json.loads(line)
        for line in (path / "resources.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    timing = re.search(r"^TIMING (.+)$", text, flags=re.MULTILINE)
    payload = re.search(r"\bkv_payload_bytes=(\d+)", text)
    if timing is None or payload is None or not samples:
        raise ValueError(f"Missing timing or KV/resource information: {path.name}")
    fields = {k: float(v) for k, v in re.findall(r"(\w+)=([\d.]+)", timing[1])}
    return process["command"], {
        "kv_payload_bytes": int(payload[1]),
        "timing": fields,
        "decode_forward_tokens_per_second": fields["decode_steps"]
        * 1000
        / fields["decode_forward_ms"],
        "minimum_device_free_mib": min(s["gpu_free_mib"] for s in samples),
        "minimum_system_ram_free_bytes": min(
            s["available_physical_bytes"] for s in samples
        ),
        "minimum_commit_headroom_bytes": min(
            s["available_commit_bytes"] for s in samples
        ),
    }


def log_softmax(values: LogitRow) -> LogitRow:
    """Return a float64 log probability row."""
    shifted = values - values.max()
    return shifted - np.log(np.exp(shifted).sum())


def compare(baseline: Path, candidate: Path) -> dict[str, object]:
    """Validate the paired conditions and score every full-vocabulary row."""
    ref_cmd, reference = read_case(baseline)
    cand_cmd, alternate = read_case(candidate)

    def option(cmd: list[str], flag: str) -> str:
        return cmd[cmd.index(flag) + 1]

    comparables = ("--model", "--ctx-size", "--tokens", "--force", "--spec-draft-n-max")
    if ref_cmd[0] != cand_cmd[0] or any(
        option(ref_cmd, k) != option(cand_cmd, k) for k in comparables
    ):
        raise ValueError("The cases differ outside the intended KV configuration")
    force_count = len(option(ref_cmd, "--force").split(","))
    row_count = force_count + 1
    shape = (row_count, VOCABULARY)
    logits = []
    for case in (baseline, candidate):
        path = case / "logits.bin"
        if path.stat().st_size != row_count * VOCABULARY * 4:
            raise ValueError(f"Unexpected raw logit payload length: {case.name}")
        logits.append(np.memmap(path, mode="r", dtype="<f4", shape=shape))
    kl_values, max_errors = [], []
    top1_matches = 0
    for ref, cand in zip(*logits, strict=True):
        a, b = ref.astype(np.float64), cand.astype(np.float64)
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("A paired logit row contains nonfinite values")
        pa, pb = log_softmax(a), log_softmax(b)
        kl_values.append(float(np.dot(np.exp(pa), pa - pb)))
        max_errors.append(float(np.max(np.abs(a - b))))
        top1_matches += int(a.argmax() == b.argmax())
    return {
        "context_capacity": int(option(ref_cmd, "--ctx-size")),
        "prefill_tokens": len(option(ref_cmd, "--tokens").split(",")),
        "forced_tokens": force_count,
        "logit_rows": row_count,
        "vocabulary": VOCABULARY,
        "reference_mode": option(ref_cmd, "--kv"),
        "candidate_mode": option(cand_cmd, "--kv"),
        "reference": reference,
        "candidate": alternate,
        "top1_agreement_count": top1_matches,
        "mean_full_vocab_kl_nats": float(np.mean(kl_values)),
        "max_full_vocab_kl_nats": max(kl_values),
        "max_abs_logit_error": max(max_errors),
    }


def main() -> int:
    """Write a fixed-token comparison with its measurement scope."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.reference, args.candidate)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    LOGGER.info("Paired full-vocabulary comparison written to %s", args.output)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())

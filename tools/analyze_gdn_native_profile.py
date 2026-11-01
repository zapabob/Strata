"""Compare completed, identically configured native baseline/profile diagnostics.

GPU stamps describe the instrumented graph, including waits. They must not be
used to reconstruct uninstrumented latency or physical I/O. Incomplete runs are
rejected; window counts are checked. Equal counts alone do not prove phase identity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def compare(baseline: Path, profile: Path) -> dict:
    left, right = read(baseline / "binding.json"), read(profile / "binding.json")
    for key in ("binary_sha256", "capacity", "prompt_tokens", "max_new_per_request", "requests",
                "budget", "tokenizer_hashes", "profile_sha256", "model_files"):
        if left[key] != right[key]:
            raise ValueError("Unmatched binding: " + key)
    if left["command"] != right["command"]:
        raise ValueError("Unmatched engine arguments")
    instrumented = dict(right["instrumented_env"])
    for key in ("STRATA_VERIFY_PROFILE", "STRATA_DECODE_TIMING"):
        if instrumented.pop(key, None) != "1":
            raise ValueError("Missing instrumentation flag")
    if left["instrumented_env"] != instrumented:
        raise ValueError("Other runtime flags differ")
    summaries = [read(directory / "summary.json") for directory in (baseline, profile)]
    for summary, directory in zip(summaries, (baseline, profile), strict=True):
        receipt = read(directory / "result.json")
        if (not summary["pass"] or receipt["exit_code"] != 0 or not receipt["termination_confirmed"]
                or receipt["job_active_after"] != 0 or receipt["observed_dropped_bytes"] != 0
                or len(summary["requests"]) != left["requests"]):
            raise ValueError("Incomplete or failed native run: " + str(directory))
    requests = []
    for before, after in zip(summaries[0]["requests"], summaries[1]["requests"], strict=True):
        if before["count"] <= 0 or after["count"] <= 0:
            raise ValueError("No generated tokens")
        requests.append({
            "token_ids_equal": before["tokens"] == after["tokens"],
            "baseline_count": before["count"], "profile_count": after["count"],
            "baseline_decode_ms": before["decode_ms"], "profile_decode_ms": after["decode_ms"],
            "baseline_ms_per_emitted_token": before["decode_ms"] / before["count"],
            "profile_ms_per_emitted_token": after["decode_ms"] / after["count"],
            "baseline_prompt_ms": before["prompt_ms"], "profile_prompt_ms": after["prompt_ms"],
        })
    timings = summaries[1]["timing_lines"]
    host = [line for line in timings if line.startswith("strata decode timing:")]
    gpu = [line for line in timings if line.startswith("strata decode GPU stages (ms/window):")]
    if len(host) != len(requests) or len(gpu) != len(requests):
        raise ValueError("Missing per-request timing lines")
    profiles = []
    for host_line, gpu_line in zip(host, gpu, strict=True):
        host_match = re.search(r"timing: (\d+) windows, avg T ([\d.]+), ([\d.]+) tokens/window", host_line)
        gpu_match = re.search(r"total ([\d.]+) ms/window over (\d+) windows", gpu_line)
        if host_match is None or gpu_match is None:
            raise ValueError("Unrecognized timing format")
        sections = gpu_line.split("GDN layers:", 1)[1].split(" | QSA layers:", 1)
        sections[1] = sections[1].split(" | total", 1)[0]
        stages = {}
        for kind, section in zip(("GDN", "QSA"), sections, strict=True):
            stages[kind] = {name.strip(): float(value)
                            for name, value in re.findall(r"(.+?) ([0-9]+\.[0-9]+)(?= |$)", section)}
        profiles.append({
            "host_windows": int(host_match[1]), "gpu_windows": int(gpu_match[2]),
            "counts_match": int(host_match[1]) == int(gpu_match[2]),
            "avg_window_width": float(host_match[2]), "emitted_tokens_per_window": float(host_match[3]),
            "gpu_instrumented_total_ms_per_window": float(gpu_match[1]),
            "gpu_instrumented_stages_ms_per_window": stages,
            "host_line": host_line,
        })
    return {
        "binding_match": True,
        "emitted_token_ids_equal": all(row["token_ids_equal"] for row in requests),
        "requests": requests, "profiles": profiles,
        "gpu_host_window_counts_match": all(row["counts_match"] for row in profiles),
        "limits": "Short diagnostic with profiling-altered fusion/overlap; no speedup, quality, "
                  "131k or physical-DRAM/I/O claim. Matching token IDs do not prove matching logits. "
                  "Stage intervals include waits and stamp overhead; nested host timers are not additive.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.profile), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
"""Bounded native-model timing diagnostic, separate from 131k qualification.

Reuses the repository's Windows Job containment. Never controls existing
processes, installed settings, or GPU privileges. Baseline and profile use the
same fixed model, short prompt, target-only decode and memory budget. The GPU
profile changes some fusion/overlap choices; its times are diagnostic only.
Run: uv run --no-project --python 3.12 --with regex==2026.9.29 python <script> <arm>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.perf131k import windows_job
from tools.perf131k.pilot import system_resources
from tools.strata_tokenizer import Tokenizer

ENGINE = Path("H:/Strata/releases/hakua040-native-upstream-r1/Release/strata.exe")
ENGINE_SHA = "b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1"
DESTINATION = Path("H:/Strata/evidence/gdn-native-followup-20261102")
PACK = Path("H:/Strata/packs/q2_0")
SHARD1 = Path("H:/Strata/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf")
SHARD2 = Path("H:/Strata/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf")
GIB = 1024**3
PROMPT = ("<|im_start|>system\nYou are a careful assistant. Give a concise answer.\n<|im_end|>\n"
          "<|im_start|>user\nExplain why a square orthogonal matrix preserves the Euclidean norm. "
          "Write the identity and explain it in two sentences.\n<|im_end|>\n"
          "<|im_start|>assistant\n<think>\n")


class GpuMemoryFloor(RuntimeError):
    """Dedicated VRAM crossed the diagnostic floor; terminate only our Job."""


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def save(path: Path, data: object) -> None:
    with path.open("x", encoding="utf-8") as output:
        json.dump(data, output, indent=2, allow_nan=False)


def tokenizer() -> Tokenizer:
    directory = PACK / "tokenizer"
    vocab = json.loads((directory / "vocab.json").read_text(encoding="utf-8"))
    tokens = [None] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    meta = json.loads((directory / "tokenizer.json").read_text(encoding="utf-8"))
    return Tokenizer(tokens, (directory / "merges.txt").read_text(encoding="utf-8").splitlines(),
                     json.loads((directory / "token_type.json").read_text(encoding="utf-8")),
                     meta["pre"], meta["special_ids"])


def gpu() -> dict:
    fields = ["memory.free", "memory.used", "utilization.gpu", "clocks.sm", "clocks.mem"]
    result = subprocess.run(
        ["nvidia-smi", "-i", "0", "--query-gpu=" + ",".join(fields), "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True, timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    values = [int(part.strip()) for part in result.stdout.strip().split(",")]
    if len(values) != len(fields):
        raise ValueError("Unexpected GPU telemetry")
    return {"monotonic_s": time.monotonic(), **dict(zip(fields, values, strict=True))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=("baseline", "profile"))
    parser.add_argument("--label", choices=("r1", "r2", "r3", "r4"), default="r1")
    args = parser.parse_args()
    if os.name != "nt" or digest(ENGINE) != ENGINE_SHA:
        raise ValueError("Windows and exact baseline engine required")
    for path in (PACK / "index.txt", PACK / "dense.bin", PACK / "experts.bin", SHARD1, SHARD2):
        if not path.is_file():
            raise ValueError("Model input missing: " + str(path))
    tok = tokenizer()
    ids = tok.encode(PROMPT, parse_special=True)
    if tok.decode(ids) != PROMPT or not 1 < len(ids) < 256:
        raise ValueError("Prompt round trip/count failed")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    cell = DESTINATION / (args.arm + "-" + args.label)
    cell.mkdir(exist_ok=False)
    budget = SimpleNamespace(timeout_s=480, job_commit_bytes=12 * GIB, output_bytes=8 * 1024**2,
                             max_processes=1, min_available_ram=2 * GIB,
                             min_commit_headroom=6 * GIB, min_H_free=8 * GIB)
    before = system_resources(cell)
    gpu_before = gpu()
    save(cell / "before.json", {"host": before, "gpu": gpu_before})
    if (before["available_ram"] < 16 * GIB or before["commit_headroom"] < 18 * GIB
            or before["H_free"] < 8 * GIB or gpu_before["memory.free"] < 8192):
        save(cell / "result.json", {"status": "PREFLIGHT_REFUSED", "engine_launched": False})
        return 77
    protocol = cell / "stdin.txt"
    # Two independent fresh requests: the second can benefit from OS file cache.
    # Prompt/conversation caching is disabled; no checkpoint or real user data.
    protocol.write_text(("GEN 8 " + ",".join(map(str, ids)) + "\n") * 2 + "QUIT\n", encoding="ascii")
    command = [str(ENGINE), "--pack", str(PACK), "--native", str(SHARD1), "--ple-gguf", str(SHARD2),
               "--expert-profile", str(ROOT / "data/expert-profile.bin"), "--expert-cache", "512",
               "--mmap-experts", "--pool-workers", "4", "--pcie-frac", "0.18", "--adapt-swaps", "0",
               "--ple-io", "direct", "--max-context", "4096", "--prefill", "32",
               "--kv", "k8v4", "--spec", "2", "--suffix-draft", "0", "--lookup-chain", "0",
               "--short-read", "0", "--prompt-cache", "0", "--conversation-cache-mib", "0",
               "--greedy", "--serve", "--stats"]
    # Whitelisted environment avoids accidentally inheriting experimental engine flags.
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA")
           if key in os.environ}
    env["PATH"] = str(ENGINE.parent) + os.pathsep + os.environ.get("PATH", "")
    env["STRATA_ROUTE_TAIL_SKIP"] = "0"
    if args.arm == "profile":
        env.update(STRATA_VERIFY_PROFILE="1", STRATA_DECODE_TIMING="1")
    save(cell / "binding.json", {
        "binary": str(ENGINE), "binary_sha256": ENGINE_SHA, "command": command,
        "instrumentation": args.arm, "instrumented_env": {key: value for key, value in env.items() if key.startswith("STRATA_")},
        "controller_sha256": digest(Path(__file__)), "containment_sha256": digest(Path(windows_job.__file__)),
        "regex_version": importlib.metadata.version("regex"), "admission_min_ram_bytes": 16 * GIB,
        "capacity": 4096, "prompt": PROMPT, "prompt_tokens": ids,
        "max_new_per_request": 8, "requests": 2, "budget": vars(budget),
        "tokenizer_hashes": {p.name: digest(p) for p in sorted((PACK / "tokenizer").iterdir()) if p.is_file()},
        "profile_sha256": digest(ROOT / "data/expert-profile.bin"),
        "model_files": [{"path": str(p), "bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns}
                        for p in (SHARD1, SHARD2, PACK / "dense.bin", PACK / "experts.bin")],
        "model_full_content_hash": None,
        "limitation": "Short target-only diagnostic; not 131k, standard MTP, HTTP, quality or speedup qualification.",
    })
    samples = [gpu_before]
    next_gpu = time.monotonic() + 2

    def sample(root: Path) -> dict:
        nonlocal next_gpu
        resources = system_resources(root)
        if time.monotonic() >= next_gpu:
            samples.append(gpu())
            next_gpu = time.monotonic() + 2
        # Dedicated-memory telemetry, not cudaMemGetInfo's WDDM virtual allowance.
        # A distinct exception keeps a GPU floor from being mislabeled as low host RAM.
        if samples[-1]["memory.free"] < 1024:
            raise GpuMemoryFloor("Dedicated VRAM below 1024 MiB")
        return resources

    result = windows_job.run_owned(command, cell, env, cell / "native.log", budget, sample,
                                   stdin_path=protocol, memory_diagnostics=True)
    save(cell / "result.json", result)
    save(cell / "gpu-samples.json", samples)
    raw = (cell / "native.log").read_text(encoding="utf-8", errors="replace")
    completions = []
    generated: list[int] = []
    for line in raw.splitlines():
        if line.startswith("T "):
            generated.append(int(line.split()[1]))
        elif line.startswith("DONE "):
            fields = line.split()
            completions.append({"raw": line, "tokens": generated.copy(), "text": tok.decode(generated),
                                "count": int(fields[1]), "prompt_count": int(fields[2]),
                                "prompt_ms": float(fields[3]), "decode_ms": float(fields[4]), "finish": fields[5]})
            generated.clear()
    passed = (result["exit_code"] == 0 and result["termination_confirmed"]
              and len(completions) == 2 and all(r["count"] == len(r["tokens"]) > 0
                                             and r["finish"] in ("stop", "length") for r in completions))
    summary = {"pass": passed, "controller": result["status"], "requests": completions,
               "timing_lines": [line for line in raw.splitlines() if line.startswith("strata decode ")],
               "gpu_min_free_mib": min(row["memory.free"] for row in samples)}
    save(cell / "summary.json", summary)
    print(json.dumps({"cell": str(cell), "pass": passed, "controller": result["status"],
                      "requests": len(completions), "gpu_min_free_mib": summary["gpu_min_free_mib"]}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
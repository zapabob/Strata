"""Phase XIV — Mode B Draftless Speculative Decoding Evaluator.

Evaluates Inkling-2-Mini Mode B (CPU/RAM cold-MoE offload) across:
  - Speculation disabled (Mode B Strict baseline)
  - ngram-cache, ngram-simple, ngram-map-k, ngram-map-k4v, ngram-mod
  - Draft lengths: 4, 8, 16, 32 (where supported by each mode)

Mandatory checks:
  - Greedy token-sequence parity (exact text & finish_reason match vs baseline at temp=0.0)
  - JSON grammar & tool-call argument preservation
  - Independent cold-cache (fresh server restart) and warm-cache runs (no cross-mode cache leak)
  - Peak dedicated VRAM, Windows shared GPU memory, peak system RAM, effective decode tok/s,
    draft acceptance metrics parsed from llama-server logs.

Uses logging + tqdm, strict typing, UTF-8, and zero print()/eval()/exec().
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

from tqdm import tqdm

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from phase13_acceptance_eval import (  # noqa: E402
    VramPeakMonitor,
    chat_completion,
    query_gpu_and_ram,
    query_process_shared_gpu_mib,
    stop_server,
    wait_health,
)

LOGGER = logging.getLogger("phase14.modeB_spec")

SPEC_PROMPTS: list[dict[str, Any]] = [
    {
        "id": "code_refactor_python",
        "kind": "coding",
        "max_tokens": 256,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Refactor this Python function to preserve order, add strict type hints, and include a concise docstring. "
                    "Output only the Python code block:\n"
                    "```python\n"
                    "def merge_records(primary, secondary):\n"
                    "    out = []\n"
                    "    seen = set()\n"
                    "    for item in primary + secondary:\n"
                    "        k = item['id']\n"
                    "        if k not in seen:\n"
                    "            seen.add(k)\n"
                    "            out.append(item)\n"
                    "    return out\n"
                    "```"
                ),
            }
        ],
    },
    {
        "id": "tool_call_json",
        "kind": "tool_call",
        "max_tokens": 160,
        "messages": [
            {
                "role": "user",
                "content": "Call inspect_vram_budget with device_index=0, context_tokens=139264, and kv_quant='q8_0'.",
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "inspect_vram_budget",
                    "description": "Compute VRAM headroom for an Inkling-2-Mini deployment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_index": {"type": "integer"},
                            "context_tokens": {"type": "integer"},
                            "kv_quant": {"type": "string"},
                        },
                        "required": ["device_index", "context_tokens", "kv_quant"],
                    },
                },
            }
        ],
    },
    {
        "id": "jp_technical_summary",
        "kind": "japanese_technical",
        "max_tokens": 192,
        "messages": [
            {
                "role": "user",
                "content": (
                    "次の構成仕様を日本語で3点の箇条書きに要約してください。"
                    "仕様: RTX 5060 Ti 16GB上でInkling-2-Miniを139264コンテキストで運用する。"
                    "全48バンクのMoEエキスパートはNVFP4を維持し、3回反復されるblk.6..17をGPU常駐、"
                    "1回のみ訪問されるblk.0..5とblk.22..23を32GB RAM/NVMeへオフロードする。KVキャッシュはq8_0とする。"
                ),
            }
        ],
    },
]


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def build_spec_args(mode: str, draft_len: int) -> list[str]:
    if mode == "none":
        return ["--spec-type", "none"]
    if mode == "ngram-cache":
        return ["--spec-type", "ngram-cache", "--spec-draft-n-max", str(draft_len)]
    if mode == "ngram-simple":
        return ["--spec-type", "ngram-simple", "--spec-ngram-simple-size-m", str(draft_len)]
    if mode == "ngram-map-k":
        return ["--spec-type", "ngram-map-k", "--spec-ngram-map-k-size-m", str(draft_len)]
    if mode == "ngram-map-k4v":
        return ["--spec-type", "ngram-map-k4v", "--spec-ngram-map-k4v-size-m", str(draft_len)]
    if mode == "ngram-mod":
        return ["--spec-type", "ngram-mod", "--spec-ngram-mod-n-max", str(draft_len)]
    raise ValueError(f"Unsupported speculative mode: {mode}")


def parse_spec_stats_from_log(log_path: Path) -> dict[str, Any]:
    if not log_path.is_file():
        return {}
    text = log_path.read_text(encoding="utf-8", errors="replace")
    # llama-server logs draft/accept lines when speculative decoding runs
    drafted = [int(m) for m in re.findall(r"drafted\s*=\s*(\d+)", text)]
    accepted = [int(m) for m in re.findall(r"accepted\s*=\s*(\d+)", text)]
    rates = [float(m) for m in re.findall(r"accept\w*\s*(?:rate)?\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)\s*%", text, flags=re.IGNORECASE)]
    out: dict[str, Any] = {}
    if drafted:
        out["drafted_total"] = sum(drafted)
    if accepted:
        out["accepted_total"] = sum(accepted)
    if drafted and accepted and sum(drafted) > 0:
        out["acceptance_rate_pct"] = round(100.0 * sum(accepted) / sum(drafted), 2)
    elif rates:
        out["acceptance_rate_pct"] = round(sum(rates) / len(rates), 2)
    return out


def launch_modeB_server(
    server_exe: Path,
    model_path: Path,
    *,
    ctx: int,
    ub: int,
    port: int,
    log_path: Path,
    ot_rules: list[str],
    spec_args: list[str],
) -> tuple[subprocess.Popen[str], Any]:
    cmd = [
        str(server_exe),
        "-m", str(model_path),
        "-ngl", "99",
        "--load-mode", "none",
        "-fit", "off",
        "-fa", "on",
        "-ctk", "q8_0",
        "-ctv", "q8_0",
        "-c", str(ctx),
        "-ub", str(ub),
        "-b", "2048",
        "-np", "1",
        "-t", "6",
        "--jinja",
        "--cache-ram", "0",
        "--no-context-shift",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    for ot in ot_rules:
        cmd.extend(["-ot", ot])
    cmd.extend(spec_args)
    fh = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, text=True)
    return proc, fh


def run_single_config(
    args: argparse.Namespace,
    mode: str,
    draft_len: int,
    baseline_outputs: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{args.port}"
    tag = f"{mode}_d{draft_len}"
    log_path = args.out.parent / f"spec_{tag}.log"
    spec_args = build_spec_args(mode, draft_len)
    proc, fh = launch_modeB_server(
        args.server,
        args.model,
        ctx=args.ctx,
        ub=args.ub,
        port=args.port,
        log_path=log_path,
        ot_rules=args.ot,
        spec_args=spec_args,
    )
    record: dict[str, Any] = {
        "mode": mode,
        "draft_len": draft_len,
        "spec_args": spec_args,
        "ot_rules": args.ot,
        "started": False,
    }
    try:
        load_s = wait_health(base_url, proc, timeout_s=240.0)
        monitor = VramPeakMonitor(proc.pid, interval_s=1.0)
        monitor.start()
        cold_runs: dict[str, Any] = {}
        warm_runs: dict[str, Any] = {}
        try:
            # Cold-cache pass (fresh server, empty n-gram cache)
            for p in SPEC_PROMPTS:
                body, lat = chat_completion(
                    base_url,
                    p["messages"],
                    max_tokens=p["max_tokens"],
                    temperature=0.0,
                    reasoning_effort="none",
                    tools=p.get("tools"),
                    timeout_s=300.0,
                )
                msg = body["choices"][0]["message"]
                cold_runs[p["id"]] = {
                    "content": msg.get("content") or "",
                    "tool_calls": msg.get("tool_calls") or [],
                    "finish_reason": body["choices"][0].get("finish_reason"),
                    "latency_s": lat,
                    "predicted_per_second": body.get("timings", {}).get("predicted_per_second"),
                    "prompt_per_second": body.get("timings", {}).get("prompt_per_second"),
                    "completion_tokens": body.get("usage", {}).get("completion_tokens"),
                }
            # Warm-cache pass (same prompts in same session to measure warm n-gram speedup)
            for p in SPEC_PROMPTS:
                body, lat = chat_completion(
                    base_url,
                    p["messages"],
                    max_tokens=p["max_tokens"],
                    temperature=0.0,
                    reasoning_effort="none",
                    tools=p.get("tools"),
                    timeout_s=300.0,
                )
                msg = body["choices"][0]["message"]
                warm_runs[p["id"]] = {
                    "content": msg.get("content") or "",
                    "tool_calls": msg.get("tool_calls") or [],
                    "finish_reason": body["choices"][0].get("finish_reason"),
                    "latency_s": lat,
                    "predicted_per_second": body.get("timings", {}).get("predicted_per_second"),
                    "completion_tokens": body.get("usage", {}).get("completion_tokens"),
                }
        finally:
            peak_hw = monitor.stop()

        parity_details: dict[str, bool] = {}
        if baseline_outputs is not None:
            for pid, run in cold_runs.items():
                ref = baseline_outputs[pid]
                parity_details[pid] = (
                    run["content"] == ref["content"]
                    and run["tool_calls"] == ref["tool_calls"]
                    and run["finish_reason"] == ref["finish_reason"]
                )
        cold_tps = [r["predicted_per_second"] for r in cold_runs.values() if r.get("predicted_per_second")]
        warm_tps = [r["predicted_per_second"] for r in warm_runs.values() if r.get("predicted_per_second")]
        record.update(
            {
                "started": True,
                "load_seconds": load_s,
                "cold_mean_decode_tps": round(sum(cold_tps) / len(cold_tps), 2) if cold_tps else None,
                "warm_mean_decode_tps": round(sum(warm_tps) / len(warm_tps), 2) if warm_tps else None,
                "greedy_parity_by_prompt": parity_details if baseline_outputs is not None else "baseline",
                "greedy_parity_all_exact": all(parity_details.values()) if baseline_outputs is not None else True,
                "peak_hw": peak_hw,
                "vram_safety_floor_ok": (peak_hw.get("min_vram_free_mib") or 0) >= 768,
                "shared_gpu_spill_ok": (peak_hw.get("peak_shared_gpu_mib") or 0.0) < 156.0,
                "cold_runs": cold_runs,
                "warm_runs": warm_runs,
            }
        )
    except Exception as exc:
        record["error"] = str(exc)
    finally:
        stop_server(proc, fh)
        time.sleep(2.0)

    record["log_spec_stats"] = parse_spec_stats_from_log(log_path)
    return record


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--ctx", type=int, default=16384)
    p.add_argument("--ub", type=int, default=32)
    p.add_argument("--port", type=int, default=8097)
    p.add_argument("--ot", action="append", default=[r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps=CPU"])
    p.add_argument("--modes", default="ngram-cache,ngram-simple,ngram-map-k,ngram-map-k4v,ngram-mod")
    p.add_argument("--draft-lens", default="4,8,16,32")
    args = p.parse_args(argv)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Running Phase XIV Mode B Strict baseline (speculation disabled)...")
    baseline = run_single_config(args, "none", 0, None)
    if not baseline.get("started"):
        raise RuntimeError(f"Baseline Mode B Strict failed to start: {baseline.get('error')}")
    baseline_outputs = baseline["cold_runs"]

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    draft_lens = [int(x) for x in args.draft_lens.split(",") if x.strip()]
    grid = [(m, d) for m in modes for d in draft_lens]

    results: list[dict[str, Any]] = [baseline]
    for mode, dlen in tqdm(grid, desc="phase14-spec-grid", unit="cfg"):
        res = run_single_config(args, mode, dlen, baseline_outputs)
        results.append(res)
        LOGGER.info(
            "mode=%s d=%d | cold=%.2f t/s warm=%.2f t/s | parity=%s | min_free=%s MiB",
            mode,
            dlen,
            res.get("cold_mean_decode_tps") or 0.0,
            res.get("warm_mean_decode_tps") or 0.0,
            res.get("greedy_parity_all_exact"),
            (res.get("peak_hw") or {}).get("min_vram_free_mib"),
        )
        # Checkpoint after every config so progress is never lost
        args.out.write_text(
            json.dumps({"schema": "phase14-modeB-spec-v1", "model": args.model.name, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

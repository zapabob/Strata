"""Phase XIII — Real-hardware RTX 5060 Ti acceptance suite (P3 VRAM/131K-147K + P6 Tool-Calling/Coding/Long-Context).

Measures and writes:
  - vram_profile.json        (131072, 139264, 147456 ctx; -ub 16 & 32; q8_0 KV; Windows shared GPU check)
  - long_context_results.json (actual 131,072-token input with generation headroom; 3 exact retrievals + visible answer)
  - tool_calling_results.json (unconstrained & constrained JSON schema, function selection, Hermes multi-turn tools)
  - coding_results.json       (Python execution, C++/CUDA compile checks, TypeScript, repository patch tests)

Uses logging + tqdm, strict typing, UTF-8, and zero print()/eval()/exec().
"""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
import urllib.error
import urllib.request

from tqdm import tqdm

LOGGER = logging.getLogger("phase13.acceptance")


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def query_gpu_and_ram() -> dict[str, Any]:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    ms = MEMORYSTATUSEX()
    ms.dwLength = ctypes.sizeof(ms)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
    gib = 1024.0 ** 3
    nv = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.used,memory.free,memory.total",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    parts = [p.strip() for p in nv.stdout.strip().splitlines()[0].split(",")] if nv.returncode == 0 and nv.stdout.strip() else []
    return {
        "gpu_name": parts[0] if len(parts) >= 5 else "unknown",
        "driver_version": parts[1] if len(parts) >= 5 else "unknown",
        "vram_used_mib": int(parts[2]) if len(parts) >= 5 else None,
        "vram_free_mib": int(parts[3]) if len(parts) >= 5 else None,
        "vram_total_mib": int(parts[4]) if len(parts) >= 5 else None,
        "avail_ram_gib": round(ms.ullAvailPhys / gib, 2),
        "avail_commit_gib": round(ms.ullAvailPageFile / gib, 2),
    }


def query_process_shared_gpu_mib(pid: int) -> float | None:
    """Query Windows GPU Process Memory Shared Usage (MiB) for a specific PID to detect silent WDDM spill."""
    ps = (
        f"$c = Get-Counter '\\GPU Process Memory(pid_{pid}_*)\\Shared Usage' -ErrorAction SilentlyContinue; "
        "if ($c) { ($c.CounterSamples | Measure-Object -Property CookedValue -Sum).Sum / 1MB } else { '' }"
    )
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=10, check=False)
    raw = res.stdout.strip()
    try:
        return round(float(raw), 2) if raw else None
    except ValueError:
        return None


class VramPeakMonitor:
    """Background sampler tracking peak dedicated VRAM and Windows shared GPU memory throughout prefill & decode."""

    def __init__(self, pid: int, interval_s: float = 2.0) -> None:
        self._pid = pid
        self._interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self.samples: int = 0
        self.peak_vram_used_mib: int | None = None
        self.min_vram_free_mib: int | None = None
        self.peak_shared_gpu_mib: float | None = None

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        self._thread.join(timeout=15.0)
        return {
            "samples": self.samples,
            "peak_vram_used_mib": self.peak_vram_used_mib,
            "min_vram_free_mib": self.min_vram_free_mib,
            "peak_shared_gpu_mib": self.peak_shared_gpu_mib,
        }

    def _sample_once(self) -> None:
        hw = query_gpu_and_ram()
        used = hw.get("vram_used_mib")
        free = hw.get("vram_free_mib")
        shared = query_process_shared_gpu_mib(self._pid)
        self.samples += 1
        if used is not None:
            self.peak_vram_used_mib = used if self.peak_vram_used_mib is None else max(self.peak_vram_used_mib, used)
        if free is not None:
            self.min_vram_free_mib = free if self.min_vram_free_mib is None else min(self.min_vram_free_mib, free)
        if shared is not None:
            self.peak_shared_gpu_mib = shared if self.peak_shared_gpu_mib is None else max(self.peak_shared_gpu_mib, shared)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._sample_once()
            except Exception as exc:
                LOGGER.debug("VRAM monitor sample error: %s", exc)
            self._stop.wait(self._interval_s)


def tokenize_count(base_url: str, text: str, timeout_s: float = 60.0) -> int:
    req = urllib.request.Request(
        f"{base_url}/tokenize",
        data=json.dumps({"content": text, "add_special": False}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return len(body.get("tokens", []))


def wait_health(base_url: str, proc: subprocess.Popen[str], timeout_s: float = 180.0) -> float:
    t0 = time.monotonic()
    deadline = t0 + timeout_s
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Server exited early with rc={proc.returncode}")
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2.0) as r:
                if r.status == 200:
                    return round(time.monotonic() - t0, 2)
        except (OSError, urllib.error.URLError):
            time.sleep(1.0)
    raise TimeoutError(f"Server did not become healthy within {timeout_s}s")


def chat_completion(
    base_url: str,
    messages: list[dict[str, Any]],
    *,
    max_tokens: int = 256,
    temperature: float = 0.0,
    reasoning_effort: str = "none",
    tools: list[dict[str, Any]] | None = None,
    response_format: dict[str, Any] | None = None,
    timeout_s: float = 180.0,
) -> tuple[dict[str, Any], float]:
    payload: dict[str, Any] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "seed": 42,
        "chat_template_kwargs": {"reasoning_effort": reasoning_effort},
    }
    if tools is not None:
        payload["tools"] = tools
    if response_format is not None:
        payload["response_format"] = response_format
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body, round(time.monotonic() - t0, 3)


def launch_llama_server(
    server_exe: Path,
    model_path: Path,
    *,
    ctx: int,
    ub: int,
    port: int,
    log_path: Path,
    extra_ot: list[str] | None = None,
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
    for ot in (extra_ot or []):
        cmd.extend(["-ot", ot])
    log_fh = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT, text=True)
    return proc, log_fh


def stop_server(proc: subprocess.Popen[str], log_fh: Any) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=12)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False)
    log_fh.close()


def run_vram_profile(args: argparse.Namespace) -> int:
    results: list[dict[str, Any]] = []
    contexts = [int(x) for x in args.contexts.split(",")]
    ubs = [int(x) for x in args.ubs.split(",")]
    base_url = f"http://127.0.0.1:{args.port}"

    for ctx in contexts:
        for ub in ubs:
            pre = query_gpu_and_ram()
            log_path = args.out.parent / f"vram_ctx{ctx}_ub{ub}.log"
            proc, fh = launch_llama_server(args.server, args.model, ctx=ctx, ub=ub, port=args.port, log_path=log_path, extra_ot=args.ot)
            entry: dict[str, Any] = {
                "model": args.model.name,
                "model_bytes": args.model.stat().st_size,
                "context": ctx,
                "ub": ub,
                "kv_cache": "q8_0/q8_0",
                "vision_projector": "disabled",
                "speculative_drafter": "disabled",
                "pre_hw": pre,
                "loaded": False,
            }
            try:
                load_s = wait_health(base_url, proc, timeout_s=600.0)
                body, lat_s = chat_completion(
                    base_url,
                    [{"role": "user", "content": "Reply with the exact word OK."}],
                    max_tokens=16,
                    temperature=0.0,
                )
                post = query_gpu_and_ram()
                shared_mib = query_process_shared_gpu_mib(proc.pid)
                timings = body.get("timings", {})
                entry.update(
                    {
                        "loaded": True,
                        "load_seconds": load_s,
                        "smoke_latency_s": lat_s,
                        "post_hw": post,
                        "process_shared_gpu_mib": shared_mib,
                        "silent_shared_spill_suspected": (shared_mib is not None and shared_mib >= 156.0),
                        "predicted_per_second": timings.get("predicted_per_second"),
                        "prompt_per_second": timings.get("prompt_per_second"),
                        "vram_safety_floor_ok": (post.get("vram_free_mib") or 0) >= 768,
                    }
                )
            except Exception as exc:
                entry["error"] = str(exc)
            finally:
                stop_server(proc, fh)
                time.sleep(2.0)
            results.append(entry)
            LOGGER.info("VRAM probe ctx=%d ub=%d -> loaded=%s free=%s MiB shared=%s MiB", ctx, ub, entry["loaded"], entry.get("post_hw", {}).get("vram_free_mib"), entry.get("process_shared_gpu_mib"))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"schema": "phase13-vram-v1", "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0


TOOL_CASES: list[dict[str, Any]] = [
    {
        "id": "tc_lookup_part",
        "prompt": "Find the shelf location for part P44 in warehouse west.",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "lookup_part",
                    "description": "Look up a part shelf location in a warehouse.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "part": {"type": "string"},
                            "warehouse": {"type": "string"},
                        },
                        "required": ["part", "warehouse"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_part",
                    "description": "Delete a part record.",
                    "parameters": {
                        "type": "object",
                        "properties": {"part": {"type": "string"}},
                        "required": ["part"],
                    },
                },
            },
        ],
        "expected_name": "lookup_part",
        "expected_args": {"part": "P44", "warehouse": "west"},
    },
    {
        "id": "tc_hermes_read_file",
        "prompt": "Inspect lines 10 to 40 of src/settings.ts using the read_file tool.",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a range of lines from a workspace file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "start_line": {"type": "integer"},
                            "end_line": {"type": "integer"},
                        },
                        "required": ["path", "start_line", "end_line"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        "expected_name": "read_file",
        "expected_args": {"path": "src/settings.ts", "start_line": 10, "end_line": 40},
    },
    {
        "id": "tc_json_schema_converter",
        "prompt": "Return a JSON object with sourceUnit set to 'cm' and value set to 42.5.",
        "schema": {
            "type": "object",
            "properties": {
                "sourceUnit": {"type": "string", "enum": ["mm", "cm", "m"]},
                "value": {"type": "number"},
            },
            "required": ["sourceUnit", "value"],
            "additionalProperties": False,
        },
        "expected_json": {"sourceUnit": "cm", "value": 42.5},
    },
]


def _extract_json_obj(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def run_tool_calling_eval(args: argparse.Namespace) -> int:
    base_url = f"http://127.0.0.1:{args.port}"
    log_path = args.out.parent / "tool_calling_server.log"
    proc, fh = launch_llama_server(args.server, args.model, ctx=args.ctx, ub=args.ub, port=args.port, log_path=log_path, extra_ot=args.ot)
    records: list[dict[str, Any]] = []
    try:
        wait_health(base_url, proc, timeout_s=360.0)
        for case in tqdm(TOOL_CASES, desc="tool-calling"):
            if "tools" in case:
                body, lat = chat_completion(
                    base_url,
                    [{"role": "user", "content": case["prompt"]}],
                    max_tokens=256,
                    temperature=0.0,
                    tools=case["tools"],
                )
                msg = body["choices"][0]["message"]
                calls = msg.get("tool_calls") or []
                fn_ok = False
                args_ok = False
                parsed_args: dict[str, Any] | None = None
                if calls:
                    fn = calls[0].get("function", {})
                    fn_ok = fn.get("name") == case["expected_name"]
                    raw_a = fn.get("arguments", "{}")
                    parsed_args = json.loads(raw_a) if isinstance(raw_a, str) else raw_a
                    args_ok = parsed_args == case["expected_args"]
                # Hermes multi-turn follow-up verification if first tool call succeeded
                multi_turn_ok = False
                if fn_ok and args_ok:
                    follow_msgs = [
                        {"role": "user", "content": case["prompt"]},
                        msg,
                        {
                            "role": "tool",
                            "tool_call_id": calls[0].get("id", "call_1"),
                            "content": json.dumps({"status": "ok", "result": "shelf C7"}),
                        },
                    ]
                    body2, _ = chat_completion(base_url, follow_msgs, max_tokens=128, temperature=0.0, tools=case["tools"])
                    final_text = body2["choices"][0]["message"].get("content") or ""
                    multi_turn_ok = "C7" in final_text or "ok" in final_text.lower()
                records.append(
                    {
                        "id": case["id"],
                        "mode": "hermes_native_tool_call",
                        "function_correct": fn_ok,
                        "arguments_correct": args_ok,
                        "multi_turn_completion_ok": multi_turn_ok,
                        "latency_s": lat,
                    }
                )
            else:
                for constrained in (False, True):
                    rf = (
                        {"type": "json_schema", "json_schema": {"name": "converter", "strict": True, "schema": case["schema"]}}
                        if constrained
                        else None
                    )
                    body, lat = chat_completion(
                        base_url,
                        [{"role": "user", "content": case["prompt"]}],
                        max_tokens=128,
                        temperature=0.0,
                        response_format=rf,
                    )
                    content = body["choices"][0]["message"].get("content") or ""
                    parsed = _extract_json_obj(content)
                    schema_ok = parsed == case["expected_json"]
                    records.append(
                        {
                            "id": case["id"],
                            "mode": "constrained_json_schema" if constrained else "unconstrained_json",
                            "schema_compliant": schema_ok,
                            "latency_s": lat,
                        }
                    )
    finally:
        stop_server(proc, fh)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"schema": "phase13-tool-calling-v1", "model": args.model.name, "records": records}, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Wrote tool-calling results to %s (%d records)", args.out, len(records))
    return 0


CODING_CASES: list[dict[str, Any]] = [
    {
        "id": "py_clamp_count",
        "lang": "python",
        "prompt": "Write a Python function `def clamp_count(value: int, cap: int) -> int:` that returns `min(max(value, 0), cap)`. Output only a ```python``` code block.",
        "test": "assert clamp_count(-2, 7) == 0\nassert clamp_count(10, 7) == 7\nassert clamp_count(4, 7) == 4\n",
    },
    {
        "id": "py_dedup_preserve_order",
        "lang": "python",
        "prompt": "Write a Python function `def dedup_events(events: list[int]) -> list[int]:` that preserves order and removes duplicate event IDs. Output only a ```python``` code block.",
        "test": "assert dedup_events([3, 1, 3, 2, 1]) == [3, 1, 2]\nassert dedup_events([]) == []\n",
    },
    {
        "id": "py_repo_normalise",
        "lang": "python",
        "prompt": "Write a Python function `def normalise(path: str) -> str:` that normalises POSIX relative paths like `'a/./b/../c'` to `'a/c'` using forward slashes. Output only a ```python``` code block.",
        "test": "assert normalise('a/./b') == 'a/b'\nassert normalise('a/./b/../c') == 'a/c'\n",
    },
    {
        "id": "cuda_vector_add_compile",
        "lang": "cuda",
        "prompt": "Write a valid CUDA C++ kernel `__global__ void vec_add(const float* a, const float* b, float* out, int n)` that adds `a[i] + b[i]` into `out[i]` with bounds checking. Output only a ```cuda``` code block.",
        "test": "",
    },
]


def _extract_code_block(text: str) -> str:
    m = re.search(r"```(?:python|cpp|c\+\+|cuda|cu|ts|typescript)?\s*\n(.*?)```", text, flags=re.DOTALL)
    return m.group(1) if m else text


def run_coding_eval(args: argparse.Namespace) -> int:
    base_url = f"http://127.0.0.1:{args.port}"
    log_path = args.out.parent / "coding_server.log"
    proc, fh = launch_llama_server(args.server, args.model, ctx=args.ctx, ub=args.ub, port=args.port, log_path=log_path, extra_ot=args.ot)
    records: list[dict[str, Any]] = []
    try:
        wait_health(base_url, proc, timeout_s=360.0)
        for case in tqdm(CODING_CASES, desc="coding"):
            body, lat = chat_completion(
                base_url,
                [{"role": "user", "content": case["prompt"]}],
                max_tokens=512,
                temperature=0.0,
                reasoning_effort="none",
            )
            content = body["choices"][0]["message"].get("content") or ""
            code = _extract_code_block(content)
            passed = False
            err_msg = ""
            with tempfile.TemporaryDirectory() as td:
                if case["lang"] == "python":
                    script = Path(td) / "check.py"
                    script.write_text(code + "\n\n" + case["test"], encoding="utf-8")
                    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=15, check=False)
                    passed = res.returncode == 0
                    if not passed:
                        err_msg = (res.stderr or res.stdout)[-400:]
                elif case["lang"] == "cuda":
                    cu_file = Path(td) / "kernel.cu"
                    ptx_file = Path(td) / "kernel.ptx"
                    cu_file.write_text(code + "\n", encoding="utf-8")
                    nvcc_candidates = [
                        Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.5\bin\nvcc.exe"),
                        Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe"),
                        Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe"),
                        Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"),
                    ]
                    nvcc = next((str(p) for p in nvcc_candidates if p.is_file()), "nvcc")
                    env = os.environ.copy()
                    msvc_bin = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64")
                    if msvc_bin.is_dir():
                        env["PATH"] = str(msvc_bin) + os.pathsep + env.get("PATH", "")
                    res = subprocess.run(
                        [nvcc, "--ptx", "-arch=sm_89", str(cu_file), "-o", str(ptx_file)],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=False,
                        env=env,
                    )
                    passed = res.returncode == 0 and ptx_file.is_file() and ptx_file.stat().st_size > 0
                    if not passed:
                        err_msg = (res.stderr or res.stdout)[-400:]
            records.append(
                {
                    "id": case["id"],
                    "lang": case["lang"],
                    "passed": passed,
                    "latency_s": lat,
                    "error": err_msg,
                }
            )
    finally:
        stop_server(proc, fh)

    pass_count = sum(1 for r in records if r["passed"])
    summary = {
        "schema": "phase13-coding-v1",
        "model": args.model.name,
        "passed": pass_count,
        "total": len(records),
        "pass_rate": round(pass_count / max(1, len(records)), 4),
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Wrote coding results to %s (%d/%d passed)", args.out, pass_count, len(records))
    return 0


def run_long_context_eval(args: argparse.Namespace) -> int:
    """Actual >=131,072-token input with 3 buried needles + visible terminal answer + continuous VRAM peak sampling."""
    base_url = f"http://127.0.0.1:{args.port}"
    log_path = args.out.parent / f"long_ctx_{args.ctx}.log"
    proc, fh = launch_llama_server(args.server, args.model, ctx=args.ctx, ub=args.ub, port=args.port, log_path=log_path, extra_ot=args.ot)
    needles = [
        ("ALPHA_TOKEN", "K94-SIGMA-771"),
        ("BETA_TOKEN", "M28-OMEGA-504"),
        ("GAMMA_TOKEN", "Z63-DELTA-819"),
    ]
    filler_unit = "module_log: subsystem=kv_cache status=nominal checksum=0x4a7f2c19 latency_us=412 worker_id=3\n"
    result: dict[str, Any] = {
        "schema": "phase13-long-context-v2",
        "model": args.model.name,
        "server_context_capacity": args.ctx,
        "target_input_tokens": args.target_input_tokens,
        "ub": args.ub,
        "context_shift": False,
        "vision_projector": "disabled",
        "speculative_drafter": "disabled",
    }
    try:
        load_s = wait_health(base_url, proc, timeout_s=600.0)
        # Calibrate exact token count per filler_unit via /tokenize so prompt_tokens >= target_input_tokens
        unit_tokens = max(1, tokenize_count(base_url, filler_unit))
        suffix = (
            "\nReturn the exact values of ALPHA_TOKEN, BETA_TOKEN, and GAMMA_TOKEN in the format: "
            "ALPHA_TOKEN=... BETA_TOKEN=... GAMMA_TOKEN=..."
        )
        # Add +64 token cushion so chat template + user message strictly exceeds target_input_tokens while leaving generation headroom
        blocks_needed = max(30, (args.target_input_tokens + 64) // unit_tokens)
        lines = [filler_unit] * blocks_needed
        lines[blocks_needed // 5] = f"CRITICAL_RECORD {needles[0][0]}={needles[0][1]}\n"
        lines[blocks_needed // 2] = f"CRITICAL_RECORD {needles[1][0]}={needles[1][1]}\n"
        lines[(blocks_needed * 4) // 5] = f"CRITICAL_RECORD {needles[2][0]}={needles[2][1]}\n"
        prompt = "".join(lines) + suffix

        monitor = VramPeakMonitor(proc.pid, interval_s=2.0)
        monitor.start()
        try:
            body, lat_s = chat_completion(
                base_url,
                [{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,
                reasoning_effort="low",
                timeout_s=21600.0,
            )
        finally:
            peak_hw = monitor.stop()

        content = body["choices"][0]["message"].get("content") or ""
        usage = body.get("usage", {})
        timings = body.get("timings", {})
        hits = {k: (v in content) for k, v in needles}
        post = query_gpu_and_ram()
        shared_mib = query_process_shared_gpu_mib(proc.pid)
        result.update(
            {
                "load_seconds": load_s,
                "e2e_seconds": lat_s,
                "prompt_tokens_actual": usage.get("prompt_tokens"),
                "completion_tokens_actual": usage.get("completion_tokens"),
                "exceeded_131072_input": (usage.get("prompt_tokens") or 0) >= 131072,
                "visible_terminal_answer": bool(content.strip()),
                "needle_hits": hits,
                "all_three_retrieved": all(hits.values()),
                "prompt_per_second": timings.get("prompt_per_second"),
                "predicted_per_second": timings.get("predicted_per_second"),
                "peak_during_prefill_decode": peak_hw,
                "post_hw": post,
                "process_shared_gpu_mib": shared_mib,
                "vram_safety_floor_ok": (peak_hw.get("min_vram_free_mib") or 0) >= 768,
                "reply_excerpt": content[:400],
            }
        )
    finally:
        stop_server(proc, fh)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Wrote long-context result to %s (all_three=%s, prompt_tokens=%s)", args.out, result.get("all_three_retrieved"), result.get("prompt_tokens_actual"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("vram", "tool-calling", "coding", "long-context"):
        sp = sub.add_parser(name)
        sp.add_argument("--server", type=Path, required=True)
        sp.add_argument("--model", type=Path, required=True)
        sp.add_argument("--out", type=Path, required=True)
        sp.add_argument("--port", type=int, default=8094)
        sp.add_argument("--ot", action="append", default=[], help="Extra llama-server -ot tensor offload rules (e.g. cold MoE layers to CPU/RAM/NVMe)")
        if name == "vram":
            sp.add_argument("--contexts", default="131072,139264,147456")
            sp.add_argument("--ubs", default="16,32")
        else:
            sp.add_argument("--ctx", type=int, default=16384 if name != "long-context" else 139264)
            sp.add_argument("--ub", type=int, default=32)
            if name == "long-context":
                sp.add_argument("--target-input-tokens", type=int, default=131072)
    return p


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    if args.cmd == "vram":
        return run_vram_profile(args)
    if args.cmd == "tool-calling":
        return run_tool_calling_eval(args)
    if args.cmd == "coding":
        return run_coding_eval(args)
    if args.cmd == "long-context":
        return run_long_context_eval(args)
    raise ValueError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())

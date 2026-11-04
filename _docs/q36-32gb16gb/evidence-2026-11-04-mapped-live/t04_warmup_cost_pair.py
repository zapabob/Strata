#!/usr/bin/env python3
"""T04 observational paired run: mapped-pack warmup vs --no-warmup.

Same UD-Q4_K_XL, ctx 65536, FP32 KV (engine default), MTP 2, mapped-pack.
Measures load→READY, READY→first useful token, first DONE, second TTFT.
Does NOT change product defaults. Does NOT invent speeds. DESIGN #6: never kill Hermes.
Does NOT mark the durable goal complete. One pair only — not an adoption decision.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EXPECTED_SHA256 = "64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7"
DEFAULT_EXE = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Strata"
    / "components"
    / "engine"
    / "0.4.0-q36-windows-x86_64-cuda-cuda13"
    / "strata.exe"
)
DEFAULT_GGUF = Path(
    r"H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
)
READY_RE = re.compile(r"(?m)^READY\b")
Q36_STARTUP_RE = re.compile(r"^Q36_STARTUP\b")
PIN_POOL_RE = re.compile(r"mapped-pack host pin pool|pin pool", re.I)
WARMUP_RE = re.compile(r"warm(?:ed|up)|warmup_", re.I)
# Minimal chat-ish ids; quality is not the T04 claim — cost movement is.
# 248045 = engine default --turn-token (<|im_start|>) per --help on this build.
GEN_LINE = "GEN 16 248045,872,198,77091,198,2610,525,264,3465,13,151645,198,248045,77091,198"


def jst_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def nvidia_query() -> dict:
    out = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()
    name, total, used, free, util = [p.strip() for p in out.split(",")]
    return {
        "name": name,
        "vram_total_mib": int(float(total)),
        "vram_used_mib": int(float(used)),
        "vram_free_mib": int(float(free)),
        "gpu_util_percent": int(float(util)),
    }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def wait_ready(proc: subprocess.Popen[str], stdout_path: Path, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if READY_RE.search(read_text(stdout_path)):
            return True
        if proc.poll() is not None:
            return False
        time.sleep(2.0)
    return READY_RE.search(read_text(stdout_path)) is not None


def wait_marker(
    stdout_path: Path,
    proc: subprocess.Popen[str],
    prefix: str,
    after_line_count: int,
    timeout_s: int,
) -> tuple[list[str], float | None]:
    """Wait for a new line starting with prefix after after_line_count stdout lines."""
    deadline = time.time() + timeout_s
    t0 = time.perf_counter()
    while time.time() < deadline:
        lines = read_text(stdout_path).splitlines()
        new = [ln for ln in lines[after_line_count:] if ln.startswith(prefix)]
        if new:
            return new, (time.perf_counter() - t0) * 1000.0
        if proc.poll() is not None:
            lines = read_text(stdout_path).splitlines()
            new = [ln for ln in lines[after_line_count:] if ln.startswith(prefix)]
            return new, ((time.perf_counter() - t0) * 1000.0) if new else None
        time.sleep(0.25)
    lines = read_text(stdout_path).splitlines()
    new = [ln for ln in lines[after_line_count:] if ln.startswith(prefix)]
    return new, ((time.perf_counter() - t0) * 1000.0) if new else None


def extract_startup(stderr_text: str) -> dict:
    q36 = [ln for ln in stderr_text.splitlines() if Q36_STARTUP_RE.search(ln)]
    pin = [ln for ln in stderr_text.splitlines() if PIN_POOL_RE.search(ln)]
    warm = [ln for ln in stderr_text.splitlines() if WARMUP_RE.search(ln)]
    return {
        "q36_startup_lines": q36,
        "pin_pool_lines": pin,
        "warmup_related_lines": warm,
    }


def launch(
    exe: Path,
    gguf: Path,
    out_dir: Path,
    label: str,
    *,
    no_warmup: bool,
) -> tuple[subprocess.Popen[str], Path, Path, list[str]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"{label}-stdout.log"
    stderr_path = out_dir / f"{label}-stderr.log"
    argv = [
        str(exe),
        "--native",
        str(gguf),
        "--max-context",
        "65536",
        "--prefill",
        "auto",
        "--mtp",
        "2",
        "--q36-expert-store",
        "mapped-pack",
        "--serve",
    ]
    if no_warmup:
        argv.insert(-1, "--no-warmup")
    env = os.environ.copy()
    env.setdefault("TMP", r"H:\Strata\tmp-q36-mapped-live")
    env.setdefault("TEMP", env["TMP"])
    Path(env["TMP"]).mkdir(parents=True, exist_ok=True)
    so = stdout_path.open("w", encoding="utf-8", newline="\n", buffering=1)
    se = stderr_path.open("w", encoding="utf-8", newline="\n", buffering=1)
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=so,
        stderr=se,
        env=env,
        cwd=str(out_dir),
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    proc._strata_so = so  # type: ignore[attr-defined]
    proc._strata_se = se  # type: ignore[attr-defined]
    (out_dir / f"{label}-pid.txt").write_text(str(proc.pid), encoding="ascii")
    (out_dir / f"{label}-argv.json").write_text(json.dumps(argv, indent=2), encoding="utf-8")
    return proc, stdout_path, stderr_path, argv


def close_logs(proc: subprocess.Popen[str]) -> None:
    for attr in ("_strata_so", "_strata_se"):
        handle = getattr(proc, attr, None)
        if handle is not None:
            try:
                handle.flush()
                handle.close()
            except OSError:
                pass


def send(proc: subprocess.Popen[str], line: str) -> None:
    assert proc.stdin is not None
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def stop_and_eof(proc: subprocess.Popen[str], timeout_s: int = 120) -> dict:
    """STOP then stdin EOF — T03 showed STOP alone leaves idle serve resident."""
    result = {"stop_sent": False, "eof_closed": False, "exited": False, "wait_s": None}
    t0 = time.perf_counter()
    try:
        send(proc, "STOP")
        result["stop_sent"] = True
    except (BrokenPipeError, OSError, ValueError):
        pass
    if proc.stdin is not None and not proc.stdin.closed:
        try:
            proc.stdin.close()
            result["eof_closed"] = True
        except OSError:
            pass
    try:
        proc.wait(timeout=timeout_s)
        result["exited"] = True
    except subprocess.TimeoutExpired:
        result["exited"] = False
    result["wait_s"] = round(time.perf_counter() - t0, 3)
    close_logs(proc)
    return result


def run_arm(
    *,
    exe: Path,
    gguf: Path,
    out_dir: Path,
    label: str,
    no_warmup: bool,
    ready_timeout: int,
    gen_timeout: int,
) -> dict:
    gpu_before = nvidia_query()
    arm: dict = {
        "label": label,
        "no_warmup": no_warmup,
        "started_at": jst_now(),
        "gpu_before": gpu_before,
        "invented_speeds": False,
        "defaults_changed": False,
    }
    if gpu_before["vram_free_mib"] < 12000:
        arm["result"] = "BLOCKED_VRAM"
        return arm

    t_launch = time.perf_counter()
    proc, out_path, err_path, argv = launch(exe, gguf, out_dir, label, no_warmup=no_warmup)
    arm["pid"] = proc.pid
    arm["argv"] = argv
    print(f"{label} pid={proc.pid} no_warmup={no_warmup}", flush=True)

    ok_ready = wait_ready(proc, out_path, ready_timeout)
    ready_ms = (time.perf_counter() - t_launch) * 1000.0
    arm["ready_ok"] = ok_ready
    arm["load_request_to_ready_ms"] = round(ready_ms, 1)
    arm["ready_at"] = jst_now()
    arm["startup"] = extract_startup(read_text(err_path))
    if not ok_ready:
        arm["result"] = "READY_FAIL"
        arm["stop"] = stop_and_eof(proc)
        arm["gpu_after"] = nvidia_query()
        return arm

    # First GEN: first useful token ≈ first T line after GEN; full response = DONE.
    line_count_before_gen1 = len(read_text(out_path).splitlines())
    t_gen1 = time.perf_counter()
    send(proc, GEN_LINE)
    t_lines, first_t_ms = wait_marker(out_path, proc, "T ", line_count_before_gen1, gen_timeout)
    done1, done1_ms = wait_marker(out_path, proc, "DONE ", line_count_before_gen1, gen_timeout)
    arm["gen1"] = {
        "first_t_lines": t_lines[:3],
        "ready_to_first_t_ms": None if first_t_ms is None else round(first_t_ms, 1),
        "load_request_to_first_t_ms": (
            None
            if first_t_ms is None
            else round(ready_ms + first_t_ms, 1)
        ),
        "done_lines": done1[:3],
        "ready_to_first_done_ms": None if done1_ms is None else round(done1_ms, 1),
        "wall_gen_ms": round((time.perf_counter() - t_gen1) * 1000.0, 1),
    }

    # Second GEN: steady TTFT under same session.
    line_count_before_gen2 = len(read_text(out_path).splitlines())
    t_gen2 = time.perf_counter()
    send(proc, GEN_LINE)
    t2_lines, second_t_ms = wait_marker(out_path, proc, "T ", line_count_before_gen2, gen_timeout)
    done2, done2_ms = wait_marker(out_path, proc, "DONE ", line_count_before_gen2, gen_timeout)
    arm["gen2"] = {
        "first_t_lines": t2_lines[:3],
        "second_ttft_ms": None if second_t_ms is None else round(second_t_ms, 1),
        "done_lines": done2[:3],
        "ready_to_second_done_ms": None if done2_ms is None else round(done2_ms, 1),
        "wall_gen_ms": round((time.perf_counter() - t_gen2) * 1000.0, 1),
    }

    arm["stop"] = stop_and_eof(proc)
    # Give WDDM a moment to release dedicated memory before next arm.
    time.sleep(8.0)
    arm["gpu_after"] = nvidia_query()
    arm["ended_at"] = jst_now()
    arm["startup_after"] = extract_startup(read_text(err_path))
    arm["result"] = (
        "PASS"
        if arm["gen1"].get("ready_to_first_t_ms") is not None
        and arm["gen2"].get("second_ttft_ms") is not None
        and arm["stop"].get("exited")
        else "PARTIAL"
    )
    return arm


def main() -> int:
    stamp = datetime.now().strftime("%H-%M")
    out_dir = Path(__file__).resolve().parent / f"run-{stamp}-t04"
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = DEFAULT_EXE
    gguf = DEFAULT_GGUF
    report: dict = {
        "task": "T04",
        "kind": "observational_paired_warmup_cost_movement",
        "started_at": jst_now(),
        "hardware": {
            "gpu": "NVIDIA GeForce RTX 5060 Ti 16GB",
            "ram_nominal_gb": 32,
            "os": "Windows 11",
        },
        "contract": {
            "model": "Qwen3.6-35B-A3B-UD-Q4_K_XL",
            "max_context": 65536,
            "prefill": "auto",
            "mtp": 2,
            "expert_store": "mapped-pack",
            "kv": "FP32 engine default (not changed)",
            "arms": ["warmup_default", "no_warmup"],
        },
        "hermes_killed": False,
        "invented_speeds": False,
        "defaults_changed": False,
        "goal_complete": False,
        "adoption": "NOT_DECIDED — measurement only; do not change product defaults from one pair",
        "expect_sha256": EXPECTED_SHA256,
        "gpu_preflight": nvidia_query(),
        "arms": {},
    }
    (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not exe.is_file() or not gguf.is_file():
        report["result"] = "ABORT_MISSING_FILES"
        (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 2
    digest = sha256_file(exe).lower()
    report["exe_sha256"] = digest
    if digest != EXPECTED_SHA256:
        report["result"] = "ABORT_DIGEST"
        (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 3
    if report["gpu_preflight"]["vram_free_mib"] < 12000:
        report["result"] = "BLOCKED_VRAM"
        (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 4

    ready_timeout = int(os.environ.get("Q36_T04_READY_TIMEOUT_SEC", "2400"))
    gen_timeout = int(os.environ.get("Q36_T04_GEN_TIMEOUT_SEC", "900"))

    arm_a = run_arm(
        exe=exe,
        gguf=gguf,
        out_dir=out_dir,
        label="armA_warmup",
        no_warmup=False,
        ready_timeout=ready_timeout,
        gen_timeout=gen_timeout,
    )
    report["arms"]["armA_warmup"] = arm_a
    (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Re-check headroom before arm B; never kill Hermes.
    gap = nvidia_query()
    report["between_arms_gpu"] = gap
    if gap["vram_free_mib"] < 12000:
        report["result"] = "BLOCKED_VRAM_BEFORE_ARM_B"
        report["ended_at"] = jst_now()
        (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("BLOCKED before arm B — free VRAM low; Hermes untouched.", flush=True)
        return 4

    arm_b = run_arm(
        exe=exe,
        gguf=gguf,
        out_dir=out_dir,
        label="armB_no_warmup",
        no_warmup=True,
        ready_timeout=ready_timeout,
        gen_timeout=gen_timeout,
    )
    report["arms"]["armB_no_warmup"] = arm_b
    report["ended_at"] = jst_now()
    report["gpu_final"] = nvidia_query()

    a_ok = arm_a.get("result") == "PASS"
    b_ok = arm_b.get("result") == "PASS"
    report["result"] = "PAIR_RECORDED" if (a_ok and b_ok) else "PAIR_PARTIAL"
    # Honest delta fields only when both measured; never call this an adoption win.
    if a_ok and b_ok:
        def _delta(path_a, path_b):
            va = arm_a
            vb = arm_b
            for key in path_a:
                va = va.get(key) if isinstance(va, dict) else None
            for key in path_b:
                vb = vb.get(key) if isinstance(vb, dict) else None
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                return {
                    "armA_ms": va,
                    "armB_ms": vb,
                    "armB_minus_armA_ms": round(vb - va, 1),
                }
            return {"armA_ms": va, "armB_ms": vb, "armB_minus_armA_ms": None}

        report["paired_deltas_observational"] = {
            "load_request_to_ready_ms": _delta(["load_request_to_ready_ms"], ["load_request_to_ready_ms"]),
            "ready_to_first_t_ms": _delta(["gen1", "ready_to_first_t_ms"], ["gen1", "ready_to_first_t_ms"]),
            "load_request_to_first_t_ms": _delta(
                ["gen1", "load_request_to_first_t_ms"], ["gen1", "load_request_to_first_t_ms"]
            ),
            "second_ttft_ms": _delta(["gen2", "second_ttft_ms"], ["gen2", "second_ttft_ms"]),
            "note": (
                "Positive armB_minus_armA on ready_to_first_t with faster READY "
                "suggests warmup cost moved to first request — not a product win."
            ),
        }

    (out_dir / "t04-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"result": report["result"], "out_dir": str(out_dir)}, indent=2), flush=True)
    return 0 if report["result"] == "PAIR_RECORDED" else 5


if __name__ == "__main__":
    raise SystemExit(main())

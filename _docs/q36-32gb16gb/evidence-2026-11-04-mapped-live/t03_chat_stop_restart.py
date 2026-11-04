#!/usr/bin/env python3
"""T03: mapped-pack chat (GEN) → STOP → restart → READY again.

Owns stdin end-to-end (no separate babysitter). DESIGN #6: never kills Hermes.
Does not invent speeds. Does not mark the durable goal complete.
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
# Minimal Qwen-family chat-ish ids; quality is not the T03 claim — lifecycle is.
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


def wait_done(stdout_path: Path, proc: subprocess.Popen[str], timeout_s: int) -> list[str]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        lines = read_text(stdout_path).splitlines()
        done = [ln for ln in lines if ln.startswith("DONE ") or ln.startswith("ERR ")]
        if done:
            return done
        if proc.poll() is not None:
            return [ln for ln in read_text(stdout_path).splitlines() if ln.startswith(("DONE ", "ERR "))]
        time.sleep(1.0)
    return [ln for ln in read_text(stdout_path).splitlines() if ln.startswith(("DONE ", "ERR "))]


def launch(exe: Path, gguf: Path, out_dir: Path, label: str) -> tuple[subprocess.Popen[str], Path, Path]:
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
    # Keep file objects alive on the Popen for later close.
    proc._strata_so = so  # type: ignore[attr-defined]
    proc._strata_se = se  # type: ignore[attr-defined]
    (out_dir / f"{label}-pid.txt").write_text(str(proc.pid), encoding="ascii")
    (out_dir / f"{label}-argv.json").write_text(json.dumps(argv, indent=2), encoding="utf-8")
    return proc, stdout_path, stderr_path


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


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "run-21-05-t03"
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = DEFAULT_EXE
    gguf = DEFAULT_GGUF
    report: dict = {
        "started_at": jst_now(),
        "hermes_killed": False,
        "invented_speeds": False,
        "goal_complete": False,
        "expect_sha256": EXPECTED_SHA256,
        "gpu_preflight": nvidia_query(),
        "phases": {},
    }
    if not exe.is_file() or not gguf.is_file():
        report["result"] = "ABORT_MISSING_FILES"
        (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 2
    digest = sha256_file(exe).lower()
    report["exe_sha256"] = digest
    if digest != EXPECTED_SHA256:
        report["result"] = "ABORT_DIGEST"
        (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 3
    if report["gpu_preflight"]["vram_free_mib"] < 12000:
        report["result"] = "BLOCKED_VRAM"
        (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 4

    ready_timeout = int(os.environ.get("Q36_T03_READY_TIMEOUT_SEC", "2400"))
    gen_timeout = int(os.environ.get("Q36_T03_GEN_TIMEOUT_SEC", "600"))

    # --- launch 1: chat ---
    proc1, out1, err1 = launch(exe, gguf, out_dir, "launch1")
    print(f"launch1 pid={proc1.pid}", flush=True)
    ok1 = wait_ready(proc1, out1, ready_timeout)
    report["phases"]["launch1_ready"] = {
        "ok": ok1,
        "pid": proc1.pid,
        "gpu": nvidia_query(),
        "at": jst_now(),
    }
    if not ok1:
        report["result"] = "FAIL_LAUNCH1_READY"
        if proc1.poll() is None and proc1.stdin:
            try:
                send(proc1, "STOP")
                proc1.wait(timeout=120)
            except Exception:
                pass
        close_logs(proc1)
        (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 5

    send(proc1, GEN_LINE)
    report["phases"]["gen"] = {"line": GEN_LINE, "sent_at": jst_now()}
    done_lines = wait_done(out1, proc1, gen_timeout)
    report["phases"]["gen"]["done_or_err"] = done_lines
    report["phases"]["gen"]["gpu"] = nvidia_query()
    report["phases"]["gen"]["finished_at"] = jst_now()
    t_lines = [ln for ln in read_text(out1).splitlines() if ln.startswith("T ")]
    report["phases"]["gen"]["t_token_lines"] = len(t_lines)
    chat_ok = any(ln.startswith("DONE ") for ln in done_lines)
    report["phases"]["gen"]["ok"] = chat_ok

    # STOP ends the in-flight generation; serve stays resident until stdin EOF/QUIT.
    send(proc1, "STOP")
    report["phases"]["stop1"] = {"sent_at": jst_now(), "note": "STOP then stdin close for process exit"}
    try:
        if proc1.stdin is not None and not proc1.stdin.closed:
            proc1.stdin.close()
        rc1 = proc1.wait(timeout=300)
    except subprocess.TimeoutExpired:
        rc1 = None
    report["phases"]["stop1"]["exit_code"] = rc1
    report["phases"]["stop1"]["gpu_after"] = nvidia_query()
    report["phases"]["stop1"]["at"] = jst_now()
    close_logs(proc1)
    if proc1.poll() is None:
        report["result"] = "FAIL_STOP1_STILL_ALIVE"
        (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 6

    # Headroom recheck before restart (admission honesty).
    time.sleep(3.0)
    gpu2 = nvidia_query()
    report["phases"]["pre_restart_gpu"] = gpu2
    if gpu2["vram_free_mib"] < 12000:
        report["result"] = "BLOCKED_VRAM_BEFORE_RESTART"
        (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 4

    # --- launch 2: restart ---
    proc2, out2, err2 = launch(exe, gguf, out_dir, "launch2")
    print(f"launch2 pid={proc2.pid}", flush=True)
    ok2 = wait_ready(proc2, out2, ready_timeout)
    report["phases"]["launch2_ready"] = {
        "ok": ok2,
        "pid": proc2.pid,
        "gpu": nvidia_query(),
        "at": jst_now(),
        "pid_reused": proc2.pid == proc1.pid,
    }
    pin2 = [ln for ln in read_text(err2).splitlines() if re.search(r"pin pool", ln, re.I)]
    report["phases"]["launch2_ready"]["pin_pool_lines"] = pin2
    if ok2:
        send(proc2, "STOP")
        try:
            if proc2.stdin is not None and not proc2.stdin.closed:
                proc2.stdin.close()
            proc2.wait(timeout=180)
        except subprocess.TimeoutExpired:
            pass
    close_logs(proc2)

    report["finished_at"] = jst_now()
    report["result"] = (
        "PASS"
        if chat_ok and ok2 and report["phases"]["launch2_ready"]["pid_reused"] is False
        else "PARTIAL"
    )
    (out_dir / "t03-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"result": report["result"], "chat_ok": chat_ok, "restart_ready": ok2}, indent=2), flush=True)
    return 0 if report["result"] == "PASS" else 7


if __name__ == "__main__":
    raise SystemExit(main())

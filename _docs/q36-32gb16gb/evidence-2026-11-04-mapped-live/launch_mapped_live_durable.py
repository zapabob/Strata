#!/usr/bin/env python3
"""Durable mapped-pack live launcher for Q36 pin-pool evidence.

Does NOT kill Hermes or other inference (DESIGN #6).
Refuses to start when free VRAM is below the threshold.

Durability contract (fixes 18:14 silent mid-load abort):
- stdout/stderr go to OS files via Popen handle inheritance — NOT PIPE+threads.
  PIPE buffers fill if a tee thread dies or the parent exits; that can stall or
  abort the engine mid-load and drop Q36_STARTUP / pin-pool lines.
- stdin stays an open PIPE held by this babysitter until STOP / Ctrl+C / child exit.
  Closing stdin mid-load is treated as protocol EOF and must not happen by accident.
- Marker detection tails the log files; never depends on PowerShell async handlers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:  # optional; PowerShell CIM fallback used when missing
    psutil = None  # type: ignore[assignment]


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


def jst_now() -> str:
    # Fixed local stamp for evidence folders on this machine.
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


def list_llama_servers() -> list[dict]:
    if psutil is None:
        ps = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" | "
                    "Select-Object ProcessId,ExecutablePath,WorkingSetSize | ConvertTo-Json"
                ),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if ps.returncode != 0 or not ps.stdout.strip():
            return []
        data = json.loads(ps.stdout)
        if isinstance(data, dict):
            data = [data]
        return [
            {
                "pid": int(x["ProcessId"]),
                "path": x.get("ExecutablePath"),
                "ws_mb": round(int(x.get("WorkingSetSize") or 0) / (1024 * 1024), 1),
            }
            for x in data
        ]
    procs = []
    for p in psutil.process_iter(["pid", "name", "exe", "memory_info"]):
        if (p.info.get("name") or "").lower() == "llama-server.exe":
            mi = p.info.get("memory_info")
            procs.append(
                {
                    "pid": p.info["pid"],
                    "path": p.info.get("exe"),
                    "ws_mb": round((mi.rss if mi else 0) / (1024 * 1024), 1),
                }
            )
    return procs


def read_text_best_effort(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def collect_markers(stdout_text: str, stderr_text: str) -> dict:
    q36_lines = [ln for ln in stderr_text.splitlines() if Q36_STARTUP_RE.search(ln)]
    pin_lines = [ln for ln in stderr_text.splitlines() if PIN_POOL_RE.search(ln)]
    ready = bool(READY_RE.search(stdout_text))
    return {
        "ready": ready,
        "q36_startup_lines": q36_lines,
        "pin_pool_lines": pin_lines,
    }


def stdin_keepalive(proc: subprocess.Popen[str], stop_event: threading.Event, note_path: Path) -> None:
    """Hold stdin open; never write STOP unless stop_event is set for shutdown."""
    note_path.write_text(
        json.dumps(
            {
                "started_at": jst_now(),
                "pid": proc.pid,
                "mode": "hold_open_no_auto_stop",
                "hermes_killed": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    while not stop_event.wait(5.0):
        if proc.poll() is not None:
            break
        # Touch note so operators can see babysitter is alive; do not write to child stdin.
        try:
            note_path.write_text(
                json.dumps(
                    {
                        "heartbeat_at": jst_now(),
                        "pid": proc.pid,
                        "alive": proc.poll() is None,
                        "mode": "hold_open_no_auto_stop",
                        "hermes_killed": False,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass


def send_stop(proc: subprocess.Popen[str]) -> None:
    if proc.stdin is None:
        return
    try:
        proc.stdin.write("STOP\n")
        proc.stdin.flush()
    except (BrokenPipeError, OSError, ValueError):
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    ap.add_argument("--gguf", type=Path, default=DEFAULT_GGUF)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / f"run-{datetime.now().strftime('%H-%M')}",
    )
    ap.add_argument(
        "--min-free-mib",
        type=int,
        default=12000,
        help="Refuse launch below this free dedicated VRAM (honest headroom gate).",
    )
    ap.add_argument("--max-context", default="65536")
    ap.add_argument("--prefill", default="auto")
    ap.add_argument("--mtp", default="2")
    ap.add_argument(
        "--expect-sha256",
        default=EXPECTED_SHA256,
        help="Allowlisted unsigned digest; empty string skips check.",
    )
    ap.add_argument(
        "--ready-timeout-sec",
        type=int,
        default=1200,
        help="Seconds to wait for READY before recording timeout markers.",
    )
    ap.add_argument(
        "--abandon-on-timeout",
        action="store_true",
        help=(
            "If set, exit after ready-timeout even if child is still loading. "
            "Default is to KEEP babysitting (stdin + log handles) so mid-load "
            "abort from closed pipes cannot recur."
        ),
    )
    args = ap.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stderr_path = out_dir / "stderr.log"
    stdout_path = out_dir / "stdout.log"
    meta_path = out_dir / "launch-meta.json"
    markers_path = out_dir / "markers.json"
    stdin_note_path = out_dir / "stdin-keepalive.json"

    gpu = nvidia_query()
    hermes = list_llama_servers()
    meta: dict = {
        "started_at": jst_now(),
        "exe": str(args.exe),
        "gguf": str(args.gguf),
        "min_free_mib": args.min_free_mib,
        "gpu_preflight": gpu,
        "hermes_llama_servers": hermes,
        "hermes_killed": False,
        "design6": "never kill foreign inference",
        "invented_speeds": False,
        "goal_complete": False,
        "capture_mode": "os_file_redirect_stdout_stderr_plus_stdin_babysitter",
        "root_cause_fix": (
            "18:14 used async PIPE/tee that could drop logs and close stdin mid-load; "
            "this launcher writes logs via OS file handles and holds stdin open."
        ),
    }

    if not args.exe.is_file():
        meta["mapped_live"] = "ABORT"
        meta["reason"] = f"missing exe: {args.exe}"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(meta["reason"], file=sys.stderr)
        return 2
    if not args.gguf.is_file():
        meta["mapped_live"] = "ABORT"
        meta["reason"] = f"missing gguf: {args.gguf}"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(meta["reason"], file=sys.stderr)
        return 2

    digest = sha256_file(args.exe).lower()
    meta["exe_sha256"] = digest
    if args.expect_sha256 and digest != args.expect_sha256.lower():
        meta["mapped_live"] = "ABORT"
        meta["reason"] = (
            f"exe sha256 {digest} != expected allowlisted {args.expect_sha256.lower()}"
        )
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(meta["reason"], file=sys.stderr)
        return 3

    if gpu["vram_free_mib"] < args.min_free_mib:
        meta["mapped_live"] = "BLOCKED"
        meta["reason"] = (
            f"free VRAM {gpu['vram_free_mib']} MiB < min {args.min_free_mib}; "
            f"Hermes/other inference still present ({len(hermes)} llama-server). "
            "Not killing (DESIGN #6)."
        )
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(meta["reason"], file=sys.stderr)
        return 4

    argv = [
        str(args.exe),
        "--native",
        str(args.gguf),
        "--max-context",
        str(args.max_context),
        "--prefill",
        str(args.prefill),
        "--mtp",
        str(args.mtp),
        "--q36-expert-store",
        "mapped-pack",
        "--serve",
    ]
    meta["argv"] = argv
    meta["mapped_live"] = "RUNNING"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    env = os.environ.copy()
    env.setdefault("TMP", r"H:\Strata\tmp-q36-mapped-live")
    env.setdefault("TEMP", env["TMP"])
    Path(env["TMP"]).mkdir(parents=True, exist_ok=True)

    # OS-level file redirect: child writes survive parent thread death / GC.
    # Keep these handles open for the entire babysit lifetime.
    so = stdout_path.open("w", encoding="utf-8", newline="\n", buffering=1)
    se = stderr_path.open("w", encoding="utf-8", newline="\n", buffering=1)
    stop_event = threading.Event()
    keepalive_thread: threading.Thread | None = None
    proc: subprocess.Popen[str] | None = None

    try:
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
        (out_dir / "pid.txt").write_text(str(proc.pid), encoding="ascii")
        print(f"launched pid={proc.pid} capture=os_file_redirect", flush=True)

        assert proc.stdin is not None
        keepalive_thread = threading.Thread(
            target=stdin_keepalive,
            args=(proc, stop_event, stdin_note_path),
            name="stdin-keepalive",
            daemon=False,
        )
        keepalive_thread.start()

        ready = False
        deadline = time.time() + args.ready_timeout_sec
        timed_out = False

        while True:
            stdout_text = read_text_best_effort(stdout_path)
            stderr_text = read_text_best_effort(stderr_path)
            marks = collect_markers(stdout_text, stderr_text)
            if marks["ready"]:
                ready = True
                break
            if proc.poll() is not None:
                break
            if time.time() >= deadline:
                timed_out = True
                break
            time.sleep(2.0)
            # Encourage disk visibility of child writes on Windows.
            try:
                so.flush()
                se.flush()
            except OSError:
                pass

        stdout_text = read_text_best_effort(stdout_path)
        stderr_text = read_text_best_effort(stderr_path)
        marks = collect_markers(stdout_text, stderr_text)
        ready = bool(marks["ready"] or ready)

        markers = {
            "captured_at": jst_now(),
            "pid": proc.pid,
            "alive": proc.poll() is None,
            "exit_code": proc.poll(),
            "ready": ready,
            "timed_out": timed_out,
            "q36_startup_lines": marks["q36_startup_lines"],
            "pin_pool_lines": marks["pin_pool_lines"],
            "gpu_after": nvidia_query(),
            "hermes_killed": False,
            "capture_mode": meta["capture_mode"],
            "stdin_closed": False,
        }
        markers_path.write_text(json.dumps(markers, indent=2), encoding="utf-8")

        if ready:
            meta["mapped_live"] = "READY"
        elif proc.poll() is None:
            meta["mapped_live"] = "RUNNING_TIMEOUT" if timed_out else "RUNNING"
        else:
            meta["mapped_live"] = "EXITED"
        meta["markers"] = markers
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(json.dumps(markers, indent=2), flush=True)

        if ready:
            print(
                "READY — babysitting with stdin held open; Ctrl+C sends STOP.",
                flush=True,
            )
        elif proc.poll() is None and timed_out and not args.abandon_on_timeout:
            print(
                "not READY within timeout; KEEP babysitting (stdin+log handles open) "
                "to avoid mid-load pipe abort. Use --abandon-on-timeout to exit early.",
                flush=True,
            )
        elif proc.poll() is None and args.abandon_on_timeout:
            print(
                "not READY within timeout; abandon-on-timeout set — leaving child "
                "alive but parent will exit (stdin may close; prefer default babysit).",
                flush=True,
            )
            return 5
        else:
            print("child exited before READY; see stderr.log", flush=True)
            return 5

        try:
            while proc.poll() is None:
                time.sleep(5.0)
                # Periodic marker refresh while babysitting (pin-pool may arrive late).
                stdout_text = read_text_best_effort(stdout_path)
                stderr_text = read_text_best_effort(stderr_path)
                marks = collect_markers(stdout_text, stderr_text)
                markers.update(
                    {
                        "captured_at": jst_now(),
                        "alive": True,
                        "ready": marks["ready"] or ready,
                        "q36_startup_lines": marks["q36_startup_lines"],
                        "pin_pool_lines": marks["pin_pool_lines"],
                        "gpu_after": nvidia_query(),
                    }
                )
                markers_path.write_text(json.dumps(markers, indent=2), encoding="utf-8")
                if marks["ready"] and meta.get("mapped_live") != "READY":
                    ready = True
                    meta["mapped_live"] = "READY"
                    meta["markers"] = markers
                    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                    print("READY observed during babysit.", flush=True)
        except KeyboardInterrupt:
            print("Ctrl+C — sending STOP on stdin (Hermes untouched).", flush=True)
            send_stop(proc)
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                print("STOP wait timed out; child left as-is (not force-killed).", flush=True)

        return 0 if ready else 5
    finally:
        stop_event.set()
        if keepalive_thread is not None:
            keepalive_thread.join(timeout=2.0)
        # Close log handles only after babysit ends. Closing earlier can abort child writes.
        try:
            so.flush()
            se.flush()
        except OSError:
            pass
        so.close()
        se.close()
        if proc is not None and proc.stdin is not None and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())

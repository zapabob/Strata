#!/usr/bin/env python3
"""Durable mapped-pack live launcher for Q36 pin-pool evidence.

Does NOT kill Hermes or other inference (DESIGN #6).
Refuses to start when free VRAM is below the threshold.
Captures stderr/stdout to files and keeps stdin open for serve protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
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


def jst_now() -> str:
    # Fixed +09:00 stamp for evidence folders on this machine.
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
    try:
        import psutil  # optional
    except ImportError:
        # Fallback: tasklist parse is brittle; use WMIC/CIM via PowerShell.
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
        help="Seconds to wait for READY on stdout before giving up (process kept).",
    )
    args = ap.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stderr_path = out_dir / "stderr.log"
    stdout_path = out_dir / "stdout.log"
    meta_path = out_dir / "launch-meta.json"
    markers_path = out_dir / "markers.json"

    gpu = nvidia_query()
    hermes = list_llama_servers()
    meta = {
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

    # Line-buffered-ish capture: unbuffered Python wrapping; engine may still block-buffer stderr.
    env = os.environ.copy()
    env.setdefault("TMP", r"H:\Strata\tmp-q36-mapped-live")
    env.setdefault("TEMP", env["TMP"])
    Path(env["TMP"]).mkdir(parents=True, exist_ok=True)

    with stdout_path.open("w", encoding="utf-8", newline="\n") as so, stderr_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as se:
        # stderr unbuffered via child inheritance is best-effort; flush periodically by reading.
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=str(out_dir),
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        (out_dir / "pid.txt").write_text(str(proc.pid), encoding="ascii")
        print(f"launched pid={proc.pid}", flush=True)

        q36_lines: list[str] = []
        pin_lines: list[str] = []
        ready = False
        deadline = time.time() + args.ready_timeout_sec

        assert proc.stdout is not None and proc.stderr is not None and proc.stdin is not None

        # Non-blocking-ish drain via threads.
        import threading

        def pump(stream, sink, bucket: list[str] | None, patterns: list[re.Pattern[str]] | None):
            for line in iter(stream.readline, ""):
                sink.write(line)
                sink.flush()
                if bucket is not None and patterns is not None:
                    for pat in patterns:
                        if pat.search(line):
                            bucket.append(line.rstrip("\n"))
                            break

        t_out = threading.Thread(
            target=pump,
            args=(proc.stdout, so, None, None),
            daemon=True,
        )
        t_err = threading.Thread(
            target=pump,
            args=(
                proc.stderr,
                se,
                q36_lines,
                [
                    re.compile(r"Q36_STARTUP"),
                    re.compile(r"mapped-pack host pin pool", re.I),
                    re.compile(r"pageable", re.I),
                ],
            ),
            daemon=True,
        )
        # Separate pin collector: reuse q36_lines then split.
        t_out.start()
        t_err.start()

        while time.time() < deadline:
            if proc.poll() is not None:
                break
            # READY is on stdout serve protocol.
            # Also accept pin-pool evidence without READY if startup stages completed.
            text_stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
            text_stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
            if re.search(r"(?m)^READY\b", text_stdout):
                ready = True
                break
            if "mapped-pack host pin pool" in text_stderr and "Q36_STARTUP" in text_stderr:
                # Keep waiting for READY until timeout; markers already useful.
                pass
            time.sleep(2)

        pin_lines = [
            ln
            for ln in stderr_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if "mapped-pack host pin pool" in ln or "pin pool" in ln.lower()
        ]
        q36_lines = [
            ln
            for ln in stderr_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.startswith("Q36_STARTUP")
        ]

        markers = {
            "captured_at": jst_now(),
            "pid": proc.pid,
            "alive": proc.poll() is None,
            "exit_code": proc.poll(),
            "ready": ready,
            "q36_startup_lines": q36_lines,
            "pin_pool_lines": pin_lines,
            "gpu_after": nvidia_query(),
            "hermes_killed": False,
        }
        markers_path.write_text(json.dumps(markers, indent=2), encoding="utf-8")

        meta["mapped_live"] = "READY" if ready else ("RUNNING" if proc.poll() is None else "EXITED")
        meta["markers"] = markers
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        print(json.dumps(markers, indent=2), flush=True)

        # Leave process running with stdin open if READY (caller may chat via another attach).
        # This launcher exits but keeps child alive only if we intentionally detach.
        # For evidence integrity, if READY, send STOP after a short idle so T03 can be a separate scripted run.
        # Default: keep alive; user/agent continues with the held process.
        if ready:
            print("READY — leaving process running; stdin held until this script exits.", flush=True)
            print("Send STOP on stdin by terminating this launcher with Ctrl+C after tests.", flush=True)
            try:
                while proc.poll() is None:
                    time.sleep(5)
            except KeyboardInterrupt:
                try:
                    proc.stdin.write("STOP\n")
                    proc.stdin.flush()
                except Exception:
                    pass
                proc.wait(timeout=60)
        else:
            # If not ready and still alive, leave it for manual inspection but close our wait.
            print("not READY within timeout; process left as-is (not killed).", flush=True)

    return 0 if ready else 5


if __name__ == "__main__":
    raise SystemExit(main())

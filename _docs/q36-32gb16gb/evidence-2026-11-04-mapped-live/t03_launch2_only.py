#!/usr/bin/env python3
"""T03 launch2-only: restart READY after chat/stop already evidenced on launch1.

Merges into run-21-05-t03/t03-report.json. DESIGN #6: never kills Hermes.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Reuse helpers from the full T03 script.
from t03_chat_stop_restart import (  # type: ignore
    DEFAULT_EXE,
    DEFAULT_GGUF,
    EXPECTED_SHA256,
    close_logs,
    jst_now,
    launch,
    nvidia_query,
    read_text,
    send,
    sha256_file,
    wait_ready,
)


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "run-21-05-t03"
    report_path = out_dir / "t03-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    report.setdefault("hermes_killed", False)
    report.setdefault("invented_speeds", False)
    report.setdefault("goal_complete", False)
    report["launch2_only_started_at"] = jst_now()
    digest = sha256_file(DEFAULT_EXE).lower()
    if digest != EXPECTED_SHA256:
        report["result"] = "ABORT_DIGEST_LAUNCH2"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 3
    gpu = nvidia_query()
    report["phases"] = report.get("phases") or {}
    report["phases"]["pre_restart_gpu"] = gpu
    if gpu["vram_free_mib"] < 12000:
        report["result"] = "BLOCKED_VRAM_BEFORE_RESTART"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 4

    ready_timeout = int(os.environ.get("Q36_T03_READY_TIMEOUT_SEC", "2400"))
    proc2, out2, err2 = launch(DEFAULT_EXE, DEFAULT_GGUF, out_dir, "launch2")
    print(f"launch2 pid={proc2.pid}", flush=True)
    ok2 = wait_ready(proc2, out2, ready_timeout)
    pin2 = [ln for ln in read_text(err2).splitlines() if re.search(r"pin pool", ln, re.I)]
    report["phases"]["launch2_ready"] = {
        "ok": ok2,
        "pid": proc2.pid,
        "gpu": nvidia_query(),
        "at": jst_now(),
        "pid_reused": proc2.pid == (report.get("phases", {}).get("launch1_ready", {}) or {}).get("pid"),
        "pin_pool_lines": pin2,
    }
    if ok2:
        send(proc2, "STOP")
        try:
            if proc2.stdin is not None and not proc2.stdin.closed:
                proc2.stdin.close()
            proc2.wait(timeout=180)
        except subprocess.TimeoutExpired:
            report["phases"]["launch2_ready"]["stop"] = "TIMEOUT_LEFT_ALIVE"
    close_logs(proc2)
    report["finished_at"] = jst_now()
    chat_ok = bool((report.get("phases", {}).get("gen") or {}).get("ok"))
    report["result"] = (
        "PASS"
        if chat_ok and ok2 and report["phases"]["launch2_ready"]["pid_reused"] is False
        else "PARTIAL"
    )
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"result": report["result"], "restart_ready": ok2}, indent=2), flush=True)
    return 0 if report["result"] == "PASS" else 7


if __name__ == "__main__":
    raise SystemExit(main())

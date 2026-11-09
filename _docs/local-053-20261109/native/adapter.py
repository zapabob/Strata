"""Explicit parent-operated native phases. Default is a read-only plan, never execution."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from common import (BASE, BUILD, COMPONENT, HERE, NATIVE, PHASES, PYTHON, UV, configure,
                    environment, freeze, no_links, owned, read_json, require, save)
from common import require_current_job


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=("plan", "init", "run", "launch", "_worker"))
    result.add_argument("phase", nargs="?", choices=PHASES)
    result.add_argument("--source-root", required=True, type=Path)
    result.add_argument("--reviewed-commit", required=True)
    result.add_argument("--execute", action="store_true", help="Parent's explicit execution authorisation")
    result.add_argument("--seconds", type=int, default=5400, help="Whole-phase deadline, 1..5400 seconds")
    result.add_argument("--token", help=argparse.SUPPRESS)
    return result


def check_initialised(identity: dict) -> None:
    no_links(BASE)
    require(read_json(BASE / "freeze.json") == identity, "Frozen inputs/adapters changed since init")


def main() -> int:
    args = parser().parse_args()
    require(0 < args.seconds <= 5400, "Maximum phase deadline is 90 minutes")
    # Do not resolve away junctions before checking the supplied path.
    no_links(args.source_root)
    root = args.source_root.resolve()
    require(args.reviewed_commit and len(args.reviewed_commit) == 40, "Full reviewed commit required")
    if args.action == "plan":
        print(json.dumps({"execution": False, "sourceRoot": str(root), "reviewedCommit": args.reviewed_commit,
            "freezeChecked": False, "base": str(BASE), "native": str(NATIVE), "build": str(BUILD),
            "component": str(COMPONENT), "phases": PHASES, "configure": configure(root),
            "note": "No file writes or tool/model/build launches. init/run/launch require --execute and a clean 0.5.3 freeze."}, indent=2))
        return 0
    require(args.execute, "Execution is opt-in: parent must supply --execute after reviewed freeze")
    require(os.name == "nt" and Path(sys.executable).resolve() == PYTHON.resolve(), "Pinned Windows Python 3.12 required")
    identity = freeze(root, args.reviewed_commit)
    if args.action == "init":
        require(args.phase is None, "init has no phase")
        no_links(BASE)
        require(BASE.parent.is_dir() and not BASE.exists(), "Fresh BASE required; retain earlier outputs")
        BASE.mkdir()
        for name in ("native", "receipts", "results", "temp", "cache/uv", "cache/pip", "cache/cuda"):
            (BASE / name).mkdir(parents=True, exist_ok=True)
        save(BASE / "freeze.json", identity, fresh=True)
        print(json.dumps({"initialised": str(BASE), "freeze": identity}, indent=2))
        return 0
    require(args.phase, "Explicit single phase required; there is no automatic all/restart")
    check_initialised(identity)
    lock = BASE / "active.json"
    if args.action == "_worker":
        active = read_json(lock)
        require(active["token"] == args.token and active["phase"] == args.phase, "Worker ownership mismatch")
        require(os.environ.get("NATIVE_ADAPTER_WORKER_TOKEN") == args.token, "Worker must be launched by its owning controller")
        require_current_job(root)
        # This worker is created atomically inside the outer Job before any phase subprocess.
        from phases import dispatch
        dispatch(root, args.reviewed_commit, args.phase)
        require(freeze(root, args.reviewed_commit) == identity, "Frozen inputs changed during phase")
        return 0
    reservation = BASE / "receipts" / (args.phase + "-reservation.json")
    require(not reservation.exists(), "Phase already attempted; preserve failures, no automatic retries")
    token = uuid.uuid4().hex
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"token": token, "phase": args.phase, "created": time.time()}))
    try:
        save(reservation, {"phase": args.phase, "token": token, "deadlineSeconds": args.seconds}, fresh=True)
        if args.action == "launch":
            controller = BASE / "receipts" / (args.phase + "-controller.txt")
            command = [str(UV), "run", "--offline", "--no-config", "--no-project", "--no-managed-python",
                       "--python", str(PYTHON), "python", "-B", str(HERE / "adapter.py"),
                       "run", args.phase, "--source-root", str(root), "--reviewed-commit", args.reviewed_commit,
                       "--seconds", str(args.seconds), "--execute", "--token", token]
            with controller.open("x", encoding="utf-8") as output:
                process = subprocess.Popen(command, cwd=BASE, env=environment(), stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            save(BASE / "receipts" / (args.phase + "-launch.json"),
                 {"controllerPid": process.pid, "phase": args.phase, "command": command,
                  "controllerIsNotTheOwnedJob": True, "receipt": str(BASE / "receipts" / (args.phase + "-phase.json"))}, fresh=True)
            print(json.dumps({"controllerPid": process.pid, "receipt": str(BASE / "receipts" / (args.phase + "-phase.json"))}))
            return 0  # Controller now owns the reservation; completion releases the lock.
        return controller_run(args, root, token, identity)
    except BaseException:
        # Failed starts retain their reservation. Never guess whether a launched controller is dead.
        raise


def controller_run(args: argparse.Namespace, root: Path, token: str, identity: dict) -> int:
    command = [str(PYTHON), "-B", str(HERE / "adapter.py"), "_worker", args.phase,
               "--source-root", str(root), "--reviewed-commit", args.reviewed_commit,
               "--execute", "--token", token]
    env = environment()
    env["NATIVE_ADAPTER_WORKER_TOKEN"] = token
    report = owned(root, args.phase + "-phase", command, args.seconds, env=env, output_bytes=64 * 1024**2)
    report["frozenIdentity"] = identity
    save(BASE / "receipts" / (args.phase + "-phase.json"), report)
    run = report.get("run", {})
    if run.get("termination_confirmed") is True and run.get("job_active_after") == 0:
        lock = BASE / "active.json"
        require(read_json(lock)["token"] == token, "Lock ownership changed")
        lock.unlink()
    print(json.dumps(report), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    # A detached controller reuses exactly the launch reservation; a caller cannot reserve twice.
    try:
        if "--token" in sys.argv and "run" == sys.argv[1]:
            arguments = parser().parse_args()
            require(arguments.execute and arguments.phase and 0 < arguments.seconds <= 5400, "Invalid controller")
            require(os.name == "nt" and Path(sys.executable).resolve() == PYTHON.resolve(), "Pinned Windows Python required")
            no_links(arguments.source_root)
            root = arguments.source_root.resolve()
            identity = freeze(root, arguments.reviewed_commit)
            check_initialised(identity)
            active = read_json(BASE / "active.json")
            require(active["token"] == arguments.token and active["phase"] == arguments.phase, "Controller ownership mismatch")
            raise SystemExit(controller_run(arguments, root, arguments.token, identity))
        raise SystemExit(main())
    except Exception as error:
        print(f"BLOCKED/FAIL: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)

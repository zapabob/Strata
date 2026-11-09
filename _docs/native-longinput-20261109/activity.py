"""Read-only activity admission. Never stop, signal, or open a user engine for control."""

from __future__ import annotations

import math
import os
from pathlib import Path
import queue
import sys
import threading
from collections.abc import Callable

from contracts import require

ROOT = Path(__file__).resolve().parents[2]
ENGINE_NAMES = {"strata", "strata.exe", "strata-q36", "strata-q36.exe", "llama-server", "llama-server.exe"}


def read_snapshot() -> dict:
    """Enumerate engine identities and GET installed Host state; no cached PID exemptions."""
    import psutil

    sys.path.insert(0, str(ROOT / "_docs/local-install-20261106"))
    import installed_state

    root = psutil.Process(os.getpid())
    root_identity = (root.pid, root.create_time())
    engines, shell_count = [], 0
    for process in psutil.process_iter(["name"], ad_value=None):
        name = process.info["name"]
        require(isinstance(name, str) and bool(name), "process name telemetry unavailable")
        name = name.casefold()
        if name == "strata-desktop.exe":
            shell_count += 1
        if name not in ENGINE_NAMES:
            continue
        created = process.create_time()
        # The controller creates only its contained worker and bounded telemetry children.
        # In the worker, only its own descendants qualify. Names/paths alone never confer ownership.
        ancestors = process.parents()
        owned = any((p.pid, p.create_time()) == root_identity for p in ancestors)
        require(not owned or created >= root_identity[1], "process identity/ancestry race")
        engines.append(dict(pid=process.pid, created=created, owned=owned))
    shells = installed_state.shells()
    require(len(shells) == shell_count, "installed shell enumeration changed or incomplete")
    hosts = []
    for shell in shells:
        identity = (shell.pid, shell.create_time())
        base = installed_state.endpoint(shell)
        active = installed_state.get(base, "/api/chat/active")
        serving = installed_state.get(base, "/api/serving")
        require(isinstance(active, dict) and isinstance(active.get("turns"), list), "Host turns telemetry")
        require(isinstance(serving, dict) and isinstance(serving.get("stats"), dict), "Host serving telemetry")
        stats = serving["stats"]
        require(shell.is_running() and (shell.pid, shell.create_time()) == identity, "installed shell identity changed")
        hosts.append(dict(activeTurns=len(active["turns"]), runningRequests=stats.get("running"),
                          queuedRequests=stats.get("waiting")))
    return dict(engineProcesses=engines, hosts=hosts)


def bounded_snapshot() -> dict:
    """Bound the complete read-only helper, including its older 30s HTTP timeout, to 2s."""
    results: queue.Queue = queue.Queue(maxsize=1)

    def collect() -> None:
        try:
            results.put((True, read_snapshot()))
        except Exception as error:
            results.put((False, type(error).__name__))

    threading.Thread(target=collect, daemon=True).start()
    try:
        ok, value = results.get(timeout=2)
    except queue.Empty:
        raise TimeoutError("activity snapshot deadline") from None
    require(ok, "activity snapshot failed")
    return value


class ActivityGuard:
    """Fail closed on any external engine, active/queued Host turn, or unknown telemetry."""

    def __init__(self, reader: Callable[[], dict] = bounded_snapshot):
        self.reader = reader
        self.summary: dict = {}

    def preflight(self) -> dict:
        try:
            snapshot = self.reader()
            require(isinstance(snapshot, dict), "snapshot schema")
            engines, hosts = snapshot.get("engineProcesses"), snapshot.get("hosts")
            require(isinstance(engines, list) and isinstance(hosts, list), "snapshot lists")
            for engine in engines:
                require(isinstance(engine, dict) and type(engine.get("owned")) is bool, "ownership telemetry")
                require(type(engine.get("pid")) is int and engine["pid"] > 0, "engine PID telemetry")
                created = engine.get("created")
                require(type(created) in (int, float) and math.isfinite(created) and created > 0,
                        "engine creation telemetry")
                require(engine["owned"], "external engine")
            for host in hosts:
                require(isinstance(host, dict), "Host schema")
                for name in ("activeTurns", "runningRequests", "queuedRequests"):
                    count = host.get(name)
                    require(type(count) is int and count >= 0, "Host count telemetry")
                    require(count == 0, "Host activity")
            self.summary = dict(ownedEngines=len(engines), installedHosts=len(hosts), idle=True)
            return self.summary
        except Exception as error:
            # Endpoint URLs, chat IDs and other private state never enter the public error.
            raise ValueError("activity refused or telemetry unavailable (" + type(error).__name__ + ")") from None

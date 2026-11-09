"""Short actual r3-derived native protocol checks; model execution is always an explicit phase."""
from __future__ import annotations

import argparse
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from typing import Any

from common import (BASE, COMPONENT, GIB, HERE, PYTHON, admit, environment, freeze, load_helpers,
                    no_links, owned, read_json, require, save, sha)
from common import require_current_job

MODEL = Path("H:/Strata/models/qwen36-UD-Q4_K_XL/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf")
PACK = Path(str(MODEL) + ".q36epk")
TOKENIZER = Path("H:/Strata/models/packs/qwen36-ud-q4_k_xl/tokenizer")
PROMPT = "The capital of France is"


def protected_snapshot() -> dict[str, Any]:
    paths = [MODEL, PACK, Path(str(PACK) + ".verified"), Path(str(MODEL) + ".done")]
    require(TOKENIZER.is_dir(), "Existing tokenizer directory required")
    paths += sorted(p for p in TOKENIZER.rglob("*") if p.is_file())
    result = {}
    for path in paths:
        no_links(path)
        stat = path.stat()
        digest = sha(path)
        after = path.stat()
        require((stat.st_size, stat.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Protected input changed while hashing")
        result[str(path)] = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest}
    return result


def memory_receipt(lines: list[str], mode: str) -> dict[str, str]:
    ready = [i for i, line in enumerate(lines) if line.startswith("READY ")]
    receipts = [(i, line) for i, line in enumerate(lines) if line.startswith("INFO q36_memory_mode=")]
    require(len(ready) == len(receipts) == 1, "Exactly one actual memory INFO and READY required")
    index, line = receipts[0]
    require(index < ready[0], "Memory receipt must precede READY")
    fields = dict(part.split("=", 1) for part in line.split()[1:])
    require(len(fields) == len(line.split()) - 1 == 6, "Memory receipt duplicate/additional fields")
    require(fields.get("q36_memory_mode") == mode and fields.get("q36_memory_scope") == "expert-working-storage"
            and fields.get("q36_memory_total_process_bound") == "0", "Memory receipt contract changed")
    for name in ("cpu_stage", "h2d_stage", "io_scratch"):
        require(re.fullmatch(r"0|[1-9][0-9]*", fields.get("q36_memory_" + name + "_bytes", "")), "Invalid memory byte count")
    expected = {"bounded-experts-v1": ("18512896", "1048576"), "legacy": ("0", "0")}[mode]
    require(fields["q36_memory_h2d_stage_bytes"] == "67108864", "r3 H2D storage contract changed")
    require((fields["q36_memory_cpu_stage_bytes"], fields["q36_memory_io_scratch_bytes"]) == expected,
            "r3 CPU/IO storage contract changed; retain failure for parent review")
    return fields


def tokenizer(root: Path) -> Any:
    sys.path.insert(0, str(root / "tools"))
    from strata_tokenizer import Tokenizer
    vocab = read_json(TOKENIZER / "vocab.json")
    require(sorted(vocab.values()) == list(range(len(vocab))), "Tokenizer ids must be contiguous")
    tokens = [""] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    merges = (TOKENIZER / "merges.txt").read_text(encoding="utf-8").split("\n")
    if merges and merges[-1] == "":
        merges.pop()
    tk = Tokenizer(tokens, merges, read_json(TOKENIZER / "token_type.json"))
    embedded = Tokenizer.from_gguf(MODEL)
    require(tk.tokens == embedded.tokens and tk.ranks == embedded.ranks and tk.token_types == embedded.token_types,
            "Supplied tokenizer does not match existing GGUF metadata")
    ids = tk.encode(PROMPT)
    require(tk.decode(ids) == PROMPT and ids == embedded.encode(PROMPT) and 1 <= len(ids) < 128,
            "Prompt tokenizer round trip failed")
    return tk


def model(root: Path, phase: str) -> None:
    """Hash/protect inputs around a separately owned driver job, including cleanup."""
    require((BASE / "results/package.json").is_file(), "Native-only component must be staged")
    destination = BASE / "results" / (phase + ".json")
    require(not destination.exists(), "Fresh model phase result required")
    admit(root)
    before = protected_snapshot()
    save(BASE / "results" / (phase + "-inputs-before.json"), before, fresh=True)
    identity = read_json(BASE / "freeze.json")
    active = read_json(BASE / "active.json")
    driver_env = environment()
    driver_env["NATIVE_ADAPTER_DRIVER_TOKEN"] = active["token"]
    row = owned(root, phase + "-driver", [str(PYTHON), "-B", str(HERE / "model.py"), "_drive",
                "--source-root", str(root), "--reviewed-commit", identity["sourceCommit"],
                "--phase", phase, "--execute"], 1200, env=driver_env)
    # run_owned confirms/drains only the driver's own Job before post-run input checks.
    run = row.get("run", {})
    clean = run.get("termination_confirmed") is True and run.get("job_active_after") == 0
    result = {"passed": False, "driver": row, "sourceRoot": str(root),
              "modelFilesBefore": before, "ownedJobDrained": clean, "releaseQualified": False}
    if clean:
        after = protected_snapshot()
        result.update(modelFilesAfter=after, modelFilesPreserved=before == after)
        details = BASE / "results" / (phase + "-protocol.json")
        if details.is_file():
            result["protocol"] = read_json(details)
        result["passed"] = row["passed"] and before == after and result.get("protocol", {}).get("passed", False)
    save(destination, result, fresh=True)
    require(result["passed"], "Short native qualification FAIL; inspect driver/protocol/input evidence")


def drive(root: Path, phase: str) -> None:
    from phases import gpu_admit
    load_helpers(root)
    from perf131k.windows_job import process_memory_reader
    mode = "legacy" if phase == "model-legacy7" else "bounded-experts-v1"
    short = phase == "model-restart"
    path = BASE / "results" / (phase + "-protocol.json")
    require(not path.exists(), "Fresh protocol receipt required")
    args = ["--serve", "--native", str(MODEL), "--q36-expert-store", "mapped-pack", "--q36-memory", mode,
            "--max-context", "4096", "--prefill", "512", "--expert-slots", "5", "--mtp", "2",
            "--no-warmup", "--greedy", "--prompt-cache", "0", "--conversation-cache-mib", "0",
            "--private-conversation-cache", "--cache-type-k", "f32", "--cache-type-v", "f32"]
    result: dict[str, Any] = {"passed": False, "mode": mode, "capacity": 4096, "fullInputQuality": False,
            "inputText": PROMPT, "args": args, "requests": [], "info": [], "effective": [],
            "exeSHA256": sha(COMPONENT / "strata.exe"), "memorySamples": 0,
            "maxWorkingSetBytes": 0, "maxPrivateBytes": 0}
    save(path, result, fresh=True)
    gpu_admit(root, phase + "-gpu-admission", 14 * 1024)
    require(admit(root)["available_ram"] >= 8 * GIB, "Model startup needs 8 GiB free RAM")
    tk = tokenizer(root)
    ids = tk.encode(PROMPT)
    result.update(inputIds=ids, inputCount=len(ids))
    env = environment()
    env["PATH"] = str(COMPONENT) + ";" + env["PATH"]
    env.update(STRATA_Q36_PIN_PIPELINE="1", STRATA_Q36_STREAM_RESIDENT="1", STRATA_Q36_FILE_STAGING="1",
               STRATA_Q36_STARTUP_DETAIL="1", STRATA_Q36_STARTUP_GENERATION=phase)
    messages: queue.Queue = queue.Queue(maxsize=256)
    errors: list[str] = []
    begin = time.monotonic()
    query = process_memory_reader()
    last_sample = 0.0
    proc = None

    def reader(stream: Any, channel: str) -> None:
        try:
            with (BASE / "results" / (phase + "-" + channel + ".txt")).open("x", encoding="utf-8") as log:
                total = 0
                while True:
                    line = stream.readline(65537)
                    if not line:
                        break
                    size = len(line.encode("utf-8"))
                    require(size <= 65536 and total + size <= 8 * 1024**2, "Bounded native output exceeded")
                    total += size
                    log.write(line)
                    log.flush()
                    messages.put((channel, line.rstrip()), timeout=3)
                messages.put((channel, None), timeout=3)
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")

    def nextline(deadline: float) -> str:
        nonlocal last_sample
        while time.monotonic() < min(deadline, begin + 1100):
            now = time.monotonic()
            if now - last_sample >= .2:
                last_sample = now
                counters = query(int(proc._handle))
                require(counters["working_set_bytes"] is not None and counters["private_bytes"] is not None,
                        "Owned native memory measurement failed")
                result["memorySamples"] += 1
                result["maxWorkingSetBytes"] = max(result["maxWorkingSetBytes"], counters["working_set_bytes"])
                result["maxPrivateBytes"] = max(result["maxPrivateBytes"], counters["private_bytes"])
                sampled = admit(root)
                for key in ("available_ram", "commit_headroom"):
                    result["min_" + key] = min(result.get("min_" + key, sampled[key]), sampled[key])
            require(not errors, f"Native output reader failed: {errors}")
            try:
                channel, line = messages.get(timeout=.1)
            except queue.Empty:
                continue
            if line is None:
                require(channel != "stdout", "Native stdout closed, exit=" + str(proc.poll()))
                continue
            if channel == "stderr":
                if line.startswith(("Q36_EFFECTIVE ", "Q36_MEMORY_EFFECTIVE ", "Q36_PHYSICAL_MEMORY ")):
                    result["effective"].append(line)
                continue
            return line
        raise TimeoutError("Native protocol deadline")

    def request(name: str, prompt: list[int], scope: str | None, limit: int = 1,
                reuse: int = 0, cancel: bool = False) -> list[int]:
        start = time.monotonic()
        proc.stdin.write("GEN " + str(limit) + (" cache_scope=" + scope if scope else "")
                         + " " + ",".join(map(str, prompt)) + "\n")
        proc.stdin.flush()
        generated: list[int] = []
        progress = []
        stopped = False
        while True:
            line = nextline(start + 150)
            if line.startswith("T "):
                generated.append(int(line.split()[1]))
                require(len(generated) <= limit, "Native generated beyond requested token limit")
                if cancel and not stopped:
                    proc.stdin.write("STOP\n")  # Native request cancellation, never a user process stop.
                    proc.stdin.flush()
                    stopped = True
            elif line.startswith("PP "):
                progress.append(line)
            elif line.startswith("ERR "):
                raise RuntimeError(line)
            elif line.startswith("DONE "):
                break
        fields = line.split()
        require(len(fields) >= 15, "Incomplete DONE protocol")
        row = {"name": name, "submittedCount": len(prompt), "nativePromptCount": int(fields[2]),
               "nativeFreshReadCount": int(fields[14]), "nativeReuseCount": int(fields[8]),
               "generatedCount": int(fields[1]), "generatedIds": generated, "generatedText": tk.decode(generated),
               "finish": fields[5], "done": line, "progress": progress, "requestedMaxNew": limit,
               "seconds": time.monotonic() - start}
        result["requests"].append(row)
        save(path, result)
        require(row["nativePromptCount"] == len(prompt) and row["nativeReuseCount"] == reuse
                and row["nativeFreshReadCount"] + reuse == len(prompt), "Native prompt/reuse count mismatch")
        require(row["generatedCount"] == len(generated) and generated and row["generatedText"].strip(), "Invalid generation")
        require(row["finish"] == "cancel" if cancel else row["finish"] in ("length", "stop"), "Finish reason mismatch")
        return generated

    try:
        # This descendant inherits the driver's atomic no-breakaway Job. No PID searches or external process control.
        proc = subprocess.Popen([str(COMPONENT / "strata.exe"), *args], cwd=BASE, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)
        result["ownedPid"] = proc.pid
        threads = [threading.Thread(target=reader, args=(stream, channel), daemon=True)
                   for stream, channel in ((proc.stdout, "stdout"), (proc.stderr, "stderr"))]
        for thread in threads:
            thread.start()
        while True:
            line = nextline(begin + 360)
            if line.startswith("INFO "):
                result["info"].append(line)
            if line.startswith("READY "):
                result["ready"] = line
                break
        result["readySeconds"] = time.monotonic() - begin
        require(result["ready"] == "READY 4096 stop", "Unexpected READY capacity")
        require(any("q36_private_cache=2" in line for line in result["info"]), "Private-cache owner contract missing")
        require(any("kv_cache_k=f32 kv_cache_v=f32" in line for line in result["info"]), "KV contract missing")
        actual_lines = (BASE / "results" / (phase + "-stdout.txt")).read_text(encoding="utf-8").splitlines()
        result["memoryReceipt"] = memory_receipt(actual_lines, mode)
        first = request("first-owner-A", ids, "a" * 64)
        if not short:
            request("same-owner-A", ids + first, "a" * 64, reuse=len(ids))
            request("different-owner-B", ids, "b" * 64)
            request("missing-owner", ids, None)
            request("cancel-decode", ids, "a" * 64, limit=128, cancel=True)
            request("after-cancel-clears", ids, "a" * 64)
        request("short-generation", ids, "b" * 64, limit=8)
        proc.stdin.close()
        proc.wait(timeout=15)
        for thread in threads:
            thread.join(timeout=3)
        require(not errors and all(not thread.is_alive() for thread in threads), "Native readers not drained")
        require(proc.returncode == 0, "Native process exit failed")
        if mode == "bounded-experts-v1":
            # The log, not queue scheduling, is authoritative for final diagnostics.
            stderr = (BASE / "results" / (phase + "-stderr.txt")).read_text(encoding="utf-8")
            require("Q36_MEMORY_EFFECTIVE " in stderr, "Missing bounded effective-memory diagnostics")
        result["passed"] = True
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        result["exitCodeBeforeJobCleanup"] = proc.poll() if proc else None
        result["seconds"] = time.monotonic() - begin
        save(path, result)
        # On failure the driver exits; run_owned drains its Job, then the wrapper checks protected inputs.
    require(result["passed"], result.get("error", "Native qualification failed"))


def compare() -> None:
    a, b = (read_json(BASE / "results" / (name + ".json")) for name in ("model-bounded", "model-legacy7"))
    require(a["passed"] and b["passed"] and a["modelFilesAfter"] == b["modelFilesBefore"], "Fresh protected model runs required")
    left, right = a["protocol"], b["protocol"]
    require(left["exeSHA256"] == right["exeSHA256"] == sha(COMPONENT / "strata.exe"), "Comparison binary changed")
    require(left["inputIds"] == right["inputIds"] and len(left["requests"]) == len(right["requests"]), "Comparison input/case mismatch")
    fields = ("name", "nativePromptCount", "nativeFreshReadCount", "nativeReuseCount", "generatedCount", "generatedIds", "finish")
    comparisons = [{"case": x["name"], "sameLegacy": all(x[key] == y[key] for key in fields)}
                   for x, y in zip(left["requests"], right["requests"])]
    result = {"passed": bool(comparisons) and all(row["sameLegacy"] for row in comparisons), "cases": comparisons,
              "exeSHA256": left["exeSHA256"], "releaseQualified": False,
              "limits": "r3 request semantics, short prompts, fresh bounded vs legacy only; no speed/general quality claim"}
    restart_path = BASE / "results/model-restart.json"
    if restart_path.exists():
        restart = read_json(restart_path)
        require(restart["passed"], "Explicit restart phase failed")
        result["restartPassed"] = (restart["protocol"]["exeSHA256"] == left["exeSHA256"] and
            restart["protocol"]["requests"][0]["generatedIds"] == left["requests"][0]["generatedIds"] and
            restart["modelFilesBefore"] == a["modelFilesBefore"])
        result["passed"] &= result["restartPassed"]
    else:
        result["restart"] = "NOT_RUN (explicit phase only)"
    save(BASE / "results/comparison.json", result, fresh=True)
    require(result["passed"], "Fresh bounded/legacy comparison failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("_drive",))
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--reviewed-commit", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--phase", choices=("model-bounded", "model-legacy7", "model-restart"), required=True)
    args = parser.parse_args()
    # A direct driver launch is rejected unless the parent adapter's owned worker is active.
    active = read_json(BASE / "active.json")
    import os
    require(args.execute and active["phase"] == args.phase
            and os.environ.get("NATIVE_ADAPTER_DRIVER_TOKEN") == active["token"],
            "Driver requires explicit active owned model phase")
    require(freeze(args.source_root.resolve(), args.reviewed_commit) == read_json(BASE / "freeze.json"), "Driver freeze changed")
    require_current_job(args.source_root.resolve())
    drive(args.source_root, args.phase)

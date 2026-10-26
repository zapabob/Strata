"""Explicitly authorized H-only native serve pilot. No service/lease/port operations.

Uses the frozen B0 verification binary, spec4/MTP/k8v4/capacity131072. It is a
native-protocol series: HTTP/client delivery and full P17/PPL quality remain NOT_RUN.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import time
from types import SimpleNamespace

from tools.perf131k import windows_job
from tools.perf131k.pilot import system_resources

ROOT = Path(__file__).resolve().parents[2]
BASE = Path("H:/Strata/evidence/p01-b3-20261026")
TOKENIZER = Path("H:/Strata/packs/q2_0/tokenizer")
BINARY = Path("H:/Strata/build/p01-b0-20261025/bin/strata.exe")
BINARY_SHA = "4281dd8b886f4863fd85e71e35c4fe64c084c4cdb9ce1cd1029c5dbbed958610"
SENTINEL = "BOBNYAN_131072"


def sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write(path, obj):
    with path.open("x", encoding="utf-8") as out:
        json.dump(obj, out, indent=2, allow_nan=False)


def tokenizer():
    from tools.strata_tokenizer import Tokenizer
    vocab = json.loads((TOKENIZER / "vocab.json").read_text(encoding="utf-8"))
    tokens = [None] * len(vocab)
    for token, index in vocab.items():
        tokens[index] = token
    metadata = json.loads((TOKENIZER / "tokenizer.json").read_text())
    return Tokenizer(tokens, (TOKENIZER / "merges.txt").read_text(encoding="utf-8").split("\n"),
                     json.loads((TOKENIZER / "token_type.json").read_text()),
                     metadata["pre"], metadata["special_ids"])


def prepare():
    if ROOT.drive.upper() != "H:" or sha(BINARY) != BINARY_SHA:
        raise ValueError("H checkout and exact B0 verification binary required")
    destination = BASE / "prepared"
    destination.mkdir(exist_ok=False)
    tok = tokenizer()
    snapshot = json.loads((ROOT / "_docs/perf131k/model-inventory.json").read_text(encoding="utf-8-sig"))
    cfg = snapshot["saved_Q2_configuration"]
    args = list(cfg["args"])
    args[args.index("--max-context") + 1] = "131072"
    binding = {"binary": str(BINARY), "binary_sha256": BINARY_SHA, "native_args": args,
               "baseline_env": cfg["env"], "capacity": 131072, "output_reserve": 256,
               "series": "native-serve-normal-spec4-MTP", "input_method": "fixed GEN token IDs, not HTTP",
               "tokenizer": {p.name: sha(p) for p in TOKENIZER.iterdir() if p.is_file()},
               "expert_profile_sha256": sha(Path(args[args.index("--expert-profile") + 1])),
               "model_content_hash": None, "legacy_provenance": "UNRESOLVED", "fixtures": {}}
    prefix = ("<|im_start|>system\nFollow the user's recall instruction.\n<|im_end|>\n"
              "<|im_start|>user\nThe sentinel is " + SENTINEL + ". Remember it across the filler.\n")
    suffix = ("\nWhat was the sentinel? Reply with only the sentinel, without explanation."
              "<|im_end|>\n<|im_start|>assistant\n<think>\n")
    for target in (4096, 32768):
        repeat = target - len(tok.encode(prefix + suffix, parse_special=True))
        for _ in range(8):
            text = prefix + " filler" * repeat + suffix
            ids = tok.encode(text, parse_special=True)
            if len(ids) == target:
                break
            repeat += target - len(ids)
        if len(ids) != target or tok.decode(ids) != text:
            raise ValueError("exact fixture token count/round trip failed")
        write(destination / f"tokens-{target}.json", ids)
        binding["fixtures"][str(target)] = {"tokens": target,
            "sha256_int32le": hashlib.sha256(struct.pack(f"<{len(ids)}i", *ids)).hexdigest(),
            "file_sha256": sha(destination / f"tokens-{target}.json"), "expected_answer": SENTINEL}
    write(destination / "binding.json", binding)
    print(json.dumps({"prepared": str(destination), "binary_sha256": BINARY_SHA,
                      "input_counts": [4096, 32768], "model_launched": False}))


def verify_inputs(binding):
    expected = {"vocab.json", "merges.txt", "token_type.json", "tokenizer.json", "chat_template.jinja"}
    if set(binding["tokenizer"]) != expected:
        raise ValueError("unexpected tokenizer input set")
    observed = {name: sha(TOKENIZER / name) for name in expected}
    if observed != binding["tokenizer"]:
        raise ValueError("tokenizer identity changed")
    args = binding["native_args"]
    profile = Path(args[args.index("--expert-profile") + 1])
    observed["expert_profile"] = sha(profile)
    if observed["expert_profile"] != binding["expert_profile_sha256"]:
        raise ValueError("expert profile identity changed")
    return observed


def make_budget(job_commit_gib=8):
    # The10/16GiB arms are explicit, separately authorized diagnostics. Never infer
    # a larger limit from free resources or retry an exhausted Job automatically.
    if type(job_commit_gib) is not int or job_commit_gib not in (8, 10, 16):
        raise ValueError("only explicit8GiB/default,10GiB or16GiB pilot budgets are supported")
    return SimpleNamespace(timeout_s=900, job_commit_bytes=job_commit_gib * 1024**3,
                           output_bytes=16 * 1024**2, max_processes=2,
                           min_available_ram=2 * 1024**3, min_commit_headroom=6 * 1024**3,
                           min_H_free=8 * 1024**3)


def physical_ram_bytes():
    import ctypes
    from tools.perf131k.pilot import Memory
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError("physical RAM counter unavailable")
    return int(memory.total_phys)


def make_pc_budget(resources, total_ram):
    """Explicit PC-memory diagnostic policy; freeze once, never resize in flight.

    Job commit is not physical residency. Floors are sampled abort thresholds,
    not reserved memory. Existing commit_headroom is process-available commit
    (GlobalMemoryStatusEx.ullAvailPageFile), a conservative admission counter.
    """
    if type(total_ram) is not int or total_ram <= 0:
        raise ValueError("known positive total physical RAM required")
    if any(type(resources.get(key)) is not int or resources[key] < 0
           for key in ("available_ram", "commit_headroom", "H_free")):
        raise ValueError("known nonnegative resource counters required")
    unit = 64 * 1024**2
    ceiling = min(total_ram - 2 * 1024**3, resources["commit_headroom"] - 6 * 1024**3)
    ceiling = ceiling // unit * unit
    if ceiling <= 0:
        raise ValueError("no diagnostic commit budget remains after floors")
    budget = make_budget()
    budget.job_commit_bytes = ceiling
    budget.admission_mode = "pc_memory"
    budget.startup_min_available_ram = 8 * 1024**3
    budget.total_physical_ram_bytes = total_ram
    budget.planning_resources = dict(resources)
    return budget


def make_frozen_pc_budget(cap_bytes, total_ram):
    """Explicit, predeclared cap for comparable trials; never fit it to a trial."""
    unit = 64 * 1024**2
    if (type(cap_bytes) is not int or cap_bytes <= 0 or cap_bytes % unit
            or type(total_ram) is not int or cap_bytes > total_ram - 2 * 1024**3):
        raise ValueError("fixed PC cap must be aligned and within the measured physical-total policy")
    budget = make_budget()
    budget.job_commit_bytes = cap_bytes
    budget.admission_mode = "pc_memory"
    budget.startup_min_available_ram = 8 * 1024**3
    budget.total_physical_ram_bytes = total_ram
    budget.predeclared_fixed_cap = True
    return budget


def _run_cell(count, trace, *, binding_sha, result, budget, memory_diagnostics=False, blob_diagnostics=False):
    binding_path = BASE / "prepared/binding.json"
    binding_raw = binding_path.read_bytes()
    if hashlib.sha256(binding_raw).hexdigest() != binding_sha:
        raise ValueError("approved launch binding changed")
    binding = json.loads(binding_raw)
    if binding["binary_sha256"] != sha(BINARY):
        raise ValueError("verification binary changed")
    token_path = BASE / f"prepared/tokens-{count}.json"
    if sha(token_path) != binding["fixtures"][str(count)]["file_sha256"]:
        raise ValueError("token fixture changed")
    ids = json.loads(token_path.read_text())
    cell = BASE / f"native-{count}-{trace.lower()}"
    cell.mkdir(exist_ok=False)
    result["phase"] = "input_bindings"
    result["input_hashes_before"] = verify_inputs(binding)
    # One first request + one repeated request. Preserve cold/warm results separately;
    # this admission pilot is not the full3-pair baseline or a p95 estimate.
    line = "GEN 256 " + ",".join(map(str, ids)) + "\n"
    protocol = cell / "stdin.txt"
    protocol.write_text(line * 2 + "QUIT\n", encoding="ascii")
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    cuda = "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/x64"
    env.update(binding["baseline_env"], TEMP=str(cell), TMP=str(cell),
               PATH=cuda + os.pathsep + os.environ.get("PATH", ""),
               CUDA_CACHE_PATH=str(cell / "cuda-cache"), CUDA_CACHE_MAXSIZE=str(256 * 1024**2),
               STRATA_KEEP_LEFTOVERS="1")
    if trace == "ON":
        env["STRATA_PERF131K_HOST_TRACE"] = str(cell / "host-trace.json")
    diagnostic_keys = [key for key in env if key.upper() == "STRATA_PERF131K_BLOB_DIAG"]
    if len(diagnostic_keys) > 1:
        raise ValueError("duplicate case-insensitive blob diagnostic keys")
    if diagnostic_keys:
        env["STRATA_PERF131K_BLOB_DIAG"] = env.pop(diagnostic_keys[0])
    if blob_diagnostics:
        env["STRATA_PERF131K_BLOB_DIAG"] = "1"
    if env.get("STRATA_PERF131K_BLOB_DIAG", "0") not in ("0", "1"):
        raise ValueError("blob diagnostic binding must be explicit 0 or 1")
    result["source_blob_diagnostics"] = env.get("STRATA_PERF131K_BLOB_DIAG", "0") == "1"
    resources = system_resources(cell)
    pc_memory = getattr(budget, "admission_mode", None) == "pc_memory"
    ram_minimum = budget.startup_min_available_ram if pc_memory else budget.job_commit_bytes + budget.min_available_ram
    result["admission_policy"] = ("PC-memory fixed cap; start RAM >=8GiB; process-available commit >= cap+6GiB; runtime sampled RAM/commit floors 2/6GiB; no reservation/peak proof"
                                  if pc_memory else "start RAM >= Job commit +2GiB; commit headroom >= Job commit +6GiB; H free >=8GiB; no physical reservation/peak proof; WDDM budget unknown")
    if (resources["available_ram"] < ram_minimum
            or resources["commit_headroom"] < budget.job_commit_bytes + budget.min_commit_headroom
            or resources["H_free"] < budget.min_H_free):
        result.update(status="PREFLIGHT_BLOCKED", exit_code=77, resources=resources)
        return 77
    command = [str(BINARY), *binding["native_args"]]
    write(cell / "launch.json", {"command": command, "env": env, "budget": vars(budget),
                                 "binding_sha256": sha(binding_path), "resources": resources,
                                 "trace": trace, "input_count": count, "expected_capacity": 131072,
                                 "memory_diagnostics": memory_diagnostics,
                                 "source_blob_diagnostics": result["source_blob_diagnostics"]})
    started = time.monotonic()
    result["phase"] = "execution"
    result["launch_attempted"] = True
    diagnostics = {"memory_diagnostics": True} if memory_diagnostics else {}
    result.update(windows_job.run_owned(command, cell, env, cell / "raw.bin", budget, system_resources,
                                       stdin_path=protocol, **diagnostics))
    result["execution_status"], result["execution_exit_code"] = result["status"], result["exit_code"]
    result["phase"] = "analysis"
    result["elapsed_s"] = time.monotonic() - started
    result["raw_sha256"] = sha(cell / "raw.bin")
    result["capacity_required"] = 131072
    result["HTTP_client_metrics"] = "NOT_RUN"
    raw = (cell / "raw.bin").read_bytes().decode("utf-8", errors="replace")
    result["READY"] = [s for s in raw.splitlines() if s.startswith("READY ")]
    result["DONE"] = [s for s in raw.splitlines() if s.startswith("DONE ")]
    result["error_lines"] = [s for s in raw.splitlines() if s.startswith("ERR ") or "CUDA error" in s][:32]
    tok = tokenizer()
    records, generated = [], []
    for line in raw.splitlines():
        match = re.fullmatch(r"T (\d+)", line)
        if match:
            generated.append(int(match[1]))
        elif line.startswith("DONE "):
            parts = line.split()
            prompt_ms, decode_ms = float(parts[3]), float(parts[4])
            if not all(math.isfinite(value) and value >= 0 for value in (prompt_ms, decode_ms)):
                raise ValueError("nonfinite or negative native timing")
            text = tok.decode(generated)
            answer = text.split("</think>")[-1].replace("<|im_end|>", "").strip()
            records.append({"DONE": line, "actual_T_count": len(generated), "text": text,
                "recall_probe_pass": answer == SENTINEL,
                "engine_reported_prompt_ms": prompt_ms, "engine_reported_decode_ms": decode_ms,
                "engine_reported_generated": int(parts[1]), "engine_reported_prompt_tokens": int(parts[2]),
                "finish": parts[5], "reused_tokens": int(parts[8])})
            generated = []
    result["requests"] = records
    result["P17_PPL_full_quality"] = "NOT_RUN"
    result["trace_critical_path"] = None
    valid = (result["status"] == "FINISHED" and result["exit_code"] == 0
             and result["termination_confirmed"] and len(result["READY"]) == 1
             and result["READY"][0].split()[1] == "131072" and len(records) == 2
             and not result["error_lines"] and all(r["actual_T_count"] > 0 and r["actual_T_count"] == r["engine_reported_generated"]
             and r["engine_reported_prompt_tokens"] == count and r["finish"] in ("stop", "length") for r in records))
    result["measurement_valid"] = valid
    for index, record in enumerate(records):
        record["request_role"] = "first_request" if index == 0 else "repeated_request"
        ms = record["engine_reported_decode_ms"]
        record["engine_reported_tokens_per_second"] = record["actual_T_count"] * 1000 / ms if valid and ms > 0 else None
    return result["exit_code"] or (0 if valid else 78)


def run_cell(count, trace, *, binding_sha, job_commit_gib=8, memory_diagnostics=False, blob_diagnostics=False,
             use_pc_memory=False, frozen_pc_budget_bytes=None):
    if type(memory_diagnostics) is not bool:
        raise ValueError("memory diagnostics requires an explicit bool")
    if type(blob_diagnostics) is not bool:
        raise ValueError("blob diagnostics requires an explicit bool")
    if type(use_pc_memory) is not bool or (use_pc_memory and (type(job_commit_gib) is not int or job_commit_gib != 8)):
        raise ValueError("PC-memory mode requires an explicit bool and no fixed-budget override")
    if frozen_pc_budget_bytes is not None and (use_pc_memory or type(job_commit_gib) is not int or job_commit_gib != 8):
        raise ValueError("choose exactly one declared budget policy")
    if frozen_pc_budget_bytes is not None:
        budget = make_frozen_pc_budget(frozen_pc_budget_bytes, physical_ram_bytes())
    else:
        budget = (make_pc_budget(system_resources(BASE), physical_ram_bytes()) if use_pc_memory
                  else make_budget(job_commit_gib))
    cell = BASE / f"native-{count}-{trace.lower()}"
    if cell.exists():
        raise ValueError("refuse to overwrite a pilot cell")
    result = {"status": "PREFLIGHT_BLOCKED", "exit_code": 77, "phase": "input_bindings",
              "owned_root_pid": None, "termination_confirmed": None, "job_active_after": None,
              "measurement_valid": False, "comparison_valid": False, "requests": [],
              "launch_attempted": False, "GPU_elapsed_ns": None, "physical_IO_bytes": None,
              "P17_PPL_full_quality": "NOT_RUN", "requested_job_commit_gib": None if use_pc_memory or frozen_pc_budget_bytes is not None else job_commit_gib,
              "use_pc_memory": use_pc_memory, "frozen_job_commit_bytes": budget.job_commit_bytes,
              "source_blob_diagnostics": False, "requested_blob_diagnostics": blob_diagnostics}
    try:
        result["exit_code"] = _run_cell(count, trace, binding_sha=binding_sha, result=result, budget=budget,
                                        memory_diagnostics=memory_diagnostics, blob_diagnostics=blob_diagnostics)
        result["comparison_valid"] = (result["measurement_valid"] and not result["source_blob_diagnostics"]
                                      and not memory_diagnostics and not use_pc_memory)
        if result["exit_code"] and result["status"] == "FINISHED":
            result["status"] = "INVALID_MEASUREMENT"
    except Exception as error:
        kind = "INPUT_BINDING_FAILED" if result["phase"] == "input_bindings" else "ANALYSIS_FAILED"
        result.update(status=kind, exit_code=78, error_type=type(error).__name__, measurement_valid=False)
    finally:
        # Source checks and receipt preservation also apply to timeout/truncated output.
        try:
            raw_binding = (BASE / "prepared/binding.json").read_bytes()
            if hashlib.sha256(raw_binding).hexdigest() != binding_sha:
                raise ValueError("binding changed during cell")
            result["input_hashes_after"] = verify_inputs(json.loads(raw_binding))
        except Exception as error:
            result.update(status="INPUT_BINDING_FAILED", exit_code=78, error_type=type(error).__name__,
                          measurement_valid=False, comparison_valid=False)
        if trace == "ON":
            try:
                from tools.perf131k.capture_trace import analyze
                detail = analyze(cell / "host-trace.json")
                result["detail_trace"] = {key: detail[key] for key in ("trace_status", "counts", "record_count", "source")}
                complete = detail["trace_status"] == "COMPLETE_HOST_TRACE" and detail["record_count"] >= 2
                warning = b"host trace unavailable or incomplete" in (cell / "raw.bin").read_bytes()
                if not complete or warning:
                    raise ValueError("incomplete trace")
            except Exception as error:
                result["detail_trace_error"] = type(error).__name__
                result["comparison_valid"] = False
                if result["measurement_valid"]:
                    result.update(status="TRACE_INVALID", exit_code=78)
        if not result["comparison_valid"]:
            for record in result["requests"]:
                record["engine_reported_tokens_per_second"] = None
        cell.mkdir(exist_ok=True)
        raw = cell / "raw.bin"
        if raw.exists():
            try:
                result["raw_sha256"], result["raw_bytes"] = sha(raw), raw.stat().st_size
            except OSError:
                result["raw_sha256"], result["raw_bytes"] = None, None
        # A storage failure here remains an explicit exception, never a success receipt.
        write(cell / "result.json", result)
    print(json.dumps({"cell": str(cell), "status": result["status"], "exit_code": result["exit_code"],
                      "done_count": len(result["requests"]), "job_active_after": result["job_active_after"]}))
    return result["exit_code"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--execute-authorized", action="store_true")
    parser.add_argument("--tokens", type=int, choices=(4096, 32768))
    parser.add_argument("--trace", choices=("OFF", "ON"))
    parser.add_argument("--binding-sha")
    parser.add_argument("--job-commit-gib", type=int, choices=(8, 10, 16), default=8,
                        help="10/16 require explicit diagnostic budget authorization; never auto-increased")
    parser.add_argument("--memory-diagnostics", action="store_true",
                        help="opt-in owned root CPU memory sampled aggregates; no GPU counters")
    parser.add_argument("--blob-diagnostics", action="store_true",
                        help="opt-in native blob failure trace; excluded from performance comparisons")
    parser.add_argument("--use-pc-memory", action="store_true",
                        help="explicit maximum-PC diagnostic policy; freeze cap from measured resources, never auto-retry")
    parser.add_argument("--frozen-pc-budget-bytes", type=int,
                        help="predeclared aligned PC cap shared by comparable trials; never recalculated")
    args = parser.parse_args()
    if args.prepare and not args.execute_authorized:
        prepare()
        return 0
    if not args.execute_authorized or args.tokens is None or args.trace is None or args.binding_sha is None:
        parser.error("explicit authorized cell required")
    return run_cell(args.tokens, args.trace, binding_sha=args.binding_sha, job_commit_gib=args.job_commit_gib,
                    memory_diagnostics=args.memory_diagnostics, blob_diagnostics=args.blob_diagnostics,
                    use_pc_memory=args.use_pc_memory, frozen_pc_budget_bytes=args.frozen_pc_budget_bytes)


if __name__ == "__main__":
    raise SystemExit(main())

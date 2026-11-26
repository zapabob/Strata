"""Compare SC117 SQ-10 and Heretic Mode B NVFP4 through Strata's token protocol."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
from queue import Empty, Queue
import re
import shutil
import statistics
import subprocess
import tempfile
import threading
import time

from filelock import FileLock
from tokenizers import Tokenizer

from benchmark_apex import visible_and_reasoning
from benchmark_generation import competing_inference, digest, read, save
from benchmark_modeb_mathematics import apex_grader
from benchmark_modeb_nvfp4 import stamp
from phase7_controls import immutable
from sm120_native import MemoryPolicy, Nvml, available_memory


CONTEXT = 12288
ENGINE_OPTIONS = ("--max-context", str(CONTEXT), "--slots", "1", "--gpus", "1", "--chunk", "32",
                  "--kv", "k8v8", "--draft", "off", "--vram-experts-gb", "4.75", "--ram-experts-gb", "4",
                  "--vram-reserve-mib", "1536", "--cpu-threads", "6", "--no-anti-loop")
SC117_SHA256 = "876a4586eeff14a6d0bfbb567109a02abe2207c6e9659ff2592073bfe6790fac"
PLACEMENT = re.compile(r"Expert scratch: (\d+) GPU, (\d+) RAM, (\d+) SSD, (\d+) scratch bytes, direct=(\d), path=(.*)")


def engine_options(args):
    options = list(ENGINE_OPTIONS)
    if args.expert_cache_dir:
        options[options.index("--vram-experts-gb") + 1] = str(args.expert_vram_gib)
        options[options.index("--ram-experts-gb") + 1] = str(args.expert_ram_gib)
        options[options.index("--chunk") + 1] = str(args.prefill_chunk)
        options += ["--expert-cache-dir", str(args.expert_cache_dir.resolve())]
        if args.minimum_cold_mib:
            options += ["--expert-cache-min-mib", str(args.minimum_cold_mib)]
    return options


def freeze(args, tokenizer):
    gpqa = read(args.inputs / "model-card-suite/protocol.json")
    apex = read(args.inputs / "apex2025/protocol.json")
    timing = read(args.inputs / "protocol.json")
    gpqa_keys = [key for key in gpqa["order"] if gpqa["items"][key]["cohort"] == "gpqa"]
    apex_keys = [f"apex2025-{i}" for i in range(1, 13)]
    if (len(set(gpqa_keys)) != 198 or set(apex_keys) != set(apex["items"])
            or len(timing["speed_ids"]) != 512 or timing["speed_budget"] != 128):
        raise ValueError("Unexpected fixed GPQA, Apex or throughput inputs")
    items = {key: dict(ids=gpqa["items"][key]["ids"], budget=1, seed=gpqa["seed"], suite="gpqa") for key in gpqa_keys}
    for key in apex_keys:
        row = apex["items"][key]
        items[key] = dict(ids=row["ids"], budget=row["budget"], seed=apex["seed"], suite="apex")
    if any(len(item["ids"]) + item["budget"] >= CONTEXT for item in items.values()):
        raise ValueError("A fixed prompt or expected continuation would exceed the context")
    labels = [tokenizer.encode(letter, add_special_tokens=False).ids for letter in "ABCD"]
    if any(len(ids) != 1 or tokenizer.decode(ids, skip_special_tokens=False) != letter
           for letter, ids in zip("ABCD", labels)):
        raise ValueError("GPQA answer letters must each be a single raw token")
    protocol = dict(items=items, seed=timing["seed_chat"], temperature=0, engine_options=engine_options(args),
                    engine=digest(args.engine), tokenizer=digest(args.tokenizer),
                    gpqa_scoring="Greedy maximum over the four raw A/B/C/D token logits.",
                    gpqa_choice_ids=[ids[0] for ids in labels],
                    smoke_ids=timing["smoke_ids"], speed_ids=timing["speed_ids"],
                    speed_budget=timing["speed_budget"], speed_repeats=timing["speed_repeats"],
                    dataset=apex["dataset"], grader_revision=apex["grader_revision"], strict_parsing=False)
    immutable(args.out / "protocol.json", protocol)
    return protocol, gpqa_keys, apex_keys


def finish(tokens, fields, prompt_size, budget):
    count, prompt_n, prefill_ms, decode_ms, reason, accepted, offered, reused = fields
    if (int(count) != len(tokens) or int(prompt_n) != prompt_size or int(reused) != 0
            or int(accepted) or int(offered) or reason not in {"stop", "length"}
            or (reason == "length" and len(tokens) != budget)):
        raise ValueError("Native generation accounting, cache reuse or stop reason differs")
    return dict(output_ids=tokens, input_tokens=prompt_size, output_tokens=len(tokens),
                prefill_ms=float(prefill_ms), decode_ms=float(decode_ms),
                stop="eos" if reason == "stop" else "limit")


def report(folder, gpqa_keys, apex_keys):
    suites = {}
    for name, keys in (("gpqa", gpqa_keys), ("apex", apex_keys)):
        arms = {}
        for arm in ("sq10", "nvfp4"):
            answers = folder / arm / "answers"
            arms[arm] = {key: read(answers / (key + ".json")) for key in keys
                         if (answers / (key + ".json")).is_file()}
        common = arms["sq10"].keys() & arms["nvfp4"].keys()
        stats = {arm: dict(generated=len(rows), scorable=sum(r["scorable"] for r in rows.values()),
                           correct=sum(r["correct"] for r in rows.values()),
                           unscorable=sum(not r["scorable"] for r in rows.values()),
                           budget_exhausted_without_answer=sum(r["stop"] == "limit" and not r["scorable"] for r in rows.values()),
                           token_limit_stops=sum(r["stop"] == "limit" for r in rows.values()))
                 for arm, rows in arms.items()}
        outcomes = [(arms["sq10"][key]["correct"], arms["nvfp4"][key]["correct"]) for key in common]
        suites[name] = dict(requested=len(keys), paired=len(common), models=stats,
                            both_correct=outcomes.count((True, True)), sq10_only=outcomes.count((True, False)),
                            nvfp4_only=outcomes.count((False, True)), neither=outcomes.count((False, False)),
                            complete=all(len(rows) == len(keys) for rows in arms.values()))
    save(folder / "scores.json", suites)
    print(json.dumps(suites, indent=2), flush=True)


class NativeProtocol:
    def __init__(self, process, trace, check, require_ssd=False):
        self.process = process
        self.trace = trace
        self.check = check
        self.require_ssd = require_ssd
        self.ssd_read_bytes = 0
        self.lines = Queue()
        reader = threading.Thread(target=self.read_stdout, daemon=True)
        reader.start()

    def read_stdout(self):
        for line in self.process.stdout:
            self.lines.put(line.strip())
        self.lines.put(None)

    def send(self, command):
        self.trace.write("< " + command + "\n")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def receive(self, deadline):
        while time.monotonic() < deadline:
            self.check(self.process.pid)
            try:
                line = self.lines.get(timeout=1)
            except Empty:
                continue
            if line is None:
                raise RuntimeError(f"Strata process closed the protocol, exit={self.process.poll()}")
            self.trace.write("> " + line + "\n")
            if line.startswith("ERR "):
                raise RuntimeError(line)
            return line.split()
        raise TimeoutError("Timed out waiting for Strata's token protocol")

    def wait(self, prefix, seconds=420):
        deadline = time.monotonic() + seconds
        while True:
            fields = self.receive(deadline)
            if fields and fields[0] == prefix:
                return fields

    def read_ssd_bytes(self):
        self.send("STATS")
        metrics = dict(item.split("=", 1) for item in self.wait("STATS", 20)[1:])
        count = int(metrics["expert_ssd_bytes"])
        if int(metrics["expert_ssd_errors"]) != 0 or count < self.ssd_read_bytes:
            raise RuntimeError("Native generation reported an Expert scratch I/O error or counter reset")
        return count

    def generate(self, ids, count, seed, choices=()):
        self.send("BCO 0 0")
        if self.wait("BCOK", 20) != ["BCOK", "0", "1"]:
            raise RuntimeError("Could not reset Strata slot zero")
        allowed = "choices=" + ",".join(map(str, choices)) + " " if choices else ""
        self.send(f"GEN {count} temperature=0 seed={seed} penalty_repeat=1 ckpt=0 {allowed}" + ",".join(map(str, ids)))
        self.check(self.process.pid)
        tokens = []
        deadline = time.monotonic() + 600
        while True:
            fields = self.receive(deadline)
            if fields[:1] == ["T"]:
                tokens.append(int(fields[1]))
                deadline = time.monotonic() + 180
            elif fields[:1] == ["DONE"]:
                answer = finish(tokens, fields[1:], len(ids), count)
                if choices and (len(tokens) != 1 or tokens[0] not in choices):
                    raise RuntimeError("Native generation did not use the requested answer choices")
                if self.require_ssd:
                    read_bytes = self.read_ssd_bytes()
                    if read_bytes <= 0:
                        raise RuntimeError("Native generation lacks successful Expert scratch reads")
                    answer["expert_ssd_bytes"] = read_bytes - self.ssd_read_bytes
                    answer["expert_ssd_bytes_cumulative"] = read_bytes
                    self.ssd_read_bytes = read_bytes
                return answer


@contextmanager
def native(args, model, folder):
    folder.mkdir(parents=True)
    gpu = Nvml()
    policy = MemoryPolicy(physical_floor_bytes=3 * 2**30, commit_floor_bytes=4 * 2**30, physical_grace_seconds=0)
    command = [str(args.engine), "--serve", "--native", str(model), *engine_options(args)]
    baseline = None
    peak = 0
    reason = None
    placement = None
    engine_info = None
    load_seconds = None
    run_error = None
    cleanup_error = None
    last = float("-inf")
    last_owner_check = float("-inf")

    def check(pid=None):
        nonlocal last, last_owner_check, peak, reason, baseline
        now = time.monotonic()
        if now - last < 1:
            return
        last = now
        sample = dict(**available_memory(), **gpu.memory(), destination_free_bytes=shutil.disk_usage(folder).free,
                      system_free_bytes=shutil.disk_usage(Path(os.environ["SystemRoot"]).anchor).free)
        samples.write(json.dumps(sample) + "\n")
        baseline = sample["device_used_bytes"] if baseline is None else baseline
        peak = max(peak, sample["device_used_bytes"])
        reason = policy.observe(sample, now)
        if now - last_owner_check >= 5:
            last_owner_check = now
            if reason is None and competing_inference(pid):
                reason = "shared_gpu_pressure"
        if pid is None and reason is None and sample["device_free_bytes"] < 12000 * 2**20:
            reason = "insufficient_gpu_admission_headroom"
        if reason:
            raise RuntimeError(reason)

    lock = FileLock(str(Path(tempfile.gettempdir()) / "strata-inkling-benchmark-gpu0.lock"), timeout=60)
    with lock, (folder / "resources.jsonl").open("x", buffering=1, encoding="utf-8") as samples:
        proc = None
        try:
            check()
            env = dict(os.environ, STRATA_INK_TIER="0")
            with (folder / "engine.log").open("x", encoding="utf-8") as err, \
                    (folder / "protocol.log").open("x", buffering=1, encoding="utf-8") as trace:
                load_started = time.monotonic()
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, env=env,
                                        text=True, encoding="utf-8", errors="replace", bufsize=1,
                                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                peer = NativeProtocol(proc, trace, check, require_ssd=bool(args.expert_cache_dir))
                info = peer.wait("INFO", 1800 if args.expert_cache_dir else 420)
                if "backend=cuda" not in info and not any(k.startswith("backend=cuda-") for k in info):
                    raise RuntimeError("No native CUDA backend identity")
                engine_info = dict(field.split("=", 1) for field in info[1:] if "=" in field)
                if engine_info.get("kv_dtype") != "k8v8" or engine_info.get("drafting") != "off":
                    raise RuntimeError("Strata did not apply the common KV and drafting settings")
                ready = peer.wait("READY")
                if int(ready[1]) < CONTEXT:
                    raise RuntimeError("Strata reduced the requested context")
                load_seconds = time.monotonic() - load_started
                if args.expert_cache_dir:
                    engine_log = (folder / "engine.log").read_text(encoding="utf-8", errors="replace")
                    record = PLACEMENT.search(engine_log)
                    if not record:
                        raise RuntimeError("Strata did not report the requested Expert scratch tier")
                    gpu_count, ram_count, ssd_count, extent, direct, path = record.groups()
                    storage = Path(path.strip()).resolve()
                    if (not all(int(n) for n in (gpu_count, ram_count, ssd_count, extent, direct))
                            or storage.parent.parent != args.expert_cache_dir.resolve()
                            or storage.stat().st_size != int(extent)):
                        raise RuntimeError("The native placement differs from the GPU, RAM and SSD protocol")
                    placement = dict(gpu=int(gpu_count), ram=int(ram_count), ssd=int(ssd_count),
                                     scratch_bytes=int(extent), direct=bool(int(direct)), scratch_path=str(storage))
                    peer.ssd_read_bytes = peer.read_ssd_bytes()
                    placement["startup_ssd_read_bytes"] = peer.ssd_read_bytes
                yield peer
                peer.send("QUIT")
                if proc.wait(timeout=15):
                    raise RuntimeError("Strata exited with an error")
        except BaseException as exc:
            run_error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=15)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    cleanup_error = f"{type(exc).__name__}: {exc}"
            scratch_released = not Path(placement["scratch_path"]).exists() if placement else None
            save(folder / "measurement.json", dict(command=command, protection_event=reason, gpu=gpu.name,
                                                     baseline_device_used_bytes=baseline, peak_device_used_bytes=peak,
                                                     info=engine_info, load_seconds=load_seconds, placement=placement,
                                                     scratch_released=scratch_released, run_error=run_error,
                                                     cleanup_error=cleanup_error))
            if cleanup_error and run_error is None:
                raise RuntimeError(cleanup_error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "report", "probe", "smoke", "gpqa", "apex"))
    parser.add_argument("--arm", choices=("both", "sq10", "nvfp4"), default="both",
                        help="Run a single native diagnostic in smoke mode")
    for name in ("engine", "inputs", "out", "tokenizer", "sq10", "nvfp4", "matharena", "apex-key"):
        parser.add_argument("--" + name, type=Path, required=name in {"engine", "inputs", "out", "tokenizer"})
    parser.add_argument("--expert-cache-dir", type=Path, help="Existing temporary directory on the selected SSD")
    parser.add_argument("--expert-vram-gib", type=float, default=5.25)
    parser.add_argument("--expert-ram-gib", type=float, default=1.0)
    parser.add_argument("--minimum-cold-mib", type=int, default=0)
    parser.add_argument("--prefill-chunk", type=int, default=32)
    args = parser.parse_args()
    if args.expert_cache_dir and (not args.expert_cache_dir.is_dir()
                                  or not 0 < args.expert_ram_gib <= 12 or not 0 < args.expert_vram_gib <= 12
                                  or not 1 <= args.prefill_chunk <= 512 or not 0 <= args.minimum_cold_mib <= 32768):
        parser.error("Check the existing scratch directory, Expert budgets and prefill chunk")
    args.out.mkdir(parents=True, exist_ok=True)
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    protocol, gpqa_keys, apex_keys = freeze(args, tokenizer)
    if args.action == "prepare":
        print("Frozen 198 GPQA questions and 12 Apex problems", flush=True)
        return
    if args.action == "report":
        report(args.out, gpqa_keys, apex_keys)
        return
    if args.arm != "both" and args.action not in {"probe", "smoke"}:
        parser.error("The full benchmarks require both models")
    models = [(arm, model) for arm, model in (("sq10", args.sq10), ("nvfp4", args.nvfp4))
              if args.arm in ("both", arm)]
    if any(model is None for _, model in models) or (args.action == "apex" and not (args.matharena and args.apex_key)):
        parser.error("Supply the paired builds and, for Apex, the frozen key and official grader")
    if args.arm != "nvfp4" and (args.sq10.stat().st_size != 10471526400 or digest(args.sq10) != SC117_SHA256):
        raise ValueError("SC117 SQ-10 differs from the publisher's file")
    if args.arm != "sq10" and args.nvfp4.stat().st_size != read(args.nvfp4.with_suffix(".manifest.json"))["bytes"]:
        raise ValueError("Mode B NVFP4 differs from the local build receipt")
    if args.action in {"probe", "smoke"}:
        def smoke(peer, folder):
            reply = peer.generate(protocol["smoke_ids"], 16, protocol["seed"])
            reply["content"] = tokenizer.decode(reply["output_ids"], skip_special_tokens=True)
            if not reply["content"].strip():
                raise ValueError("No visible text in native smoke")
            evidence = dict(smoke=reply, trials=[], speed=None)
            save(folder / "generation.json", evidence)
            if args.action == "probe":
                return
            rows = evidence["trials"]
            for _ in range(protocol["speed_repeats"]):
                rows.append(peer.generate(protocol["speed_ids"], 128, protocol["seed"]))
                save(folder / "generation.json", evidence)
            if any(row["output_tokens"] != 128 or min(row["prefill_ms"], row["decode_ms"]) <= 0 for row in rows):
                raise ValueError("A fixed-length native speed trial did not complete")
            evidence["speed"] = dict(prefill_tps=statistics.median(512000 / row["prefill_ms"] for row in rows),
                                     decode_tps=statistics.median(1000 * (row["output_tokens"] - 1) / row["decode_ms"] for row in rows))
            save(folder / "generation.json", evidence)
        for arm, model in models:
            folder = args.out / arm / (args.action + "-" + stamp())
            with native(args, model, folder) as peer:
                smoke(peer, folder)
        return
    keys = gpqa_keys if args.action == "gpqa" else apex_keys
    gold = read(args.inputs / "model-card-suite/scoring-key.json") if args.action == "gpqa" else read(args.apex_key)
    grade = None if args.action == "gpqa" else apex_grader(args, protocol)
    for arm, model in models:
        answers = args.out / arm / "answers"
        answers.mkdir(parents=True, exist_ok=True)
        pending = [key for key in keys if not (answers / (key + ".json")).is_file()]
        if not pending:
            continue
        folder = args.out / arm / (args.action + "-" + stamp())
        with native(args, model, folder) as peer:
            for key in pending:
                item = protocol["items"][key]
                choices = protocol["gpqa_choice_ids"] if grade is None else ()
                reply = peer.generate(item["ids"], item["budget"], item["seed"], choices)
                if grade is None:
                    text = tokenizer.decode(reply["output_ids"], skip_special_tokens=True).strip()
                    reply.update(content=text, scorable=text in {"A", "B", "C", "D"}, correct=text == gold[key])
                else:
                    visible = visible_and_reasoning(reply["output_ids"], tokenizer, reply["stop"])["content"]
                    score = grade(visible.strip(), reply["output_tokens"], gold[key.removeprefix("apex2025-")])
                    reply.update(content=visible, scorable=score["extracted"] is not None, **score)
                save(answers / (key + ".json"), reply)
                print(arm, key, reply["output_tokens"], reply["stop"], flush=True)


if __name__ == "__main__":
    main()

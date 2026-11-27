"""Serial GPU measurements for Inkling expert promotion on one Windows PC."""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from filelock import FileLock

DEFAULT = (4, 16)
PROMPT_IDS = "200002,200004,34182,279,154554,150628,25,220,15,200010,200000,200004,40,150480,149882,150617,153048,13,153611,154845,30,200010,200001,200004"
RUNTIME_FLAGS = ("--native", "--gpus", "--slots", "--kv-dtype", "--chunk", "--draft",
                 "--vram-experts-gb", "--ram-experts-gb", "--cpu-threads",
                 "--expert-cache-dir", "--expert-cache-min-mib", "--vram-reserve-mib")
BENCH_RESULT = re.compile(r"prefill=([0-9.]+) ppts .*?decode=([0-9.]+) tps")
CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def gpu_memory():
    query = ["nvidia-smi", "--id=0", "--query-gpu=memory.total,memory.used", "--format=csv,noheader,nounits"]
    return tuple(map(int, subprocess.check_output(query, text=True, timeout=8, creationflags=CREATION_FLAGS).split(",")))


def runtime_args(profile):
    saved = json.loads(profile.read_text(encoding="utf-8-sig"))["args"]
    return [item for flag in RUNTIME_FLAGS if flag in saved for item in (flag, saved[saved.index(flag) + 1])]


def run(engine, args, settings, output, label, extra):
    rows, swaps = settings
    env = {**os.environ, "STRATA_INK_TIER_ROWS": str(rows), "STRATA_INK_TIER_SWAPS": str(swaps), "STRATA_INK_TIER_LOG": "1"}
    total, used = gpu_memory()
    if total - used < 11 * 1024:
        raise RuntimeError("The device has less than 11 GiB available before this experimental load.")
    peak = used
    start = time.monotonic()
    stdout, stderr = output / (label + ".stdout"), output / (label + ".stderr")
    with stdout.open("wb") as out, stderr.open("wb") as err:
        with subprocess.Popen([str(engine), *args, *extra], cwd=engine.parent, env=env, stdout=out, stderr=err, creationflags=CREATION_FLAGS) as child:
            try:
                while child.poll() is None:
                    _, used = gpu_memory()
                    peak = max(peak, used)
                    if time.monotonic() - start > 360:
                        raise TimeoutError("The experimental runtime exceeded 360 seconds.")
                    if total - used < 1024:
                        raise RuntimeError("The experimental runtime crossed the 1 GiB free-VRAM floor.")
                    time.sleep(1)
            finally:
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=15)
            if child.returncode:
                raise RuntimeError(f"{label} exited with {child.returncode}. See {stderr}.")
    text = stdout.read_text(encoding="utf-8", errors="replace")
    result = {"run": label, "rows": rows, "swaps": swaps, "peak_device_mib": peak,
              "wall_s": time.monotonic() - start}
    if "--bench" in extra:
        match = BENCH_RESULT.search(text)
        if not match:
            raise RuntimeError(f"No native benchmark summary in {stdout}.")
        result["prefill_tps"], result["decode_tps"] = map(float, match.groups())
    else:
        lines = [line for line in text.splitlines() if re.fullmatch(r"\d+(?:,\d+)*,?", line)]
        if not lines:
            raise RuntimeError(f"No generated token IDs in {stdout}.")
        result["generated_ids"] = list(map(int, lines[-1].rstrip(",").split(",")))
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--installed-engine", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    opt = parser.parse_args()
    opt.output.mkdir(parents=True, exist_ok=False)
    args = [*runtime_args(opt.profile), "--max-context", "16384"]
    results = []

    def measure(engine, settings, name, measurements):
        result = run(engine.resolve(), args, settings, opt.output, name, measurements)
        results.append(result)
        (opt.output / "samples.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        return result

    def bench(engine, settings, name, prompt):
        return measure(engine, settings, name, ["--bench", "--prompt-len", str(prompt), "--gen", "32"])

    with FileLock(Path(tempfile.gettempdir()) / "strata-inkling-benchmark-gpu0.lock", timeout=90):
        bench(opt.installed_engine, DEFAULT, "installed", 256)
        control = bench(opt.engine, DEFAULT, "calibration-default", 256)
        pool = [control, bench(opt.engine, (8, 16), "calibration-rows", 256),
                bench(opt.engine, (4, 8), "calibration-swaps", 256)]
        select = lambda trials: max((r for r in trials if r["prefill_tps"] >= 0.95 * control["prefill_tps"]),
                                    key=lambda result: result["decode_tps"])
        parent = select(pool)
        child = (parent["rows"] * 2, max(4, parent["swaps"] // 2))
        pool.append(bench(opt.engine, child, "calibration-mutation", 256))
        selection = select(pool)
        settings = selection["rows"], selection["swaps"]
        pairs = [(bench(opt.engine, DEFAULT, f"holdout-{i}-default", 1024),
                  bench(opt.engine, settings, f"holdout-{i}-selected", 1024)) for i in range(1, 3)]
        tokens = ["--prompt-ids", PROMPT_IDS, "--temp", "0", "--gen", "32"]
        base = measure(opt.engine, DEFAULT, "tokens-default", tokens)
        tuned = measure(opt.engine, settings, "tokens-selected", tokens)
    delta = [after["decode_tps"] / before["decode_tps"] - 1 for before, after in pairs]
    summary = {"selected": settings, "paired_decode_change": delta,
               "median_decode_change": statistics.median(delta),
               "greedy_ids_equal": base["generated_ids"] == tuned["generated_ids"],
               "greedy_tokens": len(base["generated_ids"])}
    (opt.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

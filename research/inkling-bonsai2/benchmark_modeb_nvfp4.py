"""Compare the two Heretic Mode B GGUFs on one GPU with frozen inputs and offload."""
import argparse
import ast
from datetime import datetime, timezone
from pathlib import Path
import re
import statistics
import time

import numpy as np
import psutil
from tokenizers import Tokenizer

from agentic_quality import lease
from benchmark_generation import complete, digest, local_server, read, save
from benchmark_inkling2 import aggregate, score
from phase7_controls import immutable, matrix
from phase13_acceptance_eval import VramPeakMonitor, chat_completion
from phase14_modeB_spec_eval import SPEC_PROMPTS
from sm120_native import run


CONTEXT = 4096
BATCH = 2048
MICROBATCH = 32
THREADS = 6
COLD_EXPERTS = r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps"
SERVER_FLAGS = ("-t", str(THREADS), "--load-mode", "none", "-fit", "off", "-fa", "on",
                "-ctk", "q8_0", "-ctv", "q8_0", "--jinja", "--spec-type", "none",
                "-ot", COLD_EXPERTS + "=CPU")
GENERATION_BUDGET = 128
REPEATS = 3


def freeze(args):
    corpus = read(args.root / "evaluation/phase7/protocol.json")
    items = {row["id"]: row for row in corpus["entries"]}
    heldout = {key: items[key]["ids"] for key in corpus["core"]}
    if [len(ids) - 1 for ids in heldout.values()] != [54, 16, 28, 23, 45, 46, 48]:
        raise ValueError("Different held-out prediction positions")
    maths = read(args.root / "evaluation/mmlu-sm120/selection.json")
    mmlu = maths["items"][:30]
    if len({row["row"] for row in mmlu}) != 30 or len(set(maths["label_token_ids"])) != 4:
        raise ValueError("Invalid frozen Mode B MMLU selection")

    tok = Tokenizer.from_file(str(args.root / "source/tokenizer.json"))
    warmup = "The capital of France is"
    intro = "Technical handbook notes. Use the following background when writing the next chapter.\n"
    body = ("The deployment keeps its weights on local storage. Each session records prompt tokens, "
            "allocated memory and generated tokens. The operators compare runs with equal cache settings.\n")
    ending = ("Write a detailed chapter for system operators explaining the entire workflow, "
              "including measurement, diagnostics, recovery and reporting.\n\nChapter One\n")
    prefix = tok.encode(intro, add_special_tokens=False).ids
    filler = tok.encode(body, add_special_tokens=False).ids
    suffix = tok.encode(ending, add_special_tokens=False).ids
    fill = 512 - len(prefix) - len(suffix)
    perf = prefix + (filler * (fill // len(filler) + 1))[:fill] + suffix
    if len(perf) != 512:
        raise ValueError("Incorrect fixed prefill size")
    spec = dict(context=CONTEXT, batch=BATCH, microbatch=MICROBATCH, cpu_threads=THREADS,
                kv="q8_0 for K and V", slots=1, cold_experts=COLD_EXPERTS, use_drafter=False,
                seed_chat=42, temperature=0, speed_repeats=REPEATS, speed_budget=GENERATION_BUDGET,
                smoke_text=warmup, smoke_ids=tok.encode(warmup, add_special_tokens=False).ids,
                speed_ids=perf, heldout=heldout, label_ids=maths["label_token_ids"], mmlu=mmlu,
                chat=SPEC_PROMPTS, server_digest=digest(args.server), logits_probe_digest=digest(args.logits))
    immutable(args.out / "protocol.json", spec)
    return spec


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def chat_result(key, body, seconds):
    choice = body["choices"][0]
    message = choice["message"]
    text = message.get("content") or ""
    calls = message.get("tool_calls") or []
    checks = {}
    if key == "tool_call_json":
        import json
        valid = False
        if len(calls) == 1:
            function = calls[0].get("function", {})
            arguments = function.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = None
            valid = function.get("name") == "inspect_vram_budget" and arguments == {
                "device_index": 0, "context_tokens": 139264, "kv_quant": "q8_0"
            }
        checks["exact_function_and_arguments"] = valid
    if key == "code_refactor_python":
        block = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
        try:
            code = ast.parse(block[1] if block else text)
            checks["python_syntax"] = any(isinstance(n, ast.FunctionDef) for n in code.body)
        except SyntaxError:
            checks["python_syntax"] = False
    return dict(content=text, reasoning=message.get("reasoning_content"), tool_calls=calls,
                finish_reason=choice["finish_reason"], usage=body.get("usage"), timings=body.get("timings"),
                elapsed_seconds=seconds, checks=checks)


def throughput(rows):
    eligible = [r for r in rows if r["output_tokens"] == GENERATION_BUDGET and r["stop"] == "limit"]
    return dict(total_trials=len(rows), trials_at_fixed_budget=len(eligible),
                actual_output_tokens=[r["output_tokens"] for r in rows],
                prefill_median_tps=statistics.median(r["timings"]["prompt_per_second"] for r in rows),
                decode_median_tps=statistics.median(r["timings"]["predicted_per_second"] for r in rows),
                fixed_budget_decode_median_tps=(statistics.median(r["timings"]["predicted_per_second"]
                                                                 for r in eligible) if eligible else None))


def generate(args, name, model, spec):
    folder = args.out / name
    folder.mkdir(exist_ok=True)
    result = folder / "generation.json"
    if result.exists():
        return read(result)
    attempt = folder / ("server-" + stamp())
    started = time.monotonic()
    with local_server(args.server, model, attempt, 1, CONTEXT, batch=BATCH, ubatch=MICROBATCH,
                      extra=SERVER_FLAGS, admission=12000) as url:
        load_seconds = time.monotonic() - started
        owned = [p for p in psutil.Process().children()
                 if p.name().casefold() == args.server.name.casefold()]
        if len(owned) != 1:
            raise RuntimeError("Cannot identify the owned benchmark server")
        monitor = VramPeakMonitor(owned[0].pid)
        monitor.start()
        try:
            warm = complete(url, spec["smoke_ids"], 16)
            if warm["output_tokens"] <= 0 or not warm["content"].strip():
                raise ValueError("Smoke request returned no visible tokens")
            save(attempt / "smoke.json", warm)
            trials = []
            for index in range(REPEATS):
                trial = complete(url, spec["speed_ids"], GENERATION_BUDGET)
                timings = trial["timings"]
                if timings.get("cache_n", 0) or timings["prompt_n"] != 512:
                    raise ValueError("The 512-token speed trial reused a cached prefix")
                trials.append(trial)
                save(attempt / f"speed-{index+1}.json", trial)
            task_results = {}
            for task in spec["chat"]:
                body, seconds = chat_completion(url, task["messages"], max_tokens=task["max_tokens"],
                                                tools=task.get("tools"), timeout_s=600)
                task_results[task["id"]] = chat_result(task["id"], body, seconds)
                save(attempt / (task["id"] + ".json"), task_results[task["id"]])
        finally:
            wddm = monitor.stop()
    result = dict(model=model.name, context=CONTEXT, load_seconds=load_seconds, smoke=warm,
                  speed=throughput(trials), trials=trials, chat=task_results, wddm=wddm,
                  device=read(attempt / "measurement.json"), receipt=str(attempt))
    save(folder / "generation.json", result)
    print(name, "measured generation:", result["speed"], flush=True)
    return result


def logits(args, name, model, spec):
    folder = args.out / name / "logits"
    folder.mkdir(parents=True, exist_ok=True)
    targets = [(key, "all", ids) for key, ids in spec["heldout"].items()]
    targets.extend((f"mmlu-{row['row']}", "last", row["tokens"]) for row in spec["mmlu"])
    completed_attempts = []
    for attempt in sorted(folder.glob("run-*"), reverse=True):
        receipt = attempt / "measurement.json"
        if receipt.exists():
            command = read(receipt)["command"]
            if command[:2] == [str(args.logits), str(model)]:
                completed_attempts.append((attempt, [tuple(command[i:i+3]) for i in range(2, len(command), 3)]))

    def promote(path, key, mode, ids):
        if not path.is_file():
            return False
        try:
            values = matrix(path, ids if mode == "all" else [0])
        except ValueError:
            return False
        valid = values.shape[1] == 200058 and np.isfinite(values).all()
        del values
        if valid:
            path.rename(folder / (key + ".logits"))
        return bool(valid)

    missing = []
    reused = 0
    for key, mode, ids in targets:
        tokens = folder / (key + ".i32")
        raw = np.asarray(ids, dtype="<i4").tobytes()
        if not tokens.exists():
            tokens.write_bytes(raw)
        if tokens.read_bytes() != raw:
            raise ValueError("Unexpected input IDs for " + key)
        if (folder / (key + ".logits")).exists():
            continue
        for attempt, commands in completed_attempts:
            output = attempt / (key + ".logits")
            if (mode, str(tokens), str(output)) in commands and promote(output, key, mode, ids):
                reused += 1
                break
        else:
            missing.append((key, mode, ids, tokens))
    if reused:
        print(name, "reused", reused, "verified logit files from earlier runs; pending", len(missing), flush=True)
    if missing:
        attempt = folder / ("run-" + stamp())
        cmd = [str(args.logits), str(model)]
        for key, mode, _, tokens in missing:
            cmd.extend([mode, str(tokens), str(attempt / (key + ".logits"))])
        with lease().acquire(poll_interval=.025):
            run(attempt, cmd, 12000, 1800, 3600)
        for key, mode, ids, _ in missing:
            if not promote(attempt / (key + ".logits"), key, mode, ids):
                raise ValueError("Invalid logit artifact for " + key)
    return folder


def score_mmlu(arms, spec):
    rows = []
    for item in spec["mmlu"]:
        entry = dict(row=item["row"], answer=item["answer"])
        for name, folder in arms.items():
            values = matrix(folder / f"mmlu-{item['row']}.logits", [0])[0, spec["label_ids"]]
            pred = int(np.argmax(values))
            entry[name] = dict(prediction=pred, correct=pred == item["answer"], logits=values.tolist())
        rows.append(entry)
    counts = {name: sum(row[name]["correct"] for row in rows) for name in arms}
    return dict(items=len(rows), correct=counts,
                old_only=sum(row["old"]["correct"] and not row["nvfp4"]["correct"] for row in rows),
                nvfp4_only=sum(row["nvfp4"]["correct"] and not row["old"]["correct"] for row in rows), rows=rows)


def score_text(args, arms, spec):
    rows = {}
    for key, ids in spec["heldout"].items():
        old = matrix(arms["old"] / (key + ".logits"), ids)
        new = matrix(arms["nvfp4"] / (key + ".logits"), ids)
        rows[key] = score(old, new, ids)
    result = dict(old_to_nvfp4=aggregate(rows), japanese_139=aggregate(
        {key: row for key, row in rows.items() if key.startswith("japanese-prose")}))
    available = [*args.root.glob("evaluation/phase7/ablated/core/reference/holdout-*.npz"),
                 *args.root.glob("evaluation/ablated-bf16-heldout/holdout-*.npz")]
    compared = {name: {} for name in arms}
    keys = {tuple(ids): key for key, ids in spec["heldout"].items()}
    for file in sorted(available):
        with np.load(file) as z:
            ids = z["input_ids"][0].tolist()
            key = keys.get(tuple(ids))
            if key is None or key in compared["old"]:
                continue
            for name, folder in arms.items():
                compared[name][key] = score(z["logits"], matrix(folder / (key + ".logits"), ids), ids)
    if compared["old"]:
        result["heretic_bf16_to_each"] = {name: aggregate(rows) for name, rows in compared.items()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("root", "old", "new", "server", "logits", "out"):
        parser.add_argument("--"+flag, required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    models = {"old": args.old, "nvfp4": args.new}
    for name, model in models.items():
        manifest = model.with_suffix(".manifest.json")
        if read(manifest)["bytes"] != model.stat().st_size:
            raise ValueError("GGUF extent differs from its verified build")
        immutable(args.out / (name + "-identity.json"), dict(path=str(model), manifest=digest(manifest)))
    spec = freeze(args)
    generation = {name: generate(args, name, model, spec) for name, model in models.items()}
    save(args.out / "generation-results.json", generation)
    arms = {name: logits(args, name, model, spec) for name, model in models.items()}
    result = dict(generation=generation, text=score_text(args, arms, spec), maths=score_mmlu(arms, spec))
    save(args.out / "matched-results.json", result)
    print("Completed four matched measurements. MMLU scores:", result["maths"]["correct"], flush=True)


if __name__ == "__main__":
    main()

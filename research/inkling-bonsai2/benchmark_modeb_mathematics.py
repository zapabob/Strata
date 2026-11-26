"""Evaluate paired free-generation mathematics on the two frozen Mode B variants."""
import argparse
from collections import Counter
from pathlib import Path
import statistics
import subprocess
import time

import requests
from tokenizers import Tokenizer

from benchmark_apex import visible_and_reasoning
from benchmark_generation import GSM, MATH, complete, digest, local_server, read, save
from benchmark_modeb_nvfp4 import BATCH, MICROBATCH, SERVER_FLAGS, stamp
from grade_generation import Grader, wilson
from modeb_apex_state import CHUNK_TOKENS, checkpointed_completion, discard_completed_checkpoint
from phase7_controls import immutable
from termination_survival import parse_integer


def freeze(args):
    base = args.root / "evaluation"
    if args.suite == "apex":
        path = base / "apex2025/protocol.json"
        config = read(path)
        if list(sorted(map(int, config["items"]))) != list(range(1, 13)) or config["strict_parsing"]:
            raise ValueError("The official twelve-item Apex protocol differs")
        items = {f"apex2025-{key}": dict(ids=config["items"][key], suite="apex2025",
                 budget=config["output_budget"], key=key) for key in sorted(config["items"], key=int)}
        protocol = dict(items=items, dataset_digest=digest(path), dataset=config["dataset"],
                        context=12288, seed=config["seed"], temperature=config["temperature"],
                        reasoning_effort=config["reasoning_effort"], strict_parsing=False,
                        grader_revision=config["grader_revision"])
    else:
        gen_file = base / "generative-maths/protocol.json"
        aime_file = base / "aime2025/protocol.json"
        gen, aime = read(gen_file), read(aime_file)
        gsm_ids = [key for key in gen["pilot"] if gen["items"][key]["suite"] == GSM][:12]
        math_ids = []
        for level in range(1, 6):
            selected = [key for key in gen["pilot"] if gen["items"][key]["suite"] == MATH
                        and int(gen["items"][key]["level"]) == level][:2]
            math_ids.extend(selected)
        aime_ids = [f"aime25-{n:02d}" for n in (0, 7, 14, 15, 22, 29)]
        items = {}
        for key in (*gsm_ids, *math_ids, *aime_ids):
            source = aime if key in aime_ids else gen
            row = source["items"][key]
            kind = row["suite"]
            items[key] = dict(ids=row["tokens"], suite=kind, budget=source["generation_limits"][kind], key=key)
        if Counter(a["suite"] for a in items.values()) != Counter({GSM: 12, MATH: 10, "aime25": 6}):
            raise ValueError("The pilot benchmark denominators differ")
        protocol = dict(items=items, dataset_digests={p.parent.name: digest(p) for p in (gen_file, aime_file)},
                        context=5120, seed=gen["seed"], temperature=0,
                        reasoning_effort="none", original_templates=True)
    if any(len(item["ids"]) + item["budget"] > protocol["context"] for item in protocol["items"].values()):
        raise ValueError("The requested output could exceed the context")
    protocol["server"] = digest(args.server)
    protocol["shared_flags"] = list(SERVER_FLAGS)
    immutable(args.out / "protocol.json", protocol)
    return protocol


def apex_completion(url, ids, limit, seed, cache_prompt=False):
    beg = time.monotonic()
    response = requests.post(url + "/completion", json=dict(prompt=ids, temperature=0, seed=seed,
                            n_predict=limit, return_tokens=True, special=True, repeat_penalty=1.0,
                            cache_prompt=cache_prompt, stream=False), timeout=(15, 5400))
    response.raise_for_status()
    data = response.json()
    if (data.get("truncated") or data["tokens_evaluated"] != len(ids)
            or data["stop_type"] not in ("eos", "limit") or not isinstance(data.get("tokens"), list)):
        raise ValueError("Apex token accounting failed")
    return dict(output_ids=data["tokens"], input_tokens=len(ids), output_tokens=data["tokens_predicted"],
                elapsed_seconds=time.monotonic()-beg, stop=data["stop_type"], timings=data["timings"])


def generate(args, spec, name, model, selection=None):
    manifest = model.with_suffix(".manifest.json")
    if model.stat().st_size != read(manifest)["bytes"]:
        raise ValueError("Unexpected GGUF file length")
    dest = args.out / name
    answers = dest / "answers"
    answers.mkdir(parents=True, exist_ok=True)
    immutable(dest / "identity.json", dict(model=str(model), manifest=digest(manifest), protocol=digest(args.out/"protocol.json")))
    pending = [key for key in spec["items"] if not (answers / (key + ".json")).exists()]
    if selection is not None:
        pending = [key for key in pending if key in selection]
    if not pending:
        return
    tokenizer = Tokenizer.from_file(str(args.root / "source/tokenizer.json"))
    flags = SERVER_FLAGS
    slot_dir = None
    if args.checkpoint_root:
        proof = read(args.checkpoint_proof)[name]
        if not proof["token_for_token_equal"] or proof["model"] != model.name:
            raise ValueError("This model has no verified slot-continuation control")
        control = read(Path(proof["receipt"]) / "before/measurement.json")
        if control["cmd"][:3] != [str(args.server), "-m", str(model)]:
            raise ValueError("The checkpoint control ran with a different server or model")
        bytes_per_token = proof["saved"]["n_written"] / proof["saved"]["n_saved"]
        slot_dir = args.checkpoint_root / name
        slot_dir.mkdir(parents=True, exist_ok=True)
        flags = (*flags, "--slot-save-path", str(slot_dir))

    def progress():
        return sum((answers / (key + ".json")).exists() * spec["items"][key]["budget"]
                   + (len(read(dest / (key + ".slot.json"))["output_ids"])
                      if slot_dir and (dest / (key + ".slot.json")).exists() else 0)
                   for key in pending)

    stalls = 0
    while any(not (answers / (key + ".json")).exists() for key in pending):
        attempt = dest / ("server-" + stamp())
        before = progress()
        try:
            with local_server(args.server, model, attempt, 1, spec["context"], batch=BATCH,
                              ubatch=MICROBATCH, extra=flags, exclusive_gpu=True) as url:
                for key in pending:
                    result = answers / (key + ".json")
                    if result.exists():
                        continue
                    row = spec["items"][key]
                    ledger = dest / (key + ".slot.json")
                    if slot_dir:
                        outcome = checkpointed_completion(url, row, spec["seed"], key, slot_dir,
                                                          ledger, bytes_per_token, apex_completion,
                                                          start_tokens=args.checkpoint_start_tokens)
                    elif args.suite == "apex":
                        outcome = apex_completion(url, row["ids"], row["budget"], spec["seed"])
                    else:
                        outcome = complete(url, row["ids"], row["budget"])
                    channels = visible_and_reasoning(outcome["output_ids"], tokenizer, outcome["stop"])
                    outcome["content"] = channels["content"]
                    outcome.update(item=key, reasoning_characters=len(channels["reasoning"]))
                    save(result, outcome)
                    if slot_dir:
                        discard_completed_checkpoint(slot_dir, key, ledger)
                    print(name, key, outcome["output_tokens"], outcome["stop"], flush=True)
        except (RuntimeError, requests.RequestException):
            receipt = attempt / "measurement.json"
            events = read(receipt).get("protection_events", []) if receipt.exists() else []
            stalls = stalls + 1 if progress() == before else 0
            if not events or any(not event.endswith("_pressure") for event in events) or stalls >= 2:
                raise
            print(name, "guard interrupted the current case group", events, flush=True)
            time.sleep(20)


def apex_grader(args, spec):
    from matharena import grader
    revision = subprocess.check_output(["git", "-C", str(args.matharena), "rev-parse", "HEAD"],
                                       text=True).strip()
    if revision != spec["grader_revision"] or not Path(grader.__file__).is_relative_to(args.matharena.resolve()):
        raise ValueError("The Apex grader differs from the frozen version")
    cfg = dict(strict_parsing=False)
    def evaluate(text, tokens, expected):
        ans, correct, warning = grader.extract_and_grade([dict(role="assistant", content=text)],
                                                         tokens, expected, cfg)
        return dict(extracted=None if ans is None else str(ans), correct=bool(correct),
                    method="official MathArena grader", warning=int(warning))
    if not evaluate(r"\boxed{2}", 20, "2")["correct"] or evaluate(r"\boxed{3}", 20, "2")["correct"]:
        raise ValueError("Official scorer controls failed")
    return evaluate


def grade(args, spec):
    base = args.root / "evaluation"
    datasets = ("apex2025",) if args.suite == "apex" else ("generative-maths", "aime2025")
    gold = {key: val for dataset in datasets for key, val in read(base/dataset/"gold.json").items()}
    grading = Grader()
    apex = apex_grader(args, spec) if args.suite == "apex" else None
    models = {}
    details = {}
    expected_n = Counter(item["suite"] for item in spec["items"].values())
    try:
        for name in ("old", "nvfp4"):
            scores = {}
            for key, row in spec["items"].items():
                file = args.out/name/"answers"/(key+".json")
                if not file.exists():
                    continue
                answer = read(file)
                if answer["item"] != key or answer["input_tokens"] != len(row["ids"]):
                    raise ValueError("Mismatched saved generation")
                status = dict(tokens=answer["output_tokens"], truncated=answer["stop"]=="limit",
                              visible=bool(answer["content"].strip()), suite=row["suite"])
                if status["truncated"] or not status["visible"]:
                    result = dict(extracted=None, correct=False,
                                  method="budget exhausted" if status["truncated"] else "no visible answer")
                elif row["suite"] == "aime25":
                    extracted = parse_integer(answer["content"])
                    result = dict(extracted=extracted, correct=extracted == int(gold[row["key"]]),
                                  method="strict final-line integer")
                elif apex:
                    result = apex(answer["content"], status["tokens"], gold[row["key"]])
                else:
                    metrics = grading.score(row["suite"], gold[row["key"]], answer)
                    result = {name: metrics[name] for name in ("extracted", "correct", "method")}
                scores[key] = dict(status, **result)
            details[name] = scores
            models[name] = {}
            for kind, n in expected_n.items():
                rows = [value for value in scores.values() if value["suite"] == kind]
                count = len(rows)
                k = sum(value["correct"] for value in rows)
                scored = sum(value["extracted"] is not None for value in rows)
                models[name][kind] = dict(expected=n, generated=count, scored=scored, correct=k,
                    truncated=sum(value["truncated"] for value in rows),
                    unparseable_terminal=sum(value["extracted"] is None and not value["truncated"] for value in rows),
                    accuracy=k/count if count else None, wilson95=wilson(k,count),
                    mean_generated_tokens=statistics.mean(value["tokens"] for value in rows) if count else None)
    finally:
        grading.close()
    paired = {}
    for kind in expected_n:
        keys = [key for key in details["old"].keys() & details["nvfp4"].keys() if spec["items"][key]["suite"] == kind]
        cells = Counter((details["old"][key]["correct"],details["nvfp4"][key]["correct"]) for key in keys)
        paired[kind] = dict(n=len(keys), both_correct=cells[True,True], old_only=cells[True,False],
                            nvfp4_only=cells[False,True], neither=cells[False,False])
    result = dict(protocol=digest(args.out/"protocol.json"), models=models, items=details, paired=paired)
    save(args.out/"scores.json",result)
    print("Paired mathematical scores:", paired, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("run","grade"))
    p.add_argument("--suite", choices=("pilot","apex"), required=True)
    p.add_argument("--apex-problem", type=int, choices=range(1, 13))
    p.add_argument("--checkpoint-root", type=Path)
    p.add_argument("--checkpoint-proof", type=Path)
    p.add_argument("--checkpoint-start-tokens", type=int, default=CHUNK_TOKENS)
    for k in ("root","old","new","server","out","matharena"):
        p.add_argument("--"+k, type=Path, required=k!="matharena")
    args = p.parse_args()
    if args.suite == "apex" and args.matharena is None:
        p.error("The Apex suite requires the pinned official grader path")
    if args.apex_problem is not None and args.suite != "apex":
        p.error("A single-problem run is available for Apex only")
    if bool(args.checkpoint_root) != bool(args.checkpoint_proof) or (args.checkpoint_root and args.suite != "apex"):
        p.error("Apex checkpointing requires both a checkpoint path and a verified control")
    if not 64 <= args.checkpoint_start_tokens <= CHUNK_TOKENS:
        p.error(f"Use an initial Apex checkpoint interval between 64 and {CHUNK_TOKENS} tokens")
    args.out.mkdir(parents=True, exist_ok=True)
    spec = freeze(args)
    if args.action == "run":
        arms = (("old", args.old), ("nvfp4", args.new))
        batches = [None]
        if args.suite == "apex":
            items = list(spec["items"])
            batches = [items[i:i+2] for i in range(0, len(items), 2)]
        if args.apex_problem is not None:
            batches = [[f"apex2025-{args.apex_problem}"]]
        for selection in batches:
            try:
                for name, model in arms:
                    generate(args, spec, name, model, selection)
            finally:
                grade(args, spec)
    else:
        grade(args, spec)


if __name__ == "__main__":
    main()

"""Measure official and candidate likelihood on identical, frozen prediction positions."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile

from filelock import FileLock
import numpy as np

from agentic_external import MODEL
from benchmark_generation import digest, read, save
from benchmark_inkling2 import aggregate, score
from expert_attention import protocol
from phase7_controls import immutable, matrix
from sm120_native import run

HERE = Path(__file__).resolve().parent


def freeze(root):
    dest = root / "evaluation/phase13"
    dest.mkdir(parents=True, exist_ok=True)
    plan = read(HERE / "agentic_protocol.json")
    domains = list(plan["calibration"])
    texts = []
    for split in ("calibration", "validation", "holdout"):
        if list(plan[split]) != domains:
            raise ValueError("Unequal domain coverage")
        texts.extend(plan[split].values())
    if len(set(texts)) != len(texts):
        raise ValueError("Scenario overlap")
    immutable(dest / "protocol.json", plan)
    for split in ("calibration", "validation", "holdout"):
        # The capture tool accepts two named splits. Only the specified split is executed.
        other = "validation" if split != "validation" else "calibration"
        immutable(dest / (split + "-input.json"), dict(calibration=list(plan[split].values()),
                                                      holdout=list(plan[other].values())))
    return dest


def lease():
    return FileLock(str(Path(tempfile.gettempdir()) / "strata-inkling-benchmark-gpu0.lock"))


def attempt(dest):
    return dest / ("run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))


def captures(a):
    dest = freeze(a.root)
    for split in a.splits:
        folder = dest / ("source-" + split)
        cmd = [sys.executable, "-B", str(HERE / "calibrate_inkling2.py"), "--original",
               "--source", str(a.root / "official"), "--output", str(folder), "--texts",
               str(dest / (split + "-input.json")), "--split", "calibration",
               "--cache-gib", "1", "--sequence-batch", "4"]
        if split == "holdout":
            cmd += ["--compact-traces"]
        if not (folder / "splits.json").exists():
            with lease().acquire(poll_interval=.015):
                run(attempt(folder), cmd, 10300, 5400, 7200)
        if not all((folder / f"calibration-{n}.npz").exists() for n in range(8)):
            raise ValueError("Incomplete eight-domain source capture")


def compare(a):
    dest = freeze(a.root)
    _, rows, _, _ = protocol(a.root)
    if a.suite == "legacy":
        data = [(r["id"], r["ids"], a.root / f"evaluation/phase10/serial/dynamic/A/holdout-{i}.npz")
                for i, r in enumerate(rows)]
    else:
        if a.suite == "holdout" and a.label != "external" and not (dest / (a.label + "-selection.json")).is_file():
            raise ValueError("Lock the allocation before held-out inference")
        domains = read(dest / "protocol.json")[a.suite]
        data = []
        for i, domain in enumerate(domains):
            ref = dest / ("source-" + a.suite) / f"calibration-{i}.npz"
            with np.load(ref) as z:
                ids = z["input_ids"][0].tolist()
            data.append((domain, ids, ref))
    folder = dest / a.label / a.suite
    folder.mkdir(parents=True, exist_ok=True)
    model = a.model or dest / "external" / MODEL
    if not model.is_file():
        raise FileNotFoundError(model)
    immutable(folder / "identity.json", dict(model=str(model), bytes=model.stat().st_size, engine=digest(a.engine),
              runtime="Prism-derived llama.cpp CUDA, FP16 KV; single-sequence likelihood",
              dataset=a.suite, ids={name:ids for name,ids,_ in data}))
    missing = []
    for name, ids, ref in data:
        key = folder / name
        tokens = key.with_suffix(".i32")
        raw = np.array(ids, dtype="<i4").tobytes()
        if not tokens.exists():
            tokens.write_bytes(raw)
        if tokens.read_bytes() != raw:
            raise ValueError("Different input tokens")
        out = key.with_suffix(".logits")
        if not out.exists():
            missing.append((tokens, out, ids))
    if missing:
        work = attempt(folder)
        cmd = [str(a.engine), "--gpu-layers", "99", str(model)]
        for tokens, out, ids in missing:
            cmd.extend([str(tokens), str(work / out.name)])
        with lease().acquire(poll_interval=.012):
            run(work, cmd, 12500, 7200, 3600)
        for _, out, ids in missing:
            del_matrix = matrix(work / out.name, ids)
            del del_matrix
            (work / out.name).rename(out)
    results = {}
    for name, ids, ref in data:
        with np.load(ref) as z:
            if not np.array_equal(ids,z["input_ids"][0]):
                raise ValueError("Different source token sequence")
            results[name] = score(z["logits"], matrix(folder / (name + ".logits"), ids), ids)
    result = aggregate(results)
    result["device_runs"] = [read(p) for p in sorted(folder.glob("run-*/measurement.json"))]
    result["domain_equal_mean_kl"] = float(np.mean([s["sum_kl"]/s["tokens"] for s in results.values()]))
    save(folder / "results.json", result)
    print(a.label, a.suite, result["total_tokens"], result["candidate_ppl"], result["mean_kl"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("freeze","captures","compare"))
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--engine", type=Path)
    p.add_argument("--model", type=Path)
    p.add_argument("--label", default="external")
    p.add_argument("--suite", choices=("legacy","calibration","validation","holdout"), default="legacy")
    p.add_argument("--splits", nargs="+", choices=("calibration","validation","holdout"), default=["calibration","validation","holdout"])
    args=p.parse_args()
    if args.action=="captures": captures(args)
    elif args.action=="compare": compare(args)
    else: freeze(args.root)

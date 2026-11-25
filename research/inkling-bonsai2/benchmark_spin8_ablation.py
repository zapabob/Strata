"""Compare fixed-budget rotations on identified physical Inkling experts. Never infer missing metrics."""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from official_weights import Original, reconstruct, reference_bf16
from source import atomic_bytes
from spin8_quantizer import Basis, basis_matrix, decode, fit_for_activations, unpack


def candidates(budget):
    angles = np.asarray([0, .18, -.18, .34, -.34, .08, -.08, .49, -.49], np.float32)
    if not 1 <= budget <= len(angles):
        raise ValueError("The exploration budget must lie between one and nine")
    table = {k: [] for k in ("A", "B", "C", "C8", "D", "E", "F", "G", "H", "gauge")}
    for n in range(budget):
        theta, seed = float(angles[n]), 101 + n
        table["A"].append(Basis("direct"))
        table["B"].append(Basis("hadamard") if n == 0 else Basis("signed", seed=seed))
        table["C"].append(Basis("random", seed=seed))
        table["C8"].append(Basis("random-octet", seed=seed))
        for code, rep in zip("DEF", "VPM"):
            table[code].append(Basis(rep, theta=theta))
        rep = "VPM"[n % 3]
        for code in ("G", "H"):
            table[code].append(Basis(rep, theta=float(angles[n//3])))
        table["gauge"].append(Basis("gauged-P", theta=theta, seed=seed))
    return table


def metrics(w, reconstructed, visits=None):
    a, b = w.astype(np.float64), reconstructed.astype(np.float64)
    diff = b - a
    m = dict(weight_mse=float(np.mean(diff**2)), maximum_absolute_error=float(np.max(np.abs(diff))),
             weight_cosine=float(np.vdot(a, b) / (np.linalg.norm(a)*np.linalg.norm(b))) if np.any(b) else None)
    if visits is not None:
        per = []
        for x in visits:
            y, dy = x.astype(np.float64) @ a.T, x.astype(np.float64) @ diff.T
            per.append(dict(tokens=len(x), activation_mse=float(np.mean(dy**2)),
                            relative_l2=float(np.linalg.norm(dy) / max(np.linalg.norm(y),1e-30)),
                            cosine=float(np.vdot(y, y+dy)/max(np.linalg.norm(y)*np.linalg.norm(y+dy),1e-30))))
        m["by_visit"] = per
        m["activation_mse"] = float(np.mean([v["activation_mse"] for v in per]))
    return m


def read_acts(path, layer, expert, projection, split):
    if path is None:
        return None
    if path.is_dir():
        from calibrate_inkling2 import expert_activations
        visits=expert_activations(path,layer,expert,projection,split)
        if not visits:
            raise ValueError(f"No routed examples for layer {layer}, expert {expert} in {split}")
        return visits
    r = np.load(path)
    prefix = f"{split}.l{layer}.e{expert}.{projection}.v"
    keys = sorted(k for k in r.files if k.startswith(prefix))
    if not keys:
        raise ValueError(f"No observed activation visits for {prefix}")
    return [r[k] for k in keys]


def evaluate_bank(origin, layer, expert, proj, rows, budget, acts):
    import torch
    key = f"model.llm.layers.{layer}.mlp.experts.{proj}_weight"
    height = origin.header[key]["shape"][1]
    if 2*rows > height:
        raise ValueError("Disjoint calibration and evaluation rows are required")
    parts = [origin.parts(key, expert, start, rows, cache_ranges=True) for start in [0, height-rows]]
    matrices = [reconstruct(p) for p in parts]
    for p, w in zip(parts, matrices):
        if not torch.equal(reference_bf16(p), torch.from_numpy(w).to(torch.bfloat16)):
            raise ArithmeticError("Weights disagree with the official Transformers dequantiser at BF16")
    train, hold = matrices
    xt = read_acts(acts, layer, expert, proj, "calibration")
    xh = read_acts(acts, layer, expert, proj, "holdout")
    methods = {}
    history = {}
    for method, bases in candidates(budget).items():
        trials = []
        for b in bases:
            visit_weights = list(range(1, len(xt)+1)) if xt is not None and method=="H" else None
            cache_key = (b, bool(visit_weights))
            if cache_key not in history:
                payload = fit_for_activations(train, b, xt, visit_weights)
                trial = metrics(train, b.apply(decode(payload, train.shape), inverse=True), xt)
                history[cache_key] = trial.get("activation_mse", trial["weight_mse"])
            trials.append(history[cache_key])
        selected = int(np.argmin(trials))
        b = bases[selected]
        payload = fit_for_activations(hold, b, xt, list(range(1,len(xt)+1)) if xt is not None and method=="H" else None)
        out = b.apply(decode(payload, hold.shape), inverse=True)
        symbols, _ = unpack(payload)
        methods[method] = dict(kind=b.kind, theta=b.theta, seed=b.seed, calibration_scores=trials,
                               payload_bpw=8*payload.nbytes/hold.size, counts=np.bincount(
                                   symbols.ravel().astype(np.int16)+1, minlength=4).tolist(),
                               **metrics(hold, out, xh))
    return dict(layer=layer, expert=expert, projection=proj, source_scheme=origin.schemes[key]["weight_transform"],
                split_rows=[[0, rows], [height-rows, height]], width=train.shape[1],
                official_bf16_bit_match=True, methods=methods)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--banks", nargs="+", default=["6,0,w13","6,0,w2","20,0,w13","20,0,w2"])
    p.add_argument("--rows", type=int, default=64)
    p.add_argument("--budget", type=int, default=3)
    p.add_argument("--activations", type=Path)
    args = p.parse_args()
    origin = Original(args.source)
    report = dict(repository="thinkingmachines/Inkling-2-Mini", revision=origin.revision,
                  experiment="paired rows with held-out real activations" if args.activations else "paired weight-only row holdout",
                  angles_in_radians=True, trials_per_method=args.budget, calibration_rows_per_bank=args.rows,
                  controls={"C":"Haar SO(128)", "C8":"H16 times Haar SO(8)", "gauge":"orthogonal conjugate of S+",
                            "A":"unique identity, repeated scores are identical"},
                  v0_hadamard_max_delta=float(np.max(np.abs(basis_matrix(Basis("V"))-basis_matrix(Basis("hadamard"))))),
                  banks=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    for spec in args.banks:
        l,e,proj=spec.split(",")
        report["banks"].append(evaluate_bank(origin,int(l),int(e),proj,args.rows,args.budget,args.activations))
        report["seconds"]=time.monotonic()-start
        atomic_bytes(args.output, json.dumps(report, indent=2,allow_nan=False).encode())
        print(f"Measured {spec} ({len(report['banks'])}/{len(args.banks)})", flush=True)


if __name__ == "__main__":
    main()

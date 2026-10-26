"""Offline paired analysis. No launches, fitting, tuning, or adoption decisions.

Input is a frozen manifest and a list of collector-normalized run records.
The caller supplies the previously recorded canonical manifest SHA256 separately:
SHA256 of UTF-8 JSON serialized with sorted keys and compact comma/colon separators,
not the raw manifest file hash. Freeze it before collecting any runs.
Hashes bind records; they do not independently prove collector truth or quality.
See docs/perf131k-statistical-protocol.json for the manifest/record contract.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re
from statistics import fmean, median


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def analysis_sha256():
    """Freeze this source artifact before collection, alongside the Python environment."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def percentile(values, q):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    low = math.floor(pos)
    return ordered[low] + (ordered[math.ceil(pos)] - ordered[low]) * (pos - low)


def sign_flip(differences, seed, draws):
    """Two-sided absolute mean statistic; exchange labels once per family."""
    observed = abs(fmean(differences))
    exact = len(differences) <= 16
    rng = random.Random(seed)
    signs = (itertools.product((-1, 1), repeat=len(differences)) if exact else
             ((rng.choice((-1, 1)) for _ in differences) for _ in range(draws)))
    extreme = total = 0
    for assignment in signs:
        statistic = abs(fmean([a * b for a, b in zip(differences, assignment)]))
        # Tie tolerance scales with the endpoint's units. An absolute epsilon
        # makes sufficiently small nonzero effects count every permutation.
        extreme += statistic >= observed or math.isclose(statistic, observed, rel_tol=1e-12, abs_tol=0.0)
        total += 1
    return {"p_value": extreme / total if exact else (extreme + 1) / (total + 1),
            "method": "exact" if exact else "monte_carlo_add_one", "draws": total}


def holm(pvalues):
    ordered = sorted(pvalues, key=pvalues.get)
    result, previous = {}, 0.0
    for index, key in enumerate(ordered):
        previous = max(previous, min(1.0, (len(ordered) - index) * pvalues[key]))
        result[key] = previous
    return result


def validate(manifest, rows, frozen_sha):
    require(isinstance(manifest, dict) and isinstance(rows, list), "manifest object/run array required")
    require(sha(frozen_sha) and digest(manifest) == frozen_sha, "frozen manifest hash mismatch")
    require(manifest["analysis_sha256"] == analysis_sha256(), "frozen analysis source mismatch")
    require(manifest["schema"] == 2, "unsupported manifest schema")
    require(manifest["data_kind"] in ("synthetic", "measured"), "data kind required")
    require(manifest["stage"] in ("pilot", "full"), "unknown qualification stage")
    require(manifest["capacity"] == 131072, "capacity must be 131072")
    require(type(manifest["seed"]) is int, "integer seed required")
    for name in ("bootstrap_draws", "permutation_draws"):
        require(type(manifest[name]) is int and 100 <= manifest[name] <= 100000,
                "resampling count must be between 100 and 100000")
    require(set(manifest["arms"]) == {"baseline", "candidate"}, "two fixed arms required")
    for identity in manifest["arms"].values():
        require(set(identity) == {"source_sha256", "binary_sha256"} and
                all(sha(v) for v in identity.values()), "unresolved source/binary identity")
    require(sha(manifest["shared_identity_sha256"]), "shared configuration identity unresolved")
    endpoints = manifest["endpoints"]
    require(bool(endpoints) and all(isinstance(k, str) and k for k in endpoints) and
            all(v in ("lower", "higher") for v in endpoints.values()),
            "freeze endpoints and metric directions")
    families = manifest["families"]
    require(len(families) >= 2, "at least two independent families required")
    for family in families.values():
        require(type(family["fold"]) is int and 0 <= family["fold"] < 5,
                "family must have one frozen fold in 0..4")
    require(all(isinstance(k, str) and k for k in families), "nonempty family IDs required")
    require({v["fold"] for v in families.values()} == set(range(5)),
            "all five evaluation folds must be represented")
    expected = {}
    orders = []
    for pair in manifest["pairs"]:
        require(isinstance(pair["variant"], str) and bool(pair["variant"]) and
                type(pair["repeat"]) is int and pair["repeat"] >= 0,
                "nonempty variant ID and nonnegative integer repeat required")
        key = (pair["family"], pair["variant"], pair["repeat"])
        require(pair["family"] in families and key not in expected, "duplicate/unknown frozen pair")
        require(pair["order"] in ("AB", "BA"), "AB/BA order required")
        require(sha(pair["token_ids_sha256"]), "token IDs hash required")
        require(type(pair["input_tokens"]) is int and pair["input_tokens"] > 0,
                "positive exact input token count required")
        if manifest["stage"] == "full":
            require(pair["input_tokens"] == 126000 and pair["output_reserve"] == 1024,
                    "full gate requires exact 126000 input and 1024 reserve")
        else:
            require(pair["output_reserve"] == 256 and pair["input_tokens"] <= 131072 - 256,
                    "pilot reserve must remain 256 within capacity")
        expected[key] = pair
        orders.append(pair["order"])
    require(expected and abs(orders.count("AB") - orders.count("BA")) <= 1,
            "balanced frozen AB/BA map required")
    require({k[0] for k in expected} == set(families), "family without expected pairs")
    paired = {}
    for row in rows:
        key = (row["family"], row["variant"], row["repeat"])
        arm = row["arm"]
        require(key in expected and arm in manifest["arms"], "unregistered run")
        require((key, arm) not in paired, "duplicate run")
        require(row["status"] == "PASS", "failed runs block inference; retain original records")
        require(row["manifest_sha256"] == frozen_sha, "run belongs to another freeze")
        require(row["identity"] == manifest["arms"][arm] and
                row["shared_identity_sha256"] == manifest["shared_identity_sha256"],
                "run provenance mismatch")
        require(row["capacity"] == 131072 and row["data_kind"] == manifest["data_kind"],
                "run capacity/data kind mismatch")
        require(all(row[field] == expected[key][field] for field in
                    ("token_ids_sha256", "input_tokens", "output_reserve", "order")),
                "run differs from frozen pair")
        require(sha(row["raw_artifact_sha256"]), "raw artifact digest required")
        if manifest["stage"] == "full":
            require(type(row["generated_steps"]) is int and row["generated_steps"] >= 512,
                    "at least 512 actual generated steps required")
            require(sha(row["independent_receipt_sha256"]), "independent receipt required")
            require(row["processed_input_tokens"] == 126000 and
                    row["kv_progress_tokens"] == 126000 and row["recurrence_progress_tokens"] == 126000,
                    "processed input/KV/recurrence progress required")
        require(set(row["metrics"]) == set(endpoints) and
                all(number(v) and v > 0 for v in row["metrics"].values()),
                "complete finite positive timing/throughput metrics required")
        paired[key, arm] = row
    require(len(paired) == 2 * len(expected), "missing/unmatched runs block inference")
    return expected, paired


def _analyze(manifest, rows, frozen_sha):
    """Fail closed: invalid data never returns endpoint statistics or a verdict."""
    try:
        expected, paired = validate(manifest, rows, frozen_sha)
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError, OSError) as error:
        return {"status": "BLOCKED", "reason": str(error), "performance_verdict": "NOT_EVALUATED"}
    families = sorted(manifest["families"])
    reports = {}
    for endpoint, direction in manifest["endpoints"].items():
        aggregates = {}
        for arm in ("baseline", "candidate"):
            aggregates[arm] = []
            for family in families:
                variants = sorted({k[1] for k in expected if k[0] == family})
                aggregates[arm].append(median([
                    median([paired[k, arm]["metrics"][endpoint] for k in expected
                            if k[0] == family and k[1] == variant]) for variant in variants]))
        baseline, candidate = aggregates["baseline"], aggregates["candidate"]
        delta = [c - b for b, c in zip(baseline, candidate)]
        relative = [(b / c - 1) * 100 if direction == "lower" else (c / b - 1) * 100
                    for b, c in zip(baseline, candidate)]
        rng = random.Random(manifest["seed"])
        samples = [median([delta[rng.randrange(len(delta))] for _ in delta])
                   for _ in range(manifest["bootstrap_draws"])]
        reports[endpoint] = {
            "baseline_family_median": median(baseline), "candidate_family_median": median(candidate),
            "paired_median_difference_candidate_minus_baseline": median(delta),
            "paired_relative_speedup_percent": median(relative),
            "family_bootstrap_95_ci": [percentile(samples, .025), percentile(samples, .975)],
            "family_values": {f: {"baseline": b, "candidate": c}
                              for f, b, c in zip(families, baseline, candidate)},
            "test_statistic": "absolute mean of paired family differences",
            **sign_flip(delta, manifest["seed"], manifest["permutation_draws"])}
        reports[endpoint]["evaluation_fold_summaries"] = {}
        for fold in range(5):
            indices = [i for i, family in enumerate(families) if manifest["families"][family]["fold"] == fold]
            reports[endpoint]["evaluation_fold_summaries"][str(fold)] = {
                "families": [families[i] for i in indices], "n_family": len(indices),
                "baseline_family_median": median([baseline[i] for i in indices]),
                "candidate_family_median": median([candidate[i] for i in indices]),
                "paired_median_difference_candidate_minus_baseline": median([delta[i] for i in indices]),
            }
    adjusted = holm({k: v["p_value"] for k, v in reports.items()})
    for name, value in adjusted.items():
        reports[name]["holm_p_value"] = value
    return {"status": "DESIGN_NOT_RUN" if manifest["data_kind"] == "synthetic" else "ANALYZED",
            "data_kind": manifest["data_kind"], "stage": manifest["stage"],
            "manifest_sha256": frozen_sha, "seed": manifest["seed"],
            "analysis_sha256": manifest["analysis_sha256"],
            "performance_verdict": "NOT_EVALUATED", "n_family": len(families),
            "n_variant": len({k[:2] for k in expected}), "n_repeat_pairs": len(expected),
            "fold_map": {f: manifest["families"][f]["fold"] for f in families},
            "evaluation_design": "five grouped evaluation folds with fixed arms; no fitting or tuning",
            "endpoints": reports,
            "limits": "Hashed normalized records require independent collector/artifact review. "
                      "No quality, SLO, boundary, stability or adoption verdict; folds/repeats are not independent n."}


def analyze(manifest, rows, frozen_sha):
    try:
        report = _analyze(manifest, rows, frozen_sha)
        digest(report)  # Reject overflow/nonfinite derived statistics before emitting JSON.
        return report
    except (KeyError, TypeError, ValueError, ArithmeticError, AttributeError) as error:
        return {"status": "BLOCKED", "reason": str(error), "performance_verdict": "NOT_EVALUATED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("runs", type=Path)
    parser.add_argument("--frozen-sha256", required=True,
                        help="Previously frozen canonical JSON digest from digest(); not raw file SHA256")
    args = parser.parse_args()
    try:
        result = analyze(json.loads(args.manifest.read_text(encoding="utf-8")),
                         json.loads(args.runs.read_text(encoding="utf-8")), args.frozen_sha256)
    except (OSError, ValueError) as error:
        result = {"status": "BLOCKED", "reason": str(error), "performance_verdict": "NOT_EVALUATED"}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 2 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Evaluate complete two-model evidence; missing measurements never pass."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
from typing import Any


def number(value: Any, field: str, positive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"invalid_measurement:{field}")
    if (positive and value <= 0) or (not positive and value < 0):
        raise ValueError(f"invalid_measurement:{field}")
    return float(value)


def evaluate(report: dict[str, Any]) -> dict[str, Any]:
    """Apply adoption gates to measured results, not to source capabilities."""
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    if report.get("schema") != "strata-spin8-acceptance-v1":
        return {"passed": False, "failures": ["unsupported_evidence_schema"], "results": []}
    models = report.get("models", [])
    if not isinstance(models, list) or any(not isinstance(m, dict) for m in models) or sorted(str(m.get("id", "")) for m in models) != ["bonsai27b", "strata-q2_0"]:
        return {"passed": False, "failures": ["both_required_models_missing_or_duplicated"], "results": []}
    for model in models:
        name = model["id"]
        try:
            for gate in ("real_model_loaded", "strict_graph_connected", "three_physical_k_views",
                         "runtime_transform_monitor_verified", "original_service_restored"):
                if model.get(gate) is not True:
                    failures.append(f"{name}:{gate}")
            if model.get("cuda_architecture") != "sm_120":
                failures.append(f"{name}:standard_sm120_required")
            if model.get("warmups", 0) < 3 or model.get("paired") is not True:
                failures.append(f"{name}:unpaired_or_insufficient_warmup")
            contexts = model.get("contexts", [])
            if not isinstance(contexts, list) or sorted(c.get("input_tokens", 0) for c in contexts) != [4096, 32768]:
                failures.append(f"{name}:required_contexts_missing_or_duplicated")
            for context in contexts:
                readings = context.get("pairs", [])
                if len(readings) != 10:
                    raise ValueError("ten_measured_pairs_required")
                speeds: dict[str, list[float]] = {"baseline": [], "candidate": []}
                ttft: dict[str, list[float]] = {"baseline": [], "candidate": []}
                for pair in readings:
                    for arm in speeds:
                        row = pair[arm]
                        tokens = number(row.get("completion_tokens"), "completion_tokens")
                        duration = number(row.get("decode_seconds"), "decode_seconds")
                        speeds[arm].append(tokens / duration)
                        ttft[arm].append(number(row.get("ttft_seconds"), "ttft_seconds"))
                gain = statistics.median(speeds["candidate"]) / statistics.median(speeds["baseline"])
                wait = statistics.median(ttft["candidate"]) / statistics.median(ttft["baseline"])
                if gain < 1.05:
                    failures.append(f"{name}:{context['input_tokens']}:decode_gain_below_5_percent")
                if wait > 1.05:
                    failures.append(f"{name}:{context['input_tokens']}:ttft_regression_above_5_percent")
                results.append({"model": name, "input_tokens": context["input_tokens"],
                                "decode_ratio": gain, "ttft_ratio": wait})
            quality = model["quality"]
            nll_delta = number(quality["candidate_mean_nll"], "candidate_nll", False) - number(quality["baseline_mean_nll"], "baseline_nll", False)
            if nll_delta > math.log(1.01):
                failures.append(f"{name}:perplexity_regression_above_1_percent")
            if type(quality.get("new_fixed_case_failures")) is not int or quality["new_fixed_case_failures"] != 0:
                failures.append(f"{name}:new_quality_failures")
            if number(model["monitor_overhead_ratio"], "monitor_overhead", False) > 0.01:
                failures.append(f"{name}:monitor_overhead_above_1_percent")
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
            failures.append(f"{name}:incomplete_or_invalid_evidence:{error}")
    return {"passed": not failures, "failures": failures, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.report.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

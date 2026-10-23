"""Evaluate complete two-model evidence; missing measurements never pass."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import statistics
from typing import Any


def number(value: Any, field: str, positive: bool = True) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"invalid_measurement:{field}")
    if (positive and value <= 0) or (not positive and value < 0):
        raise ValueError(f"invalid_measurement:{field}")
    return float(value)


def evaluate_v1(report: dict[str, Any]) -> dict[str, Any]:
    """Apply adoption gates to measured results, not to source capabilities."""
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    if report.get("schema") != "strata-spin8-acceptance-v1":
        return {
            "passed": False,
            "failures": ["unsupported_evidence_schema"],
            "results": [],
        }
    models = report.get("models", [])
    if (
        not isinstance(models, list)
        or any(not isinstance(m, dict) for m in models)
        or sorted(str(m.get("id", "")) for m in models) != ["bonsai27b", "strata-q2_0"]
    ):
        return {
            "passed": False,
            "failures": ["both_required_models_missing_or_duplicated"],
            "results": [],
        }
    for model in models:
        name = model["id"]
        try:
            for gate in (
                "real_model_loaded",
                "strict_graph_connected",
                "three_physical_k_views",
                "runtime_transform_monitor_verified",
                "original_service_restored",
            ):
                if model.get(gate) is not True:
                    failures.append(f"{name}:{gate}")
            if model.get("cuda_architecture") != "sm_120":
                failures.append(f"{name}:standard_sm120_required")
            if model.get("warmups", 0) < 3 or model.get("paired") is not True:
                failures.append(f"{name}:unpaired_or_insufficient_warmup")
            contexts = model.get("contexts", [])
            if not isinstance(contexts, list) or sorted(
                c.get("input_tokens", 0) for c in contexts
            ) != [4096, 32768]:
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
                        tokens = number(
                            row.get("completion_tokens"), "completion_tokens"
                        )
                        duration = number(row.get("decode_seconds"), "decode_seconds")
                        speeds[arm].append(tokens / duration)
                        ttft[arm].append(
                            number(row.get("ttft_seconds"), "ttft_seconds")
                        )
                gain = statistics.median(speeds["candidate"]) / statistics.median(
                    speeds["baseline"]
                )
                wait = statistics.median(ttft["candidate"]) / statistics.median(
                    ttft["baseline"]
                )
                if gain < 1.05:
                    failures.append(
                        f"{name}:{context['input_tokens']}:decode_gain_below_5_percent"
                    )
                if wait > 1.05:
                    failures.append(
                        f"{name}:{context['input_tokens']}:ttft_regression_above_5_percent"
                    )
                results.append(
                    {
                        "model": name,
                        "input_tokens": context["input_tokens"],
                        "decode_ratio": gain,
                        "ttft_ratio": wait,
                    }
                )
            quality = model["quality"]
            nll_delta = number(
                quality["candidate_mean_nll"], "candidate_nll", False
            ) - number(quality["baseline_mean_nll"], "baseline_nll", False)
            if nll_delta > math.log(1.01):
                failures.append(f"{name}:perplexity_regression_above_1_percent")
            if (
                type(quality.get("new_fixed_case_failures")) is not int
                or quality["new_fixed_case_failures"] != 0
            ):
                failures.append(f"{name}:new_quality_failures")
            if (
                number(model["monitor_overhead_ratio"], "monitor_overhead", False)
                > 0.01
            ):
                failures.append(f"{name}:monitor_overhead_above_1_percent")
        except (
            KeyError,
            TypeError,
            ValueError,
            ZeroDivisionError,
            OverflowError,
        ) as error:
            failures.append(f"{name}:incomplete_or_invalid_evidence:{error}")
    return {"passed": not failures, "failures": failures, "results": results}


SCHEMA_V2 = "strata-spin8-acceptance-v2"
MODEL_HASHES = {
    "bonsai27b": ["0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13"],
    "strata-q2_0": [
        "69820c02ec7d0b45ef2ebb19d6620299db749fe2aded7f39f93c6b88b199b720",
        "316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113",
    ],
}
FUNCTIONAL_CASES = {
    "japanese",
    "english",
    "code",
    "long_context",
    "tool_call",
    "oom",
    "cancel",
    "cache_save",
    "cache_restore",
    "cache_copy",
    "cache_position",
    "cache_invalidation",
}
MAX_EVIDENCE_BYTES = 1024 * 1024
MAX_TOTAL_EVIDENCE_BYTES = 16 * MAX_EVIDENCE_BYTES


def require(condition: bool, field: str) -> None:
    """Reject an incomplete contract without substituting defaults."""
    if not condition:
        raise ValueError(field)


def object_value(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"object_required:{field}")
    return value


def list_value(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"list_required:{field}")
    return value


def count(value: Any, field: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, f"integer_required:{field}")
    return value


def identity(value: Any, field: str, length: int = 64) -> str:
    # Detect obvious placeholders; this cannot authenticate a measurement's truth.
    require(
        isinstance(value, str)
        and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None
        and len(set(value)) > 4,
        f"invalid_identity:{field}",
    )
    return value


class Evidence:
    """Read small JSON receipts only, never binaries, models or executable content."""

    def __init__(self, root: Path | None) -> None:
        self.root = root.resolve() if root is not None else None
        self.total_bytes = 0
        self.cache: dict[str, tuple[str, Any]] = {}

    def verify(self, record: Any, field: str) -> dict[str, Any]:
        record = object_value(record, field)
        ref = object_value(record.get("evidence"), field + ".evidence")
        path = ref.get("path")
        digest = identity(ref.get("sha256"), field + ".sha256")
        require(self.root is not None, "evidence_root_required")
        require(
            isinstance(path, str)
            and 0 < len(path) <= 240
            and "\\" not in path
            and ":" not in path
            and not PurePosixPath(path).is_absolute()
            and all(p not in ("", ".", "..") for p in path.split("/")),
            f"unsafe_evidence_path:{field}",
        )
        target = (self.root / path).resolve()
        require(target.is_relative_to(self.root), f"evidence_outside_root:{field}")
        if path not in self.cache:
            require(target.is_file(), f"evidence_file_missing:{field}")
            require(
                target.stat().st_size <= MAX_EVIDENCE_BYTES,
                f"evidence_too_large:{field}",
            )
            # Bounded read also handles a file growing after stat().
            with target.open("rb") as stream:
                raw = stream.read(MAX_EVIDENCE_BYTES + 1)
            self.total_bytes += len(raw)
            require(
                len(raw) <= MAX_EVIDENCE_BYTES
                and self.total_bytes <= MAX_TOTAL_EVIDENCE_BYTES,
                "evidence_byte_budget_exceeded",
            )
            self.cache[path] = (hashlib.sha256(raw).hexdigest(), json.loads(raw))
        actual_hash, payload = self.cache[path]
        require(actual_hash == digest, f"evidence_hash_mismatch:{field}")
        claims = {k: v for k, v in record.items() if k != "evidence"}
        # JSON text comparison preserves bool/int distinctions lost by Python equality.
        require(
            json.dumps(payload, sort_keys=True, allow_nan=False)
            == json.dumps(claims, sort_keys=True, allow_nan=False),
            f"evidence_content_mismatch:{field}",
        )
        return record


def bound_record(
    evidence: Evidence, record: Any, binding: dict[str, Any], field: str
) -> dict[str, Any]:
    record = evidence.verify(record, field)
    for key, expected in binding.items():
        require(
            type(record.get(key)) is type(expected) and record[key] == expected,
            f"identity_mismatch:{field}.{key}",
        )
    return record


def named_records(
    value: Any, key: str, expected: set[str], field: str
) -> list[dict[str, Any]]:
    records = [object_value(item, field) for item in list_value(value, field)]
    names = [record.get(key) for record in records]
    require(
        all(isinstance(name, str) for name in names)
        and len(names) == len(expected)
        and set(names) == expected,
        f"missing_or_duplicate_cases:{field}",
    )
    return records


def check_functional(
    evidence: Evidence, context: dict[str, Any], binding: dict[str, Any]
) -> None:
    functional = bound_record(
        evidence, context.get("functional"), binding, "functional"
    )
    require(
        count(functional.get("physical_k_views"), "physical_k_views") == 3,
        "three_physical_k_views_required",
    )
    require(
        count(functional.get("shared_v_views"), "shared_v_views") == 1,
        "one_shared_v_required",
    )
    count(functional.get("real_model_loads"), "real_model_loads", 1)
    count(functional.get("strict_graph_executions"), "strict_graph_executions", 1)
    for case in named_records(
        functional.get("cases"), "name", FUNCTIONAL_CASES, "functional.cases"
    ):
        count(case.get("executed"), "executed", 1)
        require(
            count(case.get("failures"), "failures") == 0,
            f"functional_failure:{case['name']}",
        )


def check_quality(
    evidence: Evidence, context: dict[str, Any], binding: dict[str, Any]
) -> float:
    quality = bound_record(evidence, context.get("quality"), binding, "quality")
    require(quality.get("outcome") == "conclusive", "quality_inconclusive")
    datasets = object_value(quality.get("datasets"), "datasets")
    ids, hashes = [], []
    for purpose in ("evaluation", "training", "calibration", "selection"):
        dataset = object_value(datasets.get(purpose), "datasets." + purpose)
        dataset_id = dataset.get("id")
        require(
            isinstance(dataset_id, str)
            and dataset_id.strip()
            and dataset_id.lower()
            not in ("todo", "placeholder", "unknown", "synthetic"),
            f"invalid_dataset_id:{purpose}",
        )
        ids.append(dataset_id)
        hashes.append(identity(dataset.get("sha256"), "dataset." + purpose))
        for key in ("source", "revision", "split"):
            value = dataset.get(key)
            require(
                isinstance(value, str)
                and value.strip()
                and value.lower() not in ("todo", "unknown", "placeholder"),
                f"dataset_provenance_required:{purpose}.{key}",
            )
    require(
        len(set(ids)) == 4 and len(set(hashes)) == 4, "quality_dataset_not_independent"
    )
    count(quality.get("evaluated_tokens"), "evaluated_tokens", 1)
    candidate_nll = number(quality.get("candidate_mean_nll"), "candidate_nll", False)
    baseline_nll = number(quality.get("baseline_mean_nll"), "baseline_nll", False)
    delta = candidate_nll - baseline_nll
    require(
        candidate_nll <= baseline_nll + math.log(1.01),
        "perplexity_regression_above_1_percent",
    )
    for case in named_records(
        quality.get("fixed_cases"), "id", FUNCTIONAL_CASES, "fixed_cases"
    ):
        require(
            case.get("baseline") in ("pass", "fail")
            and case.get("candidate") in ("pass", "fail"),
            "fixed_case_result_required",
        )
        require(
            not (case["baseline"] == "pass" and case["candidate"] == "fail"),
            "new_quality_failures",
        )
    return delta


def check_monitor(
    evidence: Evidence, context: dict[str, Any], binding: dict[str, Any]
) -> float:
    monitor = bound_record(evidence, context.get("monitor"), binding, "monitor")
    baseline = number(
        monitor.get("overhead_baseline_seconds"), "overhead_baseline_seconds"
    )
    monitored = number(
        monitor.get("overhead_monitored_seconds"), "overhead_monitored_seconds"
    )
    overhead = (monitored - baseline) / baseline
    require(overhead <= 0.01, "monitor_overhead_above_1_percent")
    for audit in named_records(
        monitor.get("audits"),
        "trigger",
        {"load", "coefficient_change", "tokens_1024", "seconds_60"},
        "monitor.audits",
    ):
        count(audit.get("cpu_audits"), "cpu_audits", 1)
        count(audit.get("gpu_probes"), "gpu_probes", 1)
    for fault in named_records(
        monitor.get("faults"),
        "target",
        {"cpu_coefficients", "gpu_probe"},
        "monitor.faults",
    ):
        injections = count(fault.get("injections"), "injections", 1)
        require(
            count(fault.get("stopped"), "stopped") == injections
            and count(fault.get("invalidated"), "invalidated") == injections
            and fault.get("error") == "transform_invariant_violation",
            "monitor_not_fail_closed",
        )
    return overhead


def check_pairs(
    evidence: Evidence,
    value: Any,
    total: int,
    start: int,
    binding: dict[str, Any],
    builds: dict[str, Any],
    condition_hash: str,
) -> tuple[float, float]:
    pairs = list_value(value, "pairs")
    require(len(pairs) == total, f"{total}_pairs_required")
    speeds: dict[str, list[float]] = {"baseline": [], "candidate": []}
    ttft: dict[str, list[float]] = {"baseline": [], "candidate": []}
    generation_lengths: set[int] = set()
    for i, value in enumerate(pairs):
        pair = object_value(value, "pair")
        expected_order = (
            ["baseline", "candidate"] if i % 2 == 0 else ["candidate", "baseline"]
        )
        require(
            pair.get("order") == expected_order, "alternating_execution_order_required"
        )
        lengths = []
        prompts = []
        for arm in expected_order:
            identity_binding = dict(
                binding,
                arm=arm,
                source_commit=builds[arm]["source_commit"],
                binary_sha256=builds[arm]["binary_sha256"],
                conditions_sha256=condition_hash,
            )
            row = bound_record(evidence, pair.get(arm), identity_binding, "measurement")
            require(
                count(row.get("run_index"), "run_index")
                == start + i * 2 + expected_order.index(arm),
                "execution_sequence_mismatch",
            )
            tokens = count(row.get("completion_tokens"), "completion_tokens", 1)
            lengths.append(tokens)
            generation_lengths.add(tokens)
            prompts.append(identity(row.get("prompt_sha256"), "prompt_sha256"))
            speeds[arm].append(
                number(
                    tokens / number(row.get("decode_seconds"), "decode_seconds"),
                    "derived_decode_speed",
                )
            )
            ttft[arm].append(number(row.get("ttft_seconds"), "ttft_seconds"))
        require(lengths[0] == lengths[1], "generation_lengths_mismatch")
        require(prompts[0] == prompts[1], "paired_prompt_mismatch")
    require(len(generation_lengths) == 1, "generation_lengths_not_fixed")
    return (
        number(
            statistics.median(speeds["candidate"])
            / statistics.median(speeds["baseline"]),
            "derived_decode_ratio",
        ),
        number(
            statistics.median(ttft["candidate"]) / statistics.median(ttft["baseline"]),
            "derived_ttft_ratio",
        ),
    )


def evaluate_v2(report: dict[str, Any], evidence_root: Path | None) -> dict[str, Any]:
    """Qualify the recorded model gates, not the whole distribution or release."""
    evidence = Evidence(evidence_root)
    require(report.get("evidence_kind") == "measured", "measured_evidence_required")
    measured_date = report.get("measured_date")
    require(
        isinstance(measured_date, str)
        and date.fromisoformat(measured_date).isoformat() == measured_date,
        "measurement_date_required",
    )
    builds = object_value(report.get("builds"), "builds")
    for arm in ("baseline", "candidate"):
        build = evidence.verify(builds.get(arm), "builds." + arm)
        identity(build.get("source_commit"), "source_commit", 40)
        identity(build.get("binary_sha256"), "binary_sha256")
    runtime = object_value(report.get("runtime"), "runtime")
    require(
        runtime.get("policy") == "keep-8080-stopped",
        "keep_8080_stopped_policy_required",
    )
    for probe in named_records(
        runtime.get("probes"),
        "phase",
        {"before", "after_success", "after_failure", "after_cancel"},
        "runtime.probes",
    ):
        evidence.verify(probe, "runtime.probe")
        require(
            count(probe.get("port"), "port") == 8080
            and count(probe.get("listener_count"), "listener_count") == 0,
            "port_8080_not_stopped",
        )
    models = named_records(report.get("models"), "id", set(MODEL_HASHES), "models")
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    for model in models:
        name = model["id"]
        try:
            require(
                model.get("model_sha256") == MODEL_HASHES[name],
                "frozen_model_identity_mismatch",
            )
            require(
                model.get("performance_mode") in ("single-view", "three-view"),
                "performance_mode_required",
            )
            contexts = list_value(model.get("contexts"), "contexts")
            require(
                len(contexts) == 2
                and all(isinstance(c, dict) for c in contexts)
                and sorted(
                    count(c.get("input_tokens"), "input_tokens") for c in contexts
                )
                == [4096, 32768],
                "required_contexts_missing_or_duplicated",
            )
            for context in contexts:
                binding = dict(
                    model_id=name,
                    model_sha256=MODEL_HASHES[name],
                    input_tokens=context["input_tokens"],
                    measured_date=measured_date,
                )
                conditions = evidence.verify(context.get("conditions"), "conditions")
                require(
                    conditions.get("cuda_architecture") == "sm_120"
                    and conditions.get("baseline_profile") == "optimised",
                    "optimised_sm120_baseline_required",
                )
                for field in ("device", "sampling", "codec"):
                    require(
                        isinstance(conditions.get(field), str)
                        and conditions[field].strip()
                        and conditions[field].lower()
                        not in ("todo", "unknown", "placeholder"),
                        "conditions_required:" + field,
                    )
                count(conditions.get("concurrency"), "concurrency", 1)
                identity(conditions.get("adapter_sha256"), "adapter_sha256")
                mode = model["performance_mode"]
                require(
                    conditions.get("candidate_mode") == mode
                    and count(
                        conditions.get("candidate_physical_k_views"),
                        "candidate_physical_k_views",
                    )
                    == (1 if mode == "single-view" else 3),
                    "performance_mode_mismatch",
                )
                condition_hash = conditions["evidence"]["sha256"]
                check_pairs(
                    evidence,
                    context.get("warmups"),
                    3,
                    0,
                    binding,
                    builds,
                    condition_hash,
                )
                gain, wait = check_pairs(
                    evidence,
                    context.get("pairs"),
                    10,
                    6,
                    binding,
                    builds,
                    condition_hash,
                )
                candidate_binding = dict(
                    binding,
                    source_commit=builds["candidate"]["source_commit"],
                    binary_sha256=builds["candidate"]["binary_sha256"],
                    conditions_sha256=condition_hash,
                )
                result = dict(
                    model=name,
                    input_tokens=context["input_tokens"],
                    performance_mode=mode,
                    decode_ratio=gain,
                    ttft_ratio=wait,
                    quality_status="not_qualified",
                )
                results.append(result)
                quality = context.get("quality")
                if (
                    isinstance(quality, dict)
                    and quality.get("outcome") == "inconclusive"
                ):
                    result["quality_status"] = "reported_inconclusive"
                check_functional(evidence, context, candidate_binding)
                result["nll_delta"] = check_quality(
                    evidence, context, candidate_binding
                )
                result["quality_status"] = "conclusive"
                result["monitor_overhead_ratio"] = check_monitor(
                    evidence, context, candidate_binding
                )
                if gain < 1.05:
                    failures.append(
                        f"{name}:{context['input_tokens']}:decode_gain_below_5_percent"
                    )
                if wait > 1.05:
                    failures.append(
                        f"{name}:{context['input_tokens']}:ttft_regression_above_5_percent"
                    )
        except (
            KeyError,
            TypeError,
            ValueError,
            OSError,
            OverflowError,
            RecursionError,
            ZeroDivisionError,
        ) as error:
            failures.append(f"{name}:incomplete_or_invalid_evidence:{error}")
    return dict(
        passed=not failures,
        formal_eligible=not failures,
        failures=failures,
        results=results,
    )


def evaluate(report: Any, *, evidence_root: Path | None = None) -> dict[str, Any]:
    """Fail closed on malformed input; v1 remains diagnostic, never formal proof."""
    result = _evaluate(report, evidence_root=evidence_root)
    result["qualification_scope"] = "model_evidence_gate_only"
    result["release_authorized"] = False
    return result


def _evaluate(report: Any, *, evidence_root: Path | None = None) -> dict[str, Any]:
    try:
        report = object_value(report, "report")
        if report.get("schema") == "strata-spin8-acceptance-v1":
            diagnostic = evaluate_v1(report)
            return dict(
                passed=False,
                formal_eligible=False,
                diagnostic_passed=diagnostic["passed"],
                failures=["legacy_schema_not_formal_eligible", *diagnostic["failures"]],
                results=diagnostic["results"],
            )
        require(report.get("schema") == SCHEMA_V2, "unsupported_evidence_schema")
        return evaluate_v2(report, evidence_root)
    except (
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        OSError,
        OverflowError,
        RecursionError,
        ZeroDivisionError,
    ) as error:
        return dict(
            passed=False,
            formal_eligible=False,
            failures=[f"incomplete_or_invalid_evidence:{error}"],
            results=[],
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        help="Root of bounded, hashed JSON evidence receipts (v2)",
    )
    args = parser.parse_args()
    try:
        with args.report.open("rb") as stream:
            raw = stream.read(MAX_TOTAL_EVIDENCE_BYTES + 1)
        require(len(raw) <= MAX_TOTAL_EVIDENCE_BYTES, "report_too_large")
        result = evaluate(json.loads(raw), evidence_root=args.evidence_root)
    except (OSError, ValueError, RecursionError) as error:
        result = evaluate(None)
        result["failures"] = [f"invalid_report:{error}"]
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

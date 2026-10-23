"""Synthetic gate fixtures are test inputs, never benchmark evidence."""

from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from spin8_acceptance import evaluate


def fixture() -> dict:
    models = []
    for name in ("bonsai27b", "strata-q2_0"):
        model = dict(
            id=name,
            real_model_loaded=True,
            strict_graph_connected=True,
            three_physical_k_views=True,
            runtime_transform_monitor_verified=True,
            original_service_restored=True,
            cuda_architecture="sm_120",
            warmups=3,
            paired=True,
            monitor_overhead_ratio=0.005,
            quality=dict(
                candidate_mean_nll=2.001, baseline_mean_nll=2, new_fixed_case_failures=0
            ),
            contexts=[],
        )
        for count in (4096, 32768):
            pairs = [
                dict(
                    baseline=dict(
                        completion_tokens=100, decode_seconds=2, ttft_seconds=1
                    ),
                    candidate=dict(
                        completion_tokens=100, decode_seconds=1.8, ttft_seconds=1.01
                    ),
                )
                for _ in range(10)
            ]
            model["contexts"].append(dict(input_tokens=count, pairs=pairs))
        models.append(model)
    return dict(schema="strata-spin8-acceptance-v1", models=models)


class AcceptanceTest(unittest.TestCase):
    def test_complete_synthetic_evidence(self) -> None:
        result = evaluate(fixture())
        self.assertFalse(result["passed"])
        self.assertTrue(result["diagnostic_passed"])
        self.assertFalse(result["formal_eligible"])

    def test_missing_model_cannot_pass(self) -> None:
        data = fixture()
        data["models"].pop()
        self.assertFalse(evaluate(data)["passed"])

    def test_single_cache_cannot_pass_even_if_fast(self) -> None:
        data = fixture()
        data["models"][0]["three_physical_k_views"] = False
        self.assertFalse(evaluate(data)["passed"])

    def test_each_missing_gate_fails(self) -> None:
        for field in (
            "strict_graph_connected",
            "runtime_transform_monitor_verified",
            "original_service_restored",
        ):
            data = fixture()
            del data["models"][0][field]
            self.assertFalse(evaluate(data)["passed"])

    def test_invalid_or_incomplete_pairs_fail(self) -> None:
        for value in (float("nan"), 0, -1, True, "fast"):
            data = fixture()
            data["models"][0]["contexts"][0]["pairs"][0]["candidate"][
                "decode_seconds"
            ] = value
            self.assertFalse(evaluate(data)["passed"])

    def test_quality_regression_fails(self) -> None:
        data = fixture()
        data["models"][0]["quality"]["candidate_mean_nll"] = 2.02
        self.assertFalse(evaluate(data)["passed"])


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class AcceptanceV2Test(unittest.TestCase):
    """Only evaluator inputs: these generated receipts are NOT model evidence."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0
        self.data = self.make_fixture()

    def receipt(self, record: dict) -> dict:
        self.serial += 1
        raw = json.dumps(record, sort_keys=True).encode()
        path = f"receipt-{self.serial}.json"
        (self.root / path).write_bytes(raw)
        return dict(
            record, evidence=dict(path=path, sha256=hashlib.sha256(raw).hexdigest())
        )

    def make_fixture(self) -> dict:
        identities = {
            "bonsai27b": [
                "0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13"
            ],
            "strata-q2_0": [
                "69820c02ec7d0b45ef2ebb19d6620299db749fe2aded7f39f93c6b88b199b720",
                "316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113",
            ],
        }
        builds = {
            arm: self.receipt(
                dict(
                    source_commit=digest(arm)[:40], binary_sha256=digest(arm + "binary")
                )
            )
            for arm in ("baseline", "candidate")
        }
        report = dict(
            schema="strata-spin8-acceptance-v2",
            measured_date="2026-10-23",
            evidence_kind="measured",
            builds=builds,
            runtime=dict(
                policy="keep-8080-stopped",
                probes=[
                    self.receipt(dict(phase=p, port=8080, listener_count=0))
                    for p in (
                        "before",
                        "after_success",
                        "after_failure",
                        "after_cancel",
                    )
                ],
            ),
            models=[],
        )
        coverage = (
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
        )
        for name, hashes in identities.items():
            model = dict(
                id=name,
                model_sha256=hashes,
                performance_mode="single-view",
                contexts=[],
            )
            for count in (4096, 32768):
                binding = dict(
                    model_id=name,
                    model_sha256=hashes,
                    input_tokens=count,
                    measured_date=report["measured_date"],
                )
                conditions = self.receipt(
                    dict(
                        cuda_architecture="sm_120",
                        device="RTX fixture",
                        sampling="temperature=0;seed=17",
                        concurrency=1,
                        baseline_profile="optimised",
                        candidate_mode="single-view",
                        candidate_physical_k_views=1,
                        codec="reference-absmax-v1",
                        adapter_sha256=digest("adapter"),
                    )
                )
                condition_hash = conditions["evidence"]["sha256"]

                def pairs(n: int, start: int) -> list:
                    rows = []
                    for i in range(n):
                        order = (
                            ["baseline", "candidate"]
                            if i % 2 == 0
                            else ["candidate", "baseline"]
                        )
                        pair = dict(order=order)
                        for arm in order:
                            pair[arm] = self.receipt(
                                dict(
                                    binding,
                                    arm=arm,
                                    run_index=start + i * 2 + order.index(arm),
                                    source_commit=builds[arm]["source_commit"],
                                    binary_sha256=builds[arm]["binary_sha256"],
                                    prompt_sha256=digest(f"{name}-{count}-{i}"),
                                    conditions_sha256=condition_hash,
                                    completion_tokens=100,
                                    decode_seconds=2 if arm == "baseline" else 1.8,
                                    ttft_seconds=1,
                                )
                            )
                        rows.append(pair)
                    return rows

                datasets = {
                    purpose: dict(
                        id=f"{name}-{purpose}",
                        sha256=digest(name + purpose),
                        source="fixture-corpus",
                        revision="fixture-r1",
                        split=purpose,
                    )
                    for purpose in (
                        "evaluation",
                        "training",
                        "calibration",
                        "selection",
                    )
                }
                candidate_binding = dict(
                    binding,
                    source_commit=builds["candidate"]["source_commit"],
                    binary_sha256=builds["candidate"]["binary_sha256"],
                    conditions_sha256=condition_hash,
                )
                context = dict(
                    input_tokens=count,
                    conditions=conditions,
                    warmups=pairs(3, 0),
                    pairs=pairs(10, 6),
                    quality=self.receipt(
                        dict(
                            candidate_binding,
                            datasets=datasets,
                            evaluated_tokens=1000,
                            baseline_mean_nll=2,
                            candidate_mean_nll=2.001,
                            outcome="conclusive",
                            fixed_cases=[
                                dict(id=c, baseline="pass", candidate="pass")
                                for c in coverage
                            ],
                        )
                    ),
                    functional=self.receipt(
                        dict(
                            candidate_binding,
                            physical_k_views=3,
                            shared_v_views=1,
                            real_model_loads=1,
                            strict_graph_executions=1,
                            cases=[
                                dict(name=c, executed=1, failures=0) for c in coverage
                            ],
                        )
                    ),
                    monitor=self.receipt(
                        dict(
                            candidate_binding,
                            overhead_baseline_seconds=100,
                            overhead_monitored_seconds=100.5,
                            audits=[
                                dict(trigger=t, cpu_audits=1, gpu_probes=1)
                                for t in (
                                    "load",
                                    "coefficient_change",
                                    "tokens_1024",
                                    "seconds_60",
                                )
                            ],
                            faults=[
                                dict(
                                    target=t,
                                    injections=1,
                                    stopped=1,
                                    invalidated=1,
                                    error="transform_invariant_violation",
                                )
                                for t in ("cpu_coefficients", "gpu_probe")
                            ],
                        )
                    ),
                )
                model["contexts"].append(context)
            report["models"].append(model)
        return report

    def result(self) -> dict:
        return evaluate(self.data, evidence_root=self.root)

    def test_complete_single_view_candidate_with_separate_three_k_proof(self) -> None:
        result = self.result()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["formal_eligible"])
        self.assertEqual(len(result["results"]), 4)
        self.assertEqual(result["qualification_scope"], "model_evidence_gate_only")
        self.assertFalse(result["release_authorized"])

    def test_three_view_performance_candidate_can_also_qualify(self) -> None:
        for model in self.data["models"]:
            model["performance_mode"] = "three-view"
            for context in model["contexts"]:
                self.replace_record(
                    context,
                    "conditions",
                    candidate_mode="three-view",
                    candidate_physical_k_views=3,
                )
                condition_hash = context["conditions"]["evidence"]["sha256"]
                for group in ("warmups", "pairs"):
                    for pair in context[group]:
                        for arm in ("baseline", "candidate"):
                            self.replace_record(
                                pair, arm, conditions_sha256=condition_hash
                            )
                for field in ("quality", "functional", "monitor"):
                    self.replace_record(
                        context, field, conditions_sha256=condition_hash
                    )
        self.assertTrue(self.result()["passed"])

    def test_exact_quality_and_overhead_limits_are_inclusive(self) -> None:
        for model in self.data["models"]:
            for context in model["contexts"]:
                self.replace_record(
                    context, "quality", candidate_mean_nll=2 + math.log(1.01)
                )
                self.replace_record(context, "monitor", overhead_monitored_seconds=101)
        self.assertTrue(self.result()["passed"])

    def test_no_evidence_root_never_qualifies(self) -> None:
        self.assertFalse(evaluate(self.data)["passed"])

    def test_cli_qualifies_only_model_gate_and_handles_invalid_json(self) -> None:
        report_path = self.root / "report.json"
        report_path.write_text(json.dumps(self.data), encoding="utf-8")
        command = [
            sys.executable,
            str(Path(__file__).with_name("spin8_acceptance.py")),
            str(report_path),
            "--evidence-root",
            str(self.root),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse(json.loads(result.stdout)["release_authorized"])
        for raw in ("{broken", "[]", "null"):
            report_path.write_text(raw, encoding="utf-8")
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse(json.loads(result.stdout)["passed"])

    def test_exact_model_context_and_repetition_requirements(self) -> None:
        for kind in ("model", "context", "warmups", "pairs"):
            self.data = self.make_fixture()
            model = self.data["models"][0]
            context = model["contexts"][0]
            if kind == "model":
                model["model_sha256"] = [digest("wrong-model")]
            elif kind == "context":
                model["contexts"] = [context, context]
            else:
                context[kind].pop()
            self.assertFalse(self.result()["passed"], kind)

    def test_missing_quality_provenance_and_boolean_monitor_counts_fail(self) -> None:
        context = self.data["models"][0]["contexts"][0]
        datasets = copy.deepcopy(context["quality"]["datasets"])
        del datasets["evaluation"]["revision"]
        self.replace_record(context, "quality", datasets=datasets)
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        context = self.data["models"][0]["contexts"][0]
        faults = copy.deepcopy(context["monitor"]["faults"])
        faults[0]["stopped"] = True
        self.replace_record(context, "monitor", faults=faults)
        self.assertFalse(self.result()["passed"])

    def test_root_and_nested_malformed_values_fail_closed(self) -> None:
        for value in (None, [], True, 4, "report"):
            with self.subTest(root=value):
                self.assertFalse(evaluate(value)["passed"])
        original = copy.deepcopy(self.data)
        for path in (
            ("builds",),
            ("models",),
            ("runtime",),
            ("models", 0, "contexts"),
            ("models", 0, "contexts", 0, "pairs", 0, "candidate"),
            ("models", 0, "contexts", 0, "functional"),
        ):
            for value in (None, [], True, 1):
                self.data = copy.deepcopy(original)
                node = self.data
                for key in path[:-1]:
                    node = node[key]
                node[path[-1]] = value
                self.assertFalse(self.result()["passed"], (path, value))

    def test_missing_models_contexts_or_warmups_fail(self) -> None:
        for field in ("models",):
            self.data[field].pop()
            self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        self.data["models"][0]["contexts"].pop()
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        self.data["models"][0]["contexts"][0]["warmups"] = True
        self.assertFalse(self.result()["passed"])

    def replace_record(self, container: dict, key: str, **changes: object) -> None:
        record = {k: v for k, v in container[key].items() if k != "evidence"}
        record.update(changes)
        container[key] = self.receipt(record)

    def test_nonfinite_bool_count_and_generation_mismatch_fail(self) -> None:
        for field, value in (
            ("completion_tokens", True),
            ("completion_tokens", 101),
            ("decode_seconds", float("inf")),
            ("decode_seconds", 10**400),
            ("decode_seconds", 1e-320),
            ("ttft_seconds", float("nan")),
            ("input_tokens", True),
        ):
            self.data = self.make_fixture()
            pair = self.data["models"][0]["contexts"][0]["pairs"][0]
            self.replace_record(pair, "candidate", **{field: value})
            self.assertFalse(self.result()["passed"], (field, value))

    def test_repeated_pair_order_and_wrong_run_sequence_fail(self) -> None:
        pairs = self.data["models"][0]["contexts"][0]["pairs"]
        pairs[1]["order"] = pairs[0]["order"]
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        pair = self.data["models"][0]["contexts"][0]["pairs"][0]
        self.replace_record(pair, "candidate", run_index=99)
        self.assertFalse(self.result()["passed"])

    def test_identity_date_and_conditions_mismatch_fail(self) -> None:
        for field, value in (
            ("source_commit", digest("other")[:40]),
            ("binary_sha256", digest("other")),
            ("model_sha256", [digest("other")]),
            ("measured_date", "2026-10-22"),
            ("conditions_sha256", digest("other")),
        ):
            self.data = self.make_fixture()
            pair = self.data["models"][0]["contexts"][0]["pairs"][0]
            self.replace_record(pair, "candidate", **{field: value})
            self.assertFalse(self.result()["passed"], field)

    def test_same_prompt_is_required_for_both_arms(self) -> None:
        pair = self.data["models"][0]["contexts"][0]["pairs"][0]
        self.replace_record(pair, "candidate", prompt_sha256=digest("different prompt"))
        self.assertFalse(self.result()["passed"])

    def test_evidence_content_must_match_and_reads_are_bounded(self) -> None:
        build = self.data["builds"]["baseline"]
        other = self.receipt(
            dict(source_commit=digest("other")[:40], binary_sha256=digest("other"))
        )
        build["evidence"] = other["evidence"]
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        ref = self.data["builds"]["baseline"]["evidence"]
        (self.root / ref["path"]).write_bytes(b" " * (1024 * 1024 + 1))
        self.assertFalse(self.result()["passed"])

    def test_legacy_malformed_nested_evidence_never_crashes(self) -> None:
        data = fixture()
        data["models"][0]["contexts"] = [None]
        self.assertFalse(evaluate(data)["passed"])

    def test_quality_independence_and_inconclusive_fail(self) -> None:
        context = self.data["models"][0]["contexts"][0]
        sets = copy.deepcopy(context["quality"]["datasets"])
        sets["evaluation"] = sets["calibration"]
        self.replace_record(context, "quality", datasets=sets)
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        context = self.data["models"][0]["contexts"][0]
        self.replace_record(context, "quality", outcome="inconclusive")
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertEqual(
            result["results"][0]["quality_status"], "reported_inconclusive"
        )
        self.assertGreater(result["results"][0]["decode_ratio"], 1.05)

    def test_functional_coverage_cannot_be_boolean_or_single_k(self) -> None:
        for changes in (
            dict(physical_k_views=1),
            dict(real_model_loads=True),
            dict(cases=[]),
        ):
            self.data = self.make_fixture()
            context = self.data["models"][0]["contexts"][0]
            self.replace_record(context, "functional", **changes)
            self.assertFalse(self.result()["passed"], changes)

    def test_monitor_fault_and_runtime_policy_failures(self) -> None:
        context = self.data["models"][0]["contexts"][0]
        self.replace_record(context, "monitor", faults=[])
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        self.data["runtime"]["policy"] = "restore-original-service"
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        probe = self.data["runtime"]["probes"][0]
        self.data["runtime"]["probes"][0] = self.receipt(
            dict(phase=probe["phase"], port=8080, listener_count=True)
        )
        self.assertFalse(self.result()["passed"])

    def test_each_numeric_gate_rejects_a_real_regression(self) -> None:
        for gate in ("decode", "ttft", "nll", "fixed", "monitor"):
            self.data = self.make_fixture()
            context = self.data["models"][0]["contexts"][0]
            if gate in ("decode", "ttft"):
                for pair in context["pairs"]:
                    self.replace_record(
                        pair,
                        "candidate",
                        **{"decode_seconds" if gate == "decode" else "ttft_seconds": 3},
                    )
            elif gate == "nll":
                self.replace_record(context, "quality", candidate_mean_nll=2.02)
            elif gate == "fixed":
                cases = copy.deepcopy(context["quality"]["fixed_cases"])
                cases[0]["candidate"] = "fail"
                self.replace_record(context, "quality", fixed_cases=cases)
            else:
                self.replace_record(context, "monitor", overhead_monitored_seconds=102)
            self.assertFalse(self.result()["passed"], gate)

    def test_tampered_missing_placeholder_and_unsafe_evidence_fail(self) -> None:
        for bad in (
            "../outside.json",
            "C:/private.json",
            "/private.json",
            "a\\b",
            "https://example.org/a",
        ):
            self.data = self.make_fixture()
            self.data["builds"]["baseline"]["evidence"]["path"] = bad
            self.assertFalse(self.result()["passed"], bad)
        self.data = self.make_fixture()
        ref = self.data["builds"]["baseline"]["evidence"]
        (self.root / ref["path"]).write_text("{}")
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        self.data["builds"]["baseline"]["evidence"]["sha256"] = "0" * 64
        self.assertFalse(self.result()["passed"])
        self.data = self.make_fixture()
        self.data["evidence_kind"] = "synthetic"
        self.assertFalse(self.result()["passed"])


if __name__ == "__main__":
    unittest.main()

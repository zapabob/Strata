"""Synthetic gate fixtures are test inputs, never benchmark evidence."""
from __future__ import annotations
import copy
import unittest
from spin8_acceptance import evaluate


def fixture() -> dict:
    models = []
    for name in ("bonsai27b", "strata-q2_0"):
        model = dict(id=name, real_model_loaded=True, strict_graph_connected=True,
                     three_physical_k_views=True, runtime_transform_monitor_verified=True,
                     original_service_restored=True, cuda_architecture="sm_120", warmups=3,
                     paired=True, monitor_overhead_ratio=0.005,
                     quality=dict(candidate_mean_nll=2.001, baseline_mean_nll=2,
                                  new_fixed_case_failures=0), contexts=[])
        for count in (4096, 32768):
            pairs = [dict(baseline=dict(completion_tokens=100, decode_seconds=2, ttft_seconds=1),
                          candidate=dict(completion_tokens=100, decode_seconds=1.8, ttft_seconds=1.01))
                     for _ in range(10)]
            model["contexts"].append(dict(input_tokens=count, pairs=pairs))
        models.append(model)
    return dict(schema="strata-spin8-acceptance-v1", models=models)


class AcceptanceTest(unittest.TestCase):
    def test_complete_synthetic_evidence(self) -> None:
        self.assertTrue(evaluate(fixture())["passed"])

    def test_missing_model_cannot_pass(self) -> None:
        data = fixture(); data["models"].pop()
        self.assertFalse(evaluate(data)["passed"])

    def test_single_cache_cannot_pass_even_if_fast(self) -> None:
        data = fixture(); data["models"][0]["three_physical_k_views"] = False
        self.assertFalse(evaluate(data)["passed"])

    def test_each_missing_gate_fails(self) -> None:
        for field in ("strict_graph_connected", "runtime_transform_monitor_verified", "original_service_restored"):
            data = fixture(); del data["models"][0][field]
            self.assertFalse(evaluate(data)["passed"])

    def test_invalid_or_incomplete_pairs_fail(self) -> None:
        for value in (float("nan"), 0, -1, True, "fast"):
            data = fixture(); data["models"][0]["contexts"][0]["pairs"][0]["candidate"]["decode_seconds"] = value
            self.assertFalse(evaluate(data)["passed"])

    def test_quality_regression_fails(self) -> None:
        data = fixture(); data["models"][0]["quality"]["candidate_mean_nll"] = 2.02
        self.assertFalse(evaluate(data)["passed"])


if __name__ == "__main__":
    unittest.main()

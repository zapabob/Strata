"""CPU-only unit tests for PWS EDF deadline prefetch scheduler, negative controls, and TSI cert."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from pws.certificates import certify_pws_tsi_efficiency  # noqa: E402
from pws.deadline_scheduler import (  # noqa: E402
    IoTimingModel,
    PrefetchSchedulerConfig,
    simulate_deadline_prefetch,
)
from pws.trace import generate_random_negative_control_trace, generate_structured_moe_trace  # noqa: E402


class TestPwsDeadlineScheduler(unittest.TestCase):
    def test_edf_prefetch_reduces_exposed_stall_on_structured_trace(self) -> None:
        events = generate_structured_moe_trace(num_tokens=45, num_layers=6, num_experts=48, top_k=2)
        io_model = IoTimingModel(ssd_bandwidth_bytes_per_s=1.2e9, layer_compute_time_s=0.0012)
        budget = 40 * 1024 * 1024

        demand = simulate_deadline_prefetch(
            events,
            cache_budget_bytes=budget,
            io_model=io_model,
            config=PrefetchSchedulerConfig(enable_prefetch=False),
        )
        edf = simulate_deadline_prefetch(
            events,
            cache_budget_bytes=budget,
            io_model=io_model,
            config=PrefetchSchedulerConfig(enable_prefetch=True, layer_lookahead=2, min_confidence=0.25),
        )
        self.assertGreater(edf["prefetch_issued"], 0)
        self.assertGreater(edf["prefetch_hits"], 0)
        self.assertLess(edf["exposed_io_stall_ms_per_token"], demand["exposed_io_stall_ms_per_token"])
        self.assertIsNotNone(edf["read_latency_ms_p95"])

    def test_negative_control_random_trace_exposes_unused_prefetch_and_throttles(self) -> None:
        random_events = generate_random_negative_control_trace(num_tokens=45, num_layers=6, num_experts=48, top_k=2)
        io_model = IoTimingModel(ssd_bandwidth_bytes_per_s=1.2e9, layer_compute_time_s=0.0012)
        budget = 32 * 1024 * 1024

        edf_rand = simulate_deadline_prefetch(
            random_events,
            cache_budget_bytes=budget,
            io_model=io_model,
            config=PrefetchSchedulerConfig(
                enable_prefetch=True, layer_lookahead=3, min_confidence=0.10, adaptive_throttle=True
            ),
        )
        # On uniform random routing, lookahead should throttle down and unused prefetch bytes must be tracked!
        self.assertLessEqual(edf_rand["final_lookahead_after_throttle"], 2)
        self.assertGreater(edf_rand["bytes_breakdown"]["unused_prefetch_bytes"], 0)

    def test_pws_tsi_lossless_vs_lossy_certificates(self) -> None:
        lossless_ok = certify_pws_tsi_efficiency(
            optimisation_kind="lossless_cache_placement",
            p_ref=0.40, cost_ref_s=2.0, p_new=0.40, cost_new_s=1.4, bit_exact_parity_verified=True,
        )
        self.assertTrue(lossless_ok["improved"])

        lossless_unverified = certify_pws_tsi_efficiency(
            optimisation_kind="lossless_cache_placement",
            p_ref=0.40, cost_ref_s=2.0, p_new=0.40, cost_new_s=1.4, bit_exact_parity_verified=False,
        )
        self.assertFalse(lossless_unverified["improved"])
        self.assertEqual(lossless_unverified["status"], "parity_unverified")

        lossy_ok = certify_pws_tsi_efficiency(
            optimisation_kind="lossy_weight_approximation",
            p_ref=0.40, cost_ref_s=1.0, p_new=0.25, cost_new_s=0.5,
        )
        self.assertTrue(lossy_ok["improved"])


if __name__ == "__main__":
    unittest.main()

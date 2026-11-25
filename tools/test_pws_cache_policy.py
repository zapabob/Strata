"""CPU-only unit tests for PWS bandwidth models, Roofline, predictors, and 7 cache policies."""

from __future__ import annotations

from pathlib import Path
import struct
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from pws.bandwidth_model import (  # noqa: E402
    ActualSsdBytesBreakdown,
    dense_full_weight_streaming_bound,
    moe_cache_hit_requirement,
)
from pws.cache_policy import compare_all_cache_policies  # noqa: E402
from pws.expert_predictor import NKATSequencePredictor, greedy_knapsack_priority  # noqa: E402
from pws.roofline import MultiTierRooflineInput, evaluate_multitier_roofline  # noqa: E402
from pws.trace import (  # noqa: E402
    generate_random_negative_control_trace,
    generate_structured_moe_trace,
    load_strata_routing_trace,
)


class TestPwsBandwidthAndCachePolicy(unittest.TestCase):
    def test_section4_dense_and_section5_moe_numerical_examples(self) -> None:
        dense = dense_full_weight_streaming_bound(
            num_params=27e9, effective_bpw=3.69, ssd_bandwidths_gb_s=(3.5, 7.0, 14.0)
        )
        self.assertAlmostEqual(dense["weight_gb_decimal"], 12.45375, places=5)
        self.assertAlmostEqual(dense["ceilings"][0]["max_decode_tok_s"], 0.28104, places=3)
        self.assertAlmostEqual(dense["ceilings"][1]["max_decode_tok_s"], 0.56208, places=3)
        self.assertAlmostEqual(dense["ceilings"][2]["max_decode_tok_s"], 1.12416, places=3)

        moe = moe_cache_hit_requirement(
            active_params=3e9,
            effective_bpw=2.0,
            ssd_bandwidth_gb_s=3.5,
            target_decode_tok_s=30.0,
            probe_hit_rates=(0.90,),
        )
        self.assertAlmostEqual(moe["active_weight_mb"], 750.0, places=6)
        self.assertAlmostEqual(moe["allowable_ssd_mb_per_token"], 116.666667, places=3)
        self.assertAlmostEqual(moe["required_byte_hit_rate"], 0.844444, places=4)
        self.assertAlmostEqual(moe["probes"][0]["ideal_ssd_demand_mb_per_token"], 75.0, places=6)
        self.assertAlmostEqual(moe["probes"][0]["ssd_bandwidth_only_ceiling_tok_s"], 46.666667, places=3)

        brk = ActualSsdBytesBreakdown(
            demand_reads_bytes=100_000, unused_prefetch_bytes=20_000, alignment_overhead_bytes=5_000
        )
        self.assertEqual(brk.physical_total_bytes, 125_000)
        self.assertAlmostEqual(brk.read_amplification_factor or 0.0, 1.25, places=6)

    def test_section6_multitier_roofline_and_dag_ceiling(self) -> None:
        roof = evaluate_multitier_roofline(
            MultiTierRooflineInput(
                flops_per_token=6e9,
                vram_bytes_per_token=600e6,
                ram_bytes_per_token=150e6,
                pcie_bytes_per_token=75e6,
                ssd_bytes_per_token=75e6,
                gpu_flops_per_s=24e12,
                vram_bw_bytes_per_s=448e9,
                ram_bw_bytes_per_s=40e9,
                pcie_bw_bytes_per_s=12e9,
                ssd_bw_bytes_per_s=3.5e9,
                cpu_compute_s_per_token=0.015,
                exposed_io_stall_s_per_token=0.010,
            )
        )
        self.assertEqual(roof["binding_roofline_tier"], "ssd_bandwidth")
        self.assertTrue(roof["exceeds_roofline_impossible"])
        self.assertLess(roof["dag_estimated_tok_s"], roof["ideal_parallel_roofline_tok_s"])

    def test_nkat_predictor_distinguishes_noncommutative_order(self) -> None:
        pred = NKATSequencePredictor()
        # Train (1, 2) -> 5 and (2, 1) -> 9 repeatedly
        for _ in range(5):
            pred.observe(0, 1)
            pred.observe(0, 2)
            pred.observe(0, 5)
            pred.observe(0, 2)
            pred.observe(0, 1)
            pred.observe(0, 9)
        # After (1, 2) -> top prediction must be 5; after (2, 1) -> top prediction must be 9!
        pred.observe(0, 1)
        pred.observe(0, 2)
        self.assertEqual(pred.predict_probs(0, top_m=1)[0][0], 5)
        pred.observe(0, 2)
        pred.observe(0, 1)
        self.assertEqual(pred.predict_probs(0, top_m=1)[0][0], 9)
        self.assertAlmostEqual(greedy_knapsack_priority(0.5, 0.002, 1000), 1e-6, places=12)

    def test_seven_cache_policies_structured_vs_random_negative_control(self) -> None:
        structured = generate_structured_moe_trace(num_tokens=40, num_layers=6, num_experts=48, top_k=2)
        random_nc = generate_random_negative_control_trace(num_tokens=40, num_layers=6, num_experts=48, top_k=2)

        cmp_s = compare_all_cache_policies(structured, memory_budget_bytes=48 * 1024 * 1024)
        cmp_r = compare_all_cache_policies(random_nc, memory_budget_bytes=48 * 1024 * 1024)
        by_pol_s = {r["policy"]: r for r in cmp_s["policies"]}
        by_pol_r = {r["policy"]: r for r in cmp_r["policies"]}

        self.assertEqual(len(by_pol_s), 7)
        self.assertFalse(by_pol_s["offline_oracle"]["deployable_online"])
        self.assertTrue(by_pol_s["nkat_seq"]["deployable_online"])
        # Offline oracle must dominate or tie online policies on structured trace
        self.assertGreaterEqual(
            by_pol_s["offline_oracle"]["byte_weighted_hit_rate"],
            by_pol_s["lru"]["byte_weighted_hit_rate"] - 1e-6,
        )
        # Negative control: uniform random trace collapses online hit rates relative to structured trace
        self.assertLess(
            by_pol_r["nkat_seq"]["byte_weighted_hit_rate"],
            by_pol_s["nkat_seq"]["byte_weighted_hit_rate"],
        )

    def test_strata_dump_routing_binary_loader(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "routing.bin"
            # Two records: layer 0 k=2 (ids 3, 7) then layer 1 k=2 (ids 2, 5)
            blob = struct.pack("<iiiiiff", 0, 2, 3, 7, 0.6, 0.4) if False else (
                struct.pack("<ii2i2f", 0, 2, 3, 7, 0.6, 0.4)
                + struct.pack("<ii2i2f", 1, 2, 2, 5, 0.7, 0.3)
            )
            p.write_bytes(blob)
            evs = load_strata_routing_trace(p, n_layers=48, n_experts=512)
            self.assertEqual(len(evs), 4)
            self.assertEqual(evs[0].key, (0, 3))
            self.assertEqual(evs[3].key, (1, 5))


if __name__ == "__main__":
    unittest.main()

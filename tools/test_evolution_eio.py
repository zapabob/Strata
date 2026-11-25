"""CPU-only unit tests for Evolutionary Inference Optimisation (EIO, Phase 3 Revised)."""

from __future__ import annotations

from pathlib import Path
import random
import sys
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from evolution.archive import CandidateRecord, EvaluationCacheKey, ParetoArchive, dominates, select_parent_fitness_proportionate  # noqa: E402
from evolution.bandit import make_bandit  # noqa: E402
from evolution.certificates import certify_paired_speedup, search_amortisation_breakeven  # noqa: E402
from evolution.genome import InferenceGenome  # noqa: E402
from evolution.hardware_evolve import (  # noqa: E402
    RealEngineGenome,
    RealEvalOutcome,
    parse_engine_tps,
    run_real_hardware_evolution,
    verify_real_engine_genome,
)
from evolution.invariant_verifier import (  # noqa: E402
    build_robust_kbench_cuda_verification_plan,
    verify_genome_invariants,
    verify_hard_acceptance_gates,
)
from evolution.multi_fidelity import FidelityContext  # noqa: E402
from evolution.mutation import MUTATION_OPERATORS, apply_mutation  # noqa: E402
from evolution.shinka_adapter import EvolutionRunConfig, inspect_official_shinka_environment, run_evolutionary_search  # noqa: E402
from pws.trace import generate_structured_moe_trace  # noqa: E402


class TestEvolutionaryInferenceOptimisation(unittest.TestCase):
    def _valid_genome(self, **overrides: object) -> InferenceGenome:
        base: dict[str, object] = {
            "gpu_cache_budget_bytes": 24 * 1024 * 1024,
            "ram_cache_budget_bytes": 24 * 1024 * 1024,
            "cache_decay": 0.95,
            "eviction_hysteresis": 0.5,
            "prefetch_depth": 2,
            "prefetch_threshold": 0.25,
            "prefetch_queue_size": 4,
            "io_chunk_bytes": 524288,
            "staging_buffers": 2,
            "cache_policy": "lru",
        }
        base.update(overrides)
        return InferenceGenome(**base)  # type: ignore[arg-type]

    def test_level0_invariant_verifier_and_hard_gates(self) -> None:
        self.assertTrue(verify_genome_invariants(self._valid_genome()).passed)
        # Unaligned I/O chunk must fail Level-0 check
        bad_align = verify_genome_invariants(self._valid_genome(io_chunk_bytes=12345))
        self.assertFalse(bad_align.passed)
        # Excessive GPU cache exceeding 12 GiB safety cap must fail
        bad_vram = verify_genome_invariants(self._valid_genome(gpu_cache_budget_bytes=20 * 1024 ** 3))
        self.assertFalse(bad_vram.passed)

        # Hard gate refuses candidate failing numerical correctness regardless of speed
        g = verify_hard_acceptance_gates(
            numerical_correctness_pass=False,
            resource_guards_pass=True,
            model_integrity_pass=True,
            required_quality_pass=True,
            verifier_integrity_pass=True,
        )
        self.assertFalse(g["accepted_for_archive"])
        self.assertIn("numerical_correctness", g["failed_gates"])

        plan = build_robust_kbench_cuda_verification_plan(kernel_name="moe_gemv_sm120", binary_path="test.exe")
        self.assertFalse(plan["executed"])
        self.assertEqual(len(plan["sanitizer_commands"]), 3)

    def test_pareto_frontier_9tuple_cache_and_fitness_parent_selection(self) -> None:
        g1 = self._valid_genome(cache_policy="lru")
        g2 = self._valid_genome(cache_policy="nkat_seq")
        r_dom = CandidateRecord(g1, 0, 1, 2, True, 0.85, 5.0, 100.0, 40.0, 48_000_000, 0.01, "op")
        r_sub = CandidateRecord(g2, 0, 1, 2, True, 0.70, 9.0, 200.0, 25.0, 48_000_000, 0.01, "op")
        self.assertTrue(dominates(r_dom, r_sub))
        self.assertFalse(dominates(r_sub, r_dom))

        arch = ParetoArchive(min_novelty_distance=0.01)
        arch.add(r_dom)
        arch.add(r_sub)
        self.assertEqual(len(arch.pareto_frontier()), 1)
        self.assertEqual(arch.pareto_frontier()[0].genome.cache_policy, "lru")

        # 9-tuple cache keys with different driver versions must produce distinct digests
        k1 = EvaluationCacheKey("c", "m", "e", "cc", "drv1", "hw", "w", "v", "b").digest()
        k2 = EvaluationCacheKey("c", "m", "e", "cc", "drv2", "hw", "w", "v", "b").digest()
        self.assertNotEqual(k1, k2)

        picked = select_parent_fitness_proportionate([r_dom, r_sub], random.Random(7), temperature=0.2)
        self.assertIn(picked, (r_dom, r_sub))

    def test_all_five_bandits_and_noncommutative_mutation(self) -> None:
        for bname in ("uniform_random", "ucb1", "sliding_window_ucb", "thompson_sampling", "cost_aware_ucb"):
            b = make_bandit(bname, MUTATION_OPERATORS, seed=42)
            for step in range(10):
                arm = b.select()
                b.update(arm, improvement=0.5 if arm == 0 else 0.05, eval_cost_s=0.1)
            self.assertEqual(sum(b.counts), 10)

        parent = self._valid_genome()
        swapped = apply_mutation(
            "noncommutative_order_swap",
            parent,
            mate=None,
            rng=random.Random(1),
            max_gpu_budget_bytes=48 * 1024 * 1024,
            max_ram_budget_bytes=48 * 1024 * 1024,
        )
        self.assertNotEqual(swapped.operator_sequence, parent.operator_sequence)
        self.assertTrue(verify_genome_invariants(swapped).passed)

    def test_urt_speedup_certificate_and_amortisation(self) -> None:
        # Uncertified range R -> Hoeffding LCB must be None (uses bootstrap LCB instead)
        unbounded = certify_paired_speedup(
            [1.0, 1.02, 0.98, 1.01, 0.99, 1.0],
            [0.80, 0.81, 0.79, 0.82, 0.80, 0.79],
            range_width_R=None,
            range_width_R_certified=False,
            is_independent_holdout=True,
        )
        self.assertIsNone(unbounded["hoeffding_lcb_d"])
        self.assertTrue(unbounded["certified_speedup"])

        # Non-holdout search data cannot certify speedup
        non_hold = certify_paired_speedup(
            [1.0, 1.0, 1.0, 1.0], [0.5, 0.5, 0.5, 0.5], is_independent_holdout=False
        )
        self.assertFalse(non_hold["certified_speedup"])

        amort = search_amortisation_breakeven(
            search_wall_s=100.0, build_and_verify_s=50.0, delta_t_saved_per_token_s=0.003, expected_deployment_tokens=100_000
        )
        self.assertEqual(amort["break_even_tokens"], 50000)
        self.assertTrue(amort["cost_recovered_at_expected_usage"])

    def test_multi_island_evolution_train_vs_holdout_end_to_end(self) -> None:
        train = generate_structured_moe_trace(num_tokens=20, num_layers=4, num_experts=32, top_k=2, seed=11)
        holdout = generate_structured_moe_trace(num_tokens=20, num_layers=4, num_experts=32, top_k=2, seed=22)
        out = run_evolutionary_search(
            train_trace=train,
            holdout_trace=holdout,
            baseline_genome=self._valid_genome(prefetch_depth=0, cache_policy="lru"),
            run_cfg=EvolutionRunConfig(
                generations=6,
                num_islands=2,
                bandit_name="sliding_window_ucb",
                seed=42,
                max_gpu_budget_bytes=32 * 1024 * 1024,
                max_ram_budget_bytes=32 * 1024 * 1024,
            ),
            ctx=FidelityContext(ssd_bandwidth_bytes_per_s=800e6),
        )
        self.assertEqual(out["engine_kind"], "shinka_inspired_builtin")
        self.assertFalse(out["auto_adopted_into_default_inference"])
        self.assertGreaterEqual(out["pareto_frontier_size"], 1)
        self.assertIsNotNone(out["best_holdout_candidate"])
        deps = inspect_official_shinka_environment()
        self.assertIn("packages", deps)

    def test_real_hardware_evolution_parity_gate_and_holdout_cert(self) -> None:
        ok, errs = verify_real_engine_genome(RealEngineGenome(vram_reserve_mb=1536, cpu_pool_threads=6))
        self.assertTrue(ok)
        self.assertEqual(errs, [])
        # Violating WDDM VRAM reserve floor (<1536 MiB) must be rejected
        bad, errs_bad = verify_real_engine_genome(RealEngineGenome(vram_reserve_mb=512))
        self.assertFalse(bad)
        self.assertTrue(errs_bad)

        pp, tg = parse_engine_tps("prompt: 14.20 t/s | decode: 35.80 tok/s")
        self.assertAlmostEqual(pp or 0.0, 14.20, places=2)
        self.assertAlmostEqual(tg or 0.0, 35.80, places=2)

        def mock_eval(g: RealEngineGenome, prompt: str, ref_sha: str | None) -> RealEvalOutcome:
            # Candidate with ram_embd=1 & ssd_prefetch=0 simulates a verified 20% faster config;
            # candidate with q8_head_pack=0 simulates a broken parity candidate (must be REJECTED!)
            sha = "broken_sha" if g.q8_head_pack == 0 else f"sha_{hash(prompt) & 0xFFFF}"
            parity = True if ref_sha is None else (sha == ref_sha)
            tps = 36.0 if (g.ram_embd == 1 and g.ssd_prefetch == 0) else 30.0
            return RealEvalOutcome(g, 0, 1.0, tps, 15.0, sha, parity, 10_000, 10_000, parity, "ok" if parity else "mismatch")

        res = run_real_hardware_evolution(
            evaluator=mock_eval,
            baseline=RealEngineGenome(vram_reserve_mb=1536, ram_embd=0, q8_head_pack=1),
            search_prompt="search prompt",
            holdout_prompts=("h1", "h2", "h3", "h4"),
            budget_candidates=8,
            seed=42,
        )
        self.assertFalse(res["auto_adopted_into_default_inference"])
        self.assertTrue(res["holdout_all_bit_exact_parity"])
        self.assertGreaterEqual(res["holdout_candidate_median_decode_tps"], res["holdout_baseline_median_decode_tps"])


if __name__ == "__main__":
    unittest.main()

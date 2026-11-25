"""CPU-only tests for URT information geometry, GDN memory diagnostics, and VRE Theorems 1-7."""

from __future__ import annotations

import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from tsi.bellman import DiscreteMDP  # noqa: E402
from tsi.bellman_residual import (  # noqa: E402
    audit_tree_bellman_residuals,
    bellman_residual_success_bound,
    certify_controlled_discovery_rate,
    control_error_propagation_bound,
    unified_quantisation_control_bound,
)
from tsi.certificates import certify_quantisation_discovery_rate  # noqa: E402
from tsi.doob import (  # noqa: E402
    FiniteSearchTree,
    StepCandidate,
    TreeEdge,
    compute_committor,
    doob_conditioned_success_policy,
    rollout_policy_path_probs,
    select_step_candidates_gibbs,
    verify_doob_gibbs_equivalence,
)
from tsi.information import (  # noqa: E402
    binary_kl,
    compare_logits_dump_files,
    dpi_consistency_check,
    pinsker_success_lower_bound,
    sequence_kl_chain_rule,
)
from tsi.memory import analyse_gdn_trajectory, simulate_low_rank_residual_compensation  # noqa: E402
from tsi.phase_diagram import evaluate_phase_diagram, reference_four_path_ensemble  # noqa: E402
from tsi.proof_graph import verify_quotient_bellman_invariance  # noqa: E402
from tsi.variational import (  # noqa: E402
    feynman_kac_gibbs_ensemble,
    gibbs_functional_and_gap,
    gibbs_variational_binary,
    min_kl_information_cost,
)


class TestUrtInformationAndMemory(unittest.TestCase):
    def test_quantisation_certificate_refuses_non_certified_kl(self) -> None:
        # Must strictly REFUSE empirical_topk_kl, empirical_full_vocab_kl, estimated_sequence_kl!
        for bad_kind in ("empirical_topk_kl", "empirical_full_vocab_kl", "estimated_sequence_kl"):
            res = certify_quantisation_discovery_rate(
                p_ref=0.40, cost_ref=1.0, cost_quant=0.5, kl_value=0.01, kl_kind=bad_kind  # type: ignore[arg-type]
            )
            self.assertFalse(res["certified"])
            self.assertIn("refused", res["reason"].lower())

        # Must CERTIFY when certified_sequence_kl_upper_bound < binary_KL(0.40 || p_crit=0.225403)
        ok = certify_quantisation_discovery_rate(
            p_ref=0.40, cost_ref=1.0, cost_quant=0.5, kl_value=0.04, kl_kind="certified_sequence_kl_upper_bound"
        )
        self.assertTrue(ok["certified"])
        self.assertGreater(ok["margin_nats"], 0.0)

        # Must NOT certify if KL exceeds threshold
        too_large = certify_quantisation_discovery_rate(
            p_ref=0.40, cost_ref=1.0, cost_quant=0.5, kl_value=0.25, kl_kind="certified_sequence_kl_upper_bound"
        )
        self.assertFalse(too_large["certified"])

    def test_dpi_pinsker_chain_rule_and_logs_dump_adapter(self) -> None:
        dpi = dpi_consistency_check(0.60, 0.50, 0.05)
        self.assertTrue(dpi["dpi_satisfied"])
        self.assertAlmostEqual(pinsker_success_lower_bound(0.60, 0.08), 0.40, places=10)
        self.assertGreater(binary_kl(0.60, 0.50), 0.0)

        chain = sequence_kl_chain_rule(
            [[2.5, 1.0, -0.5, -1.2], [1.8, 0.9, 0.1, -0.8]],
            [[2.2, 1.2, -0.4, -1.0], [1.5, 1.0, 0.2, -0.7]],
            top_k=2,
        )
        self.assertTrue(chain["all_steps_within_range_bound"])
        self.assertLessEqual(chain["empirical_full_vocab_kl"], chain["shared_prefix_range_upper_bound"] + 1e-12)

        # Test native LOGS binary reader compatibility
        with tempfile.TemporaryDirectory() as td:
            p1, p2 = Path(td) / "ref.f32", Path(td) / "q.f32"
            p1.write_bytes(struct.pack("<4siii4f", b"LOGS", 0, 1, 4, 2.0, 1.0, 0.0, -1.0))
            p2.write_bytes(struct.pack("<4siii4f", b"LOGS", 0, 1, 4, 1.9, 1.1, 0.0, -0.9))
            cmp = compare_logits_dump_files(p1, p2, top_k=2)
            self.assertEqual(cmp["num_steps"], 1)
            self.assertTrue(cmp["all_steps_within_range_bound"])

    def test_gdn_trajectory_and_low_rank_compensation(self) -> None:
        alphas = [0.95, 0.92, 0.90]
        betas = [0.4, 0.5, 0.3]
        keys = [[1.0, 0.0, 0.0], [0.6, 0.8, 0.0], [0.0, 0.6, 0.8]]
        queries = [[1.0, 0.2, 0.0], [0.8, 0.5, 0.1], [0.5, 0.5, 0.2]]
        # Coherent identical error across time steps amplifies output energy relative to uncorrelated sum!
        err = [[0.1, 0.05, -0.02], [-0.04, 0.08, 0.03]]
        diag = analyse_gdn_trajectory(alphas=alphas, betas=betas, keys=keys, queries=queries, step_errors=[err, err, err])
        self.assertGreater(diag["max_key_non_orthogonality_abs_cos"], 0.5)
        self.assertGreater(diag["time_correlation_amplification_ratio"], 1.0)

        # Low-rank compensation aligned with top Gramian eigenvector reduces future readout energy!
        gram = [[4.0, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.01]]
        state = [[1.23, -0.47, 0.88], [-0.61, 0.34, -0.77]]
        sim = simulate_low_rank_residual_compensation(state_matrix=state, quant_step=0.25, gramian=gram, rank=1)
        self.assertLess(sim["gramian_error_energy_after"], sim["gramian_error_energy_before"])
        self.assertGreater(sim["gramian_energy_reduction_fraction"], 0.80)
        self.assertGreater(sim["extra_flops_per_step"], 0)


class TestVreTheorems1To7(unittest.TestCase):
    def _sample_tree(self) -> FiniteSearchTree:
        return FiniteSearchTree(
            root="u0",
            edges={
                "u0": [TreeEdge("A", "uA", 0.35, 1.0), TreeEdge("B", "uB", 0.65, 2.0)],
                "uA": [TreeEdge("ok", "ok1", 0.30, 1.5), TreeEdge("fail", "fail1", 0.70, 0.5)],
                "uB": [TreeEdge("ok", "ok2", 0.05, 3.0), TreeEdge("fail", "fail2", 0.95, 1.0)],
            },
            terminals={"ok1": 1.0, "fail1": 0.0, "ok2": 1.0, "fail2": 0.0},
        )

    def test_theorem1_min_kl_numerical_example(self) -> None:
        res = min_kl_information_cost(0.01, 0.90)
        self.assertAlmostEqual(res["min_kl_nats"], 3.820624, places=4)
        self.assertAlmostEqual(res["min_kl_bits"], 5.511995, places=3)
        self.assertAlmostEqual(res["full_success_kl_nats"], -math.log(0.01), places=5)
        self.assertFalse(min_kl_information_cost(0.0, 0.5)["achievable_with_finite_kl"])

    def test_theorem2_gibbs_variational_and_exact_gap(self) -> None:
        g = gibbs_variational_binary(0.05, 5.0)
        self.assertAlmostEqual(g["p_star"], 0.886508, places=5)
        self.assertLess(g["logit_shift_identity_err"], 1e-12)

        gap = gibbs_functional_and_gap(
            prior_probs=[0.5, 0.3, 0.15, 0.05],
            verified_rewards=[0.0, 0.0, 1.0, 1.0],
            candidate_probs=[0.2, 0.2, 0.4, 0.2],
            lam=2.5,
        )
        self.assertLess(gap["identity_abs_err"], 1e-12)
        self.assertGreaterEqual(gap["optimality_gap_direct"], 0.0)

    def test_theorem3_doob_feynman_kac_and_section10_cumulants(self) -> None:
        tree = self._sample_tree()
        eq = verify_doob_gibbs_equivalence(tree, lam=3.0, eta=0.4)
        self.assertTrue(eq["equivalent"])
        self.assertLess(eq["max_path_prob_abs_err"], 1e-12)

        # Lambda -> inf conditioning yields 100% verified probability
        cond_pol = doob_conditioned_success_policy(tree)
        cond_probs = rollout_policy_path_probs(tree, cond_pol)
        self.assertAlmostEqual(cond_probs["A/ok"] + cond_probs["B/ok"], 1.0, places=12)
        self.assertAlmostEqual(compute_committor(tree)["u0"], 0.35 * 0.30 + 0.65 * 0.05, places=12)

        # Finite-difference verification of Section 10 cumulant identities d(log Z)/d(lam), -d(log Z)/d(eta), Var, Cov
        paths = reference_four_path_ensemble()
        lam, eta, h = 4.0, 0.5, 1e-5
        base = feynman_kac_gibbs_ensemble(paths, lam=lam, eta=eta)
        d_lam = (
            feynman_kac_gibbs_ensemble(paths, lam=lam + h, eta=eta)["log_Z"]
            - feynman_kac_gibbs_ensemble(paths, lam=lam - h, eta=eta)["log_Z"]
        ) / (2 * h)
        d_eta = -(
            feynman_kac_gibbs_ensemble(paths, lam=lam, eta=eta + h)["log_Z"]
            - feynman_kac_gibbs_ensemble(paths, lam=lam, eta=eta - h)["log_Z"]
        ) / (2 * h)
        d2_lam = (
            feynman_kac_gibbs_ensemble(paths, lam=lam + h, eta=eta)["expected_verified_success"]
            - feynman_kac_gibbs_ensemble(paths, lam=lam - h, eta=eta)["expected_verified_success"]
        ) / (2 * h)
        d2_cross = -(
            feynman_kac_gibbs_ensemble(paths, lam=lam, eta=eta + h)["expected_verified_success"]
            - feynman_kac_gibbs_ensemble(paths, lam=lam, eta=eta - h)["expected_verified_success"]
        ) / (2 * h)
        self.assertAlmostEqual(base["expected_verified_success"], d_lam, places=6)
        self.assertAlmostEqual(base["expected_cost"], d_eta, places=6)
        self.assertAlmostEqual(base["var_verified_success"], d2_lam, places=5)
        self.assertAlmostEqual(base["cov_verified_cost"], d2_cross, places=5)

    def test_theorems4_5_6_and_section12_and_step_selector(self) -> None:
        # Theorem 4
        t4 = control_error_propagation_bound(p0=0.10, lam=4.0, step_log_h_errors=[0.05, 0.05, 0.05])
        self.assertAlmostEqual(t4["kl_upper_bound_nats"], 0.5 * 3 * 0.0025, places=8)

        # Theorem 5 numerical example: p0=5%, lam=5.0, L=1.0 -> 88.65% ideal, 74.18% guaranteed lower bound
        t5 = bellman_residual_success_bound(p0=0.05, lam=5.0, residual_oscillation_L=1.0, target_success_rate=0.70)
        self.assertAlmostEqual(t5["ideal_p_star"], 0.886508, places=4)
        self.assertAlmostEqual(t5["guaranteed_lower_bound"], 0.741844, places=4)
        self.assertTrue(t5["meets_target_under_bound"])

        # Theorem 5 exact tree telescoping & lower bound check
        tree = self._sample_tree()
        lam = 2.5
        approx_h = {
            "u0": 2.4,
            "uA": 4.2,
            "uB": 1.4,
            "ok1": math.exp(lam),
            "fail1": 1.0,
            "ok2": math.exp(lam),
            "fail2": 1.0,
        }
        audit = audit_tree_bellman_residuals(tree, approx_h, lam=lam)
        self.assertLess(audit["telescoping_max_abs_err"], 1e-12)
        self.assertTrue(audit["lower_bound_holds"])

        # Theorem 6 unified quantisation + control bound
        t6 = unified_quantisation_control_bound(p_ref_star=0.85, logit_spans_r=[0.1, 0.1], control_log_errors_eps=[0.05, 0.05])
        self.assertAlmostEqual(t6["kl_upper_bound_nats"], (2 * 0.2 ** 2) / 8.0, places=8)

        # Section 12 unified discovery-rate control criterion
        c12 = certify_controlled_discovery_rate(
            p0=0.05, cost_uncontrolled=1.0, cost_controlled=2.0, lam=4.0, residual_oscillation_L=0.5, assumptions_certified=True
        )
        self.assertTrue(c12["certified_improvement"])

        # Step-level Gibbs selector favours immediately verified candidate
        sel = select_step_candidates_gibbs(
            [
                StepCandidate("c1", 0.5, 0.4, 2.0, verified_immediately=False),
                StepCandidate("c2", 0.5, 1.0, 2.5, verified_immediately=True),
            ],
            lam=3.0,
            eta=0.1,
        )
        self.assertEqual(sel["selected_candidate_id"], "c2")

    def test_theorem7_bisimulation_invariance_and_phase_diagram(self) -> None:
        # u1 and u2 have identical action costs and identical transition probabilities -> merge into one class!
        # u3 looks like the same visible goal but has different KV-context transition probability -> MUST NOT merge!
        mdp = DiscreteMDP(
            states=("u1", "u2", "u3", "verified", "fail"),
            verified_states=frozenset({"verified"}),
            actions=("step",),
            action_costs={"step": 1},
            transitions={
                ("u1", "step"): [("verified", 0.6), ("fail", 0.4)],
                ("u2", "step"): [("verified", 0.6), ("fail", 0.4)],
                ("u3", "step"): [("verified", 0.2), ("fail", 0.8)],
                ("fail", "step"): [("fail", 1.0)],
            },
        )
        inv = verify_quotient_bellman_invariance(mdp, max_budget=3)
        self.assertTrue(inv["theorem7_invariance_holds"])
        self.assertEqual(inv["original_state_count"], 5)
        self.assertEqual(inv["quotient_state_count"], 4)

        pd = evaluate_phase_diagram(reference_four_path_ensemble(), lambdas=(0.0, 2.0, 4.0), etas=(0.0, 0.5))
        self.assertEqual(len(pd["points"]), 6)


if __name__ == "__main__":
    unittest.main()

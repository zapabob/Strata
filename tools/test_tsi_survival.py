"""CPU-only unit tests for TSI stopping-time survival, discovery rate, robust adoption, and scaling."""

from __future__ import annotations

import math
from pathlib import Path
import sys
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from tsi.discovery_rate import (  # noqa: E402
    TrialCostBreakdown,
    asymptotic_discovery_rate,
    check_robust_adoption,
    compare_quantised_discovery_rate,
    critical_quantised_success_rate,
    independent_trial_success_curve,
    jensen_pass_at_k_audit,
)
from tsi.scaling import fit_weibull_scaling, weibull_success_model  # noqa: E402
from tsi.survival import (  # noqa: E402
    StoppingObservation,
    analyse_stopping_times,
    hoeffding_simultaneous_lower_bound,
    restricted_mean_time_to_success,
)


class TestTsiSurvivalAndDiscoveryRate(unittest.TestCase):
    def test_rmst_exact_step_integral_and_censoring_retention(self) -> None:
        # 4 tasks with stopping times: 100, 200, censored/failed (>400), censored/timeout (>400)
        obs = [
            StoppingObservation("q1", True, 100.0, 100.0, False, 400.0),
            StoppingObservation("q2", True, 200.0, 200.0, False, 400.0),
            StoppingObservation("q3", False, None, 400.0, True, 400.0),
            StoppingObservation("q4", False, None, 400.0, True, 400.0),
        ]
        # Exact identity: RMST(400) = (100 + 200 + 400 + 400) / 4 = 275.0
        rmst = restricted_mean_time_to_success(obs, b_max=400.0)
        self.assertAlmostEqual(rmst, 275.0, places=10)

        summary = analyse_stopping_times(
            obs,
            budget_grid=(100.0, 200.0, 400.0),
            axis_name="tokens",
            curve_type="continuous_policy",
            delta=0.50,
            alpha=0.05,
        )
        self.assertEqual(summary["censored_trials"], 2)
        self.assertEqual(summary["unsuccessful_trials"], 2)
        self.assertIsNone(summary["infinite_horizon_expected_cost"])
        self.assertAlmostEqual(summary["rmst_at_b_max"], 275.0, places=6)
        self.assertAlmostEqual(summary["curve"][0]["success_probability"], 0.25, places=6)
        self.assertAlmostEqual(summary["curve"][1]["success_probability"], 0.50, places=6)
        self.assertEqual(summary["empirical_b_star_grid"]["min_tested_budget_attained"], 200)

    def test_hoeffding_simultaneous_lower_bound(self) -> None:
        lb = hoeffding_simultaneous_lower_bound(0.80, n_tasks=100, num_budgets=4, alpha=0.05)
        expected = 0.80 - math.sqrt(math.log(4.0 / 0.05) / 200.0)
        self.assertAlmostEqual(lb, expected, places=12)

    def test_phase2_section4_numerical_discovery_rate_example(self) -> None:
        # Exact theoretical test case from Phase 2 Section 4 (not a hardware measurement)
        p_crit = critical_quantised_success_rate(0.40, 1.0, 0.5)
        self.assertAlmostEqual(p_crit, 1.0 - math.sqrt(0.60), places=12)
        self.assertAlmostEqual(p_crit, 0.22540333, places=6)

        cmp = compare_quantised_discovery_rate(
            p_ref=0.40, cost_ref=1.0, p_quant=0.25, cost_quant=0.5, finite_budgets=(3.0,)
        )
        self.assertTrue(cmp["asymptotic_quant_exceeds_ref"])
        self.assertTrue(cmp["p_quant_exceeds_p_crit"])
        b3 = cmp["finite_budget_model_comparison"][0]
        self.assertAlmostEqual(b3["reference_success_model"], 0.784, places=6)
        self.assertAlmostEqual(b3["quantised_success_model"], 0.822021, places=5)
        self.assertGreater(
            asymptotic_discovery_rate(0.25, 0.5),
            asymptotic_discovery_rate(0.40, 1.0),
        )
        self.assertAlmostEqual(independent_trial_success_curve(0.40, 1.0, 3.0), 0.784, places=10)

    def test_full_trial_cost_breakdown_and_robust_adoption(self) -> None:
        cb = TrialCostBreakdown(
            prefill_s=0.15, decode_s=0.80, model_switch_s=0.20,
            context_rebuild_s=0.05, retry_s=0.30, verify_s=0.04,
            counterexample_s=0.10, init_s=0.06,
        )
        self.assertAlmostEqual(cb.total_cost_s, 1.70, places=10)

        pos = check_robust_adoption(p_ref_upper=0.40, p_quant_lower=0.30, rho_upper=0.50)
        self.assertTrue(pos["certified_improvement"])

        neg = check_robust_adoption(p_ref_upper=0.45, p_quant_lower=0.20, rho_upper=0.60)
        self.assertFalse(neg["certified_improvement"])
        self.assertEqual(neg["status"], "not_certified_not_disqualified")

    def test_jensen_pass_at_k_heterogeneity(self) -> None:
        # 50% easy (p=0.9), 50% hard (p=0.1) -> mean pass@1 = 0.5
        audit = jensen_pass_at_k_audit([0.9, 0.1], k=4)
        self.assertTrue(audit["inequality_holds"])
        self.assertGreater(audit["jensen_overestimation_gap"], 0.25)
        self.assertLess(audit["exact_heterogeneous_pass_at_k"], audit["naive_homogeneous_upper_bound"])

    def test_weibull_scaling_hypothesis_fitter(self) -> None:
        budgets = [64.0, 128.0, 256.0, 512.0, 1024.0]
        true_rates = [weibull_success_model(b, s_inf=0.85, b0=220.0, beta=1.2) for b in budgets]
        held_b = [1536.0, 2048.0]
        held_r = [weibull_success_model(b, s_inf=0.85, b0=220.0, beta=1.2) for b in held_b]

        fit = fit_weibull_scaling(budgets, true_rates, heldout_budgets=held_b, heldout_rates=held_r)
        self.assertLess(fit["train_rmse"], 0.02)
        self.assertIsNotNone(fit["jackknife_parameter_ranges"])
        self.assertIsNotNone(fit["heldout_prediction"])
        self.assertLess(fit["heldout_prediction"]["rmse"], 0.03)


if __name__ == "__main__":
    unittest.main()

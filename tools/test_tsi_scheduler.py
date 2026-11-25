"""CPU-only tests for optimal restart, Bellman DP, ResearchState, and adaptive/VRE scheduler."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from tsi.bellman import (  # noqa: E402
    DiscreteMDP,
    evaluate_policy_dp,
    max_transition_tv_distance,
    optimal_restart_cutoff,
    solve_bellman_dp,
)
from tsi.certificates import policy_stability_certificate  # noqa: E402
from tsi.client import LocalOpenAIClient  # noqa: E402
from tsi.research_state import ResearchAction, ResearchState, VerifiedLemma  # noqa: E402
from tsi.scheduler import PrecisionEscalationGate, SchedulerConfig, run_adaptive_task  # noqa: E402
from tsi.tasks import get_builtin_suite  # noqa: E402
from tsi.verifier import VerificationLevel  # noqa: E402


class TestBellmanRestartAndResearchState(unittest.TestCase):
    def test_optimal_restart_cutoff_heavy_tail_beats_no_restart(self) -> None:
        # 50% solved by t=1.0, remaining 50% stall until t=100.0 -> restarting at t=1.0 saves massive expected cost!
        res = optimal_restart_cutoff([(1.0, 0.50), (100.0, 1.0)], restart_overhead_c0=0.2)
        self.assertAlmostEqual(res["optimal_cutoff_b_star"], 1.0, places=6)
        # L(1.0) = (0.2 + 1.0) / 0.5 = 2.4 vs L(100.0) = (0.2 + 1.0 + 0.5*99) / 1.0 = 50.7
        self.assertAlmostEqual(res["min_expected_discovery_cost"], 2.4, places=6)

    def test_exact_bellman_dp_and_section10_tv_stability_bound(self) -> None:
        mdp_true = DiscreteMDP(
            states=("start", "lemma", "verified", "dead"),
            verified_states=frozenset({"verified"}),
            actions=("direct", "build_lemma"),
            action_costs={"direct": 1, "build_lemma": 1},
            transitions={
                ("start", "direct"): [("verified", 0.30), ("dead", 0.70)],
                ("start", "build_lemma"): [("lemma", 0.80), ("dead", 0.20)],
                ("lemma", "direct"): [("verified", 0.85), ("dead", 0.15)],
                ("lemma", "build_lemma"): [("lemma", 1.0)],
                ("dead", "direct"): [("dead", 1.0)],
                ("dead", "build_lemma"): [("dead", 1.0)],
            },
        )
        # Perturbed estimated MDP with bounded TV error eps <= 0.08
        mdp_est = DiscreteMDP(
            states=mdp_true.states,
            verified_states=mdp_true.verified_states,
            actions=mdp_true.actions,
            action_costs=mdp_true.action_costs,
            transitions={
                ("start", "direct"): [("verified", 0.38), ("dead", 0.62)],
                ("start", "build_lemma"): [("lemma", 0.72), ("dead", 0.28)],
                ("lemma", "direct"): [("verified", 0.78), ("dead", 0.22)],
                ("lemma", "build_lemma"): [("lemma", 1.0)],
                ("dead", "direct"): [("dead", 1.0)],
                ("dead", "build_lemma"): [("dead", 1.0)],
            },
        )
        eps = max_transition_tv_distance(mdp_true, mdp_est)
        self.assertAlmostEqual(eps, 0.08, places=6)

        dp_true = solve_bellman_dp(mdp_true, max_budget=2)
        dp_est = solve_bellman_dp(mdp_est, max_budget=2)
        # At budget=2, building lemma then solving gives 0.80 * 0.85 = 0.68 > 0.30!
        self.assertAlmostEqual(dp_true["values"][2]["start"], 0.68, places=10)
        self.assertEqual(dp_true["policy"][2]["start"], "build_lemma")

        eval_est_in_true = evaluate_policy_dp(mdp_true, dp_est["policy"], max_budget=2)
        gap = dp_true["values"][2]["start"] - eval_est_in_true[2]["start"]
        cert = policy_stability_certificate(eps, horizon_steps=2)
        self.assertTrue(cert["coupling_tighter_or_equal"])
        self.assertLessEqual(gap, cert["coupling_optimality_gap_bound"] + 1e-12)
        self.assertLessEqual(cert["coupling_optimality_gap_bound"], cert["linear_optimality_gap_bound"] + 1e-12)

    def test_research_state_noncommutativity_and_verified_lemma_isolation(self) -> None:
        with self.assertRaises(ValueError):
            VerifiedLemma("L0", "unverified guess", VerificationLevel.UNVERIFIED, "none")

        s1 = ResearchState(["G"], {"model": "m"}, 500, 60.0, None)
        s1.apply_action(action=ResearchAction.GENERATE_LEMMA, cost_tokens=50, cost_wall_s=0.5)
        s1.apply_action(action=ResearchAction.VERIFY_CANDIDATE, cost_tokens=50, cost_wall_s=0.5)

        s2 = ResearchState(["G"], {"model": "m"}, 500, 60.0, None)
        s2.apply_action(action=ResearchAction.VERIFY_CANDIDATE, cost_tokens=50, cost_wall_s=0.5)
        s2.apply_action(action=ResearchAction.GENERATE_LEMMA, cost_tokens=50, cost_wall_s=0.5)

        self.assertNotEqual(s1.state_digest(), s2.state_digest())

    def test_precision_escalation_four_gates(self) -> None:
        blocked = PrecisionEscalationGate(allow_escalation=True, target_model_present=True, user_approved=False)
        ok, reason = blocked.can_escalate(60.0)
        self.assertFalse(ok)
        self.assertEqual(reason, "user_approval_missing")

        allowed = PrecisionEscalationGate(
            allow_escalation=True,
            target_model_present=True,
            user_approved=True,
            free_ram_bytes=8 * 1024 ** 3,
            free_vram_bytes=4 * 1024 ** 3,
            switch_cost_s=5.0,
        )
        ok2, _ = allowed.can_escalate(60.0)
        self.assertTrue(ok2)


class TestAdaptiveAndVreSchedulerIntegration(unittest.TestCase):
    def test_adaptive_recovery_timeout_disconnect_and_budget_exhaustion(self) -> None:
        calls = {"n": 0, "behavior": "wrong_then_right"}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                return

            def do_POST(self) -> None:  # noqa: N802
                calls["n"] += 1
                length = int(self.headers.get("Content-Length", "0"))
                req = json.loads(self.rfile.read(length).decode("utf-8"))
                beh = calls["behavior"]
                if beh == "disconnect":
                    self.send_response(503)
                    self.end_headers()
                    return
                if beh == "timeout":
                    time.sleep(1.5)
                    self.send_response(200)
                    self.end_headers()
                    return
                if beh == "wrong_then_right":
                    content = "\\boxed{999}" if calls["n"] == 1 else "\\boxed{9}"
                    comp = 40
                else:
                    content = "Still thinking without final marker..."
                    comp = int(req.get("max_tokens", 64))

                body = json.dumps(
                    {
                        "id": "mock",
                        "model": "mock-sched",
                        "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop" if beh == "wrong_then_right" else "length"}],
                        "usage": {"prompt_tokens": 20, "completion_tokens": comp, "total_tokens": 20 + comp},
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{srv.server_port}"
            task = get_builtin_suite("dev")[0]  # 7^100 mod 13 == 9

            # 1. Wrong answer -> failure-guided counterexample retry -> verified!
            res_ok = run_adaptive_task(
                client=LocalOpenAIClient(url, timeout_s=5.0),
                task=task,
                model="mock-sched",
                config=SchedulerConfig(mode="adaptive", total_token_budget=256, max_steps=3),
            )
            self.assertTrue(res_ok.verified)
            self.assertEqual(res_ok.termination_reason, "verified_success")
            self.assertEqual(len(res_ok.attempts_log), 2)
            self.assertEqual(res_ok.cumulative_completion_tokens, 80)
            self.assertEqual(len(res_ok.research_state_snapshot["failed_attempts"]), 1)
            self.assertEqual(len(res_ok.research_state_snapshot["verified_lemmas"]), 1)

            # 2. Step-level VRE mode recovers on branch 2
            calls["n"] = 0
            res_vre = run_adaptive_task(
                client=LocalOpenAIClient(url, timeout_s=5.0),
                task=task,
                model="mock-sched",
                config=SchedulerConfig(mode="vre", total_token_budget=256, max_steps=2, vre_branch_candidates=2),
            )
            self.assertTrue(res_vre.verified)
            self.assertEqual(res_vre.policy_label, "step_level_vre_heuristic")

            # 3. Graceful budget exhaustion
            calls["n"] = 0
            calls["behavior"] = "always_truncate"
            res_exh = run_adaptive_task(
                client=LocalOpenAIClient(url, timeout_s=5.0),
                task=task,
                model="mock-sched",
                config=SchedulerConfig(mode="adaptive", total_token_budget=64, max_steps=4),
            )
            self.assertFalse(res_exh.verified)
            self.assertEqual(res_exh.termination_reason, "token_budget_exhausted")

            # 4. API disconnect handled cleanly without crash
            calls["n"] = 0
            calls["behavior"] = "disconnect"
            res_disc = run_adaptive_task(
                client=LocalOpenAIClient(url, timeout_s=5.0),
                task=task,
                model="mock-sched",
                config=SchedulerConfig(mode="adaptive", total_token_budget=128, max_steps=4),
            )
            self.assertFalse(res_disc.verified)
            self.assertEqual(res_disc.termination_reason, "api_disconnected")

            # 5. Timeout handled cleanly
            calls["n"] = 0
            calls["behavior"] = "timeout"
            res_to = run_adaptive_task(
                client=LocalOpenAIClient(url, timeout_s=1.0),
                task=task,
                model="mock-sched",
                config=SchedulerConfig(mode="adaptive", total_token_budget=128, max_steps=1, max_wall_seconds=3.0),
            )
            self.assertFalse(res_to.verified)
            self.assertEqual(res_to.final_outcome, "timeout_error")
        finally:
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main()

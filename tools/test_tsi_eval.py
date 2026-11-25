"""CPU-only unit tests, security AST tests, and mock OpenAI API integration tests for TSI."""

from __future__ import annotations

import ast
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
from typing import Any
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from tsi import DEFAULT_API_BASE_URL, TSI_RECORD_SCHEMA_VERSION, TSI_SCHEMA_VERSION  # noqa: E402
from tsi.client import LocalOpenAIClient, validate_base_url  # noqa: E402
from tsi.math_foundations import (  # noqa: E402
    bonferroni_alpha,
    clopper_pearson_interval,
    finite_budget_attainment,
    fisher_kl_quadratic,
    full_vocab_kl,
    gdn_transition_matrix,
    hankel_singular_values,
    mat_mul,
    noncommutative_transition_product,
    range_kl_upper_bound,
    run_self_checks,
    sylvester_so8_rotation,
    topk_renormalized_kl,
    urt_observability_gramians,
    weighted_frobenius_objective,
    wilson_interval,
)
from tsi.metrics import build_section16_trial_record, sanitise_public_text  # noqa: E402
from tsi.runner import RunConfig, compare_runs, run_evaluation  # noqa: E402
from tsi.tasks import (  # noqa: E402
    MathTask,
    extract_candidate_answer,
    get_builtin_suite,
    load_tasks_file,
    verify_response,
)
from tsi.verifier import VerificationLevel, verify_lean4_proof  # noqa: E402
import tsi_eval  # noqa: E402


class _MockOpenAIState:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.requests: list[dict[str, Any]] = []


def _start_mock_server(mode: str) -> tuple[ThreadingHTTPServer, threading.Thread, _MockOpenAIState]:
    state = _MockOpenAIState(mode=mode)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/v1/models":
                body = json.dumps({"object": "list", "data": [{"id": f"mock-{state.mode}"}]}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/chat/completions":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(length).decode("utf-8"))
            state.requests.append(req)
            max_toks = int(req.get("max_tokens", 128))
            user_prompt = req["messages"][-1]["content"]

            finish_reason = "stop"
            comp_toks = min(max_toks, 24)
            content = "I am unsure."

            if "7^100" in user_prompt:
                if max_toks < 128:
                    content = "Working through powers of 7 mod 13..."
                    finish_reason = "length"
                    comp_toks = max_toks
                else:
                    content = "By Fermat's little theorem 7^12 = 1 (mod 13), so 7^100 = 7^4 = \\boxed{9}."
            elif "phi(360)" in user_prompt:
                content = (
                    "360 = 2^3 * 3^2 * 5, so phi(360) = \\boxed{96}."
                    if state.mode == "reference"
                    else "Calculating gives \\boxed{92}."
                )
            elif "mod 7" in user_prompt:
                content = "FINAL_ANSWER: 23"
            elif "Tr(A B)" in user_prompt:
                content = "The value is \\boxed{18}."
            elif "commutator AB - BA" in user_prompt:
                content = "Top-left entry is \\boxed{3}."
            elif "C(10, 4)" in user_prompt:
                content = "Binomial coefficient is \\boxed{210}."
            elif "equals 9" in user_prompt:
                content = "Exact probability is \\boxed{\\frac{1}{9}}."
            elif "3*x^2 + 2*x + 1" in user_prompt:
                content = "Integral equals \\boxed{14}."
            elif "x^3 - x" in user_prompt:
                content = "Integral equals \\boxed{63/4}."
            elif "r = 4/5" in user_prompt:
                content = "r^2 / 8 = \\boxed{2/25}."
            elif "n^2 + n + 41" in user_prompt:
                content = "Counterexample: \\boxed{40}."
            elif "7*x - 5*y = 1" in user_prompt:
                content = (
                    "One valid pair is \\boxed{3,4}."
                    if state.mode == "reference"
                    else "We could test small integers such as x=3 and y=4."
                )

            resp = {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "model": req.get("model") or f"mock-{state.mode}",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": 32,
                    "completion_tokens": comp_toks,
                    "total_tokens": 32 + comp_toks,
                },
                "timings": {
                    "prompt_per_second": 120.5,
                    "predicted_per_second": 42.0 if state.mode == "reference" else 55.0,
                },
            }
            body = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, state


class TestTsiMathFoundations(unittest.TestCase):
    def test_self_checks_pass(self) -> None:
        audit = run_self_checks()
        self.assertTrue(audit["pass"])
        self.assertLess(audit["gramian_rollout_abs_err"], 1e-12)
        self.assertLess(audit["so8_orthogonality_err"], 1e-14)
        self.assertLessEqual(audit["kl_large_full_vocab"], audit["kl_large_range_bound"] + 1e-15)

    def test_noncommutative_product_order(self) -> None:
        a1 = gdn_transition_matrix(0.9, 0.5, [1.0, 0.0])
        a2 = gdn_transition_matrix(0.8, 0.7, [0.6, 0.8])
        phi = noncommutative_transition_product([a1, a1, a2], start_after_j=0, end_t=2)
        expected = mat_mul(a2, a1)
        wrong_order = mat_mul(a1, a2)
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(phi[i][j], expected[i][j], places=12)
        diff = sum(abs(phi[i][j] - wrong_order[i][j]) for i in range(2) for j in range(2))
        self.assertGreater(diff, 0.01)

    def test_urt_gramian_and_hankel(self) -> None:
        ts = [gdn_transition_matrix(0.9, 0.3, [1.0, 0.0]), gdn_transition_matrix(0.8, 0.5, [0.0, 1.0])]
        qs = [[1.0, 2.0], [-0.5, 1.5]]
        grams = urt_observability_gramians(ts, qs)
        self.assertEqual(len(grams), 2)
        self.assertAlmostEqual(grams[0][0][1], grams[0][1][0], places=12)
        sv = hankel_singular_values([[1.0, 0.0], [0.0, 3.0]], [[2.0, 0.0], [0.0, 1.0]])
        self.assertAlmostEqual(sv[0], 3.0, places=10)
        self.assertAlmostEqual(sv[1], 2.0, places=10)

    def test_kl_full_vs_topk_and_bound(self) -> None:
        z_ref = [3.0, 2.0, 1.0, 0.0, -1.0]
        z_q = [2.6, 2.3, 0.7, 0.5, -1.2]
        full = full_vocab_kl(z_ref, z_q)
        top2 = topk_renormalized_kl(z_ref, z_q, top_k=2)
        quad = fisher_kl_quadratic(z_ref, z_q)
        bound = range_kl_upper_bound(z_ref, z_q)
        self.assertLessEqual(full, bound + 1e-15)
        self.assertGreater(quad, 0.0)
        self.assertNotAlmostEqual(full, top2, places=3)

    def test_statistics_and_finite_attainment(self) -> None:
        w_lo, w_hi = wilson_interval(8, 10)
        cp_lo, cp_hi = clopper_pearson_interval(8, 10)
        self.assertLess(cp_lo, w_lo)
        self.assertGreater(cp_hi, w_hi)
        self.assertAlmostEqual(bonferroni_alpha(0.05, 4), 0.0125)
        att = finite_budget_attainment({64: 0.5, 256: 0.85, 512: 0.9}, delta=0.20)
        self.assertTrue(att["achieved_within_tested_budgets"])
        self.assertEqual(att["min_tested_budget_attained"], 256)
        unatt = finite_budget_attainment({64: 0.5, 256: 0.75}, delta=0.10)
        self.assertFalse(unatt["achieved_within_tested_budgets"])
        self.assertIsNone(unatt["min_tested_budget_attained"])

    def test_spin8_weighted_objective(self) -> None:
        rot = sylvester_so8_rotation()
        w = [[float(i == j) for j in range(8)] for i in range(8)]
        wq = [[val + (0.1 if i == 0 and j == 0 else 0.0) for j, val in enumerate(row)] for i, row in enumerate(w)]
        obj = weighted_frobenius_objective(w, wq, rot, rot)
        self.assertAlmostEqual(obj, 0.01, places=12)


class TestTsiTasksVerifiersAndSecurity(unittest.TestCase):
    def test_all_four_splits_disjoint_and_ground_truth_verifies(self) -> None:
        dev = get_builtin_suite("dev")
        cal = get_builtin_suite("calibration")
        val = get_builtin_suite("validation")
        hold = get_builtin_suite("frozen-holdout")
        self.assertEqual(len(dev), 12)
        self.assertEqual(len(cal), 4)
        self.assertEqual(len(val), 4)
        self.assertEqual(len(hold), 8)
        all_tasks = dev + cal + val + hold
        all_ids = [t.task_id for t in all_tasks]
        self.assertEqual(len(all_ids), len(set(all_ids)))

        known_answers = {
            "core-nt-01": ("\\boxed{9}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-nt-02": ("\\boxed{96}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-nt-03": ("FINAL_ANSWER: 23", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-la-01": ("\\boxed{18}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-la-02": ("\\boxed{3}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-comb-01": ("\\boxed{210}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-comb-02": ("\\boxed{\\frac{1}{9}}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-calc-01": ("\\boxed{14}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-calc-02": ("\\boxed{63/4}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-prob-01": ("\\boxed{2/25}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "core-ce-01": ("\\boxed{41}", VerificationLevel.NUMERICAL_CERTIFICATE_VERIFIED),
            "core-ce-02": ("\\boxed{3,4}", VerificationLevel.NUMERICAL_CERTIFICATE_VERIFIED),
            "cal-nt-01": ("\\boxed{2}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "cal-alg-01": ("\\boxed{1,2,3}", VerificationLevel.DETERMINISTIC_TEST_VERIFIED),
            "cal-comb-01": ("\\boxed{42}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "cal-calc-01": ("\\boxed{30}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "val-nt-01": ("\\boxed{18}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "val-alg-01": ("\\boxed{-2,7}", VerificationLevel.DETERMINISTIC_TEST_VERIFIED),
            "val-la-01": ("\\boxed{17}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "val-prob-01": ("\\boxed{7/8}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-nt-01": ("\\boxed{5}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-nt-02": ("\\boxed{195}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-la-01": ("\\boxed{10}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-la-02": ("\\boxed{1/8}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-comb-01": ("\\boxed{9}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-calc-01": ("\\boxed{58}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-info-01": ("\\boxed{1/2}", VerificationLevel.EXACT_ANSWER_VERIFIED),
            "hold-ce-01": ("\\boxed{2,3}", VerificationLevel.NUMERICAL_CERTIFICATE_VERIFIED),
        }
        for task in all_tasks:
            ans, expected_level = known_answers[task.task_id]
            res = verify_response(task, ans, finish_reason="stop")
            self.assertTrue(res.verified, f"Ground truth failed for {task.task_id}: {res}")
            self.assertEqual(res.outcome, "verified_pass")
            self.assertEqual(res.verification_level, expected_level)

    def test_failure_taxonomy_verifier_error_and_lean_guardrails(self) -> None:
        task = get_builtin_suite("dev")[0]
        res_inj = verify_response(task, "\\boxed{__import__('os').system('echo pwned')}", finish_reason="stop")
        self.assertFalse(res_inj.verified)
        self.assertEqual(res_inj.outcome, "format_error")
        self.assertEqual(res_inj.verification_level, VerificationLevel.UNVERIFIED)

        self.assertEqual(verify_response(task, "Step 1...", finish_reason="length").outcome, "truncated_budget")
        self.assertEqual(verify_response(task, "Maybe nine.", finish_reason="stop").outcome, "unverified_no_answer")
        self.assertEqual(verify_response(task, "\\boxed{10}", finish_reason="stop").outcome, "verified_fail")
        self.assertEqual(verify_response(task, "", timed_out=True).outcome, "timeout_error")
        self.assertEqual(verify_response(task, "", api_error="connection reset").outcome, "api_error")
        self.assertEqual(extract_candidate_answer("\\boxed{\\frac{3}{4}}"), ("\\frac{3}{4}", "boxed"))

        # Verifier fault must be caught cleanly as verifier_error, not unhandled crash
        bad_task = MathTask("bad-1", "test", "dev", "custom", "p", "nonexistent_verifier", {}, "")
        res_fault = verify_response(bad_task, "\\boxed{1}", finish_reason="stop")
        self.assertFalse(res_fault.verified)
        self.assertEqual(res_fault.outcome, "verifier_error")

        # Lean 4 verifier rejects sorry, unauthorised axiom, missing signature, and missing binary
        sig = "theorem add_comm_nat (a b : Nat) : a + b = b + a"
        r_sorry = verify_lean4_proof(proof_text=f"{sig} := by sorry", required_theorem_signature=sig)
        self.assertFalse(r_sorry.verified)
        self.assertEqual(r_sorry.verification_level, VerificationLevel.UNVERIFIED)

        r_axiom = verify_lean4_proof(
            proof_text=f"axiom cheat : False\n{sig} := by exact False.elim cheat",
            required_theorem_signature=sig,
        )
        self.assertFalse(r_axiom.verified)

        r_missing_bin = verify_lean4_proof(
            proof_text=f"{sig} := by exact Nat.add_comm a b",
            required_theorem_signature=sig,
            lean_binary="nonexistent_lean_binary_for_test",
        )
        self.assertFalse(r_missing_bin.verified)
        self.assertEqual(r_missing_bin.outcome, "verifier_error")

    def test_section16_record_nulls_and_redaction(self) -> None:
        rec = build_section16_trial_record(
            task_id="core-nt-01",
            model_id="C:\\Users\\alice\\models\\m.gguf",
            model_sha256=None,
            engine_commit=None,
            quantisation="Q4_K_M",
            seed=42,
            token_budget=512,
            tokens_used=None,
            wall_time_ms=None,
            attempts=[{"api_error": "HTTP 401 Bearer secret-token-123 from C:/Users/alice/file.txt"}],
            peak_vram_bytes=None,
            peak_ram_bytes=None,
            verifier="exact_int",
            verification_level=VerificationLevel.UNVERIFIED,
            verified=False,
            termination_reason="not_run",
        )
        self.assertEqual(rec["schema_version"], TSI_RECORD_SCHEMA_VERSION)
        for null_field in ("model_sha256", "engine_commit", "tokens_used", "wall_time_ms", "peak_vram_bytes", "peak_ram_bytes"):
            self.assertIsNone(rec[null_field])
        self.assertNotIn("alice", rec["model_id"])
        self.assertNotIn("secret-token-123", rec["attempts"][0]["api_error"])
        self.assertNotIn("alice", rec["attempts"][0]["api_error"])
        self.assertEqual(sanitise_public_text("Bearer abc.123"), "Bearer <REDACTED>")

    def test_loopback_guardrail(self) -> None:
        self.assertEqual(validate_base_url(DEFAULT_API_BASE_URL), "http://127.0.0.1:8080")
        with self.assertRaises(ValueError):
            validate_base_url("https://api.openai.com")
        self.assertEqual(validate_base_url("https://api.openai.com", allow_non_loopback=True), "https://api.openai.com")

    def test_no_print_or_exec_across_all_tsi_pws_evolution_modules(self) -> None:
        py_files = (
            [TOOLS_DIR / "tsi_eval.py", TOOLS_DIR / "pws_bench.py", TOOLS_DIR / "eio_bench.py"]
            + sorted((TOOLS_DIR / "tsi").glob("*.py"))
            + sorted((TOOLS_DIR / "pws").glob("*.py"))
            + sorted((TOOLS_DIR / "evolution").glob("*.py"))
        )
        self.assertGreaterEqual(len(py_files), 25)
        for fp in py_files:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"print", "eval", "exec"}, f"Forbidden call {node.func.id} in {fp}")


class TestTsiMockServerIntegration(unittest.TestCase):
    def test_eval_persistence_compare_and_report_end_to_end(self) -> None:
        ref_srv, _, ref_state = _start_mock_server("reference")
        cand_srv, _, _ = _start_mock_server("quantised")
        try:
            ref_url = f"http://127.0.0.1:{ref_srv.server_port}"
            cand_url = f"http://127.0.0.1:{cand_srv.server_port}"
            tasks = get_builtin_suite("core-v1")

            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                ref_json = tmp / "ref.json"
                ref_jsonl = tmp / "ref.jsonl"
                cand_json = tmp / "cand.json"
                cand_jsonl = tmp / "cand.jsonl"

                ref_summary = run_evaluation(
                    LocalOpenAIClient(ref_url),
                    tasks,
                    RunConfig(
                        base_url=ref_url,
                        model="",
                        quantization="BF16-ref",
                        kv_mode="f16",
                        gdn_mode="ref",
                        compensation_mode="off",
                        suite="core-v1",
                        budgets=(64, 256),
                        attempts_per_task=1,
                        temperature=0.0,
                        seed=42,
                        reasoning_effort=None,
                        timeout_s=15.0,
                        delta_target=0.05,
                    ),
                    jsonl_path=ref_jsonl,
                    summary_path=ref_json,
                )
                self.assertEqual(ref_summary["schema"], TSI_SCHEMA_VERSION)
                self.assertFalse(ref_summary["releaseQualified"])
                self.assertEqual(len(ref_state.requests), 24)
                b64, b256 = ref_summary["budgets"]
                self.assertEqual(b64["verified_tasks"], 11)
                self.assertEqual(b64["failure_taxonomy"].get("truncated_budget"), 1)
                self.assertEqual(b256["verified_tasks"], 12)
                self.assertIn("survival_tokens", b256)
                self.assertIn("survival_wall_seconds", b256)
                self.assertEqual(ref_summary["attainment"]["min_tested_budget_attained"], 256)
                jsonl_lines = ref_jsonl.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(jsonl_lines), 24)
                first_row = json.loads(jsonl_lines[0])
                self.assertEqual(first_row["schema_version"], 1)
                self.assertIsNone(first_row["peak_vram_bytes"])

                self.assertEqual(
                    tsi_eval.main(
                        [
                            "eval", "--url", cand_url, "--quantization", "Q4_K_M",
                            "--suite", "core-v1", "--budgets", "64,256",
                            "--out", str(cand_json), "--jsonl", str(cand_jsonl),
                        ]
                    ),
                    0,
                )
                diff_path = tmp / "diff.json"
                self.assertEqual(tsi_eval.main(["compare", str(ref_json), str(cand_json), "--out", str(diff_path)]), 0)
                diff = json.loads(diff_path.read_text(encoding="utf-8"))
                b256_cmp = diff["budgets"][1]
                self.assertEqual(b256_cmp["paired_contingency"]["both_pass"], 10)
                self.assertEqual(b256_cmp["paired_contingency"]["ref_pass_cand_fail"], 2)
                self.assertEqual(sorted(b256_cmp["regressions"]), ["core-ce-02", "core-nt-02"])

                rep_path = tmp / "report.md"
                self.assertEqual(tsi_eval.main(["report", str(ref_json), str(cand_json), "--out", str(rep_path)]), 0)
                self.assertIn("NKAT–URT TSI Evaluation Report", rep_path.read_text(encoding="utf-8"))

                ext_path = tmp / "custom.jsonl"
                ext_path.write_text(
                    json.dumps(
                        {
                            "task_id": "ext-01",
                            "prompt": "Compute 2 + 2 in \\boxed{...}.",
                            "verifier_type": "exact_int",
                            "spec": {"expected": 4},
                        }
                    ) + "\n",
                    encoding="utf-8",
                )
                loaded = load_tasks_file(ext_path)
                self.assertTrue(verify_response(loaded[0], "\\boxed{4}").verified)
        finally:
            ref_srv.shutdown()
            ref_srv.server_close()
            cand_srv.shutdown()
            cand_srv.server_close()


if __name__ == "__main__":
    unittest.main()

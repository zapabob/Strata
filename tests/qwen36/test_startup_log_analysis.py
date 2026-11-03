"""Startup-log rules for the Qwen3.6 32GB/16GB plan. Not a speed result."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from startup_log_analysis import analyze_startup_logs


def _placement(seconds: str, generation: str) -> str:
    return (
        f"strata-q36: startup generation {generation}\n"
        "strata-q36: context 65536 cells, prompt chunk 2048, 4.91 GiB of VRAM free\n"
        "strata-q36: hybrid experts: 41 of 256 per layer in VRAM (3.00 GiB), all 18.75 GiB "
        f"in pageable host memory, the rest of a batch of <= 128 rows on 6 CPU threads, "
        f"bigger prompt chunks streamed (1.10 GiB staging); {seconds} s\n"
    )


class StartupLogAnalysisTest(unittest.TestCase):
    def test_duplicate_upload_is_counted_once(self) -> None:
        one = (
            "strata-q36: context 65536 cells, prompt chunk 2048, 4.91 GiB of VRAM free\n"
            "strata-q36: no host memory for the experts (19195 MiB)\n"
        ).encode()
        single = analyze_startup_logs([one])
        doubled = analyze_startup_logs([one, one])
        self.assertEqual(doubled["counts"], single["counts"])
        self.assertEqual(doubled["uploads_counted"], 1)
        self.assertEqual(doubled["uploads_received"], 2)
        self.assertEqual(single["counts"]["host_allocation_failure"], 1)

    def test_no_followup_stays_unknown(self) -> None:
        blob = b"strata-q36: context 65536 cells, prompt chunk 2048, 4.91 GiB of VRAM free\n"
        result = analyze_startup_logs([blob])
        self.assertEqual(result["attempts"][0]["outcome"], "unknown")
        self.assertEqual(result["counts"]["unknown"], 1)
        self.assertNotIn("failed", result["attempts"][0]["outcome"])

    def test_zero_of_zero_has_no_hit_rate(self) -> None:
        blob = (
            "strata-q36: context 65536 cells, prompt chunk 2048, 4.91 GiB of VRAM free\n"
            "strata-q36: hybrid experts: 0 of 0 batch entries on the GPU (0.0%), 0 on the "
            "CPU pool in 0 ms, 0 slot replacements\n"
        ).encode()
        attempt = analyze_startup_logs([blob])["attempts"][0]
        self.assertIsNone(attempt["route_hit_rate"])
        self.assertEqual(attempt["gpu_route_entries"], 0)
        self.assertEqual(attempt["total_route_entries"], 0)

    def test_different_generations_are_not_added(self) -> None:
        blob = (_placement("10.0", "g1") + _placement("20.0", "g2")).encode()
        result = analyze_startup_logs([blob])
        self.assertIsNone(result["cross_generation_placement_seconds"])
        self.assertEqual(
            [a["placement_seconds"] for a in result["attempts"]],
            [10.0, 20.0],
        )

    def test_same_generation_can_report_its_own_sum(self) -> None:
        blob = (_placement("10.0", "g1") + _placement("5.5", "g1")).encode()
        result = analyze_startup_logs([blob])
        self.assertEqual(result["cross_generation_placement_seconds"], 15.5)

    def test_synthetic_mix_matches_its_own_counts(self) -> None:
        lines = ["strata-q36: context 4096 cells, prompt chunk 512, 1.00 GiB of VRAM free\n"] * 4
        lines += ["strata-q36: context 65536 cells, prompt chunk 2048, 4.91 GiB of VRAM free\n"
                  "strata-q36: no host memory for the experts (19195 MiB)\n"] * 14
        lines += ["strata-q36: context 65536 cells, prompt chunk 2048, 1.00 GiB of VRAM free\n"
                  "strata-q36: not enough VRAM left for the hybrid experts' buffers and slots (900 MiB needed, 100 MiB free after the weights, the context and the sessions)\n"] * 2
        lines.append(_placement("266.0", "done"))
        lines.append(_placement("266.0", "done"))
        lines.append(
            "strata-q36: startup generation warm1\n"
            "strata-q36: context 65536 cells, prompt chunk 2048, 4.91 GiB of VRAM free\n"
            "strata-q36: hybrid experts: 41 of 256 per layer in VRAM (3.00 GiB), all 18.75 GiB "
            "in pageable host memory, the rest of a batch of <= 128 rows on 6 CPU threads, "
            "bigger prompt chunks streamed (1.10 GiB staging); 266.0 s\n"
            "strata-q36: warmed up in 306.6 s (one prompt chunk, a decode step, a speculative step)\n"
        )
        result = analyze_startup_logs(["".join(lines).encode()])
        counts = result["counts"]
        self.assertEqual(counts["host_allocation_failure"], 14)
        self.assertEqual(counts["vram_failure"], 2)
        self.assertGreaterEqual(counts["expert_placement_complete"], 2)
        self.assertEqual(counts["warmup_complete"], 1)
        self.assertEqual(counts["unknown"], 4)

    def test_packaged_evidence_summary_is_historical_not_a_new_run(self) -> None:
        path = Path(__file__).resolve().parents[2] / "_docs" / "q36-32gb16gb" / "evidence-summary.json"
        if not path.is_file():
            self.skipTest("evidence summary is not in this tree")
        summary = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(summary["counts"]["engine_start"], 22)
        self.assertEqual(summary["counts"]["host_allocation_failure"], 14)
        # Status may move from the initial NOT_IMPLEMENTED marker to a partial
        # marker after host/engine work, but it must never claim a GPU speed run.
        self.assertIn(
            summary["plan_execution_status"],
            {"NOT_IMPLEMENTED_NOT_GPU_TESTED", "PARTIAL_IMPL_GPU_SPEED_NOT_RUN"},
        )
        self.assertNotIn("GPU_SPEED_PASS", summary["plan_execution_status"])
        self.assertIsNone(summary["installed_binary_matches_reviewed_source"])


if __name__ == "__main__":
    unittest.main()

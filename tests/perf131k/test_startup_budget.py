"""CPU-only checks of phase overlap; no model, Job or large allocations."""

import unittest

from tools.perf131k.startup_budget import DIAGNOSTIC_JOB_LIMIT, PHASES, evaluate


def proposed(events=None, reserve=1024, limit=DIAGNOSTIC_JOB_LIMIT):
    return {"job_limit_bytes": limit, "untracked_reserve_bytes": reserve,
            "untracked_reserve_basis": "synthetic test bound, not a runtime measurement",
            "events": events if events is not None else
            [{"action": "enter", "phase": phase} for phase in PHASES]}


class StartupBudgetTests(unittest.TestCase):
    def test_replacement_overlap_counts_old_and_new_until_actual_uncommit(self):
        events = [
            {"action": "enter", "phase": "source_open"},
            {"action": "acquire", "id": "old", "category": "scratch", "bytes": 3000,
             "basis": "synthetic retained scratch"},
            {"action": "enter", "phase": "cache_attempt"},
            {"action": "enter", "phase": "profile_fill"},
            {"action": "acquire", "id": "new", "category": "scratch", "bytes": 5000,
             "basis": "synthetic replacement scratch"},
            {"action": "release", "id": "old", "kind": "actual_uncommit"},
            {"action": "enter", "phase": "resident_complement"},
            {"action": "enter", "phase": "ready"},
        ]
        result = evaluate(proposed(events))
        self.assertEqual(result["estimated_peak_host_commit_bytes"], 9024)
        self.assertEqual(result["live_at_ready_bytes"], 5000)
        self.assertFalse(result["runtime_proof"] or result["launch_authorized"])

    def test_pool_return_does_not_uncharge_commit(self):
        events = proposed()["events"]
        events.insert(1, {"action": "acquire", "id": "stage", "category": "stage",
                          "bytes": 4096, "basis": "synthetic retained stage"})
        events.insert(3, {"action": "release", "id": "stage", "kind": "pool_return"})
        with self.assertRaisesRegex(ValueError, "logical release"):
            evaluate(proposed(events))

    def test_unknown_charge_and_missing_phase_block(self):
        with self.assertRaisesRegex(ValueError, "known nonnegative"):
            evaluate(proposed(reserve=None))
        incomplete = proposed()
        incomplete["events"].pop()
        with self.assertRaisesRegex(ValueError, "all startup phases"):
            evaluate(incomplete)

    def test_over_cap_blocks_without_allocating_large_buffer(self):
        events = proposed()["events"]
        events.insert(1, {"action": "acquire", "id": "fixed", "category": "fixed",
                          "bytes": DIAGNOSTIC_JOB_LIMIT, "basis": "synthetic logical byte count"})
        result = evaluate(proposed(events))
        self.assertEqual(result["diagnostic_cap_comparison"], "ESTIMATE_OVER_CAP")
        self.assertLess(result["estimated_cap_margin_bytes"], 0)
        self.assertFalse(result["product_fit_claim"])

    def test_same_demand_is_independent_of_diagnostic_cap(self):
        low = evaluate(proposed(limit=8 * 1024**3))
        high = evaluate(proposed(limit=DIAGNOSTIC_JOB_LIMIT))
        without_cap = evaluate(proposed(limit=None))
        self.assertEqual(low["estimated_peak_host_commit_bytes"],
                         high["estimated_peak_host_commit_bytes"])
        self.assertEqual(low["estimated_peak_host_commit_bytes"],
                         without_cap["estimated_peak_host_commit_bytes"])
        self.assertEqual(without_cap["diagnostic_cap_comparison"], "CAP_UNSPECIFIED")
        self.assertFalse(without_cap["launch_authorized"])


if __name__ == "__main__":
    unittest.main()

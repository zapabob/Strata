"""CPU-only unit tests for NKAT common-basis factorisation, URT bounds, and Spin(8) comparison."""

from __future__ import annotations

import math
from pathlib import Path
import random
import sys
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from pws.factorisation import (  # noqa: E402
    analyse_common_basis_factorisation,
    compare_spin8_vs_so8_quantisation,
    evaluate_common_basis_adoption,
)


class TestPwsFactorisationAndSpin8(unittest.TestCase):
    def test_common_basis_svd_and_urt_operator_norm_bound(self) -> None:
        rng = random.Random(99)
        m, n = 6, 6
        shared = [[math.sin(0.4 * i + 0.2 * j) for j in range(n)] for i in range(m)]
        u = [math.cos(0.3 * i) for i in range(m)]
        v = [math.sin(0.5 * j) for j in range(n)]
        experts = []
        for e in range(4):
            c = 0.3 * (e + 1)
            experts.append(
                [
                    [shared[i][j] + c * u[i] * v[j] + rng.uniform(-0.01, 0.01) for j in range(n)]
                    for i in range(m)
                ]
            )
        eye = [[1.0 if i == j else 0.0 for j in range(m)] for i in range(m)]
        res = analyse_common_basis_factorisation(experts, rank=1, g_sqrt=eye, c_sqrt=eye)
        self.assertGreater(res["mean_inter_expert_cosine_correlation"], 0.70)
        self.assertLess(res["mean_relative_frobenius_error"], 0.05)
        for row in res["experts"]:
            self.assertTrue(row["urt_bound_holds"])
            self.assertIsNotNone(row["weighted_frobenius_objective"])

    def test_section10_transfer_bit_and_critical_path_adoption_negative_control(self) -> None:
        # Transfer bits drop sharply, and reconstruction is fast -> justified
        pos = evaluate_common_basis_adoption(
            m=2048, n=2048, rank=64, orig_bits=4.0, corr_bits=4.0,
            metadata_bytes=4096, effective_ssd_bw_bytes_per_s=2.0e9,
            additional_reconstruction_and_sync_s=0.0002,
        )
        self.assertTrue(pos["transfer_reduced"])
        self.assertTrue(pos["net_speedup_justified"])

        # Same transfer reduction, but expensive reconstruction exceeds saved exposed I/O -> NOT justified!
        neg = evaluate_common_basis_adoption(
            m=2048, n=2048, rank=64, orig_bits=4.0, corr_bits=4.0,
            metadata_bytes=4096, effective_ssd_bw_bytes_per_s=2.0e9,
            additional_reconstruction_and_sync_s=0.005,
        )
        self.assertTrue(neg["transfer_reduced"])
        self.assertFalse(neg["net_speedup_justified"])

    def test_spin8_vs_generic_so8_and_no_rotation_comparison(self) -> None:
        # Outlier + moderate multi-channel signal: without rotation, scale=8/7 severely distorts
        # all 7 non-outlier columns (~0.55), whereas Hadamard/SO(8) spreading reduces dynamic range.
        w_outlier_signal = [
            [8.0 if j == 0 else (0.55 * math.cos(0.7 * i + 0.5 * j)) for j in range(8)]
            for i in range(8)
        ]
        cmp = compare_spin8_vs_so8_quantisation(w_outlier_signal, bits=4)
        self.assertIn("no_rotation", cmp["methods"])
        self.assertIn("sylvester_hadamard_so8", cmp["methods"])
        self.assertIn("generic_givens_so8", cmp["methods"])
        self.assertLess(
            cmp["methods"]["sylvester_hadamard_so8"]["frobenius_error"],
            cmp["methods"]["no_rotation"]["frobenius_error"],
        )
        # Conversely, on a pure exact-grid outlier with near-zero background, rotation is NOT universally
        # better — confirming Section 11's principle that rotation gains are empirical, not automatic.
        w_sparse_grid = [
            [8.0 if j == 0 else 0.01 * math.sin(i + j) for j in range(8)]
            for i in range(8)
        ]
        cmp_neg = compare_spin8_vs_so8_quantisation(w_sparse_grid, bits=4)
        self.assertGreater(cmp_neg["methods"]["sylvester_hadamard_so8"]["frobenius_error"], 0.0)


if __name__ == "__main__":
    unittest.main()

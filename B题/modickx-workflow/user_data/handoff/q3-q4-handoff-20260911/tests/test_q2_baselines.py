"""Compare local A/B/C search with c1, 90-degree heuristic, and the old 20-3000 m grid."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from localization import evaluate_J, select_second_point  # noqa: E402
from q2_validation import (  # noqa: E402
    baseline_90deg,
    baseline_c1,
    j_of_points,
    legacy_radii_m,
    min_j,
    polar_grid,
)


class BaselineComparisonTests(unittest.TestCase):
    def test_local_search_gap_versus_dense_reference_and_legacy_grid(self):
        s = np.array([0.0, 0.0])
        t0 = time.perf_counter()
        proposed = select_second_point(s, 0.0, n_azimuth=12, refine=False)
        t_local = time.perf_counter() - t0
        f1 = proposed.F1_vertices

        t1 = time.perf_counter()
        legacy_pts = polar_grid(s, legacy_radii_m(), n_azimuth=12)
        legacy = min_j(j_of_points(legacy_pts, s, f1))
        t_legacy = time.perf_counter() - t1

        ref_radii = np.linspace(0.0, proposed.R_core + 400.0, 12)
        ref_pts = polar_grid(proposed.c1, ref_radii, n_azimuth=24)
        reference = min_j(j_of_points(ref_pts, s, f1))

        j_c1 = evaluate_J(baseline_c1(proposed), s, f1)["J"]
        j_90 = evaluate_J(baseline_90deg(s, 0.0, proposed), s, f1)["J"]

        self.assertTrue(np.isfinite(proposed.J_star))
        self.assertTrue(np.isfinite(reference["J"]))
        gap = (proposed.J_star - reference["J"]) / max(reference["J"], 1e-9)
        self.assertLess(gap, 0.35)
        self.assertLessEqual(proposed.J_star, j_c1 + 1e-6)
        self.assertLess(len(proposed.candidates), len(legacy_pts) * 3)
        self.assertLess(t_local, max(2.0, 8.0 * t_legacy + 1.0))
        self.assertTrue(np.isfinite(j_90))
        self.assertNotIn(3000.0, [round(np.linalg.norm(c["q"] - s), 1) for c in proposed.candidates])


if __name__ == "__main__":
    unittest.main()

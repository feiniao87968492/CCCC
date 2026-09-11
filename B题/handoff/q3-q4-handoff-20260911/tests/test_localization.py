"""Q2: F1 covering radius, C_core, layered candidates, and J(q)."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from localization import (  # noqa: E402
    f1_outer_vertices,
    in_c_guaranteed,
    select_second_point,
    theoretical_sector_rho,
)
from params import R_MAX, R_MIN  # noqa: E402


class SecondPointTests(unittest.TestCase):
    def test_theoretical_sector_rho_is_750_114_not_a_reception_radius(self):
        rho0 = theoretical_sector_rho()
        self.assertAlmostEqual(rho0, 750.114, places=3)
        self.assertLess(rho0, R_MIN)
        self.assertNotAlmostEqual(rho0, R_MIN, places=0)
        self.assertNotAlmostEqual(rho0, R_MAX, places=0)

    def test_f1_mec_does_not_exceed_theoretical_bound(self):
        s = np.array([0.0, 0.0])
        verts = f1_outer_vertices(s, 0.0)
        self.assertGreater(len(verts), 2)
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        self.assertLessEqual(result.rho1, theoretical_sector_rho() + 8.0)
        self.assertGreater(result.R_core, 200.0)
        dists = np.linalg.norm(verts - s, axis=1)
        self.assertTrue(np.any(dists < 1000.0))
        self.assertTrue(np.all(dists <= R_MAX + 20.0))

    def test_c_core_guarantees_1000m_reception(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        verts = result.F1_vertices
        q = result.c1
        self.assertLessEqual(np.linalg.norm(q - result.c1), result.R_core + 1e-9)
        worst = max(np.linalg.norm(verts - q, axis=1))
        self.assertLessEqual(worst, R_MIN + 1e-6)

    def test_a_layer_stays_inside_c_core(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        a_pts = [c for c in result.candidates if c["layer"] == "A"]
        self.assertGreaterEqual(len(a_pts), 8)
        for c in a_pts:
            self.assertLessEqual(np.linalg.norm(c["q"] - result.c1), result.R_core + 1e-6)

    def test_no_3000m_polar_grid_about_s(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        radii = sorted({round(np.linalg.norm(c["q"] - s), 1) for c in result.candidates})
        for banned in (1800.0, 2400.0, 3000.0):
            self.assertFalse(any(abs(r - banned) < 1.0 for r in radii))
        self.assertTrue(all(np.linalg.norm(c["q"] - result.c1) <= result.R_core + 450.0 for c in result.candidates if c["layer"] != "s"))

    def test_f_no_is_not_f1_minus_1000_disk(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        q = s + np.array([400.0, 0.0])
        verts = result.F1_vertices
        f_no = []
        naive = []
        for g in verts:
            if np.linalg.norm(g - q) > max(R_MIN, np.linalg.norm(g - s)):
                f_no.append(g)
            if np.linalg.norm(g - q) > R_MIN:
                naive.append(g)
        self.assertNotEqual(len(f_no), len(naive))

    def test_j_is_finite_and_travel_is_separate(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        self.assertTrue(np.isfinite(result.J_star))
        self.assertGreater(result.travel_s, 0.0)
        for c in result.candidates:
            self.assertIn("J", c)
            self.assertIn("travel_s", c)
            self.assertNotIn("J_plus_travel", c)

    def test_q_star_is_not_hard_wired_to_c1(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        self.assertGreater(len(result.candidates), 5)
        js = [c["J"] for c in result.candidates]
        self.assertGreater(max(js) - min(js), 0.0)
        self.assertEqual(result.claim, "candidate_set_recommendation")

    def test_c_core_points_are_c_guaranteed(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        self.assertTrue(in_c_guaranteed(result.c1, s, result.F1_vertices))
        self.assertTrue(result.layers_present >= {"A"})


if __name__ == "__main__":
    unittest.main()

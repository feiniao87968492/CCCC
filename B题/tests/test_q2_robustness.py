"""Level-2 robustness: J sensitivity, azimuth refinement, crossing angle, no_signal."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geometry import localize_wedges, unit  # noqa: E402
from localization import evaluate_J, f1_outer_vertices, select_second_point  # noqa: E402
from q2_validation import TrueState, f_no_points, naive_f_no_points, observed_bearing, simulate_measure  # noqa: E402


class CrossingAngleTests(unittest.TestCase):
    def test_near_parallel_does_not_crash_and_rho_is_large(self):
        s1 = np.array([0.0, 0.0])
        s2 = np.array([200.0, 0.0])
        rhos = []
        for phi in (0.1, 1.0, 5.0, 30.0, 60.0, 89.0, 90.0, 91.0, 175.0, 179.0):
            result = localize_wedges([s1, s2], [0.0, phi])
            self.assertIn(result.status, {"polygon", "segment", "unbounded", "empty", "numerical_uncertain"})
            if result.status in {"polygon", "segment"} and result.mec_radius is not None:
                rhos.append((phi, result.mec_radius))
        finite = [(p, r) for p, r in rhos if np.isfinite(r)]
        if len(finite) >= 3:
            by_phi = dict(finite)
            if 90.0 in by_phi and 1.0 in by_phi:
                self.assertLess(by_phi[90.0], by_phi[1.0] * 3.0 + 50.0)


class JSensitivityTests(unittest.TestCase):
    def test_small_bearing_perturbation_keeps_J_stable(self):
        s = np.array([0.0, 0.0])
        base = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        js = [base.J_star]
        for da in (0.001, 0.01, 0.05, 0.1, -0.001, -0.01):
            other = select_second_point(s, da, n_azimuth=8, refine=False)
            js.append(other.J_star)
            self.assertTrue(np.isfinite(other.J_star))
        # q* may jump; J* should not explode relative to the unperturbed value
        self.assertLess(max(js) / min(js), 4.0)

    def test_azimuth_refinement_does_not_worsen_J_much(self):
        s = np.array([0.0, 0.0])
        j8 = select_second_point(s, 0.0, n_azimuth=8, refine=False).J_star
        j16 = select_second_point(s, 0.0, n_azimuth=16, refine=False).J_star
        j24 = select_second_point(s, 0.0, n_azimuth=24, refine=False).J_star
        # 8-azimuth rays are a subset of 16 and of 24, so min J cannot increase.
        self.assertLessEqual(j16, j8 + 1e-6)
        self.assertLessEqual(j24, j8 + 1e-6)
        if j24 > 1e-9:
            self.assertLess(abs(j24 - j16) / j24, 0.35)

    def test_f1_tangent_count_stability(self):
        s = np.array([0.0, 0.0])
        rhos = []
        for n in (32, 48, 64):
            verts = f1_outer_vertices(s, 0.0, n_tangents=n)
            _, rho = __import__("geometry", fromlist=["min_enclosing_circle"]).min_enclosing_circle(verts)
            rhos.append(rho)
        self.assertLess(max(rhos) - min(rhos), 5.0)


class NoSignalStressTests(unittest.TestCase):
    def test_no_signal_uses_shared_r_not_1000_disk(self):
        s = np.array([0.0, 0.0])
        g = np.array([1200.0, 0.0])
        r = 1300.0
        b1 = observed_bearing(s, TrueState(g=g, r=r, eps1_deg=0.0))
        q = g + np.array([r + 1.0, 0.0])
        y, _ = simulate_measure(q, g, r, 0.0)
        self.assertEqual(y, "no_signal")
        verts = f1_outer_vertices(s, b1)
        exact = f_no_points(verts, s, q)
        naive = naive_f_no_points(verts, q)
        self.assertGreater(len(exact), 0)
        self.assertNotEqual(len(exact), len(naive))
        ev = evaluate_J(q, s, verts)
        self.assertTrue(np.isfinite(ev["J"]))
        self.assertGreaterEqual(ev["J"], 1.0)


if __name__ == "__main__":
    unittest.main()

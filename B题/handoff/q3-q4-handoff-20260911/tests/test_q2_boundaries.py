"""Boundary tests: angle, 5 m, r, C_core, C_guaranteed, Omega, wrap-around."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geometry import unit  # noqa: E402
from localization import f1_outer_vertices, in_c_guaranteed, select_second_point, theoretical_sector_rho  # noqa: E402
from params import NEAR_RADIUS, OMEGA_RADIUS, R_MAX, R_MIN  # noqa: E402
from q2_validation import (  # noqa: E402
    ANGLE_DELTAS_DEG,
    CORE_DELTAS_M,
    DIST_DELTAS_M,
    TrueState,
    f_no_points,
    first_observation,
    in_Z1,
    in_Z_no,
    in_c_core,
    in_wedge,
    max_distance_to_set,
    naive_f_no_points,
    naive_no_signal_position,
    observed_bearing,
    simulate_measure,
)


class AngleBoundaryTests(unittest.TestCase):
    def test_plus_minus_one_degree_keeps_boundary_truth(self):
        s = np.array([0.0, 0.0])
        dist = 800.0
        r = 1400.0
        for eps in (-1.0, 1.0):
            for true_b in (0.0, 0.4, 90.0, 179.0, 359.6):
                g = dist * unit(np.deg2rad(true_b))
                state = TrueState(g=g, r=r, eps1_deg=eps)
                y, b = first_observation(state, s)
                self.assertEqual(y, "direction")
                self.assertTrue(in_wedge(g, s, b), msg=f"true={true_b} eps={eps} obs={b}")
                self.assertTrue(in_Z1(g, r, s, b))

    def test_angle_deltas_near_error_bound(self):
        s = np.array([0.0, 0.0])
        g = np.array([900.0, 0.0])
        r = 1200.0
        for sign in (-1.0, 1.0):
            for delta in ANGLE_DELTAS_DEG:
                eps = sign * (1.0 - delta)
                b = observed_bearing(s, TrueState(g=g, r=r, eps1_deg=eps))
                self.assertTrue(in_Z1(g, r, s, b), msg=f"eps={eps}")

    def test_wrap_across_zero_and_360(self):
        s = np.array([0.0, 0.0])
        r = 1400.0
        g = 700.0 * unit(np.deg2rad(0.4))
        b = observed_bearing(s, TrueState(g=g, r=r, eps1_deg=-1.0))
        self.assertGreaterEqual(b, 359.0)
        self.assertTrue(in_Z1(g, r, s, b))
        g2 = 700.0 * unit(np.deg2rad(359.6))
        b2 = observed_bearing(s, TrueState(g=g2, r=r, eps1_deg=1.0))
        self.assertLess(b2, 1.0)
        self.assertTrue(in_Z1(g2, r, s, b2))


class NearFiveMetreTests(unittest.TestCase):
    def test_second_measure_classifies_5m_boundary(self):
        s = np.array([0.0, 0.0])
        g = np.array([800.0, 0.0])
        r = 1200.0
        for delta in DIST_DELTAS_M:
            q_in = g + np.array([NEAR_RADIUS - delta, 0.0])
            y, _ = simulate_measure(q_in, g, r, 0.0)
            self.assertEqual(y, "near", msg=delta)
            q_on = g + np.array([NEAR_RADIUS, 0.0])
            y, _ = simulate_measure(q_on, g, r, 0.0)
            self.assertEqual(y, "near")
            q_out = g + np.array([NEAR_RADIUS + delta, 0.0])
            y, _ = simulate_measure(q_out, g, r, 0.0)
            self.assertEqual(y, "direction", msg=delta)


class RadiusBoundaryTests(unittest.TestCase):
    def test_r_1000_and_1500_and_not_naive_1000_rule(self):
        s = np.array([0.0, 0.0])
        g = np.array([800.0, 0.0])
        b1 = observed_bearing(s, TrueState(g=g, r=1500.0, eps1_deg=0.0))
        for r in (1000.0, 1500.0):
            for delta in DIST_DELTAS_M:
                q_in = g + np.array([r - delta, 0.0])
                y, _ = simulate_measure(q_in, g, r, 0.0)
                self.assertNotEqual(y, "no_signal")
                q_on = g + np.array([r, 0.0])
                y, _ = simulate_measure(q_on, g, r, 0.0)
                self.assertNotEqual(y, "no_signal")
                q_out = g + np.array([r + delta, 0.0])
                y, _ = simulate_measure(q_out, g, r, 0.0)
                self.assertEqual(y, "no_signal")
                self.assertTrue(in_Z_no(g, r, s, b1, q_out))
        # r=1500, d=1201: naive 1000-rule would already say no_signal; true is direction
        q = g + np.array([1201.0, 0.0])
        y, _ = simulate_measure(q, g, 1500.0, 0.0)
        self.assertEqual(y, "direction")
        self.assertTrue(naive_no_signal_position(g, q))


class CoreAndGuaranteedTests(unittest.TestCase):
    def test_c_core_boundary_and_just_outside(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        u = np.array([0.0, 1.0])
        for delta in CORE_DELTAS_M:
            q_in = result.c1 + (result.R_core - delta) * u
            if delta < result.R_core:
                self.assertTrue(in_c_core(q_in, result.c1, result.R_core))
                self.assertLessEqual(max_distance_to_set(q_in, result.F1_vertices), R_MIN + 1e-5)
            q_on = result.c1 + result.R_core * u
            self.assertTrue(in_c_core(q_on, result.c1, result.R_core))
            self.assertLessEqual(max_distance_to_set(q_on, result.F1_vertices), R_MIN + 1e-5)
            q_out = result.c1 + (result.R_core + delta) * u
            self.assertFalse(in_c_core(q_out, result.c1, result.R_core, atol=delta * 0.1 if delta > 1e-4 else 1e-9))

    def test_c_core_subset_c_guaranteed_on_vertices(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        q = result.c1
        self.assertTrue(in_c_guaranteed(q, s, result.F1_vertices))
        q_out = result.c1 + np.array([0.0, result.R_core + 800.0])
        self.assertFalse(in_c_guaranteed(q_out, s, result.F1_vertices))

    def test_f_no_not_equal_naive_disk(self):
        s = np.array([0.0, 0.0])
        verts = f1_outer_vertices(s, 0.0)
        q = np.array([400.0, 0.0])
        exact = f_no_points(verts, s, q)
        naive = naive_f_no_points(verts, q)
        self.assertNotEqual(len(exact), len(naive))


class OmegaAndWorstSectorTests(unittest.TestCase):
    def test_source_on_omega_boundary_is_not_dropped(self):
        g = np.array([OMEGA_RADIUS, 0.0])
        s = np.array([OMEGA_RADIUS - 1200.0, 0.0])
        r = 1500.0
        b = observed_bearing(s, TrueState(g=g, r=r, eps1_deg=0.0))
        self.assertTrue(in_Z1(g, r, s, b))
        verts = f1_outer_vertices(s, b)
        result = select_second_point(s, b, n_azimuth=8, refine=False)
        self.assertLess(result.rho1, theoretical_sector_rho() + 8.0)
        self.assertGreater(result.R_core, 249.0)

    def test_unclipped_sector_rho_near_theory(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        self.assertLessEqual(result.rho1, theoretical_sector_rho() + 8.0)
        self.assertGreater(result.rho1, theoretical_sector_rho() - 5.0)


if __name__ == "__main__":
    unittest.main()

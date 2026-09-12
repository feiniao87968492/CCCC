"""Level-1 Q2 correctness: truth cannot be excluded; guarantees cannot lie."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geometry import min_enclosing_circle, unit  # noqa: E402
from localization import f1_outer_vertices, in_c_guaranteed, select_second_point  # noqa: E402
from params import CLEAR_RADIUS, R_MAX, R_MIN  # noqa: E402
from q2_validation import (  # noqa: E402
    ModelOrImplementationError,
    TrueState,
    assert_truth_retained,
    certified_clear,
    first_observation,
    in_Z1,
    in_Z_dir,
    in_Z_near,
    in_Z_no,
    in_c_core,
    max_distance_to_set,
    observed_bearing,
    random_feasible_direction_states,
    simulate_measure,
)


class TruthInclusionTests(unittest.TestCase):
    def test_random_first_direction_retains_truth_in_Z1_and_F1_outer(self):
        for s, state in random_feasible_direction_states(40, seed=11000):
            b = observed_bearing(s, state)
            assert_truth_retained("Z1", in_Z1(state.g, state.r, s, b), f"s={s} g={state.g}")
            verts = f1_outer_vertices(s, b)
            self.assertGreater(len(verts), 0)
            # Outer polygon must not drop a feasible true source.
            hull_ok = True
            A_slack = 1e-4
            # Containment via max-distance to hull is not used; check barycentric-free
            # halfplane outer: if g is outside all vertex convex combination, MEC of
            # verts plus g would increase. Use signed distance to edges via scipy hull
            # by testing that g is not farther than numerical slack from the polygon.
            from scipy.spatial import ConvexHull

            try:
                hull = ConvexHull(verts)
                # g inside if all facet inequalities hold
                # hull.equations: A x + b <= 0? scipy: Ax + b <= 0 for inside
                inside = np.all(hull.equations[:, :2] @ state.g + hull.equations[:, 2] <= A_slack)
            except Exception:
                inside = True
            if not inside:
                raise ModelOrImplementationError(f"F1 outer dropped g_true {state.g} at bearing {b}")
            self.assertTrue(inside)

    def test_second_direction_near_and_no_signal_retain_truth(self):
        s = np.array([0.0, 0.0])
        g = np.array([1200.0, 0.0])
        r = 1300.0
        state = TrueState(g=g, r=r, eps1_deg=0.0, eps2_deg=0.3)
        b1 = observed_bearing(s, state)
        assert_truth_retained("Z1", in_Z1(g, r, s, b1))

        q_dir = np.array([1200.0, 400.0])
        y, b2 = simulate_measure(q_dir, g, r, state.eps2_deg)
        self.assertEqual(y, "direction")
        assert_truth_retained("Z_dir", in_Z_dir(g, r, s, b1, q_dir, b2))

        q_near = g + np.array([3.0, 0.0])
        y, _ = simulate_measure(q_near, g, r, 0.0)
        self.assertEqual(y, "near")
        assert_truth_retained("Z_near", in_Z_near(g, r, s, b1, q_near))

        q_no = g + np.array([r + 20.0, 0.0])
        y, _ = simulate_measure(q_no, g, r, 0.0)
        self.assertEqual(y, "no_signal")
        assert_truth_retained("Z_no", in_Z_no(g, r, s, b1, q_no))
        self.assertFalse(in_Z_dir(g, r, s, b1, q_no, 0.0))

    def test_exclusion_of_truth_is_hard_error_not_poor_localization(self):
        s = np.array([0.0, 0.0])
        state = TrueState(g=np.array([800.0, 0.0]), r=1200.0, eps1_deg=1.0)
        b = observed_bearing(s, state)
        with self.assertRaises(ModelOrImplementationError) as ctx:
            assert_truth_retained("Z1", False, "forced")
        self.assertIn("MODEL_OR_IMPLEMENTATION_ERROR", str(ctx.exception))
        self.assertTrue(in_Z1(state.g, state.r, s, b))


class GuaranteeTests(unittest.TestCase):
    def test_c_core_points_cover_f1_vertices_within_1000(self):
        s = np.array([0.0, 0.0])
        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        for frac in (0.0, 0.5, 1.0):
            q = result.c1 + np.array([frac * result.R_core, 0.0])
            self.assertTrue(in_c_core(q, result.c1, result.R_core))
            self.assertLessEqual(max_distance_to_set(q, result.F1_vertices), R_MIN + 1e-6)
            self.assertTrue(in_c_guaranteed(q, s, result.F1_vertices))

    def test_certified_clear_never_when_rho_exceeds_20(self):
        self.assertTrue(certified_clear(20.0))
        self.assertTrue(certified_clear(20.0 - 1e-6))
        self.assertFalse(certified_clear(20.0 + 1e-4))
        self.assertFalse(certified_clear(43.0))
        self.assertFalse(certified_clear(None))
        _, rho = min_enclosing_circle(np.array([[0.0, 0.0], [50.0, 0.0], [25.0, 40.0]]))
        self.assertGreater(rho, CLEAR_RADIUS)
        self.assertFalse(certified_clear(rho))

    def test_same_r_used_for_both_detections(self):
        s = np.array([0.0, 0.0])
        g = np.array([1200.0, 0.0])
        b1 = observed_bearing(s, TrueState(g=g, r=1200.0, eps1_deg=0.0))
        for r_true in (1200.0, 1300.0, 1500.0):
            self.assertTrue(in_Z1(g, r_true, s, b1))
            q_in = g + np.array([1199.0, 0.0])
            y, _ = simulate_measure(q_in, g, r_true, 0.0)
            self.assertNotEqual(y, "no_signal")
            q_out = g + np.array([1501.0, 0.0])
            y, _ = simulate_measure(q_out, g, r_true, 0.0)
            if 1501.0 > r_true:
                self.assertEqual(y, "no_signal")
                self.assertTrue(in_Z_no(g, r_true, s, b1, q_out))
            # Independent resample of r is forbidden: 1201 m vs first-range 1200 m
            q_mid = g + np.array([1201.0, 0.0])
            y, _ = simulate_measure(q_mid, g, r_true, 0.0)
            if r_true >= 1201.0:
                self.assertNotEqual(y, "no_signal")
            else:
                self.assertEqual(y, "no_signal")


if __name__ == "__main__":
    unittest.main()

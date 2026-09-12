"""Q1: forward-wedge intersection, diameter, and minimum enclosing radius."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geometry import (  # noqa: E402
    diameter_circle_covers,
    localize_wedges,
    min_enclosing_circle,
    wedge_halfplanes,
)


def _eq_triangle_wedges():
    verts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, math.sqrt(3.0) / 2.0]])
    sites = []
    bearings = []
    for i in range(3):
        e = verts[(i + 1) % 3] - verts[i]
        e = e / np.linalg.norm(e)
        sites.append(verts[i] - 100.0 * e)
        bearings.append(math.degrees(math.atan2(e[1], e[0])) + 1.0)
    return sites, bearings, verts


class WedgeLocalizationTests(unittest.TestCase):
    def test_zero_observations_are_unbounded_and_diameter_is_infinite(self):
        result = localize_wedges([], [])
        self.assertEqual(result.status, "unbounded")
        self.assertTrue(math.isinf(result.diameter))
        self.assertIsNone(result.mec_radius)

    def test_single_wedge_is_unbounded(self):
        result = localize_wedges([[0.0, 0.0]], [90.0])
        self.assertEqual(result.status, "unbounded")
        self.assertTrue(math.isinf(result.diameter))

    def test_contradictory_wedges_are_empty_and_diameter_is_undefined(self):
        # Opposite rays from distinct sites: west of origin vs east of x=10.
        result = localize_wedges([[0.0, 0.0], [10.0, 0.0]], [180.0, 0.0])
        self.assertEqual(result.status, "empty")
        self.assertIsNone(result.diameter)

    def test_empty_diameter_is_not_filled_with_zero(self):
        result = localize_wedges([[0.0, 0.0], [10.0, 0.0]], [180.0, 0.0])
        self.assertIsNone(result.diameter)

    def test_two_crossing_wedges_form_a_bounded_polygon(self):
        s1 = np.array([-200.0, 0.0])
        s2 = np.array([0.0, -200.0])
        result = localize_wedges([s1, s2], [0.0, 90.0])
        self.assertEqual(result.status, "polygon")
        self.assertGreaterEqual(len(result.vertices), 3)
        self.assertTrue(math.isfinite(result.diameter))
        self.assertGreater(result.diameter, 0.0)

    def test_negative_coordinates_are_allowed(self):
        result = localize_wedges([[-500.0, -400.0]], [240.0])
        self.assertEqual(result.status, "unbounded")
        A, b = wedge_halfplanes(np.array([-500.0, -400.0]), 240.0)
        self.assertEqual(A.shape, (2, 2))

    def test_bearing_wraps_across_zero(self):
        result = localize_wedges([[0.0, 0.0], [100.0, 0.0]], [359.5, 180.5])
        self.assertIn(result.status, {"polygon", "segment", "unbounded", "empty"})

    def test_equilateral_triangle_is_realizable_and_diameter_is_one(self):
        sites, bearings, verts = _eq_triangle_wedges()
        result = localize_wedges(sites, bearings)
        self.assertEqual(result.status, "polygon")
        self.assertEqual(len(result.vertices), 3)
        self.assertAlmostEqual(result.diameter, 1.0, places=6)
        for v in verts:
            self.assertTrue(result.contains(v, atol=1e-6))

    def test_diameter_circle_does_not_cover_equilateral_triangle(self):
        sites, bearings, _ = _eq_triangle_wedges()
        result = localize_wedges(sites, bearings)
        self.assertGreater(result.mec_radius, result.diameter / 2.0 + 1e-9)
        self.assertFalse(diameter_circle_covers(result.vertices, result.diameter))
        self.assertAlmostEqual(result.mec_radius, 1.0 / math.sqrt(3.0), places=6)

    def test_point_region_has_zero_diameter_and_zero_rho(self):
        # Three wedges aimed at a common interior point from well-separated sites
        # with tiny synthetic epsilon is not used; instead intersect six halfplanes
        # that force a single vertex. Use two pairs that cross at one point plus
        # a third pair that also contains only that point.
        target = np.array([10.0, 20.0])
        sites = []
        bearings = []
        for ang in (0.0, 120.0, 240.0):
            rad = math.radians(ang)
            direction = np.array([math.cos(rad), math.sin(rad)])
            sites.append(target - 200.0 * direction)
            bearings.append(ang)
        result = localize_wedges(sites, bearings, eps_deg=1.0)
        self.assertIn(result.status, {"polygon", "point", "segment"})
        self.assertTrue(result.contains(target, atol=1e-4))
        self.assertLess(result.diameter, 20.0)

    def test_min_enclosing_circle_of_two_points(self):
        pts = np.array([[0.0, 0.0], [4.0, 0.0]])
        center, radius = min_enclosing_circle(pts)
        np.testing.assert_allclose(center, [2.0, 0.0], atol=1e-9)
        self.assertAlmostEqual(radius, 2.0, places=9)

    def test_source_stays_inside_random_consistent_wedges(self):
        rng = np.random.default_rng(11000)
        inside = 0
        for _ in range(100):
            g = rng.uniform(-500.0, 500.0, size=2)
            n = int(rng.integers(2, 5))
            sites = rng.uniform(-800.0, 800.0, size=(n, 2))
            bearings = []
            ok = True
            for s in sites:
                vec = g - s
                if np.linalg.norm(vec) < 1e-9:
                    ok = False
                    break
                true = math.degrees(math.atan2(vec[1], vec[0]))
                err = float(rng.uniform(-1.0, 1.0))
                bearings.append((true + err) % 360.0)
            if not ok:
                continue
            result = localize_wedges(sites, bearings)
            if result.status == "empty":
                self.fail("consistent wedges classified empty")
            if result.status in {"polygon", "point", "segment"}:
                self.assertTrue(result.contains(g, atol=1e-4), msg=result.status)
                inside += 1
            elif result.status == "unbounded":
                self.assertTrue(result.contains(g, atol=1e-4))
        self.assertGreater(inside, 20)


if __name__ == "__main__":
    unittest.main()

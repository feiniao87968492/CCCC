from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from params import CLEAR_RADIUS  # noqa: E402
from q4_localize import bearing_intersection, clear_poses, second_measure_points  # noqa: E402


class BearingGeometryTests(unittest.TestCase):
    def test_intersecting_bearings_recover_source(self):
        g = np.array([400.0, 300.0])
        s1 = np.array([0.0, 0.0])
        s2 = np.array([0.0, 600.0])
        d1 = g - s1
        d2 = g - s2
        a1 = float(np.rad2deg(np.arctan2(d1[1], d1[0])))
        a2 = float(np.rad2deg(np.arctan2(d2[1], d2[0])))
        loc = bearing_intersection(s1, a1, s2, a2)
        self.assertIsNotNone(loc)
        self.assertLess(float(np.linalg.norm(loc["point"] - g)), CLEAR_RADIUS)

    def test_parallel_bearings_return_none(self):
        self.assertIsNone(bearing_intersection([0.0, 0.0], 0.0, [0.0, 100.0], 0.0))
        self.assertIsNone(bearing_intersection([0.0, 0.0], 0.0, [10.0, 0.0], 0.0))

    def test_source_behind_flag(self):
        loc = bearing_intersection(np.array([0.0, 0.0]), 0.0, np.array([0.0, 200.0]), 90.0)
        self.assertIsNotNone(loc)
        self.assertTrue(loc["behind"])

    def test_second_sites_have_baseline(self):
        s1 = np.zeros(2)
        pts = second_measure_points(s1, 0.0, s1)
        self.assertGreaterEqual(len(pts), 2)
        for p in pts:
            self.assertGreater(float(np.linalg.norm(p - s1)), 200.0)

    def test_clear_poses_within_20m_of_candidate(self):
        c = np.array([100.0, 50.0])
        last = np.array([0.0, 0.0])
        for p in clear_poses(c, last):
            self.assertLessEqual(float(np.linalg.norm(p - c)), CLEAR_RADIUS)


if __name__ == "__main__":
    unittest.main()

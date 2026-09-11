import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from params import OMEGA_RADIUS, R_MIN  # noqa: E402
from q4_cover import (  # noqa: E402
    APPROACH,
    GRID_HALF,
    covering_point,
    p4_covers,
    p4_index,
    p4_points,
    p4_snake_indices,
    rf_covered,
)


class P4CoverTests(unittest.TestCase):
    def test_grid_has_81_points_in_box(self):
        pts = p4_points()
        self.assertEqual(len(pts), 81)
        self.assertEqual(len({(round(p[0], 6), round(p[1], 6)) for p in pts}), 81)
        self.assertTrue(np.all(np.abs(pts) <= 2400.0 + 1e-9))
        self.assertIs(p4_points(), p4_points())
        self.assertEqual(len(p4_snake_indices()), 81)
        self.assertEqual(p4_index(np.zeros(2)), p4_index([0.0, 0.0]))
        self.assertIsNone(p4_index(np.array([1200.0, 100.0])))
        self.assertIsNotNone(p4_index(np.array([1200.0, 0.0])))

    def test_proof_constants(self):
        slack_r = APPROACH + GRID_HALF * np.sqrt(2.0)
        slack_h = APPROACH - GRID_HALF * np.sqrt(2.0)
        self.assertLess(slack_r, R_MIN)
        self.assertGreater(slack_h, 0.0)

    def test_axis_and_boundary_sources(self):
        cases = [
            (np.array([0.0, 0.0]), 0.0),
            (np.array([OMEGA_RADIUS, 0.0]), 0.0),
            (np.array([OMEGA_RADIUS, 0.0]), np.pi),
            (np.array([0.0, OMEGA_RADIUS]), np.pi / 2),
            (np.array([OMEGA_RADIUS / np.sqrt(2), OMEGA_RADIUS / np.sqrt(2)]), np.pi / 4),
            (np.array([OMEGA_RADIUS / np.sqrt(2), OMEGA_RADIUS / np.sqrt(2)]), 5 * np.pi / 4),
        ]
        for g, h in cases:
            p = covering_point(g, h)
            self.assertTrue(rf_covered(g, h, p, directional=True), msg=f"g={g} h={h} p={p}")
            self.assertTrue(p4_covers(g, h, directional=True))
            self.assertTrue(p4_covers(g, h, directional=False))

    def test_random_disk_and_headings(self):
        rng = np.random.default_rng(20260911)
        for _ in range(200):
            rad = np.sqrt(rng.random()) * OMEGA_RADIUS
            ang = rng.uniform(0.0, 2.0 * np.pi)
            g = rad * np.array([np.cos(ang), np.sin(ang)])
            h = rng.uniform(0.0, 2.0 * np.pi)
            self.assertTrue(p4_covers(g, h, directional=True))
            self.assertTrue(p4_covers(g, h, directional=False))


if __name__ == "__main__":
    unittest.main()

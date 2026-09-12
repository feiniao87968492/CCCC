"""Offline Q3 helpers. Does not call the official simulator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))

from q3_safe import safe_grid  # noqa: E402
from q3_state import P3, Q3State, cover_index, shortest_next  # noqa: E402


class CoverGeometryTests(unittest.TestCase):
    def test_seven_points(self):
        self.assertEqual(len(P3), 7)
        self.assertAlmostEqual(float(np.linalg.norm(P3[0])), 0.0)
        self.assertAlmostEqual(float(np.linalg.norm(P3[1])), 1200.0, places=6)
        self.assertEqual(cover_index((0.0, 0.0)), 0)

    def test_shortest_next_from_origin_is_a_hex_vertex_or_origin(self):
        remaining = [p.copy() for p in P3[1:]]
        nxt = shortest_next(np.zeros(2), remaining)
        self.assertAlmostEqual(float(np.linalg.norm(nxt)), 1200.0, places=5)

    def test_safe_grid_is_225(self):
        pts = safe_grid(np.zeros(2), 0.0)
        self.assertEqual(len(pts), 225)

    def test_sixteen_detected_cancels_discovery(self):
        st = Q3State()
        for k in range(1, 17):
            st.channels[k].ever_detected = True
            st.channels[k].status = "detected"
            st.P.append(k)
        self.assertTrue(st.discovery_cancelled())
        self.assertEqual(st.unseen_to_scan(), [])

    def test_runner_does_not_import_oracle(self):
        self.assertNotIn("q2_validation", sys.modules)
        import q3_runner  # noqa: F401

        self.assertNotIn("q2_validation", sys.modules)
        self.assertNotIn("q2_scenario", sys.modules)


if __name__ == "__main__":
    unittest.main()

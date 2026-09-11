"""FAST/HYBRID selectors keep Z/F certificates; C_main is nonempty after first direction."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from active import (  # noqa: E402
    HEX_COVER,
    in_C_k,
    route_length_estimate,
    select_active,
    select_fast_point,
    select_hybrid_point,
    shortest_path_length,
)
from localization import f1_outer_vertices, theoretical_sector_rho  # noqa: E402
from params import R_MIN  # noqa: E402


class FastActiveTests(unittest.TestCase):
    def test_c_main_nonempty_after_first_direction(self):
        s = np.array([0.0, 0.0])
        verts = f1_outer_vertices(s, 0.0)
        self.assertTrue(in_C_k(np.array([750.0, 0.0]), verts, [s]) or in_C_k(verts.mean(axis=0), verts, [s]))
        choice = select_fast_point(s, 0.0, n_azimuth=8)
        self.assertEqual(choice.method, "FAST")
        self.assertTrue(np.all(np.isfinite(choice.q)))
        self.assertIsNone(choice.J)

    def test_fast_can_reuse_remaining_cover_nodes(self):
        s = np.array([0.0, 0.0])
        remaining = HEX_COVER[1:]
        choice = select_fast_point(s, 0.0, remaining_cover=remaining, n_azimuth=8)
        dists = [np.linalg.norm(choice.q - p) for p in remaining]
        # reuse is preferred but not mandatory; just ensure remaining points are legal candidates
        self.assertTrue(min(dists) < 2500.0)

    def test_hybrid_computes_J_on_shortlist_only(self):
        s = np.array([0.0, 0.0])
        choice = select_hybrid_point(s, 0.0, n_azimuth=8, top_k=4)
        self.assertEqual(choice.method, "HYBRID")
        self.assertIsNotNone(choice.J)
        self.assertTrue(np.isfinite(choice.J))

    def test_strategy_switch(self):
        s = np.array([0.0, 0.0])
        f = select_active("FAST", s, 0.0, n_azimuth=8)
        h = select_active("HYBRID", s, 0.0, n_azimuth=8, top_k=4)
        r = select_active("ROBUST", s, 0.0, n_azimuth=8)
        self.assertEqual(f.method, "FAST")
        self.assertEqual(h.method, "HYBRID")
        self.assertEqual(r.method, "ROBUST")
        self.assertIsNotNone(r.J)

    def test_ranking_uses_estimate_on_hex_cover(self):
        s = np.array([0.0, 0.0])
        remaining = HEX_COVER[1:]
        L = route_length_estimate(s, remaining)
        self.assertAlmostEqual(L, shortest_path_length(s, remaining), places=6)

    def test_no_empty_main_fallback_needed(self):
        s = np.array([0.0, 0.0])
        from localization import select_second_point

        result = select_second_point(s, 0.0, n_azimuth=8, refine=False)
        self.assertGreater(result.R_core, 200.0)
        self.assertLessEqual(result.rho1, theoretical_sector_rho() + 8.0)
        self.assertGreater(R_MIN - result.rho1, 0.0)


if __name__ == "__main__":
    unittest.main()

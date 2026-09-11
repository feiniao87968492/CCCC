"""Equal-length HEX37 Hamilton prefix routes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from q4_cover import (  # noqa: E402
    HEX37_ROUTE_CURRENT,
    HEX_STEP,
    cover_points,
    cover_route,
    register_hex37_route,
    set_cover_mode,
    set_hex37_route,
)
from q4_prefix import (  # noqa: E402
    dihedral_paths,
    evaluate_order,
    first_detect_indices,
    prefix_score,
    validate_hamilton_indices,
)


class PrefixRouteTests(unittest.TestCase):
    def tearDown(self):
        set_hex37_route(HEX37_ROUTE_CURRENT)
        set_cover_mode("SQUARE81")

    def test_current_route_is_hamilton_800(self):
        validate_hamilton_indices(list(range(37)))

    def test_dihedral_copies_are_hamilton(self):
        copies = dihedral_paths()
        self.assertGreaterEqual(len(copies), 6)
        for order in copies:
            validate_hamilton_indices(order)
            self.assertEqual(order[0], 0)

    def test_origin_omni_detected_at_index_zero(self):
        idx = first_detect_indices(
            list(range(37)),
            np.array([[0.0, 0.0]]),
            np.array([0.0]),
            directional=False,
        )
        self.assertEqual(int(idx[0]), 0)

    def test_set_hex37_route_changes_visit_order(self):
        copies = dihedral_paths()
        alt = next(c for c in copies if c != list(range(37)))
        register_hex37_route("PREFIX_TEST", alt)
        set_cover_mode("HEX37")
        set_hex37_route("PREFIX_TEST")
        self.assertEqual(cover_route(), alt)
        pts = cover_points()
        self.assertAlmostEqual(float(np.linalg.norm(pts[cover_route()[1]] - pts[0])), HEX_STEP, places=6)
        set_hex37_route(HEX37_ROUTE_CURRENT)
        self.assertEqual(cover_route(), list(range(37)))

    def test_evaluate_current_has_no_miss(self):
        rng = np.random.default_rng(0)
        stats = evaluate_order(list(range(37)), rng, n_each=400)
        self.assertEqual(stats["omni"]["miss"], 0.0)
        self.assertEqual(stats["directional"]["miss"], 0.0)
        self.assertGreater(stats["score"], 0.0)
        self.assertLess(prefix_score(stats["mixed"]), 40.0)


if __name__ == "__main__":
    unittest.main()

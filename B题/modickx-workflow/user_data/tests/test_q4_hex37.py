"""HEX37 discovery cover: continuous proof constants, finite set, route, absence certificate."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))

from params import OMEGA_RADIUS, R_MIN  # noqa: E402
from q4_cover import (  # noqa: E402
    APPROACH,
    COVER_HEX37,
    COVER_SQUARE81,
    HEX_DELTA,
    HEX_RING,
    HEX_STEP,
    cover_index,
    cover_n,
    cover_points,
    cover_route,
    cover_route_stats,
    covering_point,
    current_cover_mode,
    p4_covers,
    p4_points,
    rf_covered,
    set_cover_mode,
)
from q4_policy import next_snake_point  # noqa: E402
from q4_runner import Q4Runner  # noqa: E402
from q4_state import Q4State  # noqa: E402
from test_q4_geomsim import GeomSim  # noqa: E402
from test_q4_runner import FakeRobot  # noqa: E402


class Hex37CoverTests(unittest.TestCase):
    def setUp(self):
        set_cover_mode(COVER_HEX37)

    def tearDown(self):
        set_cover_mode(COVER_SQUARE81)

    def test_point_count_unique_origin_and_outer_ring(self):
        pts = cover_points()
        self.assertEqual(current_cover_mode(), COVER_HEX37)
        self.assertEqual(cover_n(), 37)
        self.assertEqual(len(pts), 37)
        keys = {(round(p[0], 6), round(p[1], 6)) for p in pts}
        self.assertEqual(len(keys), 37)
        origin_hits = [i for i, p in enumerate(pts) if float(np.linalg.norm(p)) <= 1e-9]
        self.assertEqual(origin_hits, [cover_index(np.zeros(2))])
        self.assertIsNotNone(cover_index(np.zeros(2)))
        qr = []
        for p in pts:
            r = float(p[1] / (400.0 * math.sqrt(3.0)))
            q = float(p[0] / HEX_STEP - r / 2.0)
            qi, ri = int(round(q)), int(round(r))
            self.assertLess(abs(q - qi) + abs(r - ri), 1e-8)
            self.assertLessEqual(max(abs(qi), abs(ri), abs(qi + ri)), HEX_RING)
            qr.append((qi, ri))
        self.assertEqual(len(set(qr)), 37)
        self.assertIn((0, 0), qr)
        self.assertTrue(any(max(abs(q), abs(r), abs(q + r)) == HEX_RING for q, r in qr))
        self.assertTrue(np.all(np.abs(pts) <= 2400.0 + 1e-8))
        self.assertIsNone(cover_index(np.array([1200.0, 100.0])))
        self.assertIsNotNone(cover_index(np.array([HEX_STEP, 0.0])))

    def test_proof_constants_and_ring4_exclusion(self):
        self.assertAlmostEqual(HEX_DELTA, HEX_STEP / math.sqrt(3.0), places=12)
        self.assertLess(APPROACH + HEX_DELTA, R_MIN)
        self.assertGreater(APPROACH - HEX_DELTA, 0.0)
        ring4_min = HEX_STEP * math.sqrt(12.0)
        y_max = OMEGA_RADIUS + APPROACH
        self.assertGreater(ring4_min, y_max + HEX_DELTA)
        self.assertLess(math.sqrt(3.0), 40.0 / 23.0)
        ring4 = []
        for q in range(-5, 6):
            for r in range(-5, 6):
                if max(abs(q), abs(r), abs(q + r)) == HEX_RING + 1:
                    ring4.append(HEX_STEP * math.sqrt(q * q + q * r + r * r))
        self.assertAlmostEqual(min(ring4), ring4_min, places=9)

    def test_boundary_and_outward_directional_sources(self):
        cases = [
            (np.array([0.0, 0.0]), 0.0),
            (np.array([OMEGA_RADIUS, 0.0]), 0.0),
            (np.array([OMEGA_RADIUS, 0.0]), math.pi),
            (np.array([0.0, OMEGA_RADIUS]), math.pi / 2),
            (np.array([OMEGA_RADIUS / math.sqrt(2), OMEGA_RADIUS / math.sqrt(2)]), math.pi / 4),
            (np.array([OMEGA_RADIUS / math.sqrt(2), OMEGA_RADIUS / math.sqrt(2)]), 5 * math.pi / 4),
            (np.array([-OMEGA_RADIUS, 0.0]), math.pi),
            (np.array([0.0, -OMEGA_RADIUS]), -math.pi / 2),
        ]
        for g, h in cases:
            p = covering_point(g, h)
            self.assertTrue(rf_covered(g, h, p, directional=True), msg=f"g={g} h={h} p={p}")
            self.assertTrue(p4_covers(g, h, directional=True))
            self.assertTrue(p4_covers(g, h, directional=False))
            self.assertIsNotNone(cover_index(p))

    def test_random_positions_headings_and_omni(self):
        rng = np.random.default_rng(20260911)
        for _ in range(500):
            rad = math.sqrt(rng.random()) * OMEGA_RADIUS
            ang = rng.uniform(0.0, 2.0 * math.pi)
            g = rad * np.array([math.cos(ang), math.sin(ang)])
            h = rng.uniform(0.0, 2.0 * math.pi)
            self.assertTrue(p4_covers(g, h, directional=True))
            self.assertTrue(p4_covers(g, h, directional=False))

    def test_finite_lattice_nearest_stays_inside_hex37(self):
        pts = cover_points()
        rng = np.random.default_rng(7)
        y_max = OMEGA_RADIUS + APPROACH
        for _ in range(400):
            rad = y_max * math.sqrt(rng.random())
            ang = rng.uniform(0.0, 2.0 * math.pi)
            y = rad * np.array([math.cos(ang), math.sin(ang)])
            d = float(np.min(np.linalg.norm(pts - y, axis=1)))
            self.assertLessEqual(d, HEX_DELTA + 1e-8)
        for ang in np.linspace(0.0, 2.0 * math.pi, 360, endpoint=False):
            y = y_max * np.array([math.cos(ang), math.sin(ang)])
            d = float(np.min(np.linalg.norm(pts - y, axis=1)))
            self.assertLessEqual(d, HEX_DELTA + 1e-8)

    def test_all_37_no_signal_certifies_absent(self):
        st = Q4State()
        pts = cover_points()
        for p in pts:
            st.apply_measure(2, p, "no_signal")
        self.assertEqual(st.channels[2].status, "certified_absent")
        self.assertEqual(len(st.channels[2].no_signal_p4), 37)
        self.assertEqual(st.channels[2].remaining_cover(), [])
        self.assertTrue(st.channels[2].can_certify_absent() or st.channels[2].status == "certified_absent")

    def test_36_no_signal_does_not_certify(self):
        st = Q4State()
        pts = cover_points()
        for p in pts[:-1]:
            st.apply_measure(3, p, "no_signal")
        self.assertEqual(st.channels[3].status, "unseen")
        self.assertEqual(len(st.channels[3].remaining_cover()), 1)
        self.assertFalse(st.channels[3].can_certify_absent())

    def test_detected_not_rewritten_absent(self):
        st = Q4State()
        st.apply_measure(6, np.zeros(2), "direction", svd_deg=0.0)
        for p in cover_points()[1:]:
            st.apply_measure(6, p, "no_signal")
        self.assertEqual(st.channels[6].status, "detected")
        self.assertFalse(st.channels[6].can_certify_absent())

    def test_hamilton_path_covers_37_without_repeat(self):
        pts = cover_points()
        route = cover_route()
        self.assertEqual(len(route), 37)
        self.assertEqual(len(set(route)), 37)
        self.assertEqual(set(route), set(range(37)))
        self.assertEqual(float(np.linalg.norm(pts[route[0]])), 0.0)
        stats = cover_route_stats()
        self.assertAlmostEqual(stats["total_length"], 36 * HEX_STEP, places=6)
        self.assertAlmostEqual(stats["max_step"], HEX_STEP, places=6)
        self.assertEqual(stats["n_adj_step"], 36)
        self.assertLess(stats["total_length"], 48000.0)
        for a, b in zip(route, route[1:]):
            self.assertAlmostEqual(float(np.linalg.norm(pts[a] - pts[b])), HEX_STEP, places=6)

    def test_next_point_follows_cover_route(self):
        st = Q4State()
        nxt = next_snake_point(st, certificate_mode=True)
        self.assertIsNotNone(nxt)
        self.assertEqual(cover_index(nxt), cover_route()[0])


class Hex37RunnerTests(unittest.TestCase):
    def setUp(self):
        set_cover_mode(COVER_HEX37)

    def tearDown(self):
        set_cover_mode(COVER_SQUARE81)

    def test_geomsim_omni_and_outward_directional(self):
        omni = Q4Runner(GeomSim([{"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False}])).run()
        self.assertEqual(omni["K"], 1)
        self.assertTrue(omni["all_certified"])
        outward = Q4Runner(GeomSim([
            {"k": 3, "g": np.array([1700.0, 0.0]), "r": 1100.0, "directional": True, "psi": 0.0}
        ])).run()
        self.assertEqual(outward["K"], 1)
        self.assertTrue(outward["all_certified"])
        self.assertIsNone(outward["failure"])

    def test_offline_run_certifies_after_all_hex_points(self):
        r = Q4Runner(FakeRobot())
        summary = r.run()
        self.assertIsNone(summary["failure"])
        self.assertTrue(summary["all_certified"])
        self.assertEqual(len(summary["certified_absent"]), 20)
        self.assertEqual(summary["cover_mode"], COVER_HEX37)
        self.assertEqual(r.state.channels[1].no_signal_p4, set(range(37)))
        self.assertEqual(summary["n_cover_visited"], 37)


class Square81StillDefaultTests(unittest.TestCase):
    def test_default_mode_is_square81(self):
        set_cover_mode(COVER_SQUARE81)
        self.assertEqual(current_cover_mode(), COVER_SQUARE81)
        self.assertEqual(cover_n(), 81)
        self.assertEqual(len(p4_points()), 81)
        self.assertEqual(len(cover_points()), 81)
        stats = cover_route_stats()
        self.assertAlmostEqual(stats["total_length"], 48000.0, places=6)


if __name__ == "__main__":
    unittest.main()

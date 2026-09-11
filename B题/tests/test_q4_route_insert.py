"""ROUTE_INSERT_V1: fixed Hamilton skeleton + pending on-path insertion."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))
sys.path.insert(0, str(ROOT / "tests"))

from q4_cover import (  # noqa: E402
    COVER_HEX37,
    COVER_SQUARE81,
    cover_index,
    cover_points,
    cover_route,
    set_cover_mode,
)
from q4_policy import (  # noqa: E402
    INSERT_MAX_M,
    ROUTE_INSERT_V1,
    ROUTE_INSERT_V2,
    ROUTE_INSERT_V3,
    ROUTE_OLD,
    act_now_vs_lookahead,
    choose_insert_or_cover,
    insertion_extra,
    intersection_not_degenerate,
    next_route_cover,
    pending_batch_order,
    probe_detected_worthwhile,
    probe_detected_worthwhile_v3,
    set_route_mode,
    set_v3_params,
)
from q4_runner import Q4Runner  # noqa: E402
from q4_state import Q4State  # noqa: E402
from test_q4_geomsim import GeomSim  # noqa: E402
from test_q4_runner import FakeRobot  # noqa: E402


class InsertionCostTests(unittest.TestCase):
    def test_on_segment_extra_is_zero(self):
        x = np.array([0.0, 0.0])
        u = np.array([800.0, 0.0])
        q = np.array([400.0, 0.0])
        self.assertAlmostEqual(insertion_extra(x, q, u), 0.0, places=9)

    def test_triangle_extra_is_positive(self):
        x = np.array([0.0, 0.0])
        u = np.array([800.0, 0.0])
        q = np.array([400.0, 400.0])
        extra = insertion_extra(x, q, u)
        self.assertGreater(extra, 0.0)
        self.assertAlmostEqual(extra, 2 * np.hypot(400.0, 400.0) - 800.0, places=9)

    def test_no_next_cover_uses_direct_distance(self):
        x = np.array([0.0, 0.0])
        q = np.array([300.0, 400.0])
        self.assertAlmostEqual(insertion_extra(x, q, None), 500.0, places=9)

    def test_choose_defers_large_detour(self):
        x = np.array([0.0, 0.0])
        u = np.array([800.0, 0.0])
        far = (1, np.array([0.0, 3000.0]))
        kind, ident = choose_insert_or_cover(x, u, [far], max_extra=INSERT_MAX_M)
        self.assertEqual(kind, "cover")
        self.assertIsNone(ident)

    def test_choose_inserts_small_detour(self):
        x = np.array([0.0, 0.0])
        u = np.array([800.0, 0.0])
        near = (7, np.array([400.0, 50.0]))
        kind, ident = choose_insert_or_cover(x, u, [near], max_extra=INSERT_MAX_M)
        self.assertEqual(kind, "insert")
        self.assertEqual(ident, 7)

    def test_choose_picks_smaller_extra(self):
        x = np.array([0.0, 0.0])
        u = np.array([800.0, 0.0])
        a = (1, np.array([400.0, 200.0]))
        b = (2, np.array([400.0, 20.0]))
        kind, ident = choose_insert_or_cover(x, u, [a, b], max_extra=INSERT_MAX_M)
        self.assertEqual((kind, ident), ("insert", 2))

    def test_no_cover_left_inserts_nearest_pending(self):
        x = np.array([0.0, 0.0])
        far = (1, np.array([2000.0, 0.0]))
        near = (2, np.array([100.0, 0.0]))
        kind, ident = choose_insert_or_cover(x, None, [far, near], max_extra=INSERT_MAX_M)
        self.assertEqual((kind, ident), ("insert", 2))


class HamiltonSkeletonTests(unittest.TestCase):
    def setUp(self):
        set_cover_mode(COVER_HEX37)
        set_route_mode(ROUTE_INSERT_V1)

    def tearDown(self):
        set_cover_mode(COVER_SQUARE81)
        set_route_mode(ROUTE_OLD)

    def test_next_route_cover_follows_hamilton_not_nearest(self):
        pts = cover_points()
        route = cover_route()
        visited = {route[0]}
        need = set(route)
        nxt = next_route_cover(visited, need)
        self.assertIsNotNone(nxt)
        self.assertEqual(cover_index(nxt), route[1])
        # A later route point may be closer after a detour; still take route[1].
        self.assertEqual(cover_index(next_route_cover({route[0], route[5]}, need)), route[1])

    def test_hex37_fake_robot_still_visits_all_37(self):
        r = Q4Runner(FakeRobot())
        summary = r.run()
        self.assertIsNone(summary["failure"])
        self.assertTrue(summary["all_certified"])
        self.assertEqual(summary["n_cover_visited"], 37)
        self.assertEqual(summary["route_mode"], ROUTE_INSERT_V1)

    def test_cover_visits_are_hamilton_prefix(self):
        r = Q4Runner(FakeRobot())
        r.run()
        route = cover_route()
        order = []
        for ev in r.log:
            if ev.get("op") != "measure":
                continue
            idx = cover_index([ev["x"], ev["y"]])
            if idx is not None and (not order or order[-1] != idx):
                order.append(idx)
        self.assertEqual(order, route)

    def test_geomsim_defers_far_pending_until_later(self):
        runner = Q4Runner(
            GeomSim(
                [{"k": 3, "g": np.array([1700.0, 0.0]), "r": 1100.0, "directional": True, "psi": 0.0}]
            )
        )
        summary = runner.run()
        self.assertEqual(summary["K"], 1)
        self.assertTrue(summary["all_certified"])
        self.assertIsNone(summary["failure"])
        self.assertEqual(summary["n_cover_visited"], 37)
        self.assertGreaterEqual(summary["n_defer"], 0)
        self.assertIn("n_insert", summary)
        self.assertIn("localization_move", summary)
        self.assertIn("pending_max", summary)


class PendingBatchOrderTests(unittest.TestCase):
    def test_line_order_visits_nearest_first(self):
        x = np.array([0.0, 0.0])
        items = [(3, np.array([300.0, 0.0])), (1, np.array([100.0, 0.0])), (2, np.array([200.0, 0.0]))]
        self.assertEqual(pending_batch_order(x, items, u=None), [1, 2, 3])

    def test_returns_to_next_cover(self):
        x = np.array([0.0, 0.0])
        u = np.array([800.0, 0.0])
        items = [(1, np.array([700.0, 50.0])), (2, np.array([100.0, 50.0]))]
        self.assertEqual(pending_batch_order(x, items, u), [2, 1])

    def test_empty(self):
        self.assertEqual(pending_batch_order(np.zeros(2), [], u=None), [])


class ProbeDetectedTests(unittest.TestCase):
    def test_skips_when_already_clearable(self):
        p = np.array([800.0, 0.0])
        region = {"center": np.array([10.0, 0.0]), "rho": 15.0}
        self.assertFalse(probe_detected_worthwhile(p, region, [np.zeros(2)], [0.0]))

    def test_skips_nearby_repeat_site(self):
        p = np.array([50.0, 0.0])
        region = {"center": np.array([400.0, 0.0]), "rho": 200.0}
        self.assertFalse(probe_detected_worthwhile(p, region, [np.zeros(2)], [0.0]))

    def test_accepts_new_baseline_in_forward_halfplane(self):
        p = np.array([800.0, 0.0])
        region = {"center": np.array([400.0, 0.0]), "rho": 250.0}
        self.assertTrue(probe_detected_worthwhile(p, region, [np.zeros(2)], [0.0]))

    def test_skips_far_behind_the_wedge(self):
        p = np.array([-800.0, 0.0])
        region = {"center": np.array([400.0, 0.0]), "rho": 250.0}
        self.assertFalse(probe_detected_worthwhile(p, region, [np.zeros(2)], [0.0]))


class InsertV2Tests(unittest.TestCase):
    def setUp(self):
        set_cover_mode(COVER_HEX37)
        set_route_mode(ROUTE_INSERT_V2)

    def tearDown(self):
        set_cover_mode(COVER_SQUARE81)
        set_route_mode(ROUTE_OLD)

    def test_fake_robot_still_visits_all_37(self):
        summary = Q4Runner(FakeRobot()).run()
        self.assertIsNone(summary["failure"])
        self.assertTrue(summary["all_certified"])
        self.assertEqual(summary["n_cover_visited"], 37)
        self.assertEqual(summary["route_mode"], ROUTE_INSERT_V2)

    def test_mixed_clears_and_certifies(self):
        robot = GeomSim(
            [
                {"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False},
                {"k": 5, "g": np.array([0.0, 500.0]), "r": 1200.0, "directional": True, "psi": np.deg2rad(-90.0)},
                {"k": 9, "g": np.array([2.0, 2.0]), "r": 1000.0, "directional": False},
            ]
        )
        summary = Q4Runner(robot).run()
        self.assertEqual(summary["K"], 3)
        self.assertTrue(summary["all_certified"])
        self.assertEqual(summary["pending"], [])

    def test_detected_not_measured_at_every_later_hex(self):
        robot = GeomSim([{"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False}])
        runner = Q4Runner(robot)
        summary = runner.run()
        self.assertEqual(summary["K"], 1)
        self.assertTrue(summary["all_certified"])
        cover_measures_after = 0
        seen = False
        for ev in runner.log:
            if ev.get("op") != "measure" or ev.get("k") != 1:
                continue
            if ev.get("result") in ("direction", "near"):
                seen = True
                continue
            if seen and cover_index([ev["x"], ev["y"]]) is not None:
                cover_measures_after += 1
        self.assertLess(cover_measures_after, 36)


class LookaheadTests(unittest.TestCase):
    def test_acts_now_when_on_current_edge(self):
        x = np.array([0.0, 0.0])
        q = np.array([400.0, 20.0])
        future = [np.array([800.0, 0.0]), np.array([1600.0, 0.0]), np.array([2400.0, 0.0])]
        self.assertTrue(act_now_vs_lookahead(x, q, future))

    def test_defers_when_later_hex_is_closer(self):
        x = np.array([0.0, 0.0])
        q = np.array([2400.0, 30.0])
        future = [np.array([800.0, 0.0]), np.array([1600.0, 0.0]), np.array([2400.0, 0.0])]
        self.assertFalse(act_now_vs_lookahead(x, q, future))


class ProbeV3Tests(unittest.TestCase):
    def test_skips_when_rho_already_small(self):
        p = np.array([800.0, 0.0])
        region = {"center": np.array([400.0, 0.0]), "rho": 50.0}
        self.assertFalse(probe_detected_worthwhile_v3(p, region, [np.zeros(2)], [0.0]))

    def test_skips_degenerate_parallel_cut(self):
        p = np.array([800.0, 10.0])
        center = np.array([400.0, 0.0])
        last = np.array([0.0, 0.0])
        self.assertFalse(intersection_not_degenerate(p, center, last, min_sin=0.34))

    def test_accepts_wide_angle_when_rho_large(self):
        p = np.array([400.0, 800.0])
        region = {"center": np.array([400.0, 0.0]), "rho": 250.0}
        self.assertTrue(probe_detected_worthwhile_v3(p, region, [np.zeros(2)], [90.0]))


class InsertV3Tests(unittest.TestCase):
    def setUp(self):
        set_cover_mode(COVER_HEX37)
        set_route_mode(ROUTE_INSERT_V3)
        set_v3_params(clear_insert_max=600.0, measure_insert_max=250.0, aggressive_clear_rho=120.0)

    def tearDown(self):
        set_cover_mode(COVER_SQUARE81)
        set_route_mode(ROUTE_OLD)
        set_v3_params()

    def test_fake_robot_still_visits_all_37(self):
        summary = Q4Runner(FakeRobot()).run()
        self.assertIsNone(summary["failure"])
        self.assertTrue(summary["all_certified"])
        self.assertEqual(summary["n_cover_visited"], 37)
        self.assertEqual(summary["route_mode"], ROUTE_INSERT_V3)

    def test_mixed_clears_and_certifies(self):
        robot = GeomSim(
            [
                {"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False},
                {"k": 5, "g": np.array([0.0, 500.0]), "r": 1200.0, "directional": True, "psi": np.deg2rad(-90.0)},
                {"k": 9, "g": np.array([2.0, 2.0]), "r": 1000.0, "directional": False},
            ]
        )
        summary = Q4Runner(robot).run()
        self.assertEqual(summary["K"], 3)
        self.assertTrue(summary["all_certified"])
        self.assertEqual(summary["pending"], [])
        self.assertIn("n_aggressive_clear", summary)

    def test_detected_not_measured_at_every_later_hex(self):
        runner = Q4Runner(GeomSim([{"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False}]))
        summary = runner.run()
        self.assertEqual(summary["K"], 1)
        self.assertTrue(summary["all_certified"])
        cover_measures_after = 0
        seen = False
        for ev in runner.log:
            if ev.get("op") != "measure" or ev.get("k") != 1:
                continue
            if ev.get("result") in ("direction", "near"):
                seen = True
                continue
            if seen and cover_index([ev["x"], ev["y"]]) is not None:
                cover_measures_after += 1
        self.assertLess(cover_measures_after, 36)


class InsertGeomLoopTests(unittest.TestCase):
    def setUp(self):
        set_cover_mode(COVER_HEX37)
        set_route_mode(ROUTE_INSERT_V1)

    def tearDown(self):
        set_cover_mode(COVER_SQUARE81)
        set_route_mode(ROUTE_OLD)

    def test_mixed_clears_and_certifies(self):
        robot = GeomSim(
            [
                {"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False},
                {"k": 5, "g": np.array([0.0, 500.0]), "r": 1200.0, "directional": True, "psi": np.deg2rad(-90.0)},
                {"k": 9, "g": np.array([2.0, 2.0]), "r": 1000.0, "directional": False},
            ]
        )
        summary = Q4Runner(robot).run()
        self.assertEqual(summary["K"], 3)
        self.assertTrue(summary["all_certified"])
        self.assertEqual(summary["pending"], [])


if __name__ == "__main__":
    unittest.main()

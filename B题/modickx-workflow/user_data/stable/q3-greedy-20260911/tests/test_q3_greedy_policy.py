"""Drive shipped greedy helpers: tour vs pending, try-clear after second bearing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))

from q3_greedy_policy import (  # noqa: E402
    APPROACH_M,
    LATERAL_M,
    RAY_STEP_M,
    TOUR_CLEAR_HOP_M,
    bearing_flip_try_clear_points,
    clear_hop_allowed,
    first_bearing_try_clear_points,
    greedy_action_candidates,
    greedy_second_measure_points,
    is_bearing_flip,
    nearby_try_clear_points,
    path_try_clear_points,
    ray_try_clear_near,
    ray_try_clear_points,
    select_next_cover,
    should_process_pending_on_tour,
    try_clear_points_after_second,
)
from q3_state import dist  # noqa: E402


class GreedyTourTests(unittest.TestCase):
    def test_unfinished_tour_at_discovery_site_does_not_process_pending(self):
        s = np.array([0.0, 0.0])
        remaining = [np.array([1200.0, 0.0])]
        self.assertFalse(should_process_pending_on_tour(s, remaining, s, 0.0))

    def test_empty_remaining_cover_processes_pending(self):
        s = np.array([0.0, 0.0])
        pos = np.array([50.0, 0.0])
        self.assertTrue(should_process_pending_on_tour(pos, [], s, 0.0))

    def test_offset_pose_is_good_second_site(self):
        s = np.array([0.0, 0.0])
        pos = np.array([700.0, 180.0])
        remaining = [np.array([1200.0, 0.0])]
        self.assertTrue(should_process_pending_on_tour(pos, remaining, s, 0.0))


class GreedyMeasureClearTests(unittest.TestCase):
    def test_discovery_site_approaches_along_bearing_then_offsets(self):
        s = np.array([0.0, 0.0])
        pts = greedy_second_measure_points(s, 0.0, s)
        self.assertGreaterEqual(len(pts), 2)
        expected = np.array([APPROACH_M, LATERAL_M])
        self.assertTrue(any(dist(p, expected) < 1.0 or dist(p, np.array([APPROACH_M, -LATERAL_M])) < 1.0 for p in pts))

    def test_try_clear_after_second_bearing_returns_one_or_two_points(self):
        s = np.array([0.0, 0.0])
        s2 = np.array([APPROACH_M, LATERAL_M])
        tries = try_clear_points_after_second(s, 0.0, s2, 270.0)
        self.assertGreaterEqual(len(tries), 1)
        self.assertLessEqual(len(tries), 2)
        for p in tries:
            self.assertEqual(p.shape, (2,))
            self.assertTrue(np.all(np.isfinite(p)))

    def test_first_bearing_try_clear_is_two_points_along_ray(self):
        pts = first_bearing_try_clear_points(np.array([0.0, 0.0]), 0.0)
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(float(pts[0][0]), 500.0, places=5)
        self.assertAlmostEqual(float(pts[1][0]), 700.0, places=5)

    def test_ray_try_clear_uses_40m_steps(self):
        pts = ray_try_clear_points(np.array([0.0, 0.0]), 0.0)
        self.assertGreater(len(pts), 10)
        self.assertAlmostEqual(dist(pts[0], pts[1]), RAY_STEP_M, places=6)


class GreedyTourSewnTests(unittest.TestCase):
    def test_select_next_cover_prefers_vertex_along_bearing(self):
        verts = [
            np.array([1200.0, 0.0]),
            np.array([600.0, 1200.0 * np.sin(np.pi / 3.0)]),
            np.array([-600.0, 1200.0 * np.sin(np.pi / 3.0)]),
        ]
        nxt = select_next_cover(np.array([0.0, 0.0]), verts, [(np.array([0.0, 0.0]), 0.0)])
        self.assertLess(dist(nxt, np.array([1200.0, 0.0])), 1.0)

    def test_select_next_cover_stays_if_already_at_a_station(self):
        here = np.array([1200.0, 0.0])
        remaining = [here, np.array([0.0, 0.0])]
        nxt = select_next_cover(here, remaining, [(np.array([0.0, 0.0]), 180.0)])
        self.assertLess(dist(nxt, here), 1.0)

    def test_path_try_clear_samples_aligned_segment_not_orthogonal(self):
        aligned = path_try_clear_points(np.array([0.0, 0.0]), np.array([1200.0, 0.0]), np.array([0.0, 0.0]), 0.0)
        self.assertGreaterEqual(len(aligned), 20)
        self.assertAlmostEqual(float(aligned[0][0]), RAY_STEP_M, places=5)
        ortho = path_try_clear_points(np.array([0.0, 0.0]), np.array([1200.0, 0.0]), np.array([0.0, 0.0]), 90.0)
        self.assertEqual(ortho, [])

    def test_bearing_flip_samples_segment_only_when_opposite(self):
        self.assertTrue(is_bearing_flip(0.0, 180.0))
        self.assertFalse(is_bearing_flip(0.0, 90.0))
        pts = bearing_flip_try_clear_points(np.array([0.0, 0.0]), 0.0, np.array([1200.0, 0.0]), 180.0)
        self.assertGreater(len(pts), 10)
        self.assertEqual(bearing_flip_try_clear_points(np.array([0.0, 0.0]), 0.0, np.array([700.0, 180.0]), 270.0), [])

    def test_nearby_try_clear_caps_hops_while_tour_unfinished(self):
        remaining = [np.array([1200.0, 0.0])]
        far = np.array([700.0, 0.0])
        near = np.array([80.0, 0.0])
        kept = nearby_try_clear_points(np.array([0.0, 0.0]), [far, near], remaining)
        self.assertEqual(len(kept), 1)
        self.assertLess(dist(kept[0], near), 1.0)
        self.assertLessEqual(dist(np.array([0.0, 0.0]), kept[0]), TOUR_CLEAR_HOP_M)
        after = nearby_try_clear_points(np.array([0.0, 0.0]), [far, near], [])
        self.assertEqual(len(after), 2)


class GreedyJointScheduleTests(unittest.TestCase):
    def test_unfinished_tour_at_origin_picks_cover_not_pending_approach(self):
        remaining = [np.array([1200.0, 0.0]), np.array([-1200.0, 0.0])]
        jobs = [{"k": 4, "first_site": np.array([0.0, 0.0]), "first_bearing": 0.0}]
        act = greedy_action_candidates(np.array([0.0, 0.0]), remaining, jobs)
        self.assertIsNotNone(act)
        self.assertEqual(act["kind"], "cover")

    def test_good_second_site_picks_pending_on_unfinished_tour(self):
        remaining = [np.array([1200.0, 0.0])]
        jobs = [{"k": 6, "first_site": np.array([0.0, 0.0]), "first_bearing": 0.0}]
        act = greedy_action_candidates(np.array([700.0, 180.0]), remaining, jobs)
        self.assertEqual(act["kind"], "pending")
        self.assertEqual(act["k"], 6)
        self.assertLess(float(act["cost"]), 1.0)

    def test_after_tour_picks_nearer_pending_not_list_order(self):
        jobs = [
            {"k": 4, "first_site": np.array([0.0, 0.0]), "first_bearing": 180.0},
            {"k": 6, "first_site": np.array([0.0, 0.0]), "first_bearing": 0.0},
        ]
        act = greedy_action_candidates(np.array([700.0, 180.0]), [], jobs)
        self.assertEqual(act["kind"], "pending")
        self.assertEqual(act["k"], 6)

    def test_far_robot_second_measure_does_not_jump_back_to_first_site(self):
        robot = np.array([1200.0, 1039.0])
        pts = greedy_second_measure_points(np.array([0.0, 0.0]), 0.0, robot)
        self.assertTrue(pts)
        self.assertTrue(all(dist(p, np.array([0.0, 0.0])) > 500.0 for p in pts))
        self.assertTrue(all(dist(robot, p) < 200.0 for p in pts))

    def test_ray_near_skips_far_first_site_points(self):
        robot = np.array([1200.0, 0.0])
        pts = ray_try_clear_near(np.array([0.0, 0.0]), 90.0, robot, max_hop=250.0)
        self.assertEqual(pts, [])

    def test_clear_hop_rejects_far_large_rho_allows_certified(self):
        here = np.array([0.0, 0.0])
        far = np.array([2000.0, 0.0])
        near = np.array([80.0, 0.0])
        remaining = [np.array([1200.0, 0.0])]
        self.assertFalse(clear_hop_allowed(here, far, 80.0, remaining))
        self.assertFalse(clear_hop_allowed(here, far, 80.0, []))
        self.assertTrue(clear_hop_allowed(here, near, 80.0, remaining))
        self.assertTrue(clear_hop_allowed(here, np.array([600.0, 0.0]), 15.0, remaining))


if __name__ == "__main__":
    unittest.main()

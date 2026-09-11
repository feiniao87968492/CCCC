"""Offline tests A–D for ACTIVE no-repeat, SAFE snake, cover reuse."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))

from active import generate_fast_candidates, select_fast_point, select_hybrid_point  # noqa: E402
from q3_safe import A_VALUES, clipped_then_full, ordered_safe_route, snake_path_length, snake_route  # noqa: E402
from q3_state import dist, pos_key  # noqa: E402


class ActiveNoRepeatTests(unittest.TestCase):
    def test_subsequent_choices_are_new_positions(self):
        s = np.array([0.0, 0.0])
        tried = {pos_key(s)}
        qs = []
        for _ in range(5):
            choice = select_fast_point(s, 0.0, n_azimuth=8, exclude_positions=tried)
            self.assertIsNotNone(choice)
            key = pos_key(choice.q)
            self.assertNotIn(key, tried)
            qs.append(key)
            tried.add(key)
        self.assertEqual(len(set(qs)), 5)


class SafeSnakeTests(unittest.TestCase):
    def test_full_snake_has_225_points_and_20m_steps(self):
        site = np.array([0.0, 0.0])
        pts = snake_route(site, 0.0)
        self.assertEqual(len(pts), 225)
        self.assertEqual(len(A_VALUES), 75)
        steps = [dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        self.assertLess(max(steps), 21.0)
        self.assertGreater(sum(1 for d in steps if abs(d - 20.0) < 0.05) / len(steps), 0.98)
        self.assertFalse(any(d > 100.0 for d in steps))
        total = snake_path_length(pts)
        self.assertLess(total, 6000.0)
        self.assertGreater(total, 4000.0)

    def test_clip_keeps_snake_order(self):
        site = np.array([0.0, 0.0])
        full = snake_route(site, 90.0)
        drop = {10, 11, 80, 200}
        fake_verts = np.array([[0.0, 800.0], [30.0, 800.0], [0.0, 820.0]])
        kept = ordered_safe_route(site, 90.0, fake_verts)
        idxs = []
        for p, _ in kept:
            for i, q in enumerate(full):
                if dist(p, q) < 1e-6:
                    idxs.append(i)
                    break
        self.assertEqual(idxs, sorted(idxs))
        self.assertGreater(len(kept), 5)
        steps = [dist(kept[i][0], kept[i + 1][0]) for i in range(len(kept) - 1)]
        self.assertLess(np.median(steps), 50.0)

    def test_clipped_failure_falls_back_to_full_snake(self):
        site = np.array([0.0, 0.0])
        far = np.array([[0.0, 50.0], [20.0, 50.0], [0.0, 70.0]])
        clipped, full = clipped_then_full(site, 0.0, far)
        self.assertEqual(len(full), 225)
        self.assertLess(len(clipped), len(full))
        rest = [p for p in full if not any(dist(p, q) < 1e-9 for q in clipped)]
        self.assertEqual(len(clipped) + len(rest), 225)
        idxs_full = list(range(225))
        idx_clip = [next(i for i, q in enumerate(full) if dist(p, q) < 1e-9) for p in clipped]
        self.assertEqual(idx_clip, sorted(idx_clip))


class CoverReuseTests(unittest.TestCase):
    def test_remaining_cover_enters_candidates_and_can_enter_shortlist(self):
        s = np.array([0.0, 0.0])
        verts, _rho_r, c1, _ = generate_fast_candidates(s, 0.0, n_azimuth=8)
        planted = c1 + np.array([15.0, 0.0])
        verts2, _, _, cands = generate_fast_candidates(s, 0.0, remaining_cover=[planted], n_azimuth=8)
        self.assertTrue(any(dist(q, planted) < 1.0 for q in cands))
        hyb = select_hybrid_point(s, 0.0, remaining_cover=[planted], n_azimuth=8, top_k=16)
        self.assertIsNotNone(hyb)
        fst = select_fast_point(s, 0.0, remaining_cover=[planted], n_azimuth=8)
        self.assertTrue(fst.reuse_global or any(dist(q, planted) < 1.0 for q in cands))


if __name__ == "__main__":
    unittest.main()

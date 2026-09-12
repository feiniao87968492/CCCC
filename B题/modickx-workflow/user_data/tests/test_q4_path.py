from __future__ import annotations

import sys
import time
import unittest
from itertools import permutations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from active import shortest_path_length  # noqa: E402
from q4_cover import p4_points  # noqa: E402


def _brute(x, pts):
    arr = [np.asarray(p, dtype=float).reshape(2) for p in pts]
    best = float("inf")
    for perm in permutations(range(len(arr))):
        L = float(np.linalg.norm(arr[perm[0]] - x))
        for i in range(len(perm) - 1):
            L += float(np.linalg.norm(arr[perm[i + 1]] - arr[perm[i]]))
        if L < best:
            best = L
    return best


class PathLengthTests(unittest.TestCase):
    def test_empty_and_single(self):
        x = np.zeros(2)
        self.assertEqual(shortest_path_length(x, []), 0.0)
        self.assertAlmostEqual(shortest_path_length(x, [np.array([3.0, 4.0])]), 5.0, places=9)

    def test_k8_matches_exact_permutation(self):
        rng = np.random.default_rng(4)
        x = rng.normal(size=2)
        pts = [rng.normal(scale=200.0, size=2) for _ in range(8)]
        exact = _brute(x, pts)
        got = shortest_path_length(x, pts)
        self.assertAlmostEqual(got, exact, places=6)

    def test_k9_and_k20_return_finite(self):
        rng = np.random.default_rng(9)
        x = np.zeros(2)
        pts9 = [rng.normal(scale=100.0, size=2) for _ in range(9)]
        pts20 = [rng.normal(scale=100.0, size=2) for _ in range(20)]
        L9 = shortest_path_length(x, pts9)
        L20 = shortest_path_length(x, pts20)
        self.assertTrue(np.isfinite(L9) and L9 > 0.0)
        self.assertTrue(np.isfinite(L20) and L20 > 0.0)

    def test_k81_p4_returns_quickly(self):
        x = np.array([100.0, -50.0])
        pts = list(p4_points())
        t0 = time.perf_counter()
        L = shortest_path_length(x, pts)
        elapsed = time.perf_counter() - t0
        self.assertTrue(np.isfinite(L) and L > 0.0)
        self.assertLess(elapsed, 0.5)

    def test_duplicates_and_illegal_ignored_via_dedup(self):
        x = np.zeros(2)
        p = np.array([600.0, 0.0])
        L = shortest_path_length(x, [p, p.copy(), np.array([600.0, 0.0])])
        self.assertAlmostEqual(L, 600.0, places=9)


if __name__ == "__main__":
    unittest.main()

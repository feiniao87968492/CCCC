"""Path-length benchmark for Q4. Run: python src/q4_bench.py from B题."""
from __future__ import annotations

import time

import numpy as np

from active import route_length_estimate, shortest_path_length
from q4_cover import p4_points


def _time(fn, *args, repeat=3):
    best = float("inf")
    val = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        val = fn(*args)
        best = min(best, time.perf_counter() - t0)
    return val, best


def main() -> None:
    rng = np.random.default_rng(0)
    x = np.zeros(2)
    pts20 = [rng.normal(scale=400.0, size=2) for _ in range(20)]
    pts50 = [rng.normal(scale=400.0, size=2) for _ in range(50)]
    pts81 = list(p4_points())
    print("old shortest_path_length: O(k * k!) permutations; k=20 ~ 2.4e18, k=81 infeasible")
    for name, pts in (("k=20", pts20), ("k=50", pts50), ("k=81 P4", pts81)):
        L, t = _time(shortest_path_length, x, pts)
        print(f"new shortest_path_length {name}: L={L:.3f}  {t*1e3:.3f} ms")
    L_est, t_est = _time(route_length_estimate, x, pts81)
    L_full, t_full = _time(shortest_path_length, x, pts81)
    print(f"ranking estimate k=81: L={L_est:.3f}  {t_est*1e3:.3f} ms")
    print(f"full k=81 after ranking: L={L_full:.3f}  {t_full*1e3:.3f} ms")
    small = [rng.normal(scale=50.0, size=2) for _ in range(7)]
    from itertools import permutations

    def brute():
        best = float("inf")
        arr = small
        for perm in permutations(range(len(arr))):
            L = float(np.linalg.norm(arr[perm[0]] - x))
            for i in range(len(perm) - 1):
                L += float(np.linalg.norm(arr[i + 1] - arr[i])) if False else float(
                    np.linalg.norm(arr[perm[i + 1]] - arr[perm[i]])
                )
            best = min(best, L)
        return best

    b, tb = _time(brute)
    n, tn = _time(shortest_path_length, x, small)
    print(f"k=7 brute vs new: L {b:.6f} vs {n:.6f}  dt={n-b:.3e}  time {tb*1e3:.3f} vs {tn*1e3:.3f} ms")


if __name__ == "__main__":
    main()

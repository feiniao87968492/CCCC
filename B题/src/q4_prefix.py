"""Offline HEX37 equal-length Hamilton prefix scoring. Not used online."""
from __future__ import annotations

import numpy as np

from params import OMEGA_RADIUS, R_MIN
from q4_cover import HEX37_ROUTE_QR, HEX_DIRS, HEX_STEP, _axial_to_xy, cover_points, rf_covered

W_MEAN = 1.0
W_P95 = 0.5
W_COV10 = 8.0
W_COV20 = 5.0


def hex37_cells() -> list[tuple[int, int]]:
    return list(HEX37_ROUTE_QR)


def hex37_adj() -> list[list[int]]:
    pos = {cell: i for i, cell in enumerate(HEX37_ROUTE_QR)}
    adj = [[] for _ in HEX37_ROUTE_QR]
    for i, (q, r) in enumerate(HEX37_ROUTE_QR):
        for dq, dr in HEX_DIRS:
            j = pos.get((q + dq, r + dr))
            if j is not None:
                adj[i].append(j)
    return adj


def validate_hamilton_indices(order) -> None:
    pts = cover_points(mode="HEX37")
    order = [int(i) for i in order]
    if len(order) != 37 or len(set(order)) != 37:
        raise ValueError("not 37 unique indices")
    if float(np.linalg.norm(pts[order[0]])) > 1e-9:
        raise ValueError("must start at origin")
    for a, b in zip(order, order[1:]):
        if abs(float(np.linalg.norm(pts[a] - pts[b])) - HEX_STEP) > 1e-6:
            raise ValueError("non-800 m step")


def rot60(q: int, r: int) -> tuple[int, int]:
    return (-r, q + r)


def reflect_qr(q: int, r: int) -> tuple[int, int]:
    return (q + r, -r)


def transform_path_qr(order, fn) -> list[int]:
    pos = {cell: i for i, cell in enumerate(HEX37_ROUTE_QR)}
    out = []
    for i in order:
        q, r = HEX37_ROUTE_QR[i]
        nq, nr = fn(q, r)
        out.append(pos[(nq, nr)])
    return out


def dihedral_paths(base=None) -> list[list[int]]:
    base = list(range(37)) if base is None else list(base)
    found = []
    seen = set()
    path_qr = [HEX37_ROUTE_QR[i] for i in base]
    fns = [lambda q, r, k=k: _compose_rot(q, r, k) for k in range(6)]
    fns += [lambda q, r, k=k: _compose_rot(*reflect_qr(q, r), k) for k in range(6)]
    for fn in fns:
        order = transform_path_qr(base, fn)
        key = tuple(order)
        if key in seen:
            continue
        seen.add(key)
        validate_hamilton_indices(order)
        found.append(order)
    return found


def _compose_rot(q: int, r: int, k: int) -> tuple[int, int]:
    for _ in range(k % 6):
        q, r = rot60(q, r)
    return q, r


def dfs_hamilton(rng: np.random.Generator, adj=None) -> list[int] | None:
    adj = hex37_adj() if adj is None else adj
    n = 37
    visited = [False] * n
    path: list[int] = []

    def remain_deg(u: int) -> int:
        return sum(1 for v in adj[u] if not visited[v])

    def dfs(u: int) -> bool:
        path.append(u)
        visited[u] = True
        if len(path) == n:
            return True
        nbrs = [v for v in adj[u] if not visited[v]]
        rng.shuffle(nbrs)
        nbrs.sort(key=remain_deg)
        for v in nbrs:
            if dfs(v):
                return True
        visited[u] = False
        path.pop()
        return False

    if dfs(0):
        return list(path)
    return None


def sample_sources(n: int, rng: np.random.Generator, *, extreme: bool = False):
    if extreme:
        ang = rng.uniform(0.0, 2.0 * np.pi, n)
        g = OMEGA_RADIUS * np.stack([np.cos(ang), np.sin(ang)], axis=1)
        heading = ang.copy()
        return g, heading
    rad = np.sqrt(rng.random(n)) * OMEGA_RADIUS
    ang = rng.uniform(0.0, 2.0 * np.pi, n)
    g = rad[:, None] * np.stack([np.cos(ang), np.sin(ang)], axis=1)
    heading = rng.uniform(0.0, 2.0 * np.pi, n)
    return g, heading


def first_detect_indices(order, g, heading, *, directional: bool) -> np.ndarray:
    pts = cover_points(mode="HEX37")[np.asarray(order, dtype=int)]
    g = np.asarray(g, dtype=float).reshape(-1, 2)
    heading = np.asarray(heading, dtype=float).reshape(-1)
    delta = pts[None, :, :] - g[:, None, :]
    dist = np.linalg.norm(delta, axis=2)
    ok = dist <= (R_MIN - 1e-9)
    if directional:
        c = np.cos(heading)[:, None]
        s = np.sin(heading)[:, None]
        dots = delta[:, :, 0] * c + delta[:, :, 1] * s
        ok &= (dist > 1e-12) & (dots > 0.0)
    m = pts.shape[0]
    idx = np.where(ok, np.arange(m, dtype=int), m)
    return idx.min(axis=1)


def summarize_indices(idx: np.ndarray) -> dict:
    idx = np.asarray(idx, dtype=float)
    return {
        "mean_first_detect_index": float(idx.mean()),
        "p95_first_detect_index": float(np.quantile(idx, 0.95)),
        "early_coverage_5": float(np.mean(idx <= 4)),
        "early_coverage_10": float(np.mean(idx <= 9)),
        "early_coverage_15": float(np.mean(idx <= 14)),
        "early_coverage_20": float(np.mean(idx <= 19)),
        "mean_first_detect_distance": float(idx.mean() * HEX_STEP),
        "miss": float(np.mean(idx >= 37)),
    }


def prefix_score(stats: dict) -> float:
    return (
        W_MEAN * stats["mean_first_detect_index"]
        + W_P95 * stats["p95_first_detect_index"]
        - W_COV10 * stats["early_coverage_10"]
        - W_COV20 * stats["early_coverage_20"]
    )


def evaluate_order(order, rng: np.random.Generator, n_each: int = 2000) -> dict:
    validate_hamilton_indices(order)
    g_o, h_o = sample_sources(n_each, rng)
    g_d, h_d = sample_sources(n_each, rng)
    g_e, h_e = sample_sources(n_each // 4, rng, extreme=True)
    omni = summarize_indices(first_detect_indices(order, g_o, h_o, directional=False))
    direc = summarize_indices(first_detect_indices(order, g_d, h_d, directional=True))
    extreme = summarize_indices(first_detect_indices(order, g_e, h_e, directional=True))
    mixed_idx = np.concatenate(
        [
            first_detect_indices(order, g_o, h_o, directional=False),
            first_detect_indices(order, g_d, h_d, directional=True),
        ]
    )
    mixed = summarize_indices(mixed_idx)
    return {
        "omni": omni,
        "directional": direc,
        "extreme_outward": extreme,
        "mixed": mixed,
        "score": prefix_score(mixed),
    }

"""Q4 discovery certificate: 600 m grid P4, 81 points.

Does not call the simulator. Existence only: for every source in Omega and
every heading, some grid point lies strictly inside the 180° RF half-plane
and inside the 1000 m minimum receive radius.

The grid, snake order, index map, and distance matrix are cached.
"""
from __future__ import annotations

import numpy as np
from params import COORD_ABS_LIMIT, R_MIN

P4_STEP = 600.0
P4_INDEX = range(-4, 5)
APPROACH = 500.0
GRID_HALF = P4_STEP / 2.0  # 300
P4_N = 81


def _build_grid() -> tuple[np.ndarray, dict, list[int], np.ndarray]:
    pts = np.array([(P4_STEP * i, P4_STEP * j) for j in P4_INDEX for i in P4_INDEX], dtype=float)
    key_to_idx: dict[tuple[float, float], int] = {}
    for idx, p in enumerate(pts):
        key_to_idx[(round(float(p[0]), 6), round(float(p[1]), 6))] = idx
    snake: list[int] = []
    for row, j in enumerate(P4_INDEX):
        xs = list(P4_INDEX) if row % 2 == 0 else list(reversed(list(P4_INDEX)))
        for i in xs:
            snake.append(key_to_idx[(round(P4_STEP * i, 6), round(P4_STEP * j, 6))])
    dist = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    return pts, key_to_idx, snake, dist


_P4_POINTS, _P4_KEY_TO_IDX, _P4_SNAKE, _P4_DIST = _build_grid()


def p4_points() -> np.ndarray:
    return _P4_POINTS


def p4_index(p) -> int | None:
    """Map a coordinate to a P4 index; None if not on the grid (tol 1e-6 m)."""
    q = np.asarray(p, dtype=float).reshape(2)
    if not np.all(np.isfinite(q)):
        return None
    if np.any(np.abs(q) > COORD_ABS_LIMIT):
        return None
    key = (round(float(q[0]), 6), round(float(q[1]), 6))
    idx = _P4_KEY_TO_IDX.get(key)
    if idx is not None:
        return idx
    snapped = nearest_p4(q)
    if float(np.linalg.norm(q - snapped)) <= 1e-6:
        key = (round(float(snapped[0]), 6), round(float(snapped[1]), 6))
        return _P4_KEY_TO_IDX.get(key)
    return None


def p4_snake_indices() -> list[int]:
    return list(_P4_SNAKE)


def p4_distance_matrix() -> np.ndarray:
    return _P4_DIST


def nearest_p4(y) -> np.ndarray:
    y = np.asarray(y, dtype=float).reshape(2)
    q = np.round(y / P4_STEP)
    q = np.clip(q, -4.0, 4.0)
    return q * P4_STEP


def covering_point(g, heading_rad: float) -> np.ndarray:
    """Constructive witness used in the proof (depends on unknown heading)."""
    g = np.asarray(g, dtype=float).reshape(2)
    d = np.array([np.cos(heading_rad), np.sin(heading_rad)], dtype=float)
    return nearest_p4(g + APPROACH * d)


def rf_covered(g, heading_rad: float, p, *, directional: bool) -> bool:
    g = np.asarray(g, dtype=float).reshape(2)
    p = np.asarray(p, dtype=float).reshape(2)
    v = p - g
    dist = float(np.linalg.norm(v))
    if dist > R_MIN - 1e-9:
        return False
    if not directional:
        return True
    if dist < 1e-12:
        return False
    d = np.array([np.cos(heading_rad), np.sin(heading_rad)], dtype=float)
    return float(np.dot(d, v)) > 0.0


def p4_covers(g, heading_rad: float, *, directional: bool) -> bool:
    pts = p4_points()
    return any(rf_covered(g, heading_rad, p, directional=directional) for p in pts)


def in_bearing_halfplane(p, site, bearing_deg: float) -> bool:
    """Forward open half-plane along a measured bearing (site → source)."""
    p = np.asarray(p, dtype=float).reshape(2)
    s = np.asarray(site, dtype=float).reshape(2)
    rad = np.deg2rad(float(bearing_deg))
    u = np.array([np.cos(rad), np.sin(rad)], dtype=float)
    return float(np.dot(p - s, u)) > 0.0

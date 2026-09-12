"""225-point SAFE corridor as an ordered snake. Never iterate a set."""
from __future__ import annotations

import numpy as np

from q3_state import dist

A_VALUES = [10.0 + 20.0 * j for j in range(75)]  # 10, 30, ..., 1490


def _uv(bearing_deg: float):
    rad = np.deg2rad(float(bearing_deg))
    u = np.array([np.cos(rad), np.sin(rad)])
    v = np.array([-u[1], u[0]])
    return u, v


def snake_route(site, bearing_deg: float) -> list[np.ndarray]:
    """B=-20 forward, B=0 reverse, B=+20 forward. Adjacent steps are 20 m."""
    site = np.asarray(site, dtype=float).reshape(2)
    u, v = _uv(bearing_deg)
    pts: list[np.ndarray] = []
    for A in A_VALUES:
        pts.append(site + A * u + (-20.0) * v)
    for A in reversed(A_VALUES):
        pts.append(site + A * u + 0.0 * v)
    for A in A_VALUES:
        pts.append(site + A * u + 20.0 * v)
    return pts


def safe_grid(site, bearing_deg: float) -> list[np.ndarray]:
    return snake_route(site, bearing_deg)


def cell_may_contain_target(q, f_verts: np.ndarray, slack: float = 35.0) -> bool:
    if f_verts is None or len(f_verts) < 1:
        return True
    q = np.asarray(q, dtype=float)
    v = np.asarray(f_verts, dtype=float)
    crosses = []
    distances = []
    for a, b in zip(v, np.roll(v, -1, axis=0)):
        edge = b - a
        crosses.append(edge[0] * (q-a)[1] - edge[1] * (q-a)[0])
        denom = float(np.dot(edge, edge))
        t = np.clip(np.dot(q-a, edge) / denom, 0., 1.) if denom > 0 else 0.
        distances.append(dist(q, a + t * edge))
    area = abs(float(np.sum(v[:, 0] * np.roll(v[:, 1], -1)
                               - v[:, 1] * np.roll(v[:, 0], -1))))
    inside = area > 1e-10 and (min(crosses) >= -1e-9 or max(crosses) <= 1e-9)
    return inside or min(distances) <= 20.0 + slack


def local_cover_route(verts, robot_pos) -> list[np.ndarray]:
    """Cover a small convex posterior with <=9 radius-20 disks.

    Rotate into principal axes and tile its enclosing rectangle with cells of
    side <=28 m. Every cell lies within 14*sqrt(2)<20 m of its center;
    this covers the continuous polygon, not just sampled points or vertices.
    """
    from geometry import min_enclosing_circle

    if verts is None or len(verts) == 0:
        return []
    v = np.asarray(verts, dtype=float)
    if not np.all(np.isfinite(v)):
        return []
    center, rho = min_enclosing_circle(v)
    if not np.isfinite(rho) or rho > 40.0:
        return []
    if rho <= 20.0:
        return [np.asarray(center)]
    origin = v.mean(axis=0)
    _, _, axes = np.linalg.svd(v-origin, full_matrices=True)
    rotated = (v-origin) @ axes.T
    lo, hi = rotated.min(axis=0), rotated.max(axis=0)
    counts = np.maximum(1, np.ceil((hi-lo)/28.).astype(int))
    if int(np.prod(counts)) > 9:
        return []
    width = (hi-lo)/counts
    points = [origin + (lo + width * [i+.5, j+.5]) @ axes
              for i in range(counts[0]) for j in range(counts[1])]
    route = []
    current = np.asarray(robot_pos)
    while points:
        index = min(range(len(points)), key=lambda i: dist(current, points[i]))
        current = points.pop(index)
        route.append(current)
    return route


def ordered_safe_route(site, bearing_deg: float, f_verts: np.ndarray | None = None) -> list[tuple[np.ndarray, bool]]:
    """Keep snake order. Filter in place; never rebuild from a set."""
    clipped, _full = clipped_then_full(site, bearing_deg, f_verts)
    return [(p, False) for p in clipped]


def clipped_then_full(site, bearing_deg: float, f_verts: np.ndarray | None = None) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Clipped snake first; full snake is the fallback list (same order)."""
    full = snake_route(site, bearing_deg)
    if f_verts is None or len(f_verts) < 1:
        return list(full), list(full)
    clipped = [p for p in full if cell_may_contain_target(p, f_verts)]
    if not clipped:
        return list(full), list(full)
    return clipped, full


def snake_path_length(pts: list[np.ndarray]) -> float:
    if len(pts) < 2:
        return 0.0
    return float(sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)))

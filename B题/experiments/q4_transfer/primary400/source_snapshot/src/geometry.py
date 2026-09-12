"""Q1 forward-wedge localization: feasibility, diameter, minimum enclosing radius."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull

from params import EPS_DEG, OMEGA_RADIUS

DEG = np.pi / 180.0
_PARALLEL = 1e-12
_FEAS_ATOL = 1e-8


def unit(angle_rad: float) -> np.ndarray:
    return np.array([np.cos(angle_rad), np.sin(angle_rad)], dtype=float)


def bearing_to_rad(bearing_deg: float) -> float:
    return float(bearing_deg) * DEG


def wedge_halfplanes(
    site: np.ndarray,
    bearing_deg: float,
    eps_deg: float = EPS_DEG,
) -> tuple[np.ndarray, np.ndarray]:
    """Two closed halfplanes A x <= b for the forward 2-eps wedge."""
    s = np.asarray(site, dtype=float).reshape(2)
    a = bearing_to_rad(bearing_deg)
    eps = float(eps_deg) * DEG
    u_minus = unit(a - eps)
    u_plus = unit(a + eps)
    n1 = np.array([u_minus[1], -u_minus[0]])
    n2 = np.array([-u_plus[1], u_plus[0]])
    A = np.vstack([n1, n2])
    b = np.array([n1 @ s, n2 @ s], dtype=float)
    return A, b


def stack_halfplanes(
    sites: Sequence[np.ndarray],
    bearings_deg: Sequence[float],
    eps_deg: float = EPS_DEG,
) -> tuple[np.ndarray, np.ndarray]:
    if len(sites) != len(bearings_deg):
        raise ValueError("sites and bearings must have the same length")
    if len(sites) == 0:
        return np.zeros((0, 2)), np.zeros((0,))
    blocks = [wedge_halfplanes(s, a, eps_deg) for s, a in zip(sites, bearings_deg)]
    A = np.vstack([bl[0] for bl in blocks])
    b = np.concatenate([bl[1] for bl in blocks])
    return A, b


def _linprog(c, A, b):
    if A.shape[0] == 0:
        return None
    return linprog(
        c,
        A_ub=A,
        b_ub=b,
        bounds=[(None, None), (None, None)],
        method="highs",
    )


def _feasible(A: np.ndarray, b: np.ndarray) -> bool:
    if A.shape[0] == 0:
        return True
    res = _linprog(np.zeros(2), A, b)
    return bool(res is not None and res.success)


def _direction_unbounded(A: np.ndarray, b: np.ndarray, c: np.ndarray) -> bool:
    """True if max c·x is unbounded (c is the maximize direction)."""
    if A.shape[0] == 0:
        return True
    res = _linprog(-np.asarray(c, dtype=float), A, b)
    if res is None:
        return True
    if res.status == 3:
        return True
    return False


def _line_intersection(n_i, b_i, n_j, b_j):
    M = np.vstack([n_i, n_j])
    det = float(np.linalg.det(M))
    if abs(det) <= _PARALLEL * (1.0 + np.linalg.norm(n_i) * np.linalg.norm(n_j)):
        return None
    try:
        x = np.linalg.solve(M, np.array([b_i, b_j], dtype=float))
    except np.linalg.LinAlgError:
        return None
    if not np.all(np.isfinite(x)):
        return None
    return x


def enumerate_vertices(A: np.ndarray, b: np.ndarray, atol: float = _FEAS_ATOL) -> np.ndarray:
    m = A.shape[0]
    pts = []
    for i in range(m):
        for j in range(i + 1, m):
            x = _line_intersection(A[i], b[i], A[j], b[j])
            if x is None:
                continue
            if np.all(A @ x <= b + atol):
                pts.append(x)
    if not pts:
        return np.zeros((0, 2))
    arr = np.unique(np.round(np.asarray(pts), decimals=10), axis=0)
    return arr.astype(float)


def farthest_pair(points: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    pts = np.asarray(points, dtype=float)
    if len(pts) == 0:
        return float("nan"), pts, pts
    if len(pts) == 1:
        return 0.0, pts[0], pts[0]
    best = -1.0
    a = pts[0]
    b = pts[0]
    for i in range(len(pts)):
        d = np.linalg.norm(pts[i:] - pts[i], axis=1)
        k = int(np.argmax(d))
        if d[k] > best:
            best = float(d[k])
            a = pts[i]
            b = pts[i + k]
    return best, a, b


def _circ2(p: np.ndarray, q: np.ndarray) -> tuple[np.ndarray, float]:
    center = 0.5 * (p + q)
    return center, float(np.linalg.norm(p - q) * 0.5)


def _circ3(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, float]:
    d = 2.0 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-18:
        candidates = [_circ2(a, b), _circ2(a, c), _circ2(b, c)]
        return min(candidates, key=lambda cr: cr[1])
    ux = (
        (a[0] ** 2 + a[1] ** 2) * (b[1] - c[1])
        + (b[0] ** 2 + b[1] ** 2) * (c[1] - a[1])
        + (c[0] ** 2 + c[1] ** 2) * (a[1] - b[1])
    ) / d
    uy = (
        (a[0] ** 2 + a[1] ** 2) * (c[0] - b[0])
        + (b[0] ** 2 + b[1] ** 2) * (a[0] - c[0])
        + (c[0] ** 2 + c[1] ** 2) * (b[0] - a[0])
    ) / d
    center = np.array([ux, uy], dtype=float)
    return center, float(np.linalg.norm(center - a))


def _trivial(boundary: list[np.ndarray]) -> tuple[np.ndarray, float]:
    if not boundary:
        return np.zeros(2), 0.0
    if len(boundary) == 1:
        return boundary[0].copy(), 0.0
    if len(boundary) == 2:
        return _circ2(boundary[0], boundary[1])
    return _circ3(boundary[0], boundary[1], boundary[2])


def min_enclosing_circle(points: np.ndarray, rng: np.random.Generator | None = None) -> tuple[np.ndarray, float]:
    pts = [np.asarray(p, dtype=float).reshape(2) for p in np.asarray(points, dtype=float)]
    if not pts:
        return np.zeros(2), 0.0
    order = np.arange(len(pts))
    if rng is None:
        rng = np.random.default_rng(0)
    rng.shuffle(order)
    shuffled = [pts[i] for i in order]

    def welzl(remaining: list[np.ndarray], boundary: list[np.ndarray]) -> tuple[np.ndarray, float]:
        if not remaining or len(boundary) == 3:
            return _trivial(boundary)
        p = remaining[-1]
        center, radius = welzl(remaining[:-1], boundary)
        if np.linalg.norm(p - center) <= radius + 1e-10:
            return center, radius
        return welzl(remaining[:-1], boundary + [p])

    return welzl(shuffled, [])


def diameter_circle_covers(points: np.ndarray, diameter: float, atol: float = 1e-9) -> bool:
    if diameter is None or not np.isfinite(diameter):
        return False
    _, radius = min_enclosing_circle(points)
    return radius <= 0.5 * float(diameter) + atol


def _unique_hull(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=float)
    if len(pts) <= 1:
        return pts
    if len(pts) == 2:
        if np.linalg.norm(pts[0] - pts[1]) < 1e-12:
            return pts[:1]
        return pts
    try:
        hull = ConvexHull(pts)
        return pts[hull.vertices]
    except Exception:
        return pts


@dataclass
class LocalizationResult:
    status: str
    vertices: np.ndarray
    diameter: float | None
    diameter_pair: tuple[np.ndarray, np.ndarray] | None
    mec_center: np.ndarray | None
    mec_radius: float | None
    A: np.ndarray = field(repr=False)
    b: np.ndarray = field(repr=False)

    def contains(self, x: Iterable[float], atol: float = 1e-7) -> bool:
        if self.status == "empty":
            return False
        pt = np.asarray(x, dtype=float).reshape(2)
        if self.A.shape[0] == 0:
            return True
        return bool(np.all(self.A @ pt <= self.b + atol))


def localize_wedges(
    sites: Sequence,
    bearings_deg: Sequence[float],
    eps_deg: float = EPS_DEG,
) -> LocalizationResult:
    A, b = stack_halfplanes(sites, bearings_deg, eps_deg)
    empty_verts = np.zeros((0, 2))
    if A.shape[0] == 0:
        return LocalizationResult(
            status="unbounded",
            vertices=empty_verts,
            diameter=float("inf"),
            diameter_pair=None,
            mec_center=None,
            mec_radius=None,
            A=A,
            b=b,
        )
    if not _feasible(A, b):
        return LocalizationResult(
            status="empty",
            vertices=empty_verts,
            diameter=None,
            diameter_pair=None,
            mec_center=None,
            mec_radius=None,
            A=A,
            b=b,
        )
    unbounded = any(
        _direction_unbounded(A, b, c)
        for c in (np.array([1.0, 0.0]), np.array([-1.0, 0.0]), np.array([0.0, 1.0]), np.array([0.0, -1.0]))
    )
    if unbounded:
        return LocalizationResult(
            status="unbounded",
            vertices=empty_verts,
            diameter=float("inf"),
            diameter_pair=None,
            mec_center=None,
            mec_radius=None,
            A=A,
            b=b,
        )
    verts = enumerate_vertices(A, b)
    if len(verts) == 0:
        return LocalizationResult(
            status="numerical_uncertain",
            vertices=empty_verts,
            diameter=None,
            diameter_pair=None,
            mec_center=None,
            mec_radius=None,
            A=A,
            b=b,
        )
    hull = _unique_hull(verts)
    if len(hull) == 1:
        status = "point"
        diameter = 0.0
        pair = (hull[0], hull[0])
    elif len(hull) == 2:
        status = "segment"
        diameter, a, c = farthest_pair(hull)
        pair = (a, c)
    else:
        status = "polygon"
        diameter, a, c = farthest_pair(hull)
        pair = (a, c)
    center, rho = min_enclosing_circle(hull)
    return LocalizationResult(
        status=status,
        vertices=hull,
        diameter=float(diameter),
        diameter_pair=pair,
        mec_center=center,
        mec_radius=float(rho),
        A=A,
        b=b,
    )


def disk_outer_halfplanes(center: np.ndarray, radius: float, n_tangents: int = 64) -> tuple[np.ndarray, np.ndarray]:
    """Outer approximation of ||x-center|| <= radius by supporting halfplanes."""
    ang = np.linspace(0.0, 2.0 * np.pi, n_tangents, endpoint=False)
    A = np.column_stack([np.cos(ang), np.sin(ang)])
    b = A @ np.asarray(center, dtype=float) + float(radius)
    return A, b


def omega_outer_halfplanes(n_tangents: int = 64) -> tuple[np.ndarray, np.ndarray]:
    return disk_outer_halfplanes(np.zeros(2), OMEGA_RADIUS, n_tangents)

"""Two-bearing geometry for Q4. No simulator I/O, no source truth."""
from __future__ import annotations

import numpy as np

from params import CLEAR_RADIUS, COORD_ABS_LIMIT, OMEGA_RADIUS

BASELINE_MIN_M = 200.0
APPROACH_M = 700.0
LATERAL_M = 180.0
MAX_HOP_M = 2500.0


def _uv(bearing_deg: float) -> tuple[np.ndarray, np.ndarray]:
    rad = np.deg2rad(float(bearing_deg))
    u = np.array([np.cos(rad), np.sin(rad)], dtype=float)
    n = np.array([-u[1], u[0]], dtype=float)
    return u, n


def legal_xy(p) -> bool:
    q = np.asarray(p, dtype=float).reshape(2)
    return bool(np.all(np.isfinite(q)) and np.all(np.abs(q) <= COORD_ABS_LIMIT))


def second_measure_points(s1, bearing_deg: float, robot_pos=None) -> list[np.ndarray]:
    """Orthogonal second sites with usable baseline; no 40 m clear lattice."""
    s1 = np.asarray(s1, dtype=float).reshape(2)
    u, n = _uv(bearing_deg)
    approach = s1 + APPROACH_M * u
    pts = [approach + LATERAL_M * n, approach - LATERAL_M * n]
    if robot_pos is not None:
        x = np.asarray(robot_pos, dtype=float).reshape(2)
        pts.sort(key=lambda p: float(np.linalg.norm(p - x)))
    return [p for p in pts if legal_xy(p)]


def bearing_intersection(s1, a1: float, s2, a2: float):
    """Intersect two bearing *lines* (site → source). None if parallel/degenerate."""
    s1 = np.asarray(s1, dtype=float).reshape(2)
    s2 = np.asarray(s2, dtype=float).reshape(2)
    if float(np.linalg.norm(s1 - s2)) < BASELINE_MIN_M:
        return None
    u1, _n1 = _uv(a1)
    u2, _n2 = _uv(a2)
    det = float(u1[0] * (-u2[1]) - u1[1] * (-u2[0]))
    if abs(det) < 1e-8:
        return None
    A = np.column_stack((u1, -u2))
    try:
        t, s = np.linalg.solve(A, s2 - s1)
    except np.linalg.LinAlgError:
        return None
    p = s1 + float(t) * u1
    if not legal_xy(p):
        return None
    if float(np.linalg.norm(p)) > OMEGA_RADIUS + 200.0:
        return None
    return {"point": p, "t": float(t), "s": float(s), "behind": bool(t < 0 or s < 0)}


def wedge_mec(s1, a1: float, s2, a2: float):
    """MEC of two ±1° wedges. More stable than raw bearing-line intersection under 1° noise."""
    from geometry import min_enclosing_circle
    from localization import _wedge_clip, f1_outer_vertices

    verts = f1_outer_vertices(s1, a1)
    verts = _wedge_clip(verts, np.asarray(s2, dtype=float).reshape(2), float(a2))
    if len(verts) == 0:
        return None
    c, rho = min_enclosing_circle(verts)
    if not legal_xy(c):
        return None
    return {"center": np.asarray(c, dtype=float).reshape(2), "rho": float(rho), "verts": verts}


def third_measure_points(center, bearing_deg: float) -> list[np.ndarray]:
    """One orthogonal hop from the current estimate; finite, not a 40 m lattice."""
    c = np.asarray(center, dtype=float).reshape(2)
    _u, n = _uv(bearing_deg)
    return [p for p in (c + 400.0 * n, c - 400.0 * n) if legal_xy(p)]


def clear_poses(candidate, last_site, verts=None) -> list[np.ndarray]:
    """Poses from which /clear is within 20 m of the estimate."""
    c = np.asarray(candidate, dtype=float).reshape(2)
    last = np.asarray(last_site, dtype=float).reshape(2)
    out = [c]
    if verts is not None and len(verts) >= 1:
        for v in list(verts)[:3]:
            out.append(0.7 * c + 0.3 * np.asarray(v, dtype=float).reshape(2))
    else:
        vec = last - c
        nrm = float(np.linalg.norm(vec))
        if nrm > 1.0:
            out.append(c + (CLEAR_RADIUS * 0.5 / nrm) * vec)
    seen = set()
    uniq = []
    for p in out:
        if not legal_xy(p):
            continue
        key = (round(float(p[0]), 1), round(float(p[1]), 1))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(np.asarray(p, dtype=float).reshape(2))
    return uniq[:4]


def hop_ok(from_pos, to_pos) -> bool:
    return float(np.linalg.norm(np.asarray(to_pos, float) - np.asarray(from_pos, float))) <= MAX_HOP_M

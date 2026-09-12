"""Two-bearing geometry for Q4. No simulator I/O, no source truth."""
from __future__ import annotations

import numpy as np

from params import CLEAR_RADIUS, COORD_ABS_LIMIT, EPS_DEG, NEAR_RADIUS, OMEGA_RADIUS, R_MAX

BASELINE_MIN_M = 200.0
APPROACH_M = 700.0
LATERAL_M = 180.0
MAX_HOP_M = 2500.0

# Explicit numerical envelope for the API's two-decimal bearing quantization.
# The contest's physical error bound remains EPS_DEG = 1 degree.
BEARING_ENVELOPE_DEG = EPS_DEG + 0.005


def _clip_convex(verts, normal, offset):
    """Clip cyclic convex vertices without rebuilding a Qhull at every edge."""
    if len(verts) == 0:
        return verts
    distances = verts @ normal - offset
    if np.all(distances <= 1e-10):
        return verts
    if np.all(distances > 1e-10):
        return np.zeros((0, 2))
    out = []
    previous, d_previous = verts[-1], distances[-1]
    for current, d_current in zip(verts, distances):
        if (d_current <= 1e-10) != (d_previous <= 1e-10):
            out.append(previous + d_previous / (d_previous - d_current) * (current - previous))
        if d_current <= 1e-10:
            out.append(current)
        previous, d_previous = current, d_current
    unique = []
    for p in out:
        if not unique or np.linalg.norm(p - unique[-1]) > 1e-9:
            unique.append(p)
    if len(unique) > 1 and np.linalg.norm(unique[0] - unique[-1]) < 1e-9:
        unique.pop()
    return np.asarray(unique, dtype=float).reshape(-1, 2)


def history_region(history):
    """Outer feasible polygon from ALL positive observations, independent of RF type.

    no_signal cannot remove a disk in Q4. Circumscribed disk polygons and
    forward wedges retain every location consistent with the observations.
    """
    from geometry import disk_outer_halfplanes, min_enclosing_circle, wedge_halfplanes

    positive = [h for h in history if h["result"] in ("direction", "near")]
    if not positive:
        return None
    r = OMEGA_RADIUS
    verts = np.array([[-r, -r], [r, -r], [r, r], [-r, r]], dtype=float)
    constraints = [disk_outer_halfplanes(np.zeros(2), r, 48)]
    for h in positive:
        site = np.asarray(h["pos"], dtype=float)
        if h["result"] == "direction":
            constraints.append(wedge_halfplanes(site, h["svd"], BEARING_ENVELOPE_DEG))
            constraints.append(disk_outer_halfplanes(site, R_MAX, 48))
        else:
            constraints.append(disk_outer_halfplanes(site, NEAR_RADIUS, 48))
    for A, b in constraints:
        for n, offset in zip(A, b):
            verts = _clip_convex(verts, n, offset)
            if len(verts) == 0:
                return None
    center, rho = min_enclosing_circle(verts)
    # Verify the radius against every vertex before using it as a certificate.
    rho = max(float(rho), float(np.max(np.linalg.norm(verts - center, axis=1))))
    return dict(center=center, rho=float(rho), verts=verts)


def optical_cover_points(verts) -> list[np.ndarray]:
    """Finite 20 m optical cover of a polygon; no RF coverage assumption.

    Rotate to its principal axis and intersect it with square cells of side
    28 m. Each clipped cell fits in its square's radius 14*sqrt(2) < 20 circle;
    its minimum enclosing circle is no larger. Thus clearing these centers
    covers the entire continuous polygon, including edges and degenerate sets.
    """
    from geometry import min_enclosing_circle

    verts = np.asarray(verts, dtype=float).reshape(-1, 2)
    if len(verts) == 0:
        return []
    center, rho = min_enclosing_circle(verts)
    rho = max(float(rho), float(np.max(np.linalg.norm(verts - center, axis=1))))
    if rho <= CLEAR_RADIUS - 1e-6:
        return [center]
    _, _, axes = np.linalg.svd(verts - center, full_matrices=False)
    rotated = (verts - center) @ axes.T
    side = CLEAR_RADIUS * 1.4
    lower = np.floor(rotated.min(axis=0) / side).astype(int)
    upper = np.floor(rotated.max(axis=0) / side).astype(int)
    points = []
    for i in range(lower[0], upper[0] + 1):
        for j in range(lower[1], upper[1] + 1):
            cell = rotated
            for axis, index in enumerate((i, j)):
                n = np.eye(2)[axis]
                cell = _clip_convex(cell, n, (index + 1) * side)
                cell = _clip_convex(cell, -n, -index * side)
            if len(cell):
                c, radius = min_enclosing_circle(cell)
                radius = max(float(radius), float(np.max(np.linalg.norm(cell - c, axis=1))))
                if radius > CLEAR_RADIUS + 1e-6:
                    # Numerical degeneration in MEC cannot invalidate the grid proof.
                    c = side * (np.array([i, j], dtype=float) + 0.5)
                points.append(c @ axes + center)
    return points


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

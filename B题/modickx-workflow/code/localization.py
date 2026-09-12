"""Q2 layered robust second-point selection around MEC(F1)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from geometry import (
    disk_outer_halfplanes,
    enumerate_vertices,
    min_enclosing_circle,
    omega_outer_halfplanes,
    unit,
    wedge_halfplanes,
    _feasible,
    _unique_hull,
)
from params import COORD_ABS_LIMIT, EPS_DEG, NEAR_RADIUS, R_MAX, R_MIN, SPEED

DEG = np.pi / 180.0
N_TANGENTS = 48
BOUNDARY_SAMPLES = 96
DIR_BEARING_STEP_DEG = 2.0


def theoretical_sector_rho(r_max: float = R_MAX, eps_deg: float = EPS_DEG) -> float:
    return float(r_max / (2.0 * np.cos(np.deg2rad(eps_deg))))


def theoretical_sector_center(s: np.ndarray, bearing_deg: float, r_max: float = R_MAX, eps_deg: float = EPS_DEG) -> np.ndarray:
    rho0 = theoretical_sector_rho(r_max, eps_deg)
    return np.asarray(s, dtype=float) + rho0 * unit(np.deg2rad(bearing_deg))


def f1_outer_vertices(s: np.ndarray, bearing_deg: float, n_tangents: int = N_TANGENTS) -> np.ndarray:
    """Convex outer polygon containing F1 (5 m hole ignored)."""
    s = np.asarray(s, dtype=float).reshape(2)
    A1, b1 = wedge_halfplanes(s, bearing_deg)
    A2, b2 = omega_outer_halfplanes(n_tangents)
    A3, b3 = disk_outer_halfplanes(s, R_MAX, n_tangents)
    A = np.vstack([A1, A2, A3])
    b = np.concatenate([b1, b2, b3])
    if not _feasible(A, b):
        return np.zeros((0, 2))
    verts = enumerate_vertices(A, b, atol=1e-6)
    if len(verts) == 0:
        return verts
    return _unique_hull(verts)


def _sample_boundary(verts: np.ndarray, n: int = BOUNDARY_SAMPLES) -> np.ndarray:
    if len(verts) == 0:
        return verts
    if len(verts) == 1:
        return verts.copy()
    closed = np.vstack([verts, verts[0]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    total = float(np.sum(seg))
    if total <= 1e-12:
        return verts.copy()
    t = np.linspace(0.0, total, n, endpoint=False)
    acc = np.concatenate([[0.0], np.cumsum(seg)])
    pts = []
    j = 0
    for ti in t:
        while j + 1 < len(acc) and acc[j + 1] < ti:
            j += 1
        span = acc[j + 1] - acc[j]
        a = 0.0 if span <= 1e-12 else (ti - acc[j]) / span
        pts.append((1.0 - a) * closed[j] + a * closed[j + 1])
    return np.unique(np.round(np.vstack([verts, np.asarray(pts)]), decimals=8), axis=0)


def in_c_guaranteed(q: np.ndarray, s: np.ndarray, f1_points: np.ndarray, atol: float = 1e-6) -> bool:
    if len(f1_points) == 0:
        return False
    q = np.asarray(q, dtype=float).reshape(2)
    s = np.asarray(s, dtype=float).reshape(2)
    d_q = np.linalg.norm(f1_points - q, axis=1)
    d_s = np.linalg.norm(f1_points - s, axis=1)
    return bool(np.all(d_q <= np.maximum(R_MIN, d_s) + atol))


def _legal(q: np.ndarray) -> bool:
    return bool(np.all(np.abs(q) <= COORD_ABS_LIMIT))


def _clip_halfplane(verts: np.ndarray, n: np.ndarray, offset: float) -> np.ndarray:
    """Keep n·x <= offset (Sutherland–Hodgman)."""
    if len(verts) == 0:
        return verts
    out = []
    prev = verts[-1]
    prev_in = n @ prev <= offset + 1e-10
    for cur in verts:
        cur_in = n @ cur <= offset + 1e-10
        if cur_in:
            if not prev_in:
                d = n @ (cur - prev)
                if abs(d) > 1e-14:
                    t = (offset - n @ prev) / d
                    out.append(prev + t * (cur - prev))
            out.append(cur)
        elif prev_in:
            d = n @ (cur - prev)
            if abs(d) > 1e-14:
                t = (offset - n @ prev) / d
                out.append(prev + t * (cur - prev))
        prev = cur
        prev_in = cur_in
    if not out:
        return np.zeros((0, 2))
    return _unique_hull(np.asarray(out, dtype=float))


def _wedge_clip(verts: np.ndarray, site: np.ndarray, bearing_deg: float) -> np.ndarray:
    A, b = wedge_halfplanes(site, bearing_deg)
    out = verts
    for i in range(A.shape[0]):
        out = _clip_halfplane(out, A[i], b[i])
        if len(out) == 0:
            return out
    return out


def _rho_points(pts: np.ndarray) -> float:
    if len(pts) == 0:
        return float("nan")
    if len(pts) == 1:
        return 0.0
    _, r = min_enclosing_circle(pts)
    return float(r)


def _angle_deg(vec: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(vec[1], vec[0]))) % 360.0


def _angle_diff_deg(a: np.ndarray, b: float) -> np.ndarray:
    d = (a - b + 180.0) % 360.0 - 180.0
    return np.abs(d)


def evaluate_J(q: np.ndarray, s: np.ndarray, f1_verts: np.ndarray, samples: np.ndarray | None = None) -> dict:
    """Ranking estimate of J(q); not a clearance certificate."""
    q = np.asarray(q, dtype=float).reshape(2)
    s = np.asarray(s, dtype=float).reshape(2)
    if samples is None:
        samples = _sample_boundary(f1_verts)
    values = []

    d_q = np.linalg.norm(samples - q, axis=1)
    d_s = np.linalg.norm(samples - s, axis=1)
    near_pts = samples[d_q <= NEAR_RADIUS + 1e-9]
    if len(near_pts):
        values.append(min(5.0, _rho_points(near_pts)))

    no_pts = samples[d_q > np.maximum(R_MIN, d_s) + 1e-9]
    if len(no_pts):
        values.append(_rho_points(no_pts))

    far = samples[d_q > NEAR_RADIUS + 1e-9]
    if len(far):
        angs = np.degrees(np.arctan2(far[:, 1] - q[1], far[:, 0] - q[0])) % 360.0
        span_lo, span_hi = _angular_span(angs)
        probes = _angle_grid(span_lo, span_hi, DIR_BEARING_STEP_DEG)
        worst = 0.0
        any_dir = False
        for b in probes:
            keep = far[_angle_diff_deg(angs, float(b)) <= EPS_DEG + 1e-9]
            if len(keep) == 0:
                continue
            any_dir = True
            worst = max(worst, _rho_points(keep))
        if any_dir:
            values.append(worst)

    if not values:
        return {"J": float("inf"), "branches": []}
    return {"J": float(max(values)), "branches": values}


def _angular_span(angles_deg: np.ndarray) -> tuple[float, float]:
    a = np.sort(angles_deg % 360.0)
    if len(a) == 1:
        return float(a[0]), float(a[0])
    a2 = np.concatenate([a, a[:1] + 360.0])
    gaps = np.diff(a2)
    k = int(np.argmax(gaps))
    lo = float(a2[k + 1] % 360.0)
    hi = float(a2[k] % 360.0)
    return lo, hi


def _angle_grid(lo: float, hi: float, step: float) -> np.ndarray:
    if abs(((hi - lo + 180) % 360) - 180) < 1e-9:
        return np.array([lo])
    span = (hi - lo) % 360.0
    n = max(1, int(np.ceil(span / step)))
    return (lo + np.arange(n + 1) * (span / n)) % 360.0


def _polar_ring(center: np.ndarray, radius: float, n_azimuth: int) -> list[np.ndarray]:
    if radius <= 1e-12:
        return [center.copy()]
    ang = np.linspace(0.0, 2.0 * np.pi, n_azimuth, endpoint=False)
    return [center + radius * np.array([np.cos(a), np.sin(a)]) for a in ang]


@dataclass
class SecondPointResult:
    s: np.ndarray
    bearing_deg: float
    c1: np.ndarray
    rho1: float
    R_core: float
    F1_vertices: np.ndarray
    candidates: list[dict]
    q_star: np.ndarray
    J_star: float
    travel_s: float
    claim: str = "candidate_set_recommendation"
    layers_present: set[str] = field(default_factory=set)


def select_second_point(
    s,
    bearing_deg: float,
    robot_pos=None,
    n_azimuth: int = 24,
    refine: bool = True,
    explore_width: float = 400.0,
) -> SecondPointResult:
    s = np.asarray(s, dtype=float).reshape(2)
    sd = s if robot_pos is None else np.asarray(robot_pos, dtype=float).reshape(2)
    verts = f1_outer_vertices(s, bearing_deg)
    if len(verts) == 0:
        raise RuntimeError("F1 outer polygon is empty")
    c1, rho1 = min_enclosing_circle(verts)
    rho1 = float(rho1)
    R_core = float(R_MIN - rho1)
    if R_core <= 0:
        # Outer approximation should not exceed 1000 m; fall back to a tiny core.
        R_core = 1.0

    u_a = unit(np.deg2rad(bearing_deg))
    lat = np.array([-u_a[1], u_a[0]])
    raw: list[tuple[str, np.ndarray]] = []

    # A-layer: C_core
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        for q in _polar_ring(c1, frac * R_core, 1 if frac == 0.0 else n_azimuth):
            raw.append(("A", q))
    raw.append(("A", 0.5 * (s + c1)))
    raw.append(("A", c1 + 0.5 * R_core * lat))
    raw.append(("A", c1 - 0.5 * R_core * lat))

    # B/C rings about c1, classified by C_guaranteed
    samples = _sample_boundary(verts)
    for extra in (0.5 * R_core, 200.0, 400.0, explore_width):
        rad = R_core + extra
        for q in _polar_ring(c1, rad, n_azimuth):
            if in_c_guaranteed(q, s, samples):
                raw.append(("B", q))
            else:
                raw.append(("C", q))
    # 90-degree heuristic laterals just outside the core
    raw.append(("B" if in_c_guaranteed(c1 + R_core * lat, s, samples) else "C", c1 + (R_core + 150.0) * lat))
    raw.append(("B" if in_c_guaranteed(c1 - R_core * lat, s, samples) else "C", c1 - (R_core + 150.0) * lat))
    raw.append(("s", s.copy()))

    seen = set()
    candidates = []
    for layer, q in raw:
        q = np.asarray(q, dtype=float).reshape(2)
        if not _legal(q):
            continue
        key = (round(q[0], 3), round(q[1], 3), layer)
        if key in seen:
            continue
        seen.add(key)
        if layer == "A" and np.linalg.norm(q - c1) > R_core + 1e-6:
            continue
        ev = evaluate_J(q, s, verts, samples=samples)
        candidates.append(
            {
                "layer": layer,
                "q": q,
                "J": ev["J"],
                "travel_s": float(np.linalg.norm(q - sd) / SPEED),
            }
        )

    if refine and candidates:
        finite = [c for c in candidates if np.isfinite(c["J"])]
        finite.sort(key=lambda c: (c["J"], c["travel_s"]))
        seeds = finite[:3]
        step = max(5.0, R_core / 16.0)
        for seed in seeds:
            for dx in np.linspace(-2 * step, 2 * step, 5):
                for dy in np.linspace(-2 * step, 2 * step, 5):
                    q = seed["q"] + np.array([dx, dy])
                    if not _legal(q):
                        continue
                    key = (round(q[0], 3), round(q[1], 3), "refine")
                    if key in seen:
                        continue
                    seen.add(key)
                    ev = evaluate_J(q, s, verts, samples=samples)
                    layer = "A" if np.linalg.norm(q - c1) <= R_core + 1e-6 else "refine"
                    candidates.append(
                        {
                            "layer": layer,
                            "q": q,
                            "J": ev["J"],
                            "travel_s": float(np.linalg.norm(q - sd) / SPEED),
                        }
                    )

    finite = [c for c in candidates if np.isfinite(c["J"])]
    if not finite:
        raise RuntimeError("no finite J(q) candidate")
    finite.sort(key=lambda c: (c["J"], c["travel_s"]))
    best = finite[0]
    return SecondPointResult(
        s=s,
        bearing_deg=float(bearing_deg),
        c1=c1,
        rho1=rho1,
        R_core=R_core,
        F1_vertices=verts,
        candidates=candidates,
        q_star=best["q"],
        J_star=float(best["J"]),
        travel_s=float(best["travel_s"]),
        layers_present={c["layer"] for c in candidates},
    )

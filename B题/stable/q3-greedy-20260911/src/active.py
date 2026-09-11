"""FAST_ACTIVE and HYBRID_ACTIVE. Do not change Z/F updates or rho<=20 certificates."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations

import numpy as np

from geometry import min_enclosing_circle, unit
from localization import (
    _polar_ring,
    _sample_boundary,
    evaluate_J,
    f1_outer_vertices,
    in_c_guaranteed,
    select_second_point,
)
from params import CLEAR_RADIUS, COORD_ABS_LIMIT, R_MIN, SPEED

STRATEGIES = ("SAFE", "ROBUST", "FAST", "HYBRID")
HEX_COVER = [np.array([0.0, 0.0])] + [
    1200.0 * np.array([np.cos(j * np.pi / 3.0), np.sin(j * np.pi / 3.0)]) for j in range(6)
]
# Implementation parameters, not contest constants.
D_PERP_MIN = 80.0
PHI_MIN_DEG = 25.0
TOP_K_DEFAULT = 8
MAX_EXTRA_MEASURE = 6


def shortest_path_length(x: np.ndarray, pts: list[np.ndarray]) -> float:
    if not pts:
        return 0.0
    x = np.asarray(x, dtype=float).reshape(2)
    arr = [np.asarray(p, dtype=float).reshape(2) for p in pts]
    best = float("inf")
    for perm in permutations(range(len(arr))):
        L = float(np.linalg.norm(arr[perm[0]] - x))
        for i in range(len(perm) - 1):
            L += float(np.linalg.norm(arr[perm[i + 1]] - arr[perm[i]]))
        if L < best:
            best = L
    return best


def d_perp(q, s, bearing_deg: float) -> float:
    u = unit(np.deg2rad(bearing_deg))
    v = np.asarray(q, dtype=float) - np.asarray(s, dtype=float)
    return float(abs(v[0] * u[1] - v[1] * u[0]))


def phi_min_deg(q, s, f_points: np.ndarray) -> float:
    q = np.asarray(q, dtype=float).reshape(2)
    s = np.asarray(s, dtype=float).reshape(2)
    if len(f_points) == 0:
        return 0.0
    vals = []
    for g in f_points:
        a = g - s
        b = g - q
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na < 1e-9 or nb < 1e-9:
            continue
        c = float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))
        vals.append(float(np.degrees(np.arccos(c))))
    return float(min(vals)) if vals else 0.0


def r_min_at(g, receptions: list[np.ndarray]) -> float:
    g = np.asarray(g, dtype=float).reshape(2)
    lo = R_MIN
    for p in receptions:
        lo = max(lo, float(np.linalg.norm(g - np.asarray(p, dtype=float))))
    return lo


def in_C_k(q, f_points: np.ndarray, receptions: list[np.ndarray], atol: float = 1e-6) -> bool:
    """q in C_k iff ||q-g|| <= r_min(g) for all g in the current location set."""
    if len(f_points) == 0:
        return False
    q = np.asarray(q, dtype=float).reshape(2)
    for g in f_points:
        if np.linalg.norm(q - g) > r_min_at(g, receptions) + atol:
            return False
    return True


@dataclass
class ActiveChoice:
    q: np.ndarray
    method: str
    in_C: bool
    d_perp: float
    phi_min: float
    travel_s: float
    reuse_global: bool
    L_remain: float
    J: float | None = None
    claim: str = "candidate_set_recommendation"


def _legal(q: np.ndarray) -> bool:
    return bool(np.all(np.abs(q) <= COORD_ABS_LIMIT))


def _excluded(q, exclude) -> bool:
    if not exclude:
        return False
    qx, qy = float(q[0]), float(q[1])
    for e in exclude:
        if abs(qx - float(e[0])) < 0.5 and abs(qy - float(e[1])) < 0.5:
            return True
    return False


def generate_fast_candidates(
    s,
    bearing_deg: float,
    robot_pos=None,
    remaining_cover: list | None = None,
    n_azimuth: int = 12,
    f_verts: np.ndarray | None = None,
    exclude_positions=None,
) -> tuple[np.ndarray, float, np.ndarray, list[np.ndarray]]:
    s = np.asarray(s, dtype=float).reshape(2)
    x = s if robot_pos is None else np.asarray(robot_pos, dtype=float).reshape(2)
    verts = np.asarray(f_verts, dtype=float) if f_verts is not None and len(f_verts) else f1_outer_vertices(s, bearing_deg)
    c1, rho1 = min_enclosing_circle(verts)
    R_core = max(1.0, float(R_MIN - rho1))
    u_a = unit(np.deg2rad(bearing_deg))
    lat = np.array([-u_a[1], u_a[0]])
    qs: list[np.ndarray] = []
    for frac in (0.0, 0.5, 1.0):
        qs.extend(_polar_ring(c1, frac * R_core, 1 if frac == 0.0 else n_azimuth))
    qs.append(c1 + 0.7 * R_core * lat)
    qs.append(c1 - 0.7 * R_core * lat)
    if remaining_cover:
        for p in remaining_cover:
            qs.append(np.asarray(p, dtype=float).reshape(2))
    # few exploration points just outside the core
    qs.extend(_polar_ring(c1, R_core + 200.0, max(6, n_azimuth // 2)))
    out = []
    seen = set()
    for q in qs:
        if not _legal(q):
            continue
        key = (round(float(q[0]), 2), round(float(q[1]), 2))
        if key in seen:
            continue
        if _excluded(q, exclude_positions):
            continue
        seen.add(key)
        out.append(q)
    return verts, R_core, np.asarray(c1, dtype=float), out


def _rank_tuple(q, s, bearing, x, verts, samples, remaining_cover, receptions) -> tuple:
    in_c = in_C_k(q, samples, receptions)
    dp = d_perp(q, s, bearing)
    phi = phi_min_deg(q, s, samples[:: max(1, len(samples) // 16)])
    reuse = False
    if remaining_cover:
        reuse = any(np.linalg.norm(q - np.asarray(p, dtype=float)) < 1.0 for p in remaining_cover)
    rest = []
    if remaining_cover:
        rest = [np.asarray(p, dtype=float) for p in remaining_cover if np.linalg.norm(q - np.asarray(p, dtype=float)) >= 1.0]
    L = float(np.linalg.norm(q - x)) + shortest_path_length(q, rest)
    travel = float(np.linalg.norm(q - x) / SPEED)
    # lex: in_C, not degenerate, reuse, then smaller L and travel, larger dp/phi
    deg = 0 if (dp < D_PERP_MIN or phi < PHI_MIN_DEG) else 1
    return (int(in_c), deg, int(reuse), -L, -travel, dp, phi)


def select_fast_point(
    s,
    bearing_deg: float,
    robot_pos=None,
    remaining_cover: list | None = None,
    receptions: list | None = None,
    n_azimuth: int = 12,
    exclude_positions=None,
    f_verts=None,
) -> ActiveChoice | None:
    s = np.asarray(s, dtype=float).reshape(2)
    x = s if robot_pos is None else np.asarray(robot_pos, dtype=float).reshape(2)
    rec = receptions if receptions is not None else [s]
    verts, _, _, cands = generate_fast_candidates(
        s, bearing_deg, x, remaining_cover, n_azimuth, f_verts=f_verts, exclude_positions=exclude_positions
    )
    if not cands:
        return None
    samples = _sample_boundary(verts)
    ranked = sorted(cands, key=lambda q: _rank_tuple(q, s, bearing_deg, x, verts, samples, remaining_cover, rec), reverse=True)
    q = ranked[0]
    rest = []
    if remaining_cover:
        rest = [np.asarray(p, dtype=float) for p in remaining_cover if np.linalg.norm(q - np.asarray(p, dtype=float)) >= 1.0]
    return ActiveChoice(
        q=q,
        method="FAST",
        in_C=in_C_k(q, samples, rec),
        d_perp=d_perp(q, s, bearing_deg),
        phi_min=phi_min_deg(q, s, samples[:: max(1, len(samples) // 16)]),
        travel_s=float(np.linalg.norm(q - x) / SPEED),
        reuse_global=any(np.linalg.norm(q - np.asarray(p, dtype=float)) < 1.0 for p in (remaining_cover or [])),
        L_remain=float(np.linalg.norm(q - x)) + shortest_path_length(q, rest),
        J=None,
    )


def select_hybrid_point(
    s,
    bearing_deg: float,
    robot_pos=None,
    remaining_cover: list | None = None,
    receptions: list | None = None,
    top_k: int = TOP_K_DEFAULT,
    n_azimuth: int = 12,
    exclude_positions=None,
    f_verts=None,
) -> ActiveChoice | None:
    s = np.asarray(s, dtype=float).reshape(2)
    x = s if robot_pos is None else np.asarray(robot_pos, dtype=float).reshape(2)
    rec = receptions if receptions is not None else [s]
    verts, _, _, cands = generate_fast_candidates(
        s, bearing_deg, x, remaining_cover, n_azimuth, f_verts=f_verts, exclude_positions=exclude_positions
    )
    if not cands:
        return None
    samples = _sample_boundary(verts)
    ranked = sorted(cands, key=lambda q: _rank_tuple(q, s, bearing_deg, x, verts, samples, remaining_cover, rec), reverse=True)
    top = ranked[: max(1, int(top_k))]
    best = None
    best_j = float("inf")
    best_travel = float("inf")
    for q in top:
        j = float(evaluate_J(q, s, verts, samples=samples)["J"])
        travel = float(np.linalg.norm(q - x) / SPEED)
        if (j, travel) < (best_j, best_travel):
            best_j, best_travel, best = j, travel, q
    q = best
    rest = []
    if remaining_cover:
        rest = [np.asarray(p, dtype=float) for p in remaining_cover if np.linalg.norm(q - np.asarray(p, dtype=float)) >= 1.0]
    return ActiveChoice(
        q=q,
        method="HYBRID",
        in_C=in_C_k(q, samples, rec),
        d_perp=d_perp(q, s, bearing_deg),
        phi_min=phi_min_deg(q, s, samples[:: max(1, len(samples) // 16)]),
        travel_s=best_travel,
        reuse_global=any(np.linalg.norm(q - np.asarray(p, dtype=float)) < 1.0 for p in (remaining_cover or [])),
        L_remain=float(np.linalg.norm(q - x)) + shortest_path_length(q, rest),
        J=best_j,
    )


def select_robust_point(
    s,
    bearing_deg: float,
    robot_pos=None,
    n_azimuth: int = 8,
    refine: bool = False,
    exclude_positions=None,
    remaining_cover=None,
    **_kw,
) -> ActiveChoice | None:
    res = select_second_point(s, bearing_deg, robot_pos=robot_pos, n_azimuth=n_azimuth, refine=refine)
    cands = [c["q"] for c in res.candidates if np.isfinite(c.get("J", np.nan))]
    if remaining_cover:
        cands = list(cands) + [np.asarray(p, dtype=float) for p in remaining_cover]
    filtered = [q for q in cands if not _excluded(q, exclude_positions)]
    if not filtered:
        return None
    best = None
    best_j = float("inf")
    for q, c in zip([c["q"] for c in res.candidates], res.candidates):
        if _excluded(q, exclude_positions):
            continue
        if c["J"] < best_j:
            best_j = c["J"]
            best = q
    if best is None:
        best = filtered[0]
        best_j = None
    q = np.asarray(best, dtype=float)
    x = s if robot_pos is None else np.asarray(robot_pos, dtype=float).reshape(2)
    reuse = False
    if remaining_cover:
        reuse = any(np.linalg.norm(q - np.asarray(p, dtype=float)) < 1.0 for p in remaining_cover)
    return ActiveChoice(
        q=q,
        method="ROBUST",
        in_C=True,
        d_perp=d_perp(q, s, bearing_deg),
        phi_min=0.0,
        travel_s=float(np.linalg.norm(q - x) / SPEED),
        reuse_global=reuse,
        L_remain=float(np.linalg.norm(q - x)),
        J=best_j,
    )


def select_active(strategy: str, s, bearing_deg: float, **kwargs) -> ActiveChoice | None:
    name = str(strategy).upper()
    keys_fast = ("robot_pos", "remaining_cover", "receptions", "n_azimuth", "exclude_positions", "f_verts")
    if name == "FAST":
        return select_fast_point(s, bearing_deg, **{k: kwargs[k] for k in keys_fast if k in kwargs})
    if name == "HYBRID":
        keys = keys_fast + ("top_k",)
        return select_hybrid_point(s, bearing_deg, **{k: kwargs[k] for k in keys if k in kwargs})
    if name in ("ROBUST", "ROBUST_ACTIVE"):
        return select_robust_point(
            s,
            bearing_deg,
            robot_pos=kwargs.get("robot_pos"),
            n_azimuth=kwargs.get("n_azimuth", 8),
            refine=kwargs.get("refine", False),
            exclude_positions=kwargs.get("exclude_positions"),
            remaining_cover=kwargs.get("remaining_cover"),
        )
    raise ValueError(f"unknown strategy {strategy}; SAFE has no second-point selector")

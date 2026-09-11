"""Truth-level oracle and membership checks for Q2. Does not change the selector."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geometry import min_enclosing_circle, unit, wedge_halfplanes
from localization import (
    evaluate_J,
    f1_outer_vertices,
    in_c_guaranteed,
    select_second_point,
    theoretical_sector_rho,
)
from params import CLEAR_RADIUS, EPS_DEG, NEAR_RADIUS, OMEGA_RADIUS, R_MAX, R_MIN, SPEED

MODEL_OR_IMPLEMENTATION_ERROR = "MODEL_OR_IMPLEMENTATION_ERROR"

# Closed-set numerical tolerances. Not contest parameters.
ATOL_M = 1e-8
ATOL_DEG = 1e-10
CORE_ATOL_M = 1e-6
RHO0_NUM_ATOL = 8.0  # outer-tangent slack on 750.114 m bound

ANGLE_DELTAS_DEG = (1e-6, 1e-3, 1e-2)
DIST_DELTAS_M = (1e-6, 1e-3, 1e-2)
CORE_DELTAS_M = (1e-6, 1e-3, 1e-2, 1.0, 10.0)


class ModelOrImplementationError(AssertionError):
    def __init__(self, message: str):
        super().__init__(f"{MODEL_OR_IMPLEMENTATION_ERROR}: {message}")


@dataclass
class TrueState:
    g: np.ndarray
    r: float
    eps1_deg: float = 0.0
    eps2_deg: float = 0.0


def in_omega(g: np.ndarray, atol: float = ATOL_M) -> bool:
    return float(np.linalg.norm(g)) <= OMEGA_RADIUS + atol


def in_wedge(g: np.ndarray, site: np.ndarray, bearing_deg: float, atol: float = ATOL_M) -> bool:
    A, b = wedge_halfplanes(site, bearing_deg)
    return bool(np.all(A @ np.asarray(g, dtype=float) <= b + atol))


def simulate_measure(p, g, r, eps_deg: float) -> tuple[str, float | None]:
    """Exact contest predicates. Reception is closed; near is closed; no_signal is d > r."""
    p = np.asarray(p, dtype=float).reshape(2)
    g = np.asarray(g, dtype=float).reshape(2)
    d = float(np.linalg.norm(g - p))
    if d > float(r) + ATOL_M:
        return "no_signal", None
    if d <= NEAR_RADIUS + ATOL_M:
        return "near", None
    true = np.degrees(np.arctan2(g[1] - p[1], g[0] - p[0]))
    return "direction", float((true + eps_deg) % 360.0)


def in_Z1(g, r, s, bearing_deg: float, atol: float = ATOL_M) -> bool:
    g = np.asarray(g, dtype=float).reshape(2)
    s = np.asarray(s, dtype=float).reshape(2)
    d = float(np.linalg.norm(g - s))
    if not in_omega(g, atol):
        return False
    if not (R_MIN - atol <= float(r) <= R_MAX + atol):
        return False
    if d <= NEAR_RADIUS - atol:
        return False
    if d > float(r) + atol:
        return False
    return in_wedge(g, s, bearing_deg, atol)


def in_Z_near(g, r, s, bearing_deg: float, q, atol: float = ATOL_M) -> bool:
    if not in_Z1(g, r, s, bearing_deg, atol):
        return False
    return float(np.linalg.norm(np.asarray(g) - np.asarray(q))) <= NEAR_RADIUS + atol


def in_Z_dir(g, r, s, bearing_deg: float, q, b: float, atol: float = ATOL_M) -> bool:
    if not in_Z1(g, r, s, bearing_deg, atol):
        return False
    d = float(np.linalg.norm(np.asarray(g) - np.asarray(q)))
    if d <= NEAR_RADIUS - atol:
        return False
    if d > float(r) + atol:
        return False
    return in_wedge(g, q, b, atol)


def in_Z_no(g, r, s, bearing_deg: float, q, atol: float = ATOL_M) -> bool:
    if not in_Z1(g, r, s, bearing_deg, atol):
        return False
    return float(np.linalg.norm(np.asarray(g) - np.asarray(q))) > float(r) + atol


def naive_no_signal_position(g, q) -> bool:
    """Incorrect rule ||g-q|| > 1000. Used only to prove the implementation must differ."""
    return float(np.linalg.norm(np.asarray(g) - np.asarray(q))) > R_MIN


def assert_truth_retained(kind: str, ok: bool, detail: str = "") -> None:
    if not ok:
        raise ModelOrImplementationError(f"z_true excluded from {kind} {detail}".strip())


def certified_clear(rho: float | None, atol: float = ATOL_M) -> bool:
    if rho is None or not np.isfinite(rho):
        return False
    return float(rho) <= CLEAR_RADIUS + atol


def in_c_core(q, c1, R_core, atol: float = CORE_ATOL_M) -> bool:
    return float(np.linalg.norm(np.asarray(q) - np.asarray(c1))) <= float(R_core) + atol


def max_distance_to_set(q, points: np.ndarray) -> float:
    if len(points) == 0:
        return float("nan")
    return float(np.max(np.linalg.norm(points - np.asarray(q, dtype=float), axis=1)))


def f_no_points(f1_points: np.ndarray, s, q) -> np.ndarray:
    s = np.asarray(s, dtype=float)
    q = np.asarray(q, dtype=float)
    d_q = np.linalg.norm(f1_points - q, axis=1)
    d_s = np.linalg.norm(f1_points - s, axis=1)
    return f1_points[d_q > np.maximum(R_MIN, d_s) + ATOL_M]


def naive_f_no_points(f1_points: np.ndarray, q) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    return f1_points[np.linalg.norm(f1_points - q, axis=1) > R_MIN + ATOL_M]


def first_observation(state: TrueState, s) -> tuple[str, float | None]:
    return simulate_measure(s, state.g, state.r, state.eps1_deg)


def make_direction_state(s, range_m: float, true_bearing_deg: float, r: float, eps1_deg: float) -> TrueState:
    s = np.asarray(s, dtype=float).reshape(2)
    g = s + float(range_m) * unit(np.deg2rad(true_bearing_deg))
    return TrueState(g=g, r=float(r), eps1_deg=float(eps1_deg))


def observed_bearing(s, state: TrueState) -> float:
    y, b = first_observation(state, s)
    if y != "direction" or b is None:
        raise ValueError(f"expected direction, got {y}")
    return b


def polar_grid(center, radii, n_azimuth: int) -> list[np.ndarray]:
    center = np.asarray(center, dtype=float).reshape(2)
    pts = []
    for rad in radii:
        if rad <= 1e-12:
            pts.append(center.copy())
            continue
        ang = np.linspace(0.0, 2.0 * np.pi, n_azimuth, endpoint=False)
        for a in ang:
            pts.append(center + rad * np.array([np.cos(a), np.sin(a)]))
    return pts


def legacy_radii_m() -> tuple[float, ...]:
    return (20.0, 50.0, 100.0, 200.0, 400.0, 800.0, 1200.0, 1800.0, 2400.0, 3000.0)


def baseline_c1(result) -> np.ndarray:
    return np.asarray(result.c1, dtype=float)


def baseline_90deg(s, bearing_deg: float, result) -> np.ndarray:
    u_a = unit(np.deg2rad(bearing_deg))
    lat = np.array([-u_a[1], u_a[0]])
    scale = max(result.R_core, 1.0)
    return np.asarray(result.c1, dtype=float) + scale * lat


def j_of_points(points, s, f1_verts) -> list[dict]:
    out = []
    for q in points:
        ev = evaluate_J(q, s, f1_verts)
        out.append({"q": np.asarray(q, dtype=float), "J": ev["J"], "travel_s": float(np.linalg.norm(q - s) / SPEED)})
    return out


def min_j(cands: list[dict]) -> dict:
    finite = [c for c in cands if np.isfinite(c["J"])]
    if not finite:
        return {"J": float("inf"), "q": None, "travel_s": float("inf")}
    finite.sort(key=lambda c: (c["J"], c["travel_s"]))
    return finite[0]


def random_feasible_direction_states(n: int, seed: int = 11000) -> list[tuple[np.ndarray, TrueState]]:
    rng = np.random.default_rng(seed)
    cases = []
    tries = 0
    while len(cases) < n and tries < n * 40:
        tries += 1
        s = rng.uniform(-400.0, 400.0, size=2)
        r = float(rng.uniform(R_MIN, R_MAX))
        dist = float(rng.uniform(NEAR_RADIUS + 1.0, r))
        ang = float(rng.uniform(0.0, 360.0))
        g = s + dist * unit(np.deg2rad(ang))
        if not in_omega(g):
            continue
        eps = float(rng.choice([-1.0, -0.5, 0.0, 0.5, 1.0]))
        state = TrueState(g=g, r=r, eps1_deg=eps)
        y, b = first_observation(state, s)
        if y != "direction":
            continue
        if not in_Z1(g, r, s, b):
            continue
        cases.append((s, state))
    return cases

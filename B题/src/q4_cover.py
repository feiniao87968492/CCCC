"""Q4 discovery certificate covers: SQUARE81 baseline and HEX37 challenger.

SQUARE81 is the 600 m square grid (81 points). HEX37 is the triangular lattice
with spacing 800 m, hex radius 3 (37 points). Voronoi cells of HEX37 are regular
hexagons; sampling points themselves form a triangular lattice.

Localization is not defined here. Existence only: for every source in Omega and
every heading, some cover point lies strictly inside the 180° RF half-plane and
inside the 1000 m minimum receive radius.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from params import COORD_ABS_LIMIT, OMEGA_RADIUS, R_MIN

COVER_SQUARE81 = "SQUARE81"
COVER_HEX37 = "HEX37"
_VALID_MODES = (COVER_SQUARE81, COVER_HEX37)

P4_STEP = 600.0
P4_INDEX = range(-4, 5)
APPROACH = 500.0
GRID_HALF = P4_STEP / 2.0  # 300
P4_N = 81

HEX_STEP = 800.0
HEX_RING = 3
HEX_DELTA = HEX_STEP / np.sqrt(3.0)
HEX_E1 = np.array([HEX_STEP, 0.0], dtype=float)
HEX_E2 = np.array([HEX_STEP / 2.0, HEX_STEP * np.sqrt(3.0) / 2.0], dtype=float)
HEX_DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
# Offline Hamilton path on the 800 m grid graph, starting at the origin.
# 36 edges × 800 m = 28800 m. Do not recompute online.
HEX37_ROUTE_QR = (
    (0, 0), (-1, 0), (-1, 1), (-2, 1), (-3, 1), (-3, 0), (-2, 0),
    (-2, -1), (-1, -2), (-1, -1), (0, -1), (0, -2), (0, -3), (1, -3),
    (1, -2), (2, -3), (3, -3), (2, -2), (1, -1), (1, 0), (0, 1),
    (-1, 2), (-2, 2), (-3, 2), (-3, 3), (-2, 3), (-1, 3), (0, 3),
    (0, 2), (1, 2), (1, 1), (2, 1), (3, 0), (2, 0), (2, -1), (3, -2),
    (3, -1),
)


def _key(p) -> tuple[float, float]:
    return (round(float(p[0]), 6), round(float(p[1]), 6))


@dataclass(frozen=True)
class CoverModel:
    name: str
    points: np.ndarray
    key_to_idx: dict
    route: list
    dist: np.ndarray
    step: float
    n: int


def _index_map(pts: np.ndarray) -> dict:
    return {_key(p): i for i, p in enumerate(pts)}


def _build_square81() -> CoverModel:
    pts = np.array([(P4_STEP * i, P4_STEP * j) for j in P4_INDEX for i in P4_INDEX], dtype=float)
    key_to_idx = _index_map(pts)
    snake: list[int] = []
    for row, j in enumerate(P4_INDEX):
        xs = list(P4_INDEX) if row % 2 == 0 else list(reversed(list(P4_INDEX)))
        for i in xs:
            snake.append(key_to_idx[_key((P4_STEP * i, P4_STEP * j))])
    dist = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    return CoverModel(COVER_SQUARE81, pts, key_to_idx, snake, dist, P4_STEP, len(pts))


def _axial_to_xy(q: int, r: int) -> np.ndarray:
    return q * HEX_E1 + r * HEX_E2


def _hex_round(qf: float, rf: float) -> tuple[int, int]:
    sf = -qf - rf
    q = int(round(qf))
    r = int(round(rf))
    s = int(round(sf))
    dq, dr, ds = abs(q - qf), abs(r - rf), abs(s - sf)
    if dq > dr and dq > ds:
        q = -r - s
    elif dr > ds:
        r = -q - s
    return q, r


def _xy_to_axial_frac(y) -> tuple[float, float]:
    y = np.asarray(y, dtype=float).reshape(2)
    r = float(y[1] / (HEX_STEP * np.sqrt(3.0) / 2.0))
    q = float(y[0] / HEX_STEP - r / 2.0)
    return q, r


def _build_hex37() -> CoverModel:
    if len(HEX37_ROUTE_QR) != 37:
        raise RuntimeError("HEX37 route must contain 37 axial cells")
    if HEX37_ROUTE_QR[0] != (0, 0):
        raise RuntimeError("HEX37 route must start at the origin")
    if len(set(HEX37_ROUTE_QR)) != 37:
        raise RuntimeError("HEX37 route repeats a lattice cell")
    for q, r in HEX37_ROUTE_QR:
        if max(abs(q), abs(r), abs(q + r)) > HEX_RING:
            raise RuntimeError(f"HEX37 route cell ({q},{r}) is outside hex radius {HEX_RING}")
    pts = np.array([_axial_to_xy(q, r) for q, r in HEX37_ROUTE_QR], dtype=float)
    for a, b in zip(pts, pts[1:]):
        step = float(np.linalg.norm(a - b))
        if abs(step - HEX_STEP) > 1e-8:
            raise RuntimeError(f"HEX37 route has a non-800 m step: {step}")
    key_to_idx = _index_map(pts)
    route = list(range(len(pts)))
    dist = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    return CoverModel(COVER_HEX37, pts, key_to_idx, route, dist, HEX_STEP, len(pts))


_SQUARE81 = _build_square81()
_HEX37 = _build_hex37()
_MODELS = {COVER_SQUARE81: _SQUARE81, COVER_HEX37: _HEX37}

_P4_POINTS = _SQUARE81.points
_P4_KEY_TO_IDX = _SQUARE81.key_to_idx
_P4_SNAKE = _SQUARE81.route
_P4_DIST = _SQUARE81.dist


def _initial_mode() -> str:
    raw = os.environ.get("Q4_COVER_MODE", COVER_SQUARE81).strip().upper()
    return raw if raw in _VALID_MODES else COVER_SQUARE81


_COVER_MODE = _initial_mode()


def current_cover_mode() -> str:
    return _COVER_MODE


def set_cover_mode(mode: str) -> None:
    global _COVER_MODE
    name = str(mode).strip().upper()
    if name not in _VALID_MODES:
        raise ValueError(f"unknown cover mode {mode!r}")
    _COVER_MODE = name


def _model(mode: str | None = None) -> CoverModel:
    name = current_cover_mode() if mode is None else str(mode).strip().upper()
    if name not in _MODELS:
        raise ValueError(f"unknown cover mode {mode!r}")
    return _MODELS[name]


def cover_n(mode: str | None = None) -> int:
    return _model(mode).n


def cover_points(mode: str | None = None) -> np.ndarray:
    return _model(mode).points


def cover_route(mode: str | None = None) -> list[int]:
    return list(_model(mode).route)


def cover_distance_matrix(mode: str | None = None) -> np.ndarray:
    return _model(mode).dist


def cover_index(p, mode: str | None = None) -> int | None:
    """Map a coordinate to the active cover index; None if off the cover (tol 1e-6 m)."""
    model = _model(mode)
    q = np.asarray(p, dtype=float).reshape(2)
    if not np.all(np.isfinite(q)):
        return None
    if np.any(np.abs(q) > COORD_ABS_LIMIT):
        return None
    idx = model.key_to_idx.get(_key(q))
    if idx is not None:
        return idx
    snapped = nearest_cover(q, mode=model.name)
    if float(np.linalg.norm(q - snapped)) <= 1e-6:
        return model.key_to_idx.get(_key(snapped))
    return None


def cover_route_stats(mode: str | None = None) -> dict:
    model = _model(mode)
    pts = model.points
    route = model.route
    steps = [float(np.linalg.norm(pts[a] - pts[b])) for a, b in zip(route, route[1:])]
    n_adj = sum(abs(step - model.step) <= 1e-6 for step in steps)
    return {
        "mode": model.name,
        "n_points": model.n,
        "total_length": float(sum(steps)),
        "max_step": float(max(steps) if steps else 0.0),
        "n_adj_step": int(n_adj),
        "step": float(model.step),
    }


def p4_points() -> np.ndarray:
    return _SQUARE81.points


def p4_index(p) -> int | None:
    """Map a coordinate to a SQUARE81 index; None if not on that grid (tol 1e-6 m)."""
    return cover_index(p, mode=COVER_SQUARE81)


def p4_snake_indices() -> list[int]:
    return list(_SQUARE81.route)


def p4_distance_matrix() -> np.ndarray:
    return _SQUARE81.dist


def nearest_p4(y) -> np.ndarray:
    y = np.asarray(y, dtype=float).reshape(2)
    q = np.round(y / P4_STEP)
    q = np.clip(q, -4.0, 4.0)
    return q * P4_STEP


def nearest_hex(y) -> np.ndarray:
    q, r = _hex_round(*_xy_to_axial_frac(y))
    return _axial_to_xy(q, r)


def nearest_cover(y, mode: str | None = None) -> np.ndarray:
    name = current_cover_mode() if mode is None else str(mode).strip().upper()
    if name == COVER_HEX37:
        return nearest_hex(y)
    if name == COVER_SQUARE81:
        return nearest_p4(y)
    raise ValueError(f"unknown cover mode {mode!r}")


def covering_point(g, heading_rad: float, mode: str | None = None) -> np.ndarray:
    """Constructive witness used in the proof (depends on unknown heading)."""
    g = np.asarray(g, dtype=float).reshape(2)
    d = np.array([np.cos(heading_rad), np.sin(heading_rad)], dtype=float)
    return nearest_cover(g + APPROACH * d, mode=mode)


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


def p4_covers(g, heading_rad: float, *, directional: bool, mode: str | None = None) -> bool:
    pts = cover_points(mode)
    return any(rf_covered(g, heading_rad, p, directional=directional) for p in pts)


def in_bearing_halfplane(p, site, bearing_deg: float) -> bool:
    """Forward open half-plane along a measured bearing (site → source)."""
    p = np.asarray(p, dtype=float).reshape(2)
    s = np.asarray(site, dtype=float).reshape(2)
    rad = np.deg2rad(float(bearing_deg))
    u = np.array([np.cos(rad), np.sin(rad)], dtype=float)
    return float(np.dot(p - s, u)) > 0.0


def hex37_ring4_min_radius() -> float:
    return float(HEX_STEP * np.sqrt(12.0))


def hex37_y_max() -> float:
    return float(OMEGA_RADIUS + APPROACH)

"""Q4 online cover routing. Uses P4 certificate + incremental snake cost, not k! TSP."""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from active import route_length_estimate
from params import SPEED
from q4_cover import cover_index, cover_points, cover_route, in_bearing_halfplane
from q4_state import Q4State

ROUTE_OLD = "OLD_HEX37"
ROUTE_INSERT_V1 = "ROUTE_INSERT_V1"
_VALID_ROUTE_MODES = (ROUTE_OLD, ROUTE_INSERT_V1)
# Extra length allowed when inserting a pending site between x and the next HEX.
# Keep this below one HEX step so inserts stay on-path; larger values bounce
# off the skeleton too often.
INSERT_MAX_M = 400.0


def _initial_route_mode() -> str:
    raw = os.environ.get("Q4_ROUTE_MODE", ROUTE_OLD).strip().upper()
    if raw in _VALID_ROUTE_MODES:
        return raw
    return ROUTE_OLD


_ROUTE_MODE = _initial_route_mode()


def current_route_mode() -> str:
    return _ROUTE_MODE


def set_route_mode(mode: str) -> None:
    global _ROUTE_MODE
    name = str(mode).strip().upper()
    if name not in _VALID_ROUTE_MODES:
        raise ValueError(f"unknown route mode {mode!r}")
    _ROUTE_MODE = name


def insertion_extra(x, q, u) -> float:
    """Detour length for visiting q between x and next cover u. If u is None, d(x,q)."""
    x = np.asarray(x, dtype=float).reshape(2)
    q = np.asarray(q, dtype=float).reshape(2)
    if u is None:
        return float(np.linalg.norm(q - x))
    u = np.asarray(u, dtype=float).reshape(2)
    return float(np.linalg.norm(q - x) + np.linalg.norm(u - q) - np.linalg.norm(u - x))


def choose_insert_or_cover(x, u, candidates, max_extra: float = INSERT_MAX_M):
    """Pick pending insert vs next cover. candidates are (id, q) pairs."""
    if not candidates:
        return "cover", None
    if u is None:
        ident, _q = min(candidates, key=lambda item: float(np.linalg.norm(
            np.asarray(item[1], dtype=float).reshape(2) - np.asarray(x, dtype=float).reshape(2)
        )))
        return "insert", ident
    best_id = None
    best_extra = None
    for ident, q in candidates:
        extra = insertion_extra(x, q, u)
        if best_extra is None or extra < best_extra:
            best_extra = extra
            best_id = ident
    if best_extra is not None and best_extra <= max_extra:
        return "insert", best_id
    return "cover", None


def next_route_cover(visited, need):
    """Next Hamilton/snake cover index that is still needed and not visited."""
    pts = cover_points()
    visited = set(visited)
    need = set(need)
    for i in cover_route():
        if i in need and i not in visited:
            return pts[i].copy()
    return None

# Implementation weights, not contest constants.
# travel_time: seconds to the candidate at 5 m/s.
# newly_certified_points: unseen channels that still need this P4 index.
# channel_progress: fraction of remaining P4 closed if we visit q (max over unseen).
# source_clear_priority: 1 if a detected source wants this point (half-plane / first site).
ALPHA = 1.0
BETA = 50.0
GAMMA = 20.0
ETA = 200.0


@dataclass
class Q4Choice:
    q: np.ndarray
    score: float
    travel_s: float
    newly_certified_points: float
    channel_progress: float
    source_clear_priority: float
    remain_len: float
    reason: str


def _unseen_need_index(state: Q4State, idx: int) -> int:
    n = 0
    for ch in state.channels.values():
        if ch.status == "unseen" and idx not in ch.visited_p4:
            n += 1
    return n


def _channel_progress(state: Q4State, idx: int) -> float:
    best = 0.0
    for ch in state.channels.values():
        if ch.status not in ("unseen", "detected"):
            continue
        rem = ch.remaining_cover()
        if idx not in rem:
            continue
        best = max(best, 1.0 / max(len(rem), 1))
    return best


def _clear_priority(state: Q4State, q: np.ndarray) -> float:
    pri = 0.0
    for k in state.pending_detected():
        ch = state.channels[k]
        if ch.first_site is None:
            pri = max(pri, 0.5)
            continue
        if ch.first_bearing is None:
            if float(np.linalg.norm(q - ch.first_site)) < 1.0:
                pri = max(pri, 1.0)
            continue
        if in_bearing_halfplane(q, ch.first_site, ch.first_bearing):
            pri = max(pri, 1.0)
    return pri


def _candidate_points(state: Q4State, *, certificate_mode: bool = False) -> list[np.ndarray]:
    pts = cover_points()
    need: set[int] = set()
    for ch in state.channels.values():
        if ch.status == "unseen":
            need.update(ch.remaining_cover())
        elif ch.status == "detected" and (certificate_mode or ch.halfplane_failed):
            need.update(ch.remaining_cover())
    if not need:
        return []
    route = [i for i in cover_route() if i in need]
    return [pts[i].copy() for i in route]


def score_point(state: Q4State, q, remain: list[np.ndarray]) -> Q4Choice:
    q = np.asarray(q, dtype=float).reshape(2)
    travel = float(np.linalg.norm(q - state.pos) / SPEED)
    idx = cover_index(q)
    newly = float(_unseen_need_index(state, idx) if idx is not None else 0)
    progress = float(_channel_progress(state, idx) if idx is not None else 0.0)
    pri = float(_clear_priority(state, q))
    rest = [p for p in remain if float(np.linalg.norm(p - q)) >= 1.0]
    remain_len = float(np.linalg.norm(q - state.pos)) + route_length_estimate(q, rest)
    sc = -ALPHA * travel + BETA * newly + GAMMA * progress + ETA * pri
    return Q4Choice(
        q=q,
        score=sc,
        travel_s=travel,
        newly_certified_points=newly,
        channel_progress=progress,
        source_clear_priority=pri,
        remain_len=remain_len,
        reason="score",
    )


def next_snake_point(state: Q4State, *, certificate_mode: bool = False) -> np.ndarray | None:
    """Next remaining cover site in snake order from the nearest entry. Visits every leftover P4."""
    cands = _candidate_points(state, certificate_mode=certificate_mode)
    if not cands:
        pts = cover_points()
        for ch in state.channels.values():
            if ch.status not in ("unseen", "detected"):
                continue
            rem = ch.remaining_cover()
            if rem:
                return pts[rem[0]].copy()
        return None
    pos = np.asarray(state.pos, dtype=float).reshape(2)
    i0 = min(range(len(cands)), key=lambda i: float(np.linalg.norm(cands[i] - pos)))
    return cands[i0]


def select_next_p4(state: Q4State, *, certificate_mode: bool = False) -> Q4Choice | None:
    """Pick the next P4 site. Ranking uses incremental snake cost, not global TSP.

    Half-plane pruning is only a priority for detected channels. Unseen channels
    always keep the full remaining P4 certificate. certificate_mode disables prune.
    """
    cands = _candidate_points(state, certificate_mode=certificate_mode)
    if not cands:
        pts = cover_points()
        for ch in state.channels.values():
            if ch.status not in ("unseen", "detected"):
                continue
            rem = ch.remaining_cover()
            if rem:
                q = pts[rem[0]].copy()
                return score_point(state, q, [q])
        return None
    best = None
    for q in cands:
        choice = score_point(state, q, cands)
        if best is None or (choice.score, -choice.travel_s) > (best.score, -best.travel_s):
            best = choice
    if best is not None:
        if any(ch.status == "detected" for ch in state.channels.values()) and best.source_clear_priority > 0:
            best.reason = "detected_halfplane"
        elif state.unseen_channels():
            best.reason = "unseen_p4"
        else:
            best.reason = "certificate_progress"
    return best

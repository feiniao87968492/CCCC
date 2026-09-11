"""Q4 online cover routing. Uses P4 certificate + incremental snake cost, not k! TSP."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from active import route_length_estimate
from params import SPEED
from q4_cover import in_bearing_halfplane, p4_index, p4_points, p4_snake_indices
from q4_state import Q4State

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
        rem = ch.remaining_p4()
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
    pts = p4_points()
    need: set[int] = set()
    for ch in state.channels.values():
        if ch.status == "unseen":
            need.update(ch.remaining_p4())
        elif ch.status == "detected" and (certificate_mode or ch.halfplane_failed):
            need.update(ch.remaining_p4())
    if not need:
        return []
    snake = [i for i in p4_snake_indices() if i in need]
    return [pts[i].copy() for i in snake]


def score_point(state: Q4State, q, remain: list[np.ndarray]) -> Q4Choice:
    q = np.asarray(q, dtype=float).reshape(2)
    travel = float(np.linalg.norm(q - state.pos) / SPEED)
    idx = p4_index(q)
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
        pts = p4_points()
        for ch in state.channels.values():
            if ch.status not in ("unseen", "detected"):
                continue
            rem = ch.remaining_p4()
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
        pts = p4_points()
        for ch in state.channels.values():
            if ch.status not in ("unseen", "detected"):
                continue
            rem = ch.remaining_p4()
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

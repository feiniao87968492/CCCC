"""Q3 online state. Observable API history only; no source truth, no q2_validation."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

P3 = [np.array([0.0, 0.0])] + [
    1200.0 * np.array([np.cos(j * np.pi / 3.0), np.sin(j * np.pi / 3.0)]) for j in range(6)
]
P3_INDEX = {tuple(np.round(p, 6)): i for i, p in enumerate(P3)}
CHANNELS = list(range(1, 21))


def cover_index(p) -> int | None:
    q = np.round(np.asarray(p, dtype=float).reshape(2), 6)
    return P3_INDEX.get((float(q[0]), float(q[1])))


def dist(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


def pos_key(p, ndigits: int = 0) -> tuple[float, float]:
    q = np.asarray(p, dtype=float).reshape(2)
    return (round(float(q[0]), ndigits), round(float(q[1]), ndigits))


@dataclass
class Channel:
    status: str = "unseen"
    ever_detected: bool = False
    V: set = field(default_factory=set)
    history: list = field(default_factory=list)
    first_site: np.ndarray | None = None
    first_bearing: float | None = None
    extra_measures: int = 0
    local_virtual0: float | None = None
    safe_attempted: bool = False
    measured_positions: list = field(default_factory=list)
    active_positions: list = field(default_factory=list)
    f_verts: np.ndarray | None = None
    receptions: list = field(default_factory=list)
    t_first_detect: float | None = None
    t_clear: float | None = None
    safe_move: float = 0.0
    loc_move: float = 0.0
    tour_skip_pos: set = field(default_factory=set)
    greedy_attempted: bool = False


@dataclass
class Q3State:
    pos: np.ndarray = field(default_factory=lambda: np.zeros(2))
    measure_channel: int = 1
    R: list = field(default_factory=lambda: [p.copy() for p in P3])
    P: list = field(default_factory=list)
    channels: dict = field(default_factory=lambda: {k: Channel() for k in CHANNELS})
    virtual_time: float = 0.0
    move_distance: float = 0.0
    n_measure: int = 0
    n_clear: int = 0
    n_clear_ok: int = 0
    n_safe: int = 0
    n_full_225: int = 0
    n_reuse: int = 0
    n_active_measure: int = 0
    n_same_pos_repeat: int = 0
    global_move: float = 0.0
    loc_move: float = 0.0
    safe_move: float = 0.0
    measure_time: float = 0.0
    clear_time: float = 0.0
    phase: str = "global"
    failure: str | None = None

    def detected_count(self) -> int:
        return sum(1 for ch in self.channels.values() if ch.ever_detected)

    def cleared_count(self) -> int:
        return sum(1 for ch in self.channels.values() if ch.status == "cleared")

    def done_all_channels(self) -> bool:
        return all(ch.status in ("cleared", "certified_absent") for ch in self.channels.values())

    def discovery_cancelled(self) -> bool:
        return self.detected_count() >= 16

    def unseen_to_scan(self) -> list[int]:
        if self.discovery_cancelled():
            return []
        return [k for k in CHANNELS if self.channels[k].status == "unseen"]

    def mark_cover_done(self, p) -> None:
        idx = cover_index(p)
        if idx is None:
            return
        self.R = [q for q in self.R if cover_index(q) != idx]


def shortest_next(x, remaining: list[np.ndarray]) -> np.ndarray:
    from itertools import permutations

    if not remaining:
        raise ValueError("no remaining cover points")
    if len(remaining) == 1:
        return remaining[0]
    best_l = float("inf")
    best_first = remaining[0]
    for perm in permutations(range(len(remaining))):
        pts = [remaining[i] for i in perm]
        L = dist(x, pts[0])
        for i in range(len(pts) - 1):
            L += dist(pts[i], pts[i + 1])
        if L < best_l:
            best_l = L
            best_first = pts[0]
    return best_first

"""Q4 online belief. Observable measure/clear history only; no source type/heading truth."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from params import CLEAR_RADIUS, COORD_ABS_LIMIT, NEAR_RADIUS
from q4_cover import P4_N, p4_index, p4_points

CHANNELS = list(range(1, 21))
Q4_STATUSES = ("unseen", "detected", "cleared", "certified_absent")
P4_INDEX_SET = frozenset(range(P4_N))


def _legal_pos(p) -> bool:
    q = np.asarray(p, dtype=float).reshape(2)
    return bool(np.all(np.isfinite(q)) and np.all(np.abs(q) <= COORD_ABS_LIMIT))


def near_physically_valid(distance_m: float, in_rf_coverage: bool) -> bool:
    """near iff d<=5 m AND the site is inside RF coverage. Does not infer heading."""
    return bool(in_rf_coverage and distance_m <= NEAR_RADIUS + 1e-12)


def optical_clear_ok(distance_m: float) -> bool:
    """Clear success depends only on Euclidean distance, not RF heading."""
    return bool(distance_m <= CLEAR_RADIUS + 1e-12)


def q4_no_signal_implies_beyond_r_min() -> bool:
    """Q4: no_signal is a 3-way union; never treat it as d>1000 m."""
    return False


@dataclass
class Q4Channel:
    status: str = "unseen"
    ever_detected: bool = False
    visited_p4: set = field(default_factory=set)
    no_signal_p4: set = field(default_factory=set)
    history: list = field(default_factory=list)
    first_site: np.ndarray | None = None
    first_bearing: float | None = None
    second_site: np.ndarray | None = None
    second_bearing: float | None = None
    cleared: bool = False
    extra_measures: int = 0
    n_clear_try: int = 0
    halfplane_failed: bool = False

    def remaining_p4(self) -> list[int]:
        return [i for i in range(P4_N) if i not in self.visited_p4]

    def remaining_p4_points(self) -> np.ndarray:
        pts = p4_points()
        idx = self.remaining_p4()
        if not idx:
            return np.zeros((0, 2))
        return pts[idx]

    def can_certify_absent(self) -> bool:
        if self.ever_detected or self.cleared or self.status == "cleared":
            return False
        return self.no_signal_p4 == P4_INDEX_SET


@dataclass
class Q4State:
    pos: np.ndarray = field(default_factory=lambda: np.zeros(2))
    channels: dict = field(default_factory=lambda: {k: Q4Channel() for k in CHANNELS})

    def pending_detected(self) -> list[int]:
        return [k for k, ch in self.channels.items() if ch.status == "detected"]

    def unseen_channels(self) -> list[int]:
        return [k for k, ch in self.channels.items() if ch.status == "unseen"]

    def apply_measure(self, k: int, pos, result: str, svd_deg: float | None = None) -> None:
        if k not in self.channels:
            raise ValueError(f"channel {k} not in 1..20")
        if not _legal_pos(pos):
            raise ValueError("illegal measure position")
        rec = str(result)
        if rec not in ("no_signal", "near", "direction"):
            raise ValueError(f"unknown measure_result {result}")
        if rec == "direction":
            try:
                ang = float(svd_deg)
            except (TypeError, ValueError):
                raise ValueError("direction requires finite svd_deg") from None
            if not np.isfinite(ang):
                raise ValueError("direction requires finite svd_deg")
        ch = self.channels[k]
        if ch.status == "cleared":
            return
        q = np.asarray(pos, dtype=float).reshape(2)
        self.pos = q.copy()
        idx = p4_index(q)
        if idx is not None:
            ch.visited_p4.add(idx)
        rec_svd = float(svd_deg) if rec == "direction" else svd_deg
        ch.history.append({"pos": q.copy(), "result": rec, "svd": rec_svd, "p4": idx})
        if rec == "no_signal":
            if idx is not None:
                ch.no_signal_p4.add(idx)
            if ch.can_certify_absent():
                ch.status = "certified_absent"
            return
        if rec == "near":
            ch.ever_detected = True
            ch.status = "detected"
            if ch.first_site is None:
                ch.first_site = q.copy()
            return
        ch.ever_detected = True
        ch.status = "detected"
        ang = float(svd_deg)
        if ch.first_site is None:
            ch.first_site = q.copy()
            ch.first_bearing = ang
        elif ch.second_site is None and float(np.linalg.norm(q - ch.first_site)) >= 50.0:
            ch.second_site = q.copy()
            ch.second_bearing = ang

    def apply_clear(self, k: int, pos, success: bool) -> None:
        if k not in self.channels:
            raise ValueError(f"channel {k} not in 1..20")
        if not _legal_pos(pos):
            raise ValueError("illegal clear position")
        ch = self.channels[k]
        self.pos = np.asarray(pos, dtype=float).reshape(2).copy()
        ch.n_clear_try += 1
        if success:
            ch.status = "cleared"
            ch.cleared = True
            ch.ever_detected = True
        else:
            ch.status = "detected"
            ch.cleared = False
            ch.halfplane_failed = True

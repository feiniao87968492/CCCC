"""Q4 PRACTICE closed loop. Independent of Q3 formal flow. No oracle, no heading truth."""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from active import select_fast_point
from q4_cover import p4_index
from q4_policy import select_next_p4
from q4_state import Q4State

_BANNED = ("q2_validation", "q2_scenario")


def _assert_no_oracle() -> None:
    for name in _BANNED:
        if name in sys.modules:
            raise RuntimeError(f"oracle module loaded: {name}")


class Q4Runner:
    def __init__(self, robot):
        _assert_no_oracle()
        self.robot = robot
        self.state = Q4State()
        self.t0 = time.perf_counter()
        self.log = []
        self.n_measure = 0
        self.n_clear = 0
        self.n_clear_ok = 0
        self.move_m = 0.0
        self.virtual_time = 0.0
        self.measure_channel = 1
        self.failure = None
        self.max_extra = 4

    def _note(self, **kw) -> None:
        self.log.append(kw)

    def _move_to(self, pos) -> None:
        q = np.asarray(pos, dtype=float).reshape(2)
        self.move_m += float(np.linalg.norm(q - self.state.pos))
        self.state.pos = q.copy()

    def measure(self, x, y, k: int) -> dict:
        resp = self.robot.measure(float(x), float(y), int(k))
        self.n_measure += 1
        self._move_to([x, y])
        self.measure_channel = int(k)
        self.virtual_time = float(resp.get("virtual_time_s", self.virtual_time))
        result = resp.get("measure_result")
        svd = resp.get("svd_deg")
        self.state.apply_measure(int(k), [x, y], result, svd)
        self._note(op="measure", k=k, x=float(x), y=float(y), result=result, t=self.virtual_time)
        return resp

    def clear(self, x, y, k: int) -> bool:
        resp = self.robot.clear(float(x), float(y), int(k))
        self.n_clear += 1
        self._move_to([x, y])
        self.virtual_time = float(resp.get("virtual_time_s", self.virtual_time))
        ok = resp.get("clear_result") == "success"
        self.state.apply_clear(int(k), [x, y], ok)
        if ok:
            self.n_clear_ok += 1
        self._note(op="clear", k=k, x=float(x), y=float(y), ok=ok, t=self.virtual_time)
        return ok

    def _channels_to_scan(self, p, *, certificate_mode: bool) -> list[int]:
        idx = p4_index(p)
        out = []
        for k, ch in self.state.channels.items():
            if ch.status in ("cleared", "certified_absent"):
                continue
            if idx is not None and idx in ch.visited_p4:
                continue
            if ch.status == "detected" and not certificate_mode:
                continue
            out.append(k)
        return out

    def scan_at(self, p, *, certificate_mode: bool = False) -> None:
        p = np.asarray(p, dtype=float).reshape(2)
        for k in self._channels_to_scan(p, certificate_mode=certificate_mode):
            resp = self.measure(float(p[0]), float(p[1]), k)
            y = resp.get("measure_result")
            if y == "near":
                self.clear(float(p[0]), float(p[1]), k)
            elif y == "direction" and self.state.channels[k].status == "detected":
                self._try_localize(k)

    def _ray_try_clear(self, k: int) -> bool:
        ch = self.state.channels[k]
        if ch.first_site is None or ch.first_bearing is None:
            return False
        s = np.asarray(ch.first_site, dtype=float).reshape(2)
        rad = np.deg2rad(float(ch.first_bearing))
        u = np.array([np.cos(rad), np.sin(rad)], dtype=float)
        step = 40.0
        d = step
        while d <= 1200.0 + 1e-9:
            p = s + d * u
            if self.clear(float(p[0]), float(p[1]), k):
                return True
            d += step
        return False

    def _try_localize(self, k: int) -> None:
        ch = self.state.channels[k]
        if ch.status != "detected" or ch.first_site is None:
            return
        if ch.extra_measures >= self.max_extra:
            ch.halfplane_failed = True
            return
        if ch.first_bearing is not None and ch.extra_measures == 0:
            ch.extra_measures += 1
            if self._ray_try_clear(k):
                return
        rem = list(ch.remaining_p4_points())
        s = ch.first_site
        bearing = float(ch.first_bearing) if ch.first_bearing is not None else 0.0
        choice = select_fast_point(s, bearing, robot_pos=self.state.pos, remaining_cover=rem, n_azimuth=8)
        q = choice.q if choice is not None else np.asarray(s, dtype=float)
        ch.extra_measures += 1
        resp = self.measure(float(q[0]), float(q[1]), k)
        y = resp.get("measure_result")
        if y == "near":
            self.clear(float(q[0]), float(q[1]), k)
            return
        if y == "direction":
            if self.clear(float(q[0]), float(q[1]), k):
                return
            if self._ray_try_clear(k):
                return
        ch.halfplane_failed = True

    def process_pending(self) -> None:
        for k in list(self.state.pending_detected()):
            if self.state.channels[k].status != "detected":
                continue
            self._try_localize(k)

    def done(self) -> bool:
        return all(ch.status in ("cleared", "certified_absent") for ch in self.state.channels.values())

    def run(self) -> dict:
        _assert_no_oracle()
        enter = self.robot.enter()
        self.virtual_time = float(enter.get("virtual_time_s", 0.0))
        try:
            origin = np.zeros(2)
            self.scan_at(origin)
            self.process_pending()
            guard = 0
            while not self.done() and guard < 400:
                guard += 1
                self.process_pending()
                cert = not bool(self.state.unseen_channels())
                choice = select_next_p4(self.state, certificate_mode=cert)
                if choice is None:
                    choice = select_next_p4(self.state, certificate_mode=True)
                if choice is None:
                    break
                self.scan_at(choice.q, certificate_mode=cert)
                self.process_pending()
        except TimeoutError as exc:
            self.failure = "budget_exhausted"
            self._note(op="timeout", err=str(exc))
        except Exception as exc:
            self.failure = f"error:{type(exc).__name__}"
            self._note(op="error", err=str(exc))
        finally:
            if getattr(self.robot, "entered", False):
                try:
                    self.robot.exit()
                except Exception as exc:
                    self._note(op="exit_failed", err=str(exc))
        K = sum(1 for ch in self.state.channels.values() if ch.status == "cleared")
        T = self.virtual_time
        return {
            "strategy": "Q4_P4",
            "failure": self.failure,
            "K": K,
            "T": T,
            "T_over_K": (T / K) if K else None,
            "wall_s": time.perf_counter() - self.t0,
            "move_m": self.move_m,
            "n_measure": self.n_measure,
            "n_clear": self.n_clear,
            "n_clear_ok": self.n_clear_ok,
            "detected": sum(1 for ch in self.state.channels.values() if ch.ever_detected),
            "certified_absent": [k for k, ch in self.state.channels.items() if ch.status == "certified_absent"],
            "cleared_channels": [k for k, ch in self.state.channels.items() if ch.status == "cleared"],
            "pending": self.state.pending_detected(),
            "all_certified": self.done(),
            "channel_status": {str(k): ch.status for k, ch in self.state.channels.items()},
        }

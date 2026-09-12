"""Q4 PRACTICE closed loop. Independent of Q3 formal flow. No oracle, no heading truth."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from q4_cover import p4_index, p4_points
from q4_localize import (
    bearing_intersection,
    clear_poses,
    hop_ok,
    legal_xy,
    second_measure_points,
    third_measure_points,
    wedge_mec,
)
from q4_policy import next_snake_point
from q4_state import Q4State

MAX_MEASURE = 8
MAX_CLEAR = 6

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
        self.max_extra = MAX_MEASURE

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
            if ch.status == "detected" and not certificate_mode and ch.second_site is not None:
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

    def _try_clear_at(self, k: int, p) -> bool:
        ch = self.state.channels[k]
        if ch.n_clear_try >= MAX_CLEAR:
            return False
        p = np.asarray(p, dtype=float).reshape(2)
        if not legal_xy(p) or not hop_ok(self.state.pos, p):
            return False
        ok = self.clear(float(p[0]), float(p[1]), k)
        self._note(
            op="clear_try",
            k=k,
            x=float(p[0]),
            y=float(p[1]),
            ok=ok,
            n_try=ch.n_clear_try,
            t=self.virtual_time,
        )
        return ok

    def _second_measure(self, k: int) -> None:
        ch = self.state.channels[k]
        if ch.first_site is None or ch.first_bearing is None:
            return
        if ch.second_site is not None:
            return
        cands = second_measure_points(ch.first_site, ch.first_bearing, self.state.pos)
        u = np.array(
            [np.cos(np.deg2rad(ch.first_bearing)), np.sin(np.deg2rad(ch.first_bearing))],
            dtype=float,
        )
        n = np.array([-u[1], u[0]], dtype=float)
        s1 = np.asarray(ch.first_site, dtype=float)
        for dist in (300.0, 600.0, 900.0):
            for sign in (1.0, -1.0):
                cands.append(s1 + dist * u + sign * 200.0 * n)
        for cand in cands:
            if ch.extra_measures >= MAX_MEASURE or ch.status != "detected":
                break
            if not legal_xy(cand) or not hop_ok(self.state.pos, cand):
                continue
            ch.extra_measures += 1
            resp = self.measure(float(cand[0]), float(cand[1]), k)
            self._note(
                op="second_measure",
                k=k,
                x=float(cand[0]),
                y=float(cand[1]),
                result=resp.get("measure_result"),
                svd=resp.get("svd_deg"),
                t=self.virtual_time,
            )
            y = resp.get("measure_result")
            if y == "near":
                self._try_clear_at(k, cand)
                return
            if y == "direction":
                return

    def _clear_from_two_bearings(self, k: int) -> None:
        ch = self.state.channels[k]
        if ch.first_site is None or ch.second_site is None:
            return
        if ch.first_bearing is None or ch.second_bearing is None:
            return
        mec = wedge_mec(ch.first_site, ch.first_bearing, ch.second_site, ch.second_bearing)
        behind = False
        verts = None
        if mec is not None:
            cand = mec["center"]
            rho = mec["rho"]
            verts = mec["verts"]
        else:
            loc = bearing_intersection(
                ch.first_site, ch.first_bearing, ch.second_site, ch.second_bearing
            )
            if loc is None:
                self._note(op="intersect_fail", k=k, reason="parallel_or_short_baseline")
                ch.halfplane_failed = True
                return
            cand = loc["point"]
            rho = float("nan")
            behind = loc["behind"]
        self._note(
            op="intersect",
            k=k,
            candidate=np.asarray(cand).tolist(),
            rho=None if rho != rho else float(rho),
            behind=behind,
            t=self.virtual_time,
        )
        last = ch.second_site
        for p in clear_poses(cand, last, verts):
            if ch.status != "detected":
                return
            if self._try_clear_at(k, p):
                return
        if ch.status != "detected" or ch.extra_measures >= MAX_MEASURE:
            ch.halfplane_failed = True
            return
        for s3 in third_measure_points(cand, ch.second_bearing):
            if ch.extra_measures >= MAX_MEASURE or ch.status != "detected":
                break
            if not legal_xy(s3) or not hop_ok(self.state.pos, s3):
                continue
            ch.extra_measures += 1
            resp = self.measure(float(s3[0]), float(s3[1]), k)
            self._note(
                op="third_measure",
                k=k,
                x=float(s3[0]),
                y=float(s3[1]),
                result=resp.get("measure_result"),
                svd=resp.get("svd_deg"),
                t=self.virtual_time,
            )
            y = resp.get("measure_result")
            if y == "near":
                self._try_clear_at(k, s3)
                return
            if y != "direction" or resp.get("svd_deg") is None:
                continue
            th3 = float(resp["svd_deg"])
            mec3 = wedge_mec(ch.first_site, ch.first_bearing, s3, th3)
            if mec3 is None:
                loc3 = bearing_intersection(ch.first_site, ch.first_bearing, s3, th3)
                if loc3 is None:
                    continue
                c3, v3 = loc3["point"], None
            else:
                c3, v3 = mec3["center"], mec3["verts"]
            self._note(op="intersect3", k=k, candidate=np.asarray(c3).tolist(), t=self.virtual_time)
            for p in clear_poses(c3, s3, v3):
                if ch.status != "detected":
                    return
                if self._try_clear_at(k, p):
                    return
            break
        ch.halfplane_failed = True

    def _try_localize(self, k: int) -> None:
        ch = self.state.channels[k]
        if ch.status != "detected" or ch.first_site is None:
            return
        if ch.n_clear_try >= MAX_CLEAR or ch.extra_measures >= MAX_MEASURE:
            ch.halfplane_failed = True
            return
        if ch.second_site is None:
            self._second_measure(k)
            ch = self.state.channels[k]
        if ch.status == "cleared":
            return
        if ch.second_site is not None and ch.second_bearing is not None:
            self._clear_from_two_bearings(k)
            return
        if ch.first_bearing is not None:
            u = np.array(
                [np.cos(np.deg2rad(ch.first_bearing)), np.sin(np.deg2rad(ch.first_bearing))],
                dtype=float,
            )
            g_hat = np.asarray(ch.first_site, dtype=float) + 800.0 * u
            self._note(op="fallback_ghat", k=k, x=float(g_hat[0]), y=float(g_hat[1]))
            if self._try_clear_at(k, g_hat):
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
                nxt = next_snake_point(self.state, certificate_mode=cert)
                if nxt is None:
                    nxt = next_snake_point(self.state, certificate_mode=True)
                if nxt is not None:
                    before = self.n_measure
                    self.scan_at(nxt, certificate_mode=cert)
                    if self.n_measure == before:
                        for ch in self.state.channels.values():
                            if ch.status != "unseen":
                                continue
                            rem = ch.remaining_p4()
                            if rem:
                                self.scan_at(p4_points()[rem[0]], certificate_mode=False)
                                break
                        if self.n_measure == before:
                            self.failure = "no_progress"
                            self._note(op="no_progress", nxt=np.asarray(nxt).tolist(), guard=guard)
                            break
                    self.process_pending()
                    continue
                pend = self.state.pending_detected()
                if pend:
                    for pk in pend:
                        ch = self.state.channels[pk]
                        if ch.extra_measures < MAX_MEASURE:
                            ch.halfplane_failed = False
                            self._try_localize(pk)
                    if self.state.pending_detected():
                        self.failure = self.failure or "pending_unresolved"
                        self._note(op="stop_pending", pending=list(self.state.pending_detected()), guard=guard)
                    break
                self._note(op="stop_none", guard=guard, unseen=self.state.unseen_channels())
                break
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

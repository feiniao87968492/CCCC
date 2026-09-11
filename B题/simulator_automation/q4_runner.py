"""Q4 practice: P4 discovery, cumulative localization, certified optical fallback."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from params import CLEAR_RADIUS
from q4_cover import cover_index, current_cover_mode
from q4_localize import history_region, legal_xy, optical_cover_points, second_measure_points
from q4_policy import next_snake_point
from q4_state import Q4State

# Only cap heuristic refinement. The optical coverage certificate has no such cap.
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
        self.failed_clear_points = {k: [] for k in self.state.channels}
        self._regions = {}
        self._last_processed = {}
        self.n_optical_fallback = 0
        self.cover_visited = set()
        self.cover_mode = current_cover_mode()

    def _note(self, **kw) -> None:
        self.log.append(kw)

    def _move_to(self, pos) -> None:
        q = np.asarray(pos, dtype=float).reshape(2)
        self.move_m += float(np.linalg.norm(q - self.state.pos))
        self.state.pos = q.copy()

    def measure(self, x, y, k: int) -> dict:
        resp = self.robot.measure(float(x), float(y), int(k))
        if resp.get("accepted") is not True:
            raise RuntimeError("measure rejected; state and clock unchanged")
        self.n_measure += 1
        self._move_to([x, y])
        self.measure_channel = int(k)
        self.virtual_time = float(resp.get("virtual_time_s", self.virtual_time))
        result, svd = resp.get("measure_result"), resp.get("svd_deg")
        self.state.apply_measure(int(k), [x, y], result, svd)
        self._note(op="measure", k=k, x=float(x), y=float(y), result=result, svd=svd, t=self.virtual_time)
        return resp

    def clear(self, x, y, k: int) -> bool:
        resp = self.robot.clear(float(x), float(y), int(k))
        if resp.get("accepted") is not True:
            raise RuntimeError("clear rejected; state and clock unchanged")
        self.n_clear += 1
        self._move_to([x, y])
        self.virtual_time = float(resp.get("virtual_time_s", self.virtual_time))
        ok = resp.get("clear_result") == "success"
        self.state.apply_clear(int(k), [x, y], ok)
        if ok:
            self.n_clear_ok += 1
        else:
            self.failed_clear_points[k].append(np.array([x, y], dtype=float))
        self._note(op="clear", k=k, x=float(x), y=float(y), ok=ok, t=self.virtual_time)
        return ok

    def _channels_to_scan(self, p, *, certificate_mode: bool) -> list[int]:
        idx = cover_index(p)
        out = []
        for k, ch in self.state.channels.items():
            if ch.status in ("cleared", "certified_absent"):
                continue
            if idx is not None and idx in ch.visited_p4:
                continue
            if ch.status == "detected" and not certificate_mode:
                continue
            out.append(k)
        return sorted(out, key=lambda k: (k != self.measure_channel, k))

    def scan_at(self, p, *, certificate_mode: bool = False) -> None:
        p = np.asarray(p, dtype=float).reshape(2)
        idx = cover_index(p)
        if idx is not None:
            self.cover_visited.add(idx)
        for k in self._channels_to_scan(p, certificate_mode=certificate_mode):
            resp = self.measure(*p, k)
            if resp.get("measure_result") == "near":
                self.clear(*p, k)
        # Every direction is queued; process_pending moves only after the sweep.

    def _region(self, k):
        history = self.state.channels[k].history
        positives = sum(h["result"] in ("direction", "near") for h in history)
        cached = self._regions.get(k)
        if cached is None or cached[0] != positives:
            cached = (positives, history_region(history))
            self._regions[k] = cached
        return cached[1]

    def _try_clear_at(self, k: int, p) -> bool:
        p = np.asarray(p, dtype=float).reshape(2)
        if not legal_xy(p):
            return False
        if any(np.linalg.norm(p - prev) < 1e-7 for prev in self.failed_clear_points[k]):
            return False
        return self.clear(*p, k)

    def _refinement_points(self, k, region):
        ch = self.state.channels[k]
        bearings = [h for h in ch.history if h["result"] == "direction"]
        if len(bearings) == 1:
            last = bearings[-1]
            candidates = second_measure_points(last["pos"], last["svd"], self.state.pos)
        else:
            last = bearings[-1]
            center = region["center"]
            toward = np.asarray(last["pos"]) - center
            norm = float(np.linalg.norm(toward))
            toward = toward / norm if norm > 1e-9 else np.array([1., 0.])
            lateral = np.array([-toward[1], toward[0]])
            distance = float(np.clip(2 * region["rho"], 60, 250))
            candidates = [center + distance * toward,
                          center + distance * (0.7 * toward + lateral),
                          center + distance * (0.7 * toward - lateral),
                          center - distance * toward]
        measured = [h["pos"] for h in ch.history]
        return [p for p in candidates if legal_xy(p) and
                all(np.linalg.norm(p - q) > 1.0 for q in measured)]

    def _optical_fallback(self, k, region):
        self.n_optical_fallback += 1
        candidates = optical_cover_points(region["verts"])
        self._note(op="optical_cover", k=k, count=len(candidates), rho=region["rho"], t=self.virtual_time)
        while candidates:
            i = min(range(len(candidates)), key=lambda i: float(np.linalg.norm(candidates[i] - self.state.pos)))
            if self._try_clear_at(k, candidates.pop(i)):
                return
        raise RuntimeError(f"channel {k}: optical cover exhausted without success")

    def _try_localize(self, k: int) -> None:
        ch = self.state.channels[k]
        if ch.status != "detected":
            return
        for _ in range(MAX_MEASURE + 1):
            region = self._region(k)
            if region is None:
                raise RuntimeError(f"channel {k}: positive observations have empty feasible region")
            self._note(op="posterior", k=k, rho=region["rho"],
                       center=region["center"].tolist(), t=self.virtual_time)
            # Certified clear remains allowed after the heuristic budget expires.
            if region["rho"] <= CLEAR_RADIUS - 1e-6:
                if self._try_clear_at(k, region["center"]):
                    return
                self._optical_fallback(k, region)
                return
            # At most two center trials; further clearing uses a coverage proof.
            if region["rho"] <= 80 and len(self.failed_clear_points[k]) < 2:
                if self._try_clear_at(k, region["center"]):
                    return
            if ch.extra_measures >= MAX_MEASURE:
                break
            candidates = self._refinement_points(k, region)
            if not candidates:
                break
            progressed = False
            for p in candidates:
                if ch.extra_measures >= MAX_MEASURE:
                    break
                ch.extra_measures += 1
                resp = self.measure(*p, k)
                if resp["measure_result"] == "near":
                    if self._try_clear_at(k, p):
                        return
                if resp["measure_result"] == "direction":
                    progressed = True
                    break
            if not progressed:
                break
        self._optical_fallback(k, self._region(k))

    def process_pending(self) -> None:
        pending = list(self.state.pending_detected())
        while pending:
            def distance(k):
                region = self._region(k)
                return float(np.linalg.norm(region["center"] - self.state.pos)) if region else float("inf")
            k = min(pending, key=distance)
            pending.remove(k)
            ch = self.state.channels[k]
            if self._last_processed.get(k) == len(ch.history):
                continue
            self._try_localize(k)
            self._last_processed[k] = len(ch.history)

    def done(self) -> bool:
        return all(ch.status in ("cleared", "certified_absent") for ch in self.state.channels.values())

    def run(self) -> dict:
        _assert_no_oracle()
        try:
            enter = self.robot.enter()
            if enter.get("accepted") is not True:
                raise RuntimeError("enter rejected")
            self.virtual_time = float(enter.get("virtual_time_s", 0.0))
            self.scan_at(np.zeros(2))
            self.process_pending()
            for _ in range(400):
                if self.done():
                    break
                nxt = next_snake_point(self.state, certificate_mode=True)
                if nxt is None:
                    self.failure = "pending_unresolved"
                    break
                before = self.n_measure
                self.scan_at(nxt, certificate_mode=True)
                self.process_pending()
                if self.n_measure == before:
                    self.failure = "no_progress"
                    break
            if not self.done() and self.failure is None:
                self.failure = "iteration_limit"
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
                    self.failure = self.failure or "exit_failed"
                    self._note(op="exit_failed", err=str(exc))
        K = sum(ch.status == "cleared" for ch in self.state.channels.values())
        T = self.virtual_time
        return dict(strategy="Q4_P4", revision="cumulative-optical-v2", failure=self.failure,
                    cover_mode=self.cover_mode, K=K, T=T, T_over_K=(T / K) if K else None,
                    wall_s=time.perf_counter() - self.t0, move_m=self.move_m,
                    n_measure=self.n_measure, n_clear=self.n_clear, n_clear_ok=self.n_clear_ok,
                    n_optical_fallback=self.n_optical_fallback,
                    n_cover_visited=len(self.cover_visited),
                    detected=sum(ch.ever_detected for ch in self.state.channels.values()),
                    certified_absent=[k for k, ch in self.state.channels.items() if ch.status == "certified_absent"],
                    cleared_channels=[k for k, ch in self.state.channels.items() if ch.status == "cleared"],
                    pending=self.state.pending_detected(), all_certified=self.done(),
                    channel_status={str(k): ch.status for k, ch in self.state.channels.items()})

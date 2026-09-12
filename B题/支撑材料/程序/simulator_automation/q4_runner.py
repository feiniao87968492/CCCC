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
from q4_cover import cover_index, cover_points, cover_route, current_cover_mode, current_hex37_route_name
from q4_adaptive import ReceptionBelief, ranked_refinement_points
from q4_localize import history_region, legal_xy, optical_cover_points, second_measure_points
from q4_policy import (
    INSERT_MAX_M,
    PRIORITY_AGGR_CLEAR,
    PRIORITY_CERT_CLEAR,
    PRIORITY_MEASURE,
    PRIORITY_STRONG_CLEAR,
    ROUTE_INSERT_V1,
    ROUTE_INSERT_V2,
    ROUTE_INSERT_V3,
    ROUTE_ADAPTIVE_V4,
    act_now_vs_lookahead,
    choose_insert_or_cover,
    clear_time_cost,
    current_route_mode,
    current_v3_params,
    insertion_extra,
    next_route_cover,
    next_snake_point,
    pending_batch_order,
    probe_detected_worthwhile,
    probe_detected_worthwhile_v3,
    remaining_route_covers,
)
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
        self.route_mode = current_route_mode()
        self.localization_move = 0.0
        self.n_insert = 0
        self.n_defer = 0
        self.n_batch = 0
        self.n_probe = 0
        self.n_aggressive_clear = 0
        self.n_aggressive_clear_ok = 0
        self._aggressive_tries = {k: 0 for k in self.state.channels}
        self.pending_max = 0
        self._loc_leg = False
        self.first_detect_index: dict[int, int] = {}
        self.actual_cover_order = []
        self._beliefs = {}
        self.n_replan = 0
        self.planner_wall_s = 0.0

    def _note(self, **kw) -> None:
        self.log.append(kw)

    def _move_to(self, pos) -> None:
        q = np.asarray(pos, dtype=float).reshape(2)
        dist = float(np.linalg.norm(q - self.state.pos))
        self.move_m += dist
        if self._loc_leg:
            self.localization_move += dist
        self.state.pos = q.copy()
        idx = cover_index(q)
        if idx is not None and idx not in self.actual_cover_order:
            self.actual_cover_order.append(idx)

    def _note_pending(self) -> None:
        n = len(self.state.pending_detected())
        if n > self.pending_max:
            self.pending_max = n

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
        if result in ("direction", "near") and k not in self.first_detect_index:
            idx = cover_index([x, y])
            if idx is not None:
                self.first_detect_index[k] = self.actual_cover_order.index(idx)
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
            if self.state.channels[k].status in ("cleared", "certified_absent"):
                continue  # The N=16 certificate can fire part-way through this sweep.
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
        if self.route_mode == ROUTE_ADAPTIVE_V4:
            return ranked_refinement_points(region, ch.history, self.state.pos,
                                            self._next_cover_xy(), belief=self._reception_belief(k))
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

    def _try_localize(self, k: int, *, allow_optical: bool = True) -> None:
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
                if allow_optical:
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
                if self.route_mode == ROUTE_ADAPTIVE_V4:
                    # A negative reading changes RF weights too. Re-rank before
                    # spending another measurement on the old candidate list.
                    progressed = True
                    break
            if not progressed:
                break
        if allow_optical:
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

    def _cover_need(self) -> set[int]:
        need: set[int] = set()
        for ch in self.state.channels.values():
            if ch.status == "unseen":
                need.update(ch.remaining_cover())
        return need

    def _next_cover_xy(self):
        return next_route_cover(self.cover_visited, self._cover_need())

    def _pending_task_site(self, k: int):
        ch = self.state.channels[k]
        if ch.status != "detected":
            return None, None
        region = self._region(k)
        if region is None:
            return None, "optical"
        center = region["center"]
        already = any(np.linalg.norm(center - prev) < 1e-7 for prev in self.failed_clear_points[k])
        if region["rho"] <= CLEAR_RADIUS - 1e-6:
            if already:
                return None, "optical"
            return center, "clear"
        if region["rho"] <= 80 and len(self.failed_clear_points[k]) < 2 and not already:
            return center, "clear"
        if ch.extra_measures >= MAX_MEASURE:
            return None, "optical"
        candidates = self._refinement_points(k, region)
        if not candidates:
            return None, "optical"
        u = self._next_cover_xy()
        q = min(candidates, key=lambda p: insertion_extra(self.state.pos, p, u))
        return q, "measure"

    def _do_insert(self, k: int, q, kind: str) -> None:
        self._loc_leg = True
        try:
            if kind == "clear":
                self._try_clear_at(k, q)
                return
            ch = self.state.channels[k]
            if ch.extra_measures >= MAX_MEASURE:
                return
            ch.extra_measures += 1
            resp = self.measure(*np.asarray(q, dtype=float).reshape(2), k)
            if resp.get("measure_result") == "near":
                self._try_clear_at(k, q)
        finally:
            self._loc_leg = False

    def _drain_pending(self) -> None:
        self._loc_leg = True
        try:
            self.process_pending()
            leftover = list(self.state.pending_detected())
            for k in leftover:
                ch = self.state.channels[k]
                if ch.status == "detected":
                    self._try_localize(k)
        finally:
            self._loc_leg = False

    def _step_insert_v1(self) -> str:
        """One scheduler step. Returns 'ok', 'done', or a failure token."""
        if self.done():
            return "done"
        self._note_pending()
        x = self.state.pos
        u = self._next_cover_xy()
        cands = []
        for k in self.state.pending_detected():
            q, kind = self._pending_task_site(k)
            if q is None or kind == "optical":
                continue
            cands.append((k, q, kind))
        pairs = [(k, q) for k, q, _kind in cands]
        if u is None:
            if self.state.pending_detected():
                self._drain_pending()
                return "ok" if not self.done() else "done"
            if self._cover_need():
                return "pending_unresolved"
            return "done" if self.done() else "pending_unresolved"
        kind, ident = choose_insert_or_cover(x, u, pairs)
        if kind == "insert" and ident is not None:
            self.n_insert += 1
            q, task_kind = next((q, knd) for k, q, knd in cands if k == ident)
            self._note(op="insert", k=int(ident), kind=task_kind,
                       extra=insertion_extra(x, q, u), t=self.virtual_time)
            self._do_insert(ident, q, task_kind)
            self._note_pending()
            return "ok"
        if pairs:
            self.n_defer += 1
            self._note(op="defer", n_pending=len(pairs), t=self.virtual_time)
        before = self.n_measure
        self.scan_at(u, certificate_mode=True)
        self._note_pending()
        if self.n_measure == before and not self.done():
            return "no_progress"
        return "ok"

    def _run_old(self) -> None:
        self.scan_at(np.zeros(2))
        self.process_pending()
        self._note_pending()
        for _ in range(400):
            if self.done():
                return
            nxt = next_snake_point(self.state, certificate_mode=True)
            if nxt is None:
                self.failure = "pending_unresolved"
                return
            before = self.n_measure
            self.scan_at(nxt, certificate_mode=True)
            self.process_pending()
            self._note_pending()
            if self.n_measure == before:
                self.failure = "no_progress"
                return
        if not self.done():
            self.failure = "iteration_limit"

    def _run_insert_v1(self) -> None:
        self.scan_at(np.zeros(2))
        self._note_pending()
        for _ in range(800):
            status = self._step_insert_v1()
            if status == "done":
                return
            if status != "ok":
                self.failure = status
                return
        if not self.done():
            self.failure = "iteration_limit"

    def _probe_detected_at(self, p) -> None:
        p = np.asarray(p, dtype=float).reshape(2)
        idx = cover_index(p)
        for k, ch in self.state.channels.items():
            if ch.status != "detected":
                continue
            if idx is not None and idx in ch.visited_p4:
                continue
            bearings = [h for h in ch.history if h["result"] == "direction"]
            sites = [h["pos"] for h in bearings]
            degs = [h["svd"] for h in bearings]
            if not probe_detected_worthwhile(p, self._region(k), sites, degs):
                continue
            self.n_probe += 1
            resp = self.measure(*p, k)
            if resp.get("measure_result") == "near":
                self.clear(*p, k)

    def _on_path_pending(self, x, u, cands):
        return [(k, q, kind) for k, q, kind in cands if insertion_extra(x, q, u) <= INSERT_MAX_M]

    def _process_batch(self, x, u, group) -> None:
        items = [(k, q) for k, q, _kind in group]
        order = pending_batch_order(x, items, u)
        self.n_batch += 1
        self._loc_leg = True
        try:
            for k in order:
                if self.state.channels[k].status != "detected":
                    continue
                self.n_insert += 1
                self._note(op="batch_localize", k=int(k), t=self.virtual_time)
                self._try_localize(k, allow_optical=False)
        finally:
            self._loc_leg = False

    def _drain_pending_v2(self) -> None:
        self._loc_leg = True
        try:
            items = []
            for k in self.state.pending_detected():
                q, _kind = self._pending_task_site(k)
                if q is None:
                    region = self._region(k)
                    q = region["center"] if region is not None else self.state.pos
                items.append((k, q))
            order = pending_batch_order(self.state.pos, items, None)
            self.n_batch += 1
            for k in order:
                if self.state.channels[k].status == "detected":
                    self._try_localize(k, allow_optical=True)
            for k in list(self.state.pending_detected()):
                if self.state.channels[k].status == "detected":
                    self._try_localize(k, allow_optical=True)
        finally:
            self._loc_leg = False

    def _step_insert_v2(self) -> str:
        if self.done():
            return "done"
        self._note_pending()
        x = self.state.pos
        u = self._next_cover_xy()
        cands = []
        for k in self.state.pending_detected():
            q, kind = self._pending_task_site(k)
            if q is None or kind == "optical":
                continue
            cands.append((k, q, kind))
        pairs = [(k, q) for k, q, _kind in cands]
        if u is None:
            if self.state.pending_detected():
                self._drain_pending_v2()
                return "ok" if not self.done() else "done"
            if self._cover_need():
                return "pending_unresolved"
            return "done" if self.done() else "pending_unresolved"
        kind, ident = choose_insert_or_cover(x, u, pairs)
        if kind == "insert" and ident is not None:
            group = self._on_path_pending(x, u, cands)
            if not group:
                group = [c for c in cands if c[0] == ident]
            self._note(op="insert_batch", n=len(group), t=self.virtual_time)
            self._process_batch(x, u, group)
            self._note_pending()
            return "ok"
        if pairs:
            self.n_defer += 1
            self._note(op="defer", n_pending=len(pairs), t=self.virtual_time)
        before = self.n_measure
        self.scan_at(u, certificate_mode=False)
        self._probe_detected_at(u)
        self._note_pending()
        if self.n_measure == before and not self.done():
            return "no_progress"
        return "ok"

    def _run_insert_v2(self) -> None:
        self.scan_at(np.zeros(2), certificate_mode=False)
        self._probe_detected_at(np.zeros(2))
        self._note_pending()
        for _ in range(800):
            status = self._step_insert_v2()
            if status == "done":
                return
            if status != "ok":
                self.failure = status
                return
        if not self.done():
            self.failure = "iteration_limit"

    def _future_covers(self, limit: int | None = None):
        n = current_v3_params().lookahead if limit is None else limit
        return remaining_route_covers(self.cover_visited, self._cover_need(), n)

    def _probe_detected_at_v3(self, p) -> None:
        p = np.asarray(p, dtype=float).reshape(2)
        idx = cover_index(p)
        for k, ch in self.state.channels.items():
            if ch.status != "detected":
                continue
            if idx is not None and idx in ch.visited_p4:
                continue
            bearings = [h for h in ch.history if h["result"] == "direction"]
            sites = [h["pos"] for h in bearings]
            degs = [h["svd"] for h in bearings]
            if not probe_detected_worthwhile_v3(p, self._region(k), sites, degs):
                continue
            self.n_probe += 1
            resp = self.measure(*p, k)
            if resp.get("measure_result") == "near":
                self.clear(*p, k)

    def _classify_v3(self, k, x, u):
        ch = self.state.channels[k]
        if ch.status != "detected":
            return None
        region = self._region(k)
        if region is None:
            return None
        center = region["center"]
        extra_c = insertion_extra(x, center, u)
        already = any(np.linalg.norm(center - prev) < 1e-7 for prev in self.failed_clear_points[k])
        rho = float(region["rho"])
        params = current_v3_params()
        if rho <= CLEAR_RADIUS - 1e-6:
            if already:
                return None
            return (k, center, "cert_clear", PRIORITY_CERT_CLEAR, extra_c)
        if rho <= params.strong_clear_rho and not already:
            return (k, center, "strong_clear", PRIORITY_STRONG_CLEAR, extra_c)
        if (
            rho <= params.aggressive_clear_rho
            and self._aggressive_tries[k] < params.aggressive_clear_max
            and not already
        ):
            return (k, center, "aggr_clear", PRIORITY_AGGR_CLEAR, extra_c)
        if ch.extra_measures >= MAX_MEASURE:
            return None
        candidates = self._refinement_points(k, region)
        if not candidates:
            return None
        q = min(candidates, key=lambda p: insertion_extra(x, p, u))
        extra_m = insertion_extra(x, q, u)
        return (k, q, "measure", PRIORITY_MEASURE, extra_m)

    def _select_v3_now(self, x, u, future):
        params = current_v3_params()
        selected = []
        deferred = 0
        for k in self.state.pending_detected():
            task = self._classify_v3(k, x, u)
            if task is None:
                continue
            _k, q, kind, _pr, extra = task
            cap = params.measure_insert_max if kind == "measure" else params.clear_insert_max
            if extra > cap:
                deferred += 1
                continue
            if future and not act_now_vs_lookahead(x, q, future, params.lookahead_slack):
                deferred += 1
                continue
            selected.append(task)
        return selected, deferred

    def _do_v3_action(self, k, q, kind) -> None:
        region = self._region(k)
        rho = float(region["rho"]) if region is not None else 1e9
        if kind in ("cert_clear", "strong_clear", "aggr_clear"):
            if rho > 20:
                self.n_aggressive_clear += 1
            if rho > 60:
                self._aggressive_tries[k] += 1
            ok = self._try_clear_at(k, q)
            if rho > 20 and ok:
                self.n_aggressive_clear_ok += 1
            return
        ch = self.state.channels[k]
        if ch.extra_measures >= MAX_MEASURE:
            return
        ch.extra_measures += 1
        resp = self.measure(*np.asarray(q, dtype=float).reshape(2), k)
        if resp.get("measure_result") == "near":
            self._try_clear_at(k, q)

    def _process_v3_tasks(self, x, u, tasks) -> None:
        if not tasks:
            return
        cert = [t for t in tasks if t[3] == PRIORITY_CERT_CLEAR]
        rest = [t for t in tasks if t[3] != PRIORITY_CERT_CLEAR]
        rest.sort(key=lambda t: (t[3], clear_time_cost(t[4]) if t[2].endswith("clear") else t[4]))
        ordered = [t[0] for t in cert]
        if rest:
            ordered.extend(pending_batch_order(x, [(t[0], t[1]) for t in rest], u))
        by_id = {t[0]: t for t in tasks}
        self.n_batch += 1
        self._loc_leg = True
        try:
            for k in ordered:
                task = by_id.get(k)
                if task is None or self.state.channels[k].status != "detected":
                    continue
                self.n_insert += 1
                self._note(op="v3_action", k=int(k), kind=task[2], extra=task[4], t=self.virtual_time)
                self._do_v3_action(k, task[1], task[2])
        finally:
            self._loc_leg = False

    def _step_insert_v3(self) -> str:
        if self.done():
            return "done"
        self._note_pending()
        x = self.state.pos
        future = self._future_covers()
        u = future[0] if future else None
        selected, n_skip = self._select_v3_now(x, u, future)
        if u is None:
            if self.state.pending_detected():
                self._drain_pending_v2()
                return "ok" if not self.done() else "done"
            if self._cover_need():
                return "pending_unresolved"
            return "done" if self.done() else "pending_unresolved"
        if selected:
            self._process_v3_tasks(x, u, selected)
            self._note_pending()
            return "ok"
        if n_skip or self.state.pending_detected():
            self.n_defer += 1
            self._note(op="defer", n_pending=len(self.state.pending_detected()), t=self.virtual_time)
        before = self.n_measure
        self.scan_at(u, certificate_mode=False)
        self._probe_detected_at_v3(u)
        self._note_pending()
        if self.n_measure == before and not self.done():
            return "no_progress"
        return "ok"

    def _run_insert_v3(self) -> None:
        self.scan_at(np.zeros(2), certificate_mode=False)
        self._probe_detected_at_v3(np.zeros(2))
        self._note_pending()
        for _ in range(800):
            status = self._step_insert_v3()
            if status == "done":
                return
            if status != "ok":
                self.failure = status
                return
        if not self.done():
            self.failure = "iteration_limit"

    def done(self) -> bool:
        return all(ch.status in ("cleared", "certified_absent") for ch in self.state.channels.values())

    def _reception_belief(self, k):
        history = self.state.channels[k].history
        cached = self._beliefs.get(k)
        if cached is None or cached[0] != len(history):
            cached = (len(history), ReceptionBelief(self._region(k), history))
            self._beliefs[k] = cached
        return cached[1]

    def _adaptive_task(self, k):
        region = self._region(k)
        if region is None:
            raise RuntimeError(f"channel {k}: positive observations have empty feasible region")
        center, rho = region["center"], float(region["rho"])
        tried = any(np.linalg.norm(center - p) < 1e-7 for p in self.failed_clear_points[k])
        if rho <= CLEAR_RADIUS - 1e-6 and not tried:
            return center, "cert_clear"
        if rho <= 80 and len(self.failed_clear_points[k]) < 2 and not tried:
            return center, "aggr_clear"
        if self.state.channels[k].extra_measures < MAX_MEASURE:
            points = self._refinement_points(k, region)
            if points:
                return points[0], "measure"
        return center, "optical"

    def _probe_detected_at_v4(self, p):
        for k in list(self.state.pending_detected()):
            ch = self.state.channels[k]
            if any(np.linalg.norm(p - h["pos"]) <= 1 for h in ch.history):
                continue
            region = self._region(k)
            if region is None or region["rho"] <= 40:
                continue
            belief = self._reception_belief(k)
            if belief.reception_probability(p) < .7 or belief.expected_gain(p) < .3:
                continue
            self.n_probe += 1
            resp = self.measure(*p, k)
            if resp.get("measure_result") == "near":
                self._try_clear_at(k, p)

    def _run_adaptive_v4(self):
        """Replan a joint open route after every observation/clear, never stale batches."""
        self.scan_at(np.zeros(2))
        for _ in range(800):
            if self.done():
                return
            self._note_pending()
            started = time.perf_counter()
            need = self._cover_need() - self.cover_visited
            pts = cover_points()
            tasks = [(('cover', i), pts[i]) for i in cover_route() if i in need]
            kinds = {}
            for k in self.state.pending_detected():
                p, kind = self._adaptive_task(k)
                ident = ('source', k)
                tasks.append((ident, p))
                kinds[ident] = kind
            if not tasks:
                self.failure = "pending_unresolved"
                return
            order = pending_batch_order(self.state.pos, tasks)
            ident = order[0]
            p = dict(tasks)[ident]
            self.n_replan += 1
            self.planner_wall_s += time.perf_counter() - started
            if ident[0] == "cover":
                self.scan_at(p)
                self._probe_detected_at_v4(p)
                continue
            k, kind = ident[1], kinds[ident]
            self.n_insert += 1
            self._note(op="v4_action", k=k, kind=kind, t=self.virtual_time)
            self._loc_leg = True
            try:
                if kind == "optical":
                    self._optical_fallback(k, self._region(k))
                else:
                    self._do_v3_action(k, p, kind)
            finally:
                self._loc_leg = False
        if not self.done():
            self.failure = "iteration_limit"

    def run(self) -> dict:
        _assert_no_oracle()
        try:
            enter = self.robot.enter()
            if enter.get("accepted") is not True:
                raise RuntimeError("enter rejected")
            self.virtual_time = float(enter.get("virtual_time_s", 0.0))
            if self.route_mode == ROUTE_ADAPTIVE_V4:
                self._run_adaptive_v4()
            elif self.route_mode == ROUTE_INSERT_V3:
                self._run_insert_v3()
            elif self.route_mode == ROUTE_INSERT_V2:
                self._run_insert_v2()
            elif self.route_mode == ROUTE_INSERT_V1:
                self._run_insert_v1()
            else:
                self._run_old()
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
        revision = "adaptive-reception-v4" if self.route_mode == ROUTE_ADAPTIVE_V4 else "cumulative-optical-v2"
        return dict(strategy="Q4_P4", revision=revision, failure=self.failure,
                    cover_mode=self.cover_mode, route_mode=self.route_mode,
                    K=K, T=T, T_over_K=(T / K) if K else None,
                    wall_s=time.perf_counter() - self.t0, move_m=self.move_m,
                    localization_move=self.localization_move,
                    n_measure=self.n_measure, n_clear=self.n_clear, n_clear_ok=self.n_clear_ok,
                    n_optical_fallback=self.n_optical_fallback,
                    n_cover_visited=len(self.cover_visited),
                    n_insert=self.n_insert, n_defer=self.n_defer, pending_max=self.pending_max,
                    n_batch=self.n_batch, n_probe=self.n_probe,
                    n_replan=self.n_replan, planner_wall_s=self.planner_wall_s,
                    n_aggressive_clear=self.n_aggressive_clear,
                    n_aggressive_clear_ok=self.n_aggressive_clear_ok,
                    hex37_route=current_hex37_route_name() if self.cover_mode == "HEX37" else None,
                    actual_cover_order=list(self.actual_cover_order),
                    first_detect_indices=list(self.first_detect_index.values()),
                    mean_first_detect_index=(
                        float(np.mean(list(self.first_detect_index.values())))
                        if self.first_detect_index else None
                    ),
                    p95_first_detect_index=(
                        float(np.quantile(list(self.first_detect_index.values()), 0.95))
                        if self.first_detect_index else None
                    ),
                    detected=sum(ch.ever_detected for ch in self.state.channels.values()),
                    certified_absent=[k for k, ch in self.state.channels.items() if ch.status == "certified_absent"],
                    cleared_channels=[k for k, ch in self.state.channels.items() if ch.status == "cleared"],
                    pending=self.state.pending_detected(), all_certified=self.done(),
                    channel_status={str(k): ch.status for k, ch in self.state.channels.items()})

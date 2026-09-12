"""Q3 online closed loop. API observations only; never imports q2_validation."""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from q3_safe import clipped_then_full
from q3_state import P3, Q3State, cover_index, dist, pos_key, shortest_next

# Guard: oracle modules must not be imported by this runner.
_BANNED = ("q2_validation", "q2_scenario")


def _assert_no_oracle() -> None:
    for name in _BANNED:
        if name in sys.modules:
            raise RuntimeError(f"oracle module loaded: {name}")


class Q3Runner:
    def __init__(self, robot, strategy: str = "SAFE"):
        _assert_no_oracle()
        self.robot = robot
        self.strategy = str(strategy).upper().replace("_ACTIVE", "").replace("_ONLY", "")
        if self.strategy not in {"SAFE", "ROBUST", "FAST", "HYBRID", "GREEDY"}:
            raise ValueError(self.strategy)
        self.state = Q3State()
        self.t0 = time.perf_counter()
        self.log = []
        self.local_cover_attempted = set()

    def _note(self, **kw) -> None:
        self.log.append(kw)

    def _account_move(self, pos, k: int | None) -> float:
        st = self.state
        d = dist(st.pos, pos)
        st.move_distance += d
        if st.phase == "safe":
            st.safe_move += d
            if k is not None:
                st.channels[k].safe_move += d
        elif st.phase == "active":
            st.loc_move += d
            if k is not None:
                st.channels[k].loc_move += d
        else:
            st.global_move += d
        st.pos = np.asarray(pos, dtype=float).reshape(2)
        return d

    def measure(self, x, y, k: int, *, active: bool = False) -> dict:
        pos = np.array([float(x), float(y)], dtype=float)
        t_before = self.state.virtual_time
        resp = self.robot.measure(float(x), float(y), int(k))
        st = self.state
        st.n_measure += 1
        self._account_move(pos, k)
        st.measure_channel = int(k)
        st.virtual_time = float(resp.get("virtual_time_s", st.virtual_time))
        st.measure_time += max(0.0, st.virtual_time - t_before)
        ch = st.channels[k]
        result = resp.get("measure_result")
        svd = resp.get("svd_deg")
        ch.history.append({"pos": [float(x), float(y)], "result": result, "svd": svd})
        ch.measured_positions.append(pos_key(pos))
        idx = cover_index(pos)
        if result == "near":
            ch.status = "detected"
            ch.ever_detected = True
            ch.receptions.append(pos.copy())
            if ch.t_first_detect is None:
                ch.t_first_detect = st.virtual_time
            if k not in st.P:
                st.P.append(k)
        elif result == "direction":
            ch.status = "detected"
            ch.ever_detected = True
            ch.receptions.append(pos.copy())
            if ch.t_first_detect is None:
                ch.t_first_detect = st.virtual_time
            if ch.first_site is None:
                ch.first_site = pos.copy()
                ch.first_bearing = float(svd)
            if k not in st.P:
                st.P.append(k)
        elif result == "no_signal":
            if idx is not None and not ch.ever_detected:
                ch.V.add(idx)
                if len(ch.V) >= 7 and ch.status == "unseen":
                    ch.status = "certified_absent"
        if active:
            st.n_active_measure += 1
            ch.extra_measures += 1
            ch.active_positions.append([float(x), float(y)])
        if st.discovery_cancelled():
            st.R = []
        self._note(op="measure", k=k, result=result, x=float(x), y=float(y), T=st.virtual_time, active=active)
        return resp

    def clear(self, x, y, k: int) -> bool:
        pos = np.array([float(x), float(y)], dtype=float)
        t_before = self.state.virtual_time
        resp = self.robot.clear(float(x), float(y), int(k))
        st = self.state
        st.n_clear += 1
        self._account_move(pos, k)
        st.virtual_time = float(resp.get("virtual_time_s", st.virtual_time))
        st.clear_time += max(0.0, st.virtual_time - t_before)
        ok = resp.get("clear_result") == "success"
        if ok:
            st.n_clear_ok += 1
            st.channels[k].status = "cleared"
            st.channels[k].t_clear = st.virtual_time
            if k in st.P:
                st.P.remove(k)
        self._note(op="clear", k=k, ok=ok, x=float(x), y=float(y), T=st.virtual_time)
        return ok

    def heuristic_clear(self, x, y, k):
        """Reject impossible speculative actions before sending or moving.

        Near responses and complete SAFE fallback use clear() directly so an
        inconsistent posterior cannot disable the independent fallback.
        """
        from q3_safe import cell_may_contain_target
        verts = self.posterior_vertices(k)
        if verts is not None and not cell_may_contain_target(
                np.array([x, y]), verts, slack=1e-6):
            self._note(op="clear_filtered", k=k, x=float(x), y=float(y),
                       reason="disjoint_posterior")
            return False
        return self.clear(x, y, k)

    def pending_clear_ready(self, k):
        """Retain the task but stop routine sensing when <=4 visits suffice."""
        from q3_safe import local_cover_route
        if self.certified_clear_point(k) is not None:
            return True
        if k in self.local_cover_attempted:
            return False
        # Failed clears can contradict the direction model; continue sensing.
        if any(e.get("op") == "clear" and e.get("k") == k and not e.get("ok")
               for e in self.log):
            return False
        route = local_cover_route(self.posterior_vertices(k), self.state.pos)
        return 0 < len(route) <= 4

    def _scan_unseen_at(self, p) -> None:
        self.state.phase = "global"
        p = np.asarray(p, dtype=float).reshape(2)
        for k2 in list(self.state.unseen_to_scan()):
            resp = self.measure(p[0], p[1], k2)
            if resp.get("measure_result") == "near":
                self.clear(p[0], p[1], k2)

    def visit_cover(self, p) -> None:
        self.state.phase = "global"
        p = np.asarray(p, dtype=float).reshape(2)
        for k in list(self.state.unseen_to_scan()):
            resp = self.measure(p[0], p[1], k)
            if resp.get("measure_result") == "near":
                self.clear(p[0], p[1], k)
        if self.strategy == "GREEDY":
            self._scan_pending_at(p)
        self.state.mark_cover_done(p)
        if self.strategy == "GREEDY":
            self.opportunistic_greedy()
        else:
            self.drain_pending()

    def choose_greedy_action(self):
        from q3_greedy_policy import greedy_action_candidates

        jobs = []
        certified = []
        here = pos_key(self.state.pos)
        remaining = list(self.state.R)
        for k in list(self.state.P):
            ch = self.state.channels[k]
            if ch.status == "cleared" or ch.first_site is None or ch.first_bearing is None:
                continue
            point = self.certified_clear_point(k)
            if point is not None:
                certified.append({"kind": "clear", "point": point, "k": k,
                                  "cost": dist(self.state.pos, point) + 25.0})
                continue
            if not remaining and k not in self.local_cover_attempted:
                from q3_safe import local_cover_route, snake_path_length
                route = local_cover_route(self.posterior_vertices(k), self.state.pos)
                if route:
                    certified.append({"kind": "local_clear", "points": route, "k": k,
                                      "cost": dist(self.state.pos, route[0])
                                      + snake_path_length(route) + 15.*len(route) + 10.})
                    continue
            if here in ch.tour_skip_pos:
                continue
            if ch.greedy_attempted and not remaining:
                continue
            jobs.append({"k": k, "first_site": ch.first_site, "first_bearing": float(ch.first_bearing)})
        action = greedy_action_candidates(self.state.pos, remaining, jobs)
        # Once discovery is complete, visit known clear points before speculative
        # localization or SAFE. During discovery compare with the next action.
        if certified:
            best = min(certified, key=lambda a: (a["cost"], a["k"]))
            if not remaining or action is None or best["cost"] <= action["cost"]:
                return best
        return action

    def posterior_vertices(self, k):
        """Conservative convex posterior from all observed direction wedges."""
        from localization import f1_outer_vertices, _wedge_clip
        fixes = self._direction_fixes(self.state.channels[k])
        if not fixes:
            return None
        verts = f1_outer_vertices(*fixes[0])
        for site, bearing in fixes[1:]:
            verts = _wedge_clip(verts, site, bearing)
            if len(verts) == 0:
                return None
        return verts

    def _execute_local_clear(self, action):
        k = action["k"]
        self.local_cover_attempted.add(k)
        self.state.phase = "active"
        self._note(op="local_cover_start", k=k, n_points=len(action["points"]))
        for point in action["points"]:
            if self.clear(float(point[0]), float(point[1]), k):
                return True
        self._note(op="local_cover_failed", k=k)
        return False

    def certified_clear_point(self, k):
        """Fuse every observed direction; retain far, guaranteed clear visits.

        A failed clear invalidates this point so unchanged evidence cannot create
        an endless retry. No hidden source position or radius is consulted.
        """
        from localization import f1_outer_vertices, _wedge_clip
        from geometry import min_enclosing_circle

        fixes = self._direction_fixes(self.state.channels[k])
        if len(fixes) < 2:
            return None
        verts = self.posterior_vertices(k)
        if verts is None or len(verts) == 0:
            return None
        point, rho = min_enclosing_circle(verts)
        if not np.isfinite(rho) or rho > 20.0:
            return None
        point = np.asarray(point, dtype=float)
        if not np.all(np.isfinite(point)):
            return None
        for event in self.log:
            if (event.get("op") == "clear" and event.get("k") == k
                    and not event.get("ok")
                    and dist(point, [event["x"], event["y"]]) < 1.0):
                return None
        return point

    def _execute_certified_clear(self, action):
        self.state.phase = "active"
        point = action["point"]
        self._note(op="certified_visit", k=action["k"],
                   distance=dist(self.state.pos, point))
        return self.clear(float(point[0]), float(point[1]), int(action["k"]))

    def _scan_pending_at(self, p) -> None:
        """Paper incremental scan: unclosed (detected) channels at this cover station."""
        p = np.asarray(p, dtype=float).reshape(2)
        key = pos_key(p)
        for k in list(self.state.P):
            ch = self.state.channels[k]
            if ch.status == "cleared":
                if k in self.state.P:
                    self.state.P.remove(k)
                continue
            if key in ch.measured_positions:
                continue
            if self.pending_clear_ready(k):
                self._note(op="pending_scan_skipped", k=k, reason="clear_ready")
                continue
            resp = self.measure(p[0], p[1], k, active=False)
            if resp.get("measure_result") == "near":
                self.clear(p[0], p[1], k)

    def _pending_specs(self):
        out = []
        for k in list(self.state.P):
            ch = self.state.channels[k]
            if ch.status == "cleared" or ch.first_site is None or ch.first_bearing is None:
                continue
            out.append((ch.first_site, float(ch.first_bearing)))
        return out

    def _direction_fixes(self, ch):
        fixes = []
        for h in ch.history:
            if h.get("result") == "direction" and h.get("svd") is not None and h.get("pos") is not None:
                fixes.append((np.asarray(h["pos"], dtype=float).reshape(2), float(h["svd"])))
        return fixes

    def _path_try_clears(self, a, b) -> None:
        from q3_greedy_policy import path_try_clear_points

        self.state.phase = "global"
        samples = None
        ks = []
        for k in list(self.state.P):
            ch = self.state.channels[k]
            if ch.status == "cleared" or ch.first_site is None or ch.first_bearing is None:
                continue
            pts = path_try_clear_points(a, b, ch.first_site, float(ch.first_bearing))
            if not pts:
                continue
            ks.append(k)
            if samples is None:
                samples = pts
        if not samples or not ks:
            return
        for p in samples:
            for k in ks:
                if self.state.channels[k].status == "cleared":
                    continue
                if self.heuristic_clear(float(p[0]), float(p[1]), k):
                    continue

    def opportunistic_greedy(self) -> None:
        """Stay on the seven-point tour: try-clear only at/near the current station."""
        from q3_greedy_policy import (
            bearing_flip_try_clear_points,
            clear_hop_allowed,
            try_clear_points_after_second,
            two_wedge_rho,
        )

        remaining = list(self.state.R)
        for k in list(self.state.P):
            ch = self.state.channels[k]
            if ch.status == "cleared":
                if k in self.state.P:
                    self.state.P.remove(k)
                continue
            if ch.first_site is None or ch.first_bearing is None:
                continue
            fixes = self._direction_fixes(ch)
            if len(fixes) < 2:
                continue
            s, a1 = fixes[0]
            s2, a2 = fixes[-1]
            pts = list(try_clear_points_after_second(s, a1, s2, a2))
            pts.extend(bearing_flip_try_clear_points(s, a1, s2, a2))
            rho = two_wedge_rho(s, a1, s2, a2)
            for p in pts:
                if self.state.channels[k].status == "cleared":
                    break
                if not clear_hop_allowed(self.state.pos, p, rho, remaining):
                    continue
                if self.heuristic_clear(float(p[0]), float(p[1]), k):
                    break
            ch.tour_skip_pos.add(pos_key(self.state.pos))

    def drain_pending(self) -> None:
        if self.strategy == "GREEDY":
            self._drain_greedy_nearest()
            return
        for k in list(self.state.P):
            if self.state.channels[k].status == "cleared":
                if k in self.state.P:
                    self.state.P.remove(k)
                continue
            if self.strategy == "SAFE":
                self.safe_channel(k)
            else:
                self.active_channel(k)
                if self.state.channels[k].status != "cleared":
                    self.safe_channel(k)

    def _drain_greedy_nearest(self) -> None:
        guard = 0
        while self.state.P and guard < 40:
            guard += 1
            self.state.P = [k for k in self.state.P if self.state.channels[k].status != "cleared"]
            if not self.state.P:
                return
            act = self.choose_greedy_action()
            if act is not None and act["kind"] == "local_clear":
                self._execute_local_clear(act)
                continue
            if act is not None and act["kind"] == "clear":
                self._execute_certified_clear(act)
                continue
            if act is not None and act["kind"] == "pending":
                k = int(act["k"])
                self.greedy_channel(k)
                ch = self.state.channels[k]
                ch.greedy_attempted = True
                ch.tour_skip_pos.add(pos_key(self.state.pos))
                continue
            leftovers = [k for k in self.state.P if self.state.channels[k].status != "cleared"]
            if not leftovers:
                return
            k = min(
                leftovers,
                key=lambda ck: dist(self.state.pos, self.state.channels[ck].first_site)
                if self.state.channels[ck].first_site is not None
                else 1e18,
            )
            if self.state.channels[k].status != "cleared":
                self.centerline_clear(k)
            if self.state.channels[k].status != "cleared":
                self.safe_channel(k)
            if self.state.channels[k].status != "cleared":
                if k in self.state.P:
                    self.state.P.remove(k)

    def _f1(self, ch):
        from localization import f1_outer_vertices

        if ch.first_site is None or ch.first_bearing is None:
            return None
        try:
            return f1_outer_vertices(ch.first_site, ch.first_bearing)
        except Exception:
            return None

    def safe_channel(self, k: int) -> None:
        ch = self.state.channels[k]
        if ch.status == "cleared" or ch.first_site is None:
            return
        if ch.safe_attempted:
            if k in self.state.P:
                self.state.P.remove(k)
            return
        ch.safe_attempted = True
        self.state.n_safe += 1
        self.state.phase = "safe"
        posterior = self.posterior_vertices(k)
        clipped, full = clipped_then_full(ch.first_site, ch.first_bearing,
                                         posterior if posterior is not None else self._f1(ch))
        max_step = 0.0
        prev = self.state.pos
        tried = set()

        def _walk(pts) -> bool:
            nonlocal max_step, prev
            for q in pts:
                key = pos_key(q)
                if key in tried:
                    continue
                tried.add(key)
                max_step = max(max_step, dist(prev, q))
                prev = q
                if self.clear(q[0], q[1], k):
                    return True
            return False

        if _walk(clipped):
            ch.history.append({"safe_max_step": max_step, "safe_move": ch.safe_move, "safe_fallback_full": False})
            return
        used_full = len(clipped) < len(full)
        if used_full:
            self.state.n_full_225 += 1
            _walk(full)
        ch.history.append({"safe_max_step": max_step, "safe_move": ch.safe_move, "safe_fallback_full": used_full})

    def greedy_channel(self, k: int) -> None:
        """Second measure (approach if far) then 1–2 try-clears even if rho is slightly above 20 m."""
        from q3_greedy_policy import (
            greedy_second_measure_points,
            is_good_second_site,
            try_clear_points_after_second,
        )

        from q3_greedy_policy import TOUR_BRANCH_M, first_bearing_try_clear_points

        ch = self.state.channels[k]
        if ch.first_site is None or ch.first_bearing is None:
            return
        if self.pending_clear_ready(k):
            return
        self.state.phase = "active"
        s = np.asarray(ch.first_site, dtype=float).reshape(2)
        a = float(ch.first_bearing)
        on_tour = bool(self.state.R)
        if (not on_tour) and dist(self.state.pos, s) < 80.0 and ch.extra_measures == 0:
            for p in first_bearing_try_clear_points(s, a):
                if self.heuristic_clear(float(p[0]), float(p[1]), k):
                    return
        s2 = None
        th2 = None
        fixes = self._direction_fixes(ch)
        if len(fixes) >= 2:
            s2, th2 = fixes[-1]
        if is_good_second_site(self.state.pos, s, a) and pos_key(self.state.pos) not in ch.measured_positions:
            resp = self.measure(float(self.state.pos[0]), float(self.state.pos[1]), k, active=True)
            y = resp.get("measure_result")
            if y == "near":
                self.clear(float(self.state.pos[0]), float(self.state.pos[1]), k)
                return
            if y == "direction":
                s2 = self.state.pos.copy()
                th2 = float(resp["svd_deg"])
        if s2 is None:
            for cand in greedy_second_measure_points(s, a, self.state.pos):
                if ch.extra_measures >= 6:
                    break
                if on_tour and dist(self.state.pos, cand) > TOUR_BRANCH_M:
                    continue
                if abs(float(cand[0])) > 2_000_000 or abs(float(cand[1])) > 2_000_000:
                    continue
                if pos_key(cand) in ch.measured_positions:
                    continue
                resp = self.measure(float(cand[0]), float(cand[1]), k, active=True)
                y = resp.get("measure_result")
                if y == "near":
                    self.clear(float(cand[0]), float(cand[1]), k)
                    return
                if y == "direction":
                    s2 = np.asarray(cand, dtype=float)
                    th2 = float(resp["svd_deg"])
                    break
        if s2 is None or th2 is None:
            return
        from q3_greedy_policy import clear_hop_allowed, two_wedge_rho

        tries = try_clear_points_after_second(s, a, s2, th2)
        rho = two_wedge_rho(s, a, s2, th2)
        remaining = list(self.state.R)
        for p in tries:
            if self.state.channels[k].status == "cleared":
                return
            if not clear_hop_allowed(self.state.pos, p, rho, remaining):
                continue
            if self.heuristic_clear(float(p[0]), float(p[1]), k):
                return

    def centerline_clear(self, k: int) -> None:
        from q3_greedy_policy import ray_try_clear_near

        ch = self.state.channels[k]
        if ch.status == "cleared" or ch.first_site is None:
            return
        self.state.phase = "safe"
        for p in ray_try_clear_near(ch.first_site, float(ch.first_bearing), self.state.pos):
            if self.heuristic_clear(float(p[0]), float(p[1]), k):
                return

    def _update_posterior(self, ch, q, y: str, svd) -> None:
        from geometry import min_enclosing_circle
        from localization import _wedge_clip, f1_outer_vertices
        from params import CLEAR_RADIUS

        if ch.f_verts is None and ch.first_site is not None:
            try:
                ch.f_verts = f1_outer_vertices(ch.first_site, ch.first_bearing)
            except Exception:
                ch.f_verts = None
        if y == "direction" and svd is not None and ch.f_verts is not None:
            try:
                ch.f_verts = _wedge_clip(ch.f_verts, q, float(svd))
            except Exception:
                pass
        if ch.f_verts is None or len(ch.f_verts) == 0:
            return None
        c, rho = min_enclosing_circle(ch.f_verts)
        return c, float(rho)

    def active_channel(self, k: int) -> None:
        from active import select_active
        from params import CLEAR_RADIUS

        ch = self.state.channels[k]
        if ch.first_site is None or ch.first_bearing is None:
            return
        self.state.phase = "active"
        t0 = self.state.virtual_time
        if not ch.measured_positions and ch.first_site is not None:
            ch.measured_positions.append(pos_key(ch.first_site))
        tried = set(ch.measured_positions)
        while ch.extra_measures < 6 and (self.state.virtual_time - t0) < 600:
            remaining = list(self.state.R)
            choice = select_active(
                self.strategy,
                ch.first_site,
                ch.first_bearing,
                robot_pos=self.state.pos,
                remaining_cover=remaining or None,
                n_azimuth=8,
                exclude_positions=tried,
                f_verts=ch.f_verts,
                receptions=ch.receptions or [ch.first_site],
            )
            if choice is None:
                break
            q = np.asarray(choice.q, dtype=float).reshape(2)
            key = pos_key(q)
            if key in tried:
                self.state.n_same_pos_repeat += 1
                tried.add(key)
                continue
            if remaining and min(dist(q, p) for p in remaining) < 1.0:
                self.state.n_reuse += 1
                self._scan_unseen_at(q)
                self.state.mark_cover_done(q)
                self.state.phase = "active"
            resp = self.measure(q[0], q[1], k, active=True)
            tried.add(key)
            y = resp.get("measure_result")
            if y == "near":
                self.clear(q[0], q[1], k)
                return
            if y in ("direction", "no_signal"):
                updated = self._update_posterior(ch, q, y, resp.get("svd_deg"))
                if y == "direction" and updated is not None:
                    c, rho = updated
                    if rho <= CLEAR_RADIUS + 1e-6:
                        self.clear(c[0], c[1], k)
                        return
                continue
            break

    def certify_leftovers(self) -> None:
        st = self.state
        if st.detected_count() >= 16:
            for ch in st.channels.values():
                if ch.status == "unseen":
                    ch.status = "certified_absent"
            st.R = []
            return
        if not st.R:
            for ch in st.channels.values():
                if ch.status == "unseen" and len(ch.V) >= 7:
                    ch.status = "certified_absent"

    def run(self) -> dict:
        _assert_no_oracle()
        enter = self.robot.enter()
        self.state.virtual_time = float(enter.get("virtual_time_s", 0.0))
        try:
            while not self.state.done_all_channels():
                self.certify_leftovers()
                if self.state.done_all_channels():
                    break
                if self.strategy == "GREEDY":
                    act = self.choose_greedy_action()
                    if act is None:
                        if self.state.P:
                            self.drain_pending()
                            continue
                        self.certify_leftovers()
                        if not self.state.R:
                            break
                        continue
                    if act["kind"] == "cover":
                        self.visit_cover(act["point"])
                    elif act["kind"] == "clear":
                        self._execute_certified_clear(act)
                    elif act["kind"] == "local_clear":
                        self._execute_local_clear(act)
                    else:
                        k = int(act["k"])
                        self.greedy_channel(k)
                        ch = self.state.channels[k]
                        ch.tour_skip_pos.add(pos_key(self.state.pos))
                        if not self.state.R:
                            ch.greedy_attempted = True
                    continue
                if self.state.P:
                    self.drain_pending()
                    continue
                if self.state.discovery_cancelled() and not self.state.P:
                    self.certify_leftovers()
                    break
                if not self.state.R:
                    self.certify_leftovers()
                    break
                if not self.state.R and not self.state.P:
                    self.certify_leftovers()
                    break
                nxt = shortest_next(self.state.pos, self.state.R)
                self.visit_cover(nxt)
            self.drain_pending()
            self.certify_leftovers()
        except TimeoutError as exc:
            self.state.failure = "budget_exhausted"
            self._note(op="timeout", err=str(exc))
        except Exception as exc:
            self.state.failure = f"error:{type(exc).__name__}"
            self._note(op="error", err=str(exc), tb=traceback.format_exc())
        finally:
            if getattr(self.robot, "entered", False):
                try:
                    self.robot.exit()
                except Exception as exc:
                    self._note(op="exit_failed", err=str(exc))
        wall = time.perf_counter() - self.t0
        K = self.state.cleared_count()
        T = self.state.virtual_time
        per_src = {}
        for ck, ch in self.state.channels.items():
            if not ch.ever_detected:
                continue
            loc_t = None
            if ch.t_first_detect is not None and ch.t_clear is not None:
                loc_t = ch.t_clear - ch.t_first_detect
            per_src[str(ck)] = {
                "status": ch.status,
                "first_detection_virtual_time": ch.t_first_detect,
                "clear_success_virtual_time": ch.t_clear,
                "localize_clear_time": loc_t,
                "active_positions": ch.active_positions,
                "safe_move_distance": ch.safe_move,
                "active_measure_count": ch.extra_measures,
                "safe_attempted": ch.safe_attempted,
            }
        return {
            "strategy": self.strategy,
            "failure": self.state.failure,
            "K": K,
            "T": T,
            "T_over_K": (T / K) if K else None,
            "wall_s": wall,
            "move_m": self.state.move_distance,
            "global_move_distance": self.state.global_move,
            "localization_move_distance": self.state.loc_move,
            "safe_move_distance": self.state.safe_move,
            "measure_time": self.state.measure_time,
            "clear_time": self.state.clear_time,
            "n_measure": self.state.n_measure,
            "n_clear": self.state.n_clear,
            "n_clear_ok": self.state.n_clear_ok,
            "n_safe": self.state.n_safe,
            "n_full_225": self.state.n_full_225,
            "n_reuse": self.state.n_reuse,
            "n_active_measure": self.state.n_active_measure,
            "same_position_repeat_count": self.state.n_same_pos_repeat,
            "detected": self.state.detected_count(),
            "R_left": len(self.state.R),
            "P_left": list(self.state.P),
            "all_certified": self.state.done_all_channels(),
            "channel_status": {str(ck): ch.status for ck, ch in self.state.channels.items()},
            "per_source": per_src,
        }

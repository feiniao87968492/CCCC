"""Isolated extensions of actual GREEDY_FAST, using observable history only."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "simulator_automation")]
from active import _nn_tour, _two_opt
from geometry import min_enclosing_circle
from q3_fast_mode import GreedyFastRunner
from q3_state import Q3State, dist, pos_key

VARIANTS = ("ORIGINAL", "COMPACT", "J", "S", "O", "JS", "JO", "SO", "JSO", "JSO_ALLSCAN")


def enable_exact_geometry_cache():
    """Memoize the unchanged public geometry function equally for all arms."""
    import localization
    if getattr(localization.f1_outer_vertices, "_ablation_cached", False):
        return
    original = localization.f1_outer_vertices

    @lru_cache(maxsize=16384)
    def cached(x, y, bearing, n):
        return original(np.array([x, y]), bearing, n)

    def wrapper(s, bearing_deg, n_tangents=48):
        return cached(float(s[0]), float(s[1]), float(bearing_deg), int(n_tangents)).copy()

    wrapper._ablation_cached = True
    localization.f1_outer_vertices = wrapper


def cover_points(radius=1130.):
    return np.array([[0., 0.]] + [[radius*np.cos(j*np.pi/3), radius*np.sin(j*np.pi/3)]
                                 for j in range(6)])


class CompactState(Q3State):
    def mark_cover_done(self, p):
        self.R = [q for q in self.R if dist(q, p) > 1e-6]


class AblationRunner(GreedyFastRunner):
    def __init__(self, robot, variant):
        super().__init__(robot, source_budget_s=0)
        self.variant = variant
        self.joint = "J" in variant
        self.selective = "S" in variant
        self.optimistic = "O" in variant and variant != "COMPACT"
        self.allscan = variant == "JSO_ALLSCAN"
        self.stations = cover_points()
        self.state = CompactState()
        self.state.R = [p.copy() for p in self.stations]
        self._posterior_cache = {}
        self._supplementing = False
        self.joint_jobs = 0

    def _station_index(self, p):
        ds = np.linalg.norm(self.stations-np.asarray(p), axis=1)
        idx = int(np.argmin(ds))
        return idx if ds[idx] < 1e-6 else None

    def measure(self, x, y, k, *, active=False):
        previous_v = set(self.state.channels[k].V)
        previous_status = self.state.channels[k].status
        response = super().measure(x, y, k, active=active)
        idx = self._station_index([x, y])
        ch = self.state.channels[k]
        if response.get("measure_result") == "no_signal" and not ch.ever_detected:
            ch.V = previous_v
            ch.status = previous_status
            if idx is not None:
                ch.V.add(idx)
            if len(ch.V) == 7:
                ch.status = "certified_absent"
        return response

    def posterior_vertices(self, k):
        ch = self.state.channels[k]
        key = len(ch.history)
        cached = self._posterior_cache.get(k)
        if cached is None or cached[0] != key:
            self._posterior_cache[k] = (key, super().posterior_vertices(k))
        return self._posterior_cache[k][1]

    def _estimate(self, k):
        fixes = self._direction_fixes(self.state.channels[k])
        if len(fixes) < 2:
            return None
        angles = np.deg2rad([a for _, a in fixes])
        normals = np.c_[-np.sin(angles), np.cos(angles)]
        if np.linalg.cond(normals) > 30:
            return None
        rhs = np.array([n @ site for n, (site, _) in zip(normals, fixes)])
        q = np.linalg.lstsq(normals, rhs, rcond=None)[0]
        return q if np.all(np.isfinite(q)) else None

    def _useful(self, p, k):
        ch = self.state.channels[k]
        if pos_key(p) in ch.measured_positions or ch.status != "detected":
            return False
        v = self.posterior_vertices(k)
        if v is None:
            return True
        c, rho = min_enclosing_circle(v)
        if rho <= (80 if self.optimistic else 40) and self._estimate(k) is not None:
            return False
        dv = np.linalg.norm(v-p, axis=1)
        if float(np.min(dv)) > 1500 or dist(p, c) > 1100:
            return False
        fixes = self._direction_fixes(ch)
        if not fixes:
            return True
        ray = c-p
        improvements = []
        for site, _ in fixes:
            a = c-site
            denom = np.linalg.norm(a)*np.linalg.norm(ray)
            cross = abs(float(a[0]*ray[1] - a[1]*ray[0]))
            improvements.append(cross / max(denom, 1e-9))
        return max(improvements) >= np.sin(np.deg2rad(12)) or dist(p, c) < .5*dist(fixes[-1][0], c)

    def _scan_pending_at(self, p):
        if not self.selective:
            return super()._scan_pending_at(p)
        for k in list(self.state.P):
            if self._useful(p, k):
                resp = self.measure(*p, k)
                if resp.get("measure_result") == "near":
                    self.clear(*p, k)

    def _supplement(self):
        if self._supplementing:
            return
        self._supplementing = True
        try:
            p = self.state.pos.copy()
            if self.allscan:
                for k in list(self.state.unseen_to_scan()):
                    if pos_key(p) in self.state.channels[k].measured_positions:
                        continue
                    resp = self.measure(*p, k)
                    if resp.get("measure_result") == "near":
                        self.clear(*p, k)
            if self.selective:
                self._scan_pending_at(p)
        finally:
            self._supplementing = False

    def clear(self, x, y, k):
        ok = super().clear(x, y, k)
        self._supplement()
        return ok

    def _viewpoint(self, k):
        ch = self.state.channels[k]
        v = self.posterior_vertices(k)
        if v is None:
            return None
        c, _ = min_enclosing_circle(v)
        candidates = [c + r*np.array([np.cos(a), np.sin(a)])
                      for r in (100., 200.) for a in np.linspace(0, 2*np.pi, 8, endpoint=False)]
        candidates = [q for q in candidates
                      if pos_key(q) not in ch.measured_positions and
                      np.max(np.linalg.norm(v-q, axis=1)) <= 1000]
        if not candidates:
            return None
        first, a = self._direction_fixes(ch)[0]
        u = np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))])
        def cost(q):
            offset = q-first
            perp = abs(float(offset[0]*u[1]-offset[1]*u[0]))
            return dist(self.state.pos, q) + 2000/max(perp, 10)
        return min(candidates, key=cost)

    def _resolve(self, k):
        if not self.optimistic:
            return super()._resolve(k)
        self.state.phase = "active"
        tried = []
        for _ in range(4):
            if self.state.channels[k].status == "cleared":
                return
            point = self.certified_clear_point(k)
            if point is not None and self.clear(*point, k):
                return
            v = self.posterior_vertices(k)
            if v is None:
                break
            _, rho = min_enclosing_circle(v)
            q = self._estimate(k)
            if q is not None and rho <= 80 and not any(dist(q, p) < 1 for p in tried):
                tried.append(q)
                self._note(op="optimistic_clear", k=k, rho=float(rho))
                if self.heuristic_clear(*q, k):
                    return
            q = self._viewpoint(k)
            if q is None:
                break
            resp = self.measure(*q, k, active=True)
            if resp.get("measure_result") == "near" and self.clear(*q, k):
                return
            self._supplement()
        self.safe_channel(k)

    def choose_greedy_action(self):
        if not self.joint:
            return super().choose_greedy_action()
        tasks = [("cover", p, None) for p in self.state.R]
        for k in self.state.P:
            ch = self.state.channels[k]
            if ch.status == "cleared" or k in self.fast_processed or ch.first_site is None:
                continue
            v = self.posterior_vertices(k)
            if v is not None:
                c, _ = min_enclosing_circle(v)
                tasks.append(("source", c, k))
        if not tasks:
            return None
        points = [t[1] for t in tasks]
        route = _two_opt(self.state.pos, _nn_tour(self.state.pos, points))
        idx = min(range(len(tasks)), key=lambda i: dist(tasks[i][1], route[0]))
        kind, p, k = tasks[idx]
        if kind == "cover":
            return {"kind": "cover", "point": p}
        return {"kind": "local_clear", "k": k}

    def _execute_local_clear(self, action):
        k = action["k"]
        if self.joint and len(self._direction_fixes(self.state.channels[k])) < 2:
            q = self._viewpoint(k)
            if q is not None:
                self.state.phase = "active"
                resp = self.measure(*q, k, active=True)
                if resp.get("measure_result") == "near":
                    self.clear(*q, k)
                self._supplement()
        self.joint_jobs += 1
        if self.state.channels[k].status != "cleared":
            self._process_source(k)

    def run(self):
        result = super().run()
        result["variant"] = self.variant
        result["joint_jobs"] = self.joint_jobs
        return result


def make_runner(robot, variant):
    if variant not in VARIANTS:
        raise ValueError(variant)
    enable_exact_geometry_cache()
    if variant == "ORIGINAL":
        return GreedyFastRunner(robot, source_budget_s=0)
    return AblationRunner(robot, variant)

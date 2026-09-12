"""Experimental Q3 practice policy; optional explicit loss of completeness."""
import math
import numpy as np
from q3_runner import Q3Runner
from q3_state import dist
from q3_safe import local_cover_route, snake_path_length
from geometry import min_enclosing_circle


class SourceBudgetExceeded(Exception):
    pass


class GreedyFastRunner(Q3Runner):
    def __init__(self, robot, source_budget_s=0):
        super().__init__(robot, 'GREEDY')
        if not math.isfinite(source_budget_s) or source_budget_s < 0:
            raise ValueError('source budget must be finite and nonnegative')
        self.source_budget_s = float(source_budget_s)
        self.source_start = None
        self.abandoned = []
        self.fast_processed = set()

    def _check_cost(self, x, y, fixed):
        if self.source_start is not None and self.source_budget_s:
            projected = self.state.virtual_time - self.source_start + dist(self.state.pos, [x, y])/5 + fixed
            if projected > self.source_budget_s:
                raise SourceBudgetExceeded()

    def clear(self, x, y, k):
        self._check_cost(x, y, 5.)
        return super().clear(x, y, k)

    def measure(self, x, y, k, *, active=False):
        self._check_cost(x, y, 5. + int(self.state.measure_channel != k))
        return super().measure(x, y, k, active=active)

    def pending_clear_ready(self, k):
        # Only guaranteed single-point clearance suppresses a free station scan.
        return self.certified_clear_point(k) is not None

    def choose_greedy_action(self):
        if not self.state.R:
            return None  # Tail is handled by the explicit bounded resolver below.
        return super().choose_greedy_action()

    def _execute_local_clear(self, action):
        return self._process_source(action['k'])

    def greedy_channel(self, k):
        if not self.state.R:
            return self._process_source(k)
        # During discovery only collect a useful observation, without trial rays.
        from q3_greedy_policy import is_good_second_site
        ch = self.state.channels[k]
        from q3_state import pos_key
        if (ch.first_site is not None and not self.pending_clear_ready(k)
                and pos_key(self.state.pos) not in ch.measured_positions
                and is_good_second_site(self.state.pos, ch.first_site, ch.first_bearing)):
            q = self.state.pos.copy()
            resp = self.measure(*q, k, active=True)
            if resp.get('measure_result') == 'near':
                self.clear(*q, k)

    def opportunistic_greedy(self):
        # Preserve coverage-tour progress; tail resolver owns speculative clears.
        pass

    def _center(self, k):
        v = self.posterior_vertices(k)
        if v is None:
            return self.state.channels[k].first_site
        return np.asarray(min_enclosing_circle(v)[0])

    def _trial_points(self, k):
        fixes = self._direction_fixes(self.state.channels[k])
        v = self.posterior_vertices(k)
        if v is None:
            return []
        center = np.asarray(min_enclosing_circle(v)[0])
        points = []
        if len(fixes) >= 2:
            normals = np.array([[-np.sin(np.deg2rad(a)), np.cos(np.deg2rad(a))] for _, a in fixes])
            rhs = np.array([np.dot(n, s) for n, (s, _) in zip(normals, fixes)])
            if np.linalg.matrix_rank(normals) == 2:
                points.append(np.linalg.lstsq(normals, rhs, rcond=None)[0])
        points.append(center)
        points.extend(local_cover_route(v, self.state.pos))
        unique = []
        for q in points:
            if np.all(np.isfinite(q)) and not any(dist(q, p) < 1. for p in unique):
                unique.append(q)
        return unique

    def _resolve(self, k):
        self.state.phase = 'active'
        point = self.certified_clear_point(k)
        if point is not None and self.clear(*point, k):
            return
        tried = []
        # At most three speculative API clears per round, then compare sensing
        # against bounded local coverage. Two rounds keep this policy finite.
        for round_index in range(2):
            sent = 0
            for q in self._trial_points(k):
                if any(dist(q, p) < 1. for p in tried):
                    continue
                tried.append(q)
                before = self.state.n_clear
                if self.heuristic_clear(*q, k):
                    return
                sent += self.state.n_clear - before
                if sent >= 3:
                    break
            if round_index == 1:
                break
            v = self.posterior_vertices(k)
            if v is None:
                break
            center, rho = min_enclosing_circle(v)
            route = local_cover_route(v, self.state.pos)
            cover_cost = ((dist(self.state.pos, route[0])+snake_path_length(route))/5
                          +3*len(route)+2) if route else float('inf')
            # Nearby side views, bounded by the conservative 1000 m reception
            # radius for every vertex of the current outer polygon.
            candidates = [np.asarray(center)+150*np.array([np.cos(a), np.sin(a)])
                          for a in np.linspace(0, 2*np.pi, 8, endpoint=False)]
            from q3_state import pos_key
            candidates = [q for q in candidates if max(dist(q, p) for p in v) <= 1000
                          and pos_key(q) not in self.state.channels[k].measured_positions]
            if not candidates:
                break
            q = min(candidates, key=lambda q: dist(self.state.pos, q))
            sensing_cost = dist(self.state.pos, q)/5+6+dist(q, center)/5+5
            if sensing_cost >= cover_cost:
                break
            self._note(op='fast_refine', k=k, estimated_cost=sensing_cost, cover_cost=cover_cost if route else None)
            resp = self.measure(*q, k, active=True)
            if resp.get('measure_result') == 'near' and self.clear(*q, k):
                return
            point = self.certified_clear_point(k)
            if point is not None and self.clear(*point, k):
                return
        # Full-completion mode retains fallback; budget mode checks every action.
        self.safe_channel(k)

    def _process_source(self, k):
        if k in self.fast_processed:
            return
        self.fast_processed.add(k)
        self.source_start = self.state.virtual_time
        try:
            self._resolve(k)
        except SourceBudgetExceeded:
            self.abandoned.append(k)
            self._note(op='source_budget_stop', k=k, budget_s=self.source_budget_s,
                       spent_s=self.state.virtual_time-self.source_start)
        finally:
            self.source_start = None
        if k in self.state.P:
            self.state.P.remove(k)

    def drain_pending(self):
        if self.state.R:
            return
        while self.state.P:
            k = min(self.state.P, key=lambda k: dist(self.state.pos, self._center(k)))
            self._process_source(k)
            if k in self.state.P:
                self.state.P.remove(k)

    def run(self):
        result = super().run()
        result.update(strategy='GREEDY_FAST', source_budget_s=self.source_budget_s,
                      abandoned_channels=self.abandoned,
                      uncleared_detected_channels=[k for k, ch in self.state.channels.items()
                                                   if ch.ever_detected and ch.status != 'cleared'],
                      experimental_incomplete_allowed=bool(self.source_budget_s))
        return result

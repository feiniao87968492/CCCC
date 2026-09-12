"""Isolated Q4 policy ablations; frozen source modules are never edited."""
from contextlib import contextmanager
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'simulator_automation')]
import q4_cover
from q4_certificate import discovery_certificate
from q4_policy import ROUTE_ADAPTIVE_V4, pending_batch_order, set_route_mode
from q4_runner import MAX_MEASURE, Q4Runner


@dataclass(frozen=True)
class Config:
    name: str
    route: str = 'tour'
    reuse: bool = False
    clear_rho: float = 80.
    probe: str = 'baseline'
    outer_radius: float = 1950.
    every_stop: bool = False


VARIANTS = {
    'baseline': Config('baseline'),
    'nearest': Config('nearest', route='nearest'),
    'reuse': Config('reuse', reuse=True),
    'early160': Config('early160', clear_rho=160),
    'nearest_reuse': Config('nearest_reuse', route='nearest', reuse=True),
    'nearest_early': Config('nearest_early', route='nearest', clear_rho=160),
    'reuse_early': Config('reuse_early', reuse=True, clear_rho=160),
    'full': Config('full', route='nearest', reuse=True, clear_rho=160),
    'probe_off': Config('probe_off', probe='off'),
    'probe_strict': Config('probe_strict', probe='strict'),
    'probe_loose': Config('probe_loose', probe='loose'),
    'early120': Config('early120', clear_rho=120),
    'early220': Config('early220', clear_rho=220),
    'center_route': Config('center_route', route='center'),
    'finish_source': Config('finish_source', route='finish'),
    'compact': Config('compact', outer_radius=1900),
    'full_compact': Config('full_compact', route='nearest', reuse=True,
                           clear_rho=160, outer_radius=1900),
    'every_stop': Config('every_stop', route='nearest', reuse=True,
                         clear_rho=160, every_stop=True),
    'proxy_compact': Config('proxy_compact', route='center', outer_radius=1900),
    'proxy_reuse_early_compact': Config('proxy_reuse_early_compact', route='center',
                                       reuse=True, clear_rho=160, outer_radius=1900),
}


@lru_cache(maxsize=8)
def _cover_model(radius):
    original = q4_cover._MODELS['TRI25']
    points = original.points.copy()
    points[19:] *= radius / 1950.
    certificate = discovery_certificate(points)
    if not certificate['valid']:
        raise ValueError(f'uncertified discovery geometry: {certificate}')
    model = replace(original, points=points, key_to_idx=q4_cover._index_map(points),
                    dist=np.linalg.norm(points[:, None] - points[None, :], axis=2))
    return model, certificate


@contextmanager
def cover_context(radius=1950.):
    old_mode = q4_cover.current_cover_mode()
    original = q4_cover._MODELS['TRI25']
    original_alias = q4_cover._TRI25
    model, certificate = _cover_model(float(radius))
    try:
        q4_cover._MODELS['TRI25'] = q4_cover._TRI25 = model
        q4_cover.set_cover_mode('TRI25')
        yield certificate
    finally:
        q4_cover._MODELS['TRI25'] = original
        q4_cover._TRI25 = original_alias
        q4_cover.set_cover_mode(old_mode)


def make_runner(robot, config):
    set_route_mode(ROUTE_ADAPTIVE_V4)
    return Q4Runner(robot) if config.name == 'baseline' else AblationRunner(robot, config)


class AblationRunner(Q4Runner):
    def __init__(self, robot, config):
        super().__init__(robot)
        self.config = config
        self._focus = None

    def _adaptive_task(self, k):
        if self.config.clear_rho == 80:
            point, kind = super()._adaptive_task(k)
        else:
            region = self._region(k)
            if region is None:
                raise RuntimeError(f'channel {k}: empty positive region')
            point, rho = region['center'], float(region['rho'])
            tried = any(np.linalg.norm(point-p) < 1e-7 for p in self.failed_clear_points[k])
            if rho <= 20-1e-6 and not tried:
                kind = 'cert_clear'
            elif rho <= self.config.clear_rho and len(self.failed_clear_points[k]) < 2 and not tried:
                kind = 'aggr_clear'
            elif self.state.channels[k].extra_measures < MAX_MEASURE:
                points = self._refinement_points(k, region)
                point, kind = (points[0], 'measure') if points else (point, 'optical')
            else:
                kind = 'optical'
        if self.config.reuse and kind == 'measure':
            shared = self._shared_cover(k, point)
            if shared is not None:
                return shared, 'reuse'
        return point, kind

    def _shared_cover(self, k, dedicated):
        ch = self.state.channels[k]
        belief = self._reception_belief(k)
        direct_distance = np.linalg.norm(dedicated-self.state.pos)
        required_gain = max(.3, .65*belief.expected_gain(dedicated))
        candidates = []
        for i in sorted(self._cover_need()-self.cover_visited):
            p = q4_cover.cover_points()[i]
            distance = np.linalg.norm(p-self.state.pos)
            if distance > direct_distance+180 or any(np.linalg.norm(p-h['pos']) <= 1 for h in ch.history):
                continue
            if belief.reception_probability(p) < .7:
                continue
            gain = belief.expected_gain(p)
            if gain >= required_gain:
                candidates.append((float(distance), i, gain, p))
        if not candidates:
            return None
        distance, i, gain, p = min(candidates, key=lambda c: (c[0], c[1]))
        self._note(op='reuse_candidate', k=k, cover=i, gain=gain,
                   distance=distance, t=self.virtual_time)
        return p

    def _probe_detected_at_v4(self, p):
        if self.config.probe == 'baseline':
            return super()._probe_detected_at_v4(p)
        if self.config.probe == 'off':
            return
        probability, gain = (.85, .5) if self.config.probe == 'strict' else (.55, .2)
        for k in list(self.state.pending_detected()):
            ch = self.state.channels[k]
            if any(np.linalg.norm(p-h['pos']) <= 1 for h in ch.history):
                continue
            region = self._region(k)
            if region is None or region['rho'] <= 40:
                continue
            belief = self._reception_belief(k)
            if belief.reception_probability(p) < probability or belief.expected_gain(p) < gain:
                continue
            self.n_probe += 1
            if self.measure(*p, k).get('measure_result') == 'near':
                self._try_clear_at(k, p)

    def _select(self, tasks, kinds):
        if self.config.route == 'nearest':
            return min(tasks, key=lambda t: (np.linalg.norm(t[1]-self.state.pos), t[0]))[0]
        if self.config.route == 'center':
            proxies = [(ident, self._region(ident[1])['center'] if ident[0]=='source' else p)
                       for ident, p in tasks]
            return pending_batch_order(self.state.pos, proxies)[0]
        if self.config.route == 'finish':
            source_tasks = [t for t in tasks if t[0][0] == 'source']
            if source_tasks:
                if ('source', self._focus) in kinds:
                    return ('source', self._focus)
                ident = min(source_tasks, key=lambda t: (np.linalg.norm(t[1]-self.state.pos), t[0]))[0]
                self._focus = ident[1]
                return ident
        return pending_batch_order(self.state.pos, tasks)[0]

    def _run_adaptive_v4(self):
        self.scan_at(np.zeros(2))
        for _ in range(800):
            if self.done():
                return
            self._note_pending()
            started = time.perf_counter()
            need = self._cover_need()-self.cover_visited
            tasks = [(('cover', i), q4_cover.cover_points()[i])
                     for i in q4_cover.cover_route() if i in need]
            kinds = {}
            for k in self.state.pending_detected():
                point, kind = self._adaptive_task(k)
                ident = ('source', k)
                tasks.append((ident, point))
                kinds[ident] = kind
            if not tasks:
                self.failure = 'pending_unresolved'
                return
            ident = self._select(tasks, kinds)
            p = dict(tasks)[ident]
            self.n_replan += 1
            self.planner_wall_s += time.perf_counter()-started
            if ident[0] == 'cover':
                self.scan_at(p)
                self._probe_detected_at_v4(p)
                continue
            k, kind = ident[1], kinds[ident]
            self.n_insert += 1
            self._note(op='ablation_action', k=k, kind=kind, t=self.virtual_time)
            self._loc_leg = True
            try:
                if kind == 'optical':
                    self._optical_fallback(k, self._region(k))
                elif kind == 'reuse':
                    self.scan_at(p)
                    if self.state.channels[k].status == 'detected':
                        self._do_v3_action(k, p, 'measure')
                    self._probe_detected_at_v4(p)
                else:
                    self._do_v3_action(k, p, kind)
                if self.config.every_stop:
                    self.scan_at(self.state.pos.copy())
            finally:
                self._loc_leg = False
        if not self.done():
            self.failure = 'iteration_limit'

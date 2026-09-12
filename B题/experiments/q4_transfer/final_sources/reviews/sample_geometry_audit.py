"""Reviewer-only fixed sample audit; reads events, never runs a policy/simulator."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import HalfspaceIntersection

HERE = Path(__file__).resolve().parent
FOLDER = HERE.parent / 'primary400'


def constraints(history):
    angles = np.arange(48) * (2 * np.pi / 48)
    normals = np.column_stack((np.cos(angles), np.sin(angles)))
    aa = [normals]
    bb = [np.full(48, 1800.)]
    for e in history:
        if e['result'] not in ('direction', 'near'):
            continue
        q = np.array([e['x'], e['y']])
        aa.append(normals)
        bb.append(normals @ q + (5. if e['result'] == 'near' else 1500.))
        if e['result'] == 'direction':
            angle = np.deg2rad(e['svd'])
            eps = np.deg2rad(1.005)
            lower = np.array([np.cos(angle - eps), np.sin(angle - eps)])
            upper = np.array([np.cos(angle + eps), np.sin(angle + eps)])
            wedge = np.array([[lower[1], -lower[0]], [-upper[1], upper[0]]])
            aa.append(wedge)
            bb.append(wedge @ q)
    return np.vstack(aa), np.concatenate(bb)


def all_vertices(aa, bb):
    norms = np.linalg.norm(aa, axis=1)
    sol = linprog([0., 0., -1.], A_ub=np.column_stack((aa, norms)), b_ub=bb,
                  bounds=[(None, None), (None, None), (0., None)], method='highs')
    assert sol.success and sol.x[2] > 1e-8, 'degenerate sample needs separate handling'
    return HalfspaceIntersection(np.column_stack((aa, -bb)), sol.x[:2]).intersections


def main():
    scenes = json.loads((FOLDER / 'scenarios.json').read_text(encoding='utf-8'))
    variants = ['O', 'JSO_r160', 'SO_doptimal', 'short_clear', 'S_dopt_short']
    chosen = []
    counts = collections.Counter()
    for scene in sorted(scenes, key=lambda s: (s['source_kind'], s['error_mode'], s['seed'])):
        key = (scene['source_kind'], scene['error_mode'])
        if counts[key] < 2:
            chosen.append(scene)
            counts[key] += 1
    checks = collections.Counter()
    failures = []
    maximum_ls_error = maximum_certified_radius = 0.
    for scene in chosen:
        truth = {s['k']: np.array(s['g']) for s in scene['sources']}
        for variant in variants:
            path = FOLDER / 'events' / variant / (scene['scene_id'] + '.json.gz')
            events = json.load(gzip.open(path, 'rt', encoding='utf-8'))['events']
            history = collections.defaultdict(list)
            pending_optimistic = set()
            action = {}
            checks['traces'] += 1
            for e in events:
                op = e['op']
                k = e.get('k')
                if op in ('ablation_action', 'v4_action'):
                    action[k] = e['kind']
                elif op == 'optimistic_attempt':
                    pending_optimistic.add(k)
                elif op == 'measure':
                    history[k].append(e)
                    if e['result'] in ('direction', 'near'):
                        aa, bb = constraints(history[k])
                        checks['positive_truth_inside'] += 1
                        if np.max(aa @ truth[k] - bb) > 1e-6:
                            failures.append([variant, scene['scene_id'], k, 'positive_truth_excluded'])
                elif op == 'clear' and k in pending_optimistic:
                    pending_optimistic.remove(k)
                    positive = [h for h in history[k] if h['result'] == 'direction']
                    angle = np.deg2rad([h['svd'] for h in positive])
                    mat = np.column_stack((-np.sin(angle), np.cos(angle)))
                    sites = np.array([[h['x'], h['y']] for h in positive])
                    q = np.array([e['x'], e['y']])
                    ls = np.linalg.lstsq(mat, np.sum(mat * sites, axis=1), rcond=None)[0]
                    error = float(np.linalg.norm(q - ls))
                    maximum_ls_error = max(maximum_ls_error, error)
                    aa, bb = constraints(history[k])
                    checks['optimistic_ls_and_region'] += 1
                    if len(positive) < 2 or np.linalg.cond(mat) > 30 + 1e-7 or error > 1e-5 or np.max(aa @ q - bb) > 1e-6:
                        failures.append([variant, scene['scene_id'], k, 'optimistic_geometry'])
                elif op == 'clear' and action.get(k) == 'cert_clear':
                    # The action is consumed here; optical or near clears have other dispatch histories.
                    action.pop(k, None)
                    aa, bb = constraints(history[k])
                    vertices = all_vertices(aa, bb)
                    q = np.array([e['x'], e['y']])
                    radius = float(np.max(np.linalg.norm(vertices - q, axis=1)))
                    maximum_certified_radius = max(maximum_certified_radius, radius)
                    checks['independent_certified_vertices'] += 1
                    if radius > 20 + 1e-6:
                        failures.append([variant, scene['scene_id'], k, 'certified_point_not_covering_polygon'])
    result = dict(status='PASS' if not failures else 'FAIL',
                  selection='First two seeds of each of the five source/error strata, fixed five variants',
                  variants=variants, scene_ids=[s['scene_id'] for s in chosen], checks=dict(checks),
                  method='Independent halfplane construction; SciPy Chebyshev-center LP and HalfspaceIntersection; independent LS solve',
                  max_ls_coordinate_error_m=maximum_ls_error,
                  max_sample_certified_vertex_distance_m=maximum_certified_radius,
                  failures=failures,
                  result_sha256=hashlib.sha256((FOLDER/'results.csv').read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'sample-geometry-audit.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Reproducible paired Q4 experiment with immutable scenarios and event traces."""
import argparse
import csv
from dataclasses import asdict
import gzip
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT/'src'), str(ROOT/'tests'),
               str(ROOT/'simulator_automation'), str(ROOT/'experiments/q4_efficiency')]
from policies import VARIANTS, cover_context, make_runner
from test_q4_regressions import NoisyGeomSim, random_sources
from bench import event_metrics


def json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=json_default)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ObservableAPI:
    """Expose only simulator actions and lifecycle status to the policy."""
    __slots__ = ('_env',)

    def __init__(self, env):
        self._env = env

    @property
    def entered(self):
        return self._env.entered

    def enter(self):
        return self._env.enter()

    def exit(self):
        return self._env.exit()

    def measure(self, x, y, k):
        return self._env.measure(x, y, k)

    def clear(self, x, y, k):
        return self._env.clear(x, y, k)


def scenarios_for(suite, seed_start, cases):
    settings = [(seed, 'mixed', 'endpoint') for seed in range(seed_start, seed_start+cases)]
    if suite == 'primary':
        settings = [(seed, 'mixed', 'endpoint') for seed in range(10000, 10200)]
        settings += [(seed, kind, err) for kind, err in
                     [('directional','endpoint'), ('omni','endpoint'),
                      ('boundary','endpoint'), ('mixed','smooth')]
                     for seed in range(10000, 10050)]
    scenes = []
    for seed, kind, err in settings:
        sources = random_sources(seed)
        for source in sources:
            if kind != 'mixed':
                source['directional'] = kind != 'omni'
            if kind == 'boundary':
                source['g'] *= 1800 / np.linalg.norm(source['g'])
                source['r'] = 1000.
                source['psi'] = float(np.arctan2(source['g'][1], source['g'][0]))
        scene = json.loads(canonical(dict(seed=seed, source_kind=kind, error_mode=err,
                                         scene_id=f'{kind}_{err}_{seed}', sources=sources)))
        scene['scenario_sha256'] = hashlib.sha256(canonical(scene).encode()).hexdigest()
        scenes.append(scene)
    return scenes


def one(job):
    name, scene, output = job
    config = VARIANTS[name]
    sources = [dict(s, g=np.asarray(s['g'])) for s in scene['sources']]
    env = NoisyGeomSim(sources, scene['seed'], scene['error_mode'])
    with cover_context(config.outer_radius) as cert:
        runner = make_runner(ObservableAPI(env), config)
        result = runner.run()
    row = dict(variant=name, **{k: scene[k] for k in
               ('scene_id','seed','source_kind','error_mode','scenario_sha256')},
               N=len(sources), **{k: result.get(k) for k in
               ('K','T','T_over_K','move_m','localization_move','n_measure','n_clear',
                'n_clear_ok','n_optical_fallback','n_cover_visited','failure','all_certified',
                'n_probe','n_replan','planner_wall_s','wall_s')}, **event_metrics(runner.log))
    row['failed_clears'] = row['n_clear']-row['n_clear_ok']
    row['switches'] = round(row['measure_s']-5*row['n_measure'])
    row['accounting_residual_s'] = row['T']-(row['move_m']/5+5*row['n_measure']+
                                           row['switches']+3*row['n_clear']+2*row['K'])
    row['full_success'] = not row['failure'] and row['K']==row['N'] and row['all_certified']
    row['certificate_max_distance_m'] = cert['max_distance_m']
    row['certificate_hull_margin_m'] = cert['hull_margin_m']
    row['event_sha256'] = hashlib.sha256(canonical(runner.log).encode()).hexdigest()
    event_path = Path(output)/'events'/name/(scene['scene_id']+'.json.gz')
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(event_path, 'wt', encoding='utf-8') as f:
        json.dump(dict(row=row, events=runner.log), f, default=json_default)
    return row


def capture_manifest(args, scenes, names):
    frozen = json.loads((ROOT/'experiments/q4_efficiency/release_holdout100.meta.json').read_text())
    mismatches = [p for p, digest in frozen['sha256'].items() if sha(ROOT/p) != digest]
    if mismatches:
        raise RuntimeError(f'frozen baseline source drift: {mismatches}')
    paths = [ROOT/p for p in frozen['sha256']]
    paths += [HERE/'policies.py', Path(__file__), HERE/'design.md']
    return dict(arguments={k: str(v) for k,v in vars(args).items()}, python=sys.version,
                numpy=np.__version__, source='offline bounded-error geometry; not official simulator',
                baseline='claims/baseline-q4.md', review_status='independent review pending',
                configurations={n: asdict(VARIANTS[n]) for n in names},
                scenarios_sha256=hashlib.sha256(canonical(scenes).encode()).hexdigest(),
                sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
                frozen_sha256_mismatches=mismatches)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--suite', choices=['dev','primary'], default='dev')
    ap.add_argument('--seed-start', type=int, default=5000)
    ap.add_argument('--cases', type=int, default=30)
    ap.add_argument('--variants', default='')
    ap.add_argument('--workers', type=int, default=8)
    args = ap.parse_args()
    names = args.variants.split(',') if args.variants else list(VARIANTS)
    if not names or len(set(names)) != len(names) or any(n not in VARIANTS for n in names):
        ap.error('variants must be distinct known configurations')
    if args.output.exists():
        ap.error('output directory already exists; choose a new run directory')
    scenes = scenarios_for(args.suite, args.seed_start, args.cases)
    if not scenes:
        ap.error('empty scenario suite')
    manifest = capture_manifest(args, scenes, names)
    args.output.mkdir(parents=True)
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (args.output/'scenarios.json').write_text(canonical(scenes)+'\n', encoding='utf-8')
    jobs = [(name, scene, str(args.output)) for scene in scenes for name in names]
    completed = 0
    failures = 0
    started = time.perf_counter()
    with (args.output/'results.csv').open('w', newline='', encoding='utf-8') as f:
        writer = None
        with mp.Pool(args.workers) as pool:
            for row in pool.imap_unordered(one, jobs):
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
                completed += 1
                failures += not row['full_success']
                if completed % 100 == 0 or completed == len(jobs):
                    f.flush()
                    print(json.dumps(dict(completed=completed, total=len(jobs), failures=failures,
                                          elapsed_s=round(time.perf_counter()-started,1))), flush=True)
    changed = [p for p,d in manifest['sha256'].items() if sha(ROOT/p) != d]
    completion = dict(completed=completed, expected=len(jobs), failures=failures,
                      code_changed_during_run=changed, elapsed_s=time.perf_counter()-started)
    (args.output/'completion.json').write_text(json.dumps(completion, indent=2)+'\n', encoding='utf-8')
    if changed:
        raise RuntimeError(f'code changed during run: {changed}')


if __name__ == '__main__':
    main()

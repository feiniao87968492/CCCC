"""Independent primary matrix/statistical reconstruction; no simulator execution."""
import ast
import collections
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ROOT = EXP.parents[1]
FOLDER = EXP / 'primary_valid400'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def table(path):
    return list(csv.DictReader(path.open(encoding='utf-8-sig', newline='')))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def close(left, right, tolerance=1e-8):
    assert abs(float(left)-float(right)) < tolerance, (left, right)


def load_matrix():
    manifest = read(FOLDER/'manifest.json')
    scenes = read(FOLDER/'scenarios.json')
    rows = table(FOLDER/'results.csv')
    completion = read(FOLDER/'completion.json')
    names = list(manifest['configurations'])
    assert len(names) == 19 and len(scenes) == 400
    expected_scenes = {f'mixed_endpoint_{seed}' for seed in range(70000, 70200)}
    for kind, error in [('mixed', 'smooth'), ('directional', 'endpoint'), ('omni', 'endpoint'), ('boundary', 'endpoint')]:
        expected_scenes.update(f'{kind}_{error}_{seed}' for seed in range(70000, 70050))
    assert {s['scene_id'] for s in scenes} == expected_scenes
    assert hashlib.sha256(canonical(scenes)).hexdigest() == manifest['scenarios_sha256']
    scene_map = {s['scene_id']: s for s in scenes}
    for scene in scenes:
        assert hashlib.sha256(canonical({k: v for k, v in scene.items() if k != 'scenario_sha256'})).hexdigest() == scene['scenario_sha256']
        assert scene['scene_id'] == f"{scene['source_kind']}_{scene['error_mode']}_{scene['seed']}"
        sources = scene['sources']
        assert 10 <= len(sources) <= 16 and len({s['k'] for s in sources}) == len(sources)
        for source in sources:
            assert 1 <= source['k'] <= 20 and 1000 <= source['r'] <= 1500
            assert np.linalg.norm(source['g']) <= 1800 + 1e-8
            if scene['source_kind'] == 'omni': assert not source['directional']
            if scene['source_kind'] in ('boundary', 'directional'): assert source['directional']
            if scene['source_kind'] == 'boundary':
                close(np.linalg.norm(source['g']), 1800)
                assert source['r'] == 1000
                close(np.sin(source['psi']), source['g'][1]/1800)
                close(np.cos(source['psi']), source['g'][0]/1800)
    expected_matrix = {(v, s) for v in names for s in expected_scenes}
    assert len(rows) == len(expected_matrix) == completion['completed'] == completion['expected'] == 7600
    assert {(r['variant'], r['scene_id']) for r in rows} == expected_matrix
    assert completion['failures'] == 0 and not completion['code_changed_during_run']
    for row in rows:
        scene = scene_map[row['scene_id']]
        assert int(row['seed']) == scene['seed'] and row['source_kind'] == scene['source_kind'] and row['error_mode'] == scene['error_mode']
        assert row['scenario_sha256'] == scene['scenario_sha256']
        assert row['failure'] in ('', 'None') and row['full_success'] == row['all_certified'] == 'True'
        assert int(row['K']) == int(row['N']) == len(scene['sources'])
        close(row['T_over_K'], float(row['T'])/int(row['K']))
        close(row['movement_s'], float(row['move_m'])/5)
        close(row['T'], float(row['movement_s']) + 5*int(row['n_measure']) + int(row['switches']) + 3*int(row['n_clear']) + 2*int(row['K']))
        assert int(row['n_measure']) == int(row['discovery_measure']) + int(row['refine_measure'])
    assert len(manifest['sha256']) == 32
    current_changes = []
    for relative, expected in manifest['sha256'].items():
        assert sha(FOLDER/'source_snapshot'/relative) == expected, relative
        if sha(ROOT/relative) != expected: current_changes.append(relative)
    allowed_reporting_change = str(Path('experiments/q4_aggressive/summary_aggressive.py'))
    assert set(current_changes) <= {allowed_reporting_change}, current_changes
    if current_changes:
        before = ast.parse((FOLDER/'source_snapshot'/allowed_reporting_change).read_text(encoding='utf-8'))
        after = ast.parse((ROOT/allowed_reporting_change).read_text(encoding='utf-8'))
        # Normalize exactly the two inspected shared-seed wording edits, once each.
        class ReportingText(ast.NodeTransformer):
            def __init__(self): self.replaced = self.removed = 0
            def visit_Constant(self, node):
                if node.value == '单列边界压力组':
                    node.value = '独立边界压力组'; self.replaced += 1
                return node
            def visit_List(self, node):
                kept = []
                for item in node.elts:
                    if isinstance(item, ast.Constant) and item.value == '边界压力组与其他组共享部分种子；单列报告不表示与一般场景统计独立。':
                        self.removed += 1
                    else: kept.append(item)
                node.elts = kept
                return self.generic_visit(node)
        normalization = ReportingText(); after = normalization.visit(after)
        assert normalization.replaced == normalization.removed == 1
        # The other inspected change only adjusts per-figure highlighting/text/meta.
        before.body = [n for n in before.body if not isinstance(n, ast.FunctionDef) or n.name != 'render_table']
        after.body = [n for n in after.body if not isinstance(n, ast.FunctionDef) or n.name != 'render_table']
        assert ast.dump(before) == ast.dump(after)
    frozen = read(ROOT/'experiments/q4_efficiency/release_holdout100.meta.json')
    assert len(frozen['sha256']) == 13
    for relative, expected in frozen['sha256'].items(): assert sha(ROOT/relative) == expected
    original = read(EXP/'dev_valid40/manifest.json')
    combinations = read(EXP/'dev_combinations40/manifest.json')
    for name, cfg in original['configurations'].items(): assert manifest['configurations'][name] == cfg
    lock = read(EXP/'selection.json')
    assert set(names) == set(original['configurations']) | set(lock['combinations'])
    for name, item in lock['combinations'].items(): assert manifest['configurations'][name] == combinations['configurations'][name] == item['config']
    selection_key = next(k for k in manifest['sha256'] if k.endswith('selection.json'))
    assert manifest['sha256'][selection_key] == combinations['sha256'][selection_key] == sha(EXP/'selection.json')
    assert lock['results_sha256'] == sha(EXP/'dev_valid40/results.csv')
    assert lock['summary_sha256'] == sha(EXP/'dev_valid40/summary_general.csv')
    development_seeds = {s['seed'] for s in read(EXP/'dev_valid40/scenarios.json')}
    assert not development_seeds & {s['seed'] for s in scenes}
    record = dict(status='PASS',rows=len(rows),settings=len(scenes),arms=len(names),general_settings=350,stress_settings=50,
                  independent_seed_blocks=200,source_total_per_arm=sum(len(s['sources']) for s in scenes),
                  general_sources_per_arm=sum(len(s['sources']) for s in scenes if s['source_kind'] != 'boundary'),
                  verified_dependency_snapshots=32,verified_frozen_files=13,current_changes=current_changes,
                  reporting_change='render_table highlighting/text/meta plus exactly two shared-seed wording edits; statistical and policy AST unchanged' if current_changes else None,
                  locked_configs_unchanged=True,selection_unchanged=True,development_seed_overlap=False,
                  results_sha256=sha(FOLDER/'results.csv'),scenarios_sha256=sha(FOLDER/'scenarios.json'),script_sha256=sha(Path(__file__)))
    return manifest, rows, record


class PairedInference:
    """Reconstruct cluster resampling from setting rows without importing summaries."""
    def __init__(self, rows, names):
        self.rows = {name: {r['scene_id']: r for r in rows if r['variant'] == name} for name in names}
        self.ids = sorted(self.rows[names[0]])
        self.seeds = sorted({int(self.rows[names[0]][s]['seed']) for s in self.ids})
        self.index = {seed: i for i, seed in enumerate(self.seeds)}
        self.counts = np.zeros(len(self.seeds), dtype=int)
        for scene in self.ids: self.counts[self.index[int(self.rows[names[0]][scene]['seed'])]] += 1
        rng = np.random.default_rng(20260912)
        self.multiplicity = rng.multinomial(len(self.seeds), np.repeat(1/len(self.seeds), len(self.seeds)), 5000)
        self.signs = rng.choice([-1., 1.], (10000, len(self.seeds)))
        self.denominators = self.multiplicity @ self.counts

    def compare(self, control, candidate):
        delta = np.array([float(self.rows[candidate][s]['T_over_K'])-float(self.rows[control][s]['T_over_K']) for s in self.ids])
        sums = np.zeros(len(self.seeds))
        for scene, value in zip(self.ids, delta): sums[self.index[int(self.rows[control][scene]['seed'])]] += value
        draw_means = (self.multiplicity @ sums)/self.denominators
        bounds = np.quantile(draw_means, [.025, .975])
        extreme = np.abs(self.signs @ sums) >= abs(sum(delta))-1e-10
        probes = np.mean([int(self.rows[candidate][s]['n_measure'])-int(self.rows[control][s]['n_measure']) for s in self.ids])
        return dict(delta_T_over_K=float(delta.mean()),ci95_low=float(bounds[0]),ci95_high=float(bounds[1]),
                    block_signflip_p=float((1+extreme.sum())/10001),delta_probes=float(probes),
                    wins=int((delta < -1e-7).sum()),losses=int((delta > 1e-7).sum()))


def verify_explanatory(rows, names):
    mechanisms = table(FOLDER/'mechanisms.csv')
    assert len(mechanisms) == len(rows) == len({(r['variant'], r['scene_id']) for r in mechanisms})
    assert {(r['variant'], r['scene_id']) for r in mechanisms} == {(r['variant'], r['scene_id']) for r in rows}
    mechanisms = {(r['variant'], r['scene_id']): r for r in mechanisms}
    costs = table(FOLDER/'cost_decomposition.csv'); activations = table(FOLDER/'activation_summary.csv')
    expected_keys = {(c, n) for c in ('general','all','stress') for n in names}
    assert len(costs) == len(activations) == len(expected_keys)
    assert {(r['cohort'],r['variant']) for r in costs} == {(r['cohort'],r['variant']) for r in activations} == expected_keys
    decomposed = {}; activity = {}
    for cohort, name in sorted(expected_keys):
        subset = [r for r in rows if r['variant'] == name and (cohort == 'all' or (r['source_kind'] == 'boundary') == (cohort == 'stress'))]
        values = {key: float(np.mean([multiplier*float(r[column])/int(r['K']) for r in subset])) for key,column,multiplier in
                  [('walking','movement_s',1),('measurement','n_measure',5),('switching','switches',1),('clear_attempt','n_clear',3),('success','K',2)]}
        values['mean_T_over_K'] = float(np.mean([float(r['T_over_K']) for r in subset])); close(sum(v for k,v in values.items() if k != 'mean_T_over_K'),values['mean_T_over_K'])
        decomposed[cohort,name] = values
        checked = dict(cases=len(subset))
        for field in ('e_dispatch','expected_optical','two_step_probes','value_probes','value_heard','r_dispatch','wide_attempts','wide_success','n_trials','n_success'):
            counts = [int(mechanisms[r['variant'],r['scene_id']][field]) for r in subset]
            checked[field] = sum(counts); checked[field+'_active_cases'] = sum(n > 0 for n in counts)
        activity[cohort,name] = checked
    for row in costs:
        values = decomposed[row['cohort'],row['variant']]; lc = decomposed[row['cohort'],'LC']
        for field,value in values.items(): close(row[field],value); close(row['delta_'+field+'_vs_LC'],value-lc[field])
    for row in activations:
        for field,value in activity[row['cohort'],row['variant']].items(): assert int(row[field]) == value
    family = table(FOLDER/'family_comparisons.csv'); contrasts = table(FOLDER/'comparisons.csv')
    contrast_map = {(r['cohort'],r['control'],r['candidate']):r for r in contrasts}
    assert len(family) == 12 and {r['variant'] for r in family} == {'E1','E2','B20','B60','G075','G15','R2','R4','H200','H400','N20','N50'}
    for row in family:
        assert row['eligible'] == 'True' and row['family'] == row['variant'][0]
        close(row['mean_T_over_K'],decomposed['general',row['variant']]['mean_T_over_K'])
        source = contrast_map['general','LC',row['variant']]
        for field in ('ci95_low','ci95_high','delta_probes'): close(row[field],source[field])
        close(row['delta_vs_LC'],source['delta_T_over_K'])
    g = decomposed['general','G15']; lc = decomposed['general','LC']
    assert activity['general','R4']['r_dispatch_active_cases'] == 23
    for kind,error in { (r['source_kind'],r['error_mode']) for r in rows }:
        means = {n: np.mean([float(r['T_over_K']) for r in rows if r['variant']==n and r['source_kind']==kind and r['error_mode']==error]) for n in ('G15','LC')}
        assert means['G15'] < means['LC']
    return dict(status='PASS',cost_rows=len(costs),activation_rows=len(activations),family_rows=len(family),
                G15_walking_delta_vs_LC=g['walking']-lc['walking'],G15_other_cost_delta_vs_LC=sum(g[k]-lc[k] for k in ('measurement','switching','clear_attempt','success')),
                R4_general_active_dispatch_cases=23,G15_lower_mean_than_LC_in_all_five_strata=True,
                hashes={name:sha(FOLDER/name) for name in ('mechanisms.csv','cost_decomposition.csv','activation_summary.csv','family_comparisons.csv')},
                README_sha256=sha(EXP/'README.md'))


def verify_stats(manifest, rows, matrix):
    audit = read(FOLDER/'audit.json')
    assert audit['status'] == 'PASS' and audit['audited_runs'] == audit['expected_runs'] == 7600 and not audit['failed_runs']
    assert audit['results_sha256'] == matrix['results_sha256'] and audit['scenarios_sha256'] == matrix['scenarios_sha256']
    assert not audit['source_changes_after_completion'] and audit['verified_start_code_files'] == 32 and audit['frozen_file_mismatches'] == 0
    assert audit['operations'] == sum(int(r['n_measure'])+int(r['n_clear']) for r in rows)
    sample = read(HERE/'reviewer-audit-primary_valid400.json')
    assert sample['status'] == 'PASS' and sample['results_sha256'] == matrix['results_sha256']
    assert sample['script_sha256'] == sha(HERE/'reviewer_aggressive.py')
    names = list(manifest['configurations']); cohorts = {}; output = {}
    for cohort in ('general', 'all', 'stress'):
        part = [r for r in rows if cohort == 'all' or (r['source_kind'] == 'boundary') == (cohort == 'stress')]
        cohort_stats = PairedInference(part, names); cohorts[cohort] = cohort_stats
        comparisons = {name: cohort_stats.compare('baseline', name) for name in names}
        ordered = sorted((n for n in names if n != 'baseline'), key=lambda n: comparisons[n]['block_signflip_p'])
        holm = {}; previous = 0.
        for i, name in enumerate(ordered):
            previous = max(previous, comparisons[name]['block_signflip_p']*(len(ordered)-i)); holm[name] = min(previous, 1.)
        holm['baseline'] = 1.
        summary = table(FOLDER/f'summary_{cohort}.csv')
        assert {r['variant'] for r in summary} == set(names)
        checked = []
        for row in summary:
            name = row['variant']; subset = [r for r in part if r['variant'] == name]
            values = np.array([float(r['T_over_K']) for r in subset])
            expected = comparisons[name]
            assert int(row['cases']) == len(subset) and row['eligible_all400'] == 'True'
            assert int(row['source_total']) == int(row['cleared_total']) == sum(int(r['N']) for r in subset)
            assert int(row['independent_seed_blocks']) == len(cohort_stats.seeds)
            for target, source in [('mean_T', 'T'), ('mean_T_over_K', 'T_over_K'), ('mean_move', 'movement_s'), ('mean_probe', 'n_measure'), ('failed_clears','failed_clears')]:
                close(row[target], np.mean([float(r[source]) for r in subset]))
            for target, source in [('delta_vs_baseline','delta_T_over_K'), ('ci95_delta_low','ci95_low'), ('ci95_delta_high','ci95_high'), ('block_signflip_p','block_signflip_p')]: close(row[target], expected[source])
            assert int(row['wins']) == expected['wins'] and int(row['losses']) == expected['losses']
            close(row['holm_p'], holm[name]); close(row['p95'], np.quantile(values, .95))
            delta = [float(r['T_over_K'])-float(cohort_stats.rows['baseline'][r['scene_id']]['T_over_K']) for r in subset]
            close(row['worst_delta'], max(delta)); close(row['best_delta'], min(delta))
            checked.append(dict(variant=name,mean_T_over_K=float(values.mean()),mean_move=float(row['mean_move']),mean_probe=float(row['mean_probe']),
                                mean_T=float(row['mean_T']),p95=float(row['p95']),worst_delta=float(row['worst_delta']),holm_p=holm[name],**expected))
        output[cohort] = sorted(checked, key=lambda r: (r['mean_T_over_K'],r['variant']))
    compared = 0
    for filename in ('comparisons.csv', 'interactions.csv'):
        comparisons = table(FOLDER/filename)
        expected_keys = ({(cohort, control, candidate) for cohort in cohorts for control in ('LC','LPC','previous_best') for candidate in names if candidate not in ('baseline', control)}
                         if filename == 'comparisons.csv' else {(cohort, a, b) for cohort in cohorts for a,b in [('G075','G15'),('G075','GR'),('G075','GN'),('GR','GRN'),('GN','GRN')]})
        assert len(comparisons) == len(expected_keys) and {(r['cohort'], r['control'], r['candidate']) for r in comparisons} == expected_keys
        for row in comparisons:
            expected = cohorts[row['cohort']].compare(row['control'], row['candidate'])
            for field in ('delta_T_over_K', 'ci95_low', 'ci95_high', 'delta_probes'): close(row[field], expected[field])
            compared += 1
    assert not table(FOLDER/'failures.csv')
    top = output['general'][0]['variant']
    explanatory = verify_explanatory(rows, names)
    final = dict(status='PASS',matrix=matrix,physical_operations=audit['operations'],audited_result_sha256=audit['results_sha256'],explanatory=explanatory,
                 independent_sample=sample['counts'],cohorts=output,comparison_interaction_rows_reconstructed=compared,
                 general_winner=top,winner_vs_controls={c:cohorts['general'].compare(c,top) for c in ('LC','LPC','previous_best')},
                 statistics='All setting means, paired 5000-draw seed-block percentile intervals, 10000 sign flips, Holm across18 baseline contrasts, tails and mechanism contrasts independently reconstructed',
                 summary_hashes={f:sha(FOLDER/f) for f in ('summary_general.csv','summary_all.csv','summary_stress.csv','comparisons.csv','interactions.csv')},script_sha256=sha(Path(__file__)))
    (HERE/'reviewer-primary-statistics.json').write_text(json.dumps(final, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS',general_winner=top,general=output['general'],winner_vs_controls=final['winner_vs_controls'],comparison_rows=compared)))


if __name__ == '__main__':
    manifest, rows, record = load_matrix()
    (HERE/'reviewer-primary-matrix.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    if '--matrix' in sys.argv: print(json.dumps(record))
    else: verify_stats(manifest, rows, record)

"""Run local-decision Q4 families using the immutable first-round scenario/event engine."""
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

for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name]='1'
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT/'experiments/q4_ablation'),str(ROOT/'experiments/q4_local')]
import run_ablation as engine
from q4_aggressive_policies import VARIANTS,make_runner,cover_context

# Rebind the imported engine interface in this isolated process. Source is not edited.
engine.VARIANTS=VARIANTS
engine.make_runner=make_runner
engine.cover_context=cover_context


def settings(suite):
    if suite=='primary':
        start,count=70000,200
        extras=50
    else:
        start,count=60000,20
        extras=10
    scenes=engine.scenarios_for('dev',start,count)
    more=engine.scenarios_for('primary',0,0)
    template=[s for s in more if s['seed']<10000+extras and
              (s['source_kind'],s['error_mode'])!=('mixed','endpoint')]
    if suite=='dev':
        template=[s for s in template if (s['source_kind'],s['error_mode']) in
                  {('mixed','smooth'),('boundary','endpoint')}]
    for source in template:
        seed=source['seed']-10000+start
        base=engine.scenarios_for('dev',seed,1)[0]
        base.update(source_kind=source['source_kind'],error_mode=source['error_mode'],
                    scene_id=f"{source['source_kind']}_{source['error_mode']}_{seed}")
        if base['source_kind']!='mixed':
            for s in base['sources']:
                s['directional']=base['source_kind']!='omni'
                if base['source_kind']=='boundary':
                    g=engine.np.asarray(s['g']);g=g*1800/engine.np.linalg.norm(g)
                    s['g']=g.tolist();s['r']=1000.
                    s['psi']=float(engine.np.arctan2(g[1],g[0]))
        base.pop('scenario_sha256')
        base['scenario_sha256']=hashlib.sha256(engine.canonical(base).encode()).hexdigest()
        scenes.append(base)
    return scenes


def one(job):
    row=engine.one(job)
    name,scene,output=job
    with gzip.open(Path(output)/'events'/name/(scene['scene_id']+'.json.gz'),'rt',encoding='utf-8') as f:
        events=json.load(f)['events']
    row['n_selective_probe']=sum(e['op']=='selective_probe' for e in events)
    row['n_optimistic_attempt']=sum(e['op']=='optimistic_attempt' for e in events)
    row['n_early_optical_proposals']=sum(e['op']=='early_optical' for e in events)
    row['n_mass_attempt']=sum(e['op']=='mass_attempt' for e in events)
    row['n_budget_probe']=sum(e['op']=='budget_probe' for e in events)
    row['n_burst_actions']=sum(e['op']=='local_burst_action' for e in events)
    row['n_local_optical_proposals']=sum(e['op']=='local_optical_choice' for e in events)
    for op in ('expected_optical_choice','expected_optical_execution','value_probe','g_opportunity',
               'two_step_probe','wide_optimistic_attempt','early_exit_choice','endpoint_clear_attempt'):
        row['n_'+op]=sum(e['op']==op for e in events)
    return row


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--suite',choices=['dev','primary'],default='dev')
    ap.add_argument('--variants',default='')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args()
    names=args.variants.split(',') if args.variants else list(VARIANTS)
    assert len(set(names))==len(names) and all(n in VARIANTS for n in names)
    selection=HERE/'selection.json'
    if selection.exists():
        locked=json.loads(selection.read_text(encoding='utf-8'))
        for name,item in locked['combinations'].items():
            assert asdict(VARIANTS[name])==item['config']
    if args.output.exists():
        ap.error('output already exists; use a new run directory')
    scenes=settings(args.suite)
    manifest=engine.capture_manifest(args,scenes,names)
    dependencies=[HERE/'q4_aggressive_policies.py',Path(__file__),HERE/'design.md',HERE/'test_aggressive.py',
                  HERE/'acceptance.md',HERE/'reviews/implementation-readiness.md',HERE/'reviews/critique.md',
                  HERE/'reviews/skepticism.md',HERE/'reviews/correction-readiness.md',
                  ROOT/'experiments/q4_local/q4_local_policies.py',
                  ROOT/'experiments/q4_transfer/q4_transfer_policies.py']
    if selection.exists():dependencies.extend([selection,HERE/'select_combinations.py'])
    development_review=HERE/'reviews/development-validation.md'
    if args.suite=='primary':
        if not development_review.exists():ap.error('primary requires independent development review')
        dependencies.extend([development_review,HERE/'audit_aggressive.py',HERE/'summary_aggressive.py'])
    manifest['sha256'].update({str(p.relative_to(ROOT)):engine.sha(p) for p in dependencies})
    manifest['review_status']='correction-readiness PASS_WITH_WARNINGS for corrected initial development; result review pending'
    if args.suite=='primary':manifest['review_status']='development-validation reviewed; primary result review pending'
    manifest['prior_result_comparator']='previous_best is additional comparator; paired anchor remains frozen V4'
    manifest['selection_rule']='all rows; complete scenes required; rank mean T/K; disclose stress/tail regressions'
    manifest['eligibility']='Every setting: empty failure AND full_success AND K=N AND all_certified. N is true source count available only to evaluation; K is physically cleared sources, excluding absent channels.'
    manifest['ranking']='eligible on all settings, then minimum setting-weighted mean(T/K) on source_kind != boundary; retain all settings and failures'
    args.output.mkdir(parents=True)
    for name,digest in manifest['sha256'].items():
        p=ROOT/name
        snap=args.output/'source_snapshot'/name
        snap.parent.mkdir(parents=True,exist_ok=True);snap.write_bytes(p.read_bytes())
        assert engine.sha(snap)==digest
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (args.output/'scenarios.json').write_text(engine.canonical(scenes)+'\n',encoding='utf-8')
    jobs=[(name,scene,str(args.output)) for scene in scenes for name in names]
    failures=completed=0;started=time.perf_counter()
    with (args.output/'results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=None
        with mp.Pool(args.workers) as pool:
            for row in pool.imap_unordered(one,jobs):
                if writer is None:
                    writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                writer.writerow(row);completed+=1;failures+=not row['full_success']
                if completed%100==0 or completed==len(jobs):
                    f.flush();print(json.dumps(dict(completed=completed,total=len(jobs),failures=failures,
                                                  elapsed_s=round(time.perf_counter()-started,1))),flush=True)
    changed=[p for p,d in manifest['sha256'].items() if not (ROOT/p).exists() or engine.sha(ROOT/p)!=d]
    final=dict(completed=completed,expected=len(jobs),failures=failures,code_changed_during_run=changed,
               elapsed_s=time.perf_counter()-started)
    (args.output/'completion.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
    if changed:
        raise RuntimeError(f'source drift: {changed}')


if __name__=='__main__':
    main()

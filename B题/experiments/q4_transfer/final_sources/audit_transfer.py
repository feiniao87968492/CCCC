"""Replay every primary event against scenario truth and the published cost model.

Derived from q4_ablation/audit_evidence.py with source-snapshot validation.
This is a main-agent automated audit, not an independent expert review.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from q4_transfer_policies import cover_context
from q4_cover import cover_points
from params import COORD_ABS_LIMIT


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'))

def check_mechanisms(events,row,config):
    versions={k:0 for k in range(1,21)}
    trials={k:[] for k in versions}
    pending_o=pending_s=None
    o_success=s_heard=0
    optical_actions=optical_cells=0
    optical_early_executed=0
    positive=set()
    last_kind={}
    for e in events:
        op=e['op'];k=e.get('k')
        if op in ('ablation_action','v4_action'):
            last_kind[k]=e['kind']
        elif op=='optimistic_attempt':
            assert config['optimistic'] and pending_o is None
            assert e['positive_version']==versions[k] and versions[k]>=2
            assert versions[k] not in trials[k]
            trials[k].append(versions[k])
            assert len(trials[k])==e['trial']<=2
            pending_o=k
        elif op=='selective_probe':
            assert config['selective'] and k in positive and pending_s is None
            assert e['probability']>=config['reception_gate']-1e-12
            pending_s=k
        elif op=='measure':
            if pending_s is not None:
                assert k==pending_s
                s_heard+=e['result']!='no_signal'
                pending_s=None
            if e['result'] in ('direction','near'):
                versions[k]+=1;positive.add(k)
        elif op=='clear' and pending_o is not None:
            assert k==pending_o
            o_success+=bool(e['ok']);pending_o=None
        elif op=='optical_cover':
            optical_actions+=1;optical_cells+=e['count']
            if config['optical_cells'] and e['rho']<=60 and e['count']<=config['optical_cells']:
                optical_early_executed+=1
    assert pending_o is None and pending_s is None
    assert sum(map(len,trials.values()))==int(row['n_optimistic_attempt'])
    assert sum(e['op']=='selective_probe' for e in events)==int(row['n_selective_probe'])
    assert optical_actions==int(row['n_optical_fallback'])
    return dict(variant=row['variant'], scene_id=row['scene_id'],
                selective_probe=sum(e.get('op')=='selective_probe' for e in events),
                optimistic_attempt=sum(e.get('op')=='optimistic_attempt' for e in events),
                optimistic_success=o_success,selective_heard=s_heard,
                early_optical=sum(e.get('op')=='early_optical' for e in events),
                optical_actions=optical_actions,optical_candidate_cells=optical_cells,
                optical_actions_within_early_threshold=optical_early_executed,
                failed_clear=sum(e.get('op')=='clear' and not e.get('ok',True) for e in events),
                measures=sum(e.get('op')=='measure' for e in events),
                clears=sum(e.get('op')=='clear' for e in events))


def audit(folder):
    manifest = read(folder/'manifest.json')
    scenes = read(folder/'scenarios.json')
    assert hashlib.sha256(canonical(scenes).encode()).hexdigest()==manifest['scenarios_sha256']
    scenario_map = {s['scene_id']:s for s in scenes}
    for s in scenes:
        raw = {k:v for k,v in s.items() if k!='scenario_sha256'}
        assert hashlib.sha256(canonical(raw).encode()).hexdigest()==s['scenario_sha256']
    with (folder/'results.csv').open(encoding='utf-8-sig',newline='') as f:
        rows = list(csv.DictReader(f))
    expected = len(scenes)*len(manifest['configurations'])
    assert len(rows)==expected
    assert len({(r['variant'],r['scene_id']) for r in rows})==expected
    assert {(r['variant'],r['scene_id']) for r in rows}=={
        (n,s['scene_id']) for n in manifest['configurations'] for s in scenes}
    start_code = []
    changed_since_run = []
    for name,h in manifest['sha256'].items():
        snapshot=folder/'source_snapshot'/name
        assert snapshot.exists() and digest(snapshot)==h, name
        start_code.append(name)
        p=ROOT/name
        if not p.exists() or digest(p)!=h:
            changed_since_run.append(name)
    completion=read(folder/'completion.json')
    assert not completion['code_changed_during_run']
    assert completion['completed']==completion['expected']==expected
    frozen = read(ROOT/'experiments/q4_efficiency/release_holdout100.meta.json')
    assert all(digest(ROOT/p)==h for p,h in frozen['sha256'].items())
    max_residual = 0.
    operations = 0
    failures = []
    mechanism_rows=[]
    for index,row in enumerate(rows,1):
        config = manifest['configurations'][row['variant']]
        scene = scenario_map[row['scene_id']]
        assert scene['scenario_sha256']==row['scenario_sha256']
        with cover_context(config['outer_radius']):
            cover = cover_points().copy()
        with gzip.open(folder/'events'/row['variant']/(row['scene_id']+'.json.gz'),'rt',encoding='utf-8') as f:
            data=json.load(f)
        events=data['events']
        mechanism_rows.append(check_mechanisms(events,row,config))
        assert hashlib.sha256(canonical(events).encode()).hexdigest()==row['event_sha256']
        sources={s['k']:s for s in scene['sources']}
        pos=np.zeros(2); t=0.; move=0.; channel=1; nm=nc=switches=0
        cleared=set(); detected=set(); negative={k:set() for k in range(1,21)}
        for e in events:
            if e['op'] not in ('measure','clear'):
                continue
            operations+=1
            q=np.array([e['x'],e['y']]); k=e['k']
            assert np.all(np.isfinite(q)) and np.all(np.abs(q)<=COORD_ABS_LIMIT)
            assert k in range(1,21) and k not in cleared
            dist=float(np.linalg.norm(q-pos)); move+=dist; t+=dist/5
            src=sources.get(k)
            if e['op']=='measure':
                nm+=1; switches+=channel!=k; t+=5+(channel!=k); channel=k
                if src is None:
                    heard=False
                else:
                    v=q-np.asarray(src['g']); d=float(np.linalg.norm(v))
                    h=np.array([np.cos(src.get('psi',0)),np.sin(src.get('psi',0))])
                    heard=d<=src['r']+1e-9 and (not src['directional'] or
                          (d>=1e-12 and float(h@v)>=-1e-9))
                if e['result']=='no_signal':
                    assert not heard, (row['variant'],row['scene_id'],e)
                    ids=np.flatnonzero(np.linalg.norm(cover-q,axis=1)<=1e-6)
                    negative[k].update(ids.tolist())
                else:
                    assert heard
                    detected.add(k)
                    assert (e['result']=='near')==(d<=5.)
                    if e['result']=='direction':
                        truth=np.rad2deg(np.arctan2(-v[1],-v[0]))
                        err=(e['svd']-truth+180)%360-180
                        assert abs(err)<=1.0050001
            else:
                nc+=1; t+=3+2*e['ok']
                ok=src is not None and np.linalg.norm(q-np.asarray(src['g']))<=20.+1e-9
                assert bool(e['ok'])==bool(ok)
                if ok:
                    cleared.add(k)
            max_residual=max(max_residual,abs(t-e['t']))
            assert abs(t-e['t'])<1e-7
            pos=q
        assert nm==int(row['n_measure']) and nc==int(row['n_clear'])
        assert switches==int(row['switches']) and len(cleared)==int(row['K'])
        assert abs(move-float(row['move_m']))<1e-7 and abs(t-float(row['T']))<1e-7
        expected_full=cleared==set(sources) and row['failure'] in ('','None','nan')
        if expected_full:
            assert len(detected)>=16 or all(len(negative[k])==len(cover) for k in range(1,21) if k not in sources)
        assert (row['full_success']=='True')==expected_full
        if not expected_full:
            failures.append((row['variant'],row['scene_id']))
        if index%1000==0:
            print(f'audited {index}/{expected} event traces',flush=True)
    result=dict(status='PASS',audit_type='automated event/truth replay, not independent expert review',
                audited_runs=len(rows),expected_runs=expected,operations=operations,
                failed_runs=failures,max_event_time_residual_s=max_residual,
                verified_start_code_files=len(start_code),frozen_file_mismatches=0,
                source_changes_after_completion=changed_since_run,results_sha256=digest(folder/'results.csv'),
                scenarios_sha256=digest(folder/'scenarios.json'),audit_script_sha256=digest(Path(__file__)))
    (folder/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (folder/'mechanisms.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(mechanism_rows[0]))
        writer.writeheader();writer.writerows(mechanism_rows)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path)
    audit(ap.parse_args().folder)

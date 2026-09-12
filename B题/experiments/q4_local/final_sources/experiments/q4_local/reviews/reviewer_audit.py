"""Independent local-event linkage and bounded posterior-mass reconstruction.

No policy or simulator is executed. Production positive polygon construction
is reused to preserve its deterministic sample ordering; RF weights, candidate
scores/LS and candidate halfplane membership are reconstructed here.
"""
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'src'))
from q4_localize import history_region,optical_cover_points


def rf_distribution(region,history):
    v=np.asarray(region['verts']);anchor=v.mean(axis=0)
    a=v-anchor;b=np.roll(v,-1,axis=0)-anchor
    areas=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])
    if areas.sum()<1e-9:
        ij=np.unravel_index(np.argmax(np.linalg.norm(v[:,None]-v[None,:],axis=2)),(len(v),len(v)))
        points=np.linspace(v[ij[0]],v[ij[1]],48)
    else:
        ids=np.searchsorted(np.cumsum(areas)/areas.sum(),(np.arange(48)+.5)/48)
        u=np.sqrt((.5+np.arange(48)*.618033988749895)%1)
        z=(.5+np.arange(48)*.414213562373095)%1
        points=anchor+u[:,None]*((1-z[:,None])*a[ids]+z[:,None]*b[ids])
    angles=np.arange(32)*2*np.pi/32
    heading=np.column_stack((np.cos(angles),np.sin(angles)))
    radii=np.array([1000.,1250.,1500.])
    weights=np.ones((48,33,3));weights[:,:32,:]/=32
    for h in history:
        vec=h['pos']-points
        received=(np.column_stack((vec@heading.T>=0,np.ones(48,dtype=bool)))[:,:,None]
                  & (np.linalg.norm(vec,axis=1)[:,None]<=radii)[:,None,:])
        weights*=np.where(received==(h['result'] in ('direction','near')),1.,.002)
        weights/=weights.sum()
    return points,(weights/weights.sum()).sum(axis=(1,2))


def in_positive_halfplanes(q,history):
    theta=np.arange(48)*2*np.pi/48
    normals=np.column_stack((np.cos(theta),np.sin(theta)))
    if np.max(normals@q-1800)>1e-6:return False
    for h in history:
        if h['result'] not in ('direction','near'):continue
        offset=q-h['pos']
        if np.max(normals@offset-(5. if h['result']=='near' else 1500.))>1e-6:return False
        if h['result']=='direction':
            low,high=np.deg2rad([h['svd']-1.005,h['svd']+1.005])
            aa=np.array([[np.sin(low),-np.cos(low)],[-np.sin(high),np.cos(high)]])
            if np.max(aa@offset)>1e-6:return False
    return True


def ls_candidate(history):
    bearings=[h for h in history if h['result']=='direction']
    if len(bearings)<2:return None
    angle=np.deg2rad([h['svd'] for h in bearings]);aa=np.column_stack((-np.sin(angle),np.cos(angle)))
    if np.linalg.cond(aa)>30:return None
    return np.linalg.lstsq(aa,np.array([n@h['pos'] for n,h in zip(aa,bearings)]),rcond=None)[0]


def main():
    folder=HERE.parent/(sys.argv[1] if len(sys.argv)>1 else 'primary400')
    assert (folder/'completion.json').exists()
    rows=list(csv.DictReader((folder/'results.csv').open(encoding='utf-8')))
    manifest=json.loads((folder/'manifest.json').read_text())
    sample_seeds=sorted({int(r['seed']) for r in rows})[:2]
    counts=collections.Counter();failures=[];max_mass_error=0.;max_choice_error=0.;max_optical_cost_error=0.
    for row in rows:
        config=manifest['configurations'][row['variant']]
        optical_sample=config['optical_ratio'] and int(row['seed']) in sample_seeds
        if not (config['stop_budget'] or config['burst_radius'] or config['mass_gate'] or optical_sample):continue
        events=json.load(gzip.open(folder/'events'/row['variant']/(row['scene_id']+'.json.gz'),'rt'))['events']
        counts['mechanism_traces']+=1
        pos=np.zeros(2);stop=0;used=0;budget_pending=None;selective_pending=None
        burst=None;bad_burst_step=False;last={};versions=collections.Counter();mass_versions=collections.defaultdict(list)
        history=collections.defaultdict(list);failed=collections.defaultdict(list);optical_cache={}
        sample=config['mass_gate'] and int(row['seed']) in sample_seeds
        if sample:counts['mass_sample_traces']+=1
        if optical_sample:counts['optical_sample_traces']+=1
        for e in events:
            op=e['op'];k=e.get('k')
            if op=='budget_probe':
                assert budget_pending is None and selective_pending is None
                used+=1
                assert e['stop_id']==stop and e['used']==used<=config['stop_budget']
                budget_pending=k;counts['budget_tokens']+=1
            elif op=='selective_probe' and config['stop_budget']:
                assert budget_pending==k and selective_pending is None
                selective_pending=k;budget_pending=None;counts['budget_linked_selective']+=1
            elif op=='local_burst_start':
                assert burst is None and last[k]['op']=='measure' and last[k]['result'] in ('direction','near')
                burst=dict(k=k,id=e['burst_id'],steps=0);bad_burst_step=False
            elif op=='local_burst_action':
                assert burst is not None and not bad_burst_step
                burst['steps']+=1
                assert k==burst['k'] and e['index']==burst['steps']<=2 and e['burst_id']==burst['id']
                assert e['kind']!='optical' and e['distance']<=config['burst_radius']+1e-9
                counts['burst_steps']+=1
            elif op=='local_burst_end':
                assert burst is not None
                if bad_burst_step:assert e['reason'] in ('no_signal','failed_clear')
                burst=None
            elif op=='local_optical_choice' and optical_sample:
                if k not in optical_cache or optical_cache[k][0]!=versions[k]:
                    region=history_region(history[k])
                    optical_cache[k]=(versions[k],optical_cover_points(region['verts']),region['rho'])
                _,cells,rho=optical_cache[k]
                current=pos.copy();remaining=list(cells);distance=0.
                while remaining:
                    index=min(range(len(remaining)),key=lambda j:np.linalg.norm(remaining[j]-current))
                    q=remaining.pop(index);distance+=float(np.linalg.norm(q-current));current=q
                cost=distance/5+3*len(cells)+2
                max_optical_cost_error=max(max_optical_cost_error,abs(cost-e['optical_cost']))
                assert len(cells)==e['cells']<=12 and rho<=80+1e-7 and abs(cost-e['optical_cost'])<1e-8
                assert cost<=config['optical_ratio']*e['rf_cost']+1e-8
                counts['optical_cost_proposals']+=1
            elif op=='mass_attempt':
                assert e['positive_version']==versions[k] and versions[k] not in mass_versions[k]
                mass_versions[k].append(versions[k]);assert len(mass_versions[k])==e['trial']<=2
                assert config['mass_gate']-1e-12<=e['mass']<=1+1e-12
                counts['mass_attempts']+=1
                if sample:
                    region=history_region(history[k]);points,w=rf_distribution(region,history[k])
                    q=np.array([e['x'],e['y']]);mass=float((np.linalg.norm(points-q,axis=1)<=20)@w)
                    max_mass_error=max(max_mass_error,abs(mass-e['mass']))
                    candidates=[region['center'],*points];ls=ls_candidate(history[k])
                    if ls is not None:candidates.append(ls)
                    candidates=[p for p in candidates if np.all(np.abs(p)<=2000000) and in_positive_halfplanes(p,history[k])
                                and all(np.linalg.norm(p-f)>1 for f in failed[k])]
                    cover=np.linalg.norm(np.asarray(candidates)[:,None]-points[None,:],axis=2)<=20
                    scores=cover@w
                    index=min(range(len(candidates)),key=lambda i:(-scores[i],float(np.linalg.norm(candidates[i]-pos))))
                    error=float(np.linalg.norm(q-candidates[index]));max_choice_error=max(max_choice_error,error)
                    counts['mass_sample_attempts']+=1
                    assert region['rho']<=160+1e-7 and in_positive_halfplanes(q,history[k])
                    assert mass>=config['mass_gate']-1e-12 and abs(mass-e['mass'])<1e-10 and error<1e-6, (row['variant'],row['scene_id'],k,mass,e['mass'],error,q,candidates[index],scores[index])
            elif op in ('measure','clear'):
                if selective_pending is not None:
                    assert op=='measure' and k==selective_pending
                    selective_pending=None;counts['budget_linked_measure']+=1
                q=np.array([e['x'],e['y']])
                if np.linalg.norm(q-pos)>1:stop+=1;used=0
                pos=q;last[k]=e
                if burst is not None and k==burst['k']:
                    if op=='measure' and e['result']=='no_signal':bad_burst_step=True
                    if op=='clear' and not e['ok']:bad_burst_step=True
                if op=='measure':
                    history[k].append(dict(pos=q,result=e['result'],svd=e.get('svd')))
                    versions[k]+=e['result'] in ('direction','near')
                elif not e['ok']:failed[k].append(q)
        assert budget_pending is None and selective_pending is None and burst is None
    result=dict(status='PASS',checks=dict(counts),max_mass_error=max_mass_error,max_candidate_distance_error_m=max_choice_error,
                max_optical_cost_error_s=max_optical_cost_error,
                sample='M50/M75, first two seeds in each available source/error stratum',sample_seeds=sample_seeds,
                independence='Production positive polygon/center and optical cells reused; RF weights, LS/mass ranking, positive halfplane inclusion and NN optical route/charging independently reconstructed; RF cost surrogate not independently reconstructed; no policy/simulator executed',
                results_sha256=hashlib.sha256((folder/'results.csv').read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),failures=failures)
    (HERE/('reviewer-audit.json' if folder.name=='primary400' else 'reviewer-audit-'+folder.name+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()

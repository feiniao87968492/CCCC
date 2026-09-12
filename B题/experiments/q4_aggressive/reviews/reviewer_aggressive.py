"""Reviewer-only independent score reconstruction; never runs a simulator/policy."""
import ast
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent.parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from q4_localize import history_region,optical_cover_points


def legal(q):return bool(np.all(np.isfinite(q)) and np.all(np.abs(q)<=2000000))


def rf(region,hist):
    v=np.asarray(region['verts']);center=v.mean(axis=0);a=v-center;b=np.roll(v,-1,axis=0)-center
    areas=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])
    if areas.sum()<1e-9:
        ij=np.unravel_index(np.argmax(np.linalg.norm(v[:,None]-v[None,:],axis=2)),(len(v),len(v)))
        points=np.linspace(v[ij[0]],v[ij[1]],48)
    else:
        ids=np.searchsorted(np.cumsum(areas)/areas.sum(),(np.arange(48)+.5)/48)
        u=np.sqrt((.5+np.arange(48)*.618033988749895)%1);z=(.5+np.arange(48)*.414213562373095)%1
        points=center+u[:,None]*((1-z[:,None])*a[ids]+z[:,None]*b[ids])
    angle=np.arange(32)*2*np.pi/32;head=np.c_[np.cos(angle),np.sin(angle)]
    def heard(q):
        vec=q-points
        return np.column_stack((vec@head.T>=0,np.ones(48,dtype=bool)))[:,:,None] & (np.linalg.norm(vec,axis=1)[:,None]<=np.array([1000.,1250.,1500.]))[:,None,:]
    weights=np.ones((48,33,3));weights[:,:32]/=32
    for h in hist:
        weights*=np.where(heard(h['pos'])==(h['result'] in ('direction','near')),1.,.002)
        weights/=weights.sum()
    return points,weights/weights.sum(),heard


def predicted_radius(points,q,hist):
    vec=points-q;dist=np.linalg.norm(vec,axis=1);sine=np.zeros(len(points))
    for h in hist:
        if h['result']!='direction':continue
        old=points-h['pos'];sine=np.maximum(sine,np.abs(old[:,0]*vec[:,1]-old[:,1]*vec[:,0])/np.maximum(dist*np.linalg.norm(old,axis=1),1e-9))
    return 2*np.tan(np.deg2rad(1.005))*dist/np.maximum(sine,.015),dist


def b_score(points,weights,heard,hist,pos,q):
    pred,dist=predicted_radius(points,q,hist);vec=points-q
    unit=np.divide(vec,dist[:,None],out=np.tile([1.,0.],(len(points),1)),where=dist[:,None]>1e-12)
    side=np.c_[-unit[:,1],unit[:,0]]*np.clip(pred,20,120)[:,None]
    costs=[]
    for virtual in (points+side,points-side):
        costs.append(np.where(np.array([legal(v) for v in virtual]),(np.linalg.norm(virtual-q,axis=1)+np.linalg.norm(virtual-points,axis=1))/5+11,np.inf))
    continuation=np.minimum(costs[0],costs[1]);continuation=np.where(np.isfinite(continuation),continuation,dist/5+89)
    continuation=np.where(pred<=20,dist/5+5,continuation)
    positive=(weights*heard(q)).sum(axis=(1,2));prob=float(positive.sum());first=float(np.linalg.norm(q-pos))/5+6
    after=float(positive@continuation);negative=78*(1-prob)
    return dict(score=first+after+negative,first=first,continuation=after,no_reception_cost=negative,probability=prob)


def inside(q,hist):
    theta=np.arange(48)*2*np.pi/48;normal=np.c_[np.cos(theta),np.sin(theta)]
    if np.max(normal@q-1800)>1e-6:return False
    for h in hist:
        if h['result'] not in ('direction','near'):continue
        offset=q-h['pos']
        if np.max(normal@offset-(5 if h['result']=='near' else 1500))>1e-6:return False
        if h['result']=='direction':
            lo,hi=np.deg2rad([h['svd']-1.005,h['svd']+1.005]);aa=np.array([[np.sin(lo),-np.cos(lo)],[-np.sin(hi),np.cos(hi)]])
            if np.max(aa@offset)>1e-6:return False
    return True


def estimate(hist):
    pos=[h for h in hist if h['result']=='direction']
    if len(pos)<2:return None
    angle=np.deg2rad([h['svd'] for h in pos]);aa=np.c_[-np.sin(angle),np.cos(angle)]
    if np.linalg.cond(aa)>30:return None
    q=np.linalg.lstsq(aa,np.array([n@h['pos'] for n,h in zip(aa,pos)]),rcond=None)[0]
    return q if legal(q) and inside(q,hist) else None


def b_candidates(region,hist,points,weights,radius,pos):
    bearings=[h for h in hist if h['result']=='direction'];last=bearings[-1]
    origin=last['pos'];a=np.deg2rad(last['svd']);axis=np.array([np.cos(a),np.sin(a)]);side=np.array([-axis[1],axis[0]])
    projection=(region['verts']-origin)@axis;center=region['center'];candidates=[]
    for along,across in ((80.,60.),(200.,100.)):
        for sign in (-1,1):candidates.append(origin+along*axis+sign*across*side)
    for fraction in (.25,.5,.75):
        approach=origin+(projection.min()+fraction*np.ptp(projection))*axis
        for offset in (-140.,-60.,60.,140.):candidates.append(approach+offset*side)
    distance=float(np.clip(2*region['rho'],40,180))
    for along,across in ((-1,0),(-.7,1),(-.7,-1),(0,1),(0,-1),(1,0)):candidates.append(center+distance*(along*axis+across*side))
    centers=[weights.sum(axis=(1,2))@points];ls=estimate(hist)
    if ls is not None:centers.append(ls)
    for c in centers:candidates.extend([c,*[c+radius*np.array(v) for v in ((1,0),(-1,0),(0,1),(0,-1))]])
    fresh=[]
    for q in candidates:
        if legal(q) and all(np.linalg.norm(q-h['pos'])>1 for h in hist) and all(np.linalg.norm(q-p)>1e-8 for p in fresh):fresh.append(q)
    pair=[]
    if len(bearings)==1 and hist[-1]['result']=='no_signal' and projection.min()>30:
        along=min(80.,.4*float(projection.min()));width=.75*along
        pair=[origin+along*axis+sign*width*side for sign in (-1,1)]
        if not all(legal(q) and np.max(np.dot(q-origin,q-origin)-2*(region['verts']-origin)@(q-origin))<-1e-6 for q in pair):pair=[]
        pair=[q for q in pair if all(np.linalg.norm(q-h['pos'])>1 for h in hist)]
        pair.sort(key=lambda q:float(np.linalg.norm(q-pos)))
    return fresh,pair


def e_plan(cells,points,weights,pos,failed):
    w=weights.copy()
    for f in failed:w[np.linalg.norm(points-f,axis=1)<=20]=0
    reset=w.sum()<=1e-12;w=np.ones(len(w))/len(w) if reset else w/w.sum()
    hit=np.linalg.norm(cells[:,None]-points[None,:],axis=2)<=20;unhit=np.ones(len(w),dtype=bool)
    pending=list(range(len(cells)));order=[];at=pos.copy();charges=[];executed=[]
    while pending:
        ratios=[((float(w[unhit&hit[j]].sum())+.05/len(cells))/(3+float(np.linalg.norm(cells[j]-at))/5),-float(np.linalg.norm(cells[j]-at)),-j,j) for j in pending]
        j=max(ratios)[3];order.append(j);pending.remove(j)
        if any(np.linalg.norm(cells[j]-f)<1e-7 for f in failed):continue
        charges.append(float(np.linalg.norm(cells[j]-at))/5+3);executed.append(j);at=cells[j];unhit&=~hit[j]
    cumulative=np.cumsum(charges);sample_cost=[]
    for i in range(len(points)):
        first=next((t for t,j in enumerate(executed) if hit[j,i]),None)
        sample_cost.append(0 if not len(cumulative) else cumulative[-1] if first is None else cumulative[first])
    return order,float(w@sample_cost+2),float(sum(charges)+2),bool(reset)


def g_admission(region,hist,points,weights,heard,pos,channel,k):
    if region is None or region['rho']<=40 or any(np.linalg.norm(pos-h['pos'])<=1 for h in hist):return None
    directions=[h for h in hist if h['result']=='direction']
    center=region['center'];distance=float(np.linalg.norm(center-pos))
    if not directions or distance>1100:return None
    vec=center-pos
    sine=max(abs(float(vec[0]*(center-h['pos'])[1]-vec[1]*(center-h['pos'])[0]))/max(float(np.linalg.norm(vec)*np.linalg.norm(center-h['pos'])),1e-9) for h in directions)
    if sine<np.sin(np.deg2rad(12)) and distance>=.5*np.linalg.norm(center-directions[-1]['pos']):return None
    pred,_=predicted_radius(points,pos,hist);wh=(weights*heard(pos)).sum(axis=(1,2));prob=float(wh.sum())
    if prob<.5:return None
    gain=float(wh@np.maximum(0,np.log((region['rho']+2)/(np.maximum(pred,2)+2))))
    charge=5+int(channel!=k)
    return dict(score=float(region['rho']*(1-np.exp(-gain))/(5*charge)),gain=gain,probability=prob,charge=charge,parallax_sine=sine)


def pure_fixtures():
    sys.path.insert(0,str(HERE))
    from q4_aggressive_policies import optical_plan,continuation_cost
    cases=[
        ([[0,0],[20,0],[60,0]],[[10,0],[60,0],[200,0]],[.4,.5,.1],[-10,0],[]),
        ([[0,0],[40,0],[80,0]],[[0,0],[80,0]],[.5,.5],[0,0],[[0,0]]),
        ([[0,0],[40,0]],[[0,0]],[1.],[0,0],[[0,0]]),
        ([],[[0,0]],[1.],[0,0],[]),
    ]
    for c,pts,w,pos,failed in cases:
        args=(np.asarray(c,dtype=float).reshape(-1,2),np.asarray(pts,dtype=float),np.asarray(w),np.asarray(pos,dtype=float),failed)
        ours=e_plan(*args);actual=optical_plan(*args)
        assert ours[0]==actual[0] and ours[3]==actual[3] and np.allclose(ours[1:3],actual[1:3],atol=1e-10,rtol=0)
    points=np.array([[0.,0.],[100.,0.],[2000000.,2000000.]])
    q=np.zeros(2);pred=np.array([80.,20.,100.]);actual=continuation_cost(points,q,pred)
    expected=np.array([43.,25.,np.sqrt(8e12)/5+89])
    assert np.allclose(actual,expected,atol=1e-8,rtol=0)
    weights=np.ones((3,1,1))/3
    zero=lambda at:np.zeros((3,1,1),dtype=bool)
    terms=b_score(points,weights,zero,[],q,np.array([100.,0.]))
    assert terms['probability']==terms['continuation']==0 and abs(terms['score']-104)<1e-10
    return dict(E_overlap_skip_reset_empty=4,B_coincident_certified_illegal_virtual=3,B_zero_heard=1)


def matrix_audit():
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    table=lambda p:list(csv.DictReader(p.open(encoding='utf-8')))
    records={};matrices={}
    for name in ('dev_valid40','dev_combinations40'):
        folder=HERE/name;manifest=read(folder/'manifest.json');scenes=read(folder/'scenarios.json')
        completion=read(folder/'completion.json');audit=read(folder/'audit.json');rows=table(folder/'results.csv')
        assert digest(folder/'results.csv')==audit['results_sha256'] and audit['status']=='PASS' and not audit['failed_runs']
        assert digest(folder/'scenarios.json')==audit['scenarios_sha256']
        assert hashlib.sha256(canonical(scenes)).hexdigest()==manifest['scenarios_sha256']
        expected={(v,s['scene_id']) for v in manifest['configurations'] for s in scenes}
        assert len(rows)==len(expected)==completion['completed']==completion['expected']==audit['audited_runs']==audit['expected_runs']
        assert {(r['variant'],r['scene_id']) for r in rows}==expected
        assert not completion['code_changed_during_run'] and completion['failures']==0
        scene_map={s['scene_id']:s for s in scenes}
        for s in scenes:assert hashlib.sha256(canonical({k:v for k,v in s.items() if k!='scenario_sha256'})).hexdigest()==s['scenario_sha256']
        for r in rows:
            assert r['failure'] in ('','None') and r['full_success']==r['all_certified']=='True'
            assert int(r['K'])==int(r['N'])==len(scene_map[r['scene_id']]['sources'])
            assert r['scenario_sha256']==scene_map[r['scene_id']]['scenario_sha256']
            assert abs(float(r['T_over_K'])-float(r['T'])/int(r['K']))<1e-9
            assert abs(float(r['movement_s'])-float(r['move_m'])/5)<1e-8
            charge=float(r['movement_s'])+5*int(r['n_measure'])+int(r['switches'])+3*int(r['n_clear'])+2*int(r['K'])
            assert abs(float(r['T'])-charge)<1e-8
        current_changes=[]
        for rel,sha in manifest['sha256'].items():
            assert digest(folder/'source_snapshot'/rel)==sha
            if digest(ROOT/rel)!=sha:current_changes.append(rel)
        for cohort in ('all','general','stress'):
            for s in table(folder/('summary_'+cohort+'.csv')):
                part=[r for r in rows if r['variant']==s['variant'] and (cohort=='all' or (r['source_kind']=='boundary')==(cohort=='stress'))]
                assert len(part)==int(s['cases']) and s['eligible_all400']=='True'
                for column,key in (('mean_T','T'),('mean_T_over_K','T_over_K'),('mean_move','movement_s'),('mean_probe','n_measure')):
                    assert abs(float(s[column])-sum(float(r[key]) for r in part)/len(part))<1e-8
                for column,key in (('source_total','N'),('cleared_total','K')):
                    if column in s:assert int(s[column])==sum(int(r[key]) for r in part)
        means={v:sum(float(r['T_over_K']) for r in rows if r['variant']==v and r['source_kind']!='boundary')/30 for v in manifest['configurations']}
        records[name]=dict(status='PASS',rows=len(rows),settings=len(scenes),source_total_per_arm=sum(len(s['sources']) for s in scenes),
            general_settings=sum(s['source_kind']!='boundary' for s in scenes),seed_blocks=len({r['seed'] for r in rows}),
            means=means,results_sha256=digest(folder/'results.csv'),current_changes=current_changes,verified_snapshot_files=len(manifest['sha256']))
        matrices[name]={(r['variant'],r['scene_id']):r for r in rows}
    shared=set(matrices['dev_valid40'])&set(matrices['dev_combinations40'])
    for key in shared:
        for field,value in matrices['dev_valid40'][key].items():
            if field not in ('planner_wall_s','wall_s'):assert value==matrices['dev_combinations40'][key][field],(key,field)
    lock=read(HERE/'selection.json');means=records['dev_valid40']['means'];best=[]
    assert lock['results_sha256']==records['dev_valid40']['results_sha256'] and lock['summary_sha256']==digest(HERE/'dev_valid40/summary_general.csv')
    for family in ('E','B','G','R','H','N'):
        names=[v for v in means if v.startswith(family)];winner=min(names,key=lambda v:(means[v],v));best.append(dict(family=family,variant=winner,delta=means[winner]-means['LC']))
    assert all(a['family']==b['family'] and a['variant']==b['variant'] and abs(a['delta']-b['delta'])<1e-9 for a,b in zip(best,lock['families']))
    selected=sorted([b for b in best if b['delta']< -1e-7],key=lambda b:(b['delta'],b['variant']))[:3]
    assert [b['variant'] for b in selected]==[b['variant'] for b in lock['selected_families']]
    combo_manifest=read(HERE/'dev_combinations40/manifest.json')
    assert set(lock['combinations'])=={'GR','GN','GRN'}
    for name,item in lock['combinations'].items():assert item['config']==combo_manifest['configurations'][name]
    rel=Path('experiments/q4_aggressive/q4_aggressive_policies.py')
    original=ast.parse((HERE/'dev_valid40/source_snapshot'/rel).read_text())
    current=ast.parse((ROOT/rel).read_text())
    for node in ast.walk(current):
        if isinstance(node,ast.Dict):
            keep=[i for i,k in enumerate(node.keys) if not (isinstance(k,ast.Constant) and k.value in ('GR','GN','GRN'))]
            node.keys=[node.keys[i] for i in keep];node.values=[node.values[i] for i in keep]
    assert ast.dump(current)==ast.dump(original)
    frozen=read(ROOT/'experiments/q4_efficiency/release_holdout100.meta.json')
    for rel,sha in frozen['sha256'].items():assert digest(ROOT/rel)==sha
    out=dict(status='PASS',cohorts=records,identical_shared_physical_and_event_rows=len(shared),selection_verified=True,
             policy_change='AST identical after removing exactly GR/GN/GRN registry entries',frozen_files_verified=len(frozen['sha256']),
             current_policy_sha256=digest(ROOT/'experiments/q4_aggressive/q4_aggressive_policies.py'),script_sha256=digest(Path(__file__)))
    (HERE/'reviews/reviewer-matrix-development.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))


def main():
    folder=HERE/(sys.argv[1] if len(sys.argv)>1 else 'dev_valid40')
    assert folder.name not in ('dev40','dev40b','primary400')
    rows=list(csv.DictReader((folder/'results.csv').open(encoding='utf-8')));manifest=json.loads((folder/'manifest.json').read_text())
    chosen=sorted({int(r['seed']) for r in rows})[:2];counts=collections.Counter();maxerror=collections.Counter();violations=[]
    fixture_counts=pure_fixtures()
    for row in rows:
        cfg=manifest['configurations'][row['variant']]
        if (int(row['seed']) not in chosen and int(row.get('n_endpoint_clear_attempt',0))==0) or not any(cfg.get(n,0) for n in ('e_ratio','b_radius','g_ratio','r_count','h_rho','n_mass')):continue
        events=json.load(gzip.open(folder/'events'/row['variant']/(row['scene_id']+'.json.gz'),'rt'))['events'];counts['traces']+=1
        history=collections.defaultdict(list);failed=collections.defaultdict(list);pos=np.zeros(2);channel=1;cleared=set();cache={};dedicated=collections.Counter();pending_dedicated=None;opt=None
        def belief(k):
            if k not in cache or cache[k][0]!=len(history[k]):
                r=history_region(history[k]);cache[k]=(len(history[k]),r,rf(r,history[k]))
            return cache[k][1],cache[k][2]
        for e in events:
            op=e['op'];k=e.get('k')
            if op=='ablation_action' and e['kind']=='measure':pending_dedicated=k
            elif op in ('expected_optical_choice','expected_optical_execution'):
                region,(points,weights,heard)=belief(k);cells=np.asarray(e['cells']) if op.endswith('execution') else np.asarray(optical_cover_points(region['verts']))
                order,cost,full,reset=e_plan(cells,points,weights.sum(axis=(1,2)),pos,failed[k]);err=max(abs(cost-e['expected_cost']),abs(full-e['full_cost']))
                maxerror['E_cost']=max(maxerror['E_cost'],err);assert err<1e-7 and reset==e['reset_weights'],(row['variant'],row['scene_id'],k,'E',cost,e)
                counts[op]+=1
                if op.endswith('execution'):
                    assert order==e['order'];opt=dict(k=k,targets=[cells[j] for j in order if all(np.linalg.norm(cells[j]-f)>=1e-7 for f in failed[k])])
            elif op=='two_step_probe':
                region,(points,weights,heard)=belief(k);q=np.array([e['x'],e['y']]);terms=b_score(points,weights,heard,history[k],pos,q)
                if e['score_terms'] is not None:
                    err=max(abs(terms[key]-e['score_terms'][key]) for key in terms);maxerror['B_score']=max(maxerror['B_score'],err);assert err<1e-7
                candidates,pair=b_candidates(region,history[k],points,weights,cfg['b_radius'],pos)
                if pair:assert e['recovery'] and np.linalg.norm(pair[0]-q)<1e-7;counts['B_recovery']+=1
                else:
                    assert not e['recovery'] and any(np.linalg.norm(q-p)<1e-7 for p in candidates)
                    minimum=min(b_score(points,weights,heard,history[k],pos,p)['score'] for p in candidates)
                    assert terms['score']<=minimum+1e-7,(row['variant'],row['scene_id'],k,'B selection',terms['score'],minimum)
                counts['B_full_candidate_selection']+=1
            elif op in ('g_opportunity','value_probe'):
                region,(points,weights,heard)=belief(k);value=g_admission(region,history[k],points,weights,heard,pos,channel,k)
                assert value is not None
                err=max(abs(value[key]-e[key]) for key in value);maxerror['G_score']=max(maxerror['G_score'],err);assert err<1e-8;counts['G_reconstructed']+=1
                if op=='value_probe':
                    options=[]
                    for other,hist in list(history.items()):
                        if other in cleared or not any(h['result'] in ('direction','near') for h in hist):continue
                        r,(ps,ws,hs)=belief(other);val=g_admission(r,hist,ps,ws,hs,pos,channel,other)
                        if val is not None and val['score']>=cfg['g_ratio']:options.append((-val['score'],other))
                    assert options and min(options)[1]==k,(row['variant'],row['scene_id'],'G selection',k,options)
                    counts['G_full_candidate_selection']+=1
            elif op=='early_exit_choice':
                region,_=belief(k);assert e['dedicated']==dedicated[k]>=cfg['r_count'] and sum(h['result']=='direction' for h in history[k])>=2 and region['rho']<=200+1e-7;counts['R_gate']+=1
            elif op=='wide_optimistic_attempt':
                region,_=belief(k);assert region['rho']<=cfg['h_rho']+1e-7 and region['rho']>20-1e-6 and estimate(history[k]) is not None;counts['H_gate']+=1
            elif op=='endpoint_clear_attempt':
                region,(points,weights,_)=belief(k);mass=float((np.linalg.norm(points-pos,axis=1)<=20)@weights.sum(axis=(1,2)))
                assert abs(mass-e['mass'])<1e-10 and region['rho']<=320+1e-7 and sum(h['result']=='direction' for h in history[k])>=2;counts['N_mass_gate']+=1
            elif op in ('measure','clear'):
                assert k not in cleared,'physical action after clearing';q=np.array([e['x'],e['y']])
                if opt:
                    assert op=='clear' and k==opt['k'] and np.linalg.norm(q-opt['targets'].pop(0))<1e-7
                    counts['E_executed_order']+=1
                    if e['ok']:opt=None
                if op=='measure':
                    if pending_dedicated is not None:assert k==pending_dedicated;dedicated[k]+=1;pending_dedicated=None
                    history[k].append(dict(pos=q,result=e['result'],svd=e.get('svd')));channel=k
                elif e['ok']:cleared.add(k)
                else:failed[k].append(q)
                pos=q
        assert opt is None
    result=dict(status='PASS',counts=dict(counts),fixtures=fixture_counts,max_error=dict(maxerror),sample_seeds=chosen,
                scope='Fixed first two seeds across every available source/error stratum and all new arms plus every N activation trace; production positive-region and optical-cell geometry reused; RF weights/E first-hit cost/B and G full candidate selections independently reconstructed',
                results_sha256=hashlib.sha256((folder/'results.csv').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),violations=violations)
    out=HERE/'reviews'/('reviewer-audit-'+folder.name+'.json');out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--matrix':matrix_audit()
    else:main()

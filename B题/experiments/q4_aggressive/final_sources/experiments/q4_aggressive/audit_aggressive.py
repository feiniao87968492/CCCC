"""Full physical replay plus independent parsing of new local mechanisms."""
import argparse,json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'q4_local'),str(HERE.parent/'q4_transfer')]
import audit_local as local
parent=local.parent

def check(events,row,cfg):
    out=local.check_local(events,row,cfg)
    versions={k:0 for k in range(1,21)};bearings=versions.copy();dedicated=versions.copy()
    n_trials={k:[] for k in versions};failed={k:[] for k in versions}
    pos=np.zeros(2);channel=1;stop=0;used=0;token=None;n_token=None;opt=None;b_token=None
    dedicated_token=None;wide=None;last_e={};last_r={};selected=None
    counts=dict(value_probes=0,value_heard=0,n_trials=0,n_success=0,expected_optical=0,
                e_dispatch=0,r_dispatch=0,two_step_probes=0,wide_attempts=0,wide_success=0)
    for e in events:
        op=e['op'];k=e.get('k')
        if op=='g_opportunity':
            assert cfg.get('g_ratio',0)>0 and e['probability']>=.5-1e-12 and e['rho']>40
            expected=e['rho']*(1-np.exp(-e['gain']))/(5*(5+int(channel!=k)))
            assert abs(e['score']-expected)<1e-9 and e['charge']==5+int(channel!=k)
        elif op=='value_probe':
            assert token is None and e['score']>=cfg['g_ratio']-1e-12 and bearings[k]>=1
            used+=1;assert e['used']==used<=3 and e['stop_id']==stop
            token=e;counts['value_probes']+=1
        elif op=='endpoint_clear_attempt':
            assert n_token is None and cfg.get('n_mass',0)>0
            assert cfg['n_mass']-1e-12<=e['mass']<=1+1e-12 and bearings[k]>=2
            assert np.linalg.norm(pos-[e['x'],e['y']])<1e-7
            assert e['positive_version']==versions[k] and versions[k] not in n_trials[k]
            assert all(np.linalg.norm(pos-q)>1 for q in failed[k])
            n_trials[k].append(versions[k]);assert e['trial']==len(n_trials[k])<=2
            n_token=e;counts['n_trials']+=1
        elif op=='expected_optical_choice':
            assert cfg.get('e_ratio',0)>0 and e['ratio']==cfg['e_ratio']
            assert e['cells']<=48 and e['rho']<=160 and e['expected_cost']<=e['ratio']*e['rf_cost']+1e-9
            assert e['expected_cost']<=e['full_cost']+1e-9;last_e[k]=e
        elif op=='early_exit_choice':
            assert cfg.get('r_count',0)>0 and cfg['r_count']<=e['dedicated']==dedicated[k]<=8
            assert e['positive_bearings']==bearings[k]>=2 and e['rho']<=200;last_r[k]=e
        elif op=='ablation_action':
            selected=e
            if e['kind']=='measure':dedicated_token=k
        elif op=='optical_cover':
            if selected and selected['k']==k and selected['kind']=='optical':
                for proposals,name in ((last_e,'e_dispatch'),(last_r,'r_dispatch')):
                    if k in proposals and abs(proposals[k]['t']-selected['t'])<1e-9:counts[name]+=1
        elif op=='expected_optical_execution':
            assert opt is None and cfg.get('e_ratio',0)>0
            cells=np.asarray(e['cells']);assert sorted(e['order'])==list(range(len(cells))) and len(cells)<=256
            order=[j for j in e['order'] if all(np.linalg.norm(cells[j]-f)>=1e-7 for f in failed[k])]
            assert e['expected_cost']<=e['full_cost']+1e-9
            opt=dict(k=k,cells=cells,order=order,index=0);counts['expected_optical']+=1
        elif op=='two_step_probe':
            assert cfg.get('b_radius',0)>0 and b_token is None
            terms=e['score_terms']
            if terms is not None:
                assert all(np.isfinite(v) for v in terms.values()) and 0<=terms['probability']<=1+1e-12
                assert abs(terms['score']-terms['first']-terms['continuation']-terms['no_reception_cost'])<1e-7
                assert abs(terms['no_reception_cost']-78*(1-terms['probability']))<1e-7
            else:assert e['recovery']
            b_token=e;counts['two_step_probes']+=1
        elif op=='wide_optimistic_attempt':
            assert wide is None and cfg.get('h_rho',0)>0 and e['rho']<=e['limit']==cfg['h_rho']
            wide=k;counts['wide_attempts']+=1
        elif op in ('measure','clear'):
            q=np.array([e['x'],e['y']]);move=float(np.linalg.norm(q-pos))
            if token:
                assert op=='measure' and k==token['k'] and move<1e-7
                assert token['charge']==5+int(channel!=k)
                counts['value_heard']+=e['result']!='no_signal';token=None
            if b_token:
                assert op=='measure' and k==b_token['k'] and np.linalg.norm(q-[b_token['x'],b_token['y']])<1e-7;b_token=None
            if n_token:
                assert op=='clear' and k==n_token['k'] and move<1e-7
                counts['n_success']+=bool(e['ok']);n_token=None
            if wide is not None:
                assert op=='clear' and k==wide;counts['wide_success']+=bool(e['ok']);wide=None
            if opt:
                assert op=='clear' and k==opt['k'] and opt['index']<len(opt['order'])
                target=opt['cells'][opt['order'][opt['index']]]
                assert np.linalg.norm(q-target)<1e-7;opt['index']+=1
                if e['ok']:opt=None
            if dedicated_token is not None:
                assert op=='measure' and k==dedicated_token;dedicated[k]+=1;dedicated_token=None
            if move>1:stop+=1;used=0
            if op=='measure':
                channel=k
                if e['result'] in ('direction','near'):versions[k]+=1
                if e['result']=='direction':bearings[k]+=1
            elif not e['ok']:failed[k].append(q)
            pos=q
    assert all(x is None for x in (token,n_token,opt,b_token,dedicated_token,wide))
    for op,key in [('value_probe','value_probes'),('endpoint_clear_attempt','n_trials'),
                   ('expected_optical_execution','expected_optical'),('two_step_probe','two_step_probes'),
                   ('wide_optimistic_attempt','wide_attempts')]:
        assert int(row['n_'+op])==counts[key]
    out.update(counts);return out

def audit(folder):
    parent.check_mechanisms=check;parent.audit(folder)
    path=folder/'audit.json';data=parent.read(path)
    data['aggressive_audit_sha256']=parent.digest(Path(__file__))
    data['inherited_local_audit_sha256']=parent.digest(Path(local.__file__))
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);audit(ap.parse_args().folder)

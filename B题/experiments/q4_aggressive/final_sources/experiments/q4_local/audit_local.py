"""Full physical audit plus local budget, burst and mass-trial invariants."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'q4_transfer'))
import audit_transfer as parent
base_check=parent.check_mechanisms


def check_local(events,row,config):
    out=base_check(events,row,config)
    versions={k:0 for k in range(1,21)}
    mass_versions={k:[] for k in versions}
    pos=np.zeros(2);stop_id=0;used=0;burst=None;pending_step=None;pending_mass=None
    last_physical={};optical_proposals={};optical_selected=False;budget_token=None
    counts=dict(mass_attempts=0,mass_success=0,budget_probes=0,burst_actions=0,
                burst_measurements=0,burst_clears=0,cost_gated_optical_executions=0)
    for e in events:
        op=e['op'];k=e.get('k')
        if op=='budget_probe':
            assert config['stop_budget']>0 and budget_token is None
            used+=1
            assert e['stop_id']==stop_id and e['used']==used<=e['cap']==config['stop_budget']
            counts['budget_probes']+=1
            budget_token=k
        elif op=='selective_probe' and config['stop_budget']:
            assert budget_token==k
            budget_token=None
        elif op=='mass_attempt':
            assert config['mass_gate']>0 and pending_mass is None
            assert config['mass_gate']-1e-12<=e['mass']<=1+1e-12
            assert e['positive_version']==versions[k] and versions[k] not in mass_versions[k]
            mass_versions[k].append(versions[k])
            assert len(mass_versions[k])==e['trial']<=2
            pending_mass=e;counts['mass_attempts']+=1
        elif op=='local_burst_start':
            assert burst is None and config['burst_radius']>0
            last=last_physical[k]
            assert last['op']=='measure' and last['result'] in ('near','direction')
            burst=dict(k=k,ident=e['burst_id'],index=0,failed=False)
        elif op=='local_burst_action':
            assert burst is not None and k==burst['k'] and e['burst_id']==burst['ident']
            assert not burst['failed'], 'continued a burst after negative/failed physical result'
            burst['index']+=1
            assert e['index']==burst['index']<=2 and e['kind']!='optical'
            assert e['distance']<=config['burst_radius']+1e-9 and e['cap']==config['burst_radius']
            pending_step=e;counts['burst_actions']+=1
        elif op=='local_burst_end':
            assert burst is not None and e['burst_id']==burst['ident'] and k==burst['k']
            assert pending_step is None
            if e['reason']=='no_signal': assert last_physical[k]['result']=='no_signal'
            if e['reason']=='failed_clear': assert not last_physical[k]['ok']
            burst=None
        elif op=='local_optical_choice':
            assert e['cells']<=12 and e['ratio']==config['optical_ratio']
            assert e['optical_cost']<=e['ratio']*e['rf_cost']+1e-9
            optical_proposals[k]=e
        elif op=='ablation_action':
            optical_selected=(e['kind']=='optical' and k in optical_proposals and
                              abs(e['t']-optical_proposals[k]['t'])<1e-9)
        elif op=='optical_cover':
            if optical_selected:
                assert e['count']==optical_proposals[k]['cells']
                counts['cost_gated_optical_executions']+=1
            optical_selected=False
        elif op in ('measure','clear'):
            q=np.array([e['x'],e['y']]);distance=float(np.linalg.norm(q-pos))
            if pending_step is not None:
                assert k==pending_step['k']
                assert abs(distance-pending_step['distance'])<1e-7
                expected='measure' if pending_step['kind']=='measure' else 'clear'
                assert op==expected
                counts['burst_measurements' if op=='measure' else 'burst_clears']+=1
                pending_step=None
            if distance>1: stop_id+=1;used=0
            if pending_mass is not None:
                assert op=='clear' and k==pending_mass['k']
                assert np.linalg.norm(q-[pending_mass['x'],pending_mass['y']])<1e-7
                counts['mass_success']+=bool(e['ok']);pending_mass=None
            if op=='measure' and e['result'] in ('near','direction'): versions[k]+=1
            if burst is not None and k==burst['k']:
                if (op=='measure' and e['result']=='no_signal') or (op=='clear' and not e['ok']):
                    burst['failed']=True
            last_physical[k]=e;pos=q
    assert pending_mass is None and burst is None and pending_step is None and budget_token is None
    assert counts['mass_attempts']==int(row['n_mass_attempt'])
    assert counts['burst_actions']==int(row['n_burst_actions'])
    assert counts['budget_probes']==int(row['n_budget_probe'])
    out.update(counts)
    return out


def audit(folder):
    parent.check_mechanisms=check_local
    parent.audit(folder)
    path=folder/'audit.json';result=parent.read(path)
    result['local_audit_script_sha256']=parent.digest(Path(__file__))
    result['local_mechanisms']='stop budget, mass threshold/version/cap, nonrecursive two-action burst, optical cost gates'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    audit(parser.parse_args().folder)

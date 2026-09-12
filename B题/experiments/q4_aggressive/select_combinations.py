"""Freeze combination choices exclusively from audited corrected development."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import pandas as pd
from q4_aggressive_policies import config

HERE=Path(__file__).resolve().parent
FIELDS={'E':'e_ratio','B':'b_radius','G':'g_ratio','R':'r_count','H':'h_rho','N':'n_mass'}
PARAMETERS={'E1':1.,'E2':2.,'B20':20.,'B60':60.,'G075':.75,'G15':1.5,
            'R2':2,'R4':4,'H200':200.,'H400':400.,'N20':.2,'N50':.5}

def main():
    folder=HERE/'dev_valid40';target=HERE/'selection.json'
    if target.exists():raise RuntimeError('selection already locked')
    audit=json.loads((folder/'audit.json').read_text())
    digest=hashlib.sha256((folder/'results.csv').read_bytes()).hexdigest()
    assert audit['status']=='PASS' and audit['results_sha256']==digest
    data=pd.read_csv(folder/'summary_general.csv');lc=float(data[data.variant=='LC'].mean_T_over_K.iloc[0])
    families=[]
    for family in FIELDS:
        eligible=data[data.variant.str.startswith(family)&data.variant.isin(PARAMETERS)&data.eligible_all400]
        if eligible.empty:continue
        best=eligible.sort_values(['mean_T_over_K','variant']).iloc[0]
        families.append(dict(family=family,variant=best.variant,delta=float(best.mean_T_over_K-lc)))
    improving=sorted([r for r in families if r['delta']< -1e-7],key=lambda r:(r['delta'],r['variant']))[:3]
    groups=[]
    if len(improving)>=2:groups.append(improving[:2])
    if len(improving)==3:groups.extend([[improving[0],improving[2]],improving])
    combos={}
    for group in groups:
        name=''.join(r['family'] for r in group)
        kw={FIELDS[r['family']]:PARAMETERS[r['variant']] for r in group}
        combos[name]=dict(components=[r['variant'] for r in group],config=asdict(config(name,**kw)))
    record=dict(source='dev_valid40/results.csv',results_sha256=digest,
                summary_sha256=hashlib.sha256((folder/'summary_general.csv').read_bytes()).hexdigest(),
                families=families,selected_families=improving,combinations=combos,
                rule='eligible all40; mean general T/K delta vs LC < -1e-7; best per family; lexicographic ties; top3')
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()

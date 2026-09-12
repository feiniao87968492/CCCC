"""Explain paired T/K changes using additive physical costs and activation rates."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

FAMILIES={'E':['E1','E2'],'B':['B20','B60'],'G':['G075','G15'],
          'R':['R2','R4'],'H':['H200','H400'],'N':['N20','N50']}

def main(folder):
    folder=Path(folder)
    audit=json.loads((folder/'audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='PASS'
    assert audit['results_sha256']==hashlib.sha256((folder/'results.csv').read_bytes()).hexdigest()
    data=pd.read_csv(folder/'results.csv')
    mechanisms=pd.read_csv(folder/'mechanisms.csv')
    assert len(data)==audit['audited_runs']==len(mechanisms)
    costs=[];activations=[]
    for cohort,part in [('general',data[data.source_kind!='boundary']),('all',data),
                        ('stress',data[data.source_kind=='boundary'])]:
        for name,g in part.groupby('variant',sort=False):
            values=dict(walking=float((g.movement_s/g.K).mean()),
                        measurement=float((5*g.n_measure/g.K).mean()),
                        switching=float((g.switches/g.K).mean()),
                        clear_attempt=float((3*g.n_clear/g.K).mean()),
                        success=float((2*g.K/g.K).mean()))
            assert abs(sum(values.values())-g.T_over_K.mean())<1e-8
            costs.append(dict(cohort=cohort,variant=name,mean_T_over_K=float(g.T_over_K.mean()),**values))
            m=mechanisms[(mechanisms.variant==name)&mechanisms.scene_id.isin(g.scene_id)]
            row=dict(cohort=cohort,variant=name,cases=len(g))
            for col in ('e_dispatch','expected_optical','two_step_probes','value_probes',
                        'value_heard','r_dispatch','wide_attempts','wide_success','n_trials','n_success'):
                row[col]=int(m[col].sum())
                row[col+'_active_cases']=int((m[col]>0).sum())
            activations.append(row)
    costs=pd.DataFrame(costs)
    for cohort in costs.cohort.unique():
        lc=costs[(costs.cohort==cohort)&(costs.variant=='LC')].iloc[0]
        for col in ('mean_T_over_K','walking','measurement','switching','clear_attempt','success'):
            costs.loc[costs.cohort==cohort,'delta_'+col+'_vs_LC']=costs.loc[costs.cohort==cohort,col]-lc[col]
    costs.to_csv(folder/'cost_decomposition.csv',index=False)
    pd.DataFrame(activations).to_csv(folder/'activation_summary.csv',index=False)
    general=pd.read_csv(folder/'summary_general.csv').set_index('variant')
    comparisons=pd.read_csv(folder/'comparisons.csv')
    families=[]
    for family,names in FAMILIES.items():
        for name in names:
            if name not in general.index:continue
            row=general.loc[name]
            c=comparisons[(comparisons.cohort=='general')&(comparisons.control=='LC')&(comparisons.candidate==name)].iloc[0]
            families.append(dict(family=family,variant=name,eligible=bool(row.eligible_all400),
                                 mean_T_over_K=row.mean_T_over_K,delta_vs_LC=c.delta_T_over_K,
                                 ci95_low=c.ci95_low,ci95_high=c.ci95_high,delta_probes=c.delta_probes))
    pd.DataFrame(families).to_csv(folder/'family_comparisons.csv',index=False)
    print(pd.DataFrame(families).to_string(index=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder');main(ap.parse_args().folder)

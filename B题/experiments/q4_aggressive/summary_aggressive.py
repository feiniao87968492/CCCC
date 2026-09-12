"""General-case ranking with all-setting eligibility checked first."""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'q4_ablation'))
import summarize as common
LABELS={'baseline':'冻结基线','LC':'L+C','LPC':'L+P+C','previous_best':'上一轮JSO紧凑D-optimal',
        'E1':'E 预期光学比1','E2':'E 预期光学比2','B20':'B 两步20m','B60':'B 两步60m',
        'G075':'G 动态补测0.75','G15':'G 动态补测1.5','R2':'R 专用探测2次后转光学','R4':'R 专用探测4次后转光学',
        'H200':'H 乐观半径200','H400':'H 乐观半径400','N20':'N 路过试清除0.20','N50':'N 路过试清除0.50'}
LABELS.update({'GR':'G0.75+R2','GN':'G0.75+N0.20','GRN':'G0.75+R2+N0.20'})

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def eligible_rows(d):
    return d.full_success.eq(True)&d.all_certified.eq(True)&d.K.eq(d.N)&d.failure.fillna('').isin(['','None'])
def aggregate(d, general=False):
    part=d[d.source_kind!='boundary'] if general else d
    base=part[part.variant=='baseline'].set_index('scene_id')
    out=[]
    for name,g in d.groupby('variant',sort=False):
        g=g[g.source_kind!='boundary'] if general else g; g=g.set_index('scene_id').loc[base.index]
        delta=g.T_over_K-base.T_over_K
        eligible=bool(eligible_rows(d[d.variant==name]).all())
        out.append(dict(variant=name,label=LABELS.get(name,name),cases=len(g),all_cases=len(d[d.variant==name]),
                        source_total=int(g.N.sum()),cleared_total=int(g.K.sum()),
                        eligible_all400=eligible,mean_T=float(g['T'].mean()),mean_T_over_K=float(g.T_over_K.mean()),
                        mean_move=float(g.movement_s.mean()),mean_probe=float(g.n_measure.mean()),
                        failed_clears=float(g.failed_clears.mean()),delta_vs_baseline=float(delta.mean()),
                        wins=int((delta< -1e-7).sum()),losses=int((delta>1e-7).sum()),
                        p95=float(g.T_over_K.quantile(.95)),worst_delta=float(delta.max()),best_delta=float(delta.min())))
    return pd.DataFrame(out)
def main(folder):
    folder=Path(folder);d,names=common.load_checked(folder)
    audit=json.loads((folder/'audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='PASS' and audit['results_sha256']==sha(folder/'results.csv')
    assert audit['audited_runs']==audit['expected_runs']==len(d)
    for name in names:LABELS.setdefault(name,name)
    common.LABELS.update(LABELS)
    all_s=aggregate(d); gen_s=aggregate(d,True)
    stress=aggregate(d[d.source_kind=='boundary'])
    stress=stress.merge(common.uncertainty(d[d.source_kind=='boundary'],names),on='variant')
    stress['eligible_all400']=stress.variant.map(all_s.set_index('variant').eligible_all400)
    stress.to_csv(folder/'summary_stress.csv',index=False)
    gen_s=gen_s.merge(common.uncertainty(d[d.source_kind!='boundary'],names),on='variant')
    all_s=all_s.merge(common.uncertainty(d,names),on='variant')
    gen_s=gen_s.set_index('variant').loc[names].reset_index()
    all_s=all_s.set_index('variant').loc[names].reset_index()
    all_s.to_csv(folder/'summary_all.csv',index=False);gen_s.to_csv(folder/'summary_general.csv',index=False)
    strata=[]
    for (kind,error),part in d.groupby(['source_kind','error_mode']):
        s=common.aggregate(part);s['source_kind']=kind;s['error_mode']=error;strata.append(s)
    pd.concat(strata).to_csv(folder/'strata.csv',index=False)
    by_n=[]
    for n,part in d.groupby('N'):
        s=common.aggregate(part);s['N']=n;by_n.append(s)
    pd.concat(by_n).to_csv(folder/'by_source_count.csv',index=False)
    d[~eligible_rows(d)].to_csv(folder/'failures.csv',index=False)
    anchor=d[d.variant=='baseline'].set_index('scene_id');paired=[]
    for name in names:
        part=d[d.variant==name].set_index('scene_id').loc[anchor.index].copy()
        for key in common.KEYS:part['delta_'+key]=part[key]-anchor[key]
        paired.append(part.reset_index())
    paired=pd.concat(paired);paired.to_csv(folder/'paired.csv',index=False)
    paired.sort_values('delta_T_over_K',ascending=False).head(50).to_csv(folder/'worst50.csv',index=False)
    comparisons=[]
    for cohort,part in [('general',d[d.source_kind!='boundary']),('all',d),('stress',d[d.source_kind=='boundary'])]:
        for control in ('LC','LPC','previous_best'):
            if control not in names:continue
            for candidate in names:
                if candidate in ('baseline',control):continue
                two=part[part.variant.isin([control,candidate])].copy()
                two['variant']=two.variant.replace({control:'baseline'})
                interval=common.uncertainty(two,['baseline',candidate]).iloc[1]
                left=part[part.variant==control].set_index('scene_id')
                right=part[part.variant==candidate].set_index('scene_id').loc[left.index]
                comparisons.append(dict(cohort=cohort,control=control,candidate=candidate,
                    delta_T_over_K=float((right.T_over_K-left.T_over_K).mean()),
                    ci95_low=interval.ci95_delta_low,ci95_high=interval.ci95_delta_high,
                    delta_probes=float((right.n_measure-left.n_measure).mean()),note='marginal descriptive interval'))
    pd.DataFrame(comparisons).to_csv(folder/'comparisons.csv',index=False)
    interactions=[]
    for control,candidate in [('G075','G15'),('G075','GR'),('G075','GN'),('GR','GRN'),('GN','GRN')]:
        if control not in names or candidate not in names:continue
        for cohort,part in [('general',d[d.source_kind!='boundary']),('all',d),('stress',d[d.source_kind=='boundary'])]:
            two=part[part.variant.isin([control,candidate])].copy()
            two['variant']=two.variant.replace({control:'baseline'})
            interval=common.uncertainty(two,['baseline',candidate]).iloc[1]
            left=part[part.variant==control].set_index('scene_id')
            right=part[part.variant==candidate].set_index('scene_id').loc[left.index]
            interactions.append(dict(cohort=cohort,control=control,candidate=candidate,
                delta_T_over_K=float((right.T_over_K-left.T_over_K).mean()),
                ci95_low=interval.ci95_delta_low,ci95_high=interval.ci95_delta_high,
                delta_probes=float((right.n_measure-left.n_measure).mean()),note='marginal descriptive interval'))
    pd.DataFrame(interactions).to_csv(folder/'interactions.csv',index=False)
    eligible=gen_s[gen_s.eligible_all400]
    if eligible.empty:raise RuntimeError('No eligible complete arm; raw failure tables preserved')
    best=eligible.sort_values(['mean_T_over_K','variant']).iloc[0]
    base=gen_s[gen_s.variant=='baseline'].iloc[0]
    lc=gen_s[gen_s.variant=='LC'].iloc[0]
    lines=['# Q4 激进局部策略消融结果','',f'共{len(names)}组；每组{int(base.all_cases)}场。先要求全场景 eligible_all400=True，再在一般场景{int(base.cases)}场上排名。','',f'一般场景最低均值：**{best.label} {best.mean_T_over_K:.3f} s/源**。冻结基线为{base.mean_T_over_K:.3f}，LC为{lc.mean_T_over_K:.3f}。','', '## 全部策略（一般场景）','', '|策略|全场景资格|一般T/K|行走|探测|相对基线|胜/负|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in gen_s.iterrows():lines.append(f"|{r.label}|{'是' if r.eligible_all400 else '否'}|{r.mean_T_over_K:.3f}|{r.mean_move:.2f}|{r.mean_probe:.2f}|{100*(1-r.mean_T_over_K/base.mean_T_over_K):+.3f}%|{r.wins}/{r.losses}|")
    new=eligible[~eligible.variant.isin(['baseline','LC','LPC','previous_best'])].sort_values(['mean_T_over_K','variant'])
    if len(new):
        winner=new.iloc[0];all_winner=all_s[all_s.variant==winner.variant].iloc[0]
        stress_winner=stress[stress.variant==winner.variant].iloc[0]
        lines += ['', '## 新候选与尾部','',f'新候选最低均值为 {winner.label}：一般场景{winner.mean_T_over_K:.4f} s/源，全场景{all_winner.mean_T_over_K:.4f} s/源。',
                  f'单列边界压力组{stress_winner.cases}场：{stress_winner.mean_T_over_K:.4f} s/源，相对基线差{stress_winner.delta_vs_baseline:+.4f}，配对区间[{stress_winner.ci95_delta_low:.4f}, {stress_winner.ci95_delta_high:.4f}]。',
                  f'一般场景相对基线配对差区间[{winner.ci95_delta_low:.4f}, {winner.ci95_delta_high:.4f}] s/源；胜/负 {winner.wins}/{winner.losses}，p95={winner.p95:.3f}。',
                  '最低观测均值不证明唯一最优；与LC/LPC/上一轮JSO的同场差及区间见comparisons.csv。']
    lines += ['', '## 资格与限制','',f'本批每组{int(base.all_cases)}场均须 `full_success=True`、K=N、`all_certified=True` 且无failure；边界组不参与一般场景排名。',
              '所有失败清除和探测均计入耗时；一般场景均值是设置等权的 mean(T/K)，不使用历史517 s作为分母。',
              '新局部方案保持TRI25半径1950和全域tour规则；previous_best附加对照保留自身1900半径/center设置。',
              f'本批{d.seed.nunique()}个独立种子块；区间按整块重采样且按设置等权，主比较报告Holm校正，机制比较为描述性区间。',
              '边界压力组与其他组共享部分种子；单列报告不表示与一般场景统计独立。',
              '预期分数不是校准成功概率。全量清除为本批离线证据；冻结基线和官方入口不替换。无效试跑与撤销选择见../invalid-runs.md。',
              '审查状态以../reviews/内当前结果审查文件为准，早期BLOCKED评审及后续修正记录全部保留。']
    (folder/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    render_table(gen_s,folder,'general',best.variant)
    for cohort,table in [('all',all_s),('stress',stress)]:
        render_table(table,folder,cohort,best.variant)
    print(gen_s[['variant','eligible_all400','mean_T_over_K','mean_move','mean_probe']].to_string(index=False))

def render_table(table,folder,cohort,highlight):
    highlight=table[table.eligible_all400].sort_values(['mean_T_over_K','variant']).iloc[0].variant
    base=table[table.variant=='baseline'].iloc[0]
    title={'general':'一般场景','all':'全部场景','stress':'边界压力场景'}[cohort]
    font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc');height=1.5+.42*(len(table)+1)
    fig=plt.figure(figsize=(16,height),dpi=180)
    ax=fig.add_axes([.025,.03,.95,1-1.2/height-.03]);ax.axis('off')
    cells=[[r.label,f'{r.mean_T:.1f}',f'{r.mean_T_over_K:.2f}',f'{r.mean_move:.1f}',f'{r.mean_probe:.2f}'] for _,r in table.iterrows()]
    tab=ax.table(cellText=cells,colLabels=['策略','总耗时/场(s)','T/K(s/源)','行走/场(s)','探测/场'],colWidths=[.46,.14,.14,.14,.12],cellLoc='right',bbox=[0,0,1,1]);tab.auto_set_font_size(False)
    for (i,j),c in tab.get_celld().items():
        c.visible_edges='B';c.set_edgecolor('#ddd');c.get_text().set_fontproperties(font);c.get_text().set_fontsize(10.5)
        if j==0:c.get_text().set_ha('left')
        if i>0 and table.iloc[i-1].variant==highlight:c.get_text().set_color('#12633f');c.get_text().set_fontweight('bold')
    fig.text(.025,1-.15/height,f'Q4 激进局部消融：{title} {int(base.cases)} 场；T/K 优先',fontproperties=font,fontsize=18,va='top')
    complete=bool(table.eligible_all400.all())
    subtitle=f'每组清除 {int(base.source_total)} 个源；全场景清除与认证均通过；绿色为本表最低 T/K' if complete else '存在未通过全场景清除与认证的策略，详见配套 CSV'
    fig.text(.025,1-.65/height,subtitle,fontproperties=font,fontsize=11,color='#555555',va='top')
    for ext in ('png','pdf'):fig.savefig(folder/f'ablation_table_{cohort}.{ext}',bbox_inches='tight')
    plt.close(fig)
    source=folder/f'summary_{cohort}.csv'
    (folder/f'ablation_table_{cohort}.csv').write_bytes(source.read_bytes())
    meta={'source':source.name,'source_sha256':sha(source),'script_sha256':sha(__file__),'ranking':'all-setting eligibility then general non-boundary settings','highlight':highlight,'highlight_basis':'minimum eligible mean within the displayed cohort; primary ranking remains general'}
    (folder/f'ablation_table_{cohort}.meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folders',nargs='+')
    for f in ap.parse_args().folders:main(f)

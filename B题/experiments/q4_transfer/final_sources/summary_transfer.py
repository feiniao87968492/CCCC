"""Transfer-specific paired summaries and screenshot-style figures."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/q4_ablation'))
import summarize as common

LABELS={
 'baseline':'冻结基线 TRI25 + V4','previous_best':'上一轮最优（附加对照）',
 'J':'J 源中心联合路线','S':'S 选择性顺路探测','O':'O 测向交点试清除',
 'JS':'J + S','JO':'J + O','SO':'S + O','JSO':'J + S + O',
 'insert80':'路线插入 ≤80 m','insert200':'路线插入 ≤200 m','insert400':'路线插入 ≤400 m',
 'aligned':'定位点面向后续覆盖站','doptimal':'D-optimal 信息增益选点',
 'bracket':'无信号后对称恢复探测','optical2':'提前光学覆盖 ≤2 格','optical4':'提前光学覆盖 ≤4 格',
 'short_clear':'认证清除点缩短路程','JSO_p50':'JSO 接收门槛 0.50','JSO_p85':'JSO 接收门槛 0.85',
 'JSO_r120':'JSO 试清除半径 120 m','JSO_r160':'JSO 试清除半径 160 m',
 'JSO_compact':'JSO 外圈 1900 m','JSO_outer1980':'JSO 外圈 1980 m',
 'S_doptimal':'S + D-optimal','SO_doptimal':'S + O + D-optimal',
 'S_dopt_short':'S + D-optimal + 短清除','JSO_compact_dopt':'JSO + 外圈 1900 m + D-optimal',
}
common.LABELS.update(LABELS)


def render(summary,folder,full=False):
    best=summary[summary.failures==0].sort_values('mean_T_over_K').iloc[0].variant
    selected=list(summary.variant) if full else list(dict.fromkeys([
        'baseline','previous_best','JSO',best,'S','O','doptimal','aligned','S_dopt_short','optical4','insert80']))
    selected=[n for n in selected if n in set(summary.variant)]
    tab=summary.set_index('variant').loc[selected]
    prop=common.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
    fig,ax=common.plt.subplots(figsize=(17,2.5+.47*len(tab)),dpi=180)
    ax.set_axis_off();fig.patch.set_facecolor('white')
    cases=int(tab.iloc[0].cases);sources=int(tab.iloc[0].source_total)
    fig.text(.025,.968,f'Q4 扩展消融：每组 {cases} 个相同场景，{sources} 个源',fontproperties=prop,fontsize=20,va='top')
    subtitle=(f'所示各组均清除 {sources}/{sources}（100%），完成全部场景认证'
              if (tab.full_success==cases).all() else '各组完成率及失败场景详见 summary.csv')
    fig.text(.025,.916,subtitle,fontproperties=prop,fontsize=12,color='#555555',va='top')
    cells=[[r.label,f'{r.mean_T:.2f} s',f'{r.mean_T_over_K:.2f} s',
            f'{r.mean_movement_s:.2f} s',f'{r.mean_n_measure:.2f}'] for _,r in tab.iterrows()]
    table=ax.table(cellText=cells,colLabels=['策略','平均每场总耗时','平均清除一个','平均行走时间','平均探测次数'],
       colWidths=[.40,.16,.16,.16,.12],cellLoc='right',colLoc='right',bbox=[0,.035,1,.87])
    table.auto_set_font_size(False)
    for (row,col),cell in table.get_celld().items():
        cell.visible_edges='B';cell.set_edgecolor('#dadada');cell.set_linewidth(.65);cell.PAD=.02
        cell.get_text().set_fontproperties(prop);cell.get_text().set_fontsize(11.5)
        if col==0: cell.get_text().set_ha('left')
        if row==0: cell.get_text().set_color('#777777')
        elif tab.index[row-1]==best:
            cell.get_text().set_fontweight('bold');cell.get_text().set_color('#12633f')
    fig.text(.025,.025,'每源耗时为各场 T/K 的均值。离线配对实验；压力组与逐场退化见报告；冻结基线未替换。',
             fontproperties=prop,fontsize=10,color='#666666')
    fig.subplots_adjust(left=.025,right=.98,top=.915,bottom=.055)
    stem='ablation_table_all' if full else 'ablation_table'
    for ext in ('png','pdf'): fig.savefig(folder/f'{stem}.{ext}',facecolor='white')
    common.plt.close(fig)
    meta=dict(source='summary.csv',source_sha256=common.sha(folder/'summary.csv'),script_sha256=common.sha(__file__),
              variants=selected,claim_level='offline exploratory comparison; baseline not adopted')
    (folder/f'{stem}.meta.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')


def factorial(df,folder):
    names=['baseline','J','S','O','JS','JO','SO','JSO']
    if not set(names).issubset(set(df.variant)): return
    tab=df[df.variant.isin(names)].pivot(index='scene_id',columns='variant',values='T_over_K')
    pairs={'J':[('baseline','J'),('S','JS'),('O','JO'),('SO','JSO')],
           'S':[('baseline','S'),('J','JS'),('O','SO'),('JO','JSO')],
           'O':[('baseline','O'),('J','JO'),('S','SO'),('JS','JSO')]}
    rows=[]
    for factor,comparisons in pairs.items():
        deltas=[]
        for off,on in comparisons:
            delta=(tab[on]-tab[off]).mean();deltas.append(delta)
            rows.append(dict(factor=factor,off=off,on=on,mean_delta_T_over_K=delta))
        rows.append(dict(factor=factor,off='average_over_other_factors',on=factor,mean_delta_T_over_K=np.mean(deltas)))
    pd.DataFrame(rows).to_csv(folder/'factorial_effects.csv',index=False)


def main(folder):
    df,names=common.load_checked(folder)
    summary=common.aggregate(df).merge(common.uncertainty(df,names),on='variant')
    counters=['n_selective_probe','n_optimistic_attempt','n_early_optical_proposals']
    summary=summary.merge(df.groupby('variant')[counters].mean().add_prefix('mean_'),on='variant')
    if (folder/'mechanisms.csv').exists():
        mechanisms=pd.read_csv(folder/'mechanisms.csv')
        cols=['optimistic_success','selective_heard','optical_actions','optical_candidate_cells',
              'optical_actions_within_early_threshold']
        cols=[c for c in cols if c in mechanisms]
        summary=summary.merge(mechanisms.groupby('variant')[cols].mean().add_prefix('mean_'),on='variant')
    summary=summary.set_index('variant').loc[names].reset_index()
    summary.to_csv(folder/'summary.csv',index=False)
    summary.to_json(folder/'summary.json',orient='records',indent=2,force_ascii=False)
    strata=[]
    for (kind,error),part in df.groupby(['source_kind','error_mode']):
        s=common.aggregate(part);s['source_kind']=kind;s['error_mode']=error;strata.append(s)
    strata=pd.concat(strata);strata.to_csv(folder/'strata.csv',index=False)
    by_n=[]
    for n,part in df.groupby('N'):
        s=common.aggregate(part);s['N']=n;by_n.append(s)
    pd.concat(by_n).to_csv(folder/'by_source_count.csv',index=False)
    base=df[df.variant=='baseline'].set_index('scene_id');paired=[]
    for name in names:
        part=df[df.variant==name].set_index('scene_id').loc[base.index].copy()
        for key in common.KEYS: part['delta_'+key]=part[key]-base[key]
        paired.append(part.reset_index())
    paired=pd.concat(paired);paired.to_csv(folder/'paired.csv',index=False)
    paired.sort_values('delta_T_over_K',ascending=False).head(50).to_csv(folder/'worst50.csv',index=False)
    df[~df.full_success].to_csv(folder/'failures.csv',index=False);factorial(df,folder)
    best=summary[summary.failures==0].sort_values('mean_T_over_K').iloc[0]
    baseline=summary[summary.variant=='baseline'].iloc[0]
    best_strata=strata[strata.variant==best.variant]
    scenario_lines=['| 场景 | 误差 | 每组场数 | 最佳均值候选 T/K | 相对基线改善 |','|---|---|---:|---:|---:|']
    for _,r in best_strata.iterrows():
        scenario_lines.append(f'| {r.source_kind} | {r.error_mode} | {int(r.cases)} | {r.mean_T_over_K:.2f} s | {r.improvement_pct:+.2f}% |')
    jso=summary[summary.variant=='JSO']
    leading_note=''
    if {'JSO_compact','JSO_compact_dopt'}.issubset(names):
        comparison=df[df.variant.isin(['JSO_compact','JSO_compact_dopt'])].copy()
        comparison['variant']=comparison.variant.replace({'JSO_compact':'baseline'})
        result=common.uncertainty(comparison,['baseline','JSO_compact_dopt']).iloc[1]
        means=summary.set_index('variant').mean_T_over_K
        delta=means['JSO_compact_dopt']-means['JSO_compact']
        result['anchor']='JSO_compact';result['mean_delta_T_over_K']=delta
        result.to_frame().T.to_csv(folder/'leading_comparison.csv',index=False)
        leading_note=(f'与JSO+1900 m外圈相比，再加D-optimal的均值差为 {delta:.3f} s/源，'
                      f'95%种子块区间 [{result.ci95_delta_low:.3f}, {result.ci95_delta_high:.3f}]。'
                      '这是事后描述性比较；区间跨零时，不能证明D-optimal加成更优。')
    review_note='独立审查状态以 ../reviews/ 中对应批次文件为准。'
    review_json=HERE/'reviews/sample-geometry-audit.json'
    if review_json.exists() and json.loads(review_json.read_text(encoding='utf-8'))['result_sha256']==common.sha(folder/'results.csv'):
        if (HERE/'reviews/primary-validation.md').exists():
            review_note='主实验独立审查：PASS_WITH_WARNINGS，见 ../reviews/primary-validation.md；完整事件审计和独立几何抽样均通过。'
    jso_note=(f'本批 Q4 JSO 为 {jso.iloc[0].mean_T_over_K:.2f} s/源，改善 {jso.iloc[0].improvement_pct:+.2f}%，'
              f'行走改善 {jso.iloc[0].movement_reduction_pct:+.2f}%，探测改善 {jso.iloc[0].probe_reduction_pct:+.2f}%。'
              if len(jso) else '本批仅检查新增组合，JSO见dev40。')
    boundary=best_strata[best_strata.source_kind=='boundary']
    boundary_note=(f'边界外向压力组相对基线改善 {boundary.iloc[0].improvement_pct:+.3f}%。'
                   if len(boundary) else '')
    if len(boundary) and boundary.iloc[0].improvement_pct<0:
        boundary_note+=' **该组退化，不能声称所有重要场景均改善。**'
    eligible=[]
    for _,r in summary.iterrows():
        group=strata[strata.variant==r.variant]
        eligible.append(dict(variant=r.variant,min_stratum_improvement_pct=group.improvement_pct.min(),
                             all_strata_mean_nonworse=bool((group.improvement_pct>=-1e-9).all()),
                             both_walk_and_probes_improved=bool(r.movement_reduction_pct>0 and r.probe_reduction_pct>0)))
    pd.DataFrame(eligible).to_csv(folder/'tradeoffs.csv',index=False)
    report=f'''# Q4 扩展消融结果

完成 {len(names)} 组 × {int(baseline.cases)} 场，共 {len(df)} 次运行；每组 {int(baseline.source_total)} 个源。
失败场数共 {int(summary.failures.sum())}。平均 T/K 最低的完成率合格候选为 **{best.label}**：
{baseline.mean_T_over_K:.4f} → {best.mean_T_over_K:.4f} s/源，降低 {best.improvement_pct:.3f}%。
行走降低 {best.movement_reduction_pct:.3f}%，探测降低 {best.probe_reduction_pct:.3f}%。
{boundary_note}

## 与Q3参考的关系

Q3 JSO 的420场 T/K为254.053210 s，源自 ../../q3_ablation/evaluation/summary.csv。
Q3是全向源、七站发现；Q4含定向源、25站发现，254 s不可直接用作Q4同条件对照。
{jso_note}
Q4原冻结100场均值517.584293 s；本批分布不同，所有百分比均使用本批重跑基线配对。
previous_best是上一轮最优的同场重跑，只作附加对照。Q4已有联合规划和试清除，J/S/O是增量迁移。

## 对比表

{common.markdown_table(summary)}

平均清除一个源为mean(T/K)；sum(T)/sum(K)另列summary.csv。全部失败试清除与换频也计费。
算法族定义与参数见 ../README.md 和 ../design.md。

## 分组与不确定性

{chr(10).join(scenario_lines)}

负改善率表示退化；综合均值改善不保证压力组改善。配对胜/负/平为
{int(best.paired_wins)}/{int(best.paired_losses)}/{int(best.paired_ties)}。
最差退化 {best.worst_delta_T_over_K:.3f} s/源（{best.worst_scene}）；p95 T/K为 {best.p95_T_over_K:.3f} s。
平均配对差的种子块bootstrap 95%区间 [{best.ci95_delta_low:.3f}, {best.ci95_delta_high:.3f}] s/源。
本批 {df.seed.nunique()} 个独立种子块；同一种子的多种设置一起重采样，估计场景设置等权均值。
主实验400设置为200个mixed/endpoint，加全定向、全向、边界外向、混合smooth各50，只有200个独立种子块。
区间是单比较区间；另附种子块符号翻转及Holm校正，前者假设零假设下块差值近似符号对称。
{leading_note}
组合按开发集选定，主实验保留全部28组；最终冠军仍为矩阵内选择，不能视为全局或总体最优。
按真实源数事后分层见by_source_count.csv；算法不能访问源数、位置、类型或场景标签。

## 证据

- results.csv / events/：全部逐场与逐动作记录；failures.csv保留失败行。
- manifest.json / source_snapshot/ / completion.json：参数、启动时源码快照、完成检查。
- audit.json / mechanisms.csv：自动核验与实际机制计数；自动核验不替代独立审查。
- paired.csv / strata.csv / by_source_count.csv / worst50.csv：配对、分组与尾部退化。
- factorial_effects.csv：每个J/S/O因子在其他因子组合下的边际效果。
- ablation_table.png / ablation_table_all.png：精选/完整对比图，附PDF和数据哈希。
- ../reviews/：实现前、开发集及主实验独立审查，以实际存在的审查文件结论为准。

optical2未触发时不能据此证明有效；early_optical日志是候选提议，实际执行见mechanisms.csv。
专门定位上限8不含S顺路补测。所有25站未知频道证书或已观测16频道证书、完整光学兜底保留。
dev40的previous_best清单漏字段由provenance-correction.json补正，原清单不覆盖，主实验前修正。
本结果为离线探索性比较，不更换冻结基线，也不代填官方模拟器成绩。
{review_note}
'''
    (folder/'report.md').write_text(report,encoding='utf-8')
    render(summary,folder);render(summary,folder,True)
    print(summary[['variant','full_success','mean_T_over_K','mean_movement_s','mean_n_measure',
                   'improvement_pct','ci95_delta_low','ci95_delta_high','holm_p']].to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folders',nargs='+',type=Path)
    for folder in parser.parse_args().folders: main(folder)

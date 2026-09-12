"""Paired local-decision experiments; all failures and subgroups remain visible."""
import argparse
import json
from pathlib import Path
import sys
import pandas as pd
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/q4_ablation'))
import summarize as common
LABELS={
 'baseline':'冻结基线 TRI25 + V4','previous_best':'上轮 JSO + 紧凑外圈 + D-optimal',
 'S_all':'S 不限制单站补测数量','L30':'L 局部完成代价（惩罚30 s）','L90':'L 局部完成代价（惩罚90 s）',
 'P1':'P 每站最多补测1次','P2':'P 每站最多补测2次','F60':'F 连续处理当前源（60 m）',
 'F120':'F 连续处理当前源（120 m）','C1':'C 局部光学代价比 ≤1.0',
 'C15':'C 局部光学代价比 ≤1.5','M50':'M 后验质量试清除（0.50）','M75':'M 后验质量试清除（0.75）',
 'LC':'L + C','PC':'P + C','LPC':'L + P + C',
}
common.LABELS.update(LABELS)


def render(summary,folder):
    font=common.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
    fig,ax=common.plt.subplots(figsize=(17,2.5+.47*len(summary)),dpi=180)
    ax.set_axis_off();fig.patch.set_facecolor('white')
    first=summary.iloc[0]
    fig.text(.025,.968,f'Q4 局部策略消融：每组 {int(first.cases)} 场，{int(first.source_total)} 个源',
             fontproperties=font,fontsize=20,va='top')
    complete=bool((summary.full_success==summary.cases).all())
    subtitle=('各组清除率与场景认证完成率均为100%；新局部策略保持TRI25和全域规划方法'
              if complete else '完成率与失败场景详见完整报告')
    fig.text(.025,.925,subtitle,fontproperties=font,fontsize=12,color='#555555',va='top')
    cells=[[r.label,f'{r.mean_T:.2f} s',f'{r.mean_T_over_K:.2f} s',f'{r.mean_movement_s:.2f} s',
            f'{r.mean_n_measure:.2f}'] for _,r in summary.iterrows()]
    table=ax.table(cellText=cells,colLabels=['策略','平均每场总耗时','平均清除一个','平均行走时间','平均探测次数'],
                   colWidths=[.40,.16,.16,.16,.12],cellLoc='right',colLoc='right',bbox=[0,.03,1,.89])
    table.auto_set_font_size(False)
    best=summary[(summary.failures==0)&(~summary.variant.isin(['baseline','previous_best','S_all']))].sort_values('mean_T_over_K')
    best=best.iloc[0].variant if len(best) else None
    for (row,col),cell in table.get_celld().items():
        cell.visible_edges='B';cell.set_edgecolor('#d8d8d8');cell.set_linewidth(.65);cell.PAD=.02
        cell.get_text().set_fontproperties(font);cell.get_text().set_fontsize(11.5)
        if col==0: cell.get_text().set_ha('left')
        if row==0: cell.get_text().set_color('#777777')
        elif summary.iloc[row-1].variant==best:
            cell.get_text().set_color('#12633f');cell.get_text().set_fontweight('bold')
    fig.text(.025,.025,'L：局部探测选点；P：单站补测预算；C：局部光学清除选择。离线配对均值；退化与不确定性见报告。',
             fontproperties=font,fontsize=10,color='#666666')
    fig.subplots_adjust(left=.025,right=.98,top=.92,bottom=.055)
    for ext in ('png','pdf'): fig.savefig(folder/f'ablation_table_all.{ext}',facecolor='white')
    common.plt.close(fig)
    meta=dict(source='summary.csv',source_sha256=common.sha(folder/'summary.csv'),script_sha256=common.sha(__file__),
              variants=list(summary.variant),highlight='lowest observed mean among new local candidates',
              claim_level='offline exploratory analysis; no baseline adoption')
    (folder/'ablation_table_all.meta.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')


def main(folder):
    df,names=common.load_checked(folder)
    summary=common.aggregate(df).merge(common.uncertainty(df,names),on='variant')
    counters=['n_mass_attempt','n_budget_probe','n_burst_actions','n_local_optical_proposals']
    summary=summary.merge(df.groupby('variant')[counters].mean().add_prefix('mean_'),on='variant')
    if (folder/'mechanisms.csv').exists():
        mechanisms=pd.read_csv(folder/'mechanisms.csv')
        columns=['mass_success','burst_measurements','burst_clears','cost_gated_optical_executions',
                 'optimistic_success','selective_heard']
        summary=summary.merge(mechanisms.groupby('variant')[columns].mean().add_prefix('mean_'),on='variant')
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
    df[~df.full_success].to_csv(folder/'failures.csv',index=False)
    comparisons=[]
    for anchor,challenger in [('S_all','P1'),('S_all','P2'),('L30','LC'),('C15','LC'),
                               ('C15','PC'),('P1','PC'),('LC','LPC'),('PC','LPC'),
                               ('previous_best','LC'),('previous_best','PC'),('previous_best','LPC')]:
        if not {anchor,challenger}.issubset(names): continue
        part=df[df.variant.isin([anchor,challenger])].copy()
        part['variant']=part.variant.replace({anchor:'baseline'})
        ci=common.uncertainty(part,['baseline',challenger]).iloc[1]
        left=df[df.variant==anchor].set_index('scene_id')
        right=df[df.variant==challenger].set_index('scene_id').loc[left.index]
        comparisons.append(dict(anchor=anchor,challenger=challenger,mean_delta_T_over_K=(right.T_over_K-left.T_over_K).mean(),
                                ci95_low=ci.ci95_delta_low,ci95_high=ci.ci95_delta_high,
                                delta_probes=(right.n_measure-left.n_measure).mean(),
                                note='descriptive selected comparison; marginal interval'))
    pd.DataFrame(comparisons).to_csv(folder/'local_comparisons.csv',index=False)
    candidates=summary[(summary.failures==0)&(~summary.variant.isin(['baseline','previous_best','S_all']))]
    best=candidates.sort_values('mean_T_over_K').iloc[0];baseline=summary[summary.variant=='baseline'].iloc[0]
    subgroup=strata[strata.variant==best.variant]
    lines=['| 场景 | 误差 | 场数 | 最佳局部候选 T/K | 相对基线改善 |','|---|---|---:|---:|---:|']
    for _,r in subgroup.iterrows():
        lines.append(f'| {r.source_kind} | {r.error_mode} | {int(r.cases)} | {r.mean_T_over_K:.3f} s | {r.improvement_pct:+.3f}% |')
    losses=subgroup[subgroup.improvement_pct<0]
    stress=('所有本次场景类型均值均改善；这不是逐场或总体保证。' if losses.empty else
            '存在场景类型均值退化：'+', '.join(f'{r.source_kind}/{r.error_mode} {(-r.improvement_pct):.3f}%' for _,r in losses.iterrows())+'。')
    previous_note=''
    for r in comparisons:
        if r['anchor']=='previous_best' and r['challenger']==best.variant:
            previous_note=(f'相对上一轮最优同场重跑，最佳局部候选的T/K差为{r["mean_delta_T_over_K"]:+.3f} s/源，'
                           f'95%种子块区间[{r["ci95_low"]:.3f}, {r["ci95_high"]:.3f}]；区间跨零时不能证明两者总体均值不同。'
                           '局部方案没有替换全域路线或缩小外圈。')
    detail_lines=['| 成本或操作 | 冻结基线均值 | 最佳局部候选均值 |','|---|---:|---:|']
    for key,label in [('mean_discovery_measure','首次发现前探测'),('mean_refine_measure','发现后探测'),
                      ('mean_failed_clears','失败清除'),('mean_n_optical_fallback','完整光学覆盖调用'),
                      ('mean_n_budget_probe','预算补测'),('mean_n_replan','全域重规划')]:
        if key in summary:
            detail_lines.append(f'| {label} | {baseline[key]:.3f} | {best[key]:.3f} |')
    review_note='此输出尚未绑定独立结果审查；仅提供探索性汇总。'
    review_name=('primary-validation.md' if folder.name=='primary400' else
                 'development-validation.md' if folder.name in ('dev40','dev_combinations40') else None)
    if review_name and (HERE/'reviews'/review_name).exists():
        review_note=(f'独立审查：[PASS_WITH_WARNINGS](../reviews/{review_name})。'
                     '具体抽查范围和限制以审查文件为准；最终分析源码与结果哈希见../evidence_manifest.json。')
    interpretation=''
    if folder.name=='primary400':
        interpretation='''## 组件取舍与建议

LPC是本轮新局部候选的最低观测均值。上一轮方案同场均值513.489 s仍略低，
但其边界组退化0.697%；LPC边界组改善5.339%，五类场景的平均探测次数也均下降。
两者均值差的区间跨零，不能宣称LPC总体优于上一轮方案。

- **强调综合局部效率：LPC**。多数探测节省来自发现后的精定位阶段；失败清除从5.388增至14.650次/场，其代价已完整计入。
- **优先少探测：LC**。每场285.103次，略少于LPC的286次；加入P1后T/K再降4.279 s，但探测增加0.898次/场。
- **较小改动：C15**。T/K改善2.082%，行走改善2.740%，探测改善2.116%；379胜/21负，最差退化26.940 s/源。
- **P预算的独立贡献有限**。P1/P2比不限预算的S_all少测3.725/1.285次，但仍比冻结V4多测；P1对S_all的T/K差区间跨零。组合收益不能全部归因于P。
- **F/M在本轮无平均耗时收益**。F60基本持平，F120、M50、M75略差。M50实际764/2428次试清除成功，M75为702/2033；质量门槛不是50%/75%的成功率保证。

上述组件比较为描述性配对结果，完整11项差值及区间见local_comparisons.csv。
'''
    report=f'''# Q4 局部策略消融结果

完成 {len(names)} 组×{int(baseline.cases)}个配对设置，共{len(df)}次运行；每组{int(baseline.source_total)}个源。
失败场数共{int(summary.failures.sum())}。新局部候选中最低观测均值为 **{best.label}**：
冻结算法同场重跑 {baseline.mean_T_over_K:.4f} → {best.mean_T_over_K:.4f} s/源，改善{best.improvement_pct:+.3f}%。
行走改善{best.movement_reduction_pct:+.3f}%，探测改善{best.probe_reduction_pct:+.3f}%。{stress}
{previous_note}

## 完整比较

{common.markdown_table(summary)}

mean(T/K)是各场比值均值，sum(T)/sum(K)另列summary.csv；总时间包含所有失败清除和换频。
上轮最优是JSO_compact_dopt的同场重跑，作为附加对照。所有百分比锚定本次冻结算法。
旧517/514 s分属其他种子和场景，不能用来计算这一批的改善率。

{interpretation}

## 算法与局部机制

- L30/L90：最小化当前点→探测点→源的局部代价，加未完成定位惩罚；不使用后续全域路线项。
- P1/P2：保留S的准入条件，每个实际停车点最多补测1/2次；S_all对照用于隔离预算本身。
- F60/F120：最多追加两次同源决策，距离限60/120 m；实际无信号或失败清除后停止，不嵌套光学清除。
- C1/C15：比较完整光学覆盖路线成本与一次探测后清除的代价代理，阈值1.0/1.5。
- M50/M75：用后验空间质量选择试清除点，每源最多2次、每个正观测版本最多1次；质量不代表校准概率。
- LC/PC/LPC：开发集选定L30、P1、C15的组合。初始13组全部保留，新增3组在主实验前锁定。

新局部策略都保持TRI25外圈1950 m和冻结V4全域规划规则，实际路线会随局部决策变化。
正观测多边形、25站/16频道缺失证明、完整光学兜底保留；负RF不裁剪位置可行域。
专门定位上限8不含顺路P/S探测。光学提议数不等于实际执行数；详见mechanisms.csv。

{chr(10).join(detail_lines)}

这里的“发现后探测”包括专门定位和顺路补测。更多失败清除可能换来更少RF探测和行走；
均值已计入每次失败3 s的实际代价，不按试清除成功率单独排名。

## 分组与尾部

{chr(10).join(lines)}

候选配对胜/负/平：{int(best.paired_wins)}/{int(best.paired_losses)}/{int(best.paired_ties)}。
最差退化 {best.worst_delta_T_over_K:.3f} s/源（{best.worst_scene}），p95={best.p95_T_over_K:.3f} s/源。
平均配对差95%种子块bootstrap区间[{best.ci95_delta_low:.3f}, {best.ci95_delta_high:.3f}] s/源。
本批有{df.seed.nunique()}个独立种子块；同种子的场景设置整块抽样，按设置等权计算均值。
本批各类型的设置数见上方分组表；开发集用于选组合，主实验使用未参与开发的新种子。
主表比较采用Holm校正的块符号翻转检验，假设零假设下块差值近似符号对称。
置信区间为单比较区间，选出最低均值不证明唯一胜者。local_comparisons.csv是机制间描述性比较。
按真实N分层只用于事后分析，运行策略不得读取真值N、位置、朝向或源类型。

## 复现与审查

原始数据results.csv/events；哈希manifest.json/source_snapshot/completion.json；
自动事件审计audit.json及mechanisms.csv；配对paired.csv；分组strata.csv/by_source_count.csv；
失败failures.csv；最差50行worst50.csv。完整对比图ablation_table_all.png，附PDF及数据哈希。
独立审查见../reviews/；自动审计不等同独立几何验证。
主实验审查独立复算P/F/M事件关联、统计区间及有限样本的质量评分和光学路线成本；
其中正观测多边形与光学覆盖格复用原实现，RF备选代价代理未逐动作独立重建。
这是一轮离线探索性消融，冻结基线不替换，不填写官方模拟器成绩。
{review_note}
'''
    (folder/'report.md').write_text(report,encoding='utf-8')
    render(summary,folder)
    print(summary[['variant','full_success','mean_T_over_K','mean_movement_s','mean_n_measure','improvement_pct']].to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folders',nargs='+',type=Path)
    for folder in parser.parse_args().folders: main(folder)

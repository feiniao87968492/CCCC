"""Paired summaries, seed-block uncertainty and screenshot-style Q4 tables."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd

LABELS = {
    'baseline': '冻结基线 TRI25 + V4',
    'nearest': 'A 就近任务调度',
    'reuse': 'B 覆盖站复用定位',
    'early160': 'C 提前清除（160 m）',
    'nearest_reuse': 'A + B',
    'nearest_early': 'A + C',
    'reuse_early': 'B + C',
    'full': 'A + B + C',
    'probe_off': '关闭已发现频道顺路探测',
    'probe_strict': '收紧顺路探测门槛',
    'probe_loose': '放宽顺路探测门槛',
    'early120': '提前清除（120 m）',
    'early220': '提前清除（220 m）',
    'center_route': '按源中心规划联合路线',
    'finish_source': '选中一个源后连续清除',
    'compact': '仅外圈半径 1950→1900 m',
    'full_compact': 'A + B + C + 外圈微调',
    'every_stop': 'A + B + C，每次停车扫未知频道',
    'proxy_compact': '源中心路线 + 外圈微调',
    'proxy_reuse_early_compact': '源中心路线 + B + C + 外圈微调',
}
KEYS = ['T','T_over_K','move_m','movement_s','n_measure','discovery_measure',
        'refine_measure','discovery_no_signal','refine_no_signal','failed_clears',
        'n_clear','n_optical_fallback','measure_s','clear_s','after_last_clear_s','switches']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_checked(folder):
    df = pd.read_csv(folder/'results.csv')
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    scenarios = json.loads((folder/'scenarios.json').read_text(encoding='utf-8-sig'))
    completion = json.loads((folder/'completion.json').read_text(encoding='utf-8-sig'))
    names = list(manifest['configurations'])
    assert completion['completed'] == len(names)*len(scenarios) == len(df)
    if completion['code_changed_during_run']:
        audit = json.loads((folder/'audit.json').read_text(encoding='utf-8'))
        assert audit['status']=='PASS' and audit['results_sha256']==sha(folder/'results.csv')
        assert audit['audited_runs']==len(df) and not completion['algorithm_changes_during_run']
    assert not df.duplicated(['variant','scene_id']).any()
    expected = {s['scene_id']: s['scenario_sha256'] for s in scenarios}
    for name in names:
        part = df[df.variant == name]
        assert dict(zip(part.scene_id, part.scenario_sha256)) == expected
    assert np.all(np.abs(df.accounting_residual_s) < 1e-7)
    assert np.allclose(df['T'], df.movement_s+df.measure_s+df.clear_s, atol=1e-7)
    assert np.allclose(df.move_m/5, df.movement_s, atol=1e-7)
    assert np.all(df.n_measure == df.discovery_measure+df.refine_measure)
    assert np.all(df.certificate_max_distance_m < 1000)
    assert np.all(df.certificate_hull_margin_m > 0)
    return df, names


def aggregate(df):
    out = []
    base = df[df.variant == 'baseline'].set_index('scene_id')
    for name, part in df.groupby('variant', sort=False):
        part = part.set_index('scene_id').loc[base.index]
        delta = part.T_over_K-base.T_over_K
        row = dict(variant=name, label=LABELS[name], cases=len(part),
                   source_total=int(part.N.sum()), cleared_total=int(part.K.sum()),
                   full_success=int(part.full_success.sum()), failures=int((~part.full_success).sum()),
                   ratio_sum_T_K=part['T'].sum()/part.K.sum(),
                   p95_T_over_K=part.T_over_K.quantile(.95),
                   paired_wins=int((delta < -1e-7).sum()), paired_losses=int((delta > 1e-7).sum()),
                   paired_ties=int((delta.abs() <= 1e-7).sum()),
                   worst_delta_T_over_K=float(delta.max()),
                   worst_scene=str(delta.idxmax()),
                   delta_T_over_K=float(delta.mean()),
                   improvement_pct=100*(1-part.T_over_K.mean()/base.T_over_K.mean()),
                   movement_reduction_pct=100*(1-part.movement_s.mean()/base.movement_s.mean()),
                   probe_reduction_pct=100*(1-part.n_measure.mean()/base.n_measure.mean()))
        row.update({'mean_'+k: float(part[k].mean()) for k in KEYS})
        out.append(row)
    return pd.DataFrame(out)


def uncertainty(df, names):
    base = df[df.variant == 'baseline'].set_index('scene_id')
    seeds = sorted(base.seed.unique())
    counts = base.groupby('seed').size().reindex(seeds).to_numpy()
    rng = np.random.default_rng(20260912)
    weights = rng.multinomial(len(seeds), np.full(len(seeds),1/len(seeds)), size=5000)
    signs = rng.choice([-1.,1.], size=(10000,len(seeds)))
    out = []
    for name in names:
        part = df[df.variant == name].set_index('scene_id').loc[base.index]
        delta = part.T_over_K-base.T_over_K
        sums = pd.DataFrame({'seed':base.seed,'delta':delta}).groupby('seed').delta.sum().reindex(seeds).to_numpy()
        sampled = (weights@sums)/(weights@counts)
        lo,hi = np.quantile(sampled,[.025,.975])
        p = (1+np.sum(np.abs(signs@sums) >= abs(sums.sum())-1e-10))/(len(signs)+1)
        out.append(dict(variant=name, ci95_delta_low=lo, ci95_delta_high=hi,
                        block_signflip_p=p, independent_seed_blocks=len(seeds)))
    result = pd.DataFrame(out)
    challengers = result[result.variant != 'baseline'].sort_values('block_signflip_p')
    adjusted = np.maximum.accumulate(challengers.block_signflip_p.to_numpy()*np.arange(len(challengers),0,-1))
    result['holm_p'] = 1.
    result.loc[challengers.index,'holm_p'] = np.minimum(adjusted,1)
    return result


def render_table(summary, folder, full=False):
    selected = list(LABELS) if full else ['baseline','compact','center_route','proxy_compact',
               'proxy_reuse_early_compact','reuse_early','nearest','probe_off','every_stop']
    table = summary.set_index('variant').loc[selected]
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    if not font_path.exists():
        font_path = Path('C:/Windows/Fonts/simhei.ttf')
    prop = FontProperties(fname=str(font_path))
    fig, ax = plt.subplots(figsize=(16, 2.4+.48*len(table)), dpi=180)
    fig.patch.set_facecolor('white')
    ax.set_axis_off()
    total = int(table.iloc[0].source_total)
    cases = int(table.iloc[0].cases)
    all_ok = bool((table.full_success == cases).all())
    title = f'Q4 大范围配对消融：每组相同 {cases} 个场景，共 {total} 个源'
    subtitle = (f'所示各组均清除 {total}/{total}（100%）；全部场景完成认证'
                if all_ok else '清除与认证完成情况见逐组数据')
    fig.text(.035,.965,title,fontproperties=prop,fontsize=19,va='top')
    fig.text(.035,.91,subtitle,fontproperties=prop,fontsize=12,color='#555555',va='top')
    headers = ['策略','平均每场总耗时','平均清除一个','平均行走时间','平均探测次数']
    celltext = [[r.label,f'{r.mean_T:.2f} s',f'{r.mean_T_over_K:.2f} s',
                 f'{r.mean_movement_s:.2f} s',f'{r.mean_n_measure:.2f}'] for _,r in table.iterrows()]
    tab = ax.table(cellText=celltext,colLabels=headers,colWidths=[.40,.16,.16,.16,.12],
                   cellLoc='right',colLoc='right',bbox=[0,.03,1,.88])
    tab.auto_set_font_size(False)
    tab.set_fontsize(12)
    eligible = summary[summary.failures==0]
    best = eligible.loc[eligible.mean_T_over_K.idxmin(),'variant'] if len(eligible) else None
    for (row,col),cell in tab.get_celld().items():
        cell.set_edgecolor('#d5d5d5')
        cell.set_linewidth(.65)
        cell.visible_edges = 'B'
        cell.get_text().set_fontproperties(prop)
        cell.get_text().set_fontsize(12)
        cell.PAD = .025
        if col == 0:
            cell.get_text().set_ha('left')
        if row == 0:
            cell.get_text().set_color('#888888')
        elif table.index[row-1] == best:
            cell.get_text().set_fontweight('bold')
            cell.get_text().set_color('#146347')
    fig.text(.035,.023,'A：就近调度；B：覆盖站复用定位；C：提前清除（160 m）。离线仿真；每源耗时 = 各场 T/K 的均值。',
             fontproperties=prop,fontsize=10,color='#666666')
    fig.subplots_adjust(left=.035,right=.98,bottom=.06,top=.91)
    stem = 'ablation_table_all' if full else 'ablation_table'
    fig.savefig(folder/(stem+'.png'),facecolor='white')
    fig.savefig(folder/(stem+'.pdf'),facecolor='white')
    plt.close(fig)
    meta = dict(source='summary.csv',source_sha256=sha(folder/'summary.csv'),
                script_sha256=sha(__file__),variants=selected,
                note='Offline exploratory results; independent review pending')
    (folder/(stem+'.meta.json')).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')


def markdown_table(summary):
    lines = ['| 策略 | 总耗时 s | 每源耗时 s | 行走 s | 探测次数 | T/K 降幅 |',
             '|---|---:|---:|---:|---:|---:|']
    for _,r in summary.iterrows():
        lines.append(f'| {r.label} | {r.mean_T:.2f} | {r.mean_T_over_K:.2f} | '
                     f'{r.mean_movement_s:.2f} | {r.mean_n_measure:.2f} | {r.improvement_pct:+.2f}% |')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder',type=Path)
    args = ap.parse_args()
    folder = args.folder
    df,names = load_checked(folder)
    summary = aggregate(df).merge(uncertainty(df,names),on='variant')
    summary = summary.set_index('variant').loc[names].reset_index()
    summary.to_csv(folder/'summary.csv',index=False)
    summary.to_json(folder/'summary.json',orient='records',indent=2,force_ascii=False)
    base = df[df.variant=='baseline'].set_index('scene_id')
    paired = []
    for name in names:
        part = df[df.variant==name].set_index('scene_id').loc[base.index].copy()
        for key in KEYS:
            part['delta_'+key] = part[key]-base[key]
        paired.append(part.reset_index())
    pd.concat(paired).to_csv(folder/'paired.csv',index=False)
    strata = []
    for (kind,err),part in df.groupby(['source_kind','error_mode']):
        s = aggregate(part)
        s['source_kind'],s['error_mode'] = kind,err
        strata.append(s)
    pd.concat(strata).to_csv(folder/'strata.csv',index=False)
    counts = []
    for n,part in df.groupby('N'):
        s = aggregate(part)
        s['N'] = n
        counts.append(s)
    pd.concat(counts).to_csv(folder/'by_source_count.csv',index=False)
    df[~df.full_success].to_csv(folder/'failures.csv',index=False)
    eligible = summary[summary.failures==0].sort_values('mean_T_over_K')
    best = eligible.iloc[0]
    baseline = summary[summary.variant=='baseline'].iloc[0]
    best_strata = pd.concat(strata)
    best_strata = best_strata[best_strata.variant==best.variant]
    completion = json.loads((folder/'completion.json').read_text(encoding='utf-8-sig'))
    provenance_note = '本次入口正常完成，运行结束时的全部源码哈希与启动时一致。'
    if completion.get('code_changed_during_run'):
        provenance_note = '''运行中为解决 Q3 同名导入冲突，将 policies.py 改名为 q4_ablation_policies.py，
策略文件字节哈希相同。原运行在 8000 行全部写出后，最终路径哈希检查因旧文件名失败。
completion.json 记录原退出码 1、路径变化和事后恢复；
code_at_start/ 保存按运行前 SHA256 验证的原入口和策略字节。'''
    if (folder/'harness_replay.json').exists():
        provenance_note += '\n修正后的入口另用 20 个策略 x 2 个原场景复跑，事件哈希逐项一致（harness_replay.json）。'
    stratum_lines = ['| 场景类型 | 误差 | 候选平均 T/K s | 相对基线改善 |',
                     '|---|---|---:|---:|']
    for _,r in best_strata.iterrows():
        stratum_lines.append(f'| {r.source_kind} | {r.error_mode} | {r.mean_T_over_K:.2f} | {r.improvement_pct:+.2f}% |')
    nblocks = int(df.seed.nunique())
    report = f'''# Q4 大范围配对消融结果

已完成 {len(names)} 个策略，每组 {int(baseline.cases)} 个相同场景设置，共 {len(df)} 次运行。
每组共有 {int(baseline.source_total)} 个源。全部实验的失败场数为 {int(summary.failures.sum())}。
场景包含 200 个混合源端点误差场景，以及全定向、全向、边界外向、混合平滑误差各 50 个。
这是 {nblocks} 个独立种子块，其中前 50 个种子含五种配对扰动，不能把 400 场当作 400 个独立样本。

## 对比表

{markdown_table(summary)}

“平均清除一个”是各场 T/K 的均值。sum(T)/sum(K) 另列在 summary.csv。
本次全新 400 场基线为 {baseline.mean_T_over_K:.6f} s，与旧留出集 517.584293 s 属于不同场景分布。
所有差值都与本次相同场景上的原冻结算法配对计算，未将旧均值直接当作新场景分母。

## 排名与实际限制

本矩阵中完成率合格且平均 T/K 最低的是“{best.label}”：
{baseline.mean_T_over_K:.4f} → {best.mean_T_over_K:.4f} s，降低 {best.improvement_pct:.3f}%。
行走时间降低 {best.movement_reduction_pct:.3f}%，探测次数降低 {best.probe_reduction_pct:.3f}%。
配对胜/负/平为 {int(best.paired_wins)}/{int(best.paired_losses)}/{int(best.paired_ties)}；
最差场景退化 {best.worst_delta_T_over_K:.4f} s/源（{best.worst_scene}）。
平均配对差的种子块 bootstrap 95% 区间为
[{best.ci95_delta_low:.4f}, {best.ci95_delta_high:.4f}] s/源。

{chr(10).join(stratum_lines)}

该组合在边界外向压力组有平均退化，不能称为各类场景均改善。
“平均冠军”只按预定平均 T/K 排名；若要求重要子群也不退化，则该组合不满足替换基线的要求。

排名是这 20 个候选在指定分布上的结果，不是全局最优或逐场最优。
summary.csv 的区间为逐比较的 95% 区间，未经多重比较校正。
另附种子块符号翻转检验及 19 次比较的 Holm 校正 p 值；该检验假设零假设下种子块差值近似符号对称。
组合策略先根据独立开发集确定，再运行本组新场景；最终冠军仍是矩阵内选择，宜继续用新种子复核。

## 策略机制

A：用最近的可执行任务替代全任务开路线规划，逐动作重规划。
B：在接收概率和信息增益门槛内，用尚未访问的覆盖站替代专门定位点，同时完成未知频道扫描。
C：把试清除阈值从后验包围半径 80 m 放宽到 160 m；失败最多两次且保留完整光学兜底。
其他单项包括顺路探测门槛、120/220 m 提前清除、源中心路线代理、连续处理同一源及 1900 m 外圈。
“每次停车扫未知频道”用来量化过度扫描成本。所有失败清除和行走均计入总时间。
外圈微调没有删站，仍为 25 点，须通过连续证书；no_signal 从不被解释成距源大于 1000 m。

## 复现与证据

- 原始逐场结果：results.csv；逐动作记录：events/，每场 gzip JSON。
- 场景及算法哈希：scenarios.json、manifest.json、completion.json。
- 全部事件与场景真值、计时公式复核：audit.json（主 agent 自动核验，非独立专家审查）。
- 逐场差值：paired.csv；分类型：strata.csv；按真实源数事后分层：by_source_count.csv。
- 完整对比图：ablation_table_all.png；精选对比图：ablation_table.png。
- 原冻结算法 100 场精确重跑：../baseline_replay.csv。
- 冻结源码不变，Q1/Q2/Q3 算法不变。

{provenance_note}

```powershell
python experiments/q4_ablation/run_ablation.py --suite primary --output experiments/q4_ablation/reproduce400 --workers 8
python experiments/q4_ablation/summarize.py experiments/q4_ablation/reproduce400
```

独立评审因子进程服务商 403 insufficient balance 未完成，本结果为待独立复核的离线探索性消融。
没有自动替换冻结基线，也不能引用为官方模拟器成绩。
'''
    (folder/'report.md').write_text(report,encoding='utf-8')
    render_table(summary,folder)
    render_table(summary,folder,full=True)
    print(summary[['variant','full_success','mean_T_over_K','mean_movement_s','mean_n_measure',
                   'improvement_pct','ci95_delta_low','ci95_delta_high','holm_p']].to_string(index=False))


if __name__=='__main__':
    main()

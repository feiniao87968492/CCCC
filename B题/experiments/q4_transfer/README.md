# Q4 扩展消融：学习Q3 JSO并测试不同算法族

这是独立实验目录。冻结算法仍为TRI25 + ROUTE_ADAPTIVE_V4，哈希依据为
`../q4_efficiency/release_holdout100.meta.json`，没有采用本目录候选替换正式入口。

## 实验入口

主实验28组×400场全部完成，每组清除5187/5187个源；11200条事件轨迹、
3438321次探测/清除操作通过真值与计时审计，272项测试通过。
综合均值最低为JSO+1900 m外圈+D-optimal：532.172912→513.958406 s/源，
行走减少4.402%、探测减少1.301%，但边界外向组T/K增加0.586%。

JS=523.332762，JSO=523.327595 s/源，在JS上增加O的平均差仅−0.005167 s/源。
若要求本次五类场景均值均改善，S+D-optimal+短清除为522.007222 s/源，
但探测次数增加2.005%；短清除单项529.625589、提前4格光学530.469721 s/源，
两者均同时减少行走和探测且五类均值均改善，收益较小，仍存在逐场退化。
这些是当前样本结果，不是总体或逐场不退化保证。

独立主实验审查为PASS_WITH_WARNINGS。相对JSO+1900 m外圈，再加D-optimal
仅快1.225 s/源，95%种子块区间[-3.591, +1.219]跨零，不能证明该加成优于次名。
本目录以最低观测均值排序，不宣称唯一优胜或最优。

- [主实验完整报告](primary400/report.md)
- [精选对比图](primary400/ablation_table.png) / [28组完整对比图](primary400/ablation_table_all.png)
- [全部汇总](primary400/summary.csv) / [场景分组](primary400/strata.csv) / [逐场配对](primary400/paired.csv)
- [初始开发集](dev40/report.md) / [新增组合开发集](dev_combinations40/report.md)
- [预先设计与参数锁定](design.md) / [独立审查](reviews/)

## 不同类型的算法

| 类型 | 实际改动 | 试验参数与组合 |
|---|---|---|
| Q3 J/S/O增量迁移 | J按后验源中心规划路线；S在停车点选择性补测；O用正测向最小二乘交点试清除 | baseline/J/S/O/JS/JO/SO/JSO完整八组 |
| 覆盖路线插入 | 先规划覆盖站，再按绕行预算插入定位或清除任务 | 80/200/400 m |
| 定位点重排 | aligned面向最近尚需访问覆盖站；D-optimal按接收概率加权信息增益与行走代价选点 | aligned、doptimal |
| 定向接收恢复 | 无信号后以短基线对称探测争取恢复接收，须通过投影和所有顶点距离证明 | bracket |
| 几何清除 | 后验只需少量光学格时提前完整覆盖；认证清除点沿来路作有证明的短移 | optical2/optical4/short_clear |
| 微调与组合 | 接收阈值、试清除半径、外圈半径，加开发集选定的4个组合 | 阈值0.50/0.70/0.85；半径80/120/160 m；外圈1900/1950/1980 m |

四个组合是S+D-optimal、S+O+D-optimal、S+D-optimal+短清除、
JSO+1900 m外圈+D-optimal。全部初始策略（包括开发集退化策略）都进入主实验，没有删掉负结果。

S要求接收概率≥门槛，并同时满足“视差≥12°或距离减半”；只操作已发现频道。
它也替换了V4覆盖站的顺路探测准则，因此效果不只来自新增停车点补测。
O至少需两条正测向，cond(A)≤30；解须合法且在正观测可行多边形内。
每源非认证O尝试最多2次，同一正观测计数不重复尝试；负观测不重置计数。
O失败仍计费，并保留完整无上限光学兜底。O有时使用多于两条测向。

Q4冻结算法已经有联合规划和中心试清除，J/S/O在这里是增量替换，
不能将八组因子实验解释成“冻结基线没有联合路线或乐观清除”。
Q3七站全向环境的254.05 s不是Q4二十五站定向环境的同条件对照。

## 规模与指标

1. 开发：24组×40设置=960次，另5组×40=200次检验新增组合。
2. 主实验：锁定28组×400设置=11200次。200个mixed/endpoint场景，
   全定向、全向、边界外向最小半径、mixed/smooth各50场。
3. 400设置来自200独立种子块。bootstrap按种子块重采样、按设置等权计算均值。

报告mean(T/K)、sum(T)/sum(K)、总耗时、行走、探测拆分、失败清除、
顺路S补测、O尝试/成功、实际光学兜底、全部完成率、分层、配对胜负和最坏退化。
`n_early_optical_proposals`是重规划中提议次数；`mechanisms.csv`的`optical_actions`
是实际完整光学调用次数。专门定位上限8不包括顺路S补测。

不论候选为何，未发现频道都保留25站无信号证书，或独立的已观测16频道计数证书。
`no_signal`不被解释成距源大于1000 m，正观测可行多边形不被负观测裁剪。

## 复现

在`B题`目录运行：

```powershell
python -m pytest tests experiments/q4_ablation/test_ablation.py experiments/q4_transfer/test_transfer.py -q
python experiments/q4_transfer/run_transfer.py --suite primary --output experiments/q4_transfer/reproduce400 --workers 10
python experiments/q4_transfer/audit_transfer.py experiments/q4_transfer/reproduce400
python experiments/q4_transfer/summary_transfer.py experiments/q4_transfer/reproduce400
```

入口拒绝覆盖已有实验目录。启动时保存22份依赖快照；运行结束复核哈希。
使用进程池隔离覆盖几何的全局参数，不使用线程并发仿真。
算法与仿真入口的文件在运行过程中不得修改或重命名。

初始dev40的previous_best配置清单漏写route/reuse/clear_rho，实际始终调用上一轮最优配置。
原清单保留；补正见`dev40/provenance-correction.json`；后续清单已正确记录所有字段。

所有成绩均为有界误差几何仿真的探索性比较，主实验排名不能证明总体或逐场最优。
基线是否替换与官方模拟器成绩不在本次实验结论范围内。

# GREEDY_FAST 演练实验

当前 GREEDY 保留为基线。GREEDY_FAST 是独立策略，不预设提速或全清成绩。

在 B题 目录运行（只进入问题3演练）：

```powershell
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST -SourceBudgetS 300
```

默认 SourceBudgetS=0：保留 SAFE 全部回退。中心优先采用示向直线最小二乘估计，执行前用完整楔形后验过滤；每轮最多3次启发式清除，最多两轮。补测仅在当前后验全部顶点距候选点不超过1000m、且估计补测加清除成本低于局部覆盖时进行。估计不是最优性或成功概率保证。覆盖途中只对确定单点清除的频道停止常规补测。

SourceBudgetS>0：仅限制发现覆盖完成后的逐源处理，包含入场移动及检测、清除、SAFE；检查下一动作最坏耗时，超限前停止发送。该源从本轮任务队列移出，不自动再试。七点发现覆盖仍保留。这是有意允许未全清的实验，不是全清模式；300s可能连较远目标的入场路程都不够。

summary.json 包含 source_budget_s、experimental_incomplete_allowed、abandoned_channels、uncleared_detected_channels、all_certified。预算放弃不是 certified_absent，也不会计为清除。比较时同时报告 K/N、全清率、T、T/K、墙钟、SAFE 次数，不能只看 T/K。

此版本没有实现非凸失败圆域扣除，也没有宣称联合路线全局最优。新策略包含多项变化，若需归因，应另做单因素对照。固定策略和预算后多局测试，不将随机案例比较写成配对结果。

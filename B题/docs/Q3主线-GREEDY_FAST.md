# 问题3 当前算法

总览见 [`当前算法与消融状态.md`](当前算法与消融状态.md)。

2026-09-11 用户确认过 **GREEDY_FAST**（全清兜底，`SourceBudgetS=0`）为主线。2026-09-12 离线消融与 20 局官方演练表明 **JSO 更省虚拟时间且保持全清**；演练脚本默认改为 JSO。GREEDY_FAST 仍可回退。正式测试未跑，不把任一数字写入表1。

## 当前演练入口

```powershell
.\simulator_automation\run_q3_practice.ps1 -Strategy JSO
```

JSO = 联合调度 + 选择性复测 + 乐观试清，发现环为中心加半径 1130 m 六点。实现：`experiments/q3_ablation/policies.py`。

| 口径 | 全清 | 平均 T/K | 区间 | SAFE均值 |
|---|---|---:|---|---:|
| 离线 420 场配对 | 420/420 | **254.05** | P95 351.81 | 0.08 |
| 官方演练 20 局（非配对） | **20/20** | **239.08** | 190.39–311.80 | 0.20 |

20 局 \(T/K\) 中位数 235.52，Q1–Q3 为 221.48–256.43，IQR 34.95，极差 121.41。10/20 局落在 220–260；\(N=10\) 的 3 局全在 287–312，\(N=16\) 的 3 局在 190–211。样本小、场景随机，只描述这 20 局，不外推正式成绩。

两套场景不同，禁止平均。证据：`experiments/q3_ablation/evaluation/`、`experiments/q3_simulator/practice_results.md`。

## 历史筛选（2026-09-11 演练，非配对）

| 策略 | 全清 | T/K 均值 | 区间 | SAFE均值 |
|------|------|----------|------|----------|
| GREEDY | 10/10 | 390 | 334–455 | 1.20 |
| **GREEDY_FAST** | **10/10** | **341** | 244–450 | 0.20 |
| GREEDY_ABORT | 1/10 | 382 | 295–482 | 0 |

GREEDY 快照：`stable/q3-greedy-20260911/`。ABORT 与 `SourceBudgetS=300` 不作候选。

回退：

```powershell
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST
```

## 正式测试

问题3正式仍未使用，额度 3 次，与问题4独立。截止：2026-09-13 17:30 后不能启动新测试。

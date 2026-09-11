# Q3 主线：GREEDY_FAST

确认时间：2026-09-11。用户决定：**问题3以 GREEDY_FAST（全清兜底，`SourceBudgetS=0`）为主线。**

## 依据（演练，非配对、非正式）

同晚 10 局对照：

| 策略 | 全清 | T/K 均值 | 区间 | SAFE均值 |
|------|------|----------|------|----------|
| GREEDY | 10/10 | 390 | 334–455 | 1.20 |
| **GREEDY_FAST** | **10/10** | **341** | 244–450 | 0.20 |
| GREEDY_ABORT | 1/10 | 382 | 295–482 | 0 |

GREEDY 保留为回退基线（`stable/q3-greedy-20260911/`）。ABORT 不作为正式候选。预算模式 `-SourceBudgetS 300` 不作为主线。

## 正式测试

问题3正式仍未使用，额度 3 次，与问题4独立。主线未在正式上验证。截止：2026-09-13 17:30 后不能启动新测试。

## 入口

```powershell
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST
```

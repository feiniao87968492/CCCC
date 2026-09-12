# GREEDY_ABORT 演练实验

GREEDY 全清基线不动。GREEDY_ABORT 是独立策略：七点发现、确定清除、贪心定位都与 GREEDY 相同；**下一步只能走中心线走廊或 SAFE 时放弃该频道**，不走 225。

在 B题 目录（只进入问题3演练）：

```powershell
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_ABORT
```

放弃记入 `abandoned_channels`，不是 `certified_absent`，不计 K。比较时同时看 K/N、全清率、T、T/K、SAFE 次数。各局随机非配对。

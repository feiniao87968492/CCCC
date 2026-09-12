# Q3 GREEDY 稳定快照（2026-09-11）

在做更激进改动前冻结的可运行源码。不含演练 evidence 目录、不含正式测试。

## 冻结时演练（问题3演练，非配对、非正式）

过滤清除版 5 局（`20260911-162333` … `162914`）：

| K/N | T/K | SAFE源 | 完整225 |
|-----|-----|--------|---------|
| 15/15 | 393 | 4 | 0 |
| 13/13 | **309** | 0 | 0 |
| 16/16 | 479 | 7 | 0 |
| 15/15 | 356 | 2 | 0 |
| 13/13 | 550 | 5 | 0 |

5/5 全清；T/K 均值约 417 s；3 局 &lt; 400 s。完整表见 `experiments/q3_simulator/practice_results.md`。

## 策略要点（本快照）

- 七点覆盖巡回 + 联合调度；启发式清除前丢掉与定位区域不相交的点。
- 已确定清除或 ≤4 点可覆盖的频道暂停常规补测，保留待清除任务。
- 未知频道扫描、near 直接清除、裁剪 SAFE + 完整 225 兜底仍在。

## 回退方法

把本目录下三个文件夹覆盖回 `B题/` 对应位置（先自行备份正在改的文件）：

```
simulator_automation/*.py  *.ps1
src/*.py
tests/test_q3*.py
```

然后：

```
python -m unittest tests.test_q3_greedy_policy tests.test_q3_greedy_schedule tests.test_q3_certified_queue tests.test_q3_fixes tests.test_q3_offline tests.test_q3_tail tests.test_q3_action_filter tests.test_q3_fast_mode
```

演练入口仍是 `simulator_automation/run_q3_practice.ps1 -Strategy GREEDY`（仅演练，不要正式）。

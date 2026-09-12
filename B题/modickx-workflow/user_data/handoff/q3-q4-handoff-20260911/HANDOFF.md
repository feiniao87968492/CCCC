# CUMCM 2026 B 题转交说明（Q3 主线 + Q4 演练）

日期：2026-09-11 晚。队号默认 `202611102016`。

本包转交 **Q1–Q2 离线代码、Q3 在线主线 GREEDY_FAST、Q4 $P_4$ 建模与演练 runner**。不含正式测试、不含模拟器安装包、不含加密 `.jlog`。

---

## 1. 硬约束

- **只跑演练，禁止启动问题3/问题4正式。** 每问正式仅 3 次，点了就算。
- Q3 入口 Inspect 必须是 `问题3 演练 测试`；Q4 必须是 `问题4 演练 测试`。
- 在线只许 `127.0.0.1:2026` 的 `/enter` `/measure` `/clear` `/exit`。禁止真值 `g,r,ψ`、`q2_validation` 驱动这些调用。
- 演练各局随机、非配对。T/K 是虚拟时间，不是墙钟。
- 截止：2026-09-13 17:30 后不能启动新的演练或正式。

---

## 2. 目录

```
HANDOFF.md
docs/                 Q3 主线、Q4 覆盖/状态/策略、口径
simulator_automation/ Q3 + Q4 演练入口
src/                  几何、定位、P4、Q4 状态/寻路
tests/
experiments/q3_simulator/practice_results.md
experiments/q4_simulator/practice_results.md
stable/q3-greedy-20260911/   GREEDY 冻结回退
evidence/             近期明文 summary + requests.jsonl
```

---

## 3. 问题3：主线 GREEDY_FAST

确认文档：`docs/Q3主线-GREEDY_FAST.md`。

```powershell
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST
```

同晚 10 局演练：全清 10/10，T/K 均值 **341**（244–450），SAFE 均值 0.20。GREEDY 全清但均值 390。GREEDY_ABORT 不走 SAFE，全清仅 1/10，不作正式候选。

GREEDY 回退：`stable/q3-greedy-20260911/`。

**问题3正式尚未使用。** 主线未在正式上验证。

---

## 4. 问题4：建模已接演练，非正式可用

覆盖：$P_4$ 600 m 网格、81 点。命题见 `docs/Q4覆盖命题.md`。`no_signal` 三分支，81 点全无信号才判空。

```powershell
.\simulator_automation\run_q4_practice.ps1
```

闭环：`q4_runner.py`（与 Q3 正式流程独立）。寻路禁止 $k!$ TSP。

演练（摘）：`195953` K=10、证书走完；其余多局 K=9–12 且未完成证书。T/K 约 2000 s。**不能用于正式。** 明细 `experiments/q4_simulator/practice_results.md`。

---

## 5. 测试

工作目录仓库根或 `B题` 上一级：

```
python -m pytest -q B题/tests
```

最近一次 **132 passed**。

---

## 6. 接手后不要做的事

- 不要点问题3/4正式。
- 不要把 Q3 七点当 Q4 判空证书。
- 不要把 Q4 当前 T/K 写进论文当成绩。
- 不要用 `q2_validation` 驱动 HTTP。

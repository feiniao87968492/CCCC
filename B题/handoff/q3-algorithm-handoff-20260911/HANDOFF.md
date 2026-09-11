# CUMCM 2026 B 题 Q3 转交说明

日期：2026-09-11。队号默认 `202611102016`。

本包只转交 **问题3 在线定位/清除算法、单元测试、官方演练成绩**。不含正式测试、不含模拟器安装包、不含加密 `.jlog`。

---

## 1. 硬约束（接手后不要破）

- **只跑问题3演练，禁止启动问题3正式。** 正式每问仅 3 次，点了就算。脚本会 Inspect UI，标题必须是 `问题3 演练 测试`。
- 在线闭环只许调官方 HTTP：`127.0.0.1:2026` 的 `/enter` `/measure` `/clear` `/exit`。禁止用离线种子、真值 `g,r`、`q2_validation` 驱动这些调用。
- `ρ≤20 m` 的最小外接圆是**证书**（可以宣称一击清除）；启发式试清可以在 ρ 略大于 20 时尝试，失败代价是 3 s + 路程。
- 演练各局是**随机新案例、非配对**。不能把两局 T/K 差写成“改动有效”。正式成绩只有案例编码、K、T/K、墙钟，没有 N。
- **T/K 是平均虚拟耗时**（模拟器累加），不是程序墙钟。移动 5 m/s；检测 5 s + 切频 1 s；清除失败 3 s、成功再 +2 s。

---

## 2. 目录

解压后建议放到已有 `B题/` 上覆盖，或单独打开本包：

```
HANDOFF.md                          ← 本文件
docs/
  GREEDY_FAST实验说明.md
  Q3模拟器测试说明.md
simulator_automation/               ← 在线入口
src/                                ← 几何/定位（无 HTTP）
tests/test_q3*.py
experiments/q3_simulator/practice_results.md
stable/q3-greedy-20260911/          ← 过滤清除版 GREEDY 冻结快照（回退用）
evidence/                           ← 近期 GREEDY / GREEDY_FAST 演练明文日志
```

---

## 3. 当前两条策略

| 策略 | 代码 | 角色 |
|------|------|------|
| **GREEDY** | `q3_runner.py` + `q3_greedy_policy.py` | 稳定基线。七点巡回 + 联合调度 + 定位区域覆盖尾段 + 裁剪 SAFE + 完整 225 兜底。 |
| **GREEDY_FAST** | `q3_fast_mode.py`（继承 GREEDY） | 独立实验策略。覆盖途中少试清；尾段中心优先、每轮最多 3 次启发式清除；默认可走 SAFE；可选逐源预算放弃。 |

稳定快照：`stable/q3-greedy-20260911/`（过滤清除版 GREEDY，5 局演练全清）。激进改动请不要覆盖该目录。

### GREEDY（基线）在做什么

1. 原点全扫 1–20 频道，再走七点骨架（原点 + 1200 m 六顶点）。
2. 每到一站：扫未见频道；扫已发现未清除频道（增量测向）。
3. `greedy_action_candidates`：覆盖点与 pending 放进同一次决策，按预计新增路程选下一个。未完成巡回时，不把所有 pending 拉去长距离二次测向。
4. 融合全部历史示向度；若两楔交的 MEC 半径 ≤20 m，该点作为**确定清除任务**，按距离排队，失败后不再用同一点死循环。
5. 启发式试清前丢掉与当前定位多边形不相交的点。
6. 已确定清除或 ≤4 点可覆盖的频道，暂停常规补测，只保留待清除。
7. 尾段优先覆盖完整定位区域，而不是先走首示向长走廊。局部覆盖失败仍回退裁剪 SAFE，再完整 225。
8. `near` 立刻原地清除。

### GREEDY_FAST 相对 GREEDY 的差异

详见 `docs/GREEDY_FAST实验说明.md`。要点：

- 覆盖巡回进行中：几乎不发启发式试清；只在当前站已是好二次测向位时补一条测向。
- 巡回结束后，对每个 pending：确定点 → 每轮最多 3 次启发式清除（中心 / 示向最小二乘 / 局部覆盖点）→ 最多两轮；若估计补测成本低于局部覆盖且候选对全部顶点 ≤1000 m，才补测。
- 默认 `SourceBudgetS=0`：最后仍 `safe_channel`（全清兜底）。
- `SourceBudgetS=300`：发现完成后逐源限额；下一动作最坏耗时超限则放弃该频道，写入 `abandoned_channels`。**放弃 ≠ 判空**，也不计入 K。七点发现覆盖仍做。300 s 可能连入场都不够。

---

## 4. 怎么跑

工作目录：`B题/`。模拟器需已登录、本机 `127.0.0.1:2026`。

```powershell
# 单元测试（不连模拟器）
python -m unittest tests.test_q3_greedy_policy tests.test_q3_greedy_schedule tests.test_q3_certified_queue tests.test_q3_fixes tests.test_q3_offline tests.test_q3_tail tests.test_q3_action_filter tests.test_q3_fast_mode

# 基线 GREEDY 演练
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY

# GREEDY_FAST 全清兜底
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST

# GREEDY_FAST 允许不满清
.\simulator_automation\run_q3_practice.ps1 -Strategy GREEDY_FAST -SourceBudgetS 300
```

每局证据写到 `simulator_automation/evidence/YYYYMMDD-HHMMSS-q3-<strategy>/`：

- `summary.json` 成绩
- `requests.jsonl` 明文 API（不是官方加密 `.jlog`）
- `events.json` 策略日志（含 `certified_visit`、`fast_refine`、`source_budget_stop`、过滤清除等）
- `ui-before.txt` / `ui-after.txt`

比较 FAST 与 GREEDY 时同时看：**K/N、是否全清、T、T/K、墙钟、SAFE 次数、放弃频道**。不要只报 T/K。

---

## 5. 演练成绩（截至打包时）

全部是问题3**演练**、随机非配对。完整表：`experiments/q3_simulator/practice_results.md`。

### GREEDY 过滤清除版（稳定快照对应）5 局

| 证据 | K/N | T/K | SAFE源 | 完整225 |
|------|-----|-----|--------|---------|
| 162333 | 15/15 | 393 | 4 | 0 |
| 162539 | 13/13 | **309** | 0 | 0 |
| 162636 | 16/16 | 479 | 7 | 0 |
| 162806 | 15/15 | 356 | 2 | 0 |
| 162914 | 13/13 | 550 | 5 | 0 |

5/5 全清；T/K 均值约 **417 s**；3 局 &lt;400。偏高两局 SAFE 源多，但都没有走完整 225。

### GREEDY_FAST 全清兜底 3 局

| 证据 | K/N | T/K | SAFE |
|------|-----|-----|------|
| 163743 | 10/10 | 403 | 0 |
| 163823 | 14/14 | **353** | 0 |
| 163931 | 10/10 | 416 | 0 |

3/3 全清、SAFE=0；T/K 均值约 **391 s**。样本少，不能写成已稳定优于 GREEDY。

### GREEDY_FAST `-SourceBudgetS 300` 2 局

| 证据 | K/N | T/K | 放弃 |
|------|-----|-----|------|
| 164019 | 9/15 | 384 | 7,10,11,13,16,19 |
| 164153 | 14/15 | 310 | 1 |

T 更短，清除率会掉。论文若要全清，不要用预算模式当正式策略。

时间口径：T/K = 总虚拟时间 / 成功清除数。墙钟 15–60 s 量级。

---

## 6. 关键源文件

| 文件 | 作用 |
|------|------|
| `simulator_automation/q3_practice.py` | 演练入口；Inspect 非演练则不发 API |
| `simulator_automation/run_q3_practice.ps1` | Login + StartPractice + runner |
| `simulator_automation/q3_runner.py` | GREEDY 主循环、确定清除点、SAFE |
| `simulator_automation/q3_greedy_policy.py` | 纯几何决策（巡回 vs pending、试清点） |
| `simulator_automation/q3_fast_mode.py` | GREEDY_FAST |
| `simulator_automation/q3_safe.py` | 裁剪蛇形 + 完整 225 |
| `simulator_automation/q3_state.py` | 七点 P3、频道状态 |
| `simulator_automation/robot_client.py` | HTTP 客户端 |
| `src/geometry.py` `src/localization.py` | MEC、楔形裁剪 |

`q3_runner` **禁止** import `q2_validation` / `q2_scenario`。

---

## 7. 已知缺口（接手后优先知道）

- 演练样本仍少，T/K 波动大（GREEDY 约 309–550）。不能用单局宣称正式水平。
- GREEDY_FAST 未做相对 GREEDY 的单因素对照；多项改动叠在一起。
- 没有实现非凸“失败圆域扣除”；没有宣称联合路线全局最优。
- 预算 300 s 经常放弃远源；`abandoned` 不是判空证书。
- Q3 模拟器测试说明里仍有过时句子（“闭环从未在模拟器里跑过”），以本文件和 `practice_results.md` 为准。
- **正式三次尚未使用。** 截止：北京时间 2026-09-13 17:30 后不能启动新正式测试。

---

## 8. 回退 GREEDY 稳定版

把 `stable/q3-greedy-20260911/` 下的 `simulator_automation`、`src`、`tests` 覆盖回 `B题/` 对应位置。详见该目录 `STABLE.md`。GREEDY_FAST 文件（`q3_fast_mode.py`）稳定快照里没有，覆盖后需从本包根目录再拷回来，或不要覆盖 `q3_fast_mode.py`。

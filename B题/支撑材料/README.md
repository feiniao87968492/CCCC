# CUMCM 2026 B 题支撑材料（Q3 / Q4 离线结果）

日期：2026-09-12。本包冻结于 **Q3 JSO 254.05 s / Q4 第 1 轮 529.29 s**。其后第 2、3、4 轮消融与 JSO 20 局演练在仓库 `experiments/q4_transfer/`、`experiments/q4_local/`、`experiments/q4_aggressive/`、`experiments/q3_simulator/`，不在本 zip。当前入口见 `docs/当前算法与消融状态.md`。Q3 没有第二轮离线消融目录。

本包只整理当时代码与结果，不改论文章节。

正式测试未执行。表1保持空缺。本包数字全部是离线几何模型，禁止当作官方模拟器成绩。

## 提交数字

| 问 | 方案 | 场数 | 全清且证书 | 平均 T/K (s) | 精确值 |
|---|---|---:|---:|---:|---|
| 问题3 | JSO | 420 | 420/420 | **254.05** | 254.05321048920862 |
| 问题4 | 源中心路线 + 覆盖站复用 + 提前清除 160 m + 外圈 1900 m | 400 | 400/400 | **529.29** | 529.2899300477935 |

对照（同一批场景，勿与上表平均）：

- Q3 原 GREEDY_FAST（1200 m 七点）：379.60 s，配对下降 125.55 s（33.07%），胜 418/420。
- Q4 同 400 场上的冻结 TRI25/V4：543.54 s，配对下降 14.25 s（2.62%），胜/负/平 275/125/0。
- Q4 另一套留出 100 场（种子 1000–1099）上的 TRI25/V4 均值是 517.58 s，场景分布不同，不能和 529.29 混成一个数。

明细见 `结果说明.md` 与 `结果/headline.json`。

## 目录

```
README.md                 本说明
结果说明.md               表格、分层、限制、复现命令
结果/headline.json        机器可读的提交数字
程序/                     可复现代码快照（相对路径与 B题 相同）
  src/
  simulator_automation/   仅 .py / .ps1，不含历史演练 evidence
  data_preparation/parameters.csv
  experiments/q3_ablation/
  experiments/q4_ablation/
  experiments/q4_efficiency/bench.py 及留出集汇总
  tests/                  复现所需测试依赖
结果/q3/                  420 场汇总、逐场 rows、配对差
结果/q4/                  400 场汇总、分层、逐场 results、对照图
```

未放入本包：模拟器安装包、加密 `.jlog`、8000 场逐动作 gzip 轨迹、论文 TeX。轨迹仍在原仓库 `experiments/*/traces` 与 `primary400/events`。

## 方案对应代码

问题3 JSO：`程序/experiments/q3_ablation/policies.py`，变体名 `JSO`。
在 GREEDY_FAST 上打开联合调度、选择性复测、乐观试清；发现环改为中心 + 半径 1130 m 六点。

问题4 最新方案：`程序/experiments/q4_ablation/q4_ablation_policies.py`，变体名 `proxy_reuse_early_compact`。

```
route=center, reuse=true, clear_rho=160, outer_radius=1900, every_stop=false
```

底层覆盖仍是 TRI25 + `ROUTE_ADAPTIVE_V4`（`程序/src/q4_*.py`）。

## 复现

把 `程序/` 当作 `B题` 根目录。需要 Python 3.10、numpy、scipy；Q4 汇总图还需要 pandas、matplotlib。

```powershell
# 问题3：420 场配对（输出目录必须是新路径）
python experiments/q3_ablation/run_ablation.py --split evaluation --workers 8

# 问题4：400 场配对
python experiments/q4_ablation/run_ablation.py --suite primary --output experiments/q4_ablation/reproduce400 --workers 8
python experiments/q4_ablation/summarize.py experiments/q4_ablation/reproduce400
```

已完成的数字以 `结果/q3/summary.csv`、`结果/q4/summary.csv` 为准，不必为了提交再跑一遍。

## 不要做的事

- 不要用本包数字填正式测试表。
- 不要点问题3/问题4正式测试（各仅 3 次额度）。
- 不要把 Q4 留出集 517.58 与消融 529.29 平均。
- 不要把边界外向组的退化（最新方案 +3.90%）写成各类场景均更优。

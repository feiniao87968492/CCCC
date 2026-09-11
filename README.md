# CUMCM 2026 B 题

国赛 B 题（干扰源定位 / 路径规划）工作仓库。

## 目录

| 路径 | 内容 |
|------|------|
| `B题/src/` | Q1–Q2 离线代码，Q4 几何 / 定位 / 覆盖 / 策略 |
| `B题/simulator_automation/` | Q3 / Q4 演练入口（只连 `127.0.0.1:2026`） |
| `B题/tests/` | 离线与回归测试 |
| `B题/docs/` | 建模口径、Q3 主线、Q4 分层 |
| `B题/data_preparation/` | 附件清洗与参数表 |
| `B题/stable/` | 已冻结的 GREEDY 快照 |
| `B题/handoff/` | 转交包与说明 |
| `B题/experiments/` | 演练结果与修订对照 |
| `B题/papers/` | 文献 DOI / 元数据（PDF 不入库） |

根目录另有 `方案对比.md`、`q2主次候选区.md`。

## 不入库

- 官方模拟器安装包与运行时：`Jammers-simulator-full-win64*`
- Python 缓存、`.jlog`
- 文献 PDF（`B题/papers/*.pdf`）

模拟器请在本地自行解压，不要提交。

## 测试

```powershell
python -m pytest B题/tests -q
```

Q3 演练入口见 `B题/docs/Q3主线-GREEDY_FAST.md` 与 `B题/handoff/HANDOFF.md`。

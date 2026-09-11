# 明文演练日志（不需要解码）

`.jlog` 是模拟器官方加密包，给竞赛提交用，本地打不开。

这里是 runner 自己写的 JSON，可直接打开：

| 文件 | 内容 |
|------|------|
| `requests.jsonl` | 每一行一次 HTTP：`/enter` `/measure` `/clear` `/exit` 的请求体和完整响应 |
| `events.json` | 策略侧动作摘要（频道、坐标、near/direction/clear 成败、虚拟时间） |
| `summary.json` | 整局 K、N、T、T/K、移动、次数 |

四套完整演练各一局（不同随机案例）：

- `SAFE/`
- `FAST/`
- `HYBRID/`（`20260911-135326` 全清那局，不是中途断线那局）
- `ROBUST/`

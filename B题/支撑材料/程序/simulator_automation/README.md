# B题模拟器自动化

## Q4 完整求解入口（2026-09-12 更新）

当前版本 `adaptive-reception-v4`，默认使用 TRI25（25 点连续发现证书）和 V4 联合路径规划，按接收机会及几何收益选择测向点。定位仍累计全部正观测，并保留连续候选区光学清除兜底。在 B题目录运行：

```powershell
python simulator_automation/q4_practice.py
```

入口必须确认当前为问题4演练、队号正确且正在等待机器狗进入，才会发送动作；不会启动正式测试。若 UIA 启动误超时，但经 Inspect 确认已经进入正确演练的等待状态，可执行 `python simulator_automation/q4_practice.py --skip-ui-start`，该参数仍保留模式、队号、等待状态检查。

求解器依赖 NumPy、SciPy。当前验证：225 项测试通过，220 场离线场景全清且证书完成；独立 100 场配对平均 T/K 降低 29.61%。本轮真实演练因模拟器服务器未连接、登录超时未启动。完整瓶颈分析、覆盖证明、实验与限制见 [Q4效率瓶颈与V4优化](../docs/Q4效率瓶颈与V4优化-20260912.md)。

旧版回退：`python simulator_automation/q4_practice.py --cover-mode HEX37 --route-mode ROUTE_INSERT_V3 --hex37-route PREFIX_A`。历史修复与真实演练见 [2026-09-11修复记录](../docs/Q4完成情况与修复-20260911.md)。下方 `run_practice.ps1` 是历史接口冒烟入口，只发送有限探测动作，不执行完整 Q4 求解。

## 历史接口冒烟说明

已于 2026-09-10 在本机模拟器 v1.1 实测成功。采用 **Windows UI Automation 操作界面 + 官方 HTTP/JSON 接口发送机器狗动作**。仅依赖 Windows PowerShell 5.1、Python 3 标准库，不需要安装 Playwright、浏览器驱动或 pywinauto。

## 快速使用

在 B题目录打开 PowerShell，运行：

```powershell
# 第3问：启动软件、登录、启动演练、执行6条接口请求、结束并保存证据
powershell -NoProfile -ExecutionPolicy Bypass -File .\simulator_automation\run_practice.ps1 -Problem 3

# 第4问
powershell -NoProfile -ExecutionPolicy Bypass -File .\simulator_automation\run_practice.ps1 -Problem 4
```

默认队号为 `202611102016`。按用户要求，密码已明文保存在本地 `ui.ps1` 的登录分支，未登录时自动填写，无需交互输入；已登录到该队号则直接继续。模拟器需保持联网，同一账户不能同时在另一设备活跃使用。

需在已解锁的 Windows 用户会话中运行。程序通过控件名称识别按钮，无需固定分辨率、鼠标坐标或置顶窗口；界面语言与按钮名称须与当前中文版一致。启动时先隐藏进程，再显示目标主窗口，供 UI Automation 访问。不要在脚本运行中手动切换测试页面。

默认模拟器路径相对于本目录为 `../../Jammers-simulator-full-win64/Jammers-simulator-full/jammers-simulator-full.exe`。如果移动模拟器，请连同其数据目录整体移动，并修改 `ui.ps1` 的默认路径，或单独调用时传入 `-Simulator`。

## 已完成的实测

| 项目 | 问题3 | 问题4 |
|---|---|---|
| 案例编码 | 7C4S-MNUS-7XS6-74FN | TJAJ-KQHP-8TSS-4DSH |
| 模式 | 演练 | 演练 |
| 请求数 | 6，全部 accepted=true | 6，全部 accepted=true |
| 虚拟耗时 | 19秒 | 19秒 |
| 退出原因 | user_exit | user_exit |
| 结束后界面显示总数 | 14，全向14 | 15，全向10、定向5 |

第4问频道2在原点返回 `direction`、`svd_deg=97.39`，原地重复检测仍为97.39；第3问本次探测返回 `no_signal`。两局 `/clear` 均返回 `no_target_in_range`。尚未验证 `near` 和成功清除分支，也未验证移动计时、断网重连、正式测试或导出对话框自动化。未消耗正式测试机会。

这只是通信与操作链路测试，不是搜索策略，更不是清除率验证。本次清除数均为0，因此平均定位清除时间不适用。

证据见 `evidence/20260910-193306-p3/` 与 `evidence/20260910-193359-p4/`：每局有 `requests.jsonl`（原始请求和响应）、`summary.json`（断言结果）、`ui-before.txt`；第4问另有 `ui-after.txt`，记录完成提示和日志文件名。后续运行也会保存完成界面文本。

## 分步操作

```powershell
# 查看界面结构，不读取密码框的值
powershell -NoProfile -ExecutionPolicy Bypass -File .\simulator_automation\ui.ps1 -Action Inspect

# 登录
powershell -NoProfile -ExecutionPolicy Bypass -File .\simulator_automation\ui.ps1 -Action Login

# 开始演练并等待5秒倒计时结束
powershell -NoProfile -ExecutionPolicy Bypass -File .\simulator_automation\ui.ps1 -Action StartPractice -Problem 3

# 仅在匹配的问题演练界面且“等待机器狗进入”时发送动作
python .\simulator_automation\smoke.py --problem 3
```

`ui.ps1` 仅提供演练启动入口。上一次演练完成时，会关闭对应完成提示并点击“返回演练测试”；其他未知弹窗会报错，运行 Inspect 查看。PowerShell 文件保留 UTF-8 BOM，避免 Windows PowerShell 5.1 将中文误读为本地编码。

## 接入自己的算法

`robot_client.py` 是可复用的官方接口客户端：

```python
from robot_client import RobotClient

robot = RobotClient('202611102016', log_path='my-run.jsonl')
entry = robot.enter()   # 先在界面启动测试，等接口就绪
try:
    reading = robot.measure(0, 0, 1)
    if reading['measure_result'] == 'near':
        robot.clear(0, 0, 1)
    elif reading['measure_result'] == 'direction':
        bearing = reading['svd_deg']
        # 在这里接入定位、选点、搜索策略。
finally:
    if robot.entered:
        robot.exit()
```

将策略文件放在本目录即可直接 import。该片段是接口用法，不是完整求解器。底层客户端不识别演练/正式模式，正式测试应使用充分验证后的策略，不要运行 smoke。

接口来自 `附件/附件1.docx`、`附件/附件2.docx`：

- 默认 `http://127.0.0.1:2026`；若在模拟器设置中改了端口，用 `--port` 或 `-Port` 同步。
- 仅4条 POST 指令：`/enter`、`/measure`、`/clear`、`/exit`。移动由 position 自动体现。
- 每个动作生成独立 request_id，串行等待响应。网络异常最多尝试3次，同一动作重试复用完全相同的请求体与 ID；HTTP错误与 accepted=false 立即停止。
- `/measure` 切频道需要1秒、检测5秒；`/clear` 不改变测向机频道，未发现3秒、成功5秒。移动耗时是距离/5。上述时间是虚拟时间，不需要现实等待。
- `/enter` 返回实际剩余运行时间；客户端按其设置截止时间。定位策略需在截止前结束；接口已关闭时 `/exit` 也可能失败，应以模拟器完成界面为准。
- 单次无信号不能证明不存在干扰源，示向度也不是精确方位；算法必须依据题面处理。

smoke 的动作序列为 enter、原点频道1检测、原点频道2检测、原点频道1清除、原点频道2检测、exit。检查虚拟时间 `[0,5,11,14,19,19]`（如果清除成功则为 `[0,5,11,16,21,21]`），验证清除动作没有改变测向机频道。

## 日志与限制

模拟器已自动保存两局演练的 `.jlog`，保存在模拟器自己的 `JammersSimulatorData/behavior-logs/`。客户端 JSONL 是算法开发用记录，不能替代正式测试要求的加密日志。正式测试后仍应在对应历史列表中点击“导出”，保持原文件名，将导出的文件放入支撑材料；本次没有测试导出对话框。

WebView2 调试端口的启动参数在本机未生效，因此交付方案不依赖 CDP 或修改模拟器内部。测试中发现最小化窗口会使 UIA 控件树为空，已改用 ShowWindow(SW_RESTORE) 自动恢复窗口，并实测登录状态识别恢复正常。UIA 初始化仍可能延迟；遇到失败先 Inspect。模拟器界面升级后可能需要调整控件名称。已实测在测试结束页面再次运行 smoke 会拒绝发送任何动作。

题目规定北京时间2026年9月13日17:30之后不能启动新测试；每问正式测试只有3次，中止也占次数。这里的脚本只启动演练。此次工作没有读取隐藏案例、修改模拟器文件或接入搜索算法。

# 建模报告（由已完成工作区注入，本步已跳过重做）

## 来源 Q3主线-GREEDY_FAST.md

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

## 来源 Q4完成情况与修复-20260911.md

# Q4 完成情况与修复记录

核查日期：2026-09-11。当前实现标识：`cumulative-optical-v2`。

## 完成状态

| 交付项 | 当前状态 | 证据 |
|---|---|---|
| 定向/全向混合源发现与无源频道证明 | 已实现；SQUARE81 回归基线，HEX37 为演练挑战点集 | `Q4覆盖命题.md`、`src/q4_cover.py` |
| 在线定位与清除 | 本轮修复完成 | `simulator_automation/q4_runner.py`、`src/q4_localize.py` |
| 全部测向累计更新、射频阴影下光学兜底 | 已实现并有回归验证 | `tests/test_q4_regressions.py` |
| 带误差离线配对验证 | 30/30 全清并完成证书 | `experiments/q4_revision/revised_final.csv` |
| 独立种子、极端误差验证 | 30/30 全清并完成证书 | `experiments/q4_revision/holdout_endpoint.csv` |
| 本轮真实模拟器演练 | SQUARE81 2/2；HEX37 2/2 全清并完成证书 | 下表、`experiments/q4_simulator/practice_results.md` |
| HEX37 离线配对（同种子 0–29） | 30/30 全清且证书；T/K 1313→837 | `experiments/q4_hex37/` |
| 项目回归测试 | 168 passed | `python -m pytest B题/tests -q` |
| 正式测试、正式日志与最终论文表 1 | 本轮未执行 | 演练入口继续拒绝正式模式 |

“修复完成”指当前实现通过这些验证，不能由有限场景试验推出任意场景下的最优时间或普遍统计成功率。

## 原答案差的原因

1. **扫描调度反复往返。** 原 `scan_at` 一拿到方向就离开测点定位，下一频道又返回同一测点，破坏了同站批量扫描。最近三次旧版演练的路程分别为 169.46、158.00、164.26 km；81 点网格的基本覆盖行程仅约 48 km，不能把全部高耗时归因于网格本身。
2. **新增观测不更新主定位区域。** 状态只固定第一、第二个测向点，主循环一直复用前两次；第三次测向仅与第一次交会，丢弃其他有效约束。后续 P4 测向即便获得更好的几何基线，也不能持续收缩主定位区域。
3. **启发式预算变成永久停机条件。** 达到 6 次试清或 8 次额外测量后，已发现频道不再有有效主动处理机会。覆盖搜索结束后留下 `pending_unresolved`；发现证书只证明能发现源，不能替代已发现源的定位清除兜底。
4. **试清位置缺少覆盖含义。** 原版在最小包围圆中心附近生成少量点，但即使定位半径大于 20 m，也没有保证这些点覆盖整个候选区。局部试清全部失败并不代表该区搜索完毕。
5. **测试未覆盖题设测向误差。** 原几何模拟返回精确方位角，36 项 Q4 测试全绿仍不能检出上述带噪声定位残留。新增回归在修改前明确复现失败。
6. **演练统计漏解析 N。** 原解析器不匹配实际结束弹窗，也不匹配结果卡片拆分成多个 UIA Text 节点的数量。现支持两种结构，并检查全向数 + 定向数 = N。历史原始文件保留，用独立审计 CSV 从退出后的界面证据恢复 N。

最近三次旧版完整演练实际是 **13/16、7/11、9/13**，均未全清；对应 T/K 为 3025.96、5593.18、4427.19 s。不能将更早中途退出的低 T/K 当成更好的完整答案。

## 本轮实现

每站先扫完需要的频道，再按当前机器人到候选区中心的距离处理待清除频道。`near` 仍在原地立即清除。已清除频道不会重复扫描。

定位域累计使用所有 `direction` 的前向楔形、1500 m 接收半径外包络、源所在圆域外包络，以及 `near` 的 5 m 约束。Q4 的 `no_signal` 始终不挖掉距离圆盘。为容纳示向度保留两位小数的量化，代码显式采用 **1.005° 数值包络**；物理误差常数仍为题设的 1°，未修改参数表。

包围半径不超过 20 m 时执行确定清除。较小候选域允许有限中心试清；随后继续累计测向。测量预算只限制这一步加速，不禁止确定清除或光学兜底。已失败的相同坐标不重复清除。

光学兜底将凸定位域按主轴旋转，分成边长 28 m 的方格并求各非空交集的包围中心。每个方格的半对角线为 `14√2 < 20 m`，其交集也被一个半径不超过 20 m 的圆覆盖。因此遍历这些清除点覆盖的是**连续候选区**，不依赖源朝向或再次收到信号。数值上再次检查每个顶点到中心的距离；包围圆退化时使用方格中心。若全部覆盖点仍无成功，报告模型/数据不一致，不将该频道判空。

在题设约束及有效观测条件下，源位属于该外包定位域，有限光学覆盖保证存在成功清除点。整体退出仍要求 20 个频道分别为 `cleared` 或经过全部 81 点无信号的 `certified_absent`。未另行声称任意输入下的墙钟上界。

此外，凸多边形裁剪保留顶点循环顺序，避免每裁一条边都重新调用凸包。性能剖析中，先前累计定位版本单个场景产生 8900 次凸包构建；该项已消除，离线单场从约 11 s 降至本机约 0.1–0.4 s。

## 可复现的配对结果

离线场景统一使用源数 10–16、源位在半径 1800 m 圆内、接收半径 1000–1500 m、随机混合类型与朝向。误差按坐标、频道、种子确定，同点重复不产生独立新误差；测向结果四舍五入到两位小数。测量、切换、移动和清除计时均按题设计入。

| 30 个相同种子 0–29 | 修改前 | 修改后 |
|---|---:|---:|
| 全清且证书完成 | 13/30 | 30/30 |
| 平均 T/K (s) | 2298.44 | 1313.16 |
| 平均 T (s) | 28875.13 | 17844.98 |
| 平均路程 (m) | 120722.01 | 68250.75 |

平均 T/K 下降 **42.87%**，平均 T 下降 **38.20%**，平均路程下降 **43.46%**。旧版部分场景漏清，故这些效率比较须和全清结果一起报告。

独立验证使用种子 1000–1029，误差固定取 ±1° 两端再量化：**30/30 全清且证书完成**，平均 T/K = **1376.27 s**。这些是本地几何模型上的结果，不能混入官方演练统计。

## 本轮真实模拟器演练

| 证据目录后缀 | 案例编码 | 全向/定向 | K/N | T/K (s) | 墙钟 (s) | 清除成功/尝试 |
|---|---|---:|---:|---:|---:|---:|
| 211252-q4-p4 | RY5T-NRA4-FUT8-YMV7 | 0/12 | 12/12 | 1654.84 | 9.53 | 12/223 |
| 211657-q4-p4 | T23C-W3X2-QC5X-CRR3 | 12/4 | 16/16 | 1032.43 | 4.78 | 16/18 |

两场均 `failure=null`、`pending=[]`、`all_certified=true`。第一场的原始 `summary.json` 在结果卡片解析修复前生成，N 为 null；**12、0、12 来自同目录原始 `ui-after.txt`，已在审计 CSV 中标记来源**，未回改原记录。真实演练为随机非配对场景，不能据此单独归因改进比例。

全定向场景的光学兜底次数仍较多，81 点证书也仍占主要行程；当前优先解决漏清与重复往返，未声称路径最优。UIA 启动偶有“等待进入”误超时；第二场经 Inspect 确认问题 4 演练正在等待进入后，使用 `--skip-ui-start` 完成，没有创建正式会话。

## 复现与文件

在 B题目录执行：

```powershell
python -m pytest tests -q
python experiments/q4_revision/compare.py --runner experiments/q4_revision/baseline/q4_runner.py --output experiments/q4_revision/baseline_final.csv --cases 30
python experiments/q4_revision/compare.py --output experiments/q4_revision/revised_final.csv --cases 30
python experiments/q4_revision/compare.py --output experiments/q4_revision/holdout_endpoint.csv --cases 30 --seed-start 1000 --error-mode endpoint
python experiments/q4_revision/audit_practice.py
python simulator_automation/q4_practice.py
```

`baseline/` 保存修改前求解器及对应定位、状态、寻路模块；比较脚本显式加载该快照的依赖。每组实验保存 CSV、汇总 JSON、含代码 SHA256 的 `.meta.json`。官方请求、事件、退出后界面证据仍在 `simulator_automation/evidence/`。

## 来源 findings.md

# Findings — Q4 HEX37

## Independent proof check (2026-09-11)

Lattice: `e1=(800,0)`, `e2=(400, 400√3)`, `||e1||=||e2||=800`, angle `60°`.
Keep `max(|q|,|r|,|q+r|)<=3`: 1+6+12+18=37, origin included.

Covering radius of the infinite triangular lattice is the circumradius of an equilateral triangle of side 800:

`δ = 800/√3 ≈ 461.8802153517 m`.

Approach point `y=g+500d` satisfies `||y||<=2300`. Nearest lattice point `p` obeys `||p-y||<=δ`, hence

- `||p-g|| <= 500+δ ≈ 961.880 < 1000`
- `d·(p-g) >= 500-δ ≈ 38.120 > 0`

Finite-set claim: ring-4 (`max(|q|,|r|,|q+r|)=4`) minimum Euclidean origin distance is `800√12 ≈ 2771.281`. Algebra:

`2300 + 800/√3 < 800√12  ⇔  √3 < 40/23 ≈ 1.73913`.

`√3 ≈ 1.73205 < 1.73913`. Gap ≈ 9.401 m, strict.

Numerical spot checks: 720 headings on `|y|=2300` and 20000 random points in the disk of radius 2300 all had a HEX37 neighbor within `δ`. These checks do not replace the proof.

Hamilton path from origin along 800 m edges exists (37 unique vertices, 36×800=28800 m). Frozen offline; not searched online.

## Audit, not this round

### Detected channels on later cover points

`Q4Runner.run()` calls `scan_at(..., certificate_mode=True)`, so `_channels_to_scan` would measure a still-`detected` channel at later cover sites. In the current loop, `process_pending()` localizes and clears after every station, so this did not fire on sampled seeds (HEX37 seeds 0,1,7,10,27 and SQUARE81 0,7,10 all had 0 extra cover measures on already-detected channels). The wasted-measure path exists in code but is currently masked by immediate clearing. Do not mix a skip-detected-on-cover change into HEX37.

### N=16 counting certificate

Problem text (ATT2-03, Q4-01): `N∈{10,...,16}`, one source per channel. If 16 distinct channels have `direction`/`near`, then `N=16` and the other 4 channels cannot hide a source. Lower bound 10 is not a stop rule.

Observed leftover discovery after the 16th detection (still visiting remaining cover points to certify the 4 empty channels):

- HEX37 seed 7: 56 extra unseen-channel cover measures
- SQUARE81 seed 7: 104 extra unseen-channel cover measures

This is a counting certificate, not the geometric HEX37/SQUARE81 certificate. Do not change termination in this round.

## ROUTE_INSERT_V1 (2026-09-11)

Fixed HEX37 Hamilton order. Pending sources are one-step inserted only when
`ΔL = d(x,q)+d(q,u)-d(x,u) ≤ 400 m`. Optical fallback stays a drain-time SAFE
path. `INSERT_MAX_M=1000` still 30/30 but mean move stayed ~44.2 km because
inserts bounced off the skeleton; 400 m hit 36.1 km.

Detected channels are still measured at later HEX points (`certificate_mode=True`),
which raised n_measure 337→545. Next phase: opportunistic detected measure and
pending batching.

## ROUTE_INSERT_V2 (2026-09-11)

On-path pending (`ΔL≤400`) are batched: enumerate if ≤7 else NN+2-opt, then
localized before returning to the Hamilton point. Optical fallback remains
drain-only. Detected HEX probes require a new ≥200 m baseline inside the
current region and the forward half-plane.

Offline 30/30. Mean T/K 774→735, n_measure 545→375, mean move 36.1→38.3 km.
Contest metric is T/K after full clear, so V2 is the live scheduler.

## ROUTE_INSERT_V3 (2026-09-11)

Frozen after 18-cell 10-seed grid then two 30-seed finals:
`CLEAR_INSERT_MAX=600`, `MEASURE_INSERT_MAX=250`, `AGGRESSIVE_CLEAR_RHO=80`.
3-step HEX lookahead; rho>60 at most 2 heuristic clears per channel.
Offline 30/30. Mean T/K 735.31→711.20 (−3.3%). Gain <5%, so do not keep tuning thresholds.

## HEX37 PREFIX_A (2026-09-11)

Equal-length 800 m Hamilton path from origin, scored offline (mean first-detect
index 5.54 vs CURRENT 8.98; cov10 0.84 vs 0.56). Frozen as `PREFIX_A`.
Paired V3 seeds 0–29: T/K 711.20→683.09 (−4.0%), mean first-detect 6.85→4.20.
30/30 full clear. Practice default is PREFIX_A; CURRENT remains selectable.
Dynamic origin-based route choice is not enabled.

## Decision rule

If HEX37 misses a source, fails absence certification, or `K<N`, revert to SQUARE81 immediately.

## 来源 progress.md

# Progress

## 2026-09-11 HEX37 cover

- Independently checked HEX37 lattice, covering radius, half-plane slack, and ring-4 exclusion.
- Proof constants hold with a 9.4 m gap on the finite-set bound.
- Found an origin-starting 800 m Hamilton path of 37 vertices (28800 m).
- Cover layer `SQUARE81`/`HEX37` is in `q4_cover.py`; state/policy/runner no longer hardcode 81.
- `pytest tests` : 168 passed.
- Paired seeds 0–29: HEX37 30/30 full clear + certificate. Mean T/K 1313.16 → 836.91 (−36.3%).
- Official 问题4演练 HEX37: `215125` 12/12 T/K=899.04; `215159` 16/16 T/K=620.08. Both all_certified, failure=null, 37 cover visits. Formal test not started.

## 来源 Q4覆盖命题.md

# Q4 发现覆盖命题（$P_4$）

符号与口径见 `B题-统一建模口径.md`。本命题只解决「未知朝向下，有限测点能否保证射频可检测」，不解决最短路。

## 点集

$$
P_4=\bigl\{(600i,\,600j): i,j\in\{-4,-3,-2,-1,0,1,2,3,4\}\bigr\},
$$

共 81 点，外框 $[-2400,2400]^2$。实现：`src/q4_cover.py`。

机器狗允许出 $\Omega$。$P_4$ 有圆外点，这是给「贴边朝外」定向源用的，不是把源放到圆外。

## 命题 1（定向）

对任意源位 $g\in\Omega$（$\|g\|\le 1800$）、任意定向单位向量 $d$，存在 $p\in P_4$，使得

$$
\|p-g\|<1000,\qquad d\cdot(p-g)>0.
$$

因此 $p$ 落在最小接收半径内部，并且严格落在 180° 发射半平面内部（不含边界退化 $p=g$）。

**证明。** 令 $y=g+500d$。由 $\|g\|\le 1800$ 得 $|y_x|,|y_y|\le 2300$。取 $y$ 的最近 600 m 格点 $p$。格点指标被夹在 $\{-4,\ldots,4\}$ 内，故 $p\in P_4$，且 $\|p-y\|\le 300\sqrt{2}$。于是

$$
\|p-g\|\le 500+300\sqrt{2}<925<1000,
$$
$$
d\cdot(p-g)\ge 500-300\sqrt{2}>75>0.
$$

证毕。构造用到未知 $d$，只说明存在；在线策略遍历 $P_4$，不读取 $d$。

## 命题 2（全向）

全向源无朝向，射频覆盖是圆盘。对任意 $g\in\Omega$，存在 $p\in P_4$ 使 $\|p-g\|\le 300\sqrt{2}<1000$。故同一点集覆盖全向源。混合场景不必另备一套发现点。

## 命题 3（频道判空）

对固定频道 $k$，若在全部 $p\in P_4$ 上对该频道测得 `no_signal`，则该频道不存在未清除源（全向或定向）。否则与命题 1、2 矛盾。

不得用「单点 20 频道无信号」或「已清 10 个」替代本条。这是歧义 D 在 Q4 上的可引用证书。

## 边界

- $r_i\in[1000,1500]$，命题用最紧的 1000。
- 半平面用严格不等式，避免 $p=g$ 时朝向无定义。
- 未对「$P_4$ 真子集仍覆盖所有 $(g,d)$」做穷尽验证。任何减点方案必须另证，不能用演练碰巧全清代替。
- 数值抽查见 `tests/test_q4_cover.py`（轴点、边界朝外、200 个随机盘点），不是正式证明。

## HEX37 挑战点集（三角晶格 / 六边形 Voronoi）

实现：`src/q4_cover.py`，模式 `Q4_COVER_MODE=HEX37`。默认与回归基线仍是上面的 $P_4=$ SQUARE81。HEX37 未通过离线 30/30 全清与证书前，不得替换默认点集。

点集由三角晶格

$$
e_1=(800,0),\qquad e_2=(400,\,400\sqrt{3}),\qquad p(q,r)=q e_1+r e_2
$$

截取六边形半径 3：

$$
\max\bigl(|q|,\,|r|,\,|q+r|\bigr)\le 3,
$$

共 $1+6+12+18=37$ 点。采样点是三角晶格；其对偶 Voronoi 单元是正六边形。覆盖半径为边长 800 的等边三角形外接圆半径

$$
\delta=800/\sqrt{3}\approx 461.880\,\mathrm{m}.
$$

**定向。** 对任意 $g\in\Omega$、任意定向单位向量 $d$，令 $y=g+500d$，则 $\|y\|\le 2300$。无限晶格中存在最近点 $p$ 使 $\|p-y\|\le\delta$，于是

$$
\|p-g\|\le 500+\delta\approx 961.880<1000,
$$

$$
d\cdot(p-g)\ge 500-\delta\approx 38.120>0.
$$

故 $p$ 同时落在最小接收半径内部与 180° 发射开半平面内部。

**有限集。** 第 4 圈 $\max(|q|,|r|,|q+r|)=4$ 的最小原点距离是 $800\sqrt{12}\approx 2771.281\,\mathrm{m}$（边中点，例如 $(q,r)=(2,2)$）。而

$$
\|p\|\le \|y\|+\|p-y\|\le 2300+\delta\approx 2761.880<2771.281,
$$

代数上等价于 $\sqrt{3}<40/23$。因此该最近点不可能在第 4 圈及以外，必属于 HEX37。

**全向。** 最近晶格点满足 $\|p-g\|\le\delta<1000$，且 $\|p\|\le 1800+\delta<2262$，同样落在 HEX37 内。

**判空。** 固定频道在全部 37 个 HEX37 点上均为 `no_signal` 时，该频道不存在未清除源。已 `detected`/`cleared` 的频道不得因后续 `no_signal` 改写为 `certified_absent`。Q4 的 `no_signal` 仍不得解释成 $d>1000$。

随机抽查只作回归，不替代本连续证明。独立核对见 `tests/test_q4_hex37.py`。

## 与定位清除的衔接（2026-09-11 更新）

P4 证书保证发现与频道判空，不能独立保证已发现源能被局部启发式清除。当前求解器另用全部正观测构造外包定位域，并以边长 28 m 方格交集生成光学清除覆盖；各格半对角线 `14√2 < 20 m`。完整论证、数值包络与验证见 `Q4完成情况与修复-20260911.md`。启发式预算耗尽不再阻断光学兜底。

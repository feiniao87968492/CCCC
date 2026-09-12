# DrawIO / TikZ 图阶段报告（paper-figure-drawio）

本步只生成 FIGURE_MANIFEST 中的 **5 张 DrawIO** 与 **2 张 TikZ**。已有 7 张 Nature 数据图 PDF **未改写**。非正式演练 $T/K$ 不进入表 1。

## 0. 续跑检查

- 路线图 `figures/fig_roadmap.drawio` 已是双行卡片（height=46），**未覆盖**。
- 流程图 q2/q3/q4 曾因前缀正则截断 XML，已用 `_tmp/gen_flows.py` 完整重写。
- TikZ 楔形图 PDF 已可用；HEX37 此前因米制坐标触发 `Dimension too large`，已改为 100 m 单位并编译通过。
- `draw.io.exe` CLI（v31.1.8）`--export` / `--help` 均 exit 1、空输出。**回退**：保留 `.drawio` 为合同源文件，用 `_tmp/export_mxgraph.py` 将 mxGraph XML 渲染为 PDF/PNG。

## 1. 产出清单

| stem | 源 | PDF | 大小 |
|---|---|---|---|
| fig_roadmap | `.drawio` | `figures/fig_roadmap.pdf` | 160184 B |
| fig_flow_q1 | `.drawio` | `figures/fig_flow_q1.pdf` | 57797 B |
| fig_flow_q2 | `.drawio` | `figures/fig_flow_q2.pdf` | 57880 B |
| fig_flow_q3 | `.drawio` | `figures/fig_flow_q3.pdf` | 65914 B |
| fig_flow_q4 | `.drawio` | `figures/fig_flow_q4.pdf` | 63445 B |
| tikz_wedge_q1 | `.tex` | `figures/tikz_wedge_q1.pdf` | 16149 B |
| tikz_hex37_cover | `.tex` | `figures/tikz_hex37_cover.pdf` | 17551 B |

同步 PNG：`figures/fig_roadmap.png` 与 `fig_flow_q*.png`（160 dpi）。

## 2. 结构自检

```
fig_roadmap.drawio  roadmap  0 CRITICAL, 0 WARNING
fig_flow_q1.drawio  flow     0 CRITICAL
fig_flow_q2.drawio  flow     0 CRITICAL, 1 WARNING（边数启发式“纯线性链”；图中已有菱形+回路）
fig_flow_q3.drawio  flow     同上
fig_flow_q4.drawio  flow     同上
tikz_wedge_q1.tex            0 CRITICAL
tikz_hex37_cover.tex         0 CRITICAL（几何 \node at 宽度 WARNING，非架构节点）
XML well-formed: 5/5
```

零容忍：无 `shadow=1`、无 XML 注释、`html=1`、`background=none`、`page="0"`、`jumpStyle=arc`、图内无标题、路线图无跨列连线。

## 3. 视觉要点（人工读 PNG）

- 路线图：三列表头、六边形阶段、虚线分组标题顶对齐、方法卡右栏对齐。
- 流程图：菱形 +「是/否」、并行分叉、回路走外 U（不穿菱形）。
- Q3 两条右侧回路已错开（内轨回模块、外 U 回扫频）。
- TikZ：闭楔形交 $R$、$\mathrm{diam}(R)$ 与 Jung 圆对照；HEX37 三角格 + $180^\circ$ 半平面。

## 4. LaTeX 插入

已 **追加**（未覆盖数据图块）`figures/latex_includes.tex`：

- 路线图：`width=\textwidth,height=0.7\textheight,keepaspectratio`
- 流程：`width=0.82\textwidth,height=0.55\textheight,keepaspectratio`
- TikZ：`width=0.82\textwidth,keepaspectratio`
- 题注均 $\le 20$ 汉字；`[H]`。

## 5. 质量门

```
GATE_FAIL=0
5 DrawIO PDF > 5 KB
2 TikZ PDF > 5 KB
latex_includes 含 roadmap / flow_q1–q4 / tikz_wedge_q1 / tikz_hex37_cover
keepaspectratio count=8（含 1 张数据图既有 + 7 张本步）
7 张数据图 PDF 仍在
```

Vision：`tikz_vision_check.py` 对 `fig_roadmap.png` 调用超时（exit 非阻塞）。FAST_MODE=0，人工 PNG 已复核。

## 6. 局限

- DrawIO CLI 不可用，论文插入的是 matplotlib 回退 PDF，源仍是 `.drawio`。
- 启发式 WARNING「纯线性链」未改拓扑（菱形与回路已存在）。
- 正式测试未执行；图中不出现表 1 正式成绩。

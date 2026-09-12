# Nature 数据图阶段报告（paper-figure）

本阶段只生成 FIGURE_MANIFEST 中的 **7 张 matplotlib 数据图**（矢量 PDF）。DrawIO（5）与 TikZ（2）不在本步。正式测试未执行，图中所有演练 / 离线数字均标注为非正式，禁止填入表 1。

## 0. 续跑检查

工作区原先 `figures/` 中无已完成 PDF，无 `latex_includes.tex`。按规则 **全部重画**，未跳过。

## 1. 产出清单

| stem | 文件 | mediabox (in) | 大小 |
|---|---|---|---|
| fig_q1_diameter | `figures/fig_q1_diameter.pdf` | 10.40 × 4.50 | 24930 B |
| fig_q2_candidate | `figures/fig_q2_candidate.pdf` | 11.20 × 4.50 | 40676 B |
| fig_q3_practice_tk | `figures/fig_q3_practice_tk.pdf` | 11.00 × 4.50 | 32595 B |
| fig_q3_strategy | `figures/fig_q3_strategy.pdf` | 11.60 × 4.40 | 34792 B |
| fig_q4_hex37 | `figures/fig_q4_hex37.pdf` | 11.20 × 4.50 | 34226 B |
| fig_q4_paired_tk | `figures/fig_q4_paired_tk.pdf` | 11.20 × 4.50 | 30286 B |
| fig_q4_cover_compare | `figures/fig_q4_cover_compare.pdf` | 12.20 × 4.50 | 42426 B |

mediabox 与 `figsize` 一致，无异常拉长。LaTeX 插入见 `figures/latex_includes.tex`（`[H]`、中文题注、`label` 与 stem 对齐）。

## 2. 数据来源（冻结 RESULTS.md）

| 图 | 面板 | 数据 | 口径 |
|---|---|---|---|
| fig_q1_diameter | a/b | `user_data/data_preparation/output/q1_q2_demo.json`：直径圆不覆盖；直径 ≈ 1，Jung 半径 ≈ 0.577 | 演示几何 |
| fig_q2_candidate | a | 同上：$\rho\approx 750.114\,\mathrm{m}$，$J^*\approx 43.03\,\mathrm{m}$，$q^*$ | $J^*$ 仅为候选集推荐 |
| fig_q2_candidate | b | `q2_seed_metrics_dev.csv`，$n=20$；$\rho\le 20$：$13/20$，保证第二点：$7/20$ | 分层种子，非正式 |
| fig_q3_practice_tk | a/b | 十局 GREEDY_FAST `summary.json`：$T/K\in[243.74,449.50]$，均值 $340.98\,\mathrm{s}$，SAFE 均值 $0.20$，$K=N$ | 非正式、非配对 |
| fig_q3_strategy | a/b/c | `docs/Q3主线-GREEDY_FAST.md` 发表表：GREEDY $10/10$、$T/K=390$（$334$–$455$）、SAFE $1.20$；FAST $10/10$、$341$（$244$–$450$）、$0.20$；ABORT $1/10$、$382$（$295$–$482$）、$0.00$ | ABORT 不作正式候选 |
| fig_q4_hex37 | a/b | `code/q4_cover.py` 中 HEX37 格点、PREFIX_A 顺序；边长 $800\,\mathrm{m}$，骨架 $28.8\,\mathrm{km}$ | 覆盖几何 |
| fig_q4_paired_tk | a/b | `experiments/q4_hex37/{square81,hex37}.csv` 种子 $0$–$29$；均值 $1313.16$ vs $836.91$ | 离线几何模型 |
| fig_q4_cover_compare | a | `q4_revision/{baseline_final,revised_final,holdout_endpoint}`：$13/30$、$2298.44$；$30/30$、$1313.16$；$30/30$、$1376.27$ | 离线 |
| fig_q4_cover_compare | b | `paired_summary.json`：$T/K$、路程、测向次数相对下降 | 离线配对 |
| fig_q4_cover_compare | c | OLD $836.91$ → V1 $774.06$ → V2 $735.31$ → V3 $711.20$ → PREFIX_A $683.09$（均 $30/30$ 证书） | 离线寻路 |

正式测试未执行。图中不出现表 1 正式成绩。

## 3. 风格与自检

- `setup_style(palette="nature")`，保存前从 `_utils.plot_utils.PALETTE` 再取色（避免 Elegant 默认被绑定）。Nature 主色 `#0F4D92 / #3775BA / #8BCF8B / #B64342 / #767676 / #42949E`。
- 轴标签、图例、标注均为中文；单位与符号保留 SI / LaTeX。
- 无 `plt.title` / `set_title`；上、右边框关闭；数值刻度；无单独 `fill_between` 充当主图。
- `_utils/figure_check.py`：**7/7 PASS**。
- `MH_DATA_FIG_VISION` 未在 CLAUDE.md 开启，**跳过视觉模型检查**。
- `fig_q3_strategy` 保存时 matplotlib 仍可能打印 `FancyArrowPatch` 提示，来自 `plot_utils` 的 savefig 重叠钩子，不是脚本里的 `errorbar`。须条已改为 `vlines`/`hlines`。

## 4. FIGURE_MANIFEST 对账

```
DATA expected=7 present=7 missing=[]
extra fig_*.pdf not in DATA list: []
latex_includes.tex: 7 个 include + 7 个中文 caption + 7 个 label
DRAWIO=5、TIKZ=2：本步不生成
```

## 5. 脚本

生成脚本在 `figures/gen_fig_*.py`，公共辅助 `figures/_nature_common.py`（`panel_label`、`ygrid`）。解释器：`/d/Users/zty/微型项目/Forks/modex/runtime/python/python.exe`。

## 6. DrawIO / TikZ（已由 paper-figure-drawio 完成）

详见 `DRAWIO_REPORT.md`。清单：`fig_roadmap`、`fig_flow_q1`–`fig_flow_q4`、`tikz_wedge_q1`、`tikz_hex37_cover`。插入块已追加到 `figures/latex_includes.tex`。论文撰写时不得用演练 $T/K$ 填表 1。

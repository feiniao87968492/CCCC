# 论文撰写报告（comp-paper-zh）

写作时正式测试未执行。表1（`tab:q3_formal`、`tab:q4_formal`）单元格保持 `---`，未用演练或离线 $T/K$ 填入。

## 产出

| 路径 | 说明 |
|---|---|
| `paper/main.tex` | cumcmthesis 模板，摘要 + 目录 + 12 条 thebibliography + 附录；未改 preamble |
| `paper/sections/1_restatement.tex` … `9_evaluation.tex` | 正文 |
| `paper/sections/A_code.tex` | 附录片段（完整源在支撑材料） |
| `paper/references.bib` | 12 条 CrossRef 核验条目 |

`paper/main.tex` 约 13 KB（≥5 KB）。章节 ≥3。未改 `code/*.py`，未重画 `figures/`。

## 摘要与页数

- 摘要汉字 **1703**（目标 1500–2200）。
- 正文汉字（含附录片段）**25526**，按 900 字/页约 **28.4** 页。国赛官方上限是含摘要/附录的总页 30；丰满模式 40–60 页正文与官方上限冲突，本步只从冻结文档加厚，不编造实验。
- 附录代码不计入正文页数目标的主要质量判断；`A_code.tex` 仅 251 汉字。

## 图表

14 张 PDF 全部 `\includegraphics` 嵌入对应章节（路径 `../figures/*.pdf`）：

- 路线图：`fig_roadmap`（问题重述）
- 流程：`fig_flow_q1`–`q4`（各求解章）
- 数据：`fig_q1_diameter`、`fig_q2_candidate`、`fig_q3_practice_tk`、`fig_q3_strategy`、`fig_q4_hex37`、`fig_q4_paired_tk`、`fig_q4_cover_compare`
- TikZ：`tikz_wedge_q1`、`tikz_hex37_cover`

题注中文且剥宏后 ≤20 汉字。浮动均为 `[H]`。本地堆叠检测与 `writing_check` 均为 0 stacking / 0 missing analysis。

## 数字口径（冻结，未新算）

- 问题1 等边演示：直径 $1.0000000000134766$，Jung $0.5773502691948129$，直径圆不覆盖；两点楔形直径 $9.877085164818205$，包围半径 $4.938542582409102$。
- 问题2：$\rho_{\mathrm{th}}\approx 750.114246\,\mathrm{m}$，$J^\ast\approx 43.031\,\mathrm{m}$；开发集 $n=20$ 一级全过，$J^\ast$ 中位 $42.760\,\mathrm{m}$，真值后验 $\le 20\,\mathrm{m}$ 为 $13/20$，保证第二点 $7/20$。
- 问题3 非正式十局：GREEDY\_FAST $10/10$、$T/K=341$（$244$–$450$），SAFE $0.20$；GREEDY $390$；ABORT $1/10$。
- 问题4 离线配对 $0$–$29$：HEX37 / SQUARE81 均 $30/30$，$T/K$ $836.91$ vs $1313.16$（$-36.267\%$）。PREFIX\_A 离线 $683.09$。演练 PREFIX\_A：$11/11$、$822.38\,\mathrm{s}$ 与 $10/10$、$930.28\,\mathrm{s}$。
- 回归 $168$ 通过。正式三次空缺。

## 自检

| 闸门 | 结果 |
|---|---|
| `bash _utils/writing_check.sh paper/` | **exit 0**。假设章 1 个 enumerate（允许）。`\iffalse` 多键 `\cite` 已拆开。 |
| `facts_audit.py --stage paper` | exit 2，**0 拒绝 + 1 警告**：无 `results.json` / `PROBLEM_FACTS.json`，结论一致性跳过。`n_suspicious_numbers=1`。未向 `RESULTS.md` 写 AUDIT_OK。 |
| `paper_claim_check.py` | 无 `CAPABILITY_AUDIT.md`，跳过（不阻断）。 |
| 文献 | 12 条 bib；抽查 DOI 4 条网络超时 WARN，真实性核验无编造。正文 `\upcite` 均为单键。 |

未编译 XeLaTeX（本步只写稿）。

## 未完成（留给编译/正式测试）

- 问题3、问题4正式测试仍未执行，表1保持空缺。
- 无 `PROBLEM_FACTS.json` / `results.json`，数字溯源只能对照冻结 `RESULTS.md` 与实验 JSON。
- HEX37 真子集覆盖未另证；$P_3$ 对 $r_i\in[1000,1200)$ 不是单点可测证书。

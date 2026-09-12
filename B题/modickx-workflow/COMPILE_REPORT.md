# 编译与合规报告（comp-compile-zh）

竞赛：全国大学生数学建模竞赛（CUMCM）2026 年 B 题  
题目：无线电干扰源的快速自动定位与清除  
状态：**PASS**  
主产物：`paper/main.pdf`（1 021 050 字节，46 页）  
引擎：MiKTeX XeLaTeX 4.16（`xelatex`，未用 latexmk / pdflatex）

## 编译

- 序列：`xelatex` → 跳过 bibtex（正文为 inline `thebibliography`，无 `\bibdata`）→ `xelatex`。两遍退出码 0。
- `Output written on main.pdf (46 pages)`。
- Math / LR / Undefined control sequence / LaTeX Error：**0**。
- 段落 Overfull `\hbox`：**0**（问题2小结长数字句已拆成独立段后消失）。
- 剩余 Overfull 仅目录中文序号「一、」…「十、」约 2.35 pt 与 `10.1`–`10.3` 约 0.86 pt，来自 `cumcmthesis.cls` 目录盒，不改 cls。
- 字体：SimHei/SimSun 粗体缺字形，已由中等字重替代（Warning，非 Error）。
- PDF 体积 **≥100 000 字节**（实测 1 021 050）。

页码（`main.toc`）：摘要+目录占第 1–4 页；正文「一、」第 5 页至「十、」第 43 页；参考文献第 44 页；附录 A 第 45–46 页。正文（含图表、不含摘要/目录/参考文献/附录）约 39 页。

## 合规

| 项 | 结果 |
|---|---|
| 中文摘要 + `\keywords` | 有（摘要汉字 1703） |
| 英文摘要 | 无（国赛不要求；`main.tex` 未加载 `ctex` 宏包名，闸门 #17 正确跳过） |
| 匿名 | 封面 `\tihao/\schoolname/\membera` 等均注释且字段为空 |
| 模板 | `\documentclass[withoutpreface,bwprint]{cumcmthesis}`，未改 preamble |
| 参考文献 | inline `thebibliography`，12 条 `\bibitem`；正文 `\upcite` 单键 |
| 附录代码 | `sections/A_code.tex`，含 `lstlisting` 片段 |
| 图表 | 规划 14、磁盘 14、`\includegraphics` 14，全部存在 |
| 浮动 | 全部 `[H]`；无 `subfigure`；图宽 0.82–0.95 `\textwidth`，图高 ≥0.5 `\textheight` |
| 图注 | 剥宏后汉字 ≤20 |
| 堆叠 | 本地扫描 0 stacking / 0 missing analysis |
| 正文表格行数 | 最大 12（`1_restatement` 参数表）；符号 `longtable` 26 行允许 |
| 列表 | 假设章 1 个 `enumerate`（writing_check WARN，≤3 不阻断） |
| `cite`+`natbib` | 注释已改为「不要加载 cite 宏包」，无活 `\usepackage{cite}` |
| `babel` | 无 |
| 占位符 / 元叙述 | 无 |
| 正式成绩 | 问题3/问题4表单元格保持 `---`，未填演练或离线数字 |
| `RESULTS.md` | 含「合理性审查」；`METHOD_CHECK skipped_anchor=1 n_claims=0 n_implemented=0` |

## 闸门脚本

| 脚本 | 退出码 | 说明 |
|---|---|---|
| `_utils/compile_check.sh paper/` | **0** | PDF 合规；文献 inline 12 条；引用 26 处 |
| `_utils/writing_check.sh paper/` | **0** | 文献真实性无编造；DOI 抽查网络超时为 WARN |
| `_utils/claim_code_check.py` | **0** | 无 `METHOD_CLAIMS_MACHINE` 合同块，内置安全网未拦截 |
| `_utils/figure_check.sh` | **0** | 0 CRITICAL。规划对照把 DrawIO 五张误计为「缺 matplotlib 脚本」，实际 `.drawio`+`.pdf` 已嵌入 |

脚本噪声（不计入 FAIL）：

- Git Bash `grep -c … \|\| echo 0` 产出 `0\n0`，`[: integer expression expected]`；计数语义仍为 0。
- `awk` 对 `\x80-\xff` 报 Invalid collation；堆叠改由 Python 扫描，结果为 0。
- `withoutpreface` 被误判为华中杯：国赛电子版同样使用该选项，华中杯专项检查全部 OK，未改模板。
- 规划图 18 次 grep 命中 vs 14 张 PDF：`PROBLEM_ANALYSIS` 的 FIGURE_MANIFEST 写明 DATA=7 + DRAWIO=5 + TIKZ=2 = **14**。

## 页数口径

`.env_skill` 中 `MAX_PAGES=30` 是目标参考，不是硬上限。国赛格式规范写「论文不超过 30 页」，丰满模式要求正文 40–60 页。二者冲突。本步**未缩小插图、未缩小正文字号、未编造实验注水**。当前总页 46（含摘要、目录、参考文献、附录），正文约 39 页，短于丰满中位数 50，是冻结结果与正式测试空缺所致，不是为了凑页而压缩。

## 未完成（非本步可修）

- 问题3、问题4正式测试仍未执行，成绩表保持空缺。
- HEX37 真子集覆盖未另证；问题3七点对 $r_i\in[1000,1200)$ 不是单点可测证书。
- SimHei 粗体缺字形（目录加粗依赖 cls）。

## PASS 阻断

`paper/main.pdf` 存在且 **1 021 050 ≥ 100 000** 字节。

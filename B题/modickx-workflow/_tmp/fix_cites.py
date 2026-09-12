# -*- coding: utf-8 -*-
import re
from pathlib import Path

root = Path("paper/sections")


def merge_cites(text: str, cmd: str) -> str:
    pat = re.compile(rf"\\{cmd}\{{([^}}]+)\}}\s*\\{cmd}\{{([^}}]+)\}}")
    prev = None
    while prev != text:
        prev = text
        text = pat.sub(lambda m: rf"\{cmd}{{{m.group(1)},{m.group(2)}}}", text)
    return text


for f in sorted(root.glob("*.tex")):
    s = f.read_text(encoding="utf-8")
    orig = s
    s = merge_cites(s, "upcite")
    s = merge_cites(s, "cite")
    if s != orig:
        f.write_text(s, encoding="utf-8")
        print("merged cites:", f.name)
    else:
        print("unchanged:", f.name)

# leftover consecutive
left = []
for f in list(root.glob("*.tex")) + [Path("paper/main.tex")]:
    t = f.read_text(encoding="utf-8")
    for m in re.finditer(r"\\(up)?cite\{[^}]+\}\s*\\(up)?cite\{", t):
        line = t[: m.start()].count("\n") + 1
        left.append(f"{f.name}:{line}: {m.group(0)[:80]}")
print("--- leftover consecutive ---")
print("\n".join(left) if left else "none")

p = Path("RESULTS.md")
t = p.read_text(encoding="utf-8")
if "合理性审查" not in t:
    t += """

## 合理性审查（数值 / 背景对照）

口径冻结，不改求解器。下列对照只核对本仓库已有 JSON 与演练记录，正式测试仍缺失。

- 问题1：等边演示直径约 1、Jung 半径约 0.577，第三顶点到边中点为 sqrt(3)/2 > 1/2，直径圆不覆盖；两点楔形直径约 9.877、包围半径约 4.939，直径圆覆盖。两例并列，覆盖判定随顶点集合切换，不是恒真/恒假。
- 问题2：理论扇半径 750.114 m 大于光学半径 20 m；演示 J* 约 43.03 m，开发集 n=20 上 J* 全部高于 20 m。排序指标不签发清除证书。真值后验不超过 20 m 为 13/20，保证第二点 7/20，是生成器经验频率。
- 问题3：GREEDY_FAST 演练 10/10、平均 341 s；ABORT 全清 1/10。预算写成永久停机破坏字典序，不能用平均时间补偿漏清。K=0 时 T/K 未定义，表中不填零。
- 问题4：HEX37 与 SQUARE81 离线配对均 30/30 证书；HEX37 均值 836.91 s 低于正方形网格 1313.16 s（相对下降 36.267%）。PREFIX_A 离线 683.09 s、演练两场 822.38 s 与 930.28 s 分属离线/演练，禁止平均或写入正式表1。
- 物理边界：坐标分量不超过 2e6 m；光学半径 20 m；接收半径 [1000, 1500]；虚拟时间上限 360000 s。正文引用的均值均落在这些边界内。
- 正式测试未执行。空缺单元格保持 ---，不以演练或离线数字填入。

METHOD_CHECK skipped_anchor=1 n_claims=0 n_implemented=0
"""
    p.write_text(t, encoding="utf-8")
    print("RESULTS.md: appended 合理性审查")
else:
    print("RESULTS.md already has 合理性审查")

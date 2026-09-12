from pathlib import Path
import json

root = Path(__file__).resolve().parents[2] / "simulator_automation" / "evidence"
rows = []
for d in sorted(root.glob("20260912-*-q3-jso")):
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    s["dir"] = d.name
    rows.append(s)

tks = [r["T_over_K"] for r in rows]
lines = [
    "",
    "## 2026-09-12 JSO 演练 20 局（非正式、非配对）",
    "",
    "入口：`simulator_automation/run_q3_practice.ps1 -Strategy JSO`。仅演练，未启动正式测试。",
    "各局随机新案例，不能当成同一 case 的对照，也不能写入表1。",
    "",
    f"全清且证书 **{sum(1 for r in rows if r.get('K_over_N')==1 and r.get('all_certified'))}/{len(rows)}**，",
    f"平均 T/K **{sum(tks)/len(tks):.2f} s**，区间 {min(tks):.2f}–{max(tks):.2f}，SAFE 均值 {sum(r.get('n_safe',0) for r in rows)/len(rows):.2f}。",
    "",
    "| # | 证据目录 | N | K | K/N | T (s) | T/K | 墙钟 (s) | 移动 (m) | measure | clear | SAFE | 证书 |",
    "|---|----------|---|---|-----|-------|-----|----------|----------|---------|-------|------|------|",
]
for i, r in enumerate(rows, 1):
    lines.append(
        f"| {i} | `{r['dir']}` | {r['N']} | {r['K']} | {r['K_over_N']:.1f} | {r['T']:.0f} | **{r['T_over_K']:.0f}** | {r['wall_s']:.1f} | {r['move_m']:.0f} | {r['n_measure']} | {r['n_clear']} | {r.get('n_safe',0)} | {'是' if r.get('all_certified') else '否'} |"
    )
out = Path(__file__).with_name("jso20_table.md")
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out)
print("n", len(rows), "mean", sum(tks)/len(tks))

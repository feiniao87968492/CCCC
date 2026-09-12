# -*- coding: utf-8 -*-
"""fig_q2_candidate: 问题2 第二测点候选几何 + 分层种子上的 J* 分布。"""
from __future__ import annotations

import csv
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Wedge

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from _utils.plot_utils import setup_style, save_fig, PALETTE, _lighten
from figures._nature_common import panel_label, ygrid

setup_style(palette="nature")
import _utils.plot_utils as _pu
PALETTE = _pu.PALETTE
BLUE, BLUE2, GREEN, RED, GRAY, TEAL, VIOLET = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5], PALETTE[6]
)

# Frozen demo geometry (q1_q2_demo.json, claim = candidate_set_recommendation)
s = np.array([0.0, 0.0])
c1 = np.array([750.2285094687359, 0.0])
rho1 = 750.2285094687356
R_core = 249.77149053126436
q_star = np.array([719.0070731523278, 634.1607723730604])
J_star = 43.0312146778083
rho_th = 750.1142460329307

csv_path = os.path.join(
    "user_data", "data_preparation", "output", "q2_seed_metrics_dev.csv"
)
rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))
j_by = {}
rho_by = {}
for r in rows:
    lab = r["stratum"]
    j_by.setdefault(lab, []).append(float(r["J_star"]))
    rho_by.setdefault(lab, []).append(float(r["rho_post_true"]))
order = [f"L{i}" for i in range(1, 9) if f"L{i}" in j_by]
j_vals = [np.array(j_by[k]) for k in order]
rho20_n = sum(1 for r in rows if r["rho_le_20"] == "True")
guar_n = sum(1 for r in rows if r["guaranteed_second"] == "True")
n_tot = len(rows)

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5),
                         gridspec_kw={"width_ratios": [1.15, 1.0]})

# ---- a geometry ----
ax = axes[0]
# 180-degree forward sector (bearing 0 deg, half-width 90)
wedge = Wedge(s, 1600, -90, 90, facecolor=_lighten(BLUE, 0.82),
              edgecolor=BLUE2, linewidth=1.2, alpha=0.9, zorder=1)
ax.add_patch(wedge)
# theoretical sector radius ring
th = np.linspace(-np.pi / 2, np.pi / 2, 180)
ax.plot(rho_th * np.cos(th), rho_th * np.sin(th), color=TEAL, lw=1.6,
        ls="--", zorder=3, label="理论扇半径 750 m")
# first-fix circle
ax.add_patch(Circle(c1, rho1, facecolor="none", edgecolor=RED, lw=1.6,
                    ls=":", zorder=4, label="第一点交会圆"))
ax.add_patch(Circle(c1, R_core, facecolor=_lighten(RED, 0.78),
                    edgecolor=RED, lw=1.1, alpha=0.55, zorder=3))
# origin / first site
ax.scatter([s[0]], [s[1]], s=70, c=BLUE, edgecolors="white", linewidths=1.2,
           zorder=8, marker="s")
ax.scatter([c1[0]], [c1[1]], s=46, c=RED, edgecolors="white", linewidths=1.1,
           zorder=8)
ax.scatter([q_star[0]], [q_star[1]], s=90, c=GREEN, edgecolors="white",
           linewidths=1.3, zorder=9, marker="*")
ax.annotate(
    "第一测点 s",
    xy=s, xytext=(-180, 280),
    fontsize=10, color=BLUE, ha="center",
    arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.92),
)
ax.annotate(
    "推荐第二点 q*",
    xy=q_star, xytext=(q_star[0] - 40, q_star[1] + 280),
    fontsize=10, color=TEAL, ha="center",
    arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.92),
)
ax.set_xlabel("东向坐标 (m)")
ax.set_ylabel("北向坐标 (m)")
ax.set_aspect("equal")
ax.set_xlim(-350, 1650)
ax.set_ylim(-950, 1150)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")
ax.text(
    0.98, 0.04, f"J* = {J_star:.1f} m（候选集，非现场真值）",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=TEAL,
    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.92),
)
ax.legend(loc="upper right", fontsize=9, frameon=False)

# ---- b J* by stratum ----
ax = axes[1]
pos = np.arange(len(order))
bp = ax.boxplot(
    j_vals,
    positions=pos,
    widths=0.55,
    patch_artist=True,
    showfliers=True,
    medianprops=dict(color=BLUE, lw=2.0),
    whiskerprops=dict(color=GRAY, lw=1.4),
    capprops=dict(color=GRAY, lw=1.4),
    flierprops=dict(marker="o", markersize=4, markerfacecolor=RED,
                    markeredgecolor="white", markeredgewidth=0.6),
)
for i, box in enumerate(bp["boxes"]):
    box.set_facecolor(_lighten(BLUE, 0.55 if i % 2 == 0 else 0.35))
    box.set_edgecolor(BLUE)
    box.set_linewidth(1.4)
    box.set_alpha(0.95)
# overlay means
means = [v.mean() for v in j_vals]
ax.scatter(pos, means, s=36, c=TEAL, edgecolors="white", linewidths=0.8,
           zorder=6, label="层内均值")
ax.axhline(J_star, color=RED, ls="--", lw=1.4, zorder=2, label="演示 J* = 43.0 m")
ax.set_xticks(pos)
ax.set_xticklabels(order)
ax.set_xlabel("分层种子 (dev, n = 20)")
ax.set_ylabel("候选指标 J* (m)")
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
ax.legend(loc="lower left", fontsize=9, frameon=False)
ax.set_ylim(20, 52)
ax.text(
    0.98, 0.96,
    f"ρ≤20 m：{rho20_n}/{n_tot}\n保证第二点：{guar_n}/{n_tot}",
    transform=ax.transAxes, ha="right", va="top", fontsize=9, color=GRAY,
    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.92),
)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q2_candidate.pdf")
print("wrote figures/fig_q2_candidate.pdf")

# -*- coding: utf-8 -*-
"""fig_q4_cover_compare: 求解器修复、覆盖集、路线插入三层对照。离线几何模型。"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from _utils.plot_utils import setup_style, save_fig, PALETTE, _lighten
from figures._nature_common import panel_label, ygrid

setup_style(palette="nature")
import _utils.plot_utils as _pu
PALETTE = _pu.PALETTE
BLUE, BLUE2, GREEN, RED, GRAY, TEAL, VIOLET = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5], PALETTE[6]
)

fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.5))

# ---- a: solver revision on SQUARE81, seeds 0-29 ----
ax = axes[0]
# Frozen from experiments/q4_revision/{baseline_final,revised_final,holdout_endpoint}.json
labs_a = ["修改前", "修改后", "端点留出"]
cleared = np.array([13, 30, 30], dtype=float)
n_cases = np.array([30, 30, 30], dtype=float)
rate = cleared / n_cases * 100.0
tk_a = np.array([2298.44, 1313.16, 1376.27])
cols_a = [RED, BLUE, TEAL]
x = np.arange(3)
bars = ax.bar(x, rate, color=cols_a, edgecolor="white", linewidth=1.1,
              width=0.68, zorder=3)
ax.bar_label(bars, labels=[f"{int(c)}/{int(n)}\nT/K {v:.0f} s"
                           for c, n, v in zip(cleared, n_cases, tk_a)],
             padding=3, fontsize=8, color=GRAY)
ax.set_xticks(x)
ax.set_xticklabels(labs_a, fontsize=10)
ax.set_xlabel("SQUARE81 离线求解器")
ax.set_ylabel("全清且证书完成 (%)")
ax.set_ylim(0, 125)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")

# ---- b: cover SQUARE81 vs HEX37 (same revised runner) ----
ax = axes[1]
metrics = ["T/K", "路程", "测向次数"]
s81 = np.array([1313.160522935798, 68.25075026944441, 679.7333333333333])
h37 = np.array([836.9129462514154, 46.196449687541746, 337.1])
pct = (s81 - h37) / s81 * 100.0
x = np.arange(len(metrics))
w = 0.36
s_rel = np.array([100.0, 100.0, 100.0])
h_rel = h37 / s81 * 100.0
b1 = ax.bar(x - w / 2, s_rel, width=w, color=GRAY, edgecolor="white",
            linewidth=1.0, label="SQUARE81", zorder=3)
b2 = ax.bar(x + w / 2, h_rel, width=w, color=BLUE, edgecolor="white",
            linewidth=1.0, label="HEX37", zorder=3)
ax.bar_label(b1, labels=["1313 s", "68.3 km", "680"], padding=2, fontsize=7.5, color=GRAY)
ax.bar_label(b2, labels=[f"837 s\n−{pct[0]:.0f}%", f"46.2 km\n−{pct[1]:.0f}%",
                         f"337\n−{pct[2]:.0f}%"],
             padding=2, fontsize=7.5, color=BLUE)
ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.set_xlabel("配对种子 0–29，同一求解器")
ax.set_ylabel("相对 SQUARE81 的比例 (%)")
ax.set_ylim(0, 138)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
ax.legend(loc="upper right", fontsize=8, frameon=False)
ax.axhline(100, color=GRAY, ls=":", lw=1.0, zorder=1)

# ---- c: route insert ablation on HEX37 ----
ax = axes[2]
# Frozen from experiments/q4_hex37/*.json and paired_results.md
route_labs = ["OLD", "V1", "V2", "V3", "PREFIX_A"]
route_tk = np.array([836.91, 774.06, 735.31, 711.20, 683.09])
alphas = np.linspace(0.35, 1.0, len(route_labs))
blue_rgb = tuple(int(BLUE.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
cols_c = [(*blue_rgb, a) for a in alphas]
x = np.arange(len(route_labs))
bars = ax.bar(x, route_tk, color=cols_c, edgecolor="white", linewidth=1.1,
              width=0.68, zorder=3)
ax.plot(x, route_tk, color=RED, lw=1.6, marker="o", markersize=6,
        markerfacecolor=RED, markeredgecolor="white", markeredgewidth=0.8, zorder=4)
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9, color=BLUE)
ax.set_xticks(x)
ax.set_xticklabels(route_labs, fontsize=9)
ax.set_xlabel("HEX37 寻路（均 30/30 证书）")
ax.set_ylabel("平均 T/K (s)")
ax.set_ylim(600, 920)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "c")

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q4_cover_compare.pdf")
print("wrote figures/fig_q4_cover_compare.pdf")

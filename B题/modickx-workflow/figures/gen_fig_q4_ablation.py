# -*- coding: utf-8 -*-
"""fig_q4_ablation: 问题4 400场配对。最新提交 529.29 s。"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from _utils.plot_utils import setup_style, save_fig
from figures._nature_common import panel_label, ygrid

setup_style(palette="nature")
import _utils.plot_utils as _pu
PALETTE = _pu.PALETTE
BLUE, BLUE2, GREEN, RED, GRAY, TEAL, VIOLET = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5], PALETTE[6]
)

# Frozen from experiments/q4_ablation/primary400/summary.csv
arm_labels = ["TRI25/V4", "复用B", "提前C", "源中心+外圈", "最新529", "连续清源", "每站全扫"]
arm_tk = np.array([
    543.5402015904275,
    539.1630260854663,
    540.8743897669607,
    530.59089134926,
    529.2899300477935,
    637.7950237100861,
    754.1393253400506,
])
arm_colors = [GRAY, BLUE2, TEAL, BLUE, GREEN, RED, RED]

# strata.csv: baseline vs proxy_reuse_early_compact
strata_labels = ["边界外向", "全定向", "混合端点", "混合平滑", "全向"]
base_tk = np.array([
    612.2616406367517,
    568.3628088405055,
    529.9383042598603,
    537.2337093561903,
    510.710236850531,
])
new_tk = np.array([
    636.1682355130505,
    559.4077384989,
    511.0408367754755,
    511.7885471732794,
    482.7915720952166,
])

fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.5))

ax = axes[0]
x = np.arange(len(arm_labels))
bars = ax.bar(x, arm_tk, color=arm_colors, edgecolor="white", linewidth=1.1, width=0.72, zorder=3)
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8, color=GRAY)
ax.set_xticks(x)
ax.set_xticklabels(arm_labels, rotation=28, ha="right")
ax.set_ylabel("平均 $T/K$ (s)")
ax.set_xlabel("400 场配对（离线）")
ax.set_ylim(0, 860)
ax.axhline(arm_tk[4], color=GREEN, ls="--", lw=1.0, alpha=0.7, zorder=1)
ygrid(ax)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
panel_label(ax, "a")
ax.text(
    0.02, 0.96, "最新 $=529.29$ s\n400/400 全清",
    transform=ax.transAxes, ha="left", va="top", fontsize=8, color=GREEN,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

ax = axes[1]
w = 0.38
x = np.arange(len(strata_labels))
b1 = ax.bar(x - w / 2, base_tk, width=w, color=GRAY, edgecolor="white", linewidth=1.0, zorder=3, label="TRI25/V4")
b2 = ax.bar(x + w / 2, new_tk, width=w, color=GREEN, edgecolor="white", linewidth=1.0, zorder=3, label="最新")
ax.set_xticks(x)
ax.set_xticklabels(strata_labels)
ax.set_ylabel("平均 $T/K$ (s)")
ax.set_xlabel("分层（各 50 或 200 场）")
ax.set_ylim(0, 760)
ygrid(ax)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
panel_label(ax, "b")
ax.legend(frameon=False, loc="upper right", fontsize=8)
ax.text(
    0.02, 0.04, "边界外向平均退化 $3.90\%$\n不是各类场景均更优",
    transform=ax.transAxes, ha="left", va="bottom", fontsize=8, color=RED,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q4_ablation.pdf")
print("wrote figures/fig_q4_ablation.pdf")

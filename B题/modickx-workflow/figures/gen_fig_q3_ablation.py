# -*- coding: utf-8 -*-
"""fig_q3_ablation: 问题3 420场配对消融。最新提交 JSO 平均 T/K=254.05 s。"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from _utils.plot_utils import setup_style, save_fig, _lighten
from figures._nature_common import panel_label, ygrid

setup_style(palette="nature")
import _utils.plot_utils as _pu
PALETTE = _pu.PALETTE
BLUE, BLUE2, GREEN, RED, GRAY, TEAL, VIOLET = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5], PALETTE[6]
)

# Frozen from experiments/q3_ablation/evaluation/summary.csv
labels = ["ORIGINAL", "J", "S", "O", "JS", "JO", "SO", "JSO", "ALLSCAN"]
mean_tk = np.array([
    379.60199939018304,
    279.28437681244554,
    310.14098542829277,
    319.1346276941904,
    257.41532096261375,
    269.06851522338496,
    300.5462094638496,
    254.05321048920862,
    360.37327608292594,
])
move_km = np.array([
    19.200755535904435,
    13.950535928133953,
    15.639538364905773,
    16.01245354355254,
    12.497326865054112,
    13.408148453037838,
    15.376665601396217,
    12.592647654176095,
    11.88447050662687,
])
hero = 7
colors = [GRAY, BLUE2, TEAL, VIOLET, BLUE, BLUE, TEAL, GREEN, RED]

fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.4))

ax = axes[0]
x = np.arange(len(labels))
bars = ax.bar(x, mean_tk, color=colors, edgecolor="white", linewidth=1.1, width=0.72, zorder=3)
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8, color=GRAY)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha="right")
ax.set_ylabel("平均 $T/K$ (s)")
ax.set_xlabel("420 场配对（离线）")
ax.set_ylim(0, 440)
ax.axhline(mean_tk[hero], color=GREEN, ls="--", lw=1.0, alpha=0.7, zorder=1)
ygrid(ax)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
panel_label(ax, "a")
ax.text(
    0.98, 0.04, "JSO $=254.05$ s\n420/420 全清",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=GREEN,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

ax = axes[1]
bars = ax.bar(x, move_km, color=colors, edgecolor="white", linewidth=1.1, width=0.72, zorder=3)
ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8, color=GRAY)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha="right")
ax.set_ylabel("平均路程 (km)")
ax.set_xlabel("420 场配对（离线）")
ax.set_ylim(0, 22)
ygrid(ax)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
panel_label(ax, "b")
ax.text(
    0.98, 0.04, "ALLSCAN 路程更短\n但测向升至 353 次",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=RED,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q3_ablation.pdf")
print("wrote figures/fig_q3_ablation.pdf")

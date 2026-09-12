# -*- coding: utf-8 -*-
"""fig_q3_strategy: 问题3 策略对照。非正式、非配对；ABORT 不作正式候选。"""
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

# Frozen from docs/Q3主线-GREEDY_FAST.md (practice, not paired, not official)
# GREEDY 5-run evidence also exists; published comparison uses the 10-run table.
names = ["GREEDY", "GREEDY_FAST", "GREEDY_ABORT"]
full_clear = np.array([10, 10, 1], dtype=float)
n_runs = np.array([10, 10, 10], dtype=float)
clear_rate = full_clear / n_runs * 100.0
mean_tk = np.array([390.0, 341.0, 382.0])
lo = np.array([334.0, 244.0, 295.0])
hi = np.array([455.0, 450.0, 482.0])
safe_mean = np.array([1.20, 0.20, 0.00])
hero = 1  # GREEDY_FAST
colors = [GRAY, BLUE, RED]

fig, axes = plt.subplots(1, 3, figsize=(11.6, 4.4))

# ---- a full-clear rate ----
ax = axes[0]
bars = ax.bar(np.arange(3), clear_rate, color=colors, edgecolor="white",
              linewidth=1.1, width=0.68, zorder=3)
ax.bar_label(
    bars,
    labels=[f"{k}/{n}" for k, n in zip(full_clear.astype(int), n_runs.astype(int))],
    padding=3, fontsize=10, color=GRAY,
)
ax.set_xticks(np.arange(3))
ax.set_xticklabels(["GREEDY", "FAST", "ABORT"], rotation=0)
ax.set_xlabel("策略（非正式演练）")
ax.set_ylabel("全清率 (%)")
ax.set_ylim(0, 118)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")
ax.axhline(100, color=_lighten(GREEN, 0.0), ls=":", lw=1.0, alpha=0.5, zorder=1)

# ---- b T/K mean + range ----
ax = axes[1]
x = np.arange(3)
bars = ax.bar(x, mean_tk, color=colors, edgecolor="white", linewidth=1.1,
              width=0.68, zorder=3)
# reported interval, not a statistical CI (avoid errorbar FancyArrowPatch)
for i, (a, b) in enumerate(zip(lo, hi)):
    ax.vlines(i, a, b, colors=GRAY, lw=1.8, zorder=4)
    ax.hlines([a, b], i - 0.12, i + 0.12, colors=GRAY, lw=1.8, zorder=4)
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=10, color=GRAY)
ax.set_xticks(x)
ax.set_xticklabels(["GREEDY", "FAST", "ABORT"])
ax.set_xlabel("策略（非正式演练）")
ax.set_ylabel("平均 T/K (s)")
ax.set_ylim(180, 540)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
ax.text(
    0.98, 0.04, "须条为报告区间\n非配对置信区间",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=GRAY,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

# ---- c SAFE mean ----
ax = axes[2]
bars = ax.bar(np.arange(3), safe_mean, color=colors, edgecolor="white",
              linewidth=1.1, width=0.68, zorder=3)
ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=10, color=GRAY)
ax.set_xticks(np.arange(3))
ax.set_xticklabels(["GREEDY", "FAST", "ABORT"])
ax.set_xlabel("策略（非正式演练）")
ax.set_ylabel("SAFE 动作均值 (次/局)")
ax.set_ylim(0, 1.55)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "c")
ax.text(
    0.98, 0.04, "ABORT 不作正式候选",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=RED,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q3_strategy.pdf")
print("wrote figures/fig_q3_strategy.pdf")

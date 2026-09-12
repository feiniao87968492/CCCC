# -*- coding: utf-8 -*-
"""fig_q3_practice_tk: GREEDY_FAST 10 局演练 T/K 与全清状态。非正式、非配对。"""
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
BLUE, BLUE2, GREEN, RED, GRAY, TEAL = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5]
)

# Frozen from user_data/handoff/q3-q4-handoff-20260911/evidence/*/summary.json
# strategy=GREEDY_FAST, problem=3, 10 practice runs (not paired, not official)
K = np.array([15, 11, 16, 10, 10, 15, 14, 12, 13, 10], dtype=float)
N = np.array([15, 11, 16, 10, 10, 15, 14, 12, 13, 10], dtype=float)
TK = np.array([
    337.2352628666667, 405.18926454545453, 265.545075875,
    449.50353889999997, 391.71587519999997, 243.74428600000002,
    295.2601529285715, 327.3650116666667, 321.57801238461536,
    372.6251108,
])
n_safe = np.array([0, 0, 0, 1, 1, 0, 0, 0, 0, 0], dtype=int)
run_id = np.arange(1, 11)
mean_tk = float(TK.mean())  # 340.98
min_tk, max_tk = float(TK.min()), float(TK.max())

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5),
                         gridspec_kw={"width_ratios": [1.35, 1.0]})

# ---- a: per-run T/K ----
ax = axes[0]
colors = [TEAL if s == 0 else BLUE2 for s in n_safe]
bars = ax.bar(
    run_id, TK, color=colors, edgecolor="white", linewidth=1.0, width=0.72, zorder=3,
)
ax.axhline(mean_tk, color=RED, ls="--", lw=1.6, zorder=4, label=f"均值 {mean_tk:.0f} s")
ax.axhspan(min_tk, max_tk, color=_lighten(BLUE, 0.85), alpha=0.45, zorder=0)
ax.bar_label(bars, labels=[f"K={k}" for k in K.astype(int)],
             padding=3, fontsize=8, color=GRAY)
ax.set_xlabel("演练局序号（非正式）")
ax.set_ylabel("单位清除时间 T/K (s)")
ax.set_xticks(run_id)
ax.set_ylim(200, 500)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")
# custom legend
from matplotlib.patches import Patch
handles = [
    Patch(facecolor=TEAL, edgecolor="white", label="SAFE = 0"),
    Patch(facecolor=BLUE2, edgecolor="white", label="SAFE = 1"),
    plt.Line2D([0], [0], color=RED, ls="--", lw=1.6, label=f"均值 {mean_tk:.0f} s"),
]
ax.legend(handles=handles, loc="upper right", fontsize=9, frameon=False)
ax.text(
    0.02, 0.04, "10/10 全清且证书完成",
    transform=ax.transAxes, ha="left", va="bottom", fontsize=9, color=TEAL,
    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.92),
)

# ---- b: distribution ----
ax = axes[1]
# strip + mean
jitter = np.zeros_like(TK, dtype=float)
rng = np.random.default_rng(0)
jitter = rng.uniform(-0.08, 0.08, size=len(TK))
ax.scatter(np.ones(len(TK)) + jitter, TK, s=70, c=colors, edgecolors="white",
           linewidths=1.0, zorder=5)
# violin-like density via histogram bars on the right of strip
bins = np.linspace(230, 460, 8)
hist, edges = np.histogram(TK, bins=bins)
centers = 0.5 * (edges[:-1] + edges[1:])
width = np.diff(edges)
maxh = hist.max() if hist.max() > 0 else 1
scale = 0.55 / maxh
ax.barh(centers, hist * scale, height=width * 0.85, left=1.22,
        color=_lighten(BLUE, 0.35), edgecolor="white", linewidth=0.8, zorder=2)
ax.hlines(mean_tk, 0.7, 1.9, colors=RED, linestyles="--", lw=1.5, zorder=4)
ax.hlines([min_tk, max_tk], 0.85, 1.15, colors=GRAY, linestyles="-", lw=1.2, zorder=3)
ax.set_xlim(0.55, 2.05)
ax.set_xticks([1.0, 1.5])
ax.set_xticklabels(["各局 T/K", "频数"])
ax.set_ylabel("单位清除时间 T/K (s)")
ax.set_xlabel("GREEDY_FAST 演练分布")
ax.set_ylim(200, 500)
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
ax.text(
    0.98, 0.04, f"区间 {min_tk:.0f}–{max_tk:.0f} s\nSAFE 均值 0.20",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=GRAY,
    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.92),
)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q3_practice_tk.pdf")
print("wrote figures/fig_q3_practice_tk.pdf")

# -*- coding: utf-8 -*-
"""fig_q4_paired_tk: 种子 0–29 配对离线 T/K，SQUARE81 vs HEX37。非正式几何模型。"""
from __future__ import annotations

import csv
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


def load_csv(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    seed = np.array([int(r["seed"]) for r in rows])
    tk = np.array([float(r["T_over_K"]) for r in rows])
    move = np.array([float(r["move_m"]) for r in rows]) / 1000.0
    nm = np.array([float(r["n_measure"]) for r in rows])
    k = np.array([int(r["K"]) for r in rows])
    n = np.array([int(r["N"]) for r in rows])
    cert = np.array([r["all_certified"].strip().lower() == "true" for r in rows])
    return seed, tk, move, nm, k, n, cert


s81_path = os.path.join("user_data", "experiments", "q4_hex37", "square81.csv")
h37_path = os.path.join("user_data", "experiments", "q4_hex37", "hex37.csv")
s_seed, s_tk, s_move, s_nm, s_k, s_n, s_cert = load_csv(s81_path)
h_seed, h_tk, h_move, h_nm, h_k, h_n, h_cert = load_csv(h37_path)
assert np.array_equal(s_seed, h_seed)

mean_s, mean_h = float(s_tk.mean()), float(h_tk.mean())  # 1313.16, 836.91
drop_pct = (mean_s - mean_h) / mean_s * 100.0
n16_mask = s_n == 16  # same seeds as hex37.json n16_seeds

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5))

# ---- a paired scatter ----
ax = axes[0]
lo = min(s_tk.min(), h_tk.min()) - 40
hi = max(s_tk.max(), h_tk.max()) + 40
ax.plot([lo, hi], [lo, hi], color=GRAY, ls="--", lw=1.2, zorder=1, label="y = x")
ax.fill_between([lo, hi], [lo, hi], [hi, hi], color=_lighten(GREEN, 0.7),
                alpha=0.35, zorder=0)
# non-N=16
m = ~n16_mask
ax.scatter(s_tk[m], h_tk[m], s=48, c=BLUE, edgecolors="white", linewidths=0.8,
           zorder=4, label="种子 0–29")
ax.scatter(s_tk[n16_mask], h_tk[n16_mask], s=70, c=TEAL, edgecolors="white",
           linewidths=0.9, marker="D", zorder=5, label="N = 16 子集")
ax.scatter([mean_s], [mean_h], s=110, c=RED, edgecolors="white", linewidths=1.1,
           marker="*", zorder=6, label="均值")
ax.annotate(
    f"均值下降 {drop_pct:.1f}%",
    xy=(mean_s, mean_h),
    xytext=(mean_s - 80, mean_h - 220),
    fontsize=10, color=RED, ha="center",
    arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.92),
)
ax.set_xlabel("SQUARE81 的 T/K (s)")
ax.set_ylabel("HEX37 的 T/K (s)")
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_aspect("equal")
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")
ax.legend(loc="upper left", fontsize=8, frameon=False)
ax.text(
    0.98, 0.04, "30/30 全清且证书",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=TEAL,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.92),
)

# ---- b per-seed delta ----
ax = axes[1]
delta = s_tk - h_tk
order = np.argsort(s_seed)
x = s_seed[order]
d = delta[order]
n16 = n16_mask[order]
cols = [TEAL if flag else BLUE for flag in n16]
ax.axhline(0, color=GRAY, lw=1.0, zorder=1)
ax.axhline(delta.mean(), color=RED, ls="--", lw=1.5, zorder=2,
           label=f"均值 Δ = {delta.mean():.0f} s")
ax.bar(x, d, color=cols, edgecolor="white", linewidth=0.6, width=0.82, zorder=3)
ax.set_xlabel("配对种子")
ax.set_ylabel("T/K 下降量 (s)，SQUARE81 − HEX37")
ax.set_xticks([0, 5, 10, 15, 20, 25, 29])
ygrid(ax)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
from matplotlib.patches import Patch
handles = [
    Patch(facecolor=BLUE, edgecolor="white", label="普通种子"),
    Patch(facecolor=TEAL, edgecolor="white", label="N = 16"),
    plt.Line2D([0], [0], color=RED, ls="--", lw=1.5, label=f"均值 Δ = {delta.mean():.0f} s"),
]
ax.legend(handles=handles, loc="upper right", fontsize=8, frameon=False)
ax.set_ylim(0, max(d) * 1.18)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q4_paired_tk.pdf")
print("wrote figures/fig_q4_paired_tk.pdf")

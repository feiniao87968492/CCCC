# -*- coding: utf-8 -*-
"""fig_q4_hex37: HEX37 三角格点、Hamilton 骨架与 1800 m 源圆。"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, RegularPolygon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from _utils.plot_utils import setup_style, save_fig, PALETTE, _lighten
from figures._nature_common import panel_label

setup_style(palette="nature")
import _utils.plot_utils as _pu
PALETTE = _pu.PALETTE
BLUE, BLUE2, GREEN, RED, GRAY, TEAL, VIOLET = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5], PALETTE[6]
)

HEX_STEP = 800.0
HEX_E1 = np.array([HEX_STEP, 0.0])
HEX_E2 = np.array([HEX_STEP / 2.0, HEX_STEP * np.sqrt(3.0) / 2.0])
HEX37_ROUTE_QR = (
    (0, 0), (-1, 0), (-1, 1), (-2, 1), (-3, 1), (-3, 0), (-2, 0),
    (-2, -1), (-1, -2), (-1, -1), (0, -1), (0, -2), (0, -3), (1, -3),
    (1, -2), (2, -3), (3, -3), (2, -2), (1, -1), (1, 0), (0, 1),
    (-1, 2), (-2, 2), (-3, 2), (-3, 3), (-2, 3), (-1, 3), (0, 3),
    (0, 2), (1, 2), (1, 1), (2, 1), (3, 0), (2, 0), (2, -1), (3, -2),
    (3, -1),
)
PREFIX_A = [0, 2, 1, 10, 18, 19, 20, 21, 25, 26, 27, 28, 29, 30, 31, 32, 33, 36, 34, 35, 16, 17, 15, 14, 13, 12, 11, 8, 9, 7, 5, 6, 4, 3, 23, 24, 22]


def axial_to_xy(q, r):
    return q * HEX_E1 + r * HEX_E2


pts = np.array([axial_to_xy(q, r) for q, r in HEX37_ROUTE_QR])
delta = HEX_STEP / np.sqrt(3.0)  # covering radius of infinite lattice
omega_r = 1800.0
approach_r = 2300.0  # |y|=g+500d bound used in the existence proof

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5))

# ---- a: lattice + Omega ----
ax = axes[0]
ax.add_patch(Circle((0, 0), omega_r, facecolor=_lighten(BLUE, 0.88),
                    edgecolor=BLUE2, lw=1.6, zorder=1, label="源所在圆 Ω，半径 1800 m"))
ax.add_patch(Circle((0, 0), approach_r, facecolor="none", edgecolor=GRAY,
                    lw=1.1, ls="--", zorder=2, label="接近点外包 |y|≤2300 m"))
# Voronoi hex around origin as scale cue
hex0 = RegularPolygon(
    (0, 0), numVertices=6, radius=delta, orientation=np.pi / 6,
    facecolor=_lighten(TEAL, 0.55), edgecolor=TEAL, lw=1.2, alpha=0.55, zorder=2,
)
ax.add_patch(hex0)
ax.scatter(pts[:, 0], pts[:, 1], s=28, c=BLUE, edgecolors="white",
           linewidths=0.7, zorder=5)
ax.scatter([0], [0], s=70, c=RED, edgecolors="white", linewidths=1.1,
           zorder=6, marker="s")
ax.annotate(
    "原点",
    xy=(0, 0), xytext=(-900, -700),
    fontsize=10, color=RED, ha="center",
    arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.92),
)
ax.annotate(
    "覆盖半径 δ=800/√3",
    xy=(delta * np.cos(np.pi / 6), delta * np.sin(np.pi / 6)),
    xytext=(1200, 900),
    fontsize=9, color=TEAL, ha="left",
    arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.92),
)
ax.set_xlabel("东向坐标 (m)")
ax.set_ylabel("北向坐标 (m)")
ax.set_aspect("equal")
ax.set_xlim(-2800, 2800)
ax.set_ylim(-2800, 2800)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")
ax.legend(loc="lower right", fontsize=8, frameon=False)
ax.text(
    0.02, 0.04, "37 点 · 边长 800 m",
    transform=ax.transAxes, ha="left", va="bottom", fontsize=9, color=GRAY,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

# ---- b: PREFIX_A Hamilton path ----
ax = axes[1]
ax.add_patch(Circle((0, 0), omega_r, facecolor=_lighten(BLUE, 0.90),
                    edgecolor=BLUE2, lw=1.2, zorder=1))
order = PREFIX_A
path = pts[order]
ax.plot(path[:, 0], path[:, 1], color=_lighten(BLUE, 0.15), lw=2.4,
        zorder=3, solid_capstyle="round", label="PREFIX_A，36×800 m")
# arrows on a few segments
for i in (0, 5, 12, 20, 28):
    p0, p1 = path[i], path[i + 1]
    ax.annotate(
        "",
        xy=p1, xytext=p0,
        arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.4,
                        mutation_scale=10),
        zorder=4,
    )
ax.scatter(path[:, 0], path[:, 1], s=26, c=BLUE, edgecolors="white",
           linewidths=0.6, zorder=5)
ax.scatter([path[0, 0]], [path[0, 1]], s=80, c=RED, edgecolors="white",
           linewidths=1.1, zorder=6, marker="s")
# first 6 visit numbers only (avoid label pile-up)
for k in range(6):
    ax.annotate(
        str(k),
        xy=path[k],
        xytext=(path[k, 0] + 90, path[k, 1] + 140),
        fontsize=8, color=BLUE,
        arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.6),
        bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.9),
        zorder=7,
    )
ax.set_xlabel("东向坐标 (m)")
ax.set_ylabel("北向坐标 (m)")
ax.set_aspect("equal")
ax.set_xlim(-2800, 2800)
ax.set_ylim(-2800, 2800)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
ax.legend(loc="lower right", fontsize=8, frameon=False)
ax.text(
    0.02, 0.04, "骨架行程 28.8 km",
    transform=ax.transAxes, ha="left", va="bottom", fontsize=9, color=GRAY,
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)

fig.tight_layout(pad=1.0)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q4_hex37.pdf")
print("wrote figures/fig_q4_hex37.pdf")

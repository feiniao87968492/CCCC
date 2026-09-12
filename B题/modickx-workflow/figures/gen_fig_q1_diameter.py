# -*- coding: utf-8 -*-
"""fig_q1_diameter: 等边三角形直径圆不能覆盖 vs Jung 最小覆盖圆。"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from _utils.plot_utils import setup_style, save_fig, PALETTE, _lighten
from figures._nature_common import panel_label

setup_style(palette="nature")
import _utils.plot_utils as _pu
PALETTE = _pu.PALETTE
BLUE, BLUE2, GREEN, RED, GRAY, TEAL = (
    PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5]
)

# Frozen from data_preparation/output/q1_q2_demo.json
verts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 0.8660254038]])
diameter = 1.0
mec_r = 0.5773502691948129
# diameter-circle center = midpoint of a diameter edge (here the base)
c_diam = np.array([0.5, 0.0])
# circumcenter of equilateral triangle = centroid
c_mec = verts.mean(axis=0)


def _draw_triangle(ax, v, color):
    tri = plt.Polygon(v, closed=True, facecolor=_lighten(color, 0.75),
                      edgecolor=color, linewidth=2.2, zorder=3, alpha=0.95)
    ax.add_patch(tri)
    ax.scatter(v[:, 0], v[:, 1], s=38, c=color, edgecolors="white",
               linewidths=1.1, zorder=6)
    return tri


def _annotate_vertex(ax, xy, text, dx, dy, color):
    ax.annotate(
        text,
        xy=xy,
        xytext=(xy[0] + dx, xy[1] + dy),
        fontsize=10,
        color=color,
        ha="center",
        va="center",
        arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.9),
        zorder=8,
    )


fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.5))

# ---- a: diameter circle fails ----
ax = axes[0]
circ = Circle(c_diam, diameter / 2.0, facecolor=_lighten(RED, 0.82),
              edgecolor=RED, linewidth=2.0, linestyle="--", zorder=2)
ax.add_patch(circ)
_draw_triangle(ax, verts, BLUE)
# uncovered vertex
ax.scatter([verts[2, 0]], [verts[2, 1]], s=90, c=RED, edgecolors="white",
           linewidths=1.2, zorder=7, marker="o")
_annotate_vertex(ax, verts[2], "顶点 C\n未被覆盖", 0.0, 0.28, RED)
ax.plot([verts[0, 0], verts[1, 0]], [verts[0, 1], verts[1, 1]],
        color=RED, lw=2.4, zorder=5, solid_capstyle="round")
ax.annotate(
    "直径边 AB",
    xy=(0.5, 0.0),
    xytext=(0.5, -0.28),
    fontsize=10,
    ha="center",
    color=RED,
    arrowprops=dict(arrowstyle="-", color=RED, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)
ax.set_xlabel("水平坐标 (边长单位)")
ax.set_ylabel("竖直坐标 (边长单位)")
ax.set_aspect("equal")
ax.set_xlim(-0.25, 1.25)
ax.set_ylim(-0.42, 1.28)
ax.set_xticks([0.0, 0.5, 1.0])
ax.set_yticks([0.0, 0.5, 0.866])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "a")
ax.text(
    0.98, 0.04, "直径圆半径 = 0.500",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=10, color=RED,
    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.9),
)

# ---- b: Jung / circumcircle covers ----
ax = axes[1]
circ2 = Circle(c_mec, mec_r, facecolor=_lighten(GREEN, 0.55),
               edgecolor=GREEN, linewidth=2.0, zorder=2)
ax.add_patch(circ2)
_draw_triangle(ax, verts, BLUE)
ax.scatter([c_mec[0]], [c_mec[1]], s=46, c=TEAL, edgecolors="white",
           linewidths=1.1, zorder=7, marker="D")
ax.annotate(
    "最小覆盖圆心",
    xy=c_mec,
    xytext=(c_mec[0] + 0.42, c_mec[1] - 0.22),
    fontsize=10,
    color=TEAL,
    ha="left",
    arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8),
    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
)
ax.set_xlabel("水平坐标 (边长单位)")
ax.set_ylabel("竖直坐标 (边长单位)")
ax.set_aspect("equal")
ax.set_xlim(-0.25, 1.25)
ax.set_ylim(-0.42, 1.28)
ax.set_xticks([0.0, 0.5, 1.0])
ax.set_yticks([0.0, 0.5, 0.866])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
panel_label(ax, "b")
ax.text(
    0.98, 0.04, "Jung 半径 = 0.577",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=10, color=TEAL,
    bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.9),
)

fig.tight_layout(pad=1.1)
os.makedirs("figures", exist_ok=True)
save_fig(fig, "figures/fig_q1_diameter.pdf")
print("wrote figures/fig_q1_diameter.pdf")

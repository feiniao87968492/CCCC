# -*- coding: utf-8 -*-
"""Shared Nature-style helpers for CUMCM B figures."""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from _utils.plot_utils import setup_style, save_fig, PALETTE, _lighten  # noqa: E402


def init_style():
    setup_style(palette="nature")
    from _utils.plot_utils import PALETTE as P
    return {
        "blue": P[0],
        "blue2": P[1],
        "green": P[2],
        "red": P[3],
        "gray": P[4],
        "teal": P[5],
        "violet": P[6],
        "gold": P[7] if len(P) > 7 else P[0],
        "lighten": _lighten,
        "save": save_fig,
        "palette": P,
    }


def panel_label(ax, lab, x=0.02, y=0.96, fontsize=14):
    ax.text(
        x,
        y,
        lab,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight="bold",
        va="top",
        ha="left",
        zorder=20,
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85),
    )


def hide_top_right(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def ygrid(ax):
    ax.grid(axis="y", alpha=0.15, linestyle="--", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

# -*- coding: utf-8 -*-
"""Render draw.io mxGraph XML to cropped PDF/PNG (draw.io CLI unavailable)."""
from __future__ import annotations

import html as htmlmod
import os
import re
import sys
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.path import Path as MplPath

PX = 96.0  # draw.io page units ~ CSS px


def _find_cjk_font():
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyhbd.ttc",
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                font_manager.fontManager.addfont(p)
            except Exception:
                pass
            return font_manager.FontProperties(fname=p)
    return font_manager.FontProperties(family="sans-serif")


CJK = _find_cjk_font()


def parse_style(style: str) -> dict:
    out = {}
    if not style:
        return out
    for part in style.split(";"):
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
        else:
            out[part.strip()] = "1"
    return out


def hex_to_rgb(h, default="#333333"):
    if not h or h.lower() in ("none", "default"):
        h = default
    h = h.strip()
    if h.startswith("#") and len(h) == 7:
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
    return (0.2, 0.2, 0.2)


def strip_label(value: str) -> str:
    if not value:
        return ""
    s = htmlmod.unescape(value)
    s = s.replace("✓", "").replace("★", "")
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?b>", "", s, flags=re.I)
    s = re.sub(r"<font[^>]*>", "", s, flags=re.I)
    s = re.sub(r"</font>", "", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    lines = [ln.strip() for ln in s.split("\n")]
    return "\n".join([ln for ln in lines if ln])


class Cell:
    def __init__(self, el):
        self.id = el.get("id")
        self.value = el.get("value") or ""
        self.style = parse_style(el.get("style") or "")
        self.vertex = el.get("vertex") == "1"
        self.edge = el.get("edge") == "1"
        self.source = el.get("source")
        self.target = el.get("target")
        self.parent = el.get("parent")
        self.x = self.y = self.w = self.h = 0.0
        self.points = []
        geom = None
        for ch in list(el):
            if ch.tag.endswith("mxGeometry"):
                geom = ch
                break
        if geom is not None:
            self.x = float(geom.get("x") or 0)
            self.y = float(geom.get("y") or 0)
            self.w = float(geom.get("width") or 0)
            self.h = float(geom.get("height") or 0)
            for arr in list(geom):
                if arr.tag.endswith("Array") and arr.get("as") == "points":
                    for pt in list(arr):
                        if pt.tag.endswith("mxPoint"):
                            self.points.append(
                                (float(pt.get("x") or 0), float(pt.get("y") or 0))
                            )

    def port(self, px, py):
        return self.x + px * self.w, self.y + py * self.h

    def is_text(self):
        return "text" in self.style or (
            self.style.get("strokeColor") == "none"
            and self.style.get("fillColor") == "none"
            and self.vertex
        )

    def is_group(self):
        fill = self.style.get("fillColor")
        return self.vertex and fill in (None, "none", "default") and self.style.get("dashed") == "1"


def load_cells(path):
    tree = ET.parse(path)
    root = tree.getroot()
    model = None
    for el in root.iter():
        if el.tag.endswith("mxGraphModel"):
            model = el
            break
    if model is None:
        raise SystemExit(f"no mxGraphModel in {path}")
    page_w = float(model.get("pageWidth") or 1100)
    page_h = float(model.get("pageHeight") or 800)
    cells = []
    for el in model.iter():
        if el.tag.endswith("mxCell"):
            c = Cell(el)
            if c.id in ("0", "1") or c.id is None:
                continue
            cells.append(c)
    by_id = {c.id: c for c in cells}
    return cells, by_id, page_w, page_h


def hexagon_xy(x, y, w, h, size=20.0):
    s = min(size, w * 0.35, h * 0.5)
    return [
        (x + s, y),
        (x + w - s, y),
        (x + w, y + h / 2),
        (x + w - s, y + h),
        (x + s, y + h),
        (x, y + h / 2),
    ]


def diamond_xy(x, y, w, h):
    return [
        (x + w / 2, y),
        (x + w, y + h / 2),
        (x + w / 2, y + h),
        (x, y + h / 2),
    ]


def draw_vertex(ax, c: Cell):
    st = c.style
    fill = st.get("fillColor", "#FFFFFF")
    stroke = st.get("strokeColor", "#666666")
    sw = float(st.get("strokeWidth") or 1.5)
    dashed = st.get("dashed") == "1"
    ls = (0, (4, 3)) if dashed else "-"
    shape = st.get("shape", "")
    fc = None if fill in ("none", "default") else hex_to_rgb(fill, "#FFFFFF")
    sc = None if stroke in ("none",) else hex_to_rgb(stroke, "#555555")
    lw = max(sw * 0.75, 0.6)
    z = 1 if fc is None else 2

    if c.is_text():
        return
    if shape == "hexagon":
        size = float(st.get("size") or 20)
        poly = mpatches.Polygon(
            hexagon_xy(c.x, c.y, c.w, c.h, size),
            closed=True,
            facecolor=fc or "none",
            edgecolor=sc or "none",
            linewidth=lw,
            linestyle=ls,
            joinstyle="miter",
            zorder=z,
        )
        ax.add_patch(poly)
    elif "rhombus" in st or shape == "rhombus" or shape == "diamond":
        poly = mpatches.Polygon(
            diamond_xy(c.x, c.y, c.w, c.h),
            closed=True,
            facecolor=fc or "none",
            edgecolor=sc or "none",
            linewidth=lw,
            linestyle=ls,
            zorder=z,
        )
        ax.add_patch(poly)
    else:
        rad = 0.18 if st.get("rounded") == "1" else 0.0
        if rad > 0:
            pad = min(c.w, c.h) * 0.12
            box = mpatches.FancyBboxPatch(
                (c.x, c.y),
                c.w,
                c.h,
                boxstyle=f"round,pad=0,rounding_size={min(8, pad)}",
                facecolor=fc if fc is not None else (1, 1, 1, 0),
                edgecolor=sc or (0, 0, 0, 0),
                linewidth=lw,
                linestyle=ls,
                zorder=z,
            )
            ax.add_patch(box)
        else:
            rect = mpatches.Rectangle(
                (c.x, c.y),
                c.w,
                c.h,
                facecolor=fc if fc is not None else (1, 1, 1, 0),
                edgecolor=sc or (0, 0, 0, 0),
                linewidth=lw,
                linestyle=ls,
                zorder=z,
            )
            ax.add_patch(rect)


def side_point(cell: Cell, x, y):
    left, right, top, bot = cell.x, cell.x + cell.w, cell.y, cell.y + cell.h
    dists = {
        "w": abs(x - left),
        "e": abs(x - right),
        "n": abs(y - top),
        "s": abs(y - bot),
    }
    side = min(dists, key=dists.get)
    if side == "w":
        return (left, min(max(y, top + 2), bot - 2)), "w"
    if side == "e":
        return (right, min(max(y, top + 2), bot - 2)), "e"
    if side == "n":
        return (min(max(x, left + 2), right - 2), top), "n"
    return (min(max(x, left + 2), right - 2), bot), "s"


def port_from_frac(cell: Cell, px, py):
    return cell.port(px, py), (
        "w" if px <= 0.05 else "e" if px >= 0.95 else "n" if py <= 0.05 else "s" if py >= 0.95 else "s"
    )


def manhattan(p0, p1, s0, s1):
    x0, y0 = p0
    x1, y1 = p1
    if abs(x0 - x1) < 1.5 or abs(y0 - y1) < 1.5:
        return [p0, p1]
    if s0 in "ew" and s1 in "ew":
        mx = (x0 + x1) / 2.0
        return [p0, (mx, y0), (mx, y1), p1]
    if s0 in "ns" and s1 in "ns":
        my = (y0 + y1) / 2.0
        return [p0, (x0, my), (x1, my), p1]
    if s0 in "ew":
        return [p0, (x1, y0), p1]
    return [p0, (x0, y1), p1]


def draw_label(ax, c: Cell):
    text = strip_label(c.value)
    if not text:
        return
    st = c.style
    fs_px = float(st.get("fontSize") or 12)
    fs = max(fs_px * 72.0 / PX, 6.5)
    color = hex_to_rgb(st.get("fontColor") or "#333333", "#333333")
    weight = "bold" if st.get("fontStyle") in ("1", "3", "5") else "normal"
    lines = text.split("\n")
    cx = c.x + c.w / 2
    top_align = c.is_group() or st.get("verticalAlign") == "top"
    if top_align:
        cy0 = c.y + 11
        va = "center"
        n = len(lines)
        step = max(fs * 1.25 * PX / 72.0, 13)
        for i, ln in enumerate(lines):
            ax.text(
                cx,
                cy0 + i * step,
                ln,
                ha="center",
                va=va,
                fontsize=fs,
                color=color,
                fontproperties=CJK,
                fontweight=weight,
                zorder=6,
            )
        return
    cy = c.y + c.h / 2
    if len(lines) == 1:
        ax.text(
            cx,
            cy,
            lines[0],
            ha="center",
            va="center",
            fontsize=fs,
            color=color,
            fontproperties=CJK,
            fontweight=weight,
            zorder=6,
            wrap=False,
        )
        return
    n = len(lines)
    step = min(c.h / (n + 0.35), fs * 1.55 * PX / 72.0)
    y0 = cy - (n - 1) * step / 2
    for i, ln in enumerate(lines):
        this_fs = fs if i == 0 else max(fs * 0.82, 6.2)
        this_w = "bold" if i == 0 else "normal"
        this_c = color if i == 0 else hex_to_rgb("#555555")
        ax.text(
            cx,
            y0 + i * step,
            ln,
            ha="center",
            va="center",
            fontsize=this_fs,
            color=this_c,
            fontproperties=CJK,
            fontweight=this_w,
            zorder=6,
        )


def arrowhead(ax, p0, p1, color, size=8.0, z=4):
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    L = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    s = size
    pts = [
        (x1, y1),
        (x1 - ux * s + px * s * 0.42, y1 - uy * s + py * s * 0.42),
        (x1 - ux * s - px * s * 0.42, y1 - uy * s - py * s * 0.42),
    ]
    ax.add_patch(
        mpatches.Polygon(pts, closed=True, facecolor=color, edgecolor=color, zorder=z)
    )


def draw_edge(ax, e: Cell, by_id: dict):
    src = by_id.get(e.source)
    tgt = by_id.get(e.target)
    if src is None or tgt is None:
        return
    st = e.style
    if "exitX" in st and "exitY" in st:
        p0, s0 = port_from_frac(src, float(st["exitX"]), float(st["exitY"]))
    elif e.points:
        p0, s0 = side_point(src, e.points[0][0], e.points[0][1])
    else:
        p0, s0 = side_point(src, tgt.x + tgt.w / 2, tgt.y + tgt.h / 2)
    if "entryX" in st and "entryY" in st:
        p1, s1 = port_from_frac(tgt, float(st["entryX"]), float(st["entryY"]))
    elif e.points:
        p1, s1 = side_point(tgt, e.points[-1][0], e.points[-1][1])
    else:
        p1, s1 = side_point(tgt, src.x + src.w / 2, src.y + src.h / 2)
    if e.points:
        pts = [p0] + e.points + [p1]
    else:
        pts = manhattan(p0, p1, s0, s1)
    color = hex_to_rgb(st.get("strokeColor") or "#888888", "#888888")
    sw = float(st.get("strokeWidth") or 1.5)
    lw = max(sw * 0.85, 0.8)
    dashed = st.get("dashed") == "1"
    ls = (0, (5, 3)) if dashed else "-"
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle="round", linestyle=ls, zorder=2)
    if st.get("endArrow") not in ("none",):
        arrowhead(ax, pts[-2], pts[-1], color, size=max(6.5, sw * 2.8), z=4)


def render(src, pdf_path, png_path=None):
    cells, by_id, page_w, page_h = load_cells(src)
    verts = [c for c in cells if c.vertex]
    edges = [c for c in cells if c.edge]
    if not verts:
        raise SystemExit(f"no vertices in {src}")
    xs0 = [c.x for c in verts]
    ys0 = [c.y for c in verts]
    xs1 = [c.x + c.w for c in verts]
    ys1 = [c.y + c.h for c in verts]
    for e in edges:
        for px, py in e.points:
            xs0.append(px)
            xs1.append(px)
            ys0.append(py)
            ys1.append(py)
    pad = 28.0
    xmin, xmax = min(xs0) - pad, max(xs1) + pad
    ymin, ymax = min(ys0) - pad, max(ys1) + pad
    w_px = max(xmax - xmin, 40)
    h_px = max(ymax - ymin, 40)
    fig_w = w_px / PX
    fig_h = h_px / PX
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=PX)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymax, ymin)  # draw.io y-down
    ax.set_aspect("equal")
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    groups = [c for c in verts if c.is_group()]
    solids = [c for c in verts if not c.is_group() and not c.is_text()]
    texts = [c for c in verts if c.is_text()]
    for c in groups:
        draw_vertex(ax, c)
    for e in edges:
        draw_edge(ax, e, by_id)
    for c in solids:
        draw_vertex(ax, c)
    for c in groups + solids + texts:
        draw_label(ax, c)
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight", pad_inches=0.04, facecolor="white")
    if png_path:
        fig.savefig(png_path, format="png", dpi=160, bbox_inches="tight", pad_inches=0.04, facecolor="white")
    plt.close(fig)
    print(f"wrote {pdf_path} ({os.path.getsize(pdf_path)} bytes)")


def main():
    files = sys.argv[1:]
    if not files:
        files = [
            "figures/fig_roadmap.drawio",
            "figures/fig_flow_q1.drawio",
            "figures/fig_flow_q2.drawio",
            "figures/fig_flow_q3.drawio",
            "figures/fig_flow_q4.drawio",
        ]
    for src in files:
        bn = os.path.splitext(os.path.basename(src))[0]
        pdf = os.path.join("figures", bn + ".pdf")
        png = os.path.join("figures", bn + ".png")
        render(src, pdf, png)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Regenerate four flow DrawIO files only. Does not touch fig_roadmap.drawio."""
from pathlib import Path

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

EDGE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=1.5;"
    "endArrow=block;endFill=1;jumpStyle=arc;jumpSize=6;"
)

INP = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F4FA;strokeColor=#7B9FC0;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
PROC = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7AAA7A;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
DIA = "rhombus;whiteSpace=wrap;html=1;fillColor=#F5F0E8;strokeColor=#B0A080;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
CHK = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0ECF5;strokeColor=#9A8AB0;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
OUTN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF5ED;strokeColor=#82b366;strokeWidth=2;fontSize=11;fontStyle=1;fontColor=#333333;"
BAD = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F5EDED;strokeColor=#B08080;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
LAB = "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;"

E_DN = EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
E_RT = EDGE + "strokeColor=#999999;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
E_DL = EDGE + "strokeColor=#999999;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
E_DR = EDGE + "strokeColor=#999999;exitX=0.75;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
E_ML = EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.25;entryY=0;entryDx=0;entryDy=0;"
E_MR = EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.75;entryY=0;entryDx=0;entryDy=0;"
LOOP = EDGE + "strokeColor=#B08080;dashed=1;"


def cell(cid, value, style, x, y, w, h, parent="1"):
    return (
        f'<mxCell id="{cid}" value="{value}" style="{style}" '
        f'vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
        f"</mxCell>"
    )


def edge(eid, source, target, style, parent="1"):
    return (
        f'<mxCell id="{eid}" edge="1" parent="{parent}" source="{source}" '
        f'target="{target}" style="{style}">'
        f'<mxGeometry relative="1" as="geometry"/>'
        f"</mxCell>"
    )


def edge_wp(eid, source, target, style, points, parent="1"):
    pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points)
    return (
        f'<mxCell id="{eid}" edge="1" parent="{parent}" source="{source}" '
        f'target="{target}" style="{style}">'
        f'<mxGeometry relative="1" as="geometry">'
        f'<Array as="points">{pts}</Array>'
        f"</mxGeometry></mxCell>"
    )


def mxfile(name, did, width, height, body):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" agent="Mozilla/5.0" version="21.2.9" type="device">'
        f'<diagram id="{did}" name="{name}">'
        f'<mxGraphModel dx="1200" dy="900" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" '
        f'pageWidth="{width}" pageHeight="{height}" background="none" math="0" shadow="0">'
        f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}'
        "</root></mxGraphModel></diagram></mxfile>\n"
    )


def b(title, sub):
    return (
        f"&lt;b&gt;{title}&lt;/b&gt;&lt;br&gt;"
        f"&lt;font style=&quot;font-size:9px;color:#555555;&quot;&gt;{sub}&lt;/font&gt;"
    )


# ---------------------------------------------------------------------------
# fig_flow_q1
# ---------------------------------------------------------------------------
q1 = []
q1.append(cell("q1_in", b("输入检测点与示向度", "前向闭楔形 / 误差闭区间 ±1°"), INP, 370, 20, 260, 46))
q1.append(edge("q1_e1", "q1_in", "q1_w", E_DL))
q1.append(edge("q1_e2", "q1_in", "q1_d", E_DR))
q1.append(cell("q1_w", b("构造前向闭楔形", "示向度两侧各 1° / 射线半平面"), PROC, 80, 88, 250, 50))
q1.append(cell("q1_d", b("枚举退化情形", "空集 / 点 / 线段 / 无界条带"), PROC, 670, 88, 250, 50))
q1.append(edge("q1_e3", "q1_w", "q1_r", E_ML))
q1.append(edge("q1_e4", "q1_d", "q1_r", E_MR))
q1.append(cell("q1_r", b("求楔形交集 R", "多点交为多边形；两点为四边形"), INP, 350, 163, 300, 48))
q1.append(edge("q1_e5", "q1_r", "q1_dia", E_DN))
q1.append(cell("q1_dia", "&lt;b&gt;R 是否有界&lt;br&gt;且非空?&lt;/b&gt;", DIA, 410, 228, 180, 78))
q1.append(cell("q1_yes", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 500, 308, 28, 18))
q1.append(cell("q1_no", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 600, 252, 28, 18))
q1.append(edge("q1_e6", "q1_dia", "q1_diam", E_DN))
q1.append(edge("q1_e7", "q1_dia", "q1_deg", E_RT))
q1.append(cell("q1_deg", b("退化输出", "报告空 / 无界；不强制多边形"), BAD, 680, 241, 230, 52))
q1.append(edge_wp(
    "q1_loop",
    "q1_deg",
    "q1_w",
    LOOP + "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(980, 267), (980, 6), (18, 6), (18, 113)],
))
q1.append(cell("q1_diam", b("计算几何直径 diam(R)", "最大点对距离，非覆盖圆直径"), CHK, 350, 333, 300, 48))
q1.append(edge("q1_e8", "q1_diam", "q1_cov", E_DL))
q1.append(edge("q1_e9", "q1_diam", "q1_jung", E_DR))
q1.append(cell("q1_cov", b("直径圆覆盖性判定", "一般不能覆盖 R"), PROC, 80, 408, 250, 50))
q1.append(cell("q1_jung", b("Jung 最小覆盖圆对照", "等边三角形 r = 边长/√3"), PROC, 670, 408, 250, 50))
q1.append(edge("q1_e10", "q1_cov", "q1_out", E_ML))
q1.append(edge("q1_e11", "q1_jung", "q1_out", E_MR))
q1.append(cell("q1_out", b("输出交会算法与覆盖性结论", "后续清除须核验豪斯多夫半径 ≤20 m"), OUTN, 320, 478, 360, 46))

(OUT / "fig_flow_q1.drawio").write_text(
    mxfile("问题一求解流程", "flow_q1", 1020, 560, "".join(q1)),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# fig_flow_q2
# ---------------------------------------------------------------------------
q2 = []
q2.append(cell("q2_in", b("输入第一检测点与示向度", "单全向源；真位置与 r_i 未知"), INP, 370, 20, 260, 46))
q2.append(edge("q2_e1", "q2_in", "q2_sec", E_DL))
q2.append(edge("q2_e2", "q2_in", "q2_om", E_DR))
q2.append(cell("q2_sec", b("前向 180° 可行扇", "仅用已观测楔形，不用未知真值"), PROC, 80, 88, 250, 50))
q2.append(cell("q2_om", b("叠加圆域与半径区间", "Ω 半径 1800 m；r_i∈[1000,1500]"), PROC, 670, 88, 250, 50))
q2.append(edge("q2_e3", "q2_sec", "q2_cand", E_ML))
q2.append(edge("q2_e4", "q2_om", "q2_cand", E_MR))
q2.append(cell("q2_cand", b("构造第二点候选集", "保证可能收到信号；禁止用未知 G 排点"), INP, 330, 163, 340, 48))
q2.append(edge("q2_e5", "q2_cand", "q2_j", E_DN))
q2.append(cell("q2_j", b("计算候选指标 J*", "最坏点误差 / 交会直径充分条件"), CHK, 350, 228, 300, 48))
q2.append(edge("q2_e6", "q2_j", "q2_dia", E_DN))
q2.append(cell("q2_dia", "&lt;b&gt;diam(R) 能否进入&lt;br&gt;可清除尺度?&lt;/b&gt;", DIA, 400, 293, 200, 82))
q2.append(cell("q2_yes", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 376, 28, 18))
q2.append(cell("q2_no", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 318, 28, 18))
q2.append(edge("q2_e7", "q2_dia", "q2_out", E_DN))
q2.append(edge("q2_e8", "q2_dia", "q2_adj", E_RT))
q2.append(cell("q2_adj", b("调整第二点几何", "拉开基线 / 避开共线"), BAD, 690, 308, 220, 52))
q2.append(edge_wp(
    "q2_loop",
    "q2_adj",
    "q2_cand",
    LOOP + "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
    [(980, 334), (980, 187)],
))
q2.append(cell("q2_out", b("输出第二点策略与候选区", "供问题3发现源后直接调用"), OUTN, 330, 408, 340, 46))

(OUT / "fig_flow_q2.drawio").write_text(
    mxfile("问题二求解流程", "flow_q2", 1020, 490, "".join(q2)),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# fig_flow_q3
# ---------------------------------------------------------------------------
q3 = []
q3.append(cell("q3_in", b("输入初值与全向场景", "起点 (0,0)，频道 c=1；N∈[10,16] 未知"), INP, 350, 20, 300, 46))
q3.append(edge("q3_e1", "q3_in", "q3_sc", E_DL))
q3.append(edge("q3_e2", "q3_in", "q3_mod", E_DR))
q3.append(cell("q3_sc", b("同站批量扫频", "已清频道不再测向"), PROC, 70, 86, 240, 50))
q3.append(cell("q3_mod", b("复用交会与第二点模块", "楔形交集 + 候选点策略"), PROC, 690, 86, 240, 50))
q3.append(edge("q3_e3", "q3_sc", "q3_obs", E_ML))
q3.append(edge("q3_e4", "q3_mod", "q3_obs", E_MR))
q3.append(cell("q3_obs", b("解析观测三值", "direction / near / no_signal"), INP, 350, 160, 300, 46))
q3.append(edge("q3_e5", "q3_obs", "q3_d1", E_DN))
q3.append(cell("q3_d1", "&lt;b&gt;是否收到方向&lt;br&gt;或进入近场?&lt;/b&gt;", DIA, 400, 224, 200, 80))
q3.append(cell("q3_y1", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 306, 28, 18))
q3.append(cell("q3_n1", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 248, 28, 18))
q3.append(edge("q3_e6", "q3_d1", "q3_d2", E_DN))
q3.append(edge("q3_e7", "q3_d1", "q3_ns", E_RT))
q3.append(cell("q3_ns", b("无信号距离排除", "确信有源时 d&gt;r_i≥1000 m"), BAD, 690, 238, 230, 52))
q3.append(edge("q3_e8", "q3_d2", "q3_cl", E_DN))
q3.append(cell("q3_d2", "&lt;b&gt;包围半径&lt;br&gt;是否 ≤20 m?&lt;/b&gt;", DIA, 400, 328, 200, 80))
q3.append(cell("q3_y2", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 410, 28, 18))
q3.append(cell("q3_n2", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 352, 28, 18))
q3.append(edge("q3_e9", "q3_d2", "q3_2nd", E_RT))
q3.append(cell("q3_2nd", b("调用第二点并继续交会", "拉开基线；同点重复不计新样本"), CHK, 690, 340, 230, 52))
q3.append(cell("q3_cl", b("确定清除并更新 K", "成功不计切换费；二次清除不加 K"), PROC, 350, 432, 300, 46))
q3.append(edge("q3_e10", "q3_cl", "q3_d3", E_DN))
q3.append(cell("q3_d3", "&lt;b&gt;20 频道是否均已&lt;br&gt;清除或证书判空?&lt;/b&gt;", DIA, 390, 496, 220, 82))
q3.append(cell("q3_y3", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 615, 522, 28, 18))
q3.append(cell("q3_n3", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 285, 498, 28, 18))
q3.append(edge("q3_e11", "q3_d3", "q3_out", E_RT))
q3.append(edge_wp(
    "q3_loop",
    "q3_d3",
    "q3_sc",
    LOOP + "exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(18, 537), (18, 111)],
))
q3.append(edge_wp(
    "q3_loop2",
    "q3_ns",
    "q3_sc",
    LOOP + "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(1048, 264), (1048, 6), (18, 6), (18, 111)],
))
q3.append(edge_wp(
    "q3_loop3",
    "q3_2nd",
    "q3_mod",
    LOOP + "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
    [(978, 366), (978, 111)],
))
q3.append(cell("q3_out", b("输出 GREEDY_FAST 在线策略", "先全清 K=N，再缩短任务时间 T"), OUTN, 690, 510, 250, 52))

(OUT / "fig_flow_q3.drawio").write_text(
    mxfile("问题三求解流程", "flow_q3", 1080, 620, "".join(q3)),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# fig_flow_q4
# ---------------------------------------------------------------------------
q4 = []
q4.append(cell("q4_in", b("输入定向混合场景", "继承计时与状态；朝向未知"), INP, 350, 20, 300, 46))
q4.append(edge("q4_e1", "q4_in", "q4_hex", E_DL))
q4.append(edge("q4_e2", "q4_in", "q4_loc", E_DR))
q4.append(cell("q4_hex", b("HEX37 覆盖骨架", "三角格点间距 800 m / 37 点"), PROC, 70, 86, 240, 50))
q4.append(cell("q4_loc", b("累计全部测向楔形", "外包 Ω 与 1500 m 接收半径"), PROC, 690, 86, 240, 50))
q4.append(edge("q4_e3", "q4_hex", "q4_ns", E_ML))
q4.append(edge("q4_e4", "q4_loc", "q4_ns", E_MR))
q4.append(cell("q4_ns", b("改写无信号三分支", "无源 / 过远 / 定向扇外，禁止挖距离圆盘"), INP, 310, 160, 380, 48))
q4.append(edge("q4_e5", "q4_ns", "q4_d1", E_DN))
q4.append(cell("q4_d1", "&lt;b&gt;当前频道是否&lt;br&gt;已有方向观测?&lt;/b&gt;", DIA, 400, 226, 200, 80))
q4.append(cell("q4_y1", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 308, 28, 18))
q4.append(cell("q4_n1", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 250, 28, 18))
q4.append(edge("q4_e6", "q4_d1", "q4_d2", E_DN))
q4.append(edge("q4_e7", "q4_d1", "q4_scan", E_RT))
q4.append(cell("q4_scan", b("沿覆盖路径继续扫频", "圆外测点对边缘外向源有效"), BAD, 690, 240, 240, 52))
q4.append(cell("q4_d2", "&lt;b&gt;包围半径&lt;br&gt;是否 ≤20 m?&lt;/b&gt;", DIA, 400, 332, 200, 80))
q4.append(cell("q4_y2", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 414, 28, 18))
q4.append(cell("q4_n2", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 356, 28, 18))
q4.append(edge("q4_e8", "q4_d2", "q4_cl", E_DN))
q4.append(edge("q4_e9", "q4_d2", "q4_opt", E_RT))
q4.append(cell("q4_opt", b("光学方格兜底", "边长 28 m，半对角线 &lt;20 m"), CHK, 690, 344, 240, 52))
q4.append(cell("q4_cl", b("确定清除或光学成功", "清除与射频朝向无关"), PROC, 350, 438, 300, 46))
q4.append(edge(
    "q4_e10",
    "q4_opt",
    "q4_cl",
    EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
))
q4.append(edge("q4_e11", "q4_cl", "q4_d3", E_DN))
q4.append(cell("q4_d3", "&lt;b&gt;是否 cleared 或&lt;br&gt;certified_absent?&lt;/b&gt;", DIA, 390, 502, 220, 82))
q4.append(cell("q4_y3", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 615, 528, 28, 18))
q4.append(cell("q4_n3", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 285, 504, 28, 18))
q4.append(edge("q4_e12", "q4_d3", "q4_out", E_RT))
q4.append(edge_wp(
    "q4_loop",
    "q4_d3",
    "q4_hex",
    LOOP + "exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(18, 543), (18, 111)],
))
q4.append(edge_wp(
    "q4_loop2",
    "q4_scan",
    "q4_hex",
    LOOP + "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(1020, 266), (1020, 6), (18, 6), (18, 111)],
))
q4.append(cell("q4_out", b("输出混合源覆盖策略", "发现证书与光学清除解耦"), OUTN, 690, 516, 250, 52))

(OUT / "fig_flow_q4.drawio").write_text(
    mxfile("问题四求解流程", "flow_q4", 1080, 630, "".join(q4)),
    encoding="utf-8",
)

print("wrote flows only:")
for p in [
    OUT / "fig_flow_q1.drawio",
    OUT / "fig_flow_q2.drawio",
    OUT / "fig_flow_q3.drawio",
    OUT / "fig_flow_q4.drawio",
]:
    print(f"  {p.name} {p.stat().st_size} bytes")

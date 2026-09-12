# -*- coding: utf-8 -*-
"""Generate DrawIO XML for CUMCM B: roadmap + four problem flows."""
from pathlib import Path

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

EDGE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=1.5;"
    "endArrow=block;endFill=1;jumpStyle=arc;jumpSize=6;"
)
STAGE_ARR = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=4;"
    "endArrow=block;endFill=1;strokeColor=#888888;jumpStyle=arc;jumpSize=6;"
)
MID_ARR = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=2;"
    "endArrow=classic;endFill=1;strokeColor=#555555;jumpStyle=arc;jumpSize=6;"
)


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
        f"<root><mxCell id=\"0\"/><mxCell id=\"1\" parent=\"0\"/>{body}"
        "</root></mxGraphModel></diagram></mxfile>\n"
    )


# ---------------------------------------------------------------------------
# fig_roadmap — Template C (hex, pink/mint), six stages, frozen geometry
# ---------------------------------------------------------------------------
HEX = "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;fillColor=#B4D4D0;strokeColor=#8BAEA9;fontStyle=1;fontSize=14;size=20;fontColor=#333333;"
HEAD = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F5D5E0;strokeColor=#C292A1;fontStyle=1;fontSize=15;fontColor=#333333;"
GRP = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#666666;dashed=1;align=center;verticalAlign=top;fontSize=13;fontStyle=1;spacingTop=8;fontColor=#333333;"
CARD = "rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;fontStyle=1;fontColor=#333333;"
METH = "rounded=1;whiteSpace=wrap;html=1;fillColor=#B4D4D0;strokeColor=#8BAEA9;fontStyle=1;fontSize=12;fontColor=#333333;lineHeight=1.6;"

parts = []
parts.append(cell("h1", "研究阶段", HEAD, 40, 40, 140, 40))
parts.append(cell("h2", "研究内容", HEAD, 380, 40, 380, 40))
parts.append(cell("h3", "研究方法", HEAD, 900, 40, 140, 40))

# stage 1
parts.append(cell("s1", "提出问题", HEX, 40, 160, 140, 60))
parts.append(cell("g1", "研究背景与目标", GRP, 220, 120, 540, 140))
parts.append(cell("c1_1", "频谱管理背景", CARD, 250, 155, 150, 40))
parts.append(cell("c1_2", "四问科学问题", CARD, 430, 155, 150, 40))
parts.append(cell("c1_3", "全清时效目标", CARD, 610, 155, 130, 40))
parts.append(cell("c1_4", "在线未知N与朝向", CARD, 370, 210, 240, 36))
parts.append(edge("e_c1_12", "c1_1", "c1_2", MID_ARR))
parts.append(edge("e_c1_23", "c1_2", "c1_3", MID_ARR))
parts.append(cell("m1", "文献综述法&lt;br&gt;&lt;font style=&quot;font-size:10px;color:#555;&quot;&gt;测向交会文献&lt;/font&gt;", METH, 900, 160, 140, 60))
parts.append(edge("arr_s1_s2", "s1", "s2", STAGE_ARR))

# stage 2
parts.append(cell("s2", "分析问题", HEX, 40, 380, 140, 60))
parts.append(cell("g2", "口径谓词与约束", GRP, 220, 290, 540, 240))
parts.append(cell("c2_1", "题意台账冻结", CARD, 250, 325, 150, 40))
parts.append(cell("c2_2", "符号与坐标系", CARD, 430, 325, 150, 40))
parts.append(cell("c2_3", "观测三值语义", CARD, 610, 325, 130, 40))
parts.append(cell("c2_4", "协议时间模型", CARD, 250, 395, 150, 40))
parts.append(cell("c2_5", "信息集约束", CARD, 430, 395, 150, 40))
parts.append(cell("c2_6", "光学射频解耦", CARD, 610, 395, 130, 40))
parts.append(cell("c2_7", "跨问模块复用", CARD, 370, 465, 240, 40))
parts.append(edge("e_c2_12", "c2_1", "c2_2", MID_ARR))
parts.append(edge("e_c2_23", "c2_2", "c2_3", MID_ARR))
parts.append(edge("e_c2_45", "c2_4", "c2_5", MID_ARR))
parts.append(edge("e_c2_56", "c2_5", "c2_6", MID_ARR))
parts.append(cell("m2", "EDA 口径核对&lt;br&gt;相关分析&lt;br&gt;几何谓词", METH, 900, 370, 140, 80))
parts.append(edge("arr_s2_s3", "s2", "s3", STAGE_ARR))

# stage 3
parts.append(cell("s3", "几何建模", HEX, 40, 660, 140, 60))
parts.append(cell("g3", "交会区域与第二点", GRP, 220, 570, 540, 240))
parts.append(cell("c3_1", "前向闭楔形", CARD, 250, 605, 150, 40))
parts.append(cell("c3_2", "交集直径", CARD, 430, 605, 150, 40))
parts.append(cell("c3_3", "覆盖圆反例", CARD, 610, 605, 130, 40))
parts.append(cell("c3_4", "第二测点策略", CARD, 250, 675, 150, 40))
parts.append(cell("c3_5", "候选指标构建", CARD, 430, 675, 150, 40))
parts.append(cell("c3_6", "半径不确定性", CARD, 610, 675, 130, 40))
parts.append(cell("c3_7", "交会模块封装", CARD, 370, 745, 240, 40))
parts.append(edge("e_c3_12", "c3_1", "c3_2", MID_ARR))
parts.append(edge("e_c3_23", "c3_2", "c3_3", MID_ARR))
parts.append(edge("e_c3_45", "c3_4", "c3_5", MID_ARR))
parts.append(edge("e_c3_56", "c3_5", "c3_6", MID_ARR))
parts.append(cell("m3", "计算几何&lt;br&gt;蒙特卡洛仿真&lt;br&gt;最坏情形分析", METH, 900, 640, 140, 100))
parts.append(edge("arr_s3_s4", "s3", "s4", STAGE_ARR))

# stage 4
parts.append(cell("s4", "在线清除", HEX, 40, 940, 140, 60))
parts.append(cell("g4", "全向在线策略", GRP, 220, 850, 540, 240))
parts.append(cell("c4_1", "同站频道扫描", CARD, 250, 885, 150, 40))
parts.append(cell("c4_2", "近场立即清除", CARD, 430, 885, 150, 40))
parts.append(cell("c4_3", "贪心交会定位", CARD, 610, 885, 130, 40))
parts.append(cell("c4_4", "全清兜底队列", CARD, 250, 955, 150, 40))
parts.append(cell("c4_5", "主线快速策略", CARD, 430, 955, 150, 40))
parts.append(cell("c4_6", "证书队列维护", CARD, 610, 955, 130, 40))
parts.append(cell("c4_7", "策略对照检验", CARD, 320, 1025, 340, 40))
parts.append(edge("e_c4_12", "c4_1", "c4_2", MID_ARR))
parts.append(edge("e_c4_23", "c4_2", "c4_3", MID_ARR))
parts.append(edge("e_c4_45", "c4_4", "c4_5", MID_ARR))
parts.append(edge("e_c4_56", "c4_5", "c4_6", MID_ARR))
parts.append(cell("m4", "在线贪心&lt;br&gt;Bootstrap 重采样&lt;br&gt;模拟器回放", METH, 900, 920, 140, 100))
parts.append(edge("arr_s4_s5", "s4", "s5", STAGE_ARR))

# stage 5
parts.append(cell("s5", "覆盖扩展", HEX, 40, 1200, 140, 60))
parts.append(cell("g5", "定向混合与覆盖", GRP, 220, 1130, 540, 180))
parts.append(cell("c5_1", "三角格点覆盖", CARD, 250, 1165, 150, 40))
parts.append(cell("c5_2", "无信号三分支", CARD, 430, 1165, 150, 40))
parts.append(cell("c5_3", "累计楔形定位", CARD, 610, 1165, 130, 40))
parts.append(cell("c5_4", "光学方格兜底", CARD, 250, 1235, 150, 40))
parts.append(cell("c5_5", "频道判空证书", CARD, 430, 1235, 150, 40))
parts.append(cell("c5_6", "配对离线验证", CARD, 610, 1235, 130, 40))
parts.append(edge("e_c5_12", "c5_1", "c5_2", MID_ARR))
parts.append(edge("e_c5_23", "c5_2", "c5_3", MID_ARR))
parts.append(edge("e_c5_45", "c5_4", "c5_5", MID_ARR))
parts.append(edge("e_c5_56", "c5_5", "c5_6", MID_ARR))
parts.append(cell("m5", "Matplotlib&lt;br&gt;覆盖命题证明&lt;br&gt;比较分析法", METH, 900, 1190, 140, 100))
parts.append(edge("arr_s5_s6", "s5", "s6", STAGE_ARR))

# stage 6
parts.append(cell("s6", "结论与展望", HEX, 40, 1410, 140, 60))
parts.append(cell("g6", "研究结论与应用推广", GRP, 220, 1350, 540, 170))
parts.append(cell("c6_1", "四问主要发现", CARD, 250, 1385, 200, 40))
parts.append(cell("c6_2", "策略建议与实践意义", CARD, 490, 1385, 240, 40))
parts.append(cell("c6_3", "模型推广方向", CARD, 250, 1455, 200, 40))
parts.append(cell("c6_4", "正式测试边界", CARD, 490, 1455, 240, 40))
parts.append(edge("e_c6_12", "c6_1", "c6_2", MID_ARR))
parts.append(edge("e_c6_34", "c6_3", "c6_4", MID_ARR))
parts.append(cell("m6", "归纳总结法&lt;br&gt;LaTeX 论文&lt;br&gt;局限声明", METH, 900, 1400, 140, 80))

# 路线图已人工双行化（height=46），禁止本脚本覆盖
# (OUT / "fig_roadmap.drawio").write_text(
#     mxfile("技术路线图", "roadmap-hex", 1100, 1560, "".join(parts)),
#     encoding="utf-8",
# )

# ---------------------------------------------------------------------------
# Shared flow styles
# ---------------------------------------------------------------------------
INP = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F4FA;strokeColor=#7B9FC0;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
PROC = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7AAA7A;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
DIA = "rhombus;whiteSpace=wrap;html=1;fillColor=#F5F0E8;strokeColor=#B0A080;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
CHK = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0ECF5;strokeColor=#9A8AB0;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
OUTN = "rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF5ED;strokeColor=#82b366;strokeWidth=2;fontSize=11;fontStyle=1;fontColor=#333333;"
BAD = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F5EDED;strokeColor=#B08080;strokeWidth=1.5;fontSize=11;fontStyle=1;fontColor=#333333;"
LAB = "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;"

E_DN = EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
E_RT = EDGE + "strokeColor=#999999;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
E_LT = EDGE + "strokeColor=#999999;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;"
E_UP = EDGE + "strokeColor=#B08080;dashed=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
E_DL = EDGE + "strokeColor=#999999;exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
E_DR = EDGE + "strokeColor=#999999;exitX=0.75;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
E_ML = EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.25;entryY=0;entryDx=0;entryDy=0;"
E_MR = EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.75;entryY=0;entryDx=0;entryDy=0;"


def b(title, sub):
    return (
        f"&lt;b&gt;{title}&lt;/b&gt;&lt;br&gt;"
        f"&lt;font style=&quot;font-size:9px;color:#555555;&quot;&gt;{sub}&lt;/font&gt;"
    )


# ---------------------------------------------------------------------------
# fig_flow_q1  landscape ~1000 x 520
# ---------------------------------------------------------------------------
q1 = []
q1.append(cell("q1_in", b("输入检测点与示向度", "前向闭楔形 / 误差闭区间 ±1°"), INP, 370, 12, 260, 46))
q1.append(edge("q1_e1", "q1_in", "q1_w", E_DL))
q1.append(edge("q1_e2", "q1_in", "q1_d", E_DR))
q1.append(cell("q1_w", b("构造前向闭楔形", "示向度两侧各 1° / 射线半平面"), PROC, 80, 80, 250, 50))
q1.append(cell("q1_d", b("枚举退化情形", "空集 / 点 / 线段 / 无界条带"), PROC, 670, 80, 250, 50))
q1.append(edge("q1_e3", "q1_w", "q1_r", E_ML))
q1.append(edge("q1_e4", "q1_d", "q1_r", E_MR))
q1.append(cell("q1_r", b("求楔形交集 R", "多点交为多边形；两点为四边形"), INP, 350, 155, 300, 48))
q1.append(edge("q1_e5", "q1_r", "q1_dia", E_DN))
q1.append(cell("q1_dia", "&lt;b&gt;R 是否有界&lt;br&gt;且非空?&lt;/b&gt;", DIA, 410, 220, 180, 78))
q1.append(cell("q1_yes", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 500, 300, 28, 18))
q1.append(cell("q1_no", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 600, 244, 28, 18))
q1.append(edge("q1_e6", "q1_dia", "q1_diam", E_DN))
q1.append(edge("q1_e7", "q1_dia", "q1_deg", E_RT))
q1.append(cell("q1_deg", b("退化输出", "报告空 / 无界；不强制多边形"), BAD, 680, 233, 230, 52))
q1.append(edge_wp("q1_loop", "q1_deg", "q1_w", E_UP, [(40, 259), (40, 105)]))
q1.append(cell("q1_diam", b("计算几何直径 diam(R)", "最大点对距离，非覆盖圆直径"), CHK, 350, 325, 300, 48))
q1.append(edge("q1_e8", "q1_diam", "q1_cov", E_DL))
q1.append(edge("q1_e9", "q1_diam", "q1_jung", E_DR))
q1.append(cell("q1_cov", b("直径圆覆盖性判定", "一般不能覆盖 R"), PROC, 80, 400, 250, 50))
q1.append(cell("q1_jung", b("Jung 最小覆盖圆对照", "等边三角形 r = 边长/√3"), PROC, 670, 400, 250, 50))
q1.append(edge("q1_e10", "q1_cov", "q1_out", E_ML))
q1.append(edge("q1_e11", "q1_jung", "q1_out", E_MR))
q1.append(cell("q1_out", b("✓ 输出交会算法与覆盖性结论", "后续清除须核验豪斯多夫半径 ≤20 m"), OUTN, 320, 470, 360, 46))

(OUT / "fig_flow_q1.drawio").write_text(
    mxfile("问题一求解流程", "flow_q1", 1000, 540, "".join(q1)),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# fig_flow_q2
# ---------------------------------------------------------------------------
q2 = []
q2.append(cell("q2_in", b("输入第一检测点与示向度", "单全向源；真位置与 r_i 未知"), INP, 370, 12, 260, 46))
q2.append(edge("q2_e1", "q2_in", "q2_sec", E_DL))
q2.append(edge("q2_e2", "q2_in", "q2_om", E_DR))
q2.append(cell("q2_sec", b("前向 180° 可行扇", "仅用已观测楔形，不用未知真值"), PROC, 80, 80, 250, 50))
q2.append(cell("q2_om", b("叠加圆域与半径区间", "Ω 半径 1800 m；r_i∈[1000,1500]"), PROC, 670, 80, 250, 50))
q2.append(edge("q2_e3", "q2_sec", "q2_cand", E_ML))
q2.append(edge("q2_e4", "q2_om", "q2_cand", E_MR))
q2.append(cell("q2_cand", b("构造第二点候选集", "保证可能收到信号；禁止用未知 G 排点"), INP, 330, 155, 340, 48))
q2.append(edge("q2_e5", "q2_cand", "q2_j", E_DN))
q2.append(cell("q2_j", b("计算候选指标 J*", "最坏点误差 / 交会直径充分条件"), CHK, 350, 220, 300, 48))
q2.append(edge("q2_e6", "q2_j", "q2_dia", E_DN))
q2.append(cell("q2_dia", "&lt;b&gt;diam(R) 能否进入&lt;br&gt;可清除尺度?&lt;/b&gt;", DIA, 400, 285, 200, 82))
q2.append(cell("q2_yes", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 368, 28, 18))
q2.append(cell("q2_no", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 310, 28, 18))
q2.append(edge("q2_e7", "q2_dia", "q2_out", E_DN))
q2.append(edge("q2_e8", "q2_dia", "q2_adj", E_RT))
q2.append(cell("q2_adj", b("调整第二点几何", "拉开基线 / 避开共线"), BAD, 690, 300, 220, 52))
q2.append(edge_wp("q2_loop", "q2_adj", "q2_cand", E_UP + "exitX=0.5;exitY=0;entryX=1;entryY=0.5;", [(800, 220)]))
# fix loop style: from adj top to cand right
q2[-1] = edge_wp(
    "q2_loop",
    "q2_adj",
    "q2_cand",
    EDGE + "strokeColor=#B08080;dashed=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
    [(800, 179)],
)
q2.append(cell("q2_out", b("✓ 输出第二点策略与候选区", "供问题3发现源后直接调用"), OUTN, 330, 400, 340, 46))

(OUT / "fig_flow_q2.drawio").write_text(
    mxfile("问题二求解流程", "flow_q2", 1000, 470, "".join(q2)),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# fig_flow_q3  landscape, two diamonds, parallel, loop
# ---------------------------------------------------------------------------
q3 = []
q3.append(cell("q3_in", b("输入初值与全向场景", "起点 (0,0)，频道 c=1；N∈[10,16] 未知"), INP, 350, 10, 300, 46))
q3.append(edge("q3_e1", "q3_in", "q3_sc", E_DL))
q3.append(edge("q3_e2", "q3_in", "q3_mod", E_DR))
q3.append(cell("q3_sc", b("同站批量扫频", "已清频道不再测向"), PROC, 70, 76, 240, 50))
q3.append(cell("q3_mod", b("复用交会与第二点模块", "楔形交集 + 候选点策略"), PROC, 690, 76, 240, 50))
q3.append(edge("q3_e3", "q3_sc", "q3_obs", E_ML))
q3.append(edge("q3_e4", "q3_mod", "q3_obs", E_MR))
q3.append(cell("q3_obs", b("解析观测三值", "direction / near / no_signal"), INP, 350, 150, 300, 46))
q3.append(edge("q3_e5", "q3_obs", "q3_d1", E_DN))
q3.append(cell("q3_d1", "&lt;b&gt;是否收到方向&lt;br&gt;或进入近场?&lt;/b&gt;", DIA, 400, 214, 200, 80))
q3.append(cell("q3_y1", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 296, 28, 18))
q3.append(cell("q3_n1", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 238, 28, 18))
q3.append(edge("q3_e6", "q3_d1", "q3_d2", E_DN))
q3.append(edge("q3_e7", "q3_d1", "q3_ns", E_RT))
q3.append(cell("q3_ns", b("无信号距离排除", "确信有源时 d&gt;r_i≥1000 m"), BAD, 690, 228, 230, 52))
q3.append(edge("q3_e8", "q3_d2", "q3_cl", E_DN))
q3.append(cell("q3_d2", "&lt;b&gt;包围半径&lt;br&gt;是否 ≤20 m?&lt;/b&gt;", DIA, 400, 318, 200, 80))
q3.append(cell("q3_y2", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 400, 28, 18))
q3.append(cell("q3_n2", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 342, 28, 18))
q3.append(edge("q3_e9", "q3_d2", "q3_2nd", E_RT))
q3.append(cell("q3_2nd", b("调用第二点并继续交会", "拉开基线；同点重复不计新样本"), CHK, 690, 330, 230, 52))
q3.append(cell("q3_cl", b("确定清除并更新 K", "成功不计切换费；二次清除不加 K"), PROC, 350, 422, 300, 46))
q3.append(edge("q3_e10", "q3_cl", "q3_d3", E_DN))
q3.append(cell("q3_d3", "&lt;b&gt;20 频道是否均已&lt;br&gt;清除或证书判空?&lt;/b&gt;", DIA, 390, 486, 220, 82))
q3.append(cell("q3_y3", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 615, 512, 28, 18))
q3.append(cell("q3_n3", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 318, 512, 28, 18))
q3.append(edge("q3_e11", "q3_d3", "q3_out", E_RT))
q3.append(edge_wp(
    "q3_loop",
    "q3_d3",
    "q3_sc",
    EDGE + "strokeColor=#B08080;dashed=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(30, 527), (30, 101)],
))
q3.append(edge_wp(
    "q3_loop2",
    "q3_ns",
    "q3_sc",
    EDGE + "strokeColor=#B08080;dashed=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
    [(805, 120)],
))
q3.append(edge_wp(
    "q3_loop3",
    "q3_2nd",
    "q3_mod",
    EDGE + "strokeColor=#B08080;dashed=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
    [(960, 356), (960, 101)],
))
q3.append(cell("q3_out", b("✓ 输出 GREEDY_FAST 在线策略", "先全清 K=N，再缩短任务时间 T"), OUTN, 690, 500, 250, 52))

(OUT / "fig_flow_q3.drawio").write_text(
    mxfile("问题三求解流程", "flow_q3", 1040, 600, "".join(q3)),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# fig_flow_q4
# ---------------------------------------------------------------------------
q4 = []
q4.append(cell("q4_in", b("输入定向混合场景", "继承计时与状态；朝向未知"), INP, 350, 10, 300, 46))
q4.append(edge("q4_e1", "q4_in", "q4_hex", E_DL))
q4.append(edge("q4_e2", "q4_in", "q4_loc", E_DR))
q4.append(cell("q4_hex", b("HEX37 覆盖骨架", "三角格点间距 800 m / 37 点"), PROC, 70, 76, 240, 50))
q4.append(cell("q4_loc", b("累计全部测向楔形", "外包 Ω 与 1500 m 接收半径"), PROC, 690, 76, 240, 50))
q4.append(edge("q4_e3", "q4_hex", "q4_ns", E_ML))
q4.append(edge("q4_e4", "q4_loc", "q4_ns", E_MR))
q4.append(cell("q4_ns", b("改写无信号三分支", "无源 / 过远 / 定向扇外，禁止挖距离圆盘"), INP, 310, 150, 380, 48))
q4.append(edge("q4_e5", "q4_ns", "q4_d1", E_DN))
q4.append(cell("q4_d1", "&lt;b&gt;当前频道是否&lt;br&gt;已有方向观测?&lt;/b&gt;", DIA, 400, 216, 200, 80))
q4.append(cell("q4_y1", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 298, 28, 18))
q4.append(cell("q4_n1", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 240, 28, 18))
q4.append(edge("q4_e6", "q4_d1", "q4_d2", E_DN))
q4.append(edge("q4_e7", "q4_d1", "q4_scan", E_RT))
q4.append(cell("q4_scan", b("沿覆盖路径继续扫频", "圆外测点对边缘外向源有效"), BAD, 690, 230, 240, 52))
q4.append(cell("q4_d2", "&lt;b&gt;包围半径&lt;br&gt;是否 ≤20 m?&lt;/b&gt;", DIA, 400, 322, 200, 80))
q4.append(cell("q4_y2", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 505, 404, 28, 18))
q4.append(cell("q4_n2", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 610, 346, 28, 18))
q4.append(edge("q4_e8", "q4_d2", "q4_cl", E_DN))
q4.append(edge("q4_e9", "q4_d2", "q4_opt", E_RT))
q4.append(cell("q4_opt", b("光学方格兜底", "边长 28 m，半对角线 &lt;20 m"), CHK, 690, 334, 240, 52))
q4.append(cell("q4_cl", b("确定清除或光学成功", "清除与射频朝向无关"), PROC, 350, 428, 300, 46))
q4.append(edge("q4_e10", "q4_opt", "q4_cl", EDGE + "strokeColor=#999999;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;"))
q4.append(edge("q4_e11", "q4_cl", "q4_d3", E_DN))
q4.append(cell("q4_d3", "&lt;b&gt;是否 cleared 或&lt;br&gt;certified_absent?&lt;/b&gt;", DIA, 390, 492, 220, 82))
q4.append(cell("q4_y3", "&lt;font style=&quot;font-size:10px;color:#7AAA7A;&quot;&gt;&lt;b&gt;是&lt;/b&gt;&lt;/font&gt;", LAB, 615, 518, 28, 18))
q4.append(cell("q4_n3", "&lt;font style=&quot;font-size:10px;color:#B08080;&quot;&gt;&lt;b&gt;否&lt;/b&gt;&lt;/font&gt;", LAB, 318, 518, 28, 18))
q4.append(edge("q4_e12", "q4_d3", "q4_out", E_RT))
q4.append(edge_wp(
    "q4_loop",
    "q4_d3",
    "q4_hex",
    EDGE + "strokeColor=#B08080;dashed=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;",
    [(30, 533), (30, 101)],
))
q4.append(edge_wp(
    "q4_loop2",
    "q4_scan",
    "q4_hex",
    EDGE + "strokeColor=#B08080;dashed=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;",
    [(810, 120)],
))
q4.append(cell("q4_out", b("✓ 输出混合源覆盖策略", "发现证书与光学清除解耦"), OUTN, 690, 506, 250, 52))

(OUT / "fig_flow_q4.drawio").write_text(
    mxfile("问题四求解流程", "flow_q4", 1040, 610, "".join(q4)),
    encoding="utf-8",
)

print("wrote:")
for p in sorted(OUT.glob("*.drawio")):
    print(f"  {p.name} {p.stat().st_size} bytes")

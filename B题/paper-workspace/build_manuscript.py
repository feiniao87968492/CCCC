#!/usr/bin/env python3
"""Build CUMCM 2026 B manuscript.json, figures, and claim-evidence artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WS = Path(__file__).resolve().parent
FIG_DIR = ROOT / "paper-output" / "figures"
WS_FIG = WS / "figures"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_key(path: Path) -> str:
    return "sha256:" + sha256(path)


def setup_font() -> str:
    from matplotlib import font_manager

    for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC"):
        try:
            font_manager.findfont(name, fallback_to_default=False)
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
        except Exception:
            continue
    plt.rcParams["axes.unicode_minus"] = False
    return "DejaVu Sans"


INK = "#202124"
AXIS = "#30343B"
GRID = "#E3E6EA"
SELECTED = "#3B4D7B"
SECONDARY = "#6B7280"
TEAL = "#237C68"
HATCH_A = "///"
HATCH_B = "xxx"
HATCH_C = "..."


def savefig(fig, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    WS_FIG.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    fig.savefig(WS_FIG / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def fig_q1_diameter() -> None:
    verts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, np.sqrt(3.0) / 2.0]])
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    tri = plt.Polygon(verts, closed=True, facecolor="#C7D4E9", edgecolor=INK, linewidth=1.6)
    ax.add_patch(tri)
    ax.plot([0, 1], [0, 0], color=INK, lw=2.2, label="直径边")
    circ = plt.Circle((0.5, 0.0), 0.5, fill=False, edgecolor=SECONDARY, lw=1.6, ls="--")
    ax.add_patch(circ)
    mec = plt.Circle((0.5, np.sqrt(3.0) / 6.0), 1.0 / np.sqrt(3.0), fill=False, edgecolor=SELECTED, lw=1.8)
    ax.add_patch(mec)
    ax.plot(0.5, 0.0, "o", color=INK, ms=4)
    ax.plot(0.5, np.sqrt(3.0) / 6.0, "s", color=SELECTED, ms=5, label="最小覆盖圆心")
    ax.set_aspect("equal")
    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-0.55, 1.05)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(frameon=False, loc="upper right", fontsize=8)
    ax.set_title("等边三角形：直径圆不能覆盖定位区域")
    savefig(fig, "fig-q1-diameter.png")


def fig_q3_tk() -> None:
    names = ["GREEDY", "GREEDY_FAST", "GREEDY_ABORT"]
    vals = [390, 341, 382]
    hatches = [HATCH_A, HATCH_B, HATCH_C]
    colors = ["#C7D4E9", "#6485BF", "#B8BEC6"]
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    bars = ax.bar(names, vals, color=colors, edgecolor=INK, linewidth=1.0)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    ax.set_ylabel("演练平均 T/K (s)")
    ax.set_ylim(0, 500)
    ax.axhline(341, color=SELECTED, ls="--", lw=1.0)
    for x, y in zip(names, vals):
        ax.text(x, y + 8, f"{y}", ha="center", va="bottom", color=INK, fontsize=9)
    ax.grid(True, axis="y", color=GRID, lw=0.6)
    ax.set_title("问题3演练：10局平均定位清除时间")
    savefig(fig, "fig-q3-practice-tk.png")


def fig_q4_hex() -> None:
    step = 800.0
    e1 = np.array([step, 0.0])
    e2 = np.array([step / 2.0, step * np.sqrt(3.0) / 2.0])
    route = [
        (0, 0), (-1, 0), (-1, 1), (-2, 1), (-3, 1), (-3, 0), (-2, 0),
        (-2, -1), (-1, -2), (-1, -1), (0, -1), (0, -2), (0, -3), (1, -3),
        (1, -2), (2, -3), (3, -3), (2, -2), (1, -1), (1, 0), (0, 1),
        (-1, 2), (-2, 2), (-3, 2), (-3, 3), (-2, 3), (-1, 3), (0, 3),
        (0, 2), (1, 2), (1, 1), (2, 1), (3, 0), (2, 0), (2, -1), (3, -2),
        (3, -1),
    ]
    pts = np.array([q * e1 + r * e2 for q, r in route])
    circle = plt.Circle((0, 0), 1800, fill=False, edgecolor=SECONDARY, ls="--", lw=1.2)
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    ax.add_patch(circle)
    ax.plot(pts[:, 0], pts[:, 1], "-", color=SELECTED, lw=1.4)
    ax.plot(pts[:, 0], pts[:, 1], "o", color=INK, ms=4)
    ax.plot(0, 0, "s", color=TEAL, ms=6, label="原点")
    ax.set_aspect("equal")
    ax.set_xlabel("x / m")
    ax.set_ylabel("y / m")
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(frameon=False, loc="upper right", fontsize=8)
    ax.set_title("HEX37 三角晶格覆盖点与离线 Hamilton 路")
    savefig(fig, "fig-q4-hex37.png")


def fig_q4_paired() -> None:
    names = ["SQUARE81", "HEX37"]
    vals = [1313.16, 836.91]
    hatches = [HATCH_A, HATCH_B]
    colors = ["#C7D4E9", "#6485BF"]
    fig, ax = plt.subplots(figsize=(4.8, 3.6))
    bars = ax.bar(names, vals, color=colors, edgecolor=INK, linewidth=1.0, width=0.55)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    ax.set_ylabel("离线配对平均 T/K (s)")
    for x, y in zip(names, vals):
        ax.text(x, y + 20, f"{y:.2f}", ha="center", color=INK, fontsize=9)
    ax.set_ylim(0, 1600)
    ax.grid(True, axis="y", color=GRID, lw=0.6)
    ax.set_title("问题4离线30/30：覆盖点集对 T/K")
    savefig(fig, "fig-q4-paired-tk.png")


def para(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def eq(latex: str, label: str) -> dict:
    return {"type": "equation", "latex": latex, "label": label}


def bullets(items: list[str]) -> dict:
    return {"type": "bullet_list", "items": items}


def numbered(items: list[str]) -> dict:
    return {"type": "numbered_list", "items": items}


def table(caption: str, headers: list[str], rows: list[list[str]], label: str) -> dict:
    return {"type": "table", "caption": caption, "headers": headers, "rows": rows, "label": label}


def figure(source: str, caption: str, label: str, width: float = 0.82) -> dict:
    return {"type": "figure", "source": source, "caption": caption, "label": label, "width": width}


def main() -> None:
    setup_font()
    fig_q1_diameter()
    fig_q3_tk()
    fig_q4_hex()
    fig_q4_paired()

    files = {
        "q1_q2_demo.json": ROOT / "data_preparation" / "output" / "q1_q2_demo.json",
        "parameters.csv": ROOT / "data_preparation" / "parameters.csv",
        "audit_summary.json": ROOT / "data_preparation" / "output" / "audit_summary.json",
        "q3-greedy-fast.md": ROOT / "docs" / "Q3主线-GREEDY_FAST.md",
        "paired_summary.json": ROOT / "experiments" / "q4_hex37" / "paired_summary.json",
        "hex37.json": ROOT / "experiments" / "q4_hex37" / "hex37.json",
        "practice_results.md": ROOT / "experiments" / "q4_simulator" / "practice_results.md",
        "q4-status.md": ROOT / "docs" / "Q4完成情况与修复-20260911.md",
        "q4-cover.md": ROOT / "docs" / "Q4覆盖命题.md",
        "sessions_clean.csv": ROOT / "data_preparation" / "output" / "sessions_clean.csv",
    }
    registry = {}
    for name, path in files.items():
        digest = sha_key(path)
        registry[f"data:{name}#file"] = {
            "anchor": digest,
            "locator": name,
            "note": str(path.relative_to(ROOT)).replace("\\", "/"),
        }
    registry["data:q1_q2_demo.json#q1_equilateral.diameter_circle_covers"] = {
        "anchor": sha_key(files["q1_q2_demo.json"]),
        "locator": "q1_q2_demo.json",
        "note": "q1_equilateral.diameter_circle_covers=false",
    }
    registry["data:q1_q2_demo.json#q2.theoretical_sector_rho_m"] = {
        "anchor": sha_key(files["q1_q2_demo.json"]),
        "locator": "q1_q2_demo.json",
        "note": "theoretical_sector_rho_m=750.1142460329307",
    }
    registry["run:q3-greedy-fast.md#mean_T_over_K"] = {
        "anchor": sha_key(files["q3-greedy-fast.md"]),
        "locator": "q3-greedy-fast.md",
        "note": "docs/Q3主线-GREEDY_FAST.md 10/10 practice, mean T/K=341",
    }
    registry["run:paired_summary.json#T_over_K.hex37_mean"] = {
        "anchor": sha_key(files["paired_summary.json"]),
        "locator": "paired_summary.json",
        "note": "hex37_mean=836.9129462514154, 30/30",
    }
    registry["run:paired_summary.json#hex37_all_cleared"] = {
        "anchor": sha_key(files["paired_summary.json"]),
        "locator": "paired_summary.json",
        "note": "hex37_all_cleared=30, hex37_all_certified=30",
    }
    registry["run:practice_results.md#20260911-231856-q4-p4.T_over_K"] = {
        "anchor": sha_key(files["practice_results.md"]),
        "locator": "practice_results.md",
        "note": "PREFIX_A practice T/K=822.38, K/N=11/11",
    }
    registry["data:parameters.csv#target_region_radius"] = {
        "anchor": sha_key(files["parameters.csv"]),
        "locator": "parameters.csv",
        "note": "1800 m",
    }
    registry["data:audit_summary.json#clean_rows"] = {
        "anchor": sha_key(files["audit_summary.json"]),
        "locator": "audit_summary.json",
        "note": "2 sessions, 12 clean rows",
    }
    registry["data:q4-cover.md#HEX37"] = {
        "anchor": sha_key(files["q4-cover.md"]),
        "locator": "q4-cover.md",
        "note": "docs/Q4覆盖命题.md covering radius 800/sqrt(3)",
    }

    background_ledger = [
        {
            "background_id": "bg-omega",
            "claim": "干扰源分布在半径1800米的已知圆形目标区域内，机器狗定位清除须在该区域内完成精准定位阶段。",
            "source_type": "problem_statement",
            "status": "confirmed",
            "scope": "problem_definition",
            "locator": "B题.pdf 第1页",
            "evidence": [],
            "derivation": "",
            "relevance": "确定搜索宇宙与源位置约束，而不是机器狗禁出区。",
            "retrieval": {"mode": "user_provided", "query": "", "accessed_at": "2026-09-10"},
        },
        {
            "background_id": "bg-task",
            "claim": "任务是自动定位并清除全部干扰源，在全部清除前提下使虚拟任务时间尽可能短。",
            "source_type": "problem_statement",
            "status": "confirmed",
            "scope": "problem_definition",
            "locator": "B题.pdf 问题3",
            "evidence": [],
            "derivation": "",
            "relevance": "规定先全清、再比时间的决策顺序。",
            "retrieval": {"mode": "user_provided", "query": "", "accessed_at": "2026-09-10"},
        },
        {
            "background_id": "bg-n",
            "claim": "问题3与问题4中干扰源个数N属于10到16，在线未知；正式测试不返回N。",
            "source_type": "problem_statement",
            "status": "confirmed",
            "scope": "problem_definition",
            "locator": "B题.pdf 问题3-4、附件2",
            "evidence": [],
            "derivation": "",
            "relevance": "禁止把清满10个当作结束条件。",
            "retrieval": {"mode": "user_provided", "query": "", "accessed_at": "2026-09-10"},
        },
        {
            "background_id": "bg-bearing",
            "claim": "有信号时测向机返回示向度，误差界为闭区间正负1度，接口给出两位小数。",
            "source_type": "problem_statement",
            "status": "confirmed",
            "scope": "problem_definition",
            "locator": "B题.pdf 附录2、附件2 §2.3",
            "evidence": [],
            "derivation": "",
            "relevance": "交会定位必须使用有界角域而不是精确射线。",
            "retrieval": {"mode": "user_provided", "query": "", "accessed_at": "2026-09-10"},
        },
        {
            "background_id": "bg-data-sessions",
            "claim": "附件接口样例清洗后得到2个会话、12条有效动作记录，其中direction 2条、no_signal 4条，未发现结构性错误。",
            "source_type": "supplied_data",
            "status": "derived",
            "scope": "background_context",
            "locator": "data_preparation/output/audit_summary.json",
            "evidence": ["data:audit_summary.json#clean_rows"],
            "derivation": "由 prepare.py 对附件1提取的请求记录做严格JSON解析与字段校验后汇总。",
            "relevance": "说明官方接口观测形态，不能当作问题3/4成绩。",
            "retrieval": {"mode": "user_provided", "query": "", "accessed_at": "2026-09-10"},
        },
        {
            "background_id": "bg-radius",
            "claim": "参数表冻结目标圆半径1800米、接收半径1000至1500米、示向误差1度、清除半径20米。",
            "source_type": "supplied_data",
            "status": "confirmed",
            "scope": "background_context",
            "locator": "data_preparation/parameters.csv",
            "evidence": ["data:parameters.csv#target_region_radius"],
            "derivation": "直接读取冻结参数表28项，不另改数。",
            "relevance": "全文几何与计时常数的唯一数值来源。",
            "retrieval": {"mode": "user_provided", "query": "", "accessed_at": "2026-09-10"},
        },
    ]

    evidence_ledger = [
        {
            "claim_id": "c-assume-bounded-error",
            "claim": "示向度误差为有界闭区间正负1度，不引入未知概率分布。",
            "claim_kind": "assumption",
            "status": "confirmed",
            "evidence": ["background:bg-bearing", "data:parameters.csv#target_region_radius"],
        },
        {
            "claim_id": "c-param-omega",
            "claim": "源位置约束圆半径为1800米。",
            "claim_kind": "parameter",
            "status": "confirmed",
            "evidence": ["data:parameters.csv#target_region_radius", "background:bg-omega"],
        },
        {
            "claim_id": "c-model-wedge",
            "claim": "问题1定位区域由各检测点前向正负1度闭角域的交集构成。",
            "claim_kind": "model",
            "status": "confirmed",
            "evidence": ["background:bg-bearing", "equation:eq-wedge"],
        },
        {
            "claim_id": "c-method-diameter",
            "claim": "多边形定位区域直径取顶点最远点对距离。",
            "claim_kind": "method",
            "status": "confirmed",
            "evidence": ["data:q1_q2_demo.json#q1_equilateral.diameter_circle_covers", "equation:eq-diam"],
        },
        {
            "claim_id": "c-result-q1-cover",
            "claim": "以定位区域直径为直径的圆一般不能覆盖该区域；等边三角形反例中直径圆覆盖判定为否。",
            "claim_kind": "result",
            "status": "derived",
            "evidence": [
                "data:q1_q2_demo.json#q1_equilateral.diameter_circle_covers",
                "figure:fig-q1-diameter",
                "table:tab-q1-demo",
            ],
        },
        {
            "claim_id": "c-model-q2",
            "claim": "问题2以最坏剩余覆盖半径J(q)评价第二检测点，搜索中心为第一点扇形可行域的最小覆盖圆而非固定极坐标网格。",
            "claim_kind": "model",
            "status": "confirmed",
            "evidence": ["data:q1_q2_demo.json#q2.theoretical_sector_rho_m", "equation:eq-sector-rho"],
        },
        {
            "claim_id": "c-result-q2-rho",
            "claim": "理论扇形覆盖半径为1500/(2 cos 1°)≈750.114米。",
            "claim_kind": "result",
            "status": "derived",
            "evidence": ["data:q1_q2_demo.json#q2.theoretical_sector_rho_m", "equation:eq-sector-rho"],
        },
        {
            "claim_id": "c-method-q3",
            "claim": "问题3主线策略为GREEDY_FAST：发现后优先确定清除，保留SAFE兜底，SourceBudgetS=0。",
            "claim_kind": "method",
            "status": "confirmed",
            "evidence": ["run:q3-greedy-fast.md#mean_T_over_K"],
        },
        {
            "claim_id": "c-result-q3-341",
            "claim": "问题3官方演练中GREEDY_FAST在10局全部清除，平均T/K为341秒，区间244至450秒。",
            "claim_kind": "result",
            "status": "confirmed",
            "evidence": [
                "run:q3-greedy-fast.md#mean_T_over_K",
                "figure:fig-q3-practice-tk",
                "table:tab-q3-practice",
            ],
        },
        {
            "claim_id": "c-model-hex37",
            "claim": "问题4发现层采用边长800米的三角晶格HEX37，覆盖半径为800/√3，用于未知朝向下的射频可检测证书。",
            "claim_kind": "model",
            "status": "confirmed",
            "evidence": ["data:q4-cover.md#HEX37", "equation:eq-hex-delta"],
        },
        {
            "claim_id": "c-result-q4-3030",
            "claim": "HEX37离线配对种子0至29共30组全部全清且完成无源证书，平均T/K为836.91秒，对照SQUARE81的1313.16秒。",
            "claim_kind": "result",
            "status": "confirmed",
            "evidence": [
                "run:paired_summary.json#hex37_all_cleared",
                "run:paired_summary.json#T_over_K.hex37_mean",
                "figure:fig-q4-paired-tk",
                "table:tab-q4-offline",
            ],
        },
        {
            "claim_id": "c-result-q4-practice",
            "claim": "问题4演练最新PREFIX_A局20260911-231856-q4-p4的T/K为822.38秒，K/N=11/11并完成证书。",
            "claim_kind": "result",
            "status": "confirmed",
            "evidence": ["run:practice_results.md#20260911-231856-q4-p4.T_over_K", "table:tab-q4-practice"],
        },
        {
            "claim_id": "c-val-q1",
            "claim": "问题1直径圆覆盖结论由等边三角形解析反例与离线几何演示共同检验。",
            "claim_kind": "validation",
            "status": "derived",
            "evidence": ["data:q1_q2_demo.json#q1_equilateral.diameter_circle_covers"],
        },
        {
            "claim_id": "c-val-q3",
            "claim": "问题3有效性用官方演练10局全清率与T/K检验，不是正式测试。",
            "claim_kind": "validation",
            "status": "confirmed",
            "evidence": ["run:q3-greedy-fast.md#mean_T_over_K"],
        },
        {
            "claim_id": "c-val-q4",
            "claim": "问题4有效性用离线30/30全清证书与演练全清证书检验。",
            "claim_kind": "validation",
            "status": "confirmed",
            "evidence": ["run:paired_summary.json#hex37_all_cleared", "run:practice_results.md#20260911-231856-q4-p4.T_over_K"],
        },
        {
            "claim_id": "c-stab-cover",
            "claim": "将覆盖由SQUARE81改为HEX37后，30组配对仍保持30/30全清，平均T/K下降36.27%。",
            "claim_kind": "stability",
            "status": "confirmed",
            "evidence": ["run:paired_summary.json#T_over_K.hex37_mean", "run:paired_summary.json#hex37_all_cleared"],
        },
        {
            "claim_id": "c-lim-official",
            "claim": "问题3与问题4正式测试尚未授权执行，表1正式成绩缺失，演练T/K不得填入正式表。",
            "claim_kind": "limitation",
            "status": "confirmed",
            "evidence": ["run:q3-greedy-fast.md#mean_T_over_K", "table:tab-formal-missing"],
        },
        {
            "claim_id": "c-conc",
            "claim": "四问均给出可执行模型与算法；直径圆不能覆盖，GREEDY_FAST演练10/10且平均T/K为341秒，HEX37离线30/30。",
            "claim_kind": "conclusion",
            "status": "confirmed",
            "evidence": [
                "data:q1_q2_demo.json#q1_equilateral.diameter_circle_covers",
                "run:q3-greedy-fast.md#mean_T_over_K",
                "run:paired_summary.json#hex37_all_cleared",
            ],
        },
    ]

    manuscript = {
        "title": "无线电干扰源的快速自动定位与清除",
        "problem": "B",
        "abstract": (
            "针对圆形目标区域内未知个数无线电干扰源的自动定位与清除，建立有界误差示向度的前向角域交会模型，"
            "并给出第二检测点选择、全向在线搜索与定向混合覆盖清除算法。"
            "问题1证明：以定位区域直径为直径的圆一般不能覆盖该区域；等边三角形反例的覆盖判定为否。"
            "问题2以最坏剩余覆盖半径评价第二检测点，理论扇形半径为750.114米。"
            "问题3主线GREEDY_FAST在10局官方演练中全部清除，平均定位清除时间341秒，并用全清率检验策略有效性。"
            "问题4采用HEX37三角晶格覆盖，离线30组配对全部全清并完成无源证书，平均T/K为836.91秒；"
            "演练PREFIX_A局T/K为822.38秒。上述数值均为演练或离线几何结果，正式测试尚未执行。"
        ),
        "keywords": ["交会定位", "示向度", "覆盖路径", "在线搜索", "定向干扰源"],
        "background_ledger": background_ledger,
        "evidence_registry": registry,
        "evidence_ledger": evidence_ledger,
        "references": [
            {
                "id": "Church1974MaximalCovering",
                "citation": "Church R, ReVelle C. The maximal covering location problem. Papers in Regional Science, 1974, 32(1): 101-118.",
                "status": "verified",
                "verification": "DOI:10.1111/j.1435-5597.1974.tb00902.x",
            },
            {
                "id": "Dijkstra1959ShortestPath",
                "citation": "Dijkstra E W. A note on two problems in connexion with graphs. Numerische Mathematik, 1959, 1(1): 269-271.",
                "status": "verified",
                "verification": "DOI:10.1007/bf01386390",
            },
            {
                "id": "Galceran2013CPP",
                "citation": "Galceran E, Carreras M. A survey on coverage path planning for robotics. Robotics and Autonomous Systems, 2013, 61(12): 1258-1276.",
                "status": "verified",
                "verification": "DOI:10.1016/j.robot.2013.09.001",
            },
            {
                "id": "Bishop2010Geometry",
                "citation": "Bishop A N, Fidan B, Anderson B D O, et al. Optimality analysis of sensor-target localization geometries. Automatica, 2010, 46(3): 479-492.",
                "status": "verified",
                "verification": "DOI:10.1016/j.automatica.2009.12.003",
            },
            {
                "id": "Stansfield1947DF",
                "citation": "Stansfield R G. Statistical theory of D.F. fixing. Journal of the Institution of Electrical Engineers, 1947, 94(15): 762-770.",
                "status": "verified",
                "verification": "DOI:10.1049/ji-3a-2.1947.0088",
            },
        ],
        "sections": [
            {
                "title": "问题背景与问题重述",
                "roles": ["background", "problem"],
                "background_ids": [
                    "bg-omega",
                    "bg-task",
                    "bg-n",
                    "bg-bearing",
                    "bg-data-sessions",
                    "bg-radius",
                ],
                "claim_ids": [],
                "blocks": [
                    para(
                        "无线电干扰源的精准定位通常要在已知分布区域内近距测向完成。本题给出半径1800米的圆形目标区域，源个数在10到16之间但在线未知，要求一只机器狗从原点出发，利用测向、移动与光学清除接口，在全部清除的前提下缩短虚拟任务时间。"
                    ),
                    para(
                        "测向机在覆盖内返回示向度，误差不超过1度；过近则只报告near，无信号则报告no_signal。清除成功当且仅当指定频道存在未清除源且欧氏距离不超过20米，与射频朝向无关。问题4另有定向源，有效辐射为朝向两侧各90度的闭扇形。"
                    ),
                    para(
                        "四个子问题依次为：由多点示向度计算交会多边形直径并回答直径圆能否覆盖；在仅有一个全向示向度时给出第二检测点策略与候选区；对全部全向源给出在线搜索定位清除算法并用演练检验；在全向与定向混合且朝向未知时扩展策略。附件给出接口计时与两局样例会话，清洗后得到12条有效动作，其中direction 2条、no_signal 4条，用于核对观测形态，不作为成绩。"
                    ),
                    para(
                        "本文不把1800米圆当作机器狗禁出区，不把清满10个当作结束，不把示向度当精确射线，也不把单点全频道无信号当作无源证书。覆盖路径规划的一般方法见文献，本题的证书必须针对未知朝向与未知接收半径专门证明。"
                    ),
                ],
            },
            {
                "title": "模型假设与符号",
                "roles": ["assumptions"],
                "background_ids": [],
                "claim_ids": ["c-assume-bounded-error", "c-param-omega"],
                "blocks": [
                    para(
                        "假设干扰源位置在目标圆内固定，频道互异且时不变；全向源覆盖为圆盘，定向源覆盖为180度闭扇形。示向误差为有界集合而非高斯分布，因此定位对象是可行集而不是点估计置信圆。机器狗允许离开目标圆，源不得在圆外。"
                    ),
                    table(
                        "主要符号",
                        ["符号", "含义", "单位"],
                        [
                            ["Ω", "目标圆域，半径1800", "m"],
                            ["N", "干扰源总数，属于10到16", "1"],
                            ["K", "已成功清除数", "1"],
                            ["θ̂", "示向度，误差界1度", "deg"],
                            ["r_i", "源i接收半径，属于[1000,1500]", "m"],
                            ["ρ", "可行集到候选点的豪斯多夫半径", "m"],
                            ["T", "虚拟任务时间", "s"],
                        ],
                        "tab-symbols",
                    ),
                    para(
                        "计时按附件协议：移动速度5米每秒，检测5秒，频道切换1秒，清除失败3秒，成功再加2秒。T包含空扫与失败动作。平均定位清除时间为T/K，K=0时无定义。"
                    ),
                ],
            },
            {
                "title": "数据来源与接口观测",
                "roles": ["data"],
                "background_ids": [],
                "claim_ids": ["c-param-omega"],
                "blocks": [
                    para(
                        "数值常数全部来自冻结参数表，共28项，与题面及附件一致。目标圆半径1800米、接收半径1000至1500米、示向误差1度、近距5米、清除20米。代码禁止另写一套常数。"
                    ),
                    para(
                        "附件样例会话经严格JSON解析后得到2局12条清洁记录，重复动作按幂等回放识别，未静默删行。这些记录只用于确认direction、near、no_signal三种返回及计时字段，不能外推正式成绩。"
                    ),
                    para(
                        "问题3、问题4的数量结果来自官方演练接口与本地几何模拟器。演练各局随机非配对；离线30组使用固定种子与有界确定误差。正式测试日志不存在，表1相应单元格标记为无正式日志。"
                    ),
                ],
            },
            {
                "title": "模型建立",
                "roles": ["model"],
                "background_ids": [],
                "claim_ids": ["c-model-wedge", "c-model-q2", "c-model-hex37"],
                "blocks": [
                    para(
                        "问题1的定位区域是各检测点前向闭角域的交集。对检测点s与示向度α，误差界ε=1°，角域由两条过s的射线围成，等价为两个闭半平面。"
                    ),
                    eq(
                        r"W(s,\alpha)=\{\,x\in\mathbb{R}^{2}: n_{-}(x-s)\le 0,\; n_{+}(x-s)\le 0\,\}",
                        "eq-wedge",
                    ),
                    para(
                        "多个检测点时取交集R。R可能为空、无界、退化为点或线段，算法必须输出显式状态。直径定义为区域内最远两点距离，对凸多边形只需检查顶点对。"
                    ),
                    eq(
                        r"\mathrm{diam}(R)=\max_{p,q\in R}\|p-q\|",
                        "eq-diam",
                    ),
                    para(
                        "以直径为直径的圆一般不能覆盖原区域。等边三角形直径等于边长d，最小覆盖圆半径为d/√3>d/2，因此直径圆不能覆盖。该反例同时说明：清除点充分条件应使用到区域的豪斯多夫半径不超过20米，不能用直径的一半代替。"
                    ),
                    para(
                        "问题2只有一个全向示向度。第一点观测后，源位于楔形、目标圆与最大接收圆盘的交集F1。理论扇形可用一个半径"
                    ),
                    eq(
                        r"\rho_{\mathrm{sec}}=\frac{1500}{2\cos 1^{\circ}}\approx 750.114\,\mathrm{m}",
                        "eq-sector-rho",
                    ),
                    para(
                        "的圆覆盖。第二点q的评价不是未知真位置上的最优布置，而是对near、direction与no_signal三分支取最坏剩余覆盖半径J(q)。候选在F1最小覆盖圆附近分层生成，删除20至3000米固定极坐标网格。输出是候选集推荐，不是声称全局最优的q*。"
                    ),
                    para(
                        "问题3全部为全向源。发现层需要有限测点保证：对任意源位与未知半径下界1000米，至少一点落入接收圆。实现采用原点加半径1200米六等分外围点的七点集作为历史对照，主线在线策略为GREEDY_FAST：对已发现频道优先用累计楔形收缩后的确定清除，失败则有限启发式，再回退光学网格SAFE。终止不能用K=10，必须对未观测频道给出覆盖证书或N=16计数证书。"
                    ),
                    para(
                        "问题4增加未知朝向。SQUARE81是600米方格81点，可证对任意g∈Ω与任意朝向d，存在格点落入最小接收半径内部且严格位于180度发射半平面内。HEX37改用边长800米三角晶格、环数3共37点，无限晶格覆盖半径"
                    ),
                    eq(
                        r"\delta=800/\sqrt{3}\approx 461.880\,\mathrm{m}",
                        "eq-hex-delta",
                    ),
                    para(
                        "构造点y=g+500d落在半径2300米盘内，其最近格点同时满足距离与半平面松弛。有限37点相对第4环的归属有约9.4米间隙。同一点集覆盖全向源。频道在全部覆盖点无信号则判空。寻路使用离线Hamilton路，禁止在线k!枚举。"
                    ),
                    para(
                        "覆盖选址思想与最大覆盖问题相关，但本题证书针对最坏几何而非需求权重。最短路只用于覆盖图上的固定骨架，不把动态网络最短路当作最优搜索。"
                    ),
                ],
            },
            {
                "title": "算法与求解结果",
                "roles": ["solution"],
                "background_ids": [],
                "claim_ids": [
                    "c-method-diameter",
                    "c-result-q1-cover",
                    "c-result-q2-rho",
                    "c-method-q3",
                    "c-result-q3-341",
                    "c-result-q4-3030",
                    "c-result-q4-practice",
                ],
                "blocks": [
                    para(
                        "问题1算法：构造半平面，线性规划判定可行与无界；枚举相邻约束交点得到顶点，计算最远点对作为直径，并比较最小覆盖圆半径与直径一半。离线演示中等边三角形直径约为1，最小覆盖圆半径约为0.577，直径圆覆盖判定为否。"
                    ),
                    table(
                        "问题1离线几何演示",
                        ["实例", "状态", "直径", "最小覆盖圆半径", "直径圆是否覆盖"],
                        [
                            ["等边三角形", "polygon", "1.000", "0.577", "否"],
                            ["两楔交会", "polygon", "9.877", "4.939", "演示未作覆盖断言"],
                        ],
                        "tab-q1-demo",
                    ),
                    figure(
                        "figures/fig-q1-diameter.png",
                        "等边三角形定位区域：实线直径圆不能覆盖顶点，虚线为直径圆，深色圆为最小覆盖圆。",
                        "fig-q1-diameter",
                    ),
                    para(
                        "问题2算法在F1外包多边形上计算最小覆盖圆c1，于半径比例0、0.25、0.5、0.75、1及探索环带上取候选，按J(q)排序。演示实例理论扇形半径750.114米，推荐点对应J约为43.03米，该值只说明候选集分辨率，不是现场第二点。"
                    ),
                    para(
                        "问题3在线流程：按发现点扫描频道；direction进入累计楔形后验；rho不超过20米则确定清除；否则有限中心试清与补测；失败进入光学SAFE。GREEDY_FAST令SourceBudgetS=0，不在发现完成后放弃未清源。对照GREEDY全清但更慢，GREEDY_ABORT放弃SAFE后全清仅1/10，不作候选。"
                    ),
                    table(
                        "问题3官方演练10局对照（非正式、非配对）",
                        ["策略", "全清", "平均T/K", "区间", "SAFE均值"],
                        [
                            ["GREEDY", "10/10", "390", "334-455", "1.20"],
                            ["GREEDY_FAST", "10/10", "341", "244-450", "0.20"],
                            ["GREEDY_ABORT", "1/10", "382", "295-482", "0"],
                        ],
                        "tab-q3-practice",
                    ),
                    figure(
                        "figures/fig-q3-practice-tk.png",
                        "问题3演练平均T/K。GREEDY_FAST为341秒，柱面斜线、网格与点纹区分策略，不单靠颜色。",
                        "fig-q3-practice-tk",
                    ),
                    para(
                        "问题4定位累计全部direction前向楔、1500米外包、目标圆外包与near的5米约束；Q4的no_signal不挖距离圆盘。包围半径不超过20米时确定清除；光学兜底将凸定位域划为边长28米方格，半对角线14√2<20米。发现层默认HEX37，SQUARE81保留为回归基线。"
                    ),
                    table(
                        "问题4离线配对种子0-29",
                        ["覆盖", "全清且证书", "平均T/K (s)", "平均路程 (m)", "平均测向次数"],
                        [
                            ["SQUARE81", "30/30", "1313.16", "68250.75", "679.73"],
                            ["HEX37", "30/30", "836.91", "46196.45", "337.10"],
                        ],
                        "tab-q4-offline",
                    ),
                    figure(
                        "figures/fig-q4-hex37.png",
                        "HEX37共37个覆盖点及从原点出发的800米边Hamilton路，虚线圆为半径1800米的目标域，坐标轴单位为米。",
                        "fig-q4-hex37",
                    ),
                    figure(
                        "figures/fig-q4-paired-tk.png",
                        "离线30组配对平均T/K：SQUARE81为1313.16秒，HEX37为836.91秒，斜线与网格编码覆盖方案。",
                        "fig-q4-paired-tk",
                    ),
                    para(
                        "演练最新PREFIX_A记录20260911-231856-q4-p4的T/K为822.38秒，K/N=11/11并完成证书。演练随机非配对，不能与离线36.27%降幅混为同一对照。"
                    ),
                    table(
                        "问题4演练摘录（非正式）",
                        ["证据", "路线", "K/N", "T/K (s)", "证书"],
                        [
                            ["20260911-231856-q4-p4", "PREFIX_A", "11/11", "822.38", "是"],
                            ["20260911-231927-q4-p4", "PREFIX_A", "10/10", "930.28", "是"],
                        ],
                        "tab-q4-practice",
                    ),
                    para(
                        "问题3与问题4正式测试各3次，中止也占次。当前无正式日志，表1不能填写案例编码或成绩。"
                    ),
                    table(
                        "表1 正式测试结果（缺失）",
                        ["测试", "案例编码", "清除干扰源个数", "平均定位清除时间", "程序运行时间"],
                        [
                            ["问题3测试1", "无正式日志", "无正式日志", "无正式日志", "无正式日志"],
                            ["问题3测试2", "无正式日志", "无正式日志", "无正式日志", "无正式日志"],
                            ["问题3测试3", "无正式日志", "无正式日志", "无正式日志", "无正式日志"],
                            ["问题4测试1", "无正式日志", "无正式日志", "无正式日志", "无正式日志"],
                            ["问题4测试2", "无正式日志", "无正式日志", "无正式日志", "无正式日志"],
                            ["问题4测试3", "无正式日志", "无正式日志", "无正式日志", "无正式日志"],
                        ],
                        "tab-formal-missing",
                    ),
                ],
            },
            {
                "title": "验证与检验",
                "roles": ["validation"],
                "background_ids": [],
                "claim_ids": ["c-val-q1", "c-val-q3", "c-val-q4"],
                "blocks": [
                    para(
                        "问题1用解析反例与代码演示交叉检验：直径定义与最小覆盖圆分离，覆盖判定与几何事实一致。问题2把c1与J(q)限制为候选推荐，避免把演示点写成现场最优。"
                    ),
                    para(
                        "问题3以官方演练全清率为主检验，GREEDY_FAST为10/10，平均T/K为341秒。ABORT对照表明去掉SAFE会破坏全清，因此主线保留兜底。各局非配对，区间244至450秒只描述该批演练，不外推总体分布。"
                    ),
                    para(
                        "问题4离线几何使用与题设一致的有界误差与计时，30/30全清且证书，HEX37平均T/K为836.91秒。演练PREFIX_A局T/K为822.38秒，证书完成。独立极端误差留出在修订记录中为另外30/30，本文主结论以paired_summary.json为准。"
                    ),
                ],
            },
            {
                "title": "敏感性与稳健性",
                "roles": ["sensitivity"],
                "background_ids": [],
                "claim_ids": ["c-stab-cover"],
                "blocks": [
                    para(
                        "覆盖点集从SQUARE81换到HEX37是一次结构扰动：测向次数均值由679.73降至337.10，路程由68250.75米降至46196.45米，T/K下降36.27%，全清证书仍为30/30。说明在当前离线误差模型下，证书点数减少没有破坏可检测性。"
                    ),
                    para(
                        "问题3对SAFE开关敏感：ABORT全清仅1/10，故不能为刷T/K关闭兜底。问题2对网格中心敏感：固定20至3000米极坐标网格已被删除，改以F1最小覆盖圆为局部中心，避免把搜索域写成与第一点示向无关的圆环。"
                    ),
                    para(
                        "示向度两位小数量化在实现中使用1.005度数值包络，物理误差常数仍为1度，参数表未改。该包络只吸收量化，不作为新的题设误差。"
                    ),
                ],
            },
            {
                "title": "模型局限",
                "roles": ["limitations"],
                "background_ids": [],
                "claim_ids": ["c-lim-official"],
                "blocks": [
                    para(
                        "正式测试未执行，表1成绩缺失。演练与离线几何不能代替正式三次测试，也不能把演练T/K写入正式平均定位清除时间。"
                    ),
                    para(
                        "HEX37未证明是最少点数，也未声称路径全局最优。七点发现集不是最少覆盖。GREEDY_FAST不含联合路线全局最优，也不含非凸失败域扣除。"
                    ),
                    para(
                        "Q4的no_signal不能推出距离大于1000米。光学兜底保证的是当前凸定位域可被20米球覆盖，若观测与模型矛盾则报告不一致，而不是把频道判空。"
                    ),
                ],
            },
            {
                "title": "结论",
                "roles": ["conclusion"],
                "background_ids": [],
                "claim_ids": ["c-conc"],
                "blocks": [
                    para(
                        "交会定位应输出可行集直径与状态，直径圆不能覆盖定位区域。第二检测点应按最坏剩余覆盖半径在第一点可行域附近选取。全向在线主线GREEDY_FAST在10局演练中全部清除，平均T/K为341秒。混合源采用HEX37证书网格与累计定位，离线30/30全清，演练PREFIX_A局T/K为822.38秒。"
                    ),
                    para(
                        "权衡上，保留SAFE以换全清，用更稀的三角晶格换行程，但不牺牲证书。实施上应继续只跑演练直至正式授权；提交前补齐表1与未改名日志。当前结论的边界是演练与离线几何，不是正式测试分布。"
                    ),
                ],
            },
        ],
    }

    out_ms = WS / "05-manuscript" / "manuscript.json"
    out_ms.parent.mkdir(parents=True, exist_ok=True)
    out_ms.write_text(json.dumps(manuscript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "paper-output" / "manuscript.json").write_text(
        json.dumps(manuscript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    hashes = {name: sha256(path) for name, path in files.items()}
    (WS / "04-evidence" / "source-hashes.json").parent.mkdir(parents=True, exist_ok=True)
    (WS / "04-evidence" / "source-hashes.json").write_text(
        json.dumps(hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"manuscript": str(out_ms), "hashes": hashes, "figures": [p.name for p in FIG_DIR.glob("*.png")]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

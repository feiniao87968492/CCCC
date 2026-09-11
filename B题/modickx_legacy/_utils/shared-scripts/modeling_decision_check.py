#!/usr/bin/env python3
"""Audit the decision chain in a Modex ``MODELING_REPORT.md``.

The check is intentionally structural.  It verifies that a report records the
reasoning artifacts needed by later code and review stages without attempting
to judge which mathematical model is universally best.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CHECK_LABELS = {
    "evidence_boundary": "证据与假设边界",
    "dependency_graph": "子问题依赖与误差传播",
    "candidate_a": "A 稳妥基线",
    "candidate_b": "B 竞赛方案",
    "candidate_c": "C 创新方案",
    "model_selection": "模型选型与复杂度预算",
    "validation_contract": "验证合同",
    "validation_internal": "内部正确性验证",
    "validation_empirical": "解释或样本外验证",
    "validation_comparative": "基线与消融验证",
    "validation_uncertainty": "不确定性与稳健性验证",
}


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def _candidate_labels(text: str) -> list[str]:
    labels: list[str] = []
    patterns = {
        "A": r"(?mi)^\s*(?:#{1,6}\s*)?(?:\|\s*)?A\s*[-—:]?\s*(?:稳妥|基线)",
        "B": r"(?mi)^\s*(?:#{1,6}\s*)?(?:\|\s*)?B\s*[-—:]?\s*(?:竞赛|高分|主方案)",
        "C": r"(?mi)^\s*(?:#{1,6}\s*)?(?:\|\s*)?C\s*[-—:]?\s*(?:创新|增强)",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text):
            labels.append(label)
    return labels


def _markdown_section(text: str, heading_terms: tuple[str, ...]) -> str:
    """Return the body of the first matching Markdown section."""

    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if not match or not _contains_any(match.group(2), heading_terms):
            continue
        level = len(match.group(1))
        body: list[str] = []
        for following in lines[index + 1 :]:
            next_heading = re.match(r"^\s*(#{1,6})\s+", following)
            if next_heading and len(next_heading.group(1)) <= level:
                break
            body.append(following)
        return "\n".join(body)
    return ""


def audit_modeling_decision(text: str) -> dict[str, Any]:
    """Return a deterministic, machine-readable modeling-decision audit."""

    candidates = _candidate_labels(text)
    evidence_boundary = _contains_any(
        text,
        ("证据与假设边界", "证据边界", "已知事实与假设", "evidence boundary"),
    ) and _contains_any(text, ("事实", "数据", "假设", "未知", "缺失"))
    dependency_graph = _contains_any(
        text, ("子问题依赖", "依赖与误差传播", "dependency graph", "依赖链")
    ) and _contains_any(text, ("输入", "输出", "传播", "依赖", "共享参数"))
    model_selection = _contains_any(
        text, ("模型选型与复杂度预算", "模型选择与复杂度", "选型理由")
    ) and _contains_any(text, ("选择", "拒绝", "优于", "因为", "理由"))
    validation_text = _markdown_section(
        text, ("验证合同", "验证计划", "validation contract")
    )
    validation_contract = bool(validation_text)

    validation = {
        "internal": _contains_any(
            validation_text,
            ("量纲", "守恒", "可行性", "边界", "收敛", "内部正确性"),
        ),
        "empirical": _contains_any(
            validation_text,
            (
                "样本外",
                "留出检验",
                "滚动验证",
                "滚动起点",
                "残差",
                "校准",
                "机理一致性",
                "交叉验证",
            ),
        ),
        "comparative": _contains_any(validation_text, ("基线", "baseline"))
        and _contains_any(validation_text, ("对比", "比较", "消融", "ablation")),
        "uncertainty": _contains_any(
            validation_text,
            (
                "不确定性",
                "灵敏度",
                "敏感性",
                "bootstrap",
                "扰动",
                "稳健性",
                "鲁棒性",
                "误差传播",
                "情景分析",
            ),
        ),
    }

    checks = {
        "evidence_boundary": evidence_boundary,
        "dependency_graph": dependency_graph,
        "candidate_a": "A" in candidates,
        "candidate_b": "B" in candidates,
        "candidate_c": "C" in candidates,
        "model_selection": model_selection,
        "validation_contract": validation_contract,
        "validation_internal": validation["internal"],
        "validation_empirical": validation["empirical"],
        "validation_comparative": validation["comparative"],
        "validation_uncertainty": validation["uncertainty"],
    }
    missing = [code for code, passed in checks.items() if not passed]
    return {
        "passed": not missing,
        "missing": missing,
        "candidate_labels": candidates,
        "validation_layers": [name for name, passed in validation.items() if passed],
        "checks": checks,
    }


def _human_report(result: dict[str, Any]) -> str:
    lines = [
        "[modeling_decision] 建模决策链审计",
        f"候选方案：{', '.join(result['candidate_labels']) or '无'}",
        f"验证层：{', '.join(result['validation_layers']) or '无'}",
    ]
    if result["passed"]:
        lines.append("✅ 建模决策链通过：证据、依赖、候选比较、选型和四层验证均已登记。")
        return "\n".join(lines)
    lines.append("❌ 建模决策链缺少以下必备项：")
    lines.extend(f"  - {code}: {CHECK_LABELS[code]}" for code in result["missing"])
    lines.append("修复 MODELING_REPORT.md 后重跑；禁止用模型名称堆叠代替候选比较和验证。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modeling", default="MODELING_REPORT.md")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    path = Path(args.modeling)
    if not path.is_file():
        result: dict[str, Any] = {
            "passed": False,
            "error": "modeling_report_not_found",
            "path": str(path),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else f"❌ 建模报告不存在：{path}")
        return 2

    result = audit_modeling_decision(path.read_text(encoding="utf-8", errors="replace"))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else _human_report(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

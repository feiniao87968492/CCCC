#!/usr/bin/env python3
"""Deterministic local checks for humanities Markdown and LaTeX drafts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEVERITY = {"info": 0, "warning": 1, "error": 2}
DEFAULT_REFERENCE_YEAR = 2026
RULE_CATALOG = {
    "R1-01": ("error", "模糊引用缺少可核验来源"),
    "R1-02": ("info", "存在待补充占位符"),
    "R1-03": ("error", "引用年份超过当前年份"),
    "R3-01": ("warning", "存在过度断言"),
    "T-01": ("warning", "术语或译名可能不一致"),
    "F-01": ("error", "存在空脚注"),
    "F-02": ("warning", "参考文献缺少文献类型标识"),
    "F-03": ("warning", "中文语境混用英文标点"),
    "F-04": ("warning", "标题编号体系混用"),
    "S-01": ("warning", "存在口语化表述"),
    "S-02": ("warning", "自称用法不统一"),
    "L-01": ("warning", "长段落缺少明确论证连接"),
    "L-02": ("warning", "连续段落机械使用并列连接词"),
    "L-03": ("warning", "引文后可能缺少分析"),
    "L-04": ("info", "章节开头可能缺少逻辑衔接"),
    "L-05": ("warning", "因果前提包含未论证价值判断"),
    "L-06": ("info", "长句叙述成分过多"),
    "L-07": ("warning", "总结句堆叠多个未展开概念"),
    "L-08": ("warning", "强度词附近缺少证据标记"),
    "ST-01": ("info", "缺少摘要、关键词或参考文献"),
    "ST-02": ("warning", "引言缺少明确论点句"),
}
TERM_VARIANTS = (
    ("数字化转型", "数位化转型"),
    ("机器学习", "机械学习"),
    ("人工智能", "人工智慧"),
    ("新媒体", "新媒介"),
)


def _issue(rule: str, line: int, excerpt: str, message: str | None = None) -> dict[str, object]:
    severity, default = RULE_CATALOG[rule]
    return {
        "rule": rule,
        "severity": severity,
        "line": line,
        "message": message or default,
        "excerpt": " ".join(excerpt.split())[:180],
    }


def _matches(lines: list[str], rule: str, pattern: str, flags: int = 0) -> list[dict[str, object]]:
    regex = re.compile(pattern, flags)
    return [_issue(rule, index, line) for index, line in enumerate(lines, 1) if regex.search(line)]


def _extract_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    headings: list[tuple[int, int, str]] = []
    latex_levels = {"chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4}
    for index, line in enumerate(lines, 1):
        markdown = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if markdown:
            headings.append((index, len(markdown.group(1)), markdown.group(2).strip()))
            continue
        latex = re.match(
            r"^\s*\\(chapter|section|subsection|subsubsection)\*?\{([^{}]+)\}", line
        )
        if latex:
            headings.append((index, latex_levels[latex.group(1)], latex.group(2).strip()))
    return headings


def review(
    text: str, *, current_year: int = DEFAULT_REFERENCE_YEAR
) -> list[dict[str, object]]:
    lines = text.splitlines()
    issues: list[dict[str, object]] = []
    issues += _matches(lines, "R1-01", r"有(?:学者|研究|文献)(?:指出|认为|表明|显示)")
    issues += _matches(lines, "R1-02", r"\[(?:待补充|待核实|TODO|TBD)\]", re.I)
    year_limit = current_year
    for index, line in enumerate(lines, 1):
        for year_text in re.findall(r"(?<!\d)(20\d{2})(?!\d)", line):
            if int(year_text) > year_limit:
                issues.append(_issue("R1-03", index, line, f"引用年份 {year_text} 超过 {year_limit}"))
    issues += _matches(lines, "R3-01", r"毫无疑问|众所周知|毋庸置疑|必然(?:导致|证明|说明)")
    issues += _matches(lines, "F-01", r"^\s*\[\^[^]]+\]:\s*$|\\footnote\{\s*\}\s*$")
    issues += _matches(lines, "S-01", r"我觉得|其实吧|挺(?:好|多|重要)|搞定|咱们|说白了")
    issues += _matches(lines, "L-05", r"由于.{0,40}(?:并非|不值得|不应当).{0,30}(?:因此|所以)")

    whole = "\n".join(lines)
    for left, right in TERM_VARIANTS:
        if left in whole and right in whole:
            index = next(i for i, line in enumerate(lines, 1) if right in line)
            issues.append(_issue("T-01", index, lines[index - 1], f"同时使用“{left}”和“{right}”"))

    extracted_headings = _extract_headings(lines)
    heading_systems: set[str] = set()
    for _, _, title in extracted_headings:
        if re.match(r"^\d+(?:\.\d+)*[\s、.]", title):
            heading_systems.add("arabic")
        elif re.match(r"^[一二三四五六七八九十百]+[、.]", title):
            heading_systems.add("chinese")
        elif re.match(r"^[（(]\d+[）)]", title):
            heading_systems.add("parenthesized")
    if len(heading_systems) > 1:
        issues.append(_issue("F-04", 1, ", ".join(sorted(heading_systems))))

    reference_heading_lines = {
        line_number
        for line_number, _, title in extracted_headings
        if title.strip().lower() in {"参考文献", "references", "bibliography"}
    }
    in_references = False
    for index, line in enumerate(lines, 1):
        if any(line_number == index for line_number, _, _ in extracted_headings):
            title = next(title for line_number, _, title in extracted_headings if line_number == index)
            in_references = index in reference_heading_lines
        if in_references and re.match(r"^\s*(?:\[\d+\]|\d+[.)]|\\bibitem\{[^}]+\})\s*", line):
            if not re.search(r"\[(?:J|M|D|C|R|N|S|P|Z|EB/OL)\]", line, re.I):
                issues.append(_issue("F-02", index, line))

    if re.search(r"(?:本文|本研究)", whole) and re.search(r"(?:我们|笔者)", whole):
        index = next((i for i, line in enumerate(lines, 1) if re.search(r"我们|笔者", line)), 1)
        issues.append(_issue("S-02", index, lines[index - 1]))

    for index, line in enumerate(lines, 1):
        cjk = len(re.findall(r"[\u3400-\u9fff]", line))
        if cjk >= 20 and re.search(r"[,;:]", line):
            issues.append(_issue("F-03", index, line))
        for sentence in re.split(r"[。！？!?]", line):
            if len(re.findall(r"[\u3400-\u9fff]", sentence)) >= 80:
                issues.append(_issue("L-06", index, sentence))
        if re.search(r"显然|极其|完全|绝对", line) and not re.search(r"\[\d+\]|\d+(?:\.\d+)?%", line):
            issues.append(_issue("L-08", index, line))
        sentences = [item for item in re.split(r"[。！？!?]", line) if item.strip()]
        if len(sentences) >= 3 and not re.search(r"因此|然而|由于|例如|表明|说明|意味着|由此", line):
            issues.append(_issue("L-01", index, line))
        if re.search(r"^(?:综上|总之|由此可见)", line) and len(re.findall(r"[、，]", line)) >= 3:
            issues.append(_issue("L-07", index, line))

    paragraphs: list[tuple[int, str]] = []
    buffer: list[str] = []
    buffer_line = 1
    for index, line in enumerate(lines + [""], 1):
        if line.strip():
            if not buffer:
                buffer_line = index
            buffer.append(line.strip())
        elif buffer:
            paragraphs.append((buffer_line, " ".join(buffer)))
            buffer = []
    parallel_run: list[tuple[int, str]] = []
    for paragraph in paragraphs:
        if re.match(r"^(?:首先|其次|再次|此外|同时)[，,]", paragraph[1]):
            parallel_run.append(paragraph)
            if len(parallel_run) == 3:
                issues.append(_issue("L-02", paragraph[0], paragraph[1]))
        else:
            parallel_run = []

    reference_heading_line = min(reference_heading_lines, default=len(lines) + 1)
    citation_pattern = r"(?:\[\d+\]|\\cite\w*(?:\[[^\]]*\])?\{[^}]+\})"
    for position, (line_number, paragraph) in enumerate(paragraphs[:-1]):
        if line_number >= reference_heading_line or not re.search(citation_pattern, paragraph):
            continue
        next_line, next_paragraph = paragraphs[position + 1]
        if not re.search(r"这|该|表明|说明|意味着|由此|可见|反映", next_paragraph):
            issues.append(_issue("L-03", next_line, next_paragraph))

    headings = [title for _, _, title in extracted_headings]
    heading_text = "\n".join(headings).lower()
    for label, patterns in (
        ("摘要", ("摘要", "abstract")),
        ("关键词", ("关键词", "关键字", "keywords")),
        ("参考文献", ("参考文献", "references", "bibliography")),
    ):
        if not any(pattern in whole.lower() for pattern in patterns):
            issues.append(_issue("ST-01", 1, label, f"缺少{label}"))
    intro_indices = [line for line, _, title in extracted_headings if re.search(r"引言|绪论|introduction", title, re.I)]
    if intro_indices and not re.search(r"本文(?:认为|提出|主张)|本研究(?:认为|提出)|核心论点", whole):
        issues.append(_issue("ST-02", 1, heading_text))

    for index, level, title in extracted_headings:
        if level < 2 or re.search(r"摘要|关键词|参考文献|references|bibliography", title, re.I):
            continue
        next_text = next((candidate.strip() for candidate in lines[index:] if candidate.strip()), "")
        if next_text and not re.search(r"^(?:承接|基于|在此基础上|进一步|上一|前述|本文)", next_text):
            issues.append(_issue("L-04", index, title))

    unique: dict[tuple[object, object, object], dict[str, object]] = {}
    for item in issues:
        unique[(item["rule"], item["line"], item["message"])] = item
    return sorted(unique.values(), key=lambda item: (int(item["line"]), str(item["rule"])))


def _safe_input(value: str, workspace: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = workspace / path
    unresolved = path.absolute()
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError("input escapes the workspace") from exc
    current = unresolved
    while current != workspace and current.parent != current:
        if current.exists() and current.is_symlink():
            raise ValueError("input cannot use symlinks")
        current = current.parent
    if not resolved.is_file():
        raise ValueError("input must be an existing file")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--severity", choices=tuple(SEVERITY), default="info")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--current-year", type=int, default=DEFAULT_REFERENCE_YEAR)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        source = _safe_input(args.input, Path.cwd().resolve())
        if not 1900 <= args.current_year <= 2100:
            raise ValueError("current-year must be between 1900 and 2100")
        issues = [
            item for item in review(
                source.read_text(encoding="utf-8"), current_year=args.current_year
            )
            if SEVERITY[str(item["severity"])] >= SEVERITY[args.severity]
        ]
        if args.format == "json":
            print(
                json.dumps(
                    {"rules_checked": len(RULE_CATALOG), "issues": issues},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif issues:
            for item in issues:
                print(
                    f"[{str(item['severity']).upper()}] {item['rule']} line {item['line']}: "
                    f"{item['message']} — {item['excerpt']}"
                )
        else:
            print(f"PASS: {len(RULE_CATALOG)} deterministic rules checked")
        return 1 if issues else 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"HUMANITIES_REVIEW_ERROR: {str(exc)[:500]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

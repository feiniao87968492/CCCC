#!/usr/bin/env python3
"""Audit competition LaTeX source for the frozen page-format contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


AUDIT_NAME = "LATEX_FORMAT_AUDIT.json"
SOURCE_SUFFIXES = {".tex", ".cls", ".sty"}
INCLUDE_PATTERN = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
CLASS_PATTERN = re.compile(r"\\documentclass(?:\[[^]]*\])?\s*\{([^}]+)\}")
PACKAGE_PATTERN = re.compile(r"\\usepackage(?:\[[^]]*\])?\s*\{([^}]+)\}")
FORCED_SECTION_PATTERN = re.compile(
    r"\\(?:newpage|clearpage)\s*(?:%[^\n]*\n\s*)*"
    r"\\(?P<level>section|subsection|subsubsection)\*?\s*\{(?P<title>[^}]*)\}",
    re.IGNORECASE,
)
SECTIONBREAK_DEFINITION_PATTERN = re.compile(
    r"\\(?:re)?newcommand\*?\s*\{?\\(?:section|subsection|subsubsection)break\}?"
    r"(?:\[[^]]*\])?\s*\{[^}]*\\(?:newpage|clearpage|pagebreak)[^}]*\}",
    re.IGNORECASE,
)
SECTION_REDEFINITION_BREAK_PATTERN = re.compile(
    r"\\renewcommand\*?\s*\{?\\(?:section|subsection|subsubsection)\}?"
    r"(?:\[[^]]*\])?\s*\{[^}]*\\(?:newpage|clearpage|pagebreak)",
    re.IGNORECASE,
)
PAGE_BREAK_EXEMPT_TITLE = re.compile(r"(?i)(?:附录|参考文献|appendix|references)")


class LatexFormatAuditError(ValueError):
    """Raised when source is missing or cannot be audited deterministically."""


@dataclass(frozen=True)
class FormatFinding:
    code: str
    location: str
    line: int | None = None

    def public(self) -> dict[str, object]:
        payload: dict[str, object] = {"code": self.code, "location": self.location}
        if self.line is not None:
            payload["line"] = self.line
        return payload


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise LatexFormatAuditError(f"cannot read LaTeX source as UTF-8: {path}") from exc


def _local_dependency(base: Path, value: str, suffix: str) -> Path:
    candidate = base / value
    if not candidate.suffix:
        candidate = candidate.with_suffix(suffix)
    return candidate.resolve()


def collect_latex_sources(main: Path) -> list[Path]:
    root = main.parent.resolve()
    pending = [main.resolve()]
    collected: dict[Path, None] = {}
    while pending:
        path = pending.pop()
        if path in collected:
            continue
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            raise LatexFormatAuditError(f"LaTeX dependency is missing: {path}")
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise LatexFormatAuditError(f"LaTeX dependency escapes project root: {path}") from exc
        collected[path] = None
        text = _read(path)
        for value in INCLUDE_PATTERN.findall(text):
            dependency = _local_dependency(path.parent, value.strip(), ".tex")
            if dependency.is_file():
                pending.append(dependency)
        if path == main.resolve():
            for value in CLASS_PATTERN.findall(text):
                dependency = _local_dependency(path.parent, value.strip(), ".cls")
                if dependency.is_file():
                    pending.append(dependency)
            for group in PACKAGE_PATTERN.findall(text):
                for value in group.split(","):
                    dependency = _local_dependency(path.parent, value.strip(), ".sty")
                    if dependency.is_file():
                        pending.append(dependency)
    return sorted(collected)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"(?m)%.*$", "", text)).casefold()


def _has_a4(text: str) -> bool:
    compact = _normalized(text)
    return "a4paper" in compact or "paperwidth=210mm" in compact


def _has_exact_margins(text: str) -> bool:
    compact = _normalized(text)
    if "margin=2.5cm" in compact or "margin=25mm" in compact:
        return True
    variants = ("2.5cm", "25mm")
    return all(
        any(f"{side}={value}" in compact for value in variants)
        for side in ("top", "bottom", "left", "right")
    )


def _has_small_four_body(text: str) -> bool:
    compact = _normalized(text)
    if "zihao=-4" in compact:
        return True
    if re.search(r"\\@setfontsize\\normalsize\{12(?:\.0[0-9]*)?\}", compact):
        return True
    if re.search(r"\\(?:documentclass|loadclass)\[[^]]*(?:12pt)[^]]*\]", compact):
        return True
    if re.search(r"\\begin\{document\}.{0,240}\\zihao\{-4\}", compact):
        return True
    if re.search(r"\\atbegindocument\{[^}]*\\zihao\{-4\}", compact):
        return True
    return bool(
        re.search(
            r"\\begin\{document\}.{0,240}\\fontsize\{12(?:\.0[0-9]*)?\}",
            compact,
        )
    )


def audit_latex(main: Path) -> tuple[list[FormatFinding], dict[str, object]]:
    sources = collect_latex_sources(main)
    root = main.parent.resolve()
    combined = "\n".join(_read(path) for path in sources)
    findings: list[FormatFinding] = []
    if not _has_a4(combined):
        findings.append(FormatFinding("a4_paper_not_verified", main.name))
    if not _has_exact_margins(combined):
        findings.append(FormatFinding("four_margins_2_5cm_not_verified", main.name))
    if not _has_small_four_body(combined):
        findings.append(FormatFinding("small_four_body_font_not_verified", main.name))

    for path in sources:
        text = _read(path)
        location = path.relative_to(root).as_posix()
        for pattern in (SECTIONBREAK_DEFINITION_PATTERN, SECTION_REDEFINITION_BREAK_PATTERN):
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    FormatFinding("template_forces_section_page_break", location, line)
                )
        for match in FORCED_SECTION_PATTERN.finditer(text):
            if PAGE_BREAK_EXEMPT_TITLE.search(match.group("title")):
                continue
            if (
                path.resolve() == main.resolve()
                and match.group("level").casefold() == "section"
                and "\\end{abstract}" in text[: match.start()]
                and not re.search(r"\\section\*?\s*\{", text[: match.start()])
            ):
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(FormatFinding("forced_page_break_before_section", location, line))

    evidence = {
        "format": "modickx-competition-latex-format-audit",
        "schema_version": 1,
        "status": "ready" if not findings else "blocked",
        "latex_main": main.name,
        "source_file_count": len(sources),
        "checks": {
            "a4_paper": "passed"
            if not any(item.code == "a4_paper_not_verified" for item in findings)
            else "failed",
            "body_font_small_four_12pt": "passed"
            if not any(item.code == "small_four_body_font_not_verified" for item in findings)
            else "failed",
            "margins_top_bottom_left_right_2_5cm": "passed"
            if not any(item.code == "four_margins_2_5cm_not_verified" for item in findings)
            else "failed",
            "sections_do_not_force_new_page": "passed"
            if not any(
                item.code
                in {"forced_page_break_before_section", "template_forces_section_page_break"}
                for item in findings
            )
            else "failed",
        },
        "findings": [item.public() for item in findings],
    }
    return findings, evidence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latex-main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        main_path = args.latex_main.resolve()
        output = args.output.resolve()
        findings, report = audit_latex(main_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if findings:
            raise LatexFormatAuditError(
                f"LaTeX format audit found {len(findings)} blocking item(s); see {output.name}"
            )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (LatexFormatAuditError, OSError) as exc:
        print(f"LaTeX format audit blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

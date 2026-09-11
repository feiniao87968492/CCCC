#!/usr/bin/env python3
"""Count Chinese characters and English words by Markdown heading."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ENGLISH_WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _metrics(text: str) -> dict[str, int]:
    chinese = len(CJK.findall(text))
    english = len(ENGLISH_WORD.findall(text))
    return {
        "chinese_chars": chinese,
        "english_words": english,
        "effective_words": chinese + english,
    }


def _clean_line(line: str) -> str:
    line = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", line)
    line = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", line)
    line = re.sub(r"[`*_~>|]", " ", line)
    return line


def analyze(text: str) -> dict[str, object]:
    chapters: list[dict[str, object]] = []
    all_text: list[str] = []
    current: dict[str, object] | None = None
    fenced = False
    for raw in text.splitlines():
        if raw.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = HEADING.match(raw.strip())
        if heading:
            title = _clean_line(heading.group(2)).strip()
            current = {
                "heading": title,
                "level": len(heading.group(1)),
                "_parts": [title],
            }
            chapters.append(current)
            all_text.append(title)
            continue
        cleaned = _clean_line(raw).strip()
        if not cleaned:
            continue
        all_text.append(cleaned)
        if current is not None:
            current["_parts"].append(cleaned)

    for chapter in chapters:
        chapter.update(_metrics("\n".join(chapter.pop("_parts"))))
    return {"total": _metrics("\n".join(all_text)), "chapters": chapters}


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
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        source = _safe_input(args.input, Path.cwd().resolve())
        payload = analyze(source.read_text(encoding="utf-8"))
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            total = payload["total"]
            print(
                f"总计: {total['effective_words']}（中文字符 {total['chinese_chars']}，"
                f"英文单词 {total['english_words']}）"
            )
            for chapter in payload["chapters"]:
                print(
                    f"{'  ' * (chapter['level'] - 1)}{chapter['heading']}: "
                    f"{chapter['effective_words']}"
                )
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"WORD_COUNT_ERROR: {str(exc)[:500]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

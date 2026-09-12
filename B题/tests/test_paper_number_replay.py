"""Replay frozen Q1-Q4 numbers against the shipped manuscript. No invented Table 1."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS_PATH = ROOT / "paper-workspace" / "05-manuscript" / "manuscript.json"
DEMO = ROOT / "data_preparation" / "output" / "q1_q2_demo.json"
Q3 = ROOT / "docs" / "Q3主线-GREEDY_FAST.md"
PAIRED = ROOT / "experiments" / "q4_hex37" / "paired_summary.json"
PRACTICE = ROOT / "experiments" / "q4_simulator" / "practice_results.md"


def _text(ms: dict) -> str:
    return json.dumps(ms, ensure_ascii=False)


def _tables(ms: dict) -> list[dict]:
    tables = []
    for section in ms["sections"]:
        for block in section.get("blocks", []):
            if block.get("type") == "table":
                tables.append(block)
    return tables


def test_manuscript_exists():
    assert MS_PATH.is_file(), f"missing manuscript {MS_PATH}"


def test_q1_diameter_circle_does_not_cover():
    demo = json.loads(DEMO.read_text(encoding="utf-8"))
    assert demo["q1_equilateral"]["diameter_circle_covers"] is False
    ms = json.loads(MS_PATH.read_text(encoding="utf-8"))
    text = _text(ms)
    assert "不能覆盖" in text
    tab = next(t for t in _tables(ms) if t.get("label") == "tab-q1-demo")
    assert any(cell == "否" for row in tab["rows"] for cell in row)


def test_q3_greedy_fast_practice_341_10_of_10():
    q3 = Q3.read_text(encoding="utf-8")
    assert "| **GREEDY_FAST** | **10/10** | **341** |" in q3
    ms = json.loads(MS_PATH.read_text(encoding="utf-8"))
    text = _text(ms)
    assert "341" in text
    assert "10/10" in text
    tab = next(t for t in _tables(ms) if t.get("label") == "tab-q3-practice")
    row = next(r for r in tab["rows"] if r[0] == "GREEDY_FAST")
    assert row[1] == "10/10"
    assert row[2] == "341"


def test_q4_hex37_offline_30_30_and_named_practice_tk():
    paired = json.loads(PAIRED.read_text(encoding="utf-8"))
    assert paired["hex37_all_cleared"] == 30
    assert paired["hex37_all_certified"] == 30
    assert abs(paired["T_over_K"]["hex37_mean"] - 836.9129462514154) < 1e-9
    practice = PRACTICE.read_text(encoding="utf-8")
    assert "822.38" in practice
    assert "`20260911-231856-q4-p4`" in practice
    ms = json.loads(MS_PATH.read_text(encoding="utf-8"))
    text = _text(ms)
    assert "30/30" in text
    assert "836.91" in text
    assert "822.38" in text
    tab = next(t for t in _tables(ms) if t.get("label") == "tab-q4-practice")
    assert any(row[3] == "822.38" for row in tab["rows"])


def test_table1_has_no_invented_official_results():
    ms = json.loads(MS_PATH.read_text(encoding="utf-8"))
    tab = next(t for t in _tables(ms) if t.get("label") == "tab-formal-missing")
    joined = " ".join(cell for row in tab["rows"] for cell in row)
    assert "无正式日志" in joined
    assert not re.search(r"\b\d{4,6}\.\d{2}\b", joined), joined
    assert not re.search(r"[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}", joined)
    for row in tab["rows"]:
        for cell in row[1:]:
            assert cell == "无正式日志"


def test_q1_q4_section_presence():
    ms = json.loads(MS_PATH.read_text(encoding="utf-8"))
    text = _text(ms)
    for token in ("问题1", "问题2", "问题3", "问题4"):
        assert token in text
    assert str(ms.get("abstract", "")).strip()
    assert "GREEDY_FAST" in text
    assert "HEX37" in text

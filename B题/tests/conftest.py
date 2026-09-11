"""Pytest isolation: Q3 runners refuse q2_validation if it is already imported."""
from __future__ import annotations

import sys

_ORACLE = ("q2_validation", "q2_scenario")


def pytest_runtest_setup(item) -> None:
    path = str(getattr(item, "fspath", "") or item.path)
    if "test_q3" in path or "q3_" in path.replace("\\", "/") or "test_q4" in path or "q4_" in path.replace("\\", "/"):
        for name in _ORACLE:
            sys.modules.pop(name, None)
    if "test_q4" in path or "q4_" in path.replace("\\", "/"):
        src = str(__import__("pathlib").Path(path).resolve().parents[1] / "src")
        if src not in sys.path:
            sys.path.insert(0, src)
        try:
            from q4_cover import COVER_SQUARE81, set_cover_mode
            from q4_policy import ROUTE_OLD, set_route_mode
        except ImportError:
            return
        set_cover_mode(COVER_SQUARE81)
        set_route_mode(ROUTE_OLD)

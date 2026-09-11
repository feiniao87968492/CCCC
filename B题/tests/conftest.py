"""Pytest isolation: Q3 runners refuse q2_validation if it is already imported."""
from __future__ import annotations

import sys

_ORACLE = ("q2_validation", "q2_scenario")


def pytest_runtest_setup(item) -> None:
    path = str(getattr(item, "fspath", "") or item.path)
    if "test_q3" in path or "q3_" in path.replace("\\", "/") or "test_q4" in path or "q4_" in path.replace("\\", "/"):
        for name in _ORACLE:
            sys.modules.pop(name, None)

"""Launch Q3 PRACTICE only. Aborts if the UI is not a problem-3 practice session."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from robot_client import RobotClient
from q3_runner import Q3Runner, _assert_no_oracle


def _ps(action: str, problem: int, team: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(HERE / "ui.ps1"),
            "-Action",
            action,
            "-Problem",
            str(problem),
            "-Team",
            team,
        ],
        capture_output=True,
        timeout=180,
    )


def _decode(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    if "演练" not in text and "正式" not in text:
        text = raw.decode("gb18030", errors="replace")
    return text


def assert_practice_ready(team: str, problem: int = 3) -> str:
    inspect = _ps("Inspect", problem, team)
    text = _decode(inspect.stdout)
    title = f"问题{problem} 演练 测试"
    if inspect.returncode:
        raise RuntimeError("Inspect failed; no API sent.")
    if f"ControlType.Text|test-run-title|{title}" not in text:
        raise RuntimeError(f"Not a practice session ({title} missing). No API sent.\n{text[-800:]}")
    if "问题3 正式" in text or "正式 测试" in text and "演练" not in text:
        raise RuntimeError("Formal test UI detected. Aborting without API.")
    if "ControlType.Text||等待机器狗进入" not in text:
        raise RuntimeError("Practice UI is not waiting for enter. No API sent.")
    if f"ControlType.Text||队号 {team}" not in text:
        raise RuntimeError("Team mismatch. No API sent.")
    return text


def start_practice(team: str, problem: int = 3) -> None:
    login = _ps("Login", problem, team)
    if login.returncode:
        raise RuntimeError(_decode(login.stderr) or _decode(login.stdout) or "Login failed")
    start = _ps("StartPractice", problem, team)
    if start.returncode:
        raise RuntimeError(_decode(start.stderr) or _decode(start.stdout) or "StartPractice failed")


def parse_n_from_ui(text: str) -> int | None:
    import re

    for pat in (r"干扰源总数[^\d]*(\d+)", r"总数[^\d]*(\d+)", r"全向[^\d]*(\d+)"):
        m = re.search(pat, text)
        if m:
            val = int(m.group(1))
            if 10 <= val <= 16:
                return val
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Q3 official PRACTICE runner; never starts formal.")
    parser.add_argument("--strategy", default="JSO", choices=("SAFE", "FAST", "HYBRID", "ROBUST", "GREEDY", "GREEDY_FAST", "GREEDY_ABORT", "JSO"))
    parser.add_argument("--source-budget-s", type=float, default=0,
                        help="GREEDY_FAST only: per-source virtual time cap; 0 retains full fallback")
    parser.add_argument("--team", default="202611102016")
    parser.add_argument("--port", type=int, default=2026)
    parser.add_argument("--skip-ui-start", action="store_true")
    args = parser.parse_args()
    import math
    if not math.isfinite(args.source_budget_s) or args.source_budget_s < 0:
        parser.error("source budget must be finite and nonnegative")
    if args.source_budget_s and args.strategy != "GREEDY_FAST":
        parser.error("source budget requires GREEDY_FAST")
    _assert_no_oracle()
    if not args.skip_ui_start:
        start_practice(args.team, 3)
    ui_before = assert_practice_ready(args.team, 3)
    out = HERE / "evidence" / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-q3-{args.strategy.lower()}")
    out.mkdir(parents=True, exist_ok=False)
    (out / "ui-before.txt").write_text(ui_before, encoding="utf-8")
    client = RobotClient(args.team, args.port, out / "requests.jsonl")
    if args.strategy == "JSO":
        sys.path.insert(0, str(ROOT / "experiments" / "q3_ablation"))
        from policies import make_runner
        runner = make_runner(client, "JSO")
    elif args.strategy == "GREEDY_FAST":
        from q3_fast_mode import GreedyFastRunner
        runner = GreedyFastRunner(client, source_budget_s=args.source_budget_s)
    elif args.strategy == "GREEDY_ABORT":
        from q3_abort_safe import GreedyAbortRunner
        runner = GreedyAbortRunner(client)
    else:
        runner = Q3Runner(client, strategy=args.strategy)
    summary = runner.run()
    after = _ps("Inspect", 3, args.team)
    ui_after = _decode(after.stdout)
    (out / "ui-after.txt").write_text(ui_after, encoding="utf-8")
    N = parse_n_from_ui(ui_after)
    summary["N"] = N
    summary["K_over_N"] = (summary["K"] / N) if N else None
    summary["mode"] = "practice"
    summary["problem"] = 3
    summary["evidence"] = str(out)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "events.json").write_text(json.dumps(runner.log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("evidence", out)


if __name__ == "__main__":
    main()

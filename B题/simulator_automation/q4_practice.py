"""Launch Q4 PRACTICE only. Never starts problem-4 formal."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from q4_runner import Q4Runner, _assert_no_oracle
from robot_client import RobotClient


def _ps(action: str, team: str) -> subprocess.CompletedProcess:
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
            "4",
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


def assert_q4_practice_ready(team: str) -> str:
    inspect = _ps("Inspect", team)
    text = _decode(inspect.stdout)
    if inspect.returncode:
        raise RuntimeError("Inspect failed; no API sent.")
    if "ControlType.Text|test-run-title|问题4 演练 测试" not in text:
        raise RuntimeError("Not a problem-4 practice session. No API sent.\n" + text[-800:])
    if "问题4正式" in text.replace(" ", "") and "演练" not in text:
        raise RuntimeError("Formal test UI detected. Aborting without API.")
    if "ControlType.Text||等待机器狗进入" not in text:
        raise RuntimeError("Practice UI is not waiting for enter. No API sent.")
    if f"ControlType.Text||队号 {team}" not in text:
        raise RuntimeError("Team mismatch. No API sent.")
    return text


def start_q4_practice(team: str) -> None:
    login = _ps("Login", team)
    if login.returncode:
        raise RuntimeError(_decode(login.stderr) or _decode(login.stdout) or "Login failed")
    start = _ps("StartPractice", team)
    if start.returncode:
        raise RuntimeError(_decode(start.stderr) or _decode(start.stdout) or "StartPractice failed")


def parse_n_from_ui(text: str) -> tuple[int | None, int | None, int | None]:
    # Completion counts also appear as separate UIA Text nodes on the result card.
    text_nodes = re.findall(r"^ControlType\.Text\|[^|]*\|(.*)$", text, re.MULTILINE)
    normalized = " ".join(text_nodes)
    m = re.search(r"本次演练测试干扰源数量\s*共\s*(\d+)\s*个[，,]\s*全向\s*(\d+)\s*个[，,]\s*定向\s*(\d+)\s*个", normalized)
    if m:
        n, omni, directional = map(int, m.groups())
        if 10 <= n <= 16 and omni + directional == n:
            return n, omni, directional
    m = re.search(r"本次案例含干扰源\s*(\d+)\s*个，其中全向\s*(\d+)\s*个[、，,]\s*定向\s*(\d+)\s*个", text)
    if m:
        n, omni, directional = map(int, m.groups())
        if 10 <= n <= 16 and omni + directional == n:
            return n, omni, directional
    m = re.search(r"共(\d+)（全向(\d+)，定向(\d+)）", text)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    m = re.search(r"干扰源总数[^\d]*(\d+)", text)
    if m:
        val = int(m.group(1))
        if 10 <= val <= 16:
            return val, None, None
    return None, None, None


def main() -> None:
    parser = argparse.ArgumentParser(description="Q4 official PRACTICE runner; never starts formal.")
    parser.add_argument("--team", default="202611102016")
    parser.add_argument("--port", type=int, default=2026)
    parser.add_argument("--skip-ui-start", action="store_true")
    parser.add_argument("--cover-mode", default="HEX37", help="SQUARE81 or HEX37; practice challenger default is HEX37")
    parser.add_argument("--route-mode", default="ROUTE_INSERT_V3", help="OLD_HEX37, V1, V2, or V3")
    parser.add_argument("--hex37-route", default="PREFIX_A", help="CURRENT, PREFIX_A, or PREFIX_B")
    args = parser.parse_args()
    _assert_no_oracle()
    if args.cover_mode:
        from q4_cover import set_cover_mode
        set_cover_mode(args.cover_mode)
    if args.route_mode:
        from q4_policy import set_route_mode
        set_route_mode(args.route_mode)
    if args.hex37_route:
        from q4_cover import set_hex37_route
        set_hex37_route(args.hex37_route)
    if not args.skip_ui_start:
        start_q4_practice(args.team)
    ui_before = assert_q4_practice_ready(args.team)
    out = HERE / "evidence" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-q4-p4")
    out.mkdir(parents=True, exist_ok=False)
    (out / "ui-before.txt").write_text(ui_before, encoding="utf-8")
    client = RobotClient(args.team, args.port, out / "requests.jsonl")
    runner = Q4Runner(client)
    summary = runner.run()
    after = _ps("Inspect", args.team)
    ui_after = _decode(after.stdout)
    (out / "ui-after.txt").write_text(ui_after, encoding="utf-8")
    N, n_omni, n_dir = parse_n_from_ui(ui_after)
    summary["N"] = N
    summary["n_omni"] = n_omni
    summary["n_dir"] = n_dir
    summary["K_over_N"] = (summary["K"] / N) if N else None
    summary["mode"] = "practice"
    summary["problem"] = 4
    if args.cover_mode:
        summary["cover_mode"] = args.cover_mode
    summary["evidence"] = str(out)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "events.json").write_text(json.dumps(runner.log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("evidence", out)


if __name__ == "__main__":
    main()

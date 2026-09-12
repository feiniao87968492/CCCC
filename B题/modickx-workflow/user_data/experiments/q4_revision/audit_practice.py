"""Read-only audit of practice evidence; never rewrites original run summaries."""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "simulator_automation")]
from q4_practice import parse_n_from_ui


def main():
    rows = []
    for directory in sorted((ROOT / "simulator_automation/evidence").glob("*-q4-p4")):
        summary_path = directory / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        text = (directory / "ui-after.txt").read_text(encoding="utf-8")
        n, omni, directional = parse_n_from_ui(text)
        code = re.search(r"ControlType\.Text\|\|([A-Z0-9]{4}(?:-[A-Z0-9]{4}){3})", text)
        row = dict(evidence=directory.name, revision=summary.get("revision", "historical"),
                   case_code=code.group(1) if code else None,
                   N=n, n_omni=omni, n_directional=directional, K=summary["K"],
                   K_over_N=summary["K"] / n if n else None,
                   T=summary["T"], T_over_K=summary["T_over_K"], wall_s=summary["wall_s"],
                   move_m=summary["move_m"], n_measure=summary["n_measure"], n_clear=summary["n_clear"],
                   all_certified=summary["all_certified"], failure=summary["failure"],
                   pending=";".join(map(str, summary["pending"])),
                   count_source="post-exit ui-after.txt" if n else "not available")
        rows.append(row)
    output = Path(__file__).with_name("official_practice.csv")
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(json.dumps(row, ensure_ascii=True))


if __name__ == "__main__":
    main()

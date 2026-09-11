"""Run stratified Q2 seed study. Writes CSV+JSON; does not claim contest probability."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from q2_metrics import evaluate_case, summarize
from q2_scenario import iter_set

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_preparation" / "output"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", dest="which", choices=("dev", "holdout"), default="dev")
    parser.add_argument("--n-azimuth", type=int, default=8)
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--legacy", action="store_true")
    parser.add_argument("--jitter", action="store_true")
    parser.add_argument("--max-cases", type=int, default=0)
    args = parser.parse_args()

    cases = iter_set(args.which)
    if args.max_cases:
        cases = cases[: args.max_cases]
    rows = []
    for i, sc in enumerate(cases):
        row = evaluate_case(
            sc,
            n_azimuth=args.n_azimuth,
            refine=args.refine,
            with_legacy=args.legacy,
            with_ref=True,
            jitter=args.jitter,
        )
        rows.append(row)
        print(f"{i+1}/{len(cases)} seed={sc.seed} {sc.stratum} J={row['J_star']:.3f} y2={row['y2']} fail={row['flags']}", flush=True)

    summary = summarize(rows)
    summary["set"] = args.which
    summary["n_azimuth"] = args.n_azimuth
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"q2_seed_metrics_{args.which}.csv"
    json_path = OUT / f"q2_seed_metrics_{args.which}.summary.json"
    fields = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("level1_ok", summary["level1_ok"], "failed_seeds", summary["level1"]["failed_seeds"])
    print("wrote", csv_path)
    print("wrote", json_path)


if __name__ == "__main__":
    main()

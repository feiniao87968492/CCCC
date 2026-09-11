"""Reproducible offline paired Q4 evaluation; never connects to a simulator."""
import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "simulator_automation"), str(ROOT / "tests")]
from test_q4_regressions import NoisyGeomSim, random_sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, default=ROOT / "simulator_automation/q4_runner.py")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=30)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--error-mode", choices=["smooth", "endpoint"], default="smooth")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("evaluated_q4_runner", args.runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for seed in range(args.seed_start, args.seed_start + args.cases):
        sources = random_sources(seed)
        sim = NoisyGeomSim(sources, seed, args.error_mode)
        runner = module.Q4Runner(sim)
        result = runner.run()
        row = {key: result[key] for key in ("K", "T", "T_over_K", "move_m", "n_measure", "n_clear", "all_certified", "failure", "wall_s")}
        row.update(seed=seed, N=len(sources), error_mode=args.error_mode)
        rows.append(row)
        print(json.dumps(row), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(cases=len(rows), all_cleared=sum(r["K"] == r["N"] for r in rows),
                   all_certified=sum(r["all_certified"] for r in rows),
                   mean_T=float(np.mean([r["T"] for r in rows])),
                   mean_T_over_K=float(np.mean([r["T_over_K"] for r in rows if r["T_over_K"] is not None])),
                   mean_move_m=float(np.mean([r["move_m"] for r in rows])),
                   max_wall_s=max(r["wall_s"] for r in rows),
                   source="offline geometry with bounded deterministic error; not official practice")
    args.output.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

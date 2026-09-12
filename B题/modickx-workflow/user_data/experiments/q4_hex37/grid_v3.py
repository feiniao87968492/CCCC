"""Small V3 parameter grid on seeds 0-9."""
from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "simulator_automation"), str(ROOT / "tests")]

from q4_cover import COVER_HEX37, set_cover_mode  # noqa: E402
from q4_policy import ROUTE_INSERT_V3, set_route_mode, set_v3_params  # noqa: E402
from q4_runner import Q4Runner  # noqa: E402
from test_q4_regressions import NoisyGeomSim, random_sources  # noqa: E402

CLEAR = (400.0, 600.0, 800.0)
MEASURE = (150.0, 250.0)
AGG = (80.0, 100.0, 120.0)
SEEDS = list(range(10))


def mean(rows, key):
    vals = [row[key] for row in rows if row.get(key) is not None]
    return float(np.mean(vals)) if vals else None


def eval_cfg(clear_m, measure_m, agg_rho):
    set_cover_mode(COVER_HEX37)
    set_route_mode(ROUTE_INSERT_V3)
    set_v3_params(clear_insert_max=clear_m, measure_insert_max=measure_m, aggressive_clear_rho=agg_rho)
    rows = []
    ok = 0
    cert = 0
    for seed in SEEDS:
        sources = random_sources(seed)
        r = Q4Runner(NoisyGeomSim(sources, seed, "smooth")).run()
        rows.append(r)
        if r.get("K") == len(sources) and r.get("failure") is None:
            ok += 1
        if r.get("all_certified") and r.get("failure") is None:
            cert += 1
    return {
        "clear_insert_max": clear_m,
        "measure_insert_max": measure_m,
        "aggressive_clear_rho": agg_rho,
        "all_cleared": ok,
        "all_certified": cert,
        "mean_T_over_K": mean(rows, "T_over_K"),
        "mean_T": mean(rows, "T"),
        "mean_move_m": mean(rows, "move_m"),
        "mean_n_measure": mean(rows, "n_measure"),
        "mean_n_clear": mean(rows, "n_clear"),
        "mean_n_probe": mean(rows, "n_probe"),
        "mean_n_aggressive_clear": mean(rows, "n_aggressive_clear"),
        "mean_n_aggressive_clear_ok": mean(rows, "n_aggressive_clear_ok"),
        "cases": len(SEEDS),
    }


def main():
    results = []
    for clear_m, measure_m, agg_rho in product(CLEAR, MEASURE, AGG):
        row = eval_cfg(clear_m, measure_m, agg_rho)
        results.append(row)
        print(json.dumps(row), flush=True)
    ranked = sorted(
        [r for r in results if r["all_cleared"] == 10 and r["all_certified"] == 10],
        key=lambda r: (r["mean_T_over_K"], r["mean_T"]),
    )
    payload = {"all": results, "feasible_ranked": ranked, "top2": ranked[:2]}
    out = Path(__file__).with_name("grid_v3.json")
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "feasible": len(ranked), "top2": ranked[:2]}, indent=2))


if __name__ == "__main__":
    main()

"""Reproducible offline paired Q4 evaluation; never connects to a simulator."""
import argparse
import csv
import hashlib
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
    parser.add_argument("--cover-mode", default=None, help="SQUARE81 or HEX37; default is the runner's current mode")
    parser.add_argument("--route-mode", default=None, help="OLD_HEX37, ROUTE_INSERT_V1, V2, or V3")
    parser.add_argument("--v3-clear-insert", type=float, default=None)
    parser.add_argument("--v3-measure-insert", type=float, default=None)
    parser.add_argument("--v3-agg-rho", type=float, default=None)
    parser.add_argument("--hex37-route", default=None, help="CURRENT or a registered HEX37 prefix route")
    args = parser.parse_args()
    if args.cover_mode:
        from q4_cover import set_cover_mode
        set_cover_mode(args.cover_mode)
    if args.route_mode:
        from q4_policy import set_route_mode
        set_route_mode(args.route_mode)
    if any(v is not None for v in (args.v3_clear_insert, args.v3_measure_insert, args.v3_agg_rho)):
        from q4_policy import set_v3_params
        kw = {}
        if args.v3_clear_insert is not None:
            kw["clear_insert_max"] = args.v3_clear_insert
        if args.v3_measure_insert is not None:
            kw["measure_insert_max"] = args.v3_measure_insert
        if args.v3_agg_rho is not None:
            kw["aggressive_clear_rho"] = args.v3_agg_rho
        set_v3_params(**kw)
    if args.hex37_route:
        from q4_cover import set_hex37_route
        set_hex37_route(args.hex37_route)
    if (args.runner.parent / "q4_localize.py").exists():
        # A snapshot runner must use its own localization, state and policy.
        for name in ("q4_localize", "q4_state", "q4_policy"):
            dependency = args.runner.parent / (name + ".py")
            dep_spec = importlib.util.spec_from_file_location(name, dependency)
            dep_module = importlib.util.module_from_spec(dep_spec)
            sys.modules[name] = dep_module
            dep_spec.loader.exec_module(dep_module)
    spec = importlib.util.spec_from_file_location("evaluated_q4_runner", args.runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for seed in range(args.seed_start, args.seed_start + args.cases):
        sources = random_sources(seed)
        sim = NoisyGeomSim(sources, seed, args.error_mode)
        runner = module.Q4Runner(sim)
        result = runner.run()
        keys = ("K", "T", "T_over_K", "move_m", "localization_move", "n_measure", "n_clear", "n_clear_ok",
                "all_certified", "failure", "wall_s", "cover_mode", "route_mode",
                "n_optical_fallback", "n_cover_visited", "n_insert", "n_defer", "pending_max",
                "n_batch", "n_probe", "n_aggressive_clear", "n_aggressive_clear_ok",
                "hex37_route", "mean_first_detect_index", "p95_first_detect_index")
        row = {key: result.get(key) for key in keys}
        row.update(seed=seed, N=len(sources), error_mode=args.error_mode)
        rows.append(row)
        print(json.dumps(row), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    def _mean(key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return float(np.mean(vals)) if vals else None

    summary = dict(cases=len(rows), cover_mode=args.cover_mode, route_mode=args.route_mode,
                   all_cleared=sum(r["K"] == r["N"] for r in rows),
                   all_certified=sum(bool(r["all_certified"]) for r in rows),
                   mean_T=_mean("T"),
                   mean_T_over_K=_mean("T_over_K"),
                   mean_move_m=_mean("move_m"),
                   mean_localization_move=_mean("localization_move"),
                   mean_n_measure=_mean("n_measure"),
                   mean_n_clear=_mean("n_clear"),
                   mean_n_optical_fallback=_mean("n_optical_fallback"),
                   mean_n_cover_visited=_mean("n_cover_visited"),
                   mean_n_insert=_mean("n_insert"),
                   mean_n_defer=_mean("n_defer"),
                   mean_pending_max=_mean("pending_max"),
                   mean_n_batch=_mean("n_batch"),
                   mean_n_probe=_mean("n_probe"),
                   mean_n_aggressive_clear=_mean("n_aggressive_clear"),
                   mean_n_aggressive_clear_ok=_mean("n_aggressive_clear_ok"),
                   mean_first_detect_index=_mean("mean_first_detect_index"),
                   mean_p95_first_detect_index=_mean("p95_first_detect_index"),
                   hex37_route=args.hex37_route,
                   max_wall_s=max(r["wall_s"] for r in rows),
                   source="offline geometry with bounded deterministic error; not official practice")
    args.output.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    inputs = [args.runner, ROOT / "tests/test_q4_regressions.py", ROOT / "tests/test_q4_geomsim.py",
              ROOT / "src/geometry.py", ROOT / "src/params.py", ROOT / "src/q4_cover.py",
              ROOT / "data_preparation/parameters.csv"]
    inputs += [Path(sys.modules[name].__file__) for name in ("q4_localize", "q4_state", "q4_policy")]
    manifest = dict(runner=str(args.runner), seed_start=args.seed_start, cases=args.cases,
                    error_mode=args.error_mode, cover_mode=args.cover_mode,
                    route_mode=args.route_mode, python=sys.version,
                    sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    args.output.with_suffix(".meta.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

"""Paired offline Q4 efficiency audit. Never connects to the official simulator."""
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
from q4_cover import set_cover_mode, set_hex37_route
from test_q4_regressions import NoisyGeomSim, random_sources


def event_metrics(events):
    out = dict(discovery_measure=0, discovery_no_signal=0, refine_measure=0,
               refine_no_signal=0, measure_s=0., clear_s=0., movement_s=0.)
    seen = set()
    pos = np.zeros(2)
    previous_t = last_clear = 0.
    for e in events:
        if e["op"] not in ("measure", "clear"):
            continue
        p = np.array([e["x"], e["y"]])
        move_s = float(np.linalg.norm(p - pos)) / 5
        out["movement_s"] += move_s
        out[e["op"] + "_s"] += e["t"] - previous_t - move_s
        if e["op"] == "measure":
            stage = "refine" if e["k"] in seen else "discovery"
            out[stage + "_measure"] += 1
            if e["result"] == "no_signal":
                out[stage + "_no_signal"] += 1
            else:
                seen.add(e["k"])
        elif e["ok"]:
            last_clear = e["t"]
        pos, previous_t = p, e["t"]
    out["after_last_clear_s"] = previous_t - last_clear
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=30)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--cover", default="HEX37")
    parser.add_argument("--route", default="ROUTE_INSERT_V3")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--error-mode", choices=["smooth", "endpoint"], default="smooth")
    parser.add_argument("--sources", choices=["mixed", "directional", "omni", "boundary"], default="mixed")
    args = parser.parse_args()
    files = []
    if args.snapshot:
        for name in ("q4_localize", "q4_state", "q4_policy", "q4_runner"):
            path = Path(__file__).parent / "baseline" / (name + ".py")
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            files.append(path)
    else:
        files.extend(ROOT / "src" / f"{name}.py" for name in
                     ("q4_localize", "q4_state", "q4_policy", "q4_adaptive"))
        files.append(ROOT / "simulator_automation/q4_runner.py")
    from q4_policy import set_route_mode
    from q4_runner import Q4Runner
    set_cover_mode(args.cover)
    set_hex37_route("PREFIX_A")
    set_route_mode(args.route)
    files.extend([Path(__file__), ROOT / "src/q4_cover.py", ROOT / "src/q4_certificate.py",
                  ROOT / "src/geometry.py", ROOT / "src/params.py", ROOT / "data_preparation/parameters.csv",
                  ROOT / "tests/test_q4_regressions.py", ROOT / "tests/test_q4_geomsim.py"])
    # Capture at start: an unrelated edit while a long benchmark runs must not
    # attribute its results to code that wasn't loaded by this process.
    manifest = dict(arguments={k: str(v) for k, v in vars(args).items()}, python=sys.version,
                    sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in files if p.exists()},
                    source="offline bounded-error geometry; not official practice")
    rows = []
    for seed in range(args.seed_start, args.seed_start + args.cases):
        sources = random_sources(seed)
        for source in sources:
            if args.sources != "mixed":
                source["directional"] = args.sources != "omni"
            if args.sources == "boundary":
                source["g"] *= 1800 / np.linalg.norm(source["g"])
                source["r"] = 1000.
                source["psi"] = float(np.arctan2(source["g"][1], source["g"][0]))
        runner = Q4Runner(NoisyGeomSim(sources, seed, args.error_mode))
        result = runner.run()
        keys = ("K", "T", "T_over_K", "move_m", "localization_move", "n_measure", "n_clear",
                "n_optical_fallback", "n_cover_visited", "all_certified", "failure", "wall_s")
        row = dict(seed=seed, N=len(sources), **{k: result.get(k) for k in keys},
                   **event_metrics(runner.log))
        rows.append(row)
        if result["failure"] or result["K"] != len(sources):
            print(json.dumps(row), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(cases=len(rows), cover=args.cover, route=args.route, snapshot=args.snapshot,
                   error_mode=args.error_mode, sources=args.sources,
                   full_success=sum(r["K"] == r["N"] and r["all_certified"] and not r["failure"] for r in rows),
                   failed_seeds=[r["seed"] for r in rows if r["K"] != r["N"] or not r["all_certified"] or r["failure"]])
    for key in rows[0]:
        if key not in ("failure", "all_certified", "seed"):
            summary["mean_" + key] = float(np.mean([r[key] for r in rows]))
    summary["p95_T_over_K"] = float(np.quantile([r["T_over_K"] for r in rows], .95))
    summary["max_wall_s"] = max(r["wall_s"] for r in rows)
    args.output.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".meta.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

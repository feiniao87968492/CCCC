"""Reproducible paired offline Q3 experiment; never calls an HTTP endpoint."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_name] = "1"
import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from environment import Q3Environment
from policies import VARIANTS, make_runner

FAMILIES = ("uniform", "boundary", "clustered", "spokes")
MODES = ("smooth", "spatial", "endpoint")


def scene_sources(seed, n, family):
    rng = np.random.default_rng(seed)
    channels = rng.choice(np.arange(1, 21), size=n, replace=False)
    theta = rng.uniform(0, 2*np.pi, n)
    radius = 1800*np.sqrt(rng.random(n))
    positions = radius[:, None] * np.c_[np.cos(theta), np.sin(theta)]
    reception = rng.uniform(1000, 1500, n)
    if family == "boundary":
        positions = 1800*np.c_[np.cos(theta), np.sin(theta)]
        reception[:] = 1000
    elif family == "clustered":
        centers = rng.uniform(-950, 950, (3, 2))
        positions = centers[rng.integers(0, 3, n)] + rng.normal(0, 150, (n, 2))
        norm = np.linalg.norm(positions, axis=1)
        positions *= np.minimum(1, 1799 / np.maximum(norm, 1))[:, None]
    elif family == "spokes":
        theta = (np.arange(n)%6)*np.pi/3 + rng.uniform(-.01, .01, n)
        radius = rng.uniform(200, 1800, n)
        positions = radius[:, None]*np.c_[np.cos(theta), np.sin(theta)]
        reception[:] = 1000
    return [{"k": int(k), "g": p.tolist(), "r": float(r)}
            for k, p, r in zip(channels, positions, reception)]


def scenes(split, repetitions):
    result = []
    base = 200000 if split == "evaluation" else 100000
    families = FAMILIES if split == "evaluation" else ("uniform",)
    for n in range(10, 17):
        for fi, family in enumerate(families):
            for rep in range(repetitions):
                seed = base + (n-10)*1000 + fi*100 + rep
                sources = scene_sources(seed, n, family)
                scene_hash = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
                for mode in MODES:
                    result.append(dict(scene_id=f"{split}-{n}-{family}-{rep}-{mode}",
                                       scene_group=f"{split}-{n}-{family}-{rep}",
                                       seed=seed, N=n, family=family, error_mode=mode,
                                       source_sha256=scene_hash, sources=sources))
    return result


def audit_events(events, expected_t):
    out = dict(movement_s=0., measure_s=0., clear_s=0., n_switch=0,
               discovery_measure=0, refine_measure=0, no_signal=0, failed_clear=0,
               action_time_max_error=0.)
    pos = np.zeros(2)
    channel, t, last_clear = 1, 0., 0.
    seen = set()
    for e in events:
        p = np.array([e["x"], e["y"]])
        movement = float(np.linalg.norm(p-pos))/5
        out["movement_s"] += movement
        if e["op"] == "measure":
            out["discovery_measure" if e["k"] not in seen else "refine_measure"] += 1
            switch = int(channel != e["k"])
            fixed = 5 + switch
            out["n_switch"] += switch
            out["measure_s"] += fixed
            channel = e["k"]
            if e["result"] == "no_signal":
                out["no_signal"] += 1
            else:
                seen.add(e["k"])
        else:
            fixed = 3 + 2*int(e["ok"])
            out["clear_s"] += fixed
            out["failed_clear"] += int(not e["ok"])
            if e["ok"]:
                last_clear = e["t"]
        t += movement + fixed
        out["action_time_max_error"] = max(out["action_time_max_error"], abs(t-e["t"]))
        pos = p
    out["total_time_error"] = abs(expected_t-t)
    out["after_last_clear_s"] = t-last_clear
    return out


def run_scene(task):
    scene, variants, outdir = task
    rows, traces = [], []
    for variant in variants:
        sim = Q3Environment(scene["sources"], scene["seed"], scene["error_mode"])
        runner = make_runner(sim.client(), variant)
        result = runner.run()
        row = {key: scene[key] for key in ("scene_id", "scene_group", "seed", "N", "family", "error_mode", "source_sha256")}
        row.update(variant=variant)
        for key in ("K", "T", "T_over_K", "move_m", "n_measure", "n_clear", "n_safe",
                    "n_full_225", "all_certified", "failure", "wall_s", "detected"):
            row[key] = result.get(key)
        row.update(audit_events(sim.events, result["T"]))
        row["full_success"] = bool(row["K"] == scene["N"] and row["all_certified"] and not row["failure"])
        row["truth_clear_match"] = row["K"] == len(sim.cleared)
        row["action_count_match"] = row["n_measure"] == sim.n_measure and row["n_clear"] == sim.n_clear
        rows.append(row)
        traces.append(dict(variant=variant, summary=result, actions=sim.events))
    path = Path(outdir) / "traces" / (scene["scene_id"] + ".json.gz")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(dict(scene_id=scene["scene_id"], runs=traces), f)
    return rows


def summarize(rows):
    output = []
    for variant in dict.fromkeys(r["variant"] for r in rows):
        rr = [r for r in rows if r["variant"] == variant]
        n = len(rr)
        record = dict(variant=variant, scenes=n, full_scenes=sum(r["full_success"] for r in rr),
                      total_K=sum(r["K"] for r in rr), total_N=sum(r["N"] for r in rr))
        record["clearance_rate"] = record["total_K"]/record["total_N"]
        for key in ("T", "T_over_K", "movement_s", "move_m", "n_measure", "failed_clear",
                    "n_switch", "n_safe", "discovery_measure", "refine_measure", "wall_s"):
            vals = [r[key] for r in rr if r[key] is not None]
            record["mean_"+key] = float(np.mean(vals)) if len(vals) == n else None
        record["pooled_T_over_K"] = sum(r["T"] for r in rr)/record["total_K"] if record["total_K"] else None
        values = [r["T_over_K"] for r in rr if r["T_over_K"] is not None]
        record["p95_T_over_K"] = float(np.quantile(values, .95)) if len(values) == n else None
        record["rank_eligible"] = record["full_scenes"] == n
        output.append(record)
    return output


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("pilot", "evaluation"), default="pilot")
    ap.add_argument("--repetitions", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS))
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    repetitions = args.repetitions if args.repetitions is not None else (5 if args.split == "evaluation" else 1)
    if repetitions < 1 or args.workers < 1:
        ap.error("repetitions and workers must be positive")
    out = args.output or HERE / args.split
    out.mkdir(parents=True, exist_ok=True)
    if (out / "rows.csv").exists():
        ap.error("output already has results; choose a new directory")
    (out / "traces").mkdir(exist_ok=True)
    matrix = scenes(args.split, repetitions)
    (out / "scenes.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    paths = [HERE / "environment.py", HERE / "policies.py", Path(__file__),
             ROOT / "data_preparation/parameters.csv", HERE / "design.md"]
    paths += list((ROOT / "simulator_automation").glob("q3_*.py"))
    paths += [ROOT / "src" / (name+".py") for name in ("geometry", "localization", "active", "params")]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest = dict(source="synthetic offline Q3 only", command=sys.argv,
                    python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
                    platform=platform.platform(), variants=args.variants,
                    scenes=len(matrix), code_sha256=hashes,
                    scenes_sha256=hashlib.sha256((out/"scenes.json").read_bytes()).hexdigest())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rows = []
    start = time.perf_counter()
    tasks = [(s, args.variants, str(out)) for s in matrix]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_scene, task) for task in tasks]
        for i, future in enumerate(as_completed(futures), 1):
            batch = future.result()
            rows.extend(batch)
            write_csv(out / "rows.partial.csv", rows)
            if i % 5 == 0 or i == len(tasks):
                print(json.dumps(dict(done_scenes=i, total_scenes=len(tasks),
                    runs=len(rows), failures=sum(not r["full_success"] for r in rows),
                    elapsed_s=round(time.perf_counter()-start, 1))), flush=True)
    order = {v: i for i, v in enumerate(args.variants)}
    rows.sort(key=lambda r: (r["scene_id"], order[r["variant"]]))
    write_csv(out / "rows.csv", rows)
    summary = summarize(rows)
    write_csv(out / "summary.csv", summary)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest["elapsed_s"] = time.perf_counter()-start
    manifest["changed_inputs"] = [rel for rel, digest in hashes.items()
                                  if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() != digest]
    manifest["rows_sha256"] = hashlib.sha256((out/"rows.csv").read_bytes()).hexdigest()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

"""Offline search for equal-length HEX37 Hamilton prefix routes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src")]

from q4_cover import HEX37_ROUTE_CURRENT, set_cover_mode  # noqa: E402
from q4_prefix import dfs_hamilton, dihedral_paths, evaluate_order, hex37_adj  # noqa: E402


def main():
    set_cover_mode("HEX37")
    rng = np.random.default_rng(20260911)
    adj = hex37_adj()
    candidates = {"CURRENT": list(range(37))}
    for i, order in enumerate(dihedral_paths()):
        candidates[f"DIHEDRAL_{i}"] = order
    for t in range(80):
        path = dfs_hamilton(rng, adj)
        if path is None:
            continue
        key = tuple(path)
        name = f"DFS_{t}"
        if key in {tuple(v) for v in candidates.values()}:
            continue
        candidates[name] = path
    rows = []
    for name, order in candidates.items():
        stats = evaluate_order(order, np.random.default_rng(1), n_each=2500)
        row = {
            "name": name,
            "score": stats["score"],
            "order": order,
            "mixed": stats["mixed"],
            "omni": stats["omni"],
            "directional": stats["directional"],
            "extreme_outward": stats["extreme_outward"],
        }
        rows.append(row)
        print(
            json.dumps(
                {
                    "name": name,
                    "score": row["score"],
                    "mean": stats["mixed"]["mean_first_detect_index"],
                    "p95": stats["mixed"]["p95_first_detect_index"],
                    "cov10": stats["mixed"]["early_coverage_10"],
                    "cov20": stats["mixed"]["early_coverage_20"],
                }
            ),
            flush=True,
        )
    rows.sort(key=lambda r: r["score"])
    current = next(r for r in rows if r["name"] == "CURRENT")
    payload = {
        "current": current,
        "ranked": [
            {
                "name": r["name"],
                "score": r["score"],
                "order": r["order"],
                "mixed": r["mixed"],
                "omni": r["omni"],
                "directional": r["directional"],
                "extreme_outward": r["extreme_outward"],
            }
            for r in rows[:12]
        ],
        "n_candidates": len(rows),
        "baseline": HEX37_ROUTE_CURRENT,
    }
    out = Path(__file__).with_name("prefix_routes.json")
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "n": len(rows), "best": payload["ranked"][0]["name"],
                      "best_score": payload["ranked"][0]["score"], "current_score": current["score"]}, indent=2))


if __name__ == "__main__":
    main()

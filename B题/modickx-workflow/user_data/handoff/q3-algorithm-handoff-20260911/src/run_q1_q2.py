"""Offline Q1/Q2 demonstration. No simulator calls, no formal tests."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from geometry import diameter_circle_covers, localize_wedges
from localization import select_second_point, theoretical_sector_rho

OUT = Path(__file__).resolve().parents[1] / "data_preparation" / "output"


def q1_equilateral() -> dict:
    verts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, math.sqrt(3.0) / 2.0]])
    sites = []
    bearings = []
    for i in range(3):
        e = verts[(i + 1) % 3] - verts[i]
        e = e / np.linalg.norm(e)
        sites.append(verts[i] - 100.0 * e)
        bearings.append(math.degrees(math.atan2(e[1], e[0])) + 1.0)
    result = localize_wedges(sites, bearings)
    return {
        "status": result.status,
        "n_vertices": int(len(result.vertices)),
        "diameter": result.diameter,
        "mec_radius": result.mec_radius,
        "diameter_circle_covers": diameter_circle_covers(result.vertices, result.diameter),
        "vertices": result.vertices.tolist(),
    }


def q1_two_wedges() -> dict:
    result = localize_wedges([[-200.0, 0.0], [0.0, -200.0]], [0.0, 90.0])
    return {
        "status": result.status,
        "n_vertices": int(len(result.vertices)),
        "diameter": result.diameter,
        "mec_radius": result.mec_radius,
        "mec_center": None if result.mec_center is None else result.mec_center.tolist(),
    }


def q2_demo() -> dict:
    s = np.array([0.0, 0.0])
    bearing = 0.0
    result = select_second_point(s, bearing, n_azimuth=16, refine=True)
    layers = {}
    for c in result.candidates:
        layers[c["layer"]] = layers.get(c["layer"], 0) + 1
    return {
        "s": s.tolist(),
        "bearing_deg": bearing,
        "theoretical_sector_rho_m": theoretical_sector_rho(),
        "c1": result.c1.tolist(),
        "rho1": result.rho1,
        "R_core": result.R_core,
        "q_star": result.q_star.tolist(),
        "J_star": result.J_star,
        "travel_s": result.travel_s,
        "n_candidates": len(result.candidates),
        "layers": layers,
        "claim": result.claim,
    }


def main() -> None:
    payload = {"q1_equilateral": q1_equilateral(), "q1_two_wedges": q1_two_wedges(), "q2": q2_demo()}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "q1_q2_demo.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()

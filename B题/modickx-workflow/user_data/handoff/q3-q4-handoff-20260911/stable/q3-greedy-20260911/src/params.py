"""Load frozen contest constants from data_preparation/parameters.csv."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAM_CSV = ROOT / "data_preparation" / "parameters.csv"

_CACHE: dict[str, float | str] | None = None


def load_parameters() -> dict[str, float | str]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    values: dict[str, float | str] = {}
    with PARAM_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            raw = row["value"]
            name = row["parameter"]
            try:
                values[name] = float(raw)
            except ValueError:
                values[name] = raw
    _CACHE = values
    return values


P = load_parameters()
OMEGA_RADIUS = float(P["target_region_radius"])
R_MIN = float(P["receiver_radius_min"])
R_MAX = float(P["receiver_radius_max"])
EPS_DEG = float(P["bearing_error_bound"])
NEAR_RADIUS = float(P["near_radius"])
CLEAR_RADIUS = float(P["clear_radius"])
SPEED = float(P["movement_speed"])
COORD_ABS_LIMIT = float(P["coordinate_abs_limit"])

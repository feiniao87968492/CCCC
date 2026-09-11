"""Per-case Q2 seed metrics. Level-1 failures void the comparison table."""
from __future__ import annotations

import time
from typing import Iterable

import numpy as np
from scipy.spatial import ConvexHull

from localization import evaluate_J, in_c_guaranteed, select_second_point
from params import CLEAR_RADIUS, R_MIN
from q2_scenario import Scenario, eps2_for_q
from q2_validation import (
    ATOL_M,
    CORE_ATOL_M,
    baseline_90deg,
    baseline_c1,
    certified_clear,
    f_no_points,
    in_Z1,
    in_Z_dir,
    in_Z_near,
    in_Z_no,
    in_c_core,
    j_of_points,
    legacy_radii_m,
    max_distance_to_set,
    min_j,
    polar_grid,
    simulate_measure,
)


def point_in_f1_outer(g: np.ndarray, verts: np.ndarray, slack: float = 1e-4) -> bool:
    g = np.asarray(g, dtype=float).reshape(2)
    verts = np.asarray(verts, dtype=float)
    if len(verts) == 0:
        return False
    if len(verts) < 3:
        return bool(np.min(np.linalg.norm(verts - g, axis=1)) <= slack)
    try:
        hull = ConvexHull(verts)
    except Exception:
        return True
    return bool(np.all(hull.equations[:, :2] @ g + hull.equations[:, 2] <= slack))


def rho_true_branch(y: str, b2, q, s, r, f1_verts: np.ndarray) -> float:
    q = np.asarray(q, dtype=float)
    s = np.asarray(s, dtype=float)
    if y == "near":
        return 5.0
    if y == "no_signal":
        pts = f_no_points(f1_verts, s, q)
        if len(pts) == 0:
            return 0.0
        from geometry import min_enclosing_circle

        _, rho = min_enclosing_circle(pts)
        return float(rho)
    if y == "direction" and b2 is not None:
        from localization import _sample_boundary, _angle_diff_deg
        from params import EPS_DEG, NEAR_RADIUS

        samples = _sample_boundary(f1_verts)
        d_q = np.linalg.norm(samples - q, axis=1)
        far = samples[d_q > NEAR_RADIUS + 1e-9]
        if len(far) == 0:
            return 5.0
        angs = np.degrees(np.arctan2(far[:, 1] - q[1], far[:, 0] - q[0])) % 360.0
        keep = far[_angle_diff_deg(angs, float(b2)) <= EPS_DEG + 1e-9]
        if len(keep) == 0:
            return float("nan")
        from geometry import min_enclosing_circle

        _, rho = min_enclosing_circle(keep)
        return float(rho)
    return float("nan")


def evaluate_case(
    sc: Scenario,
    n_azimuth: int = 8,
    refine: bool = False,
    with_legacy: bool = False,
    with_ref: bool = True,
    jitter: bool = False,
) -> dict:
    s = sc.s
    st = sc.state
    a = sc.bearing_deg
    t0 = time.perf_counter()
    result = select_second_point(s, a, n_azimuth=n_azimuth, refine=refine)
    cpu_s = time.perf_counter() - t0
    q = result.q_star
    eps2 = eps2_for_q(sc.seed, q)
    y2, b2 = simulate_measure(q, st.g, st.r, eps2)

    if y2 == "near":
        in_zy = in_Z_near(st.g, st.r, s, a, q)
    elif y2 == "direction":
        in_zy = in_Z_dir(st.g, st.r, s, a, q, float(b2))
    else:
        in_zy = in_Z_no(st.g, st.r, s, a, q)

    in_core = in_c_core(q, result.c1, result.R_core)
    worst_core = max_distance_to_set(q, result.F1_vertices) if in_core else float("nan")
    core_false = bool(in_core and worst_core > R_MIN + CORE_ATOL_M)
    f1_ok = point_in_f1_outer(st.g, result.F1_vertices)
    z1_ok = in_Z1(st.g, st.r, s, a)
    d_s = float(np.linalg.norm(st.g - s))
    d_q = float(np.linalg.norm(st.g - q))
    same_r_ok = d_s <= st.r + ATOL_M
    if y2 == "no_signal":
        same_r_ok = same_r_ok and d_q > st.r - ATOL_M
    else:
        same_r_ok = same_r_ok and d_q <= st.r + ATOL_M

    rho_post = rho_true_branch(y2, b2, q, s, st.r, result.F1_vertices)
    would_claim_clear = bool(np.isfinite(result.J_star) and result.J_star <= CLEAR_RADIUS)
    clear_false = bool(would_claim_clear and (not certified_clear(result.J_star)))
    # J is itself the claimed worst rho; false cert if we would claim and J>20 — tautology.
    # Keep an independent check: cannot claim clear if true-branch outer rho > 20.
    if would_claim_clear and np.isfinite(rho_post) and rho_post > CLEAR_RADIUS + 1e-6:
        clear_false = True

    guaranteed = in_c_guaranteed(q, s, result.F1_vertices)
    j_c1 = evaluate_J(baseline_c1(result), s, result.F1_vertices)["J"]
    j_90 = evaluate_J(baseline_90deg(s, a, result), s, result.F1_vertices)["J"]

    j_legacy = float("nan")
    n_legacy = 0
    if with_legacy:
        pts = polar_grid(s, legacy_radii_m(), n_azimuth=12)
        n_legacy = len(pts)
        j_legacy = min_j(j_of_points(pts, s, result.F1_vertices))["J"]

    j_ref = float("nan")
    n_ref = 0
    if with_ref:
        radii = np.linspace(0.0, result.R_core + 400.0, 8)
        pts = polar_grid(result.c1, radii, n_azimuth=12)
        n_ref = len(pts)
        j_ref = min_j(j_of_points(pts, s, result.F1_vertices))["J"]

    j_gap_ref = float("nan")
    if np.isfinite(j_ref) and j_ref > 0:
        j_gap_ref = (result.J_star - j_ref) / j_ref

    j_jitter = float("nan")
    if jitter:
        alt = select_second_point(s, a + 0.01, n_azimuth=n_azimuth, refine=False)
        if result.J_star > 1e-9:
            j_jitter = abs(alt.J_star - result.J_star) / result.J_star

    flags = []
    if not z1_ok:
        flags.append("truth_not_in_Z1")
    if not in_zy:
        flags.append("truth_not_in_Zy")
    if not f1_ok:
        flags.append("F1_outer_dropped_g")
    if core_false:
        flags.append("core_false_guarantee")
    if clear_false:
        flags.append("clear_false_certificate")
    if not same_r_ok:
        flags.append("same_r_violation")

    return {
        "seed": sc.seed,
        "stratum": sc.stratum,
        "rejects": sc.rejects,
        "s_x": float(s[0]),
        "s_y": float(s[1]),
        "g_x": float(st.g[0]),
        "g_y": float(st.g[1]),
        "r": float(st.r),
        "eps1": float(st.eps1_deg),
        "eps2": float(eps2),
        "a": float(a),
        "q_x": float(q[0]),
        "q_y": float(q[1]),
        "J_star": float(result.J_star),
        "rho1": float(result.rho1),
        "R_core": float(result.R_core),
        "y2": y2,
        "travel_s": float(result.travel_s),
        "n_cand": int(len(result.candidates)),
        "cpu_s": float(cpu_s),
        "rho_post_true": float(rho_post) if np.isfinite(rho_post) else float("nan"),
        "rho_le_20": bool(np.isfinite(rho_post) and rho_post <= CLEAR_RADIUS),
        "in_c_core": bool(in_core),
        "guaranteed_second": bool(guaranteed),
        "J_c1": float(j_c1),
        "J_90": float(j_90),
        "J_legacy": float(j_legacy) if np.isfinite(j_legacy) else float("nan"),
        "n_legacy": int(n_legacy),
        "J_ref": float(j_ref) if np.isfinite(j_ref) else float("nan"),
        "n_ref": int(n_ref),
        "J_gap_ref": float(j_gap_ref) if np.isfinite(j_gap_ref) else float("nan"),
        "J_jitter": float(j_jitter) if np.isfinite(j_jitter) else float("nan"),
        "truth_in_Z1": bool(z1_ok),
        "truth_in_Zy": bool(in_zy),
        "F1_outer_contains_g": bool(f1_ok),
        "core_false_guarantee": bool(core_false),
        "clear_false_certificate": bool(clear_false),
        "same_r_violation": bool(not same_r_ok),
        "level1_fail": bool(flags),
        "flags": "|".join(flags),
        "claim": result.claim,
    }


def _quantiles(values: Iterable[float]) -> dict:
    arr = np.array([v for v in values if v is not None and np.isfinite(v)], dtype=float)
    if len(arr) == 0:
        return {"n": 0, "p50": None, "p90": None, "p95": None, "max": None}
    return {
        "n": int(len(arr)),
        "p50": float(np.quantile(arr, 0.50)),
        "p90": float(np.quantile(arr, 0.90)),
        "p95": float(np.quantile(arr, 0.95)),
        "max": float(np.max(arr)),
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    level1 = {
        "n": n,
        "truth_in_Z1_fail": sum(not r["truth_in_Z1"] for r in rows),
        "truth_in_Zy_fail": sum(not r["truth_in_Zy"] for r in rows),
        "F1_outer_contains_g_fail": sum(not r["F1_outer_contains_g"] for r in rows),
        "core_false_guarantee": sum(r["core_false_guarantee"] for r in rows),
        "clear_false_certificate": sum(r["clear_false_certificate"] for r in rows),
        "same_r_violation": sum(r["same_r_violation"] for r in rows),
        "failed_seeds": [r["seed"] for r in rows if r["level1_fail"]],
    }
    level1_ok = all(
        level1[k] == 0
        for k in (
            "truth_in_Z1_fail",
            "truth_in_Zy_fail",
            "F1_outer_contains_g_fail",
            "core_false_guarantee",
            "clear_false_certificate",
            "same_r_violation",
        )
    )
    by_y = {}
    for y in ("near", "direction", "no_signal"):
        sub = [r for r in rows if r["y2"] == y]
        by_y[y] = {"n": len(sub), "truth_in_Zy_fail": sum(not r["truth_in_Zy"] for r in sub)}
    by_stratum = {}
    for r in rows:
        by_stratum.setdefault(r["stratum"], []).append(r)

    secondary = None
    tertiary = None
    if level1_ok:
        secondary = {
            "J_star": _quantiles(r["J_star"] for r in rows),
            "rho_post_true": _quantiles(r["rho_post_true"] for r in rows),
            "rho_le_20_rate": {
                "num": sum(r["rho_le_20"] for r in rows),
                "den": n,
                "note": "empirical under generator; not a clearance certificate rate",
            },
            "guaranteed_second_rate": {"num": sum(r["guaranteed_second"] for r in rows), "den": n},
            "no_signal_rate": {
                "all": {"num": sum(r["y2"] == "no_signal" for r in rows), "den": n},
                "L7": {
                    "num": sum(r["y2"] == "no_signal" for r in rows if r["stratum"] == "L7"),
                    "den": sum(r["stratum"] == "L7" for r in rows),
                },
            },
            "J_jitter": _quantiles(r["J_jitter"] for r in rows),
            "by_stratum_J_star": {k: _quantiles(x["J_star"] for x in v) for k, v in sorted(by_stratum.items())},
        }
        pair = [r for r in rows if np.isfinite(r["J_star"]) and np.isfinite(r["J_c1"])]
        tertiary = {
            "travel_s": _quantiles(r["travel_s"] for r in rows),
            "n_cand": _quantiles(r["n_cand"] for r in rows),
            "cpu_s": _quantiles(r["cpu_s"] for r in rows),
            "J_gap_ref": _quantiles(r["J_gap_ref"] for r in rows),
            "J_vs_c1": {
                "den": len(pair),
                "mean_diff": float(np.mean([r["J_star"] - r["J_c1"] for r in pair])) if pair else None,
            },
        }
    return {
        "generator": "q2_scenario_v1",
        "independent_unit": "first_direction_plus_second_measure",
        "level1": level1,
        "level1_ok": level1_ok,
        "by_second_feedback": by_y,
        "level2": secondary,
        "level3": tertiary,
        "claim_limit": "self-built stratified scenes; not contest probability; not continuous global optimum",
    }

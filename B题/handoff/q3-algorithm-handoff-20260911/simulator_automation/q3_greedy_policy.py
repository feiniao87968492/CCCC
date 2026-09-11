"""Greedy Q3 decisions. Pure geometry; no HTTP, no oracle, no true g/r."""
from __future__ import annotations

import numpy as np

from geometry import min_enclosing_circle, unit
from q3_state import dist

ONE_SHOT_RANGE_M = 810.0
APPROACH_M = 500.0
LATERAL_M = 150.0
MIN_ALONG_M = 200.0
MIN_PERP_M = 80.0
RAY_STEP_M = 40.0
RAY_MAX_M = 1200.0
TRY_CLEAR_IF_RHO_BELOW = 40.0
TOUR_CLEAR_HOP_M = 120.0
TOUR_BRANCH_M = 250.0
POST_TOUR_CLEAR_HOP_M = 400.0
CERTIFIED_CLEAR_HOP_M = 900.0
PATH_ALIGN_DEG = 15.0
FLIP_TOL_DEG = 25.0


def _uv(bearing_deg: float):
    u = unit(np.deg2rad(float(bearing_deg)))
    n = np.array([-u[1], u[0]])
    return u, n


def is_good_second_site(pos, first_site, first_bearing: float) -> bool:
    """True if pose is already a useful second-measure / try-clear site for this source."""
    pos = np.asarray(pos, dtype=float).reshape(2)
    s = np.asarray(first_site, dtype=float).reshape(2)
    u, _n = _uv(first_bearing)
    v = pos - s
    along = float(np.dot(v, u))
    perp = float(abs(v[0] * u[1] - v[1] * u[0]))
    return along >= MIN_ALONG_M and perp >= MIN_PERP_M


def should_process_pending_on_tour(pos, remaining_cover, first_site, first_bearing: float) -> bool:
    """Do not leave an unfinished seven-point tour unless this pose is already a good site."""
    if remaining_cover is None or len(remaining_cover) == 0:
        return True
    return is_good_second_site(pos, first_site, first_bearing)


def greedy_second_measure_points(s, bearing_deg: float, robot_pos, *, on_tour: bool = True) -> list[np.ndarray]:
    """Second-measure sites. On tour: local offsets only. After tour: approach along the first ray."""
    s = np.asarray(s, dtype=float).reshape(2)
    x = np.asarray(robot_pos, dtype=float).reshape(2)
    u, n = _uv(bearing_deg)
    approach = s + APPROACH_M * u
    if dist(x, s) < 80.0 or not on_tour:
        return [approach + LATERAL_M * n, approach - LATERAL_M * n]
    return [x + LATERAL_M * n, x - LATERAL_M * n]


def try_clear_points_after_second(s, bearing_deg: float, s2, th2: float) -> list[np.ndarray]:
    """1–2 clear tries at the two-wedge MEC even if rho is slightly above 20 m."""
    from localization import _wedge_clip, f1_outer_vertices

    s = np.asarray(s, dtype=float).reshape(2)
    s2 = np.asarray(s2, dtype=float).reshape(2)
    u, _n = _uv(bearing_deg)
    g_hat = s + APPROACH_M * u
    tries: list[np.ndarray] = []
    try:
        verts = f1_outer_vertices(s, bearing_deg)
        verts = _wedge_clip(verts, s2, float(th2))
        if len(verts):
            c, rho = min_enclosing_circle(verts)
            tries.append(np.asarray(c, dtype=float).reshape(2))
            if float(rho) > 20.0:
                tries.append(0.7 * c + 0.3 * g_hat)
    except Exception:
        tries.append(g_hat)
    if not tries:
        tries.append(g_hat)
    out = []
    seen = set()
    for p in tries:
        key = (round(float(p[0]), 0), round(float(p[1]), 0))
        if key in seen:
            continue
        seen.add(key)
        out.append(np.asarray(p, dtype=float).reshape(2))
        if len(out) >= 2:
            break
    return out


def first_bearing_try_clear_points(s, bearing_deg: float) -> list[np.ndarray]:
    """At most two try-clears along the first ray (cheaper than a long second-measure hop)."""
    s = np.asarray(s, dtype=float).reshape(2)
    u, _n = _uv(bearing_deg)
    return [s + 500.0 * u, s + 700.0 * u]


def ray_try_clear_points(s, bearing_deg: float, step: float = RAY_STEP_M, a_max: float = RAY_MAX_M) -> list[np.ndarray]:
    s = np.asarray(s, dtype=float).reshape(2)
    u, _n = _uv(bearing_deg)
    pts = []
    a = float(step)
    while a <= a_max + 1e-9:
        pts.append(s + a * u)
        a += float(step)
    return pts


def heading_delta_deg(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def is_bearing_flip(a1: float, a2: float, tol: float = FLIP_TOL_DEG) -> bool:
    return heading_delta_deg(a2, a1 + 180.0) <= float(tol)


def tour_clear_hop_cap(remaining_cover) -> float:
    """During an unfinished cover tour, only allow short try-clear branches."""
    if remaining_cover is None or len(remaining_cover) == 0:
        return 1e9
    return TOUR_CLEAR_HOP_M


def select_next_cover(pos, remaining, pending) -> np.ndarray:
    """Prefer a remaining station aligned with a pending bearing; never skip the current station."""
    remaining = [np.asarray(p, dtype=float).reshape(2) for p in remaining]
    if not remaining:
        raise ValueError("no remaining cover points")
    pos = np.asarray(pos, dtype=float).reshape(2)
    for p in remaining:
        if dist(pos, p) < 1.0:
            return p
    if len(remaining) == 1:
        return remaining[0]
    pending = list(pending or [])
    best = remaining[0]
    best_score = -1e18
    for p in remaining:
        score = -dist(pos, p) / 500.0
        for item in pending:
            s = np.asarray(item[0], dtype=float).reshape(2)
            a = float(item[1])
            if is_good_second_site(p, s, a):
                score += 2.0
            u, _n = _uv(a)
            v = p - s
            vn = float(np.linalg.norm(v))
            if vn > 1.0:
                ang = float(np.degrees(np.arccos(np.clip(float(np.dot(v / vn, u)), -1.0, 1.0))))
                if ang < 20.0:
                    score += 4.0 - ang / 10.0
        if score > best_score:
            best_score = score
            best = p
    return best


def path_try_clear_points(a, b, first_site, first_bearing: float, step: float = RAY_STEP_M, max_off_deg: float = PATH_ALIGN_DEG) -> list[np.ndarray]:
    """40 m samples along a→b only if that segment tracks the first bearing."""
    a = np.asarray(a, dtype=float).reshape(2)
    b = np.asarray(b, dtype=float).reshape(2)
    s = np.asarray(first_site, dtype=float).reshape(2)
    v = b - a
    length = float(np.linalg.norm(v))
    if length < max(step, 100.0):
        return []
    vhat = v / length
    u, _n = _uv(first_bearing)
    ang = float(np.degrees(np.arccos(np.clip(abs(float(np.dot(vhat, u))), -1.0, 1.0))))
    if ang > float(max_off_deg):
        return []
    ab2 = float(np.dot(v, v))
    t = float(np.clip(np.dot(s - a, v) / ab2, 0.0, 1.0))
    if dist(s, a + t * v) > 80.0:
        return []
    pts = []
    d = float(step)
    while d < length - 1.0:
        pts.append(a + d * vhat)
        d += float(step)
    return pts


def bearing_flip_try_clear_points(s, a1: float, s2, a2: float, step: float = RAY_STEP_M) -> list[np.ndarray]:
    """If the second bearing flipped ~180°, the source lies on the segment; sample it."""
    if not is_bearing_flip(a1, a2):
        return []
    s = np.asarray(s, dtype=float).reshape(2)
    s2 = np.asarray(s2, dtype=float).reshape(2)
    length = dist(s, s2)
    if length < 1.0:
        return []
    u = (s2 - s) / length
    pts = []
    d = float(step)
    while d < length - step / 2.0:
        pts.append(s + d * u)
        d += float(step)
    return pts


def two_wedge_rho(s, bearing_deg: float, s2, th2: float) -> float:
    from localization import _wedge_clip, f1_outer_vertices

    try:
        verts = f1_outer_vertices(s, bearing_deg)
        verts = _wedge_clip(verts, s2, float(th2))
        if len(verts):
            _c, rho = min_enclosing_circle(verts)
            return float(rho)
    except Exception:
        return 1e9
    return 1e9


def clear_hop_allowed(robot_pos, point, rho, remaining_cover) -> bool:
    """Jump to a try-clear only if it is nearby, or RMEC already certifies a hit."""
    hop = dist(robot_pos, point)
    if hop <= 1.0:
        return True
    if rho is not None and float(rho) <= 20.0 and hop <= CERTIFIED_CLEAR_HOP_M:
        return True
    cap = TOUR_CLEAR_HOP_M if remaining_cover else POST_TOUR_CLEAR_HOP_M
    return hop <= cap


def nearby_try_clear_points(robot_pos, points, remaining_cover) -> list[np.ndarray]:
    cap = tour_clear_hop_cap(remaining_cover)
    x = np.asarray(robot_pos, dtype=float).reshape(2)
    out = []
    seen = set()
    for p in points:
        q = np.asarray(p, dtype=float).reshape(2)
        if dist(x, q) > cap:
            continue
        key = (round(float(q[0]), 0), round(float(q[1]), 0))
        if key in seen:
            continue
        seen.add(key)
        out.append(q)
    return out


def ray_try_clear_walk(s, bearing_deg: float, robot_pos, step: float = RAY_STEP_M, a_max: float = RAY_MAX_M) -> list[np.ndarray]:
    """After the tour: hop to the nearest first-bearing sample, then walk the ray. Cheaper than SAFE."""
    pts = ray_try_clear_points(s, bearing_deg, step=step, a_max=a_max)
    if not pts:
        return []
    i0 = min(range(len(pts)), key=lambda i: dist(robot_pos, pts[i]))
    return pts[i0:] + list(reversed(pts[:i0]))


def ray_try_clear_near(s, bearing_deg: float, robot_pos, step: float = RAY_STEP_M, a_max: float = RAY_MAX_M, max_hop: float = TOUR_BRANCH_M) -> list[np.ndarray]:
    """Walk the first-bearing ray only through points already near the robot."""
    pts = ray_try_clear_points(s, bearing_deg, step=step, a_max=a_max)
    pts.sort(key=lambda p: dist(robot_pos, p))
    out = []
    cur = np.asarray(robot_pos, dtype=float).reshape(2)
    for p in pts:
        q = np.asarray(p, dtype=float).reshape(2)
        if dist(cur, q) <= float(max_hop):
            out.append(q)
            cur = q
    return out


def greedy_action_candidates(pos, remaining_cover, pending_jobs):
    """One joint decision: next cover station or a pending source, by extra path cost.

    Pending jobs are skipped off an unfinished tour unless the pose is already a
    good second site (`should_process_pending_on_tour`) or a local hop is shorter
    than both TOUR_BRANCH_M and the nearest remaining cover.
    """
    pos = np.asarray(pos, dtype=float).reshape(2)
    remaining = [np.asarray(p, dtype=float).reshape(2) for p in (remaining_cover or [])]
    jobs = list(pending_jobs or [])
    actions = []
    nearest_cover = min((dist(pos, p) for p in remaining), default=None)
    for p in remaining:
        cost = dist(pos, p)
        for job in jobs:
            s = np.asarray(job["first_site"], dtype=float).reshape(2)
            a = float(job["first_bearing"])
            if is_good_second_site(p, s, a):
                cost -= 80.0
                break
            u, _n = _uv(a)
            v = p - s
            vn = float(np.linalg.norm(v))
            if vn > 1.0:
                ang = float(np.degrees(np.arccos(np.clip(float(np.dot(v / vn, u)), -1.0, 1.0))))
                if ang < 20.0:
                    cost -= 40.0
                    break
        actions.append({"kind": "cover", "point": p, "cost": float(cost), "k": None})
    for job in jobs:
        k = int(job["k"])
        s = np.asarray(job["first_site"], dtype=float).reshape(2)
        a = float(job["first_bearing"])
        cands = []
        if is_good_second_site(pos, s, a):
            cands.append(pos.copy())
        allow_leave = should_process_pending_on_tour(pos, remaining, s, a) or not remaining
        for c in greedy_second_measure_points(s, a, pos):
            hop = dist(pos, c)
            if remaining:
                cheap_branch = hop <= TOUR_BRANCH_M and (nearest_cover is None or hop <= nearest_cover + 1e-9)
                if not cheap_branch:
                    continue
                if not allow_leave and not is_good_second_site(c, s, a):
                    continue
            elif not allow_leave:
                continue
            cands.append(c)
        seen = set()
        for c in cands:
            q = np.asarray(c, dtype=float).reshape(2)
            key = (round(float(q[0]), 0), round(float(q[1]), 0))
            if key in seen:
                continue
            seen.add(key)
            actions.append({"kind": "pending", "point": q, "cost": dist(pos, q), "k": k})
    if not actions:
        return None
    actions.sort(
        key=lambda z: (
            float(z["cost"]),
            0 if z["kind"] == "cover" else 1,
            0 if z["k"] is None else int(z["k"]),
        )
    )
    return actions[0]

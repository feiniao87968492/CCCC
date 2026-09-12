"""Stratified, seed-bound Q2 scenarios. Simulation generator only; not a contest distribution."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geometry import unit
from params import NEAR_RADIUS, OMEGA_RADIUS, R_MAX, R_MIN
from q2_validation import TrueState, first_observation, in_Z1, in_omega

DEV_SEEDS = list(range(12000, 12020))
HOLDOUT_SEEDS = list(range(22000, 22100))
BOOTSTRAP_SEED = 32000

DEV_QUOTA = (
    ("L1", 5),
    ("L2", 3),
    ("L3", 2),
    ("L4", 2),
    ("L5", 2),
    ("L6", 2),
    ("L7", 2),
    ("L8", 2),
)
HOLDOUT_QUOTA = (
    ("L1", 25),
    ("L2", 15),
    ("L3", 12),
    ("L4", 8),
    ("L5", 10),
    ("L6", 8),
    ("L7", 12),
    ("L8", 10),
)


@dataclass
class Scenario:
    seed: int
    stratum: str
    s: np.ndarray
    state: TrueState
    bearing_deg: float
    rejects: int
    generator: str = "q2_scenario_v1"


def expand_quota(seeds: list[int], quota: tuple[tuple[str, int], ...]) -> list[tuple[int, str]]:
    need = sum(n for _, n in quota)
    if len(seeds) != need:
        raise ValueError(f"seed count {len(seeds)} != quota {need}")
    out = []
    i = 0
    for name, n in quota:
        for _ in range(n):
            out.append((seeds[i], name))
            i += 1
    return out


def eps2_for_q(case_seed: int, q: np.ndarray) -> float:
    """Bind second-measure error to case seed and quantized q, not call index."""
    qx = int(np.round(float(q[0]) * 1000.0)) % 10**9
    qy = int(np.round(float(q[1]) * 1000.0)) % 10**9
    rng = np.random.default_rng(np.random.SeedSequence([int(case_seed), qx, qy]))
    return float(rng.uniform(-1.0, 1.0))


def _accept(s, state: TrueState) -> float | None:
    y, b = first_observation(state, s)
    if y != "direction" or b is None:
        return None
    if not in_Z1(state.g, state.r, s, b):
        return None
    return float(b)


def _draw_l1(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-400.0, 400.0, size=2)
    r = float(rng.uniform(R_MIN + 50.0, R_MAX - 50.0))
    dist = float(rng.uniform(50.0, max(51.0, r - 50.0)))
    ang = float(rng.uniform(0.0, 360.0))
    g = s + dist * unit(np.deg2rad(ang))
    eps1 = float(rng.choice([-0.5, 0.0, 0.5]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l2(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-200.0, 200.0, size=2)
    r = float(rng.uniform(1100.0, 1400.0))
    dist = float(rng.uniform(100.0, r - 20.0))
    true_b = float(rng.choice([0.3, 0.8, 359.2, 359.7, 90.0]))
    g = s + dist * unit(np.deg2rad(true_b))
    eps1 = float(rng.choice([-1.0, 1.0]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l3(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-300.0, 300.0, size=2)
    r = float(rng.choice([R_MIN, R_MAX]))
    dist = float(rng.uniform(NEAR_RADIUS + 2.0, r))
    ang = float(rng.uniform(0.0, 360.0))
    g = s + dist * unit(np.deg2rad(ang))
    eps1 = float(rng.choice([-0.5, 0.0, 0.5]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l4(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-200.0, 200.0, size=2)
    r = float(rng.uniform(1200.0, 1500.0))
    dist = float(rng.uniform(NEAR_RADIUS + 1e-3, NEAR_RADIUS + 1.0))
    ang = float(rng.uniform(0.0, 360.0))
    g = s + dist * unit(np.deg2rad(ang))
    eps1 = float(rng.choice([-1.0, 0.0, 1.0]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l5(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    ang_g = float(rng.uniform(0.0, 360.0))
    g = (OMEGA_RADIUS - float(rng.uniform(0.0, 50.0))) * unit(np.deg2rad(ang_g))
    r = float(rng.choice([1200.0, 1500.0, R_MAX]))
    mode = str(rng.choice(["inward", "tangent", "outward"]))
    dist = float(rng.uniform(200.0, min(r, 1400.0)))
    u_in = -g / max(np.linalg.norm(g), 1e-9)
    lat = np.array([-u_in[1], u_in[0]])
    if mode == "inward":
        s = g + dist * u_in
    elif mode == "outward":
        s = g - dist * u_in
    else:
        s = g + dist * lat
    eps1 = float(rng.choice([-1.0, 0.0, 1.0]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l6(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-80.0, 80.0, size=2)
    r = float(rng.uniform(1300.0, 1500.0))
    dist = float(rng.uniform(1000.0, r))
    ang = float(rng.uniform(0.0, 360.0))
    g = s + dist * unit(np.deg2rad(ang))
    eps1 = float(rng.choice([-0.2, 0.0, 0.2]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l7(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-250.0, 250.0, size=2)
    r = float(R_MIN)
    dist = float(rng.uniform(30.0, 200.0))
    ang = float(rng.uniform(0.0, 360.0))
    g = s + dist * unit(np.deg2rad(ang))
    eps1 = float(rng.choice([-1.0, 0.0, 1.0]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


def _draw_l8(rng: np.random.Generator) -> tuple[np.ndarray, TrueState]:
    s = rng.uniform(-40.0, 40.0, size=2)
    r = float(R_MAX)
    dist = float(rng.uniform(800.0, 1450.0))
    ang = float(rng.choice([0.0, 45.0, 180.0, 270.0, 359.5]))
    g = s + dist * unit(np.deg2rad(ang))
    eps1 = float(rng.choice([-1.0, 0.0, 1.0]))
    return s, TrueState(g=g, r=r, eps1_deg=eps1)


_DRAWERS = {
    "L1": _draw_l1,
    "L2": _draw_l2,
    "L3": _draw_l3,
    "L4": _draw_l4,
    "L5": _draw_l5,
    "L6": _draw_l6,
    "L7": _draw_l7,
    "L8": _draw_l8,
}


def generate_scenario(seed: int, stratum: str, max_tries: int = 250) -> Scenario:
    rng = np.random.default_rng(int(seed))
    drawer = _DRAWERS[stratum]
    rejects = 0
    for _ in range(max_tries):
        s, state = drawer(rng)
        if not in_omega(state.g):
            rejects += 1
            continue
        b = _accept(s, state)
        if b is None:
            rejects += 1
            continue
        return Scenario(
            seed=int(seed),
            stratum=stratum,
            s=np.asarray(s, dtype=float),
            state=state,
            bearing_deg=b,
            rejects=rejects,
        )
    raise RuntimeError(f"failed to generate seed={seed} stratum={stratum} after {max_tries} tries")


def iter_set(name: str) -> list[Scenario]:
    if name == "dev":
        pairs = expand_quota(DEV_SEEDS, DEV_QUOTA)
    elif name == "holdout":
        pairs = expand_quota(HOLDOUT_SEEDS, HOLDOUT_QUOTA)
    else:
        raise ValueError(name)
    return [generate_scenario(seed, stratum) for seed, stratum in pairs]

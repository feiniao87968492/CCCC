"""Observation-only RF heuristics for Q4; never used to certify absence/clearing.

Finite location, heading and radius hypotheses rank probes by reception and
intersection geometry per unit detour. Negative observations update these soft
weights only. The continuous positive-observation polygon remains the authority
for guaranteed clearing and optical fallback.
"""
from __future__ import annotations

import numpy as np

from params import R_MIN, R_MAX, SPEED
from q4_localize import BEARING_ENVELOPE_DEG, legal_xy


def _polygon_samples(verts, n=48):
    verts = np.asarray(verts, dtype=float).reshape(-1, 2)
    anchor = verts.mean(axis=0)
    a = verts - anchor
    b = np.roll(verts, -1, axis=0) - anchor
    areas = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
    if areas.sum() < 1e-9:
        far = np.unravel_index(np.argmax(np.linalg.norm(verts[:, None] - verts[None, :], axis=2)),
                               (len(verts), len(verts)))
        return np.linspace(verts[far[0]], verts[far[1]], n)
    ids = np.searchsorted(np.cumsum(areas) / areas.sum(), (np.arange(n) + .5) / n)
    u = np.sqrt((.5 + np.arange(n) * .618033988749895) % 1)
    v = (.5 + np.arange(n) * .414213562373095) % 1
    return anchor + u[:, None] * ((1 - v[:, None]) * a[ids] + v[:, None] * b[ids])


class ReceptionBelief:
    """Approximate RF posterior, with a nonzero floor for discretization misses."""
    def __init__(self, region, history):
        self.points = _polygon_samples(region["verts"])
        self.rho = float(region["rho"])
        self.history = history
        self._gains = {}
        angles = np.arange(32) * 2 * np.pi / 32
        self.headings = np.column_stack((np.cos(angles), np.sin(angles)))
        self.radii = np.linspace(R_MIN, R_MAX, 3)
        self.weights = np.ones((len(self.points), len(angles) + 1, len(self.radii)))
        self.weights[:, :-1] /= len(angles)  # Equal initial omni / directional mass.
        for h in history:
            heard = self._heard(h["pos"])
            expected = h["result"] in ("direction", "near")
            self.weights *= np.where(heard == expected, 1., .002)
            self.weights /= self.weights.sum()
        self.weights /= self.weights.sum()

    def _heard(self, p):
        vec = np.asarray(p, dtype=float) - self.points
        heading_ok = np.column_stack((vec @ self.headings.T >= 0, np.ones(len(vec), dtype=bool)))
        in_range = np.linalg.norm(vec, axis=1)[:, None] <= self.radii
        return heading_ok[:, :, None] & in_range[:, None, :]

    def reception_probability(self, p):
        return float(np.sum(self.weights * self._heard(p)))

    def expected_gain(self, p):
        """Expected log radius reduction on a positive reading (heuristic)."""
        key = tuple(np.asarray(p, dtype=float).reshape(2))
        if key in self._gains:
            return self._gains[key]
        vec = self.points - p
        distance = np.linalg.norm(vec, axis=1)
        sine = np.zeros(len(self.points))
        for h in self.history:
            if h["result"] != "direction":
                continue
            old = self.points - h["pos"]
            denom = np.maximum(distance * np.linalg.norm(old, axis=1), 1e-9)
            sine = np.maximum(sine, np.abs(old[:, 0] * vec[:, 1] - old[:, 1] * vec[:, 0]) / denom)
        predicted = 2 * np.tan(np.deg2rad(BEARING_ENVELOPE_DEG)) * distance / np.maximum(sine, .015)
        gain = np.maximum(0., np.log((self.rho + 2) / (np.maximum(predicted, 2.) + 2)))
        positive_weight = np.sum(self.weights * self._heard(p), axis=(1, 2))
        self._gains[key] = float(positive_weight @ gain)
        return self._gains[key]


def ranked_refinement_points(region, history, pos, next_cover=None, *, belief=None):
    if belief is None:
        belief = ReceptionBelief(region, history)
    bearings = [h for h in history if h["result"] == "direction"]
    if not bearings:
        return []
    last = bearings[-1]
    center = np.asarray(region["center"], dtype=float)
    origin = np.asarray(last["pos"], dtype=float)
    angle = np.deg2rad(last["svd"])
    axis = np.array([np.cos(angle), np.sin(angle)])
    lateral = np.array([-axis[1], axis[0]])
    projection = (np.asarray(region["verts"]) - origin) @ axis
    candidates = []
    # A source can be just inside the disk boundary, very close to this RF
    # witness. A fixed hundreds-of-metres approach would cross behind it.
    for along, across in ((80., 60.), (200., 100.)):
        for sign in (-1, 1):
            candidates.append(origin + along * axis + sign * across * lateral)
    for fraction in (.25, .5, .75):
        approach = origin + (projection.min() + fraction * np.ptp(projection)) * axis
        for offset in (-140., -60., 60., 140.):
            candidates.append(approach + offset * lateral)
    distance = float(np.clip(2 * region["rho"], 40, 180))
    for along, across in ((-1, 0), (-.7, 1), (-.7, -1), (0, 1), (0, -1), (1, 0)):
        candidates.append(center + distance * (along * axis + across * lateral))
    scored = []
    for p in candidates:
        if not legal_xy(p) or any(np.linalg.norm(p - h["pos"]) <= 1 for h in history):
            continue
        extra = float(np.linalg.norm(p - pos))
        if next_cover is not None:
            extra += float(np.linalg.norm(next_cover - p) - np.linalg.norm(next_cover - pos))
        gain = belief.expected_gain(p)
        score = gain / (8. + max(extra, 0.) / SPEED)
        scored.append((score, gain, p))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    ranked = [item[2] for item in scored]
    if len(bearings) == 1 and history[-1]["result"] == "no_signal" and projection.min() > 30:
        # Negative RF may mean we crossed a nearby outward-facing source.
        # Bracket every feasible source ray BEFORE its nearest possible point.
        # The ray intersects this segment between the known receiving site and
        # the source. A half-plane containing that intersection cannot exclude
        # both endpoints. Check that BOTH endpoints are no farther from ANY
        # feasible source than the original receiving site (an affine vertex
        # test on squared distances), hence both are also inside its RF radius.
        # At least one endpoint must therefore receive under the physical model.
        along = min(80., .4 * float(projection.min()))
        across = .75 * along
        pair = [origin + along * axis + sign * across * lateral for sign in (-1, 1)]
        safe = all(legal_xy(p) and np.max(
            np.dot(p - origin, p - origin) - 2 * (np.asarray(region["verts"]) - origin) @ (p - origin)
        ) < -1e-6 for p in pair)
        if safe:
            fresh = [p for p in pair if all(np.linalg.norm(p - h["pos"]) > 1 for h in history)]
            fresh.sort(key=lambda p: float(np.linalg.norm(p - pos)))
            ranked = fresh + [p for p in ranked if all(np.linalg.norm(p - q) > 1 for q in fresh)]
    return ranked

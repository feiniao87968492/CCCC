"""Minimal geometric test double for Q4Runner. Not the official simulator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))

from q4_runner import Q4Runner  # noqa: E402


class GeomSim:
    def __init__(self, sources):
        self.sources = {int(s["k"]): s for s in sources}
        self.cleared = set()
        self.entered = False
        self.t = 0.0
        self.pos = np.zeros(2)
        self.calls = []

    def enter(self):
        self.entered = True
        return {"virtual_time_s": 0.0, "accepted": True, "remaining_real_duration_s": 1200}

    def exit(self):
        self.entered = False
        return {"accepted": True}

    def _cover(self, p, src) -> bool:
        g = np.asarray(src["g"], float)
        d = float(np.linalg.norm(p - g))
        if d > float(src["r"]) + 1e-9:
            return False
        if not src.get("directional"):
            return True
        if d < 1e-12:
            return False
        psi = float(src["psi"])
        u = np.array([np.cos(psi), np.sin(psi)])
        return float(np.dot(u, p - g)) >= -1e-9

    def measure(self, x, y, k):
        p = np.array([float(x), float(y)])
        self.t += float(np.linalg.norm(p - self.pos)) / 5.0 + 6.0
        self.pos = p
        self.calls.append(("measure", x, y, k))
        src = self.sources.get(int(k))
        if src is None or int(k) in self.cleared or not self._cover(p, src):
            return {"accepted": True, "virtual_time_s": self.t, "measure_result": "no_signal"}
        d = float(np.linalg.norm(p - src["g"]))
        if d <= 5.0:
            return {"accepted": True, "virtual_time_s": self.t, "measure_result": "near"}
        vec = np.asarray(src["g"], float) - p
        svd = float(np.rad2deg(np.arctan2(vec[1], vec[0])))
        return {
            "accepted": True,
            "virtual_time_s": self.t,
            "measure_result": "direction",
            "svd_deg": svd,
        }

    def clear(self, x, y, k):
        p = np.array([float(x), float(y)])
        self.t += float(np.linalg.norm(p - self.pos)) / 5.0 + 3.0
        self.pos = p
        self.calls.append(("clear", x, y, k))
        src = self.sources.get(int(k))
        ok = False
        if src is not None and int(k) not in self.cleared:
            if float(np.linalg.norm(p - src["g"])) <= 20.0 + 1e-9:
                ok = True
                self.cleared.add(int(k))
                self.t += 2.0
        return {
            "accepted": True,
            "virtual_time_s": self.t,
            "clear_result": "success" if ok else "no_target_in_range",
        }


def _run(sources):
    r = Q4Runner(GeomSim(sources))
    return r.run(), r


class GeomLoopTests(unittest.TestCase):
    def test_single_omni(self):
        s, r = _run([{"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False}])
        self.assertEqual(s["K"], 1)
        self.assertTrue(s["all_certified"])
        self.assertEqual(s["n_clear_ok"], 1)
        self.assertNotIn(("clear",), ())
        self.assertTrue(any(c[0] == "clear" and c[3] == 1 for c in r.robot.calls))

    def test_single_directional(self):
        s, _r = _run([{"k": 2, "g": np.array([300.0, 300.0]), "r": 1200.0, "directional": True, "psi": np.deg2rad(225.0)}])
        self.assertEqual(s["K"], 1)
        self.assertTrue(s["all_certified"])

    def test_outward_directional(self):
        s, _r = _run([{"k": 3, "g": np.array([1700.0, 0.0]), "r": 1100.0, "directional": True, "psi": 0.0}])
        self.assertEqual(s["K"], 1)
        self.assertTrue(s["all_certified"])

    def test_near_source(self):
        s, r = _run([{"k": 4, "g": np.array([3.0, 0.0]), "r": 1000.0, "directional": False}])
        self.assertEqual(s["K"], 1)
        self.assertEqual(r.robot.calls[0][0], "measure")
        self.assertTrue(any(c[0] == "clear" and abs(c[1]) < 6 and abs(c[2]) < 6 for c in r.robot.calls))

    def test_mixed_channels(self):
        s, r = _run(
            [
                {"k": 1, "g": np.array([400.0, 0.0]), "r": 1200.0, "directional": False},
                {"k": 5, "g": np.array([0.0, 500.0]), "r": 1200.0, "directional": True, "psi": np.deg2rad(-90.0)},
                {"k": 9, "g": np.array([2.0, 2.0]), "r": 1000.0, "directional": False},
            ]
        )
        self.assertEqual(s["K"], 3)
        self.assertTrue(s["all_certified"])
        self.assertEqual(s["n_clear_ok"], 3)
        self.assertEqual(s["pending"], [])
        after_clear = {}
        cleared_at = {}
        for i, c in enumerate(r.robot.calls):
            if c[0] == "clear" and True:
                pass
        # cleared channels must not be measured again
        seen_clear = set()
        for c in r.robot.calls:
            if c[0] == "clear":
                # success only counted in sim.cleared
                continue
        for c in r.robot.calls:
            if c[0] == "clear":
                k = c[3]
                if k in r.robot.cleared:
                    seen_clear.add(k)
            if c[0] == "measure" and c[3] in seen_clear:
                self.fail("remeasured cleared channel")


if __name__ == "__main__":
    unittest.main()

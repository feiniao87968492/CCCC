from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))
sys.path.insert(0, str(ROOT / "tests"))

from q4_cover import p4_points  # noqa: E402
from q4_policy import select_next_p4  # noqa: E402
from q4_runner import Q4Runner  # noqa: E402
from q4_state import Q4State  # noqa: E402


class FakeRobot:
    def __init__(self):
        self.entered = False
        self.calls = []
        self.t = 0.0

    def enter(self):
        self.entered = True
        return {"virtual_time_s": 0.0, "accepted": True, "remaining_real_duration_s": 1200}

    def exit(self):
        self.entered = False
        return {"accepted": True}

    def measure(self, x, y, k):
        self.calls.append(("measure", x, y, k))
        self.t += 6.0
        return {"accepted": True, "virtual_time_s": self.t, "measure_result": "no_signal"}

    def clear(self, x, y, k):
        self.calls.append(("clear", x, y, k))
        self.t += 3.0
        return {"accepted": True, "virtual_time_s": self.t, "clear_result": "no_target_in_range"}


class Q4RunnerOfflineTests(unittest.TestCase):
    def test_illegal_direction_does_not_mutate(self):
        st = Q4State()
        with self.assertRaises(ValueError):
            st.apply_measure(1, np.zeros(2), "direction", svd_deg=None)
        self.assertEqual(st.channels[1].status, "unseen")
        self.assertEqual(st.channels[1].visited_p4, set())

    def test_failed_clear_keeps_remaining_p4(self):
        st = Q4State()
        st.apply_measure(1, np.zeros(2), "direction", svd_deg=10.0)
        rem_before = set(st.channels[1].remaining_p4())
        st.apply_clear(1, np.array([100.0, 0.0]), False)
        self.assertEqual(st.channels[1].status, "detected")
        self.assertEqual(set(st.channels[1].remaining_p4()), rem_before)
        self.assertTrue(st.channels[1].halfplane_failed)
        cands = select_next_p4(st, certificate_mode=True)
        self.assertIsNotNone(cands)

    def test_offline_runner_scans_without_early_absent(self):
        r = Q4Runner(FakeRobot())
        r.scan_at(np.zeros(2))
        self.assertEqual(r.n_measure, 20)
        self.assertTrue(all(ch.status == "unseen" for ch in r.state.channels.values()))
        self.assertTrue(all(len(ch.no_signal_p4) == 1 for ch in r.state.channels.values()))

    def test_offline_run_exits_and_does_not_use_q3_hex_certificate(self):
        r = Q4Runner(FakeRobot())
        summary = r.run()
        self.assertEqual(summary["strategy"], "Q4_P4")
        self.assertIsNone(summary["failure"])
        self.assertEqual(summary["K"], 0)
        self.assertTrue(summary["all_certified"])
        self.assertEqual(len(summary["certified_absent"]), 20)
        self.assertGreaterEqual(r.n_measure, 81)
        from q4_cover import P4_N
        self.assertEqual(r.state.channels[1].no_signal_p4, set(range(P4_N)))


if __name__ == "__main__":
    unittest.main()

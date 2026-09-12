import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))
sys.path.insert(0, str(ROOT / "tests"))
from test_q3_certified_queue import Robot, seed  # noqa: E402


class GreedyAbortTests(unittest.TestCase):
    def test_failed_localize_abandons_instead_of_safe(self):
        from q3_abort_safe import GreedyAbortRunner

        r = GreedyAbortRunner(Robot(False))
        r.state.R = []
        seed(r, 1, np.array([1200.0, 300.0]))
        r.drain_pending()
        self.assertEqual(r.abandoned, [1])
        self.assertEqual(r.state.n_safe, 0)
        self.assertEqual(r.state.n_full_225, 0)
        self.assertEqual(r.state.cleared_count(), 0)
        self.assertGreaterEqual(len(r.robot.calls), 1)
        self.assertTrue(all(c[2] == 1 for c in r.robot.calls))
        self.assertTrue(all(abs(c[0] - 1200.0) < 2.0 and abs(c[1] - 300.0) < 2.0 for c in r.robot.calls))

    def test_certified_clear_still_happens(self):
        from q3_abort_safe import GreedyAbortRunner

        r = GreedyAbortRunner(Robot(True))
        r.state.R = []
        seed(r, 1, np.array([400.0, 200.0]))
        r.drain_pending()
        self.assertEqual(r.state.cleared_count(), 1)
        self.assertEqual(r.abandoned, [])
        self.assertEqual(r.state.n_safe, 0)

    def test_baseline_greedy_still_calls_safe(self):
        from q3_runner import Q3Runner

        r = Q3Runner(Robot(False), "GREEDY")
        r.state.R = []
        seed(r, 1, np.array([1200.0, 300.0]))
        with patch.object(r, "safe_channel") as safe:
            r.drain_pending()
        safe.assert_called()
        self.assertEqual(r.strategy, "GREEDY")

    def test_run_reports_abort_fields(self):
        from q3_abort_safe import GreedyAbortRunner

        robot = Robot(False)
        robot.enter = lambda: {"virtual_time_s": 0.0}
        robot.entered = False
        r = GreedyAbortRunner(robot)
        r.state.R = []
        for ch in r.state.channels.values():
            ch.status = "certified_absent"
        seed(r, 5, np.array([1200.0, 300.0]))
        result = r.run()
        self.assertEqual(result["strategy"], "GREEDY_ABORT")
        self.assertEqual(result["abandoned_channels"], [5])
        self.assertEqual(result["uncleared_detected_channels"], [5])
        self.assertFalse(result["all_certified"])
        self.assertEqual(result["K"], 0)
        self.assertTrue(result["experimental_incomplete_allowed"])


if __name__ == "__main__":
    unittest.main()

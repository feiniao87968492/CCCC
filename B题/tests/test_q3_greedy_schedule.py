"""Whole-machine GREEDY scheduling: cover + pending in one shipped decision."""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))

from q3_greedy_policy import greedy_action_candidates, should_process_pending_on_tour  # noqa: E402
from q3_runner import Q3Runner  # noqa: E402
from q3_state import P3, dist, pos_key  # noqa: E402


class _ClockRobot:
    def __init__(self):
        self.pos = np.zeros(2)
        self.ch = 1
        self.t = 0.0
        self.entered = True
        self.ops = []

    def enter(self):
        return {"virtual_time_s": 0.0}

    def exit(self):
        return {}

    def measure(self, x, y, k):
        p = np.array([float(x), float(y)])
        self.t += dist(self.pos, p) / 5.0 + 5.0 + (1.0 if int(k) != self.ch else 0.0)
        self.pos = p
        self.ch = int(k)
        self.ops.append(("measure", float(x), float(y), int(k)))
        return {"virtual_time_s": self.t, "measure_result": "no_signal"}

    def clear(self, x, y, k):
        p = np.array([float(x), float(y)])
        hop = dist(self.pos, p)
        self.t += hop / 5.0 + 3.0
        self.pos = p
        self.ops.append(("clear", float(x), float(y), int(k), hop))
        return {"virtual_time_s": self.t, "clear_result": "fail"}


class RunnerScheduleTests(unittest.TestCase):
    def _runner_with_pending(self, pos, remaining, *, k=4, site=None, bearing=0.0):
        runner = Q3Runner(_ClockRobot(), strategy="GREEDY")
        runner.state.pos = np.asarray(pos, dtype=float).reshape(2)
        runner.state.R = [np.asarray(p, dtype=float).reshape(2).copy() for p in remaining]
        site = np.zeros(2) if site is None else np.asarray(site, dtype=float).reshape(2)
        ch = runner.state.channels[k]
        ch.status = "detected"
        ch.ever_detected = True
        ch.first_site = site.copy()
        ch.first_bearing = float(bearing)
        runner.state.P = [k]
        return runner

    def test_run_loop_calls_shipped_joint_scheduler(self):
        src = inspect.getsource(Q3Runner.run)
        self.assertIn("choose_greedy_action", src)
        self.assertNotIn("_path_try_clears", src)
        choose_src = inspect.getsource(Q3Runner.choose_greedy_action)
        self.assertIn("greedy_action_candidates", choose_src)
        self.assertIn("tour_skip_pos", choose_src)

    def test_choose_uses_should_process_and_keeps_unfinished_tour(self):
        remaining = [p.copy() for p in P3[1:]]
        runner = self._runner_with_pending(np.zeros(2), remaining, k=4, bearing=0.0)
        self.assertFalse(
            should_process_pending_on_tour(
                runner.state.pos,
                runner.state.R,
                runner.state.channels[4].first_site,
                runner.state.channels[4].first_bearing,
            )
        )
        act = runner.choose_greedy_action()
        self.assertEqual(act["kind"], "cover")
        self.assertGreater(dist(act["point"], np.zeros(2)), 100.0)

    def test_choose_pending_when_already_at_good_second_site(self):
        remaining = [np.array([1200.0, 0.0])]
        runner = self._runner_with_pending(np.array([700.0, 180.0]), remaining, k=6, bearing=0.0)
        act = runner.choose_greedy_action()
        self.assertEqual(act["kind"], "pending")
        self.assertEqual(act["k"], 6)

    def test_after_tour_nearest_pending_beats_list_order(self):
        runner = Q3Runner(_ClockRobot(), strategy="GREEDY")
        runner.state.pos = np.array([700.0, 180.0])
        runner.state.R = []
        for k, bearing in ((4, 180.0), (6, 0.0)):
            ch = runner.state.channels[k]
            ch.status = "detected"
            ch.ever_detected = True
            ch.first_site = np.array([0.0, 0.0])
            ch.first_bearing = bearing
        runner.state.P = [4, 6]
        act = runner.choose_greedy_action()
        self.assertEqual(act["kind"], "pending")
        self.assertEqual(act["k"], 6)

    def test_tour_skip_does_not_reselect_same_pending_at_same_pose(self):
        remaining = [np.array([1200.0, 0.0])]
        runner = self._runner_with_pending(np.array([700.0, 180.0]), remaining, k=6, bearing=0.0)
        runner.state.channels[6].tour_skip_pos.add(pos_key(runner.state.pos))
        act = runner.choose_greedy_action()
        self.assertEqual(act["kind"], "cover")

    def test_joint_helper_is_the_one_runner_calls(self):
        remaining = [np.array([1200.0, 0.0])]
        jobs = [{"k": 4, "first_site": np.array([0.0, 0.0]), "first_bearing": 0.0}]
        helper = greedy_action_candidates(np.zeros(2), remaining, jobs)
        runner = self._runner_with_pending(np.zeros(2), remaining, k=4, bearing=0.0)
        act = runner.choose_greedy_action()
        self.assertEqual(helper["kind"], act["kind"])


if __name__ == "__main__":
    unittest.main()

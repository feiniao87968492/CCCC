import unittest
from test_q3_certified_queue import Robot, seed
import numpy as np
from unittest.mock import patch


class FastModeTests(unittest.TestCase):
    def test_budget_rejects_expensive_move_before_sending(self):
        from q3_fast_mode import GreedyFastRunner, SourceBudgetExceeded
        r = GreedyFastRunner(Robot(), source_budget_s=300)
        r.source_start = 0.
        with self.assertRaises(SourceBudgetExceeded):
            r.clear(2000., 0., 1)
        self.assertEqual(r.robot.calls, [])

    def test_far_source_is_explicitly_abandoned_in_budget_mode(self):
        from q3_fast_mode import GreedyFastRunner
        r = GreedyFastRunner(Robot(), source_budget_s=10)
        r.state.R = []
        seed(r, 1, np.array([1200., 300.]))
        r.drain_pending()
        self.assertEqual(r.abandoned, [1])
        self.assertFalse(r.state.done_all_channels())
        self.assertEqual(r.robot.calls, [])

    def test_default_mode_clears_far_certified_source(self):
        from q3_fast_mode import GreedyFastRunner
        r = GreedyFastRunner(Robot())
        r.state.R = []
        seed(r, 1, np.array([1200., 300.]))
        r.drain_pending()
        self.assertEqual(r.state.cleared_count(), 1)
        self.assertEqual(r.abandoned, [])

    def test_budget_run_exits_and_reports_incomplete(self):
        from q3_fast_mode import GreedyFastRunner
        robot = Robot()
        robot.enter = lambda: {'virtual_time_s': 0.}
        robot.entered = False
        r = GreedyFastRunner(robot, source_budget_s=10)
        r.state.R = []
        for ch in r.state.channels.values():
            ch.status = 'certified_absent'
        seed(r, 1, np.array([1200., 300.]))
        result = r.run()
        self.assertEqual(result['strategy'], 'GREEDY_FAST')
        self.assertEqual(result['abandoned_channels'], [1])
        self.assertEqual(result['uncleared_detected_channels'], [1])
        self.assertFalse(result['all_certified'])
        self.assertEqual(result['K'], 0)

    def test_trial_round_limited_to_three_before_fallback(self):
        from q3_fast_mode import GreedyFastRunner
        r = GreedyFastRunner(Robot(False))
        seed(r, 1, np.array([1200., 300.]))
        def trial(*args):
            r.state.n_clear += 1
            return False
        with patch.object(r, 'certified_clear_point', return_value=None), \
             patch.object(r, '_trial_points', return_value=[np.array([x, 0.]) for x in range(0, 100, 10)]), \
             patch.object(r, 'heuristic_clear', side_effect=trial) as attempt, \
             patch.object(r, 'posterior_vertices', return_value=None), \
             patch.object(r, 'safe_channel') as fallback:
            r._resolve(1)
        self.assertEqual(attempt.call_count, 3)
        fallback.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()

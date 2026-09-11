import unittest
from test_q3_certified_queue import Robot, seed
import numpy as np


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


if __name__ == '__main__':
    unittest.main()

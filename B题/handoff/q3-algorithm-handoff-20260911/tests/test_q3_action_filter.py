import unittest
from unittest.mock import patch
import numpy as np
from test_q3_certified_queue import Q3Runner, Robot, seed


class FilterTests(unittest.TestCase):
    def test_impossible_heuristic_clear_does_not_move_or_send(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        self.assertFalse(r.heuristic_clear(0., 0., 1))
        self.assertEqual(r.robot.calls, [])
        self.assertEqual(r.state.n_clear, 0)
        self.assertEqual(r.state.move_distance, 0.)

    def test_intersecting_clear_is_sent(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        self.assertTrue(r.heuristic_clear(1200., 300., 1))

    def test_unknown_or_inconsistent_posterior_does_not_block_fallback(self):
        r = Q3Runner(Robot(), 'GREEDY')
        with patch.object(r, 'posterior_vertices', return_value=None):
            self.assertTrue(r.heuristic_clear(100., 100., 1))
        # Low-level clear is intentionally unconditional for near/full SAFE.
        seed(r, 2, np.array([1200., 300.]))
        self.assertTrue(r.clear(0., 0., 2))

    def test_ready_pending_is_not_rescanned_and_remains_pending(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        with patch.object(r, 'measure', side_effect=AssertionError('redundant scan')):
            r._scan_pending_at(np.array([0., 1200.]))
            r.greedy_channel(1)
        self.assertIn(1, r.state.P)

    def test_insufficient_evidence_still_gets_pending_scan(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        r.state.channels[1].history = r.state.channels[1].history[:1]
        with patch.object(r, 'measure', return_value={'measure_result': 'no_signal'}) as m:
            r._scan_pending_at(np.array([0., 1200.]))
            m.assert_called_once()

    def test_centerline_branch_really_filters_before_robot_call(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        with patch('q3_greedy_policy.ray_try_clear_near',
                   return_value=[np.zeros(2), np.array([1200., 300.])]):
            r.centerline_clear(1)
        self.assertEqual(len(r.robot.calls), 1)
        self.assertEqual(r.robot.calls[0], (1200., 300., 1))
        self.assertTrue(any(e['op'] == 'clear_filtered' for e in r.log))

    def test_small_region_scan_deferred_but_tail_action_preserved(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        v = np.array([[1170., 290.], [1230., 290.], [1230., 310.], [1170., 310.]])
        with patch.object(r, 'posterior_vertices', return_value=v):
            with patch.object(r, 'measure', side_effect=AssertionError('redundant scan')):
                r._scan_pending_at(np.array([0., 1200.]))
            r.state.R = []
            act = r.choose_greedy_action()
            self.assertEqual(act['kind'], 'local_clear')
            self.assertEqual(act['k'], 1)


if __name__ == '__main__':
    unittest.main()

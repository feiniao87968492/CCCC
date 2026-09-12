import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'simulator_automation'))
from q3_runner import Q3Runner


class Robot:
    def __init__(self, success=True):
        self.calls = []
        self.success = success

    def clear(self, x, y, k):
        self.calls.append((x, y, k))
        return {'clear_result': 'success' if self.success else 'no_target_in_range',
                'virtual_time_s': 500.0}


def seed(r, k, target):
    ch = r.state.channels[k]
    ch.status = 'detected'
    ch.ever_detected = True
    # All positions/bearings here stand in for observed API history.
    sites = [target + [-100, 0], target + [0, -100], target + [100, 0]]
    for p, a in zip(sites, [0., 90., 180.]):
        ch.history.append({'pos': p.tolist(), 'result': 'direction', 'svd': a})
    ch.first_site = sites[0]
    ch.first_bearing = 0.
    ch.greedy_attempted = True
    r.state.P.append(k)


class CertifiedQueueTests(unittest.TestCase):
    def test_far_certified_target_is_cleared_without_safe(self):
        r = Q3Runner(Robot(), 'GREEDY')
        r.state.R = []
        seed(r, 1, np.array([1200., 300.]))
        with patch.object(r, 'safe_channel', side_effect=AssertionError('unexpected SAFE')):
            r.drain_pending()
        self.assertEqual(r.state.cleared_count(), 1)
        self.assertEqual(len(r.robot.calls), 1)

    def test_queue_uses_target_distance_not_discovery_order(self):
        r = Q3Runner(Robot(), 'GREEDY')
        r.state.R = []
        seed(r, 1, np.array([1200., 300.]))
        seed(r, 2, np.array([400., 200.]))
        r.drain_pending()
        self.assertEqual([c[2] for c in r.robot.calls], [2, 1])

    def test_all_bearings_used_even_when_first_last_collinear(self):
        r = Q3Runner(Robot(), 'GREEDY')
        seed(r, 1, np.array([1200., 300.]))
        result = r.certified_clear_point(1)
        self.assertIsNotNone(result)
        self.assertLess(np.linalg.norm(result - [1200., 300.]), 2.)

    def test_failed_certified_point_not_scheduled_again(self):
        r = Q3Runner(Robot(False), 'GREEDY')
        r.state.R = []
        seed(r, 1, np.array([1200., 300.]))
        act = r.choose_greedy_action()
        self.assertEqual(act['kind'], 'clear')
        r.clear(*act['point'], act['k'])
        self.assertIsNone(r.certified_clear_point(1))


if __name__ == '__main__':
    unittest.main()

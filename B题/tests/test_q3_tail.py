import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'simulator_automation')]
import q3_safe
from q3_runner import Q3Runner
from test_q3_certified_queue import Robot, seed


class TailTests(unittest.TestCase):
    def test_local_grid_covers_entire_rectangle_not_only_vertices(self):
        v = np.array([[-30., -10.], [30., -10.], [30., 10.], [-30., 10.]])
        points = q3_safe.local_cover_route(v, np.array([100., 0.]))
        self.assertLessEqual(len(points), 9)
        self.assertGreater(len(points), 0)
        for x in np.linspace(-30, 30, 41):
            for y in np.linspace(-10, 10, 21):
                self.assertLessEqual(min(np.linalg.norm(p - [x, y]) for p in points), 20.)

    def test_safe_clip_keeps_polygon_interior_and_edge(self):
        v = np.array([[-100., -100.], [100., -100.], [100., 100.], [-100., 100.]])
        self.assertTrue(q3_safe.cell_may_contain_target(np.array([0., 0.]), v))
        self.assertTrue(q3_safe.cell_may_contain_target(np.array([105., 0.]), v))
        self.assertFalse(q3_safe.cell_may_contain_target(np.array([300., 0.]), v))

    def test_tail_attempts_local_cover_before_safe_and_does_not_repeat(self):
        r = Q3Runner(Robot(False), 'GREEDY')
        r.state.R = []
        seed(r, 1, np.array([1200., 300.]))
        v = np.array([[1170., 290.], [1230., 290.], [1230., 310.], [1170., 310.]])
        with patch.object(r, 'posterior_vertices', return_value=v):
            act = r.choose_greedy_action()
            self.assertEqual(act['kind'], 'local_clear')
            r._execute_local_clear(act)
            self.assertLessEqual(len(r.robot.calls), 9)
            self.assertIsNone(r.choose_greedy_action())

    def test_large_region_does_not_allocate_local_grid(self):
        v = np.array([[-1000., -1000.], [1000., -1000.], [1000., 1000.]])
        self.assertEqual(q3_safe.local_cover_route(v, np.zeros(2)), [])


if __name__ == '__main__':
    unittest.main()

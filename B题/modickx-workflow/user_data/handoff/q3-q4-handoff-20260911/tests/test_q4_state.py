from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from params import CLEAR_RADIUS, NEAR_RADIUS  # noqa: E402
from q4_cover import P4_N, p4_points  # noqa: E402
from q4_policy import select_next_p4  # noqa: E402
from q4_state import (  # noqa: E402
    Q4State,
    near_physically_valid,
    optical_clear_ok,
    q4_no_signal_implies_beyond_r_min,
)


class Q4StateTests(unittest.TestCase):
    def test_single_no_signal_does_not_certify(self):
        st = Q4State()
        st.apply_measure(1, np.zeros(2), "no_signal")
        self.assertEqual(st.channels[1].status, "unseen")
        self.assertFalse(q4_no_signal_implies_beyond_r_min())

    def test_all_p4_no_signal_certifies_absent(self):
        st = Q4State()
        for p in p4_points():
            st.apply_measure(2, p, "no_signal")
        self.assertEqual(st.channels[2].status, "certified_absent")
        self.assertEqual(len(st.channels[2].no_signal_p4), P4_N)
        self.assertEqual(st.channels[2].remaining_p4(), [])

    def test_eighty_no_signal_not_absent(self):
        st = Q4State()
        for p in p4_points()[:80]:
            st.apply_measure(3, p, "no_signal")
        self.assertEqual(st.channels[3].status, "unseen")
        self.assertEqual(len(st.channels[3].remaining_p4()), 1)

    def test_visited_not_requeued(self):
        st = Q4State()
        p = p4_points()[0]
        st.apply_measure(4, p, "no_signal")
        before = set(st.channels[4].visited_p4)
        st.apply_measure(4, p, "no_signal")
        self.assertEqual(st.channels[4].visited_p4, before)
        self.assertEqual(len(st.channels[4].remaining_p4()), P4_N - 1)

    def test_direction_never_uses_q3_hex_as_absent(self):
        st = Q4State()
        hex_pt = np.array([600.0, 1200.0 * np.sin(np.pi / 3.0)])
        st.apply_measure(5, hex_pt, "no_signal")
        self.assertEqual(st.channels[5].status, "unseen")
        self.assertEqual(st.channels[5].no_signal_p4, set())

    def test_direction_then_no_signal_stays_detected(self):
        st = Q4State()
        origin = np.zeros(2)
        st.apply_measure(6, origin, "direction", svd_deg=0.0)
        self.assertEqual(st.channels[6].status, "detected")
        for p in p4_points()[1:]:
            st.apply_measure(6, p, "no_signal")
        self.assertEqual(st.channels[6].status, "detected")
        self.assertFalse(st.channels[6].can_certify_absent())

    def test_near_and_optical_clear_semantics(self):
        self.assertTrue(near_physically_valid(NEAR_RADIUS, True))
        self.assertFalse(near_physically_valid(NEAR_RADIUS, False))
        self.assertFalse(near_physically_valid(NEAR_RADIUS + 0.1, True))
        self.assertTrue(optical_clear_ok(CLEAR_RADIUS))
        self.assertFalse(optical_clear_ok(CLEAR_RADIUS + 0.1))
        st = Q4State()
        st.apply_measure(7, np.zeros(2), "near")
        self.assertEqual(st.channels[7].status, "detected")
        st.apply_clear(7, np.zeros(2), True)
        self.assertEqual(st.channels[7].status, "cleared")

    def test_select_next_skips_visited(self):
        st = Q4State()
        first = p4_points()[40]
        for k in range(1, 21):
            st.apply_measure(k, first, "no_signal")
        choice = select_next_p4(st)
        self.assertIsNotNone(choice)
        self.assertGreater(float(np.linalg.norm(choice.q - first)), 1.0)


if __name__ == "__main__":
    unittest.main()

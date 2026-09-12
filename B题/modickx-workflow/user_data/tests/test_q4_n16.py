"""Counting certificate: 16 distinct detections imply remaining channels empty."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "simulator_automation"))
sys.path.insert(0, str(ROOT / "tests"))

from params import SOURCE_COUNT_MAX  # noqa: E402
from q4_cover import COVER_HEX37, COVER_SQUARE81, set_cover_mode  # noqa: E402
from q4_policy import ROUTE_INSERT_V3, ROUTE_OLD, set_route_mode  # noqa: E402
from q4_runner import Q4Runner  # noqa: E402
from q4_state import Q4State, set_count_certify_n16  # noqa: E402
from test_q4_geomsim import GeomSim  # noqa: E402


class N16CountCertifyTests(unittest.TestCase):
    def setUp(self):
        set_count_certify_n16(True)

    def tearDown(self):
        set_count_certify_n16(True)
        set_cover_mode(COVER_SQUARE81)
        set_route_mode(ROUTE_OLD)

    def test_source_count_max_is_16(self):
        self.assertEqual(SOURCE_COUNT_MAX, 16)

    def test_fifteen_detections_do_not_certify_rest(self):
        st = Q4State()
        for k in range(1, 16):
            st.apply_measure(k, np.zeros(2), "direction", svd_deg=10.0)
        self.assertEqual(st.n_detected(), 15)
        self.assertEqual(st.channels[16].status, "unseen")
        self.assertEqual(st.channels[20].status, "unseen")

    def test_sixteen_detections_certify_remaining_unseen(self):
        st = Q4State()
        for k in range(1, 17):
            st.apply_measure(k, np.zeros(2), "direction", svd_deg=10.0)
        self.assertEqual(st.n_detected(), 16)
        for k in range(17, 21):
            self.assertEqual(st.channels[k].status, "certified_absent")
        self.assertEqual(st.channels[1].status, "detected")

    def test_detected_not_rewritten_absent(self):
        st = Q4State()
        st.apply_measure(1, np.zeros(2), "direction", svd_deg=0.0)
        for k in range(2, 17):
            st.apply_measure(k, np.zeros(2), "near")
        self.assertEqual(st.channels[1].status, "detected")
        self.assertFalse(st.channels[1].can_certify_absent())

    def test_disabled_flag_does_not_count_certify(self):
        set_count_certify_n16(False)
        st = Q4State()
        for k in range(1, 17):
            st.apply_measure(k, np.zeros(2), "near")
        self.assertEqual(st.channels[20].status, "unseen")

    def test_geomsim_sixteen_sources_can_skip_remaining_hex(self):
        set_cover_mode(COVER_HEX37)
        set_route_mode(ROUTE_INSERT_V3)
        sources = []
        rng = np.random.default_rng(7)
        for k in range(1, 17):
            ang = rng.uniform(0, 2 * np.pi)
            g = 400.0 * np.array([np.cos(ang), np.sin(ang)])
            sources.append({"k": k, "g": g, "r": 1200.0, "directional": False})
        summary = Q4Runner(GeomSim(sources)).run()
        self.assertEqual(summary["K"], 16)
        self.assertTrue(summary["all_certified"])
        self.assertEqual(len(summary["certified_absent"]), 4)
        self.assertLess(summary["n_cover_visited"], 37)


if __name__ == "__main__":
    unittest.main()

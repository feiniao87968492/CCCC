"""Smoke tests for the Q2 seed protocol. Does not run the full holdout set."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from q2_metrics import evaluate_case, summarize  # noqa: E402
from q2_scenario import (  # noqa: E402
    DEV_QUOTA,
    DEV_SEEDS,
    expand_quota,
    generate_scenario,
    iter_set,
)


class SeedProtocolTests(unittest.TestCase):
    def test_dev_quota_matches_seed_count(self):
        pairs = expand_quota(DEV_SEEDS, DEV_QUOTA)
        self.assertEqual(len(pairs), 20)
        self.assertEqual(pairs[0], (12000, "L1"))
        self.assertEqual(pairs[-1][1], "L8")

    def test_same_seed_is_reproducible(self):
        a = generate_scenario(12000, "L1")
        b = generate_scenario(12000, "L1")
        self.assertEqual(a.bearing_deg, b.bearing_deg)
        self.assertEqual(a.rejects, b.rejects)
        self.assertAlmostEqual(float(a.state.r), float(b.state.r))
        self.assertAlmostEqual(float(a.s[0]), float(b.s[0]))

    def test_one_dev_case_has_denominators_and_level1_fields(self):
        sc = generate_scenario(12000, "L1")
        row = evaluate_case(sc, n_azimuth=8, refine=False, with_legacy=False, with_ref=False, jitter=False)
        for key in (
            "truth_in_Z1",
            "truth_in_Zy",
            "F1_outer_contains_g",
            "core_false_guarantee",
            "clear_false_certificate",
            "same_r_violation",
            "J_star",
            "travel_s",
            "n_cand",
            "y2",
        ):
            self.assertIn(key, row)
        self.assertTrue(row["truth_in_Z1"])
        self.assertTrue(row["truth_in_Zy"])
        summary = summarize([row])
        self.assertEqual(summary["level1"]["n"], 1)
        self.assertIn("independent_unit", summary)
        self.assertEqual(summary["independent_unit"], "first_direction_plus_second_measure")

    def test_iter_dev_generates_all_strata(self):
        cases = iter_set("dev")
        self.assertEqual(len(cases), 20)
        names = {c.stratum for c in cases}
        self.assertEqual(names, {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"})


if __name__ == "__main__":
    unittest.main()

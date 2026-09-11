"""Offline checks for cleaning semantics, based on saved responses and perturbations."""
import json
from pathlib import Path
import tempfile
import unittest
from prepare import ROOT, clean_session


class CleaningTests(unittest.TestCase):
    def setUp(self):
        self.source = ROOT / 'simulator_automation/evidence/20260910-193359-p4/requests.jsonl'
        self.records = [json.loads(line) for line in self.source.read_text(encoding='utf-8').splitlines()]

    def run_records(self, records):
        # Keep the temporary fixture inside ROOT for the source provenance invariant.
        with tempfile.TemporaryDirectory(dir=ROOT / 'data_preparation') as directory:
            path = Path(directory) / 'requests.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in records), encoding='utf-8')
            return clean_session(path)

    def test_structural_missing_and_repeated_observations(self):
        rows, issues, summary = clean_session(self.source)
        self.assertEqual(issues, [])
        self.assertIsNone(rows[1]['bearing_deg'])
        self.assertEqual(rows[1]['bearing_missing_reason'], 'no_signal')
        self.assertTrue(rows[4]['repeated_site_channel'])
        self.assertEqual(rows[4]['bearing_deg'], 97.39)
        self.assertEqual(rows[3]['receiver_channel_after'], 2)
        self.assertEqual(summary['final_virtual_time_s'], 19)
        self.assertIsNone(summary['mean_clear_time_s'])

    def test_identical_replay_does_not_charge_twice(self):
        self.records.insert(3, self.records[2])
        rows, issues, summary = self.run_records(self.records)
        self.assertEqual(issues, [])
        self.assertTrue(rows[3]['idempotent_replay'])
        self.assertEqual(summary['unique_accepted_actions'], 6)
        self.assertEqual(summary['final_virtual_time_s'], 19)

    def test_rejected_zero_does_not_reset_clock(self):
        rejected = json.loads(json.dumps(self.records[2]))
        rejected['request']['request_id'] = 'rejected-example'
        rejected['response'] = dict(accepted=False, real_timestamp_ms=1789040039602, virtual_time_s=0)
        self.records.insert(3, rejected)
        rows, issues, summary = self.run_records(self.records)
        self.assertEqual(issues, [])
        self.assertEqual(rows[3]['effective_virtual_time_s'], 11)
        self.assertEqual(summary['final_virtual_time_s'], 19)

    def test_invalid_direction_quarantines_session(self):
        self.records[2]['response']['svd_deg'] = 360
        rows, issues, summary = self.run_records(self.records)
        self.assertEqual(rows, [])
        self.assertIsNone(summary)
        self.assertEqual(issues[0]['source_line'], 3)

    def test_wrong_clear_switch_charge_is_detected(self):
        self.records[3]['response']['virtual_time_s'] += 1
        rows, issues, _ = self.run_records(self.records)
        self.assertEqual(rows, [])
        self.assertIn('Timing mismatch', issues[0]['error'])


if __name__ == '__main__':
    unittest.main()

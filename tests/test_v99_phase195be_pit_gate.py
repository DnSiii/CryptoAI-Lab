"""Read-only PIT gate tests; live archive assertions opt-in via env paths."""
import os
import unittest
from scripts.v99_phase195be_pit_gate import utc, causal_start, scan, read, compare


class PITGate(unittest.TestCase):
    def test_utc(self):
        with self.assertRaises(ValueError):
            utc('2026-10-10T06:00:00')

    def test_tminus1(self):
        self.assertEqual(causal_start('2026-10-10T06:23:00+00:00').hour, 8)

    def test_bad_decision(self):
        u = {'symbols': {'XUSDT': {'source': 'dynamic_binance_discovery',
             'discovered_at_utc': '2026-10-10T06:23:00+00:00',
             'eligible_after_timestamp': '2026-10-10T05:00:00+00:00'}}}
        l = {'mode': 'PAPER_ONLY', 'decisions': [
             {'timestamp': '2026-10-10T07:00:00+00:00', 'adjustments': [{'symbol': 'XUSDT'}]}]}
        self.assertEqual(len(scan(u, l)['unsafe_observed']), 1)

    def test_good_decision(self):
        u = {'symbols': {'XUSDT': {'source': 'dynamic_binance_discovery',
             'discovered_at_utc': '2026-10-10T06:23:00+00:00',
             'eligible_after_timestamp': '2026-10-10T08:00:00+00:00'}}}
        l = {'mode': 'PAPER_ONLY', 'decisions': [
             {'timestamp': '2026-10-10T08:00:00+00:00', 'adjustments': [{'symbol': 'XUSDT'}]}]}
        self.assertEqual(scan(u, l)['status'], 'OBSERVED_ONLY_PASS_NOT_CERTIFICATION')

    def test_real_archives_when_available(self):
        old, new = os.environ.get('V99_BE_ARTIFACT_OLD'), os.environ.get('V99_BE_ARTIFACT_NEW')
        if not old or not new:
            self.skipTest('Live artifact ZIP paths not provided')
        result = compare(read(old), read(new))
        self.assertEqual(result['decision'], 'DATA_ONLY_HOLD')
        self.assertFalse(result['promotion_authorized'])


if __name__ == '__main__':
    unittest.main()

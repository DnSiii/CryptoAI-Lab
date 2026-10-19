"""Adversarial structural history gate tests; fixtures are invented."""
import unittest
from research.tools.v99_r106_d1_paired_history_cycle61 import (
    assess_paired_hourly_coverage as assess, REQUIRED, START_MS, HOUR_MS, EXPECTED,
)

def candle(i, confirm='1'):
    return [str(START_MS+i*HOUR_MS), '100','101','99','100','1','1','1',confirm]

def fixture(hours=5):
    return {inst:[candle(i) for i in range(hours)] for inst in REQUIRED}

class PairedHistoryGateTests(unittest.TestCase):
    def test_missing_instruments(self):
        r=assess({}); self.assertEqual(r['paired_four_leg_hours'],0)
        self.assertEqual(r['paired_four_leg_missing_hours'],EXPECTED)
    def test_partial_prefix(self):
        r=assess(fixture()); self.assertEqual(r['paired_four_leg_hours'],5)
        self.assertFalse(r['complete_structural_coverage'])
    def test_duplicate_does_not_inflate_coverage(self):
        x=fixture(); x[REQUIRED[0]].append(candle(0))
        r=assess(x); self.assertEqual(r['paired_four_leg_hours'],4)
        self.assertEqual(r['per_instrument'][REQUIRED[0]]['duplicate_hours'],1)
    def test_unconfirmed_hour_rejected(self):
        x=fixture(); x[REQUIRED[1]][2]=candle(2,'0')
        self.assertEqual(assess(x)['paired_four_leg_hours'],4)
    def test_malformed_price_rejected(self):
        x=fixture(); x[REQUIRED[2]][1][2]='50'
        self.assertEqual(assess(x)['paired_four_leg_hours'],4)
    def test_nonfinite_price_rejected(self):
        x=fixture(); x[REQUIRED[2]][1][1]='NaN'
        self.assertEqual(assess(x)['paired_four_leg_hours'],4)
    def test_future_does_not_count(self):
        x=fixture(); x[REQUIRED[3]].append(candle(EXPECTED+100))
        r=assess(x); self.assertEqual(r['paired_four_leg_hours'],5)
        self.assertEqual(r['per_instrument'][REQUIRED[3]]['outside_train_rows'],1)
    def test_nonhourly_rejected(self):
        x=fixture(); x[REQUIRED[0]][0][0]=str(START_MS+1)
        with self.assertRaisesRegex(ValueError,'NON_HOURLY'):
            assess(x)
    def test_invalid_timestamp_rejected(self):
        x=fixture(); x[REQUIRED[0]][0][0]='NaN'
        with self.assertRaisesRegex(ValueError,'BAD_TIMESTAMP'):
            assess(x)
    def test_missing_hour_not_masked_by_extra_rows(self):
        x=fixture(); x[REQUIRED[0]].pop(3); x[REQUIRED[0]].append(candle(5))
        self.assertEqual(assess(x)['paired_four_leg_hours'],4)
    def test_permutation_independence(self):
        x=fixture(); x[REQUIRED[0]].reverse()
        self.assertEqual(assess(x)['paired_four_leg_hours'],5)
    def test_full_synthetic_structural_not_authentication(self):
        x=fixture(EXPECTED); r=assess(x)
        self.assertTrue(r['complete_structural_coverage'])
        self.assertEqual(r['paired_four_leg_hours'],EXPECTED)
        self.assertFalse(r['historical_economics_authorized'])
        self.assertFalse(r['validation_opened'])
        self.assertFalse(r['promotion_authorized'])

if __name__=='__main__': unittest.main()

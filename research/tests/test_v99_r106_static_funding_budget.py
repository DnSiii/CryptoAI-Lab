"""Adversarial controls for preregistered funding-rate source binding, NOT trading PnL."""
import math
import unittest
from research.tools.v99_r106_static_funding_budget import bind_original_events, STEP

class OriginalFundingClockAndCoverage(unittest.TestCase):
    def setUp(self):
        self.start = 40 * STEP
        self.end = self.start + 2 * STEP
        self.rows = [(self.start+31,8.,.0001),(self.start+STEP,8.,-.0002)]

    def test_valid_original_0_to_31ms_bind_without_backdating_signal(self):
        x=bind_original_events(self.rows,self.start,self.end)
        self.assertEqual(set(x),{self.start,self.start+STEP})
        self.assertEqual(x[self.start],(.0001,31))
        self.assertEqual(x[self.start+STEP],(-.0002,0))

    def test_32ms_is_not_silently_snapped(self):
        bad=[(self.start+32,8.,.0001),self.rows[1]]
        with self.assertRaisesRegex(ValueError,"invalid_native_event_clock_offset"):
            bind_original_events(bad,self.start,self.end)

    def test_duplicate_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate_native_funding_event"):
            bind_original_events(self.rows+[(self.start+2,8.,.0003)],self.start,self.end)

    def test_missing_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing_native_funding_events"):
            bind_original_events(self.rows[:1],self.start,self.end)

    def test_nonfinite_rate_and_wrong_interval_rejected(self):
        for row in ((self.start,8.,math.nan),(self.start,8.,math.inf),
                    (self.start,4.,.0001)):
            with self.subTest(row=row),self.assertRaises(ValueError):
                bind_original_events([row,self.rows[1]],self.start,self.end)

    def test_negative_original_funding_is_not_clipped(self):
        x=bind_original_events(self.rows,self.start,self.end)
        self.assertLess(x[self.start+STEP][0],0)
        self.assertLess(sum(v[0] for v in x.values()),0)

if __name__=="__main__":
    unittest.main()

#!/usr/bin/env python3
"""Y complete-portfolio synthetic receipt, determinism and no-holdout gates."""
import unittest
from phase1127_y_synthetic_integration import run,SEEDS
from phase1125_y_sevenslot_source import PATHS

class TestYIntegrated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=run(SEEDS[0],n=1900)
    def test_all_five_paths_and_no_holdout(self):
        self.assertEqual(tuple(self.result['results']),PATHS)
        for key in ('historical_pnl_computed','validation_2025_read','external_benchmarks_used'):
            self.assertFalse(self.result[key])
    def test_first_failure_receipt_not_silenced(self):
        for path,v in self.result['results'].items():
            if v['ok']:
                self.assertIsNone(v['first_failure'])
                self.assertEqual(v['processed_hours'],1900-721)
            else:
                self.assertIsInstance(v['first_failure']['reason'],str)
                self.assertLess(v['processed_hours'],1900-721)
    def test_repeat_deterministic(self):
        again=run(SEEDS[0],n=1900)
        self.assertEqual(self.result,again)
if __name__=='__main__':unittest.main()

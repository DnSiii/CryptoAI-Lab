import unittest
from phase1200_ad_crisis_90cell import crisis_fixture,run


class CrisisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=run()

    def test_exact_ninety_crisis_cells_survive(self):
        self.assertEqual(len(self.receipt['cells']),90)
        self.assertTrue(all(c['passed'] for c in self.receipt['cells']))

    def test_actual_nav_stress_activates(self):
        c=next(c for c in self.receipt['cells'] if c['path']=='AD_full'
               and c['mode']=='immediate' and c['fee']=='base'
               and c['order']=='carried_before_fill')
        self.assertGreater(c['active_hours']['stress'],0)

    def test_no_historical_pnl_or_holdout(self):
        self.assertFalse(self.receipt['historical_system_pnl_computed'])
        self.assertFalse(self.receipt['validation_2025_read'])
        self.assertFalse(self.receipt['external_benchmarks_used'])

    def test_shock_fixture_has_realized_crash_and_recovery(self):
        frames,_=crisis_fixture()
        c=frames[3].to_numpy(float)
        self.assertLess(c[810,0]/c[809,0],.60)
        self.assertGreater(c[850,0]/c[849,0],1.7)


if __name__=='__main__':unittest.main()

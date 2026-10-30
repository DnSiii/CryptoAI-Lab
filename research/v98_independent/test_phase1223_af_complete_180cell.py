import unittest
from phase1223_af_complete_180cell import run,PATHS,MODES,FEES,ORDERS


class AFCompleteSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=run()

    def test_exact_180_cell_geometry(self):
        cells=self.receipt['cells']
        self.assertEqual(len(cells),180)
        for name in ('benign','crisis'):
            subset=[x for x in cells if x['fixture']==name]
            self.assertEqual(len(subset),90)
            self.assertEqual(len({(x['path'],x['mode'],x['fee'],x['order'])
                                  for x in subset}),
                             len(PATHS)*len(MODES)*len(FEES)*len(ORDERS))

    def test_every_cell_survives_actual_cash_and_causal_risk(self):
        self.assertEqual(sum(x['passed'] for x in self.receipt['cells']),180)
        self.assertEqual(self.receipt['decision'],
                         'PASS_AF_180_CAUSAL_SYNTHETIC_NOT_ECONOMIC')

    def test_every_cell_executes_180_hours(self):
        for x in self.receipt['cells']:
            self.assertTrue(x['passed'],x.get('reason',''))
            self.assertEqual(x['hours_executed'],180)
            self.assertGreater(x['synthetic_final_nav'],0)

    def test_crisis_actual_nav_cash_reserve_activates(self):
        x=next(x for x in self.receipt['cells'] if x['fixture']=='crisis'
               and x['path']=='AF_full' and x['mode']=='immediate'
               and x['fee']=='base' and x['order']=='carried_before_fill')
        self.assertGreater(x['active_hours']['stress_cash'],0)

    def test_no_historical_pnl_or_future_holdout(self):
        self.assertFalse(self.receipt['historical_system_pnl_computed'])
        self.assertFalse(self.receipt['validation_2025_read'])
        self.assertFalse(self.receipt['external_benchmarks_used'])


if __name__=='__main__':unittest.main()

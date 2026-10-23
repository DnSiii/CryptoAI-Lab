import unittest
from phase1211_ae_complete_180cell import run,PATHS,MODES,FEES,ORDERS


class AECompleteCausalSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=run()

    def test_all_180_cells_present(self):
        cells=self.receipt['cells']
        self.assertEqual(len(cells),180)
        for fixture in ('benign','crisis'):
            group=[x for x in cells if x['fixture']==fixture]
            self.assertEqual(len(group),90)
            keys={(x['path'],x['mode'],x['fee'],x['order']) for x in group}
            self.assertEqual(len(keys),len(PATHS)*len(MODES)*len(FEES)*len(ORDERS))

    def test_all_180_causal_execution_gates(self):
        self.assertEqual(sum(x['passed'] for x in self.receipt['cells']),180)
        self.assertEqual(self.receipt['decision'],
                         'PASS_AE_180_CAUSAL_SYNTHETIC_NOT_ECONOMIC')

    def test_every_cell_has_180_actual_hours(self):
        for x in self.receipt['cells']:
            self.assertTrue(x['passed'],x.get('reason',''))
            self.assertEqual(x['hours_executed'],180)
            self.assertGreater(x['synthetic_final_nav'],0)

    def test_crisis_actual_nav_stress_activated(self):
        x=next(x for x in self.receipt['cells'] if x['fixture']=='crisis'
               and x['path']=='AE_full' and x['mode']=='immediate'
               and x['fee']=='base' and x['order']=='carried_before_fill')
        self.assertGreater(x['active_hours']['stress'],0)

    def test_never_historical_pnl_or_holdout(self):
        self.assertFalse(self.receipt['historical_system_pnl_computed'])
        self.assertFalse(self.receipt['validation_2025_read'])
        self.assertFalse(self.receipt['external_benchmarks_used'])


if __name__=='__main__':unittest.main()

import itertools
import unittest
import numpy as np
from phase1198_ad_complete_synthetic import (
    PATHS,MODES,FEES,ORDERS,fixture,source_slots,one_cell,run)


class FullSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=run()

    def test_exact_ninety_unique_cells(self):
        cells=self.receipt['cells']
        self.assertEqual(len(cells),90)
        self.assertEqual(len({(c['path'],c['mode'],c['fee'],c['order']) for c in cells}),90)
        self.assertEqual(len(list(itertools.product(PATHS,MODES,FEES,ORDERS))),90)

    def test_all_synthetic_survive_and_no_historical_pnl(self):
        self.assertTrue(all(c['passed'] for c in self.receipt['cells']))
        self.assertFalse(self.receipt['historical_system_pnl_computed'])
        self.assertFalse(self.receipt['validation_2025_read'])
        self.assertFalse(self.receipt['external_benchmarks_used'])

    def test_cash_and_fee_accounting_nontrivial(self):
        self.assertTrue(all(c['synthetic_final_nav']>0 for c in self.receipt['cells']))
        self.assertTrue(any(c['synthetic_fees']>0 for c in self.receipt['cells']))
        self.assertTrue(any(c['synthetic_turnover']>0 for c in self.receipt['cells']))

    def test_source_ablation_never_mutates_other_paths(self):
        frames,*marks=fixture()
        slots=source_slots(frames)
        rv_before=slots[3].copy()
        op_before=slots[2].copy()
        one_cell('AD_core_only','immediate','base',ORDERS[0],frames,marks,slots)
        np.testing.assert_array_equal(slots[3],rv_before)
        np.testing.assert_array_equal(slots[2],op_before)

    def test_opportunity_and_rv_active_in_full(self):
        full=next(c for c in self.receipt['cells'] if c['path']=='AD_full'
                  and c['mode']=='immediate' and c['fee']=='base' and c['order']==ORDERS[0])
        self.assertGreater(full['active_hours']['opportunity'],0)
        self.assertGreater(full['active_hours']['relative_value'],0)


if __name__=='__main__':unittest.main()

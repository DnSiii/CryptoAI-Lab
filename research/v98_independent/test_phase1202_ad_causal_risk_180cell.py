import unittest
from phase1202_ad_causal_risk_180cell import run


class CausalRiskRejectionAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=run()

    def test_all_one_hundred_eighty_preserved(self):
        cells=self.receipt['cells']
        self.assertEqual(len(cells),180)
        self.assertEqual(sum(c['passed'] for c in cells),90)
        self.assertEqual(sum(not c['passed'] for c in cells),90)

    def test_benign_survives_crisis_fails(self):
        cells=self.receipt['cells']
        self.assertTrue(all(c['passed'] for c in cells if c['fixture']=='benign'))
        self.assertTrue(all(not c['passed'] for c in cells if c['fixture']=='crisis'))

    def test_full_candidate_crisis_first_failure_not_hidden(self):
        c=next(c for c in self.receipt['cells'] if c['fixture']=='crisis'
               and c['path']=='AD_full' and c['mode']=='immediate'
               and c['fee']=='base' and c['order']=='carried_before_fill')
        self.assertIn('AD1196_UNEXECUTABLE_CARRIED_INVENTORY',c['reason'])
        self.assertIn('AD1202_T877_',c['reason'])

    def test_no_historical_pnl_or_promotion(self):
        self.assertEqual(self.receipt['decision'],'REJECT_AD_CAUSAL_RISK_SYNTHETIC_NO_PNL')
        self.assertFalse(self.receipt['historical_system_pnl_computed'])
        self.assertFalse(self.receipt['validation_2025_read'])
        self.assertFalse(self.receipt['external_benchmarks_used'])


if __name__=='__main__':unittest.main()

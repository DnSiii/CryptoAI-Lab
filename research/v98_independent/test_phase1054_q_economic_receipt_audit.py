import unittest
from phase1054_q_economic_receipt_audit import audit
from phase1051_q_training_gate import PATHS,FEE_TIERS,ORDERS,CAPITAL_MODES

class QReceiptTests(unittest.TestCase):
    def fake(self):
        cases={}
        for p in PATHS:
            cases[p]={}
            for t in FEE_TIERS:
                cases[p][t]={}
                for o in ORDERS:
                    cases[p][t][o]={m:{'survived':False,'reason':'Q_SYNTHETIC_REJECTION','breach_index':100} for m in CAPITAL_MODES}
        failures=[{'reason':'Q_SYNTHETIC_REJECTION'} for _ in range(90)]
        return {'phase':1051,'decision':'REJECT_Q_TRAINING_NO_RESCUE','historical_pnl_computed':True,
                'ledger_invocations':90,'matrix':{'cells_attempted':90,'cells_survived':0,'failures':failures,'cases':cases}}
    def test_honest_90_rejection_accepted_not_promoted(self):
        x=audit(self.fake());self.assertTrue(x['passed']);self.assertFalse(x['economic_approval']);self.assertEqual(x['cells_failed'],90)
    def test_missing_cell_rejected(self):
        r=self.fake();del r['matrix']['cases']['Q_full']['base']['carried_before_fill']['immediate']
        self.assertFalse(audit(r)['passed'])
    def test_inconsistent_promotion_rejected(self):
        r=self.fake();r['decision']='PASS_Q_TRAINING_PENDING_2025_VALIDATION'
        self.assertFalse(audit(r)['passed'])
    def test_no_economics_rejected(self):
        r=self.fake();r['historical_pnl_computed']=False
        self.assertFalse(audit(r)['passed'])

if __name__=='__main__':unittest.main()

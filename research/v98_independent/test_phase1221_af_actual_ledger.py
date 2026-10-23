import unittest
import numpy as np
from phase1221_af_actual_ledger import (
    execute_hour,native_funding_cash,FEES,SLIPPAGE)


def args():
    return dict(prior_close=np.full(4,100.),opening=np.full(4,100.),
        high=np.full(4,101.),low=np.full(4,99.),closing=np.full(4,100.),
        cash=10000.,old_units=np.zeros(4),desired_weights=np.array([.1,.1,0,0]),
        down=np.full(4,.35),up=np.full(4,.45),
        funding_bound=np.full(4,.006),prior_quote=np.full(4,1e9),
        min_quote=np.full(4,1e9),fee='base',
        funding_rate=np.zeros(4),mark_low=np.full(4,np.nan),
        mark_high=np.full(4,np.nan),funding_event=np.zeros(4),
        order='carried_before_fill')


class AFActualLedgerTests(unittest.TestCase):
    def test_exact_cash_and_inventory_reconciliation(self):
        x=args()
        r=execute_hour(**x)
        delta=r['units']-x['old_units']
        execution=x['opening']*(1+np.sign(delta)*SLIPPAGE)
        self.assertAlmostEqual(r['cash'],x['cash']-delta@execution-r['fees'],places=8)
        self.assertAlmostEqual(r['equity'],r['cash']+r['units']@x['closing'])
        self.assertTrue(r['actual_execution_proven'])

    def test_three_actual_fee_schedules(self):
        nav=[]
        for fee in FEES:
            x=args()
            x['fee']=fee
            nav.append(execute_hour(**x)['equity'])
        self.assertGreater(nav[0],nav[1])
        self.assertGreater(nav[1],nav[2])

    def test_carried_and_new_funding_are_distinct(self):
        x=args()
        x['cash']=9900.
        x['old_units'][0]=1.
        x['desired_weights']=np.zeros(4)
        x['funding_rate'][0]=.01
        x['funding_event'][0]=1
        x['mark_low'][0]=99
        x['mark_high'][0]=101
        a=execute_hour(**x)
        x['order']='new_after_fill'
        b=execute_hour(**x)
        self.assertAlmostEqual(a['funding_cash_delta'],-1.01)
        self.assertEqual(b['funding_cash_delta'],0)
        self.assertLess(a['equity'],b['equity'])

    def test_signed_payer_and_receiver_native_marks(self):
        u=np.array([1.,1.,0.,0.])
        rate=np.array([.01,-.01,0.,0.])
        event=np.array([1.,1.,0.,0.])
        low=np.array([99.,99.,np.nan,np.nan])
        high=np.array([101.,101.,np.nan,np.nan])
        self.assertAlmostEqual(native_funding_cash(u,rate,event,low,high),-.02)

    def test_bad_native_mark_rejected(self):
        with self.assertRaisesRegex(ValueError,'NATIVE_MARK'):
            native_funding_cash(np.ones(4),np.array([.01,0,0,0]),
                                np.array([1,0,0,0]),
                                np.full(4,np.nan),np.full(4,np.nan))

    def test_no_margin_loan_or_short_inventory(self):
        x=args()
        x['cash']=-1.
        with self.assertRaisesRegex(ValueError,'PRICE_OR_COLLATERAL'):
            execute_hour(**x)
        x=args()
        x['old_units'][0]=-1.
        with self.assertRaisesRegex(ValueError,'PRICE_OR_COLLATERAL'):
            execute_hour(**x)

    def test_realized_intrabar_excess_is_hard_failure(self):
        x=args()
        x['desired_weights']=np.array([.25,0,0,0])
        x['high'][0]=500.
        with self.assertRaisesRegex(ValueError,'ACTUAL_INTRABAR_81_CORNER'):
            execute_hour(**x)

    def test_unexitable_carried_inventory_hard_failure(self):
        x=args()
        x['cash']=9900.
        x['old_units'][0]=1.
        x['desired_weights']=np.zeros(4)
        x['prior_quote'][0]=0
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_CARRIED_EXIT'):
            execute_hour(**x)

    def test_no_historical_pnl_claim(self):
        r=execute_hour(**args())
        self.assertFalse(r['historical_system_pnl_computed'])


if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from phase1210_ae_actual_open_executor import (
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


class AEActualOpenExecutorTests(unittest.TestCase):
    def test_self_financing_actual_cash_and_fee(self):
        x=args()
        r=execute_hour(**x)
        delta=r['units']-x['old_units']
        execution=x['opening']*(1+np.sign(delta)*SLIPPAGE)
        expected=x['cash']-delta@execution-r['fees']
        self.assertAlmostEqual(r['cash'],expected,places=8)
        self.assertAlmostEqual(r['equity'],r['cash']+r['units']@x['closing'])
        self.assertAlmostEqual(r['fees'],r['turnover']*FEES['base'])
        self.assertTrue(r['actual_execution_proven'])

    def test_all_three_cost_schedules_reduce_nav(self):
        values=[]
        for fee in FEES:
            x=args()
            x['fee']=fee
            values.append(execute_hour(**x)['equity'])
        self.assertGreater(values[0],values[1])
        self.assertGreater(values[1],values[2])

    def test_carried_vs_new_native_funding_timing(self):
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
        self.assertAlmostEqual(a['funding_cash_delta'],-1.01,places=12)
        self.assertEqual(b['funding_cash_delta'],0.)
        self.assertLess(a['equity'],b['equity'])

    def test_signed_native_funding_uses_conservative_mark(self):
        u=np.array([1.,-1.,0.,0.])
        r=np.array([.01,.01,0.,0.])
        e=np.array([1.,1.,0.,0.])
        lo=np.array([99.,99.,np.nan,np.nan])
        hi=np.array([101.,101.,np.nan,np.nan])
        self.assertAlmostEqual(native_funding_cash(u,r,e,lo,hi),-2.,places=12)

    def test_reject_native_mark_mismatch(self):
        with self.assertRaisesRegex(ValueError,'NATIVE_FUNDING_MARK'):
            native_funding_cash(np.ones(4),np.array([.01,0,0,0]),
                                np.array([1,0,0,0]),
                                np.array([np.nan]*4),np.array([101.,np.nan,np.nan,np.nan]))

    def test_gap_insolvency_not_covered_by_free_stop(self):
        x=args()
        x['cash']=-2000.
        x['old_units'][0]=100.
        x['opening'][0]=10.
        x['low'][0]=9.
        x['high'][0]=101.
        with self.assertRaisesRegex(ValueError,'OPEN_GAP_INSOLVENCY'):
            execute_hour(**x)

    def test_actual_intrabar_excess_not_used_for_order_selection(self):
        x=args()
        x['desired_weights']=np.array([-.2,0,0,0])
        x['high'][0]=500.
        with self.assertRaisesRegex(ValueError,'ACTUAL_INTRABAR_81_CORNER'):
            execute_hour(**x)

    def test_carried_exit_capacity_hard_failure(self):
        x=args()
        x['cash']=9900.
        x['old_units'][0]=1.
        x['desired_weights']=np.zeros(4)
        x['prior_quote'][0]=0
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_CARRIED_EXIT'):
            execute_hour(**x)

    def test_no_historical_pnl_promotion(self):
        r=execute_hour(**args())
        self.assertFalse(r['historical_system_pnl_computed'])


if __name__=='__main__':unittest.main()

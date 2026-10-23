import unittest
import numpy as np
from phase1197_ad_actual_open_executor import execute_hour,funding_cash


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.p=np.full(4,100.)
        self.old=np.zeros(4)
        self.kw=dict(prior_close=self.p,opening=self.p,high=self.p*1.01,
            low=self.p*.99,closing=self.p,cash=10000.,old_units=self.old,
            desired_weights=np.full(4,.02),down=np.full(4,.25),up=np.full(4,.30),
            funding_bound=np.full(4,.005),prior_quote=np.full(4,1e7),
            min_quote=np.full(4,1e7),fee='base',funding_rate=np.zeros(4),
            mark_low=np.full(4,np.nan),mark_high=np.full(4,np.nan),
            funding_event=np.zeros(4),order='carried_before_fill')

    def test_cash_self_financing_and_cost(self):
        r=execute_hour(**self.kw)
        self.assertGreater(r['turnover'],0)
        self.assertAlmostEqual(r['equity'],10000-r['fees']-.003*r['turnover'],places=7)
        self.assertAlmostEqual(r['cash']+r['units']@self.p,r['equity'],places=8)

    def test_flat_remains_flat(self):
        self.kw['desired_weights']=np.zeros(4)
        r=execute_hour(**self.kw)
        self.assertEqual(r['turnover'],0)
        self.assertEqual(r['equity'],10000)

    def test_signed_long_funding_payer_uses_high(self):
        cash=funding_cash(np.array([2.,0,0,0]),np.array([.01,0,0,0]),
                          np.array([1,0,0,0]),np.array([99.,np.nan,np.nan,np.nan]),
                          np.array([101.,np.nan,np.nan,np.nan]))
        self.assertAlmostEqual(cash,-2.02)

    def test_signed_short_funding_receiver_uses_low(self):
        cash=funding_cash(np.array([-2.,0,0,0]),np.array([.01,0,0,0]),
                          np.array([1,0,0,0]),np.array([99.,np.nan,np.nan,np.nan]),
                          np.array([101.,np.nan,np.nan,np.nan]))
        self.assertAlmostEqual(cash,1.98)

    def test_no_funding_without_event(self):
        self.assertEqual(funding_cash(np.ones(4),np.zeros(4),np.zeros(4),
            np.full(4,np.nan),np.full(4,np.nan)),0.)

    def test_bad_native_mark_fails_closed(self):
        self.kw['funding_rate']=np.array([.01,0,0,0])
        self.kw['funding_event']=np.array([1,0,0,0])
        with self.assertRaisesRegex(ValueError,'NATIVE_MARK'):
            execute_hour(**self.kw)

    def test_unexecutable_open_gap_rejected(self):
        self.kw['old_units']=np.full(4,50.)
        self.kw['cash']=-19900.
        self.kw['prior_close']=np.full(4,100.)
        self.kw['opening']=np.full(4,1.)
        self.kw['high']=np.full(4,101.)
        self.kw['low']=np.full(4,1.)
        with self.assertRaisesRegex(ValueError,'OPEN_GAP_INSOLVENCY'):
            execute_hour(**self.kw)

    def test_intrabar_short_squeeze_rejected(self):
        self.kw['high']=self.p*3
        self.kw['desired_weights']=np.full(4,-.05)
        with self.assertRaisesRegex(ValueError,'INTRABAR'):
            execute_hour(**self.kw)

    def test_order_flags_rejected(self):
        self.kw['order']='unknown'
        with self.assertRaisesRegex(ValueError,'INPUT'):
            execute_hour(**self.kw)


if __name__=='__main__':unittest.main()

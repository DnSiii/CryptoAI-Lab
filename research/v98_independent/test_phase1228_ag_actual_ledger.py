#!/usr/bin/env python3
"""V98 AG1228 signed native funding and actual ledger unit gates."""
import unittest
import numpy as np
from phase1228_ag_actual_ledger import native_funding,execute_hour


class TestAGLedger(unittest.TestCase):
    def setUp(self):
        self.p=np.array([100.,150.,50.,200.])
        self.q=np.full(4,1e12)
        self.mu=np.array([.04,.035,.025,.03])
        self.d=np.full(4,.25)
        self.u=np.full(4,.25)
        self.f=np.full(4,.002)

    def hour(self,order='carried_before_fill',scheduled=True,event=None,
             units=None,cash=10000.,rate=None):
        if units is None:units=np.zeros(4)
        if event is None:event=np.zeros(4)
        if rate is None:rate=np.zeros(4)
        return execute_hour(units,cash,self.p,self.p*1.0001,
             self.p*.9999,self.p,self.mu,.10,self.d,self.u,self.f,
             self.q,self.q,'base',rate,event,self.p*.99,
             self.p*1.01,order,scheduled)

    def test_signed_funding_and_conservative_marks(self):
        u=np.array([1.,2.,3.,4.])
        r=np.array([.001,-.001,.002,-.002])
        e=np.ones(4)
        expected=-(1*101*.001+2*148.5*(-.001)+
                   3*50.5*.002+4*198*(-.002))
        self.assertAlmostEqual(native_funding(u,r,e,self.p*.99,
                               self.p*1.01),expected)

    def test_zero_funding_no_nan_mark_issue(self):
        self.assertEqual(native_funding(np.ones(4),np.zeros(4),
            np.zeros(4),np.full(4,np.nan),np.full(4,np.nan)),0.)

    def test_order_timing_changes_cash_only_causally(self):
        old=np.array([5.,2.,8.,1.])
        rate=np.array([.0001,-.0001,.00015,-.00015])
        a=self.hour(units=old,cash=7000.,rate=rate,event=np.ones(4))
        b=self.hour('new_after_fill',units=old,cash=7000.,
                    rate=rate,event=np.ones(4))
        self.assertNotEqual(a['funding'],b['funding'])
        self.assertTrue(a['nav']>0 and b['nav']>0)

    def test_reconcile_and_carry(self):
        a=self.hour()
        b=self.hour(scheduled=False,units=a['units'],cash=a['cash'])
        self.assertAlmostEqual(b['cash']+b['units']@self.p,b['nav'],places=6)
        self.assertGreaterEqual(b['cash'],-1e-8)
        self.assertTrue(np.all(b['units']>=0))

    def test_no_imaginary_carry_exit(self):
        old=np.array([85.,0.,0.,0.])
        with self.assertRaisesRegex(ValueError,'NO_JOINT_FEASIBLE'):
            execute_hour(old,1500.,self.p,self.p*1.0001,self.p*.9999,
                self.p,self.mu,.1,self.d,self.u,self.f,np.zeros(4),
                self.q,'base',np.zeros(4),np.zeros(4),self.p*.99,
                self.p*1.01,'carried_before_fill',True)


if __name__=='__main__':
    unittest.main()

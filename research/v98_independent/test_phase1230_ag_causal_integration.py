#!/usr/bin/env python3
"""V98 AG Phase1230 independent t-1 integration and fixture integrity audit."""
import unittest
import numpy as np
from phase1229_ag_complete_180cell import fixture,prior_risk
from phase1227_ag_seven_slot_sources import causal_sources
from phase1228_ag_actual_ledger import execute_hour


class TestAGCausalIntegration(unittest.TestCase):
    def test_source_and_risk_future_perturbation(self):
        a=fixture(False)
        src=causal_sources(a[3],a[4])
        risk=prior_risk(a[0],a[1],a[2],a[4],a[5],a[6])
        b=[x.copy() for x in a]
        for k in (0,1,2,3,4):
            b[k][800:]*=np.array([2.,.5,4.,.3])
        src2=causal_sources(b[3],b[4])
        risk2=prior_risk(b[0],b[1],b[2],b[4],b[5],b[6])
        for x,y in zip(src,src2):
            self.assertTrue(np.array_equal(x[:799],y[:799]))
        for x,y in zip(risk,risk2):
            self.assertTrue(np.array_equal(x[:800],y[:800]))

    def test_exact_synthetic_crisis_and_native_events(self):
        benign=fixture(False)
        crisis=fixture(True)
        for k in (4,5,6):
            self.assertTrue(np.array_equal(benign[k],crisis[k]))
        self.assertTrue(np.allclose(crisis[3][810]/benign[3][810],.55))
        self.assertTrue(np.allclose(crisis[3][850]/benign[3][850],.99))
        self.assertEqual(int(np.sum(benign[6][:,0])),113)
        self.assertTrue(np.all(benign[6][1::8]==0))
        self.assertTrue(np.all(benign[6][::8]==1))

    def test_current_bar_extremes_cannot_change_order(self):
        a=fixture(False)
        p=a[0][720]
        kwargs=dict(old_units=np.zeros(4),cash=10000.,
            opening=p,closing=p,growth_mu=np.array([.04,.03,.02,.01]),
            cash_reserve=.1,down=np.full(4,.4),up=np.full(4,.4),
            funding_bound=np.full(4,.002),
            prior_quote=np.full(4,1e12),min_quote=np.full(4,1e12),
            fee_mode='base',rate=np.zeros(4),event=np.zeros(4),
            mark_low=p*.99,mark_high=p*1.01,
            order='carried_before_fill',scheduled_rebalance=True)
        x=execute_hour(high=p*1.0001,low=p*.9999,**kwargs)
        y=execute_hour(high=p*1.001,low=p*.999,**kwargs)
        self.assertTrue(np.array_equal(x['units'],y['units']))
        self.assertEqual(x['cash'],y['cash'])


if __name__=='__main__':
    unittest.main()

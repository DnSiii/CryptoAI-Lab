#!/usr/bin/env python3
"""P economic kernel synthetic accounting smoke tests, no historical PnL."""
import sys,types,unittest
import numpy as np
import pandas as pd
try:import phase1002_lp_opening_repair
except ImportError:
    s=types.ModuleType('phase1002_lp_opening_repair');s.PARTICIPATION=.05
    s.repair_open_lp=lambda c,u,o,q,f:(c,u.copy(),np.zeros(4),True)
    sys.modules[s.__name__]=s
try:import phase935_hourly_drawdown_integrity
except ImportError:
    s=types.ModuleType('phase935_hourly_drawdown_integrity')
    s.drawdown=lambda x,b:0.
    sys.modules[s.__name__]=s
try:import phase876_k_funded_ledger
except ImportError:
    s=types.ModuleType('phase876_k_funded_ledger')
    s.CAP_GROSS=1.75;s.CAP_ASSET=.7
    s.FEE_TIERS={'base':.0007};s.ORDERS=('carried_before_fill','after_fill')
    s.CAPITAL_MODES={'immediate':1000.,'capacity_1m':1000.,'capacity_10m':10000.}
    def within(c,u,o):
        v=u*o;eq=c+v.sum()
        return eq>0 and v.sum()<=1.75*eq+1e-8 and np.all(v<=.7*eq+1e-8)
    s._within=within;s._intrabar=lambda c,u,l,h:within(c,u,l) and within(c,u,h)
    s._risk=lambda c,u,o:(c+sum(u*o),0.,0.)
    s._fold_metrics=lambda days,base,_:{'days':len(days),'log_wealth':float(np.log(days[-1][1]/base)), 'max_drawdown':0.}
    sys.modules[s.__name__]=s
from phase1027_p_funded_ledger_hourly import simulate_p_hourly

class PAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        idx=pd.date_range('2022-12-01', '2024-12-31 23:00',freq='h',tz='UTC')
        cls.years=idx.year.to_numpy()
        n=len(idx);cls.n=n
        cls.w=np.zeros((n,4));cls.o=np.full((n,4),100.);cls.h=cls.o*1.005;cls.l=cls.o*.995
        cls.c=cls.o.copy();cls.q=np.full((n,4),1e9)
        cls.fr=np.zeros((n,4));cls.mk=np.full((n,4),np.nan);cls.ev=np.zeros((n,4),bool)
        cls.dn=np.full((n,4),np.nan);cls.up=np.full((n,4),np.nan)
        cls.dn[1439:]=.10;cls.up[1439:]=.10
    def run_case(self,**override):
        a={k:getattr(self,k) for k in ('w','o','h','l','c','q','fr','mk','ev','dn','up')}
        a.update(override)
        return simulate_p_hourly(*(a[k] for k in ('w','o','h','l','c','q','fr','mk','ev','dn','up')),
                                 .0007,order='carried_before_fill',mode='immediate',years=self.years)
    def test_flat_cash_conservation_full_chronology(self):
        out=self.run_case()
        self.assertTrue(out['survived'],out)
        self.assertEqual(out['hourly_nav_observations'],17544)
        self.assertEqual(out['terminal_usd'],out['initial_usd'])
        self.assertEqual(out['fees_usd'],0.)
        self.assertEqual(out['funding_debit_usd'],0.)
    def test_reject_future_calendar(self):
        years=self.years.copy();years[-1]=2025
        with self.assertRaises(ValueError):simulate_p_hourly(self.w,self.o,self.h,self.l,self.c,self.q,self.fr,self.mk,self.ev,self.dn,self.up,
                                                              .0007,order='carried_before_fill',mode='immediate',years=years)
    def test_reject_invalid_native_funding(self):
        mark=self.mk.copy();mark[1000,0]=100
        with self.assertRaises(ValueError):self.run_case(mk=mark)

if __name__=='__main__':unittest.main()

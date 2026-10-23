"""V98 T event-driven funding order, sign and t-1 synthetic ledger tests."""
import unittest
from unittest.mock import patch
import numpy as np
from phase1083_t_event_driven_ledger import simulate_t

class FundingCausality(unittest.TestCase):
    def check_case(self,sign,order):
        n=1600;price=np.full((n,4),100.)
        quote=np.arange(n,dtype=float)[:,None]+np.ones((n,4))*1000
        target=np.zeros((n,4));target[50,0]=.1*sign
        event=np.zeros((n,4),bool);event[51,0]=True
        rate=np.zeros((n,4));rate[51,0]=.001
        marks=np.full((n,4,2),np.nan);marks[51,0]=[99.,101.]
        years=np.full(n,2023);shock=np.zeros((n,4));calls=[]
        def execute(cash,units,opening,prior_quote,desired,fee,down,up,**kw):
            calls.append((prior_quote[0],desired[0]))
            if len(calls)==1:
                units=np.zeros(4);units[0]=sign
                return {'ok':True,'cash':cash-sign*100,'units':units,'fee_usd':0.,
                        'turnover_usd':100.,'trade_usd':np.array([sign*100,0.,0.,0.])}
            return {'ok':False,'reason':'S_SIGNED_LP_INFEASIBLE'}
        with patch('phase1083_t_event_driven_ledger.execute',side_effect=execute),\
             patch('phase1083_t_event_driven_ledger.audit',return_value={'ok':True,'reason':None}):
            r=simulate_t(target,price,price,price,price,quote,rate,marks,event,shock,shock,.0007,
                         order=order,mode='immediate',years=years)
        self.assertFalse(r['survived']);self.assertEqual(r['breach_index'],52)
        self.assertEqual(calls[0],(1050.,.1*sign))
        expected=0. if order=='carried_before_fill' else (.101 if sign>0 else -.099)
        self.assertAlmostEqual(r['funding_debit_usd'],expected,places=8)
        self.assertEqual(r['signal_changes'],2)
        self.assertEqual(r['filled_orders'],1)
    def test_long_carried(self):self.check_case(1,'carried_before_fill')
    def test_long_new(self):self.check_case(1,'new_after_fill')
    def test_short_carried(self):self.check_case(-1,'carried_before_fill')
    def test_short_new(self):self.check_case(-1,'new_after_fill')

if __name__=='__main__':unittest.main()

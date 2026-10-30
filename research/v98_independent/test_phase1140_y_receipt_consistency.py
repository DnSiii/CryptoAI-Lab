#!/usr/bin/env python3
"""Phase1140 synthetic-only receipt integrity tests."""
import math
import unittest
from test_phase1138_y_90cell_growth_audit import fixture
from phase1140_y_receipt_consistency import check
from phase1135_y_funded_training_simulator import FEE_TIERS,ORDERS,CAPITAL_MODES

def data():
    a=fixture()
    for r in a:
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    x=r['cases'][tier][order][mode]
                    total=sum(x['folds'][y]['log_wealth'] for y in ('2023','2024'))
                    x['initial_usd']=10000.
                    x['terminal_usd']=10000.*math.exp(total)
                    x['total_log_wealth']=total
                    x['regime_log_wealth']={'0':total/4,'1':total/4,'2':total/2}
                    for y in ('2023','2024'):
                        f=x['folds'][y]
                        f['positive_days_share']=f['positive_days']/f['days']
    return a

class TestY1140(unittest.TestCase):
    def test_synthetic_consistency(self):
        self.assertTrue(check(data())['decision'].startswith('PASS_'))
    def test_terminal_nav_tamper(self):
        a=data();a[0]['cases']['base'][ORDERS[0]]['immediate']['terminal_usd']*=1.01
        self.assertTrue(check(a)['decision'].startswith('BLOCKED_'))
    def test_regime_wealth_tamper(self):
        a=data();a[1]['cases']['base'][ORDERS[0]]['immediate']['regime_log_wealth']['0']+=.01
        self.assertTrue(check(a)['decision'].startswith('BLOCKED_'))
    def test_risk_cap_tamper(self):
        a=data();a[1]['cases']['base'][ORDERS[0]]['immediate']['max_gross_weight']=1.5
        self.assertTrue(check(a)['decision'].startswith('BLOCKED_'))
    def test_failed_cell_cannot_pass(self):
        a=data();x=a[0]['cases']['base'][ORDERS[0]]['immediate']
        x.update(survived=False,reason='INTRABAR_GROSS',breach_index=800)
        self.assertTrue(check(a)['decision'].startswith('REJECT_'))
if __name__=='__main__':unittest.main()

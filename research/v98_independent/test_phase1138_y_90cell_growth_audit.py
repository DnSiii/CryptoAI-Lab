#!/usr/bin/env python3
"""Y Phase1138 synthetic receipt adversarial audit, no authenticated PnL."""
import copy
import unittest
from phase1138_y_90cell_growth_audit import audit
from phase1125_y_sevenslot_source import PATHS
from phase1135_y_funded_training_simulator import FEE_TIERS,ORDERS,CAPITAL_MODES

def fixture():
    receipts=[]
    for path in PATHS:
        cases={}
        for tier in FEE_TIERS:
            cases[tier]={}
            for order in ORDERS:
                cases[tier][order]={}
                for mode in CAPITAL_MODES:
                    growth=.2 if path=='Y_full' else .1
                    folds={}
                    for year,days,hours in (('2023',365,8760),('2024',366,8784)):
                        folds[year]={'days':days,'hourly_observations':hours,
                            'log_wealth':growth,'cagr':.1,'max_drawdown':-.1,
                            'hourly_cvar_5pct':-.001,'positive_days_share':.6,
                            'positive_days':200,'profit_factor':2.,'payoff':1.5,
                            'win_rate':.6}
                    cases[tier][order][mode]={
                        'survived':True,'hourly_nav_observations':17544,
                        'active_hours':5000,'filled_orders':10,
                        'folds':folds,'total_log_wealth':2*growth,
                        'all_hourly_max_drawdown':-.2,'hourly_cvar_5pct':-.002,
                        'fees_usd':100.,'funding_debit_usd':10.,'turnover_usd':1000.,
                        'max_asset_weight':.2,'max_gross_weight':.6,
                        'max_net_weight':.4,
                        'concentration':{'asset_hhi':.25,
                            'asset_exposure_shares':[.25]*4},
                        'regime_hours':{'0':5000,'1':5000,'2':7544},
                        'regime_log_wealth':{'0':.1,'1':.1,'2':.2}}
        receipts.append({'phase':1136,'path':path,'cells_attempted':18,
            'cells_survived':18,'historical_pnl_computed':True,
            'validation_2025_read':False,'holdout_accessed':False,
            'external_benchmarks_used':False,'cases':cases})
    return receipts

class TestY1138(unittest.TestCase):
    def test_full_synthetic_matrix_pass(self):
        self.assertEqual(audit(fixture())['decision'],
            'PASS_Y_TRAINING_ONLY_PENDING_UNTOUCHED_VALIDATION')
    def test_missing_path_blocked(self):
        self.assertTrue(audit(fixture()[:-1])['decision'].startswith('BLOCKED_'))
    def test_failed_cell_no_rescue(self):
        a=fixture();cell=a[0]['cases']['base'][ORDERS[0]]['immediate']
        cell.update(survived=False,reason='INTRABAR_GROSS',breach_index=800)
        a[0]['cells_survived']=17
        self.assertEqual(audit(a)['decision'],'REJECT_Y_TRAINING_NO_RESCUE')
    def test_unattributed_failure_blocked(self):
        a=fixture();cell=a[0]['cases']['base'][ORDERS[0]]['immediate']
        cell.update(survived=False,reason=None,breach_index=None)
        a[0]['cells_survived']=17
        self.assertTrue(audit(a)['decision'].startswith('BLOCKED_'))
    def test_no_positive_marginal_rejected(self):
        a=fixture();a[1]['cases']['base'][ORDERS[0]]['immediate']['folds']['2023']['log_wealth']=.3
        self.assertEqual(audit(a)['decision'],'REJECT_Y_TRAINING_NO_RESCUE')
    def test_nonpositive_growth_rejected(self):
        a=fixture();a[1]['cases']['severe'][ORDERS[0]]['immediate']['folds']['2024']['log_wealth']=-.1
        self.assertEqual(audit(a)['decision'],'REJECT_Y_TRAINING_NO_RESCUE')
    def test_missing_hour_blocked(self):
        a=fixture();a[1]['cases']['base'][ORDERS[0]]['immediate']['hourly_nav_observations']=17543
        self.assertTrue(audit(a)['decision'].startswith('BLOCKED_'))
    def test_2025_access_flag_blocked(self):
        a=fixture();a[0]['validation_2025_read']=True
        self.assertTrue(audit(a)['decision'].startswith('BLOCKED_'))
    def test_no_trades_blocked(self):
        a=fixture();a[1]['cases']['base'][ORDERS[0]]['immediate']['filled_orders']=0
        self.assertTrue(audit(a)['decision'].startswith('BLOCKED_'))
if __name__=='__main__':unittest.main()

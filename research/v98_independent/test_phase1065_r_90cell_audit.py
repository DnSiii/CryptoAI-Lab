#!/usr/bin/env python3
"""V98 R 90-cell auditor synthetic decision integrity."""
import unittest
from copy import deepcopy
from phase1065_r_90cell_audit import audit
from phase1059_r_sevenslot_source import PATHS
from phase1062_r_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES


def fixture():
    receipts=[]
    for p in PATHS:
        r={'phase':1064,'path':p,'historical_pnl_computed':True,'cells_attempted':18,'cells_survived':18,
           'validation_2025_read':False,'holdout_accessed':False,'external_benchmarks_used':False,'cases':{}}
        for tier in FEE_TIERS:
            r['cases'][tier]={}
            for order in ORDERS:
                r['cases'][tier][order]={}
                for mode in CAPITAL_MODES:
                    lw=.4 if p=='R_full' else .2
                    fold={year:{'days':days,'hourly_observations':hours,'log_wealth':lw,
                                'cagr':.4,'max_drawdown':-.2,'hourly_max_drawdown':-.25,
                                'win_rate':.55,'positive_days':200,'cvar_5pct':-.02,
                                'profit_factor':1.4,'payoff':1.2} for year,days,hours in [('2023',365,8760),('2024',366,8784)]}
                    r['cases'][tier][order][mode]={'survived':True,'folds':fold,
                        'fees_usd':1.,'funding_debit_usd':1.,'turnover_usd':100.,
                        'all_hourly_max_drawdown':-.25,'total_log_wealth':.8,'hourly_cvar_5pct':-.01,
                        'concentration':{'asset_exposure_shares':[.25]*4,'asset_hhi':.25},
                        'regime_hours':{'0':100,'1':100,'2':100},'hourly_nav_observations':300}
        receipts.append(r)
    return receipts

class RAuditTest(unittest.TestCase):
    def test_pass_training_only(self):self.assertEqual(audit(fixture())['decision'],'PASS_R_TRAINING_ONLY_PENDING_SEPARATE_2025_VALIDATION')
    def test_missing_path(self):self.assertTrue(audit(fixture()[:-1])['decision'].startswith('BLOCKED'))
    def test_missing_fold(self):
        r=fixture();r[0]['cases']['base']['carried_before_fill']['immediate']['folds'].pop('2024')
        self.assertEqual(audit(r)['decision'],'BLOCKED_R_RECEIPT_INTEGRITY')
    def test_no_rescue(self):
        r=fixture();r[1]['cases']['base']['carried_before_fill']['immediate']['survived']=False;r[1]['cells_survived']=17
        r[1]['cases']['base']['carried_before_fill']['immediate']['reason']='R_INTRABAR_R_NET'
        self.assertEqual(audit(r)['decision'],'REJECT_R_TRAINING_NO_RESCUE')
    def test_nonpositive_marginal(self):
        r=fixture();r[1]['cases']['base']['carried_before_fill']['immediate']['folds']['2023']['log_wealth']=.1
        self.assertEqual(audit(r)['decision'],'REJECT_R_TRAINING_NO_RESCUE')
    def test_future_flag(self):
        r=fixture();r[0]['validation_2025_read']=True
        self.assertEqual(audit(r)['decision'],'BLOCKED_R_RECEIPT_INTEGRITY')

if __name__=='__main__':unittest.main()

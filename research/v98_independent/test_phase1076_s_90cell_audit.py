#!/usr/bin/env python3
"""S immutable 90-cell auditor synthetic receipt integrity and growth tests."""
import unittest
from phase1076_s_90cell_audit import audit
from phase1069_s_sevenslot_source import PATHS
from phase1074_s_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES

def receipt(path,survived=True,reason=None,breach=None,wealth=1.):
    c={'survived':survived,'reason':reason,'breach_index':breach,
       'folds':{str(y):{'days':days,'hourly_observations':hours,
          'log_wealth':wealth,'cagr':.05,'max_drawdown':-.1,
          'hourly_max_drawdown':-.11,'win_rate':.5,'positive_days':days//2,
          'cvar_5pct':-.01,'profit_factor':1.1,'payoff':1.1}
          for y,days,hours in ((2023,365,8760),(2024,366,8784))},
       'fees_usd':1.,'funding_debit_usd':0.,'turnover_usd':1.,
       'all_hourly_max_drawdown':-.1,'total_log_wealth':wealth*2,
       'hourly_cvar_5pct':-.01,
       'concentration':{'asset_exposure_shares':[.25]*4,'asset_hhi':.25},
       'regime_hours':{'0':8760,'1':8784,'2':0},'hourly_nav_observations':17544}
    return {'path':path,'phase':1075,'cells_attempted':18,'cells_survived':18 if survived else 0,
            'historical_pnl_computed':True,'validation_2025_read':False,'holdout_accessed':False,
            'external_benchmarks_used':False,'cases':{tier:{order:{mode:dict(c)
            for mode in CAPITAL_MODES}for order in ORDERS}for tier in FEE_TIERS}}

def all_receipts():return [receipt(p,wealth=2. if p=='S_full' else 1.) for p in PATHS]
class SAudit(unittest.TestCase):
    def test_90_positive_growth(self):
        a=audit(all_receipts());self.assertTrue(a['decision'].startswith('PASS_'),a)
    def test_nonpositive_marginal_rejected(self):
        r=all_receipts();r[1]=receipt('S_full',wealth=.5)
        a=audit(r);self.assertEqual(a['decision'],'REJECT_S_TRAINING_NO_RESCUE')
    def test_missing_path_blocked(self):
        a=audit(all_receipts()[:4]);self.assertTrue(a['decision'].startswith('BLOCKED_'))
    def test_missing_cell_blocked(self):
        r=all_receipts();del r[1]['cases']['base']['new_after_fill']['immediate']
        a=audit(r);self.assertTrue(a['decision'].startswith('BLOCKED_'))
    def test_source_preflight_blocked(self):
        r=all_receipts();p=r[1]
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    p['cases'][tier][order][mode]['survived']=False
                    p['cases'][tier][order][mode]['reason']='S_SOURCE_GEOMETRY'
        p['cells_survived']=0
        a=audit(r);self.assertEqual(a['decision'],'BLOCKED_S_PREFLIGHT_SOURCE_NOT_ECONOMIC')
    def test_real_intrabar_rejected(self):
        r=all_receipts();p=r[1]
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    p['cases'][tier][order][mode]['survived']=False
                    p['cases'][tier][order][mode]['reason']='S_INTRABAR_ASSET'
                    p['cases'][tier][order][mode]['breach_index']=900
        p['cells_survived']=0
        a=audit(r);self.assertEqual(a['decision'],'REJECT_S_TRAINING_NO_RESCUE')
if __name__=='__main__':unittest.main()

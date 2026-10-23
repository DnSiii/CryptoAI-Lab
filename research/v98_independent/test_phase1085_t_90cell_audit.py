"""V98 T synthetic 90-cell receipt adversaries; no historical PnL."""
import unittest
from phase1081_t_sevenslot_source import PATHS
from phase1083_t_event_driven_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES
from phase1085_t_90cell_audit import audit

def receipts():
    out=[]
    for path in PATHS:
        c={};full=path=='T_full'
        for tier in FEE_TIERS:
            c[tier]={}
            for order in ORDERS:
                c[tier][order]={}
                for mode in CAPITAL_MODES:
                    f={}
                    for year,days,hours in [('2023',365,8760),('2024',366,8784)]:
                        f[year]={'days':days,'hourly_observations':hours,'log_wealth':.20 if full else .10,
                                 'cagr':.20 if full else .10,'max_drawdown':-.1,'hourly_max_drawdown':-.11,
                                 'win_rate':.5,'positive_days':days//2,'cvar_5pct':-.01,
                                 'profit_factor':1.3,'payoff':1.2}
                    c[tier][order][mode]={'survived':True,'folds':f,'fees_usd':5.,
                        'funding_debit_usd':1.,'turnover_usd':100.,'all_hourly_max_drawdown':-.11,
                        'total_log_wealth':.4 if full else .2,'hourly_cvar_5pct':-.01,
                        'concentration':{'asset_exposure_shares':[.25]*4,'asset_hhi':.25},
                        'regime_hours':{'0':1000,'1':10000,'2':6544},'hourly_nav_observations':17544}
        out.append({'phase':1084,'path':path,'decision':'PASS_T_PATH_SURVIVAL_PENDING_90CELL_GROWTH',
                    'cells_attempted':18,'cells_survived':18,'historical_pnl_computed':True,
                    'validation_2025_read':False,'holdout_accessed':False,'external_benchmarks_used':False,
                    'canonical_sha256':path,'cases':c})
    return out

def manifest():return {'decision':'FROZEN_T_PRE_ECONOMIC','canonical_sha256':{p:p for p in PATHS}}

class AuditTests(unittest.TestCase):
    def test_valid_synthetic_pass(self):
        self.assertEqual(audit(receipts(),manifest())['decision'],
                         'PASS_T_TRAINING_ONLY_PENDING_SEPARATE_2025_VALIDATION')
    def test_missing_path(self):
        self.assertEqual(audit(receipts()[:-1],manifest())['decision'],
                         'BLOCKED_T_INCOMPLETE_FIVE_PATH_RECEIPTS')
    def test_future_flag(self):
        r=receipts();r[0]['validation_2025_read']=True
        self.assertEqual(audit(r,manifest())['decision'],'BLOCKED_T_RECEIPT_INTEGRITY')
    def test_source_hash_tamper(self):
        r=receipts();r[0]['canonical_sha256']='tampered'
        self.assertEqual(audit(r,manifest())['decision'],'BLOCKED_T_RECEIPT_INTEGRITY')
    def test_nonpositive_full(self):
        r=receipts();r[1]['cases']['base']['carried_before_fill']['immediate']['folds']['2023']['log_wealth']=-.01
        self.assertEqual(audit(r,manifest())['decision'],'REJECT_T_TRAINING_NO_RESCUE')
    def test_marginal_negative(self):
        r=receipts();r[0]['cases']['base']['carried_before_fill']['immediate']['folds']['2023']['log_wealth']=.3
        self.assertEqual(audit(r,manifest())['decision'],'REJECT_T_TRAINING_NO_RESCUE')
    def test_risk_failure(self):
        r=receipts();cell=r[1]['cases']['base']['carried_before_fill']['immediate'];cell['survived']=False
        cell['reason']='T_INTRABAR_GROSS';cell['breach_index']=1234;r[1]['cells_survived']=17
        self.assertEqual(audit(r,manifest())['decision'],'REJECT_T_TRAINING_NO_RESCUE')

if __name__=='__main__':unittest.main()

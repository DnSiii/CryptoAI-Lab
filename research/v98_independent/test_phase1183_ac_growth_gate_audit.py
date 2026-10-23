#!/usr/bin/env python3
"""Synthetic receipt mutation tests for strict AC economic gate; no PnL."""
import json
import tempfile
import unittest
from pathlib import Path
from phase1183_ac_growth_gate_audit import audit,PATHS,MODES,FEES,ORDERS,SOURCE_SHA


def fake(root):
    for path in PATHS:
        cells=[]
        for mode in MODES:
            for fee in FEES:
                for order in ORDERS:
                    growth=.10 if path=='AC_full' else .05
                    f={year:{'hours':h,'starting_equity':10000.,'ending_equity':11000.,
                             'net_return':growth,'cagr_annualized':growth,
                             'max_drawdown':-.1,'daily_win_rate':.6,'daily_cvar5':-.02,
                             'trade_level_pf_payoff_win_rate':'PENDING_SEPARATE_FROZEN_FIFO_AUDIT'}
                       for year,h in (('2023',8760),('2024',8784))}
                    cells.append({'path':path,'mode':mode,'fee':fee,'funding_order':order,
                                  'passed':True,'hours_completed':17544,
                                  'historical_pnl_computed':True,'final_equity':11000.,
                                  'turnover':100.,'fees_paid':1.,'funding_cash':-.1,
                                  'max_gross':.2,'max_abs_net':.1,
                                  'max_asset_concentration':.1,'folds':f})
        (root/('phase1182_ac_official_'+path+'.json')).write_text(json.dumps({
            'path':path,'validation_2025_read':False,
            'external_benchmarks_used':False,
            'official_source_mark_sha256':SOURCE_SHA,'cells':cells}))


class GateTests(unittest.TestCase):
    def test_missing_receipts_block(self):
        with tempfile.TemporaryDirectory() as d:
            r=audit(d)
            self.assertTrue(r['decision'].startswith('BLOCKED_'))

    def test_complete_positive_passes_pending_fifo(self):
        with tempfile.TemporaryDirectory() as d:
            fake(Path(d))
            r=audit(d)
            self.assertTrue(r['decision'].startswith('PASS_'),r.get('problems'))
            self.assertFalse(r['promotion_eligible'])
            self.assertEqual(r['cells_survived'],90)

    def test_negative_growth_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fake(p)
            f=p/'phase1182_ac_official_AC_full.json';r=json.loads(f.read_text())
            r['cells'][0]['folds']['2024']['cagr_annualized']=-.01
            f.write_text(json.dumps(r))
            self.assertEqual(audit(p)['decision'],'REJECT_AC_ECONOMIC_NO_RESCUE')

    def test_missing_cell_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fake(p)
            f=p/'phase1182_ac_official_AC_full.json';r=json.loads(f.read_text())
            r['cells'].pop();f.write_text(json.dumps(r))
            self.assertTrue(audit(p)['decision'].startswith('BLOCKED_'))

    def test_sleeve_marginal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fake(p)
            f=p/'phase1182_ac_official_AC_minus_stress.json';r=json.loads(f.read_text())
            for c in r['cells']:
                for fold in c['folds'].values():
                    fold['net_return']=.2
            f.write_text(json.dumps(r))
            self.assertEqual(audit(p)['decision'],'REJECT_AC_ECONOMIC_NO_RESCUE')


if __name__=='__main__':
    unittest.main(verbosity=2)

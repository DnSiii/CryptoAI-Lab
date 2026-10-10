"""Synthetic negative tests for paper accounting and prefix immutability."""
import unittest
from scripts.v99_phase195bt_core import audit

def ledger():
    return {'mode':'PAPER_ONLY','base_capital_brl':10000,
      'equity_curve':[{'timestamp':'2026-10-01T00:00:00Z','capital_brl':10000,
      'equity_multiple':1.,'hour_result_brl':0.},
      {'timestamp':'2026-10-01T01:00:00Z','capital_brl':10002,
      'equity_multiple':1.0002,'hour_result_brl':2.}]}
class Tests(unittest.TestCase):
    def test_good(self): self.assertEqual(audit(ledger()),[])
    def test_capital(self):
        d=ledger();d['equity_curve'][1]['hour_result_brl']=3
        self.assertIn('capital',audit(d))
    def test_multiple(self):
        d=ledger();d['equity_curve'][1]['equity_multiple']=1.1
        self.assertIn('multiple',audit(d))
    def test_time(self):
        d=ledger();d['equity_curve'][1]['timestamp']='2026-10-01T03:00:00Z'
        self.assertIn('time',audit(d))

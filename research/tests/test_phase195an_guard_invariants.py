"""Phase195-AN offline invariant controls; no market or holdout access."""
import sys,unittest
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from v99_phase195an_research_prefix_guard import guard
from v99_phase195an_backtest_boundary import audit
def fixture():
 x={'mode':'PAPER_ONLY','real_orders_enabled':False,'version':'a','schema_version':2,'base_capital_brl':10000,
 'paper_start_after_timestamp':'t2','same_boundary_for_all_variants':True,
 'backtest_reference':{'f1':{'curve':[{'timestamp':'t0'}]}},
 'variants':{'f1':{'equity_curve':[{'timestamp':'t2','capital':100},{'timestamp':'t3','capital':101}],
 'operations':[{'timestamp':'t3','symbol':'BTC','to_weight_pct':10}]}}}
 return x,deepcopy(x)
class Invariants(unittest.TestCase):
 def test_append_only(self):
  a,b=fixture();b['variants']['f1']['equity_curve'].append({'timestamp':'t4','capital':102})
  self.assertEqual(guard(a,b)['gate'],'PASS_APPEND_ONLY')
 def test_rewritten_equity(self):
  a,b=fixture();b['variants']['f1']['equity_curve'][0]['capital']=99
  self.assertIn('EQUITY_REWRITE:f1',guard(a,b)['issues'])
 def test_rewritten_operations(self):
  a,b=fixture();b['variants']['f1']['operations'][0]['to_weight_pct']=12
  self.assertIn('OPERATION_REWRITE:f1',guard(a,b)['issues'])
 def test_contaminated_backtest(self):
  a,b=fixture();b['backtest_reference']['f1']['curve'].append({'timestamp':'t4'})
  self.assertIn('BACKTEST_CROSSES_PAPER_BOUNDARY:f1',guard(a,b)['issues'])
 def test_backtest_pre_paper_drift(self):
  a,b=fixture();b['backtest_reference']['f1']['curve'][0]['equity_multiple']=2
  self.assertEqual(audit(a,b)['variants']['f1']['gate'],'BLOCK_PREPAPER_REWRITE')
 def test_backtest_paper_tail_excluded(self):
  a,b=fixture();a['backtest_reference']['f1']['curve'].append({'timestamp':'t3'})
  b['backtest_reference']['f1']['curve'].append({'timestamp':'t4'})
  self.assertEqual(audit(a,b)['variants']['f1']['gate'],'PASS_PREPAPER_PREFIX')
 def test_paper_boundary_immutable(self):
  a,b=fixture();b['paper_start_after_timestamp']='t1'
  self.assertIn('IDENTITY_CHANGED:paper_start_after_timestamp',guard(a,b)['issues'])
if __name__=='__main__':unittest.main()

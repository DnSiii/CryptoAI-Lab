import copy
import unittest
from scripts.v99_phase195bg_backtest_boundary_gate import NAMES, audit

T='2026-09-16T13:00:00+00:00'
U='2026-09-16T14:00:00+00:00'
P='2026-09-15T02:00:00+00:00'


def fixture():
    return {'mode':'PAPER_ONLY','real_orders_enabled':False,
            'paper_start_after_timestamp':T,'latest_data_timestamp':U,
            'variants':{k:{'equity_curve':[{'timestamp':T,'capital_brl':10000},
                                           {'timestamp':U,'capital_brl':10001}]} for k in NAMES},
            'backtest_reference':{k:{'curve':[{'timestamp':P,'equity_multiple':1.0}]} for k in NAMES}}


class Tests(unittest.TestCase):
    def test_stable(self):
        a=fixture();self.assertEqual(audit(a,copy.deepcopy(a))['status'],'OBSERVED_ONLY_NOT_PROMOTION')
    def test_historical_rewrite(self):
        a=fixture();b=copy.deepcopy(a);b['backtest_reference']['f3']['curve'][0]['equity_multiple']=1.1
        self.assertEqual(audit(a,b)['variants']['f3']['pre_paper_backtest_rewrites'],1)
    def test_forward_mislabeled(self):
        a=fixture();b=copy.deepcopy(a);b['backtest_reference']['r98']['curve'].append({'timestamp':T,'equity_multiple':1.0})
        self.assertEqual(audit(a,b)['variants']['r98']['forward_points_mislabeled_backtest'],1)
    def test_paper_rewrite(self):
        a=fixture();b=copy.deepcopy(a);b['variants']['f1']['equity_curve'][1]['capital_brl']=9000
        self.assertEqual(audit(a,b)['variants']['f1']['rewritten_paper_hours'],1)
    def test_bad_mode(self):
        a=fixture();a['real_orders_enabled']=True
        with self.assertRaises(ValueError):audit(a,fixture())
    def test_duplicate_time(self):
        a=fixture();a['variants']['r98']['equity_curve'].append(a['variants']['r98']['equity_curve'][-1])
        with self.assertRaises(ValueError):audit(a,fixture())
    def test_bad_boundary(self):
        a=fixture();a['paper_start_after_timestamp']='2026-09-16T12:00:00+00:00'
        with self.assertRaises(ValueError):audit(a,fixture())
    def test_non_utc(self):
        a=fixture();a['variants']['f3']['equity_curve'][0]['timestamp']='2026-09-16T13:00:00'
        with self.assertRaises(ValueError):audit(a,fixture())

if __name__=='__main__':unittest.main()

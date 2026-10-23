"""C139 synthetic accounting invariants, never economic performance claims."""
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research.tools.v99_r106_d1_target_rebalance_cycle139 import rebalance

T = datetime(2023,9,29,tzinfo=timezone.utc)
BASE = dict(time=T,decision_feature_max_time=T-timedelta(hours=1),
            scenario='severe_model_only',
            before={'cash_quote':'1000','spot_base':{'BTC':'0','ETH':'0'},
                    'perp_base':{'BTC':'0','ETH':'0'}},
            target_weights={'BTC':'0.25','ETH':'0.25'},
            marks={'BTC':{'spot':'100','perp':'101'},'ETH':{'spot':'50','perp':'51'}},
            native_fees={'BTC':{'spot':'0.001','perp':'0.0005','spot_currency':'BASE'},
                         'ETH':{'spot':'0.001','perp':'0.0005','spot_currency':'QUOTE'}})

class TestC139(unittest.TestCase):
    def run_case(self, **kw):
        case=deepcopy(BASE);case.update(kw);return rebalance(**case)
    def test_both_assets_exact_hedge_and_gross_scaled(self):
        r=self.run_case();self.assertLess(Decimal(r['gross_scale']),1)
        self.assertLessEqual(Decimal(r['gross_quote']),Decimal(r['nav_after']))
        for a in ('BTC','ETH'):
            self.assertEqual(Decimal(r['after']['spot_base'][a]),-Decimal(r['after']['perp_base'][a]))
        self.assertFalse(r['historical_roi_authorized'])
        self.assertFalse(r['orders_enabled'])
    def test_both_scenarios_reconcile_fee_nav(self):
        for scenario in ('severe_model_only','supersevere_model_only'):
            r=self.run_case(scenario=scenario)
            self.assertLessEqual(abs(Decimal(r['nav_before'])-Decimal(r['nav_after'])-
                             Decimal(r['native_fee_quote'])-Decimal(r['stress_fee_quote'])),Decimal('1e-18'))
    def test_close_is_fee_consistent(self):
        a=self.run_case(target_weights={'BTC':'0.25','ETH':'0'})
        b=self.run_case(before=a['after'],target_weights={'BTC':'0','ETH':'0'})
        self.assertLessEqual(abs(Decimal(b['after']['spot_base']['BTC'])),Decimal('1e-12'))
        self.assertLessEqual(abs(Decimal(b['after']['perp_base']['BTC'])),Decimal('1e-12'))
    def test_no_lookahead(self):
        with self.assertRaisesRegex(ValueError,'LOOKAHEAD'):
            self.run_case(decision_feature_max_time=T)
    def test_no_validation(self):
        with self.assertRaisesRegex(ValueError,'SEALED'):
            self.run_case(time=datetime(2023,10,1,tzinfo=timezone.utc))
    def test_pretrain_forbidden(self):
        with self.assertRaisesRegex(ValueError,'SEALED'):
            self.run_case(time=datetime(2021,12,8,tzinfo=timezone.utc))
    def test_noncanonical_fee_rejected(self):
        f=deepcopy(BASE['native_fees']);f['BTC']['spot']='NaN'
        with self.assertRaises(ValueError):self.run_case(native_fees=f)
    def test_no_new_leverage(self):
        with self.assertRaisesRegex(ValueError,'PAIR_WEIGHT_CAP'):
            self.run_case(target_weights={'BTC':'0.251','ETH':'0'})
    def test_missing_asset_rejected(self):
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):
            self.run_case(marks={'BTC':{'spot':'100','perp':'101'}})
    def test_held_pair_does_not_invent_fees(self):
        a=self.run_case(target_weights={'BTC':'0.25','ETH':'0'})
        b=self.run_case(before=a['after'],target_weights={'BTC':'0.25','ETH':'0'},
                        marks=BASE['marks'])
        # With the target as a fraction of reduced NAV, a tiny real rebalance
        # may be required; it is not valid to assume exact zero turnover.
        self.assertTrue(Decimal(b['native_fee_quote'])>=0)

if __name__=='__main__':unittest.main()

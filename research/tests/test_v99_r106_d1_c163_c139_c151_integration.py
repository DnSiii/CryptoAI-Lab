"""C163: independent original C139 -> C151 native-lot integration, synthetic ONLY.

All contract specs here are invented fixtures; never infer OKX execution
capability, realized funding, market ROI or historical TRAIN viability.
"""
import unittest
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from research.tools.v99_r106_d1_target_rebalance_cycle139 import rebalance
from research.verification.independent_d1_c151_executable_lot_gate import (
    lot_feasibility_diagnostics, require_lot_feasible,
)

T = datetime(2023, 9, 29, tzinfo=timezone.utc)
BEFORE = {'cash_quote': '1000', 'spot_base': {'BTC': '0', 'ETH': '0'},
          'perp_base': {'BTC': '0', 'ETH': '0'}}
MARKS = {'BTC': {'spot': '100', 'perp': '101'},
         'ETH': {'spot': '50', 'perp': '51'}}
FEES = {'BTC': {'spot': '0.001', 'perp': '0.0005', 'spot_currency': 'BASE'},
        'ETH': {'spot': '0.001', 'perp': '0.0005', 'spot_currency': 'QUOTE'}}


def declared_fixture_specs():
    return {a: {
        'venue': 'OKX', 'spot_instrument': a + '-USDT',
        'swap_instrument': a + '-USDT-SWAP',
        'swap_type': 'linear', 'contract_value_currency': a,
        'contract_value_base': '0.01' if a == 'BTC' else '0.1',
        'swap_lot_contracts': '1', 'swap_min_contracts': '1',
        'spot_lot_base': '0.0001', 'spot_min_base': '0.0001',
        'effective_from': datetime(2021, 12, 1, tzinfo=timezone.utc),
        'effective_until': datetime(2023, 10, 1, tzinfo=timezone.utc),
        'published_at': datetime(2021, 12, 1, tzinfo=timezone.utc),
    } for a in ('BTC', 'ETH')}


def modeled(scenario):
    return rebalance(time=T, decision_feature_max_time=T - timedelta(hours=1),
                     scenario=scenario, before=deepcopy(BEFORE),
                     target_weights={'BTC': '0.25', 'ETH': '0.25'},
                     marks=deepcopy(MARKS), native_fees=deepcopy(FEES))


class C163CrossModule(unittest.TestCase):
    def test_native_lot_gate_rejects_original_c139_fills(self):
        for scenario in ('severe_model_only', 'supersevere_model_only'):
            r = modeled(scenario)
            journal = {'frames': [{'time': T, 'fills': r['fills']}]}
            proof = lot_feasibility_diagnostics(journal, declared_fixture_specs())
            self.assertEqual(proof['fills_checked'], 4)
            self.assertEqual(proof['unexecutable_fills'], 4)
            self.assertFalse(proof['all_modeled_fills_executable_under_declared_specs'])
            with self.assertRaisesRegex(ValueError, 'LOT_VIOLATION'):
                require_lot_feasible(journal, declared_fixture_specs())
            self.assertFalse(proof['instrument_specs_exchange_authenticated'])
            self.assertFalse(proof['historical_roi_authorized'])

    def test_scenario_fee_paths_do_not_masquerade_as_alpha(self):
        severe = modeled('severe_model_only')
        supersevere = modeled('supersevere_model_only')
        self.assertEqual(severe['after']['spot_base'], supersevere['after']['spot_base'])
        self.assertEqual(severe['after']['perp_base'], supersevere['after']['perp_base'])
        self.assertEqual(severe['native_fee_quote'], supersevere['native_fee_quote'])
        self.assertGreater(Decimal(supersevere['stress_fee_quote']),
                           Decimal(severe['stress_fee_quote']))
        self.assertGreater(Decimal(severe['nav_after']),
                           Decimal(supersevere['nav_after']))
        for r in (severe, supersevere):
            self.assertLessEqual(abs(Decimal(r['nav_before']) - Decimal(r['nav_after']) -
                                 Decimal(r['native_fee_quote']) -
                                 Decimal(r['stress_fee_quote'])), Decimal('1e-18'))
            self.assertFalse(r['historical_roi_authorized'])
            self.assertFalse(r['orders_enabled'])

    def test_unauthenticated_future_spec_is_rejected(self):
        r = modeled('severe_model_only')
        specs = declared_fixture_specs()
        specs['BTC']['published_at'] = datetime(2026, 10, 23, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, 'CAUSALLY_EFFECTIVE'):
            lot_feasibility_diagnostics({'frames': [{'time': T, 'fills': r['fills']}]}, specs)


if __name__ == '__main__':
    unittest.main()

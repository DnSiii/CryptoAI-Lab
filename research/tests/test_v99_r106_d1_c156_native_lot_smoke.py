"""C156: independent C151 lot-contract smoke tests; illustrative terms only."""
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from research.verification.independent_d1_c151_executable_lot_gate import (
    lot_feasibility_diagnostics, require_lot_feasible,
)

T = datetime(2022, 1, 1, tzinfo=timezone.utc)


def specs():
    return {a: {
        'venue': 'OKX', 'spot_instrument': a+'-USDT',
        'swap_instrument': a+'-USDT-SWAP', 'swap_type': 'linear',
        'contract_value_currency': a,
        'contract_value_base': '0.01' if a == 'BTC' else '0.1',
        'swap_lot_contracts': '1', 'swap_min_contracts': '1',
        'spot_lot_base': '0.0001', 'spot_min_base': '0.0001',
        'effective_from': datetime(2021, 12, 1, tzinfo=timezone.utc),
        'effective_until': datetime(2023, 10, 1, tzinfo=timezone.utc),
        'published_at': datetime(2021, 12, 1, tzinfo=timezone.utc),
    } for a in ('BTC', 'ETH')}


def journal(q='0.02'):
    return {'frames': [{'time': T, 'fills': [
        {'time': T, 'asset': 'BTC', 'leg': 'spot', 'base_quantity': q},
        {'time': T, 'asset': 'BTC', 'leg': 'perp', 'base_quantity': q},
    ]}]}


class LotSmoke(unittest.TestCase):
    def test_exact_grid_is_structural_only(self):
        result = require_lot_feasible(journal(), specs())
        self.assertEqual(result['fills_checked'], 2)
        self.assertEqual(result['unexecutable_fills'], 0)
        for k in ('instrument_specs_exchange_authenticated',
                  'native_fills_exchange_authenticated', 'historical_roi_authorized',
                  'validation_opened', 'holdout_opened', 'promotion_authorized',
                  'orders_enabled'):
            self.assertIs(result[k], False)

    def test_non_grid_perp_rejected(self):
        result = lot_feasibility_diagnostics(journal('0.021'), specs())
        self.assertEqual(result['unexecutable_fills'], 1)
        with self.assertRaisesRegex(ValueError, 'LOT_VIOLATION'):
            require_lot_feasible(journal('0.021'), specs())

    def test_missing_asset_specs_rejected(self):
        with self.assertRaisesRegex(ValueError, 'SPECS_REQUIRED'):
            require_lot_feasible(journal(), {'BTC': specs()['BTC']})

    def test_future_published_specs_rejected(self):
        s = specs()
        s['BTC']['published_at'] = datetime(2026, 10, 23, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, 'CAUSALLY_EFFECTIVE'):
            require_lot_feasible(journal(), s)

    def test_contract_unit_mismatch_rejected(self):
        s = specs()
        s['BTC']['contract_value_currency'] = 'USDT'
        with self.assertRaisesRegex(ValueError, 'CONTRACT_UNIT'):
            require_lot_feasible(journal(), s)

    def test_nonfinite_fill_rejected(self):
        with self.assertRaisesRegex(ValueError, 'NONPOSITIVE'):
            require_lot_feasible(journal('NaN'), specs())

    def test_cash_only_never_certifies_execution(self):
        result = require_lot_feasible({'frames': [{'time': T, 'fills': []}]}, specs())
        self.assertEqual(result['fills_checked'], 0)
        self.assertIs(result['native_fills_exchange_authenticated'], False)

    def test_below_minimum_is_infeasible(self):
        s = specs()
        s['BTC']['spot_min_base'] = '1'
        result = lot_feasibility_diagnostics(journal(), s)
        self.assertEqual(result['unexecutable_fills'], 1)


if __name__ == '__main__':
    unittest.main()

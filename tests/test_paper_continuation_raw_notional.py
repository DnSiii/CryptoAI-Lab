"""Regression checks for raw notional scaling in continuation, without changing published history."""
import unittest
from scripts.paper_continuation import merge_ledger


def fixture(raw, display, factor=2.0):
    old = {
        'latest_data_timestamp': '2026-11-04T18:00:00Z',
        'base_capital_brl': 10000,
        'equity_curve': [{'timestamp': '2026-11-04T18:00:00Z', 'capital_brl': 10000 * factor}],
        'decisions': [{'timestamp': '2026-11-04T18:00:00Z', 'adjustments': []}],
        'summary': {'current_capital_brl': 10000 * factor},
    }
    adjustment = {'symbol': 'BTCUSDT', 'order_value_brl': display,
                  'order_value_brl_unrounded': raw}
    segment = {
        'base_capital_brl': 10000,
        'latest_data_timestamp': '2026-11-04T19:00:00Z',
        'equity_curve': [{'timestamp': '2026-11-04T19:00:00Z', 'capital_brl': 10000}],
        'decisions': [{'timestamp': '2026-11-04T19:00:00Z', 'adjustments': [adjustment]}],
        'summary': {},
    }
    return old, segment


class RawNotionalContinuationTests(unittest.TestCase):
    def test_subcent_scales_without_losing_raw_precision(self):
        old, segment = fixture(0.002, 0.0)
        merged = merge_ledger(old, segment, {})
        adjustment = merged['decisions'][-1]['adjustments'][0]
        self.assertAlmostEqual(adjustment['order_value_brl_unrounded'], 0.004)
        self.assertEqual(adjustment['order_value_brl'], 0.0)
        self.assertEqual(merged['decisions'][0], old['decisions'][0])

    def test_rounding_boundary(self):
        old, segment = fixture(0.003, 0.0)
        merged = merge_ledger(old, segment, {})
        adjustment = merged['decisions'][-1]['adjustments'][0]
        self.assertAlmostEqual(adjustment['order_value_brl_unrounded'], 0.006)
        self.assertEqual(adjustment['order_value_brl'], 0.01)

    def test_source_mismatch_rejected(self):
        old, segment = fixture(0.003, 0.01)
        with self.assertRaisesRegex(RuntimeError, 'Original raw/displayed'):
            merge_ledger(old, segment, {})

    def test_preserve_existing_display_when_scaling_one(self):
        old, segment = fixture(0.003, 0.0, factor=1.0)
        merged = merge_ledger(old, segment, {})
        self.assertEqual(merged['decisions'][-1]['adjustments'][0]['order_value_brl'], 0.0)

    def test_invalid_raw_rejected(self):
        for raw in (0, -0.001, float('nan'), float('inf')):
            with self.subTest(raw=raw):
                old, segment = fixture(raw, 0.0)
                with self.assertRaisesRegex(RuntimeError, 'Invalid'):
                    merge_ledger(old, segment, {})


if __name__ == '__main__':
    unittest.main()

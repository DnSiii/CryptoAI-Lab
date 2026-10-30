#!/usr/bin/env python3
"""Synthetic causal AD source tests; never accesses vendor history."""
import unittest
import numpy as np
import pandas as pd
from phase1189_ad_online_core_router import ASSETS, online_core_router, observer_digest


def sample(n=900):
    idx = pd.date_range('2022-12-01T00:00:00Z', periods=n, freq='h')
    t = np.arange(n, dtype=float)
    close = np.column_stack([100*np.exp(.00015*t + .025*np.sin(t/(19+5*j))) for j in range(4)])
    opening = np.vstack([close[0], close[:-1]])
    high = np.maximum(close, opening) * 1.003
    low = np.minimum(close, opening) * .997
    quote = np.full_like(close, 1e7)
    fund = np.zeros_like(close)
    event = np.zeros_like(close)
    event[::8] = 1
    fund[::8] = .0001
    return [pd.DataFrame(x, index=idx, columns=ASSETS) for x in
            (opening, high, low, close, quote, fund, event)]


class ADCoreRouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = sample()
        cls.core, cls.router, cls.diag = online_core_router(*cls.frames, diagnostics=True)

    def test_cash_warmup_and_long_only(self):
        self.assertTrue((self.core[:336] == 0).all())
        self.assertTrue((self.core[336:] >= 0).all())
        self.assertTrue((self.core[336:].sum(axis=1) <= 1+1e-12).all())
        self.assertTrue((self.core[336:].sum(axis=1) > 0).all())

    def test_router_probabilities_and_regime_transitions(self):
        np.testing.assert_allclose(self.router.sum(axis=1), 1, atol=1e-12)
        self.assertTrue((self.router > 0).all())
        self.assertTrue(np.any(np.abs(self.router[337:] - self.router[336:-1]) > 1e-8))

    def test_prior_causality(self):
        frames = [f.copy() for f in self.frames]
        frames[3].iloc[600] *= 1.2
        frames[1].iloc[600] = np.maximum(frames[1].iloc[600], frames[3].iloc[600])*1.01
        frames[2].iloc[600] = np.minimum(frames[2].iloc[600], frames[3].iloc[600])*.99
        c2, r2 = online_core_router(*frames)
        np.testing.assert_array_equal(self.core[:600], c2[:600])
        np.testing.assert_array_equal(self.router[:600], r2[:600])

    def test_future_extension_preserves_prefix(self):
        extended = sample(1100)
        c2, r2 = online_core_router(*extended)
        np.testing.assert_array_equal(self.core, c2[:900])
        np.testing.assert_array_equal(self.router, r2[:900])

    def test_funding_event_only_after_settlement(self):
        frames = [f.copy() for f in self.frames]
        frames[5].iloc[800, 0] = .05
        c2, r2 = online_core_router(*frames)
        np.testing.assert_array_equal(self.core[:800], c2[:800])
        np.testing.assert_array_equal(self.router, r2)
        self.assertFalse(np.array_equal(self.core[800:], c2[800:]))

    def test_non_event_funding_rejected(self):
        frames = [f.copy() for f in self.frames]
        frames[5].iloc[801, 0] = .01
        with self.assertRaisesRegex(ValueError, 'FUNDING_MASK'):
            online_core_router(*frames)

    def test_invalid_event_clock_rejected(self):
        frames = [f.copy() for f in self.frames]
        frames[6].iloc[801, 0] = 1
        with self.assertRaisesRegex(ValueError, 'FUNDING_CLOCK'):
            online_core_router(*frames)

    def test_invalid_ohlc_rejected(self):
        frames = [f.copy() for f in self.frames]
        frames[1].iloc[600, 0] = .01
        with self.assertRaisesRegex(ValueError, 'OHLC'):
            online_core_router(*frames)

    def test_nonfinite_rejected(self):
        frames = [f.copy() for f in self.frames]
        frames[3].iloc[600, 0] = np.nan
        with self.assertRaisesRegex(ValueError, 'NONFINITE'):
            online_core_router(*frames)

    def test_future_2025_rejected(self):
        with self.assertRaisesRegex(ValueError, 'CHRONOLOGY'):
            online_core_router(*sample(19000))

    def test_wrong_asset_order_rejected(self):
        frames = [f.copy() for f in self.frames]
        frames[3] = frames[3][list(reversed(ASSETS))]
        with self.assertRaisesRegex(ValueError, 'CLEAN4'):
            online_core_router(*frames)

    def test_repeatable_observer_and_no_system_pnl(self):
        c2, r2 = online_core_router(*self.frames)
        np.testing.assert_array_equal(self.core, c2)
        np.testing.assert_array_equal(self.router, r2)
        self.assertEqual(observer_digest(self.core, self.router, self.frames[0].index),
                         observer_digest(c2, r2, self.frames[0].index))
        self.assertFalse(self.diag['historical_system_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])
        self.assertFalse(self.diag['external_benchmarks_used'])

    def test_wealth_and_refresh_observable(self):
        self.assertEqual(self.diag['expert_refreshes'], 24)
        self.assertTrue(all(x > 0 for x in self.diag['virtual_expert_wealth_last']))
        self.assertTrue(np.isfinite(self.core).all())


if __name__ == '__main__':
    unittest.main(verbosity=2)

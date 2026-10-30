#!/usr/bin/env python3
"""AC pre-economic synthetic tests: chronology, causality, integer hashes."""
import unittest
import numpy as np
import pandas as pd
from phase1174_ac_discrete_intents import (
    ASSETS, MODES, PATHS, compose_intents, canonical_hash, held_events, dwell_regime)


def sample(n=1300):
    idx = pd.date_range('2022-12-01T00:00:00Z', periods=n, freq='h')
    t = np.arange(n, dtype=float)
    arr = np.column_stack([
        100 * np.exp((.00012 + .00007 * j) * t + .035 * np.sin(t / (22 + j * 9)))
        for j in range(4)])
    arr[1000:1010] *= .87
    arr[1010:] *= 1.01
    op = np.roll(arr, 1, axis=0)
    op[0] = arr[0]
    hi = np.maximum(op, arr) * 1.01
    lo = np.minimum(op, arr) * .99
    q = np.column_stack([1e7 * (1 + .1 * j) * (1 + .05 * np.sin(t / 30))
                         for j in range(4)])
    # Explicit completed-bar volume+close-location impulse fixture.
    arr[930] = op[930] * 1.2
    hi[930] = arr[930] * 1.001
    lo[930] = op[930] * .999
    q[930, :] *= 8
    q[1020, :] *= 7
    frames = [pd.DataFrame(a, index=idx, columns=ASSETS)
              for a in (op, hi, lo, arr, q, np.zeros_like(arr))]
    return frames


class ACSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = sample()
        cls.out, cls.diag = compose_intents(*cls.frames, diagnostics=True)

    def test_fifteen_paths_and_integer_bounds(self):
        self.assertEqual(len(self.out), 15)
        for (p, m), a in self.out.items():
            self.assertIn(p, PATHS)
            self.assertIn(m, MODES)
            self.assertEqual(a.shape, (1300, 4))
            self.assertEqual(a.dtype, np.int8)
            self.assertTrue((np.abs(a) <= 4).all())
            self.assertTrue((a[:720] == 0).all())

    def test_hash_is_byte_exact(self):
        idx = self.frames[0].index
        hashes = [canonical_hash(v, idx, *k) for k, v in self.out.items()]
        self.assertEqual(len(hashes), 15)
        self.assertEqual(len(set(hashes)), 15)
        for k, a in self.out.items():
            self.assertEqual(canonical_hash(a.astype('>i2'), idx, *k),
                             canonical_hash(a.astype('<i2'), idx, *k))

    def test_causality_last_hour(self):
        mutated = [f.copy() for f in self.frames]
        mutated[3].iloc[-1] *= 1.15
        mutated[2].iloc[-1] = np.minimum(mutated[2].iloc[-1], mutated[3].iloc[-1]) * .99
        mutated[1].iloc[-1] = np.maximum(mutated[1].iloc[-1], mutated[3].iloc[-1]) * 1.01
        out2 = compose_intents(*mutated)
        for k in self.out:
            np.testing.assert_array_equal(self.out[k][:-1], out2[k][:-1])

    def test_future_is_rejected(self):
        future = sample(19000)
        with self.assertRaisesRegex(ValueError, 'CHRONOLOGY'):
            compose_intents(*future)

    def test_missing_source_rejected(self):
        bad = [f.copy() for f in self.frames]
        bad[3].iloc[900, 0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'NONFINITE'):
            compose_intents(*bad)

    def test_event_hold_lockout(self):
        d = np.ones((250, 4), dtype=np.int8)
        b = np.ones_like(d, dtype=bool)
        a = held_events(d, b)
        self.assertTrue((a[:12] == 1).all())
        self.assertTrue((a[12:96] == 0).all())
        self.assertTrue((a[96:108] == 1).all())

    def test_regime_dwell(self):
        raw = np.array([1] * 20 + [2] * 20 + [0] * 90, dtype=np.int8)
        a = dwell_regime(raw)
        self.assertEqual(a[20], 2)
        self.assertEqual(a[39], 2)
        self.assertEqual(a[40], 2)
        self.assertEqual(a[92], 0)

    def test_sleeves_have_distinct_marginal_intents(self):
        self.assertGreater(self.diag['sleeve_active_hours']['growth'], 0)
        self.assertGreater(self.diag['sleeve_active_hours']['opportunity'], 0)
        self.assertTrue(np.any(self.out['AC_full', 'immediate'] !=
                               self.out['AC_core_only', 'immediate']))

    def test_no_historical_pnl_or_future_flag(self):
        self.assertIs(self.diag['historical_pnl_computed'], False)
        self.assertIs(self.diag['validation_2025_read'], False)
        self.assertEqual(self.diag['earliest_fill'], 't+1')


if __name__ == '__main__':
    unittest.main(verbosity=2)

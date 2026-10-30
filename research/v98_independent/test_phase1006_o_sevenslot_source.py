#!/usr/bin/env python3
"""V98 Phase1006 O seven-slot deterministic source-only contract tests."""
from __future__ import annotations
import hashlib
import unittest
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, START, END
from phase1006_o_sevenslot_source import (
    PATHS, EXCLUDE, GROSS_CAP, ASSET_CAP, LOOKBACK,
    causal_shocks, robust_scale, verify_corners, waterfill, compose_o,
)


def fixture():
    idx = pd.date_range(START, END, freq="h")
    t = np.arange(len(idx), dtype=float)
    columns = {}
    for j, a in enumerate(ASSETS):
        trend = .000012 * (j+1) * t
        cycle = .035 * np.sin(t/(100 + j*29) + j)
        shock = -.14 * np.exp(-((t-2683)/80)**2) * (1 + .15*j)
        columns[a] = 100 * np.exp(trend + cycle + shock)
    close = pd.DataFrame(columns, index=idx)
    opening = close * (1 + .0002 * np.sin(t[:,None]/8 + np.arange(4)))
    high = np.maximum(opening, close) * 1.013
    low = np.minimum(opening, close) * .987
    return opening, high, low, close


class OSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = fixture()

    def test_seven_slot_registry_and_five_ablation_paths(self):
        self.assertEqual(len(PATHS), 5)
        self.assertEqual(len(EXCLUDE), 5)
        self.assertEqual(EXCLUDE["O_full"], frozenset())
        self.assertEqual(len(ASSETS), 4)

    def test_waterfill_capped_and_cash_unallocated(self):
        self.assertTrue(np.allclose(waterfill(np.array([1.,0,0,0]), 1.5), [0.7,0,0,0]))
        w = waterfill(np.array([1.,1.,1.,1.]), 1.5)
        self.assertAlmostEqual(w.sum(), 1.5)
        self.assertLessEqual(w.max(), .7)

    def test_governor_adversarial_corners(self):
        w = np.array([[.7,.4,.3,.1],[.6,.5,.3,0.],[0,0,0,0.]])
        down = np.array([[.4,.5,.2,.3],[.3,.6,.5,.2],[.8,.8,.8,.8]])
        up = np.array([[.5,.8,.4,.3],[.2,.3,.4,.5],[.9,.9,.9,.9]])
        k = robust_scale(w, down, up)
        self.assertTrue(np.all((k >= 0) & (k <= 1)))
        self.assertTrue(verify_corners(w*k[:,None], down, up))
        self.assertTrue((k[:2] < 1).any())

    def test_invalid_and_warmup_shocks(self):
        op, hi, lo, _ = self.frames
        d, u, valid = causal_shocks(op.to_numpy(), hi.to_numpy(), lo.to_numpy())
        self.assertEqual(int(valid.sum()), len(op)-LOOKBACK+1)
        self.assertTrue(np.isnan(d[:LOOKBACK-1]).all())
        with self.assertRaises(ValueError):
            causal_shocks(op.to_numpy(), hi.to_numpy(), np.zeros_like(lo.to_numpy()))

    def test_complete_engine_all_paths_and_determinism(self):
        paths, info = compose_o(*self.frames, diagnostics=True)
        self.assertEqual(tuple(paths), PATHS)
        self.assertEqual(sum(info["regime_hours"].values()), 18288)
        self.assertEqual(len(info["sleeve_active_hours"]), 4)
        for name, frame in paths.items():
            w = frame.to_numpy()
            self.assertEqual(w.shape, (18288, 4))
            self.assertTrue(np.isfinite(w).all())
            self.assertGreaterEqual(w.min(), -1e-12)
            self.assertLessEqual(w.max(), ASSET_CAP + 1e-9)
            self.assertLessEqual(w.sum(axis=1).max(), GROSS_CAP + 1e-9)
            self.assertEqual(info["paths"][name]["sha256"], hashlib.sha256(frame.to_csv(float_format="%.12g").encode()).hexdigest())
        self.assertTrue((paths["O_full"].to_numpy() != paths["O_core_only"].to_numpy()).any())

    def test_future_data_and_nonfinite_rejected(self):
        op, hi, lo, cl = self.frames
        bad = cl.copy()
        bad.index = bad.index + pd.Timedelta(days=1)
        with self.assertRaises(ValueError):
            compose_o(op, hi, lo, bad)
        bad = cl.copy()
        bad.iloc[-1,0] = np.nan
        with self.assertRaises(ValueError):
            compose_o(op, hi, lo, bad)

    def test_strict_tminus1_causality(self):
        op, hi, lo, cl = self.frames
        base = compose_o(op, hi, lo, cl)["O_full"].to_numpy()
        # Last-hour future shock may change its own close(t) target,
        # but it cannot affect any target at or before close(t-1).
        high2 = hi.copy()
        high2.iloc[-1,0] *= 1.6
        alt = compose_o(op, high2, lo, cl)["O_full"].to_numpy()
        np.testing.assert_array_equal(base[:-1], alt[:-1])


if __name__ == "__main__":
    unittest.main()

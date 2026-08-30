from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.data import FuturesData
from cryptoai_v13.v16 import ConvexCaptureSpec, combine_convex_with_core


class V16ResearchTests(unittest.TestCase):
    def test_configuration_rejects_invalid_weights(self) -> None:
        with self.assertRaises(ValueError):
            ConvexCaptureSpec(fast_weight=0.8, slow_weight=0.3, trend_weight=0.2)

    def test_allocator_respects_portfolio_gross_and_does_not_mutate_core(self) -> None:
        index = pd.date_range("2026-01-01", periods=4, freq="h", tz="UTC")
        core = pd.DataFrame({"BTCUSDT": [1.0] * 4, "ETHUSDT": [0.5] * 4}, index=index)
        opportunity = pd.DataFrame({"BTCUSDT": [2.0] * 4, "ETHUSDT": [-2.0] * 4}, index=index)
        original = core.copy()
        combined, allocated = combine_convex_with_core(
            core, opportunity, core_fraction=0.3, maximum_portfolio_gross=1.6
        )
        pd.testing.assert_frame_equal(core, original)
        self.assertTrue((combined.abs().sum(axis=1) <= 1.6 + 1e-12).all())
        self.assertTrue((allocated.abs().sum(axis=1) <= 1.15 + 1e-12).all())

    def test_v16_source_is_research_only_and_has_no_order_method(self) -> None:
        source = (PROJECT / "src" / "cryptoai_v13" / "v16.py").read_text()
        runner = (PROJECT / "scripts" / "search_v16.py").read_text()
        for forbidden in ("create_order", "create_market_order", "apiKey", "secret"):
            self.assertNotIn(forbidden, source)
            self.assertNotIn(forbidden, runner)
        self.assertIn("without_best_day_return", runner)
        self.assertIn("delay_3h", runner)
        self.assertIn("severe_cost", runner)


if __name__ == "__main__":
    unittest.main()

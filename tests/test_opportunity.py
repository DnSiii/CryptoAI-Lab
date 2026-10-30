from __future__ import annotations

import unittest
import json
from pathlib import Path

import pandas as pd

from cryptoai_v13.opportunity import (
    OpportunityBudget,
    additive_opportunity_targets,
)


class OpportunityBudgetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.index = pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC")
        self.core = pd.DataFrame(
            [[0.60, -0.40], [0.90, 0.30], [0.20, 0.00]],
            index=self.index,
            columns=["BTCUSDT", "ETHUSDT"],
        )

    def test_inactive_opportunity_preserves_core_exactly(self) -> None:
        empty = self.core * 0.0
        combined, allocated = additive_opportunity_targets(
            self.core,
            empty,
            OpportunityBudget(0.40, 1.50),
        )
        pd.testing.assert_frame_equal(combined, self.core)
        self.assertEqual(float(allocated.abs().to_numpy().sum()), 0.0)

    def test_overlay_uses_only_its_budget_and_spare_capacity(self) -> None:
        opportunity = pd.DataFrame(
            [[0.80, 0.80], [0.80, 0.80], [-0.80, 0.80]],
            index=self.index,
            columns=self.core.columns,
        )
        combined, allocated = additive_opportunity_targets(
            self.core,
            opportunity,
            OpportunityBudget(0.40, 1.50),
        )
        allocated_gross = allocated.abs().sum(axis=1)
        self.assertAlmostEqual(float(allocated_gross.iloc[0]), 0.40)
        self.assertAlmostEqual(float(allocated_gross.iloc[1]), 0.30)
        self.assertAlmostEqual(float(allocated_gross.iloc[2]), 0.40)
        self.assertTrue(bool((combined.abs().sum(axis=1) <= 1.50 + 1e-12).all()))

    def test_allocator_refuses_to_silently_dilute_core(self) -> None:
        oversized = self.core.copy()
        oversized.iloc[0] = [1.0, -0.7]
        with self.assertRaisesRegex(ValueError, "refusing to rescale"):
            additive_opportunity_targets(
                oversized,
                self.core * 0.0,
                OpportunityBudget(0.40, 1.50),
            )

    def test_candidate_is_paper_active_and_has_no_real_orders(self) -> None:
        project = Path(__file__).resolve().parents[1]
        candidate = json.loads(
            (project / "config" / "candidate_opportunity_overlay_v1.json").read_text()
        )
        self.assertTrue(candidate["paper"]["active"])
        self.assertFalse(candidate["real_orders"])
        self.assertTrue(
            candidate["allocation"]["frozen_core_is_never_rescaled_by_allocator"]
        )


if __name__ == "__main__":
    unittest.main()

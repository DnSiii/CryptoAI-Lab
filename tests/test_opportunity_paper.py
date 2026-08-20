from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd

from paper_once_opportunity_v1 import empty_ledger


PROJECT = Path(__file__).resolve().parents[1]


class OpportunityPaperTests(unittest.TestCase):
    def test_candidate_is_active_only_for_paper_and_real_orders_stay_off(self) -> None:
        candidate = json.loads(
            (PROJECT / "config" / "candidate_opportunity_overlay_v1.json").read_text()
        )
        self.assertTrue(candidate["paper"]["active"])
        self.assertFalse(candidate["real_orders"])

    def test_waiting_ledger_cannot_claim_forward_results(self) -> None:
        boundary = pd.Timestamp("2026-08-20T15:00:00Z")
        latest = pd.Timestamp("2026-08-20T12:00:00Z")
        ledger = empty_ledger("combined", "test", boundary, latest)
        self.assertEqual(ledger["status"], "waiting_for_boundary")
        self.assertEqual(ledger["summary"]["current_capital_brl"], 10_000.0)
        self.assertEqual(ledger["summary"]["net_result_brl"], 0.0)
        self.assertEqual(ledger["equity_curve"], [])
        self.assertEqual(ledger["decisions"], [])

    def test_workflow_runs_and_publishes_all_comparison_tracks(self) -> None:
        workflow = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
        self.assertIn("paper_once_opportunity_v1.py", workflow)
        self.assertIn("verify_opportunity_cycle_v1.py", workflow)
        for name in (
            "paper_core_comparison_v1_ledger.json",
            "paper_opportunity_v1_ledger.json",
            "paper_combined_v1_ledger.json",
            "paper_comparison_v1.json",
        ):
            self.assertIn(name, workflow)

    def test_runner_has_no_exchange_order_method(self) -> None:
        source = (PROJECT / "scripts" / "paper_once_opportunity_v1.py").read_text()
        for forbidden in ("create_order", "create_market_order", "apiKey", "secret"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

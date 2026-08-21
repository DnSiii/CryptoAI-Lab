from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class V14PaperTests(unittest.TestCase):
    def test_v14_is_paper_only_and_has_no_return_ceiling(self) -> None:
        config = json.loads(
            (PROJECT / "config" / "candidate_v14_max_capture.json").read_text()
        )
        self.assertEqual(config["mode"], "PAPER_ONLY")
        self.assertFalse(config["real_orders"])
        self.assertTrue(config["objective"]["no_return_ceiling"])

    def test_runner_has_no_exchange_order_method(self) -> None:
        source = (PROJECT / "scripts" / "paper_once_v14.py").read_text()
        for forbidden in ("create_order", "create_market_order", "apiKey", "secret"):
            self.assertNotIn(forbidden, source)

    def test_workflow_runs_and_publishes_v14(self) -> None:
        source = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
        for value in (
            "paper_once_v14.py",
            "verify_v14_cycle.py",
            "paper_v14_state.json",
            "paper_v14_ledger.json",
        ):
            self.assertIn(value, source)


if __name__ == "__main__":
    unittest.main()

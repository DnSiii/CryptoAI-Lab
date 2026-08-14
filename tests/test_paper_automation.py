from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from paper_once_v13 import resolve_paper_start
from run_final_candidate import frozen_component_rows


class PaperAutomationTests(unittest.TestCase):
    def test_frozen_boundary_does_not_chase_a_later_download(self) -> None:
        initialized = pd.Timestamp("2026-08-13T19:01:27.722238+00:00")
        previous = {
            "paper_start_after_timestamp": "2026-08-13T19:00:00+00:00",
            "new_forward_hours": 0,
        }
        latest = pd.Timestamp("2026-08-14T03:00:00+00:00")
        self.assertEqual(
            resolve_paper_start(previous, initialized, latest),
            pd.Timestamp("2026-08-13T19:00:00+00:00"),
        )

    def test_clean_checkout_has_every_frozen_component(self) -> None:
        rows = frozen_component_rows()
        self.assertTrue({1428, 1434, 1745, 356}.issubset(rows))

    def test_workflow_is_scheduled_manual_and_has_no_secret_dependency(self) -> None:
        source = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
        self.assertIn('cron: "17 * * * *"', source)
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("paper-results", source)
        self.assertNotIn("secrets.", source)
        self.assertIn("cancel-in-progress: false", source)

    def test_data_sync_uses_only_public_market_endpoints(self) -> None:
        source = (PROJECT / "scripts" / "sync_paper_data_v13.py").read_text()
        self.assertIn("https://fapi.binance.com", source)
        self.assertIn("/fapi/v1/klines", source)
        self.assertIn("/fapi/v1/fundingRate", source)
        for forbidden in (
            "/fapi/v1/order",
            "create_order(",
            "apiSecret",
            "X-MBX-APIKEY",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

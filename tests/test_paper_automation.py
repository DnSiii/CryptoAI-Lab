from __future__ import annotations

import sys
import unittest
import zipfile
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from paper_once_v13 import resolve_paper_start
from run_final_candidate import frozen_component_rows
from sync_paper_data_v13 import public_funding_frame, public_funding_url


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

    def test_frozen_seed_preserves_the_first_forward_checkpoint(self) -> None:
        path = PROJECT / "data" / "paper_seed_v13.zip"
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            self.assertIn("BTCUSDT_1h.csv", names)
            self.assertIn("ETHUSDT_1h.csv", names)
            with archive.open("BTCUSDT_1h.csv") as stream:
                btc = pd.read_csv(stream)
        timestamps = pd.to_datetime(btc["timestamp"], utc=True)
        self.assertEqual(timestamps.min(), pd.Timestamp("2026-08-01", tz="UTC"))
        self.assertEqual(
            timestamps.max(), pd.Timestamp("2026-08-14T03:00:00+00:00")
        )

    def test_workflow_is_scheduled_manual_and_has_no_secret_dependency(self) -> None:
        source = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
        self.assertIn("paths: [\".github/workflows/v13-paper.yml\"]", source)
        self.assertIn('cron: "17 * * * *"', source)
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("paper-results", source)
        self.assertNotIn("secrets.", source)
        self.assertIn("cancel-in-progress: false", source)

    def test_data_sync_uses_only_official_public_market_data(self) -> None:
        source = (PROJECT / "scripts" / "sync_paper_data_v13.py").read_text()
        self.assertIn("https://data.binance.vision/data/futures/um/daily", source)
        self.assertIn("https://fapi.binance.com/fapi/v1/fundingRate", source)
        self.assertIn("https://www.binance.com/fapi/v1/fundingRate", source)
        self.assertIn(".CHECKSUM", source)
        self.assertIn(
            "OFFICIAL_CHECKSUMMED_ARCHIVES_PLUS_PUBLIC_FUNDING_REST", source
        )
        for forbidden in (
            "/fapi/v1/order",
            "create_order(",
            "apiSecret",
            "X-MBX-APIKEY",
        ):
            self.assertNotIn(forbidden, source)

    def test_public_funding_response_is_canonicalized_without_credentials(self) -> None:
        payload = (
            b'[{"symbol":"BTCUSDT","fundingTime":1767225600000,'
            b'"fundingRate":"0.0001"},{"symbol":"BTCUSDT",'
            b'"fundingTime":1767254400000,"fundingRate":"-0.0002"}]'
        )
        frame = public_funding_frame(payload)
        self.assertEqual(len(frame), 2)
        self.assertEqual(frame["funding_interval_hours"].tolist(), [8.0, 8.0])
        self.assertEqual(frame["funding_rate"].tolist(), [0.0001, -0.0002])
        url = public_funding_url(
            "BTCUSDT",
            pd.Timestamp("2026-01-01", tz="UTC"),
            pd.Timestamp("2026-01-02", tz="UTC"),
        )
        self.assertIn("symbol=BTCUSDT", url)
        self.assertNotIn("signature", url)
        self.assertNotIn("apiKey", url)


if __name__ == "__main__":
    unittest.main()

"""Source-only 451 regression tests; no economics or historical market claims."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from research.tools import v99_r106_binance_funding_api_clock_binding as primary
from research.verification.independent_v99_r106_binance_funding_api_clock_oracle import (
    verify_window_attempts,
)


class Funding451Tests(unittest.TestCase):
    def test_http451_is_non_retryable(self):
        exc = HTTPError(primary.API, 451, "Unavailable For Legal Reasons", {}, None)
        with patch.object(primary, "urlopen", side_effect=exc) as opener, patch.object(
            primary.time, "sleep"
        ) as sleep:
            body, err = primary.query(primary.API)
        self.assertIsNone(body)
        self.assertEqual(err, "HTTP_451_ACCESS_RESTRICTED")
        self.assertEqual(opener.call_count, 1)
        sleep.assert_not_called()

    def test_451_stops_after_one_window(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            primary, "query", return_value=(None, "HTTP_451_ACCESS_RESTRICTED")
        ) as query:
            rows, errors, attempted, planned = primary.api_records("BTCUSDT", Path(tmp))
        self.assertEqual(rows, [])
        self.assertEqual(errors, ["BTCUSDT:WINDOW_1:HTTP_451_ACCESS_RESTRICTED"])
        self.assertEqual((attempted, planned), (1, 8))
        self.assertEqual(query.call_count, 1)
        self.assertEqual(
            verify_window_attempts(
                dict(api_windows_requested=attempted, api_windows_planned=planned),
                "BTCUSDT", errors, 8
            ), 1
        )

    def test_non451_window_failures_continue(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            primary, "query", return_value=(None, "HTTP_429:rate-limited")
        ) as query:
            rows, errors, attempted, planned = primary.api_records("ETHUSDT", Path(tmp))
        self.assertEqual(rows, [])
        self.assertEqual((attempted, planned), (8, 8))
        self.assertEqual(len(errors), 8)
        self.assertEqual(query.call_count, 8)
        self.assertEqual(
            verify_window_attempts(
                dict(api_windows_requested=attempted, api_windows_planned=planned),
                "ETHUSDT", errors, 8
            ), 8
        )

    def test_oracle_rejects_fabricated_early_stop(self):
        detail = dict(api_windows_requested=1, api_windows_planned=8)
        for errors in ([], ["BTCUSDT:WINDOW_1:HTTP_429:rate-limited"],
                       ["BTCUSDT:WINDOW_2:HTTP_451_ACCESS_RESTRICTED"]):
            with self.subTest(errors=errors), self.assertRaises(ValueError):
                verify_window_attempts(detail, "BTCUSDT", errors, 8)

    def test_oracle_rejects_planned_window_mismatch(self):
        detail = dict(api_windows_requested=1, api_windows_planned=7)
        with self.assertRaises(ValueError):
            verify_window_attempts(
                detail, "BTCUSDT", ["BTCUSDT:WINDOW_1:HTTP_451_ACCESS_RESTRICTED"], 8
            )


if __name__ == "__main__":
    unittest.main()

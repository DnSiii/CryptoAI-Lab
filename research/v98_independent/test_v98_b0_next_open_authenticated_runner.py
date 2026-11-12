import unittest
from unittest.mock import patch
from research.v98_independent.v98_b0_next_open_authenticated_runner import run
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_phase243_training_reader import START_MS

class AuthenticatedRunnerTests(unittest.TestCase):
    def test_native_funding_timestamp_mapping_and_cost_scenarios(self):
        n = 2190
        bars = {a: [(100. + (i % 2), 101., 99., 100. + (i % 2), 1.)
                    for i in range(n)] for a in ASSETS}
        native = {a: {START_MS + 2187 * HOUR_MS: .001} for a in ASSETS}
        data = dict(bars=bars, funding=native, hours=n,
                    price_manifest_sha256="price", funding_manifest_sha256="funding")
        with patch("research.v98_independent.v98_b0_next_open_authenticated_runner.load",
                   return_value=data):
            result = run("unused", "unused", "unused")
        self.assertEqual(set(result["results"]), {"1x", "2x", "4x"})
        self.assertEqual(result["results"]["1x"]["hours"], n)
        self.assertFalse(result["holdout_accessed"])
        self.assertEqual(result["source"], "AUTHENTICATED_CLEAN4")

    def test_reject_off_grid_funding(self):
        n = 3
        bars = {a: [(100., 100., 100., 100., 1.)] * n for a in ASSETS}
        native = {a: {START_MS + 1: .001} for a in ASSETS}
        data = dict(bars=bars, funding=native, hours=n,
                    price_manifest_sha256="price", funding_manifest_sha256="funding")
        with patch("research.v98_independent.v98_b0_next_open_authenticated_runner.load",
                   return_value=data):
            with self.assertRaisesRegex(ValueError, "INVALID_FUNDING_TIMESTAMP"):
                run("unused", "unused", "unused")

if __name__ == "__main__":
    unittest.main()

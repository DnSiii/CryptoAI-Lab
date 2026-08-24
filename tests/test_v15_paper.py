from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.v15 import (
    DirectionAllocatorSpec,
    adaptive_directional_targets,
    apply_eligibility_boundaries,
)
from sync_paper_data_v15 import discover_symbols


class V15PaperTests(unittest.TestCase):
    def test_v15_is_a_paper_only_v14_derivative(self) -> None:
        config = json.loads(
            (PROJECT / "config" / "candidate_v15_adaptive_capture.json").read_text()
        )
        self.assertEqual(config["mode"], "PAPER_ONLY")
        self.assertFalse(config["real_orders"])
        self.assertEqual(
            config["parent_candidate_config"], "candidate_v14_max_capture.json"
        )
        self.assertTrue(config["inheritance"]["frozen_v13_core"])
        self.assertTrue(config["inheritance"]["v14_impulse_entry_exit_logic"])
        self.assertTrue(config["inheritance"]["v14_allocation_caps"])
        self.assertTrue(config["inheritance"]["v14_circuit_breaker"])

    def test_adaptive_direction_favors_the_confirmed_market_regime(self) -> None:
        index = pd.date_range("2026-01-01", periods=400, freq="h", tz="UTC")
        targets = pd.DataFrame(
            {"LONGUSDT": 1.0, "SHORTUSDT": -1.0}, index=index
        )
        spec = DirectionAllocatorSpec()

        bull_close = pd.Series(np.linspace(100.0, 200.0, len(index)), index=index)
        bull_targets, bull_regime = adaptive_directional_targets(
            targets, bull_close, spec
        )
        self.assertEqual(bull_regime.iloc[-1], "bull")
        self.assertAlmostEqual(bull_targets.iloc[-1]["LONGUSDT"], 1.6)
        self.assertAlmostEqual(bull_targets.iloc[-1]["SHORTUSDT"], -0.4)

        bear_close = pd.Series(np.linspace(200.0, 100.0, len(index)), index=index)
        bear_targets, bear_regime = adaptive_directional_targets(
            targets, bear_close, spec
        )
        self.assertEqual(bear_regime.iloc[-1], "bear")
        self.assertAlmostEqual(bear_targets.iloc[-1]["LONGUSDT"], 0.4)
        self.assertAlmostEqual(bear_targets.iloc[-1]["SHORTUSDT"], -1.6)

    def test_new_symbol_cannot_rewrite_pre_discovery_targets(self) -> None:
        index = pd.date_range("2026-08-20", periods=6, freq="h", tz="UTC")
        targets = pd.DataFrame({"NEWUSDT": [1.0] * 6}, index=index)
        boundary = index[3]
        safe = apply_eligibility_boundaries(
            targets, {"NEWUSDT": boundary.isoformat()}
        )
        self.assertTrue(safe.loc[index[:3], "NEWUSDT"].eq(0.0).all())
        self.assertTrue(safe.loc[index[3:], "NEWUSDT"].eq(1.0).all())

    def test_discovery_uses_only_old_enough_liquid_usdt_perpetuals(self) -> None:
        now = pd.Timestamp("2026-08-24", tz="UTC")
        old = int((now - pd.Timedelta("90d")).timestamp() * 1000)
        new = int((now - pd.Timedelta("5d")).timestamp() * 1000)
        exchange = {
            "symbols": [
                {"symbol": "GOODUSDT", "quoteAsset": "USDT", "contractType": "PERPETUAL", "status": "TRADING", "onboardDate": old},
                {"symbol": "LOWUSDT", "quoteAsset": "USDT", "contractType": "PERPETUAL", "status": "TRADING", "onboardDate": old},
                {"symbol": "TOONEWUSDT", "quoteAsset": "USDT", "contractType": "PERPETUAL", "status": "TRADING", "onboardDate": new},
                {"symbol": "COINUSDC", "quoteAsset": "USDC", "contractType": "PERPETUAL", "status": "TRADING", "onboardDate": old},
            ]
        }
        tickers = [
            {"symbol": "GOODUSDT", "quoteVolume": "1000"},
            {"symbol": "LOWUSDT", "quoteVolume": "10"},
            {"symbol": "TOONEWUSDT", "quoteVolume": "5000"},
            {"symbol": "COINUSDC", "quoteVolume": "9000"},
        ]
        config = {
            "minimum_contract_age_hours": 720,
            "quote_asset": "USDT",
            "contract_type": "PERPETUAL",
            "status": "TRADING",
            "discovery_top_n": 1,
        }
        selected = discover_symbols(exchange, tickers, now, config)
        self.assertEqual([row["symbol"] for row in selected], ["GOODUSDT"])

    def test_runner_and_workflow_keep_v15_paper_only(self) -> None:
        runner = (PROJECT / "scripts" / "paper_once_v15.py").read_text()
        for forbidden in ("create_order", "create_market_order", "apiKey", "secret"):
            self.assertNotIn(forbidden, runner)
        workflow = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
        for value in (
            "sync_paper_data_v15.py",
            "paper_once_v15.py",
            "verify_v15_cycle.py",
            "paper_v15_state.json",
            "paper_v15_ledger.json",
        ):
            self.assertIn(value, workflow)


if __name__ == "__main__":
    unittest.main()

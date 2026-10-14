"""End-to-end paper generator smoke tests without exchange data, network or disk writes.

These execute the REAL main() runner with isolated synthetic dependencies.
They catch NameError on imported globals and verify the immutable publication
firewall is reached before ANY state/ledger write. No economics or holdout.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "paper_once_v99_research_variants_v2.py"
TRAIN_END = pd.Timestamp("2024-01-18T00:00:00+00:00")
BOUNDARY = pd.Timestamp("2026-09-16T13:00:00+00:00")
LAST = BOUNDARY + pd.Timedelta(hours=1)
NAMES = ("r98", "f1", "f3", "f7", "f12")


class FirewallReached(RuntimeError):
    pass


def build_fixture(guard_error=FirewallReached("QUARANTINE")):
    """Prepare synthetic data and import REAL runner under mock dependency modules."""
    observations = pd.to_datetime([
        "2024-01-16T12:00:00Z", "2024-01-17T23:00:00Z",
        "2024-01-18T00:00:00Z", BOUNDARY, LAST,
    ], utc=True)
    equity = pd.Series([100.0, 110.0, 900.0, 1300.0, 1400.0], index=observations)
    targets = pd.DataFrame({"BTCUSDT": [0.0, 0.2]}, index=pd.DatetimeIndex([BOUNDARY, LAST]))
    result = types.SimpleNamespace(equity=equity)
    data = types.SimpleNamespace(close=pd.DataFrame({"BTCUSDT": [100.0]}, index=pd.DatetimeIndex([LAST])))
    tracks = {name: (targets, result) for name in NAMES}
    captured = []
    writes = []

    base = types.ModuleType("paper_once_v99_research_variants")
    base.p1 = types.SimpleNamespace(TRAIN_END=TRAIN_END)
    base.build_variants = lambda: (data, tracks, [], {"source": "synthetic_fixture"})
    base.load_state = lambda: {
        "initialized_at_utc": "2026-09-16T13:00:00+00:00",
        "paper_start_after_timestamp": BOUNDARY.isoformat(),
    }
    base.VERSION = "v99-research-five-v1"
    base.BASE_CAPITAL_BRL = 10000.0
    base.VARIANT_META = {key: {"label": key, "status": "tracking"} for key in NAMES}
    base.REFERENCE_BACKTEST = {key: {"researchGate": "REFERENCE"} for key in NAMES}
    base.STATE_PATH = Path("/nonexistent/state.json")
    base.SNAPSHOT_PATH = Path("/nonexistent/snapshot.json")
    base.LEDGER_PATH = Path("/nonexistent/ledger.json")
    base.write_json = lambda path, payload: writes.append(path)

    def ledger_stub(key, targets, result, paper_start, latest):
        assert paper_start == BOUNDARY
        assert latest == LAST
        return {
            "label": key,
            "summary": {"current_capital_brl": 10100.0,
                        "forward_return_pct": 1.0,
                        "gross_exposure_pct": 20.0},
            "assets": {},
            "equity_curve": [
                {"timestamp": BOUNDARY.isoformat(), "capital_brl": 10000.0},
                {"timestamp": LAST.isoformat(), "capital_brl": 10100.0},
            ],
            "real_orders_enabled": False,
        }
    base.variant_ledger = ledger_stub

    guard = types.ModuleType("v99_phase195bj_paper_publication_guard")
    def firewall(ledger):
        captured.append(ledger)
        raise guard_error
    guard.enforce_published = firewall

    name = "_isolated_v99_r106_real_main"
    spec = importlib.util.spec_from_file_location(name, RUNNER)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {
        "paper_once_v99_research_variants": base,
        "v99_phase195bj_paper_publication_guard": guard,
    }):
        spec.loader.exec_module(module)
    return module, captured, writes


class TestRealRunnerIntegration(unittest.TestCase):
    def test_real_main_reaches_firewall_with_all_five_without_name_error(self):
        module, captured, writes = build_fixture()
        with self.assertRaises(FirewallReached):
            module.main()
        self.assertEqual(len(captured), 1)
        self.assertEqual(writes, [])
        ledger = captured[0]
        self.assertEqual(set(ledger["variants"]), set(NAMES))
        self.assertEqual(set(ledger["backtest_reference"]), set(NAMES))
        for key in NAMES:
            series = ledger["backtest_reference"][key]["curve"]
            self.assertEqual(len(series), 2)
            self.assertTrue(all(pd.Timestamp(x["timestamp"]) < TRAIN_END for x in series))
            self.assertEqual(series[-1]["timestamp"], "2024-01-17T23:00:00+00:00")
            self.assertEqual(len(ledger["variants"][key]["operations"]), 1)
        self.assertEqual(ledger["paper_start_after_timestamp"], BOUNDARY.isoformat())

    def test_guard_rejection_cannot_write_or_publish(self):
        module, captured, writes = build_fixture(
            RuntimeError("V99 research paper publication BLOCKED: DATA_ONLY/HOLD")
        )
        with self.assertRaisesRegex(RuntimeError, "DATA_ONLY/HOLD"):
            module.main()
        self.assertEqual(len(captured), 1)
        self.assertEqual(writes, [])

    def test_frozen_train_namespace_is_explicit(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("base.p1.TRAIN_END", source)
        self.assertNotIn("daily_backtest_curve(result, paper_start, p1.TRAIN_END)", source)

    def test_runner_no_real_order_path(self):
        code = RUNNER.read_text(encoding="utf-8")
        for forbidden in ("create_order(", "place_order(", "api_secret", "apiKey"):
            self.assertNotIn(forbidden, code)
        self.assertIn("enforce_published(ledger)", code)


if __name__ == "__main__":
    unittest.main()

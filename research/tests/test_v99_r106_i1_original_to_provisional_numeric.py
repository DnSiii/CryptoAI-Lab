"""End-to-end ORIGINAL-shaped 661d orchestration tests. ALL data synthetic."""
from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tests.test_v99_r106_i1_native_event_equity import (
    one_position_fixture, flat_fixture, complete_fixed_decisions, ms,
)
from research.tests.test_v99_r106_i1_original_event_quote_identity import (
    original_row, write_csv_gz,
)
from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_local_tape_import import (
    FIRST, DAYS, SCHEMA as ARCHIVE_SCHEMA,
)
from research.tools.v99_r106_i1_train_numeric_gate import _fold
from research.tools.v99_r106_i1_original_to_provisional_numeric import run


def original_signal_document():
    rows = []
    for day in eligible():
        at = int(day.timestamp() * 1000)
        for asset in ("BTC", "ETH"):
            signal = ("POSITIVE_EX_ANTE_PREMIUM"
                      if at == ms(2021, 12, 13) and asset == "BTC"
                      else "NO_30D_HISTORY")
            rows.append({"decision_ms": at, "asset": asset,
                         "fold": _fold(at), "signal": signal})
    assert len(rows) == 182
    return {
        "schema": "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1",
        "source_original": True,  # SYNTHETIC TEST FORGED PROVENANCE; NOT PROOF
        "structural_only": True, "observations": 182,
        "eligible_weeks": 91, "right_censored_weeks": 3,
        "source_okx_run": 40019588739, "source_dvol_run": 40072202459,
        "economic_train_executed": False, "promotion_authorized": False,
        "rows": rows,
    }


class OriginalToNumericIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.quotes = cls.root / "quotes"
        cls.quotes.mkdir()
        cls.signal = cls.root / "signal.json"
        cls.signal.write_text(json.dumps(original_signal_document()), encoding="utf-8")
        cls.journal = cls.root / "journal.json"

        # Each source quote is a separate synthetic original-row receipt.
        # Build 661 daily gzip files and hash all compressed bytes.
        journal = one_position_fixture()
        arrivals = defaultdict(list)
        seen = set()
        for day in journal["scenarios"]["severe"]:
            for event in day["events"]:
                if event["kind"] == "OPEN":
                    qs = event["quotes"]
                elif event["kind"] == "MARK":
                    qs = [event["short"], event["long"]]
                else:
                    continue
                for q in qs:
                    key = (q["arrival_ms"], q["symbol"])
                    if key in seen:
                        continue
                    seen.add(key)
                    dt = datetime.fromtimestamp(q["arrival_ms"] / 1000, timezone.utc).date()
                    arrivals[dt].append(original_row(q))
        manifest_days = []
        for i in range(DAYS):
            day = FIRST + timedelta(days=i)
            # Always include a harmless source row, so no synthetic day is empty.
            noon = int(datetime(day.year, day.month, day.day, 12,
                                tzinfo=timezone.utc).timestamp()*1000)
            dummy = {
                "exchange": "deribit", "symbol": "BTC-14JAN22-10000-P",
                "timestamp": str((noon-1500)*1000),
                "local_timestamp": str((noon-1000)*1000),
                "bid_price": "0.01", "ask_price": "0.02",
                "bid_amount": "2", "ask_amount": "2",
            }
            rows = sorted([dummy] + arrivals[day],
                          key=lambda r: int(r["local_timestamp"]))
            path = cls.quotes / (day.isoformat() + ".csv.gz")
            write_csv_gz(path, rows)
            manifest_days.append({
                "date": day.isoformat(), "file": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "rows": len(rows), "complete_capture": True,
            })
        manifest = {
            "schema": ARCHIVE_SCHEMA, "fixture": False, "venue": "deribit",
            "train_start": FIRST.isoformat(),
            "train_end_exclusive": (FIRST + timedelta(days=DAYS)).isoformat(),
            "license_evidence_sha256_not_legal_verification": "a"*64,
            "days": manifest_days,
        }
        (cls.quotes / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def document(self, *, opening=True):
        doc = one_position_fixture() if opening else flat_fixture()
        doc["fixture"] = False
        if opening:
            ledger = complete_fixed_decisions(one_open=True)
        else:
            ledger = complete_fixed_decisions(one_open=True)
            for row in ledger:
                if row["action"] == "OPEN":
                    row["action"] = "CASH"
                    row["reason"] = "RISK_VETO"
        doc["scenario_decisions"] = {
            "severe": copy.deepcopy(ledger),
            "supersevere": copy.deepcopy(ledger),
        }
        return doc

    def execute(self, doc, *, root=None):
        self.journal.write_text(json.dumps(doc), encoding="utf-8")
        return run(self.signal, root if root is not None else self.quotes,
                   self.journal)

    def test_full_661d_source_to_provisional_numeric_never_promotes(self):
        report = self.execute(self.document())
        self.assertEqual(report["original_signal_intents_checked"], 180)
        self.assertEqual(report["scenario_opens"], {"severe": 1, "supersevere": 1})
        self.assertGreater(report["original_quote_event_identities_checked"], 2)
        self.assertEqual(report["original_complete_option_lifecycles_certified"], 0)
        self.assertFalse(report["original_options_economic_train_certified"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["numeric_descriptive_only"]["numeric_train_pass_both_scenarios"])
        self.assertEqual(report["numeric_descriptive_only"]["scenarios"]["severe"]["positive_folds"], 1)

    def test_real_missing_original_archive_blocks_before_nav(self):
        with tempfile.TemporaryDirectory() as missing:
            with self.assertRaisesRegex(ValueError, "ORIGINAL_661D_MANIFEST_NOT_DELIVERED"):
                self.execute(self.document(), root=missing)

    def test_forged_signal_rejected_before_original_market(self):
        doc = self.document()
        doc["scenario_decisions"]["severe"][0]["signal"] = "NO_PREMIUM"
        with self.assertRaisesRegex(ValueError, "PROPOSED_DECISION_CONTRADICTS_ORIGINAL_SIGNAL"):
            self.execute(doc)

    def test_cross_scenario_signal_forgery_rejected(self):
        doc = self.document()
        doc["scenario_decisions"]["supersevere"][0]["signal"] = "NO_PREMIUM"
        with self.assertRaisesRegex(ValueError, "PROPOSED_DECISION_CONTRADICTS_ORIGINAL_SIGNAL"):
            self.execute(doc)

    def test_forged_original_bbo_rejected_before_numeric(self):
        doc = self.document()
        opening = next(e for d in doc["scenarios"]["severe"]
                       for e in d["events"] if e["kind"] == "OPEN")
        opening["quotes"][0]["bid_coin"] = "0.06"
        with self.assertRaisesRegex(ValueError, "SCENARIO_SOURCE_QUOTE_MISMATCH|NATIVE_EVENT_QUOTE_NOT_EQUAL_ORIGINAL_SOURCE"):
            self.execute(doc)

    def test_zero_original_event_identities_is_not_source_proof(self):
        with self.assertRaisesRegex(ValueError, "ZERO_ORIGINAL_BBO_EVENT_IDENTITIES"):
            self.execute(self.document(opening=False))

    def test_fixture_and_self_declared_promotion_rejected(self):
        doc = self.document()
        doc["fixture"] = True
        with self.assertRaisesRegex(ValueError, "NONFIXTURE_TWO_SCENARIO_JOURNAL_REQUIRED"):
            self.execute(doc)
        doc["fixture"] = False
        doc["promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "SELF_DECLARED_SOURCE_CERTIFICATION_FORBIDDEN"):
            self.execute(doc)


if __name__ == "__main__":
    unittest.main()

"""661-day original-shaped synthetic controls; NO original economic ROI."""
from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tests.test_v99_r106_i1_source_driven_entry_book import (
    source_row, intents, HEADER,
)
from research.tools.v99_r106_i1_local_tape_import import FIRST, DAYS, SCHEMA
from research.tools.v99_r106_i1_source_driven_entry_book import build
from research.tools.v99_r106_i1_source_to_mark_event_spine import compile_spine
from research.verification.independent_v99_r106_i1_source_mark_spine_oracle import verify as independent_spine

SHORT = "BTC-14JAN22-36000-P"
LONG = "BTC-14JAN22-32000-P"
ENTRY = int(datetime(2021, 12, 13, tzinfo=timezone.utc).timestamp()*1000)


def _write(path, rows):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


class SourceToMarkEventSpineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.manifest_days = []
        for i in range(DAYS):
            d = FIRST + timedelta(days=i)
            t = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            rows = [
                source_row(SHORT, t, 23, 59, 58),
                source_row(LONG, t, 23, 59, 58, "0.01", "0.012"),
                source_row("ETH-14JAN22-2700-P", t, 23, 59, 58),
            ]
            path = cls.root / (d.isoformat() + ".csv.gz")
            _write(path, rows)
            cls.manifest_days.append({
                "date": d.isoformat(), "file": path.name, "rows": len(rows),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "complete_capture": True,
            })
        cls.manifest = {
            "schema": SCHEMA, "fixture": False, "venue": "deribit",
            "train_start": FIRST.isoformat(),
            "train_end_exclusive": (FIRST+timedelta(days=DAYS)).isoformat(),
            "license_evidence_sha256_not_legal_verification": "f"*64,
            "days": cls.manifest_days,
        }
        cls._save()
        cls.baseline_rows = {d["date"]: d["rows"] for d in cls.manifest_days}
        cls.entry = build(cls.root, intents())
        cls.plan = [{"position_id": "BTC-W1", "decision_ms": ENTRY,
                     "asset": "BTC", "short_symbol": SHORT, "long_symbol": LONG}]

    @classmethod
    def _save(cls):
        (cls.root/"manifest.json").write_text(json.dumps(cls.manifest))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def tearDown(self):
        for name, raw in getattr(self, "changed", []):
            (self.root/name).write_bytes(raw)
        self.changed = []
        for item in self.manifest_days:
            item["rows"] = self.baseline_rows[item["date"]]
            item["sha256"] = hashlib.sha256(
                (self.root/item["file"]).read_bytes()).hexdigest()
        self._save()

    def _change(self, day, rows):
        name = day+".csv.gz"
        path = self.root/name
        self.changed = getattr(self, "changed", [])
        self.changed.append((name, path.read_bytes()))
        _write(path, rows)
        item = next(d for d in self.manifest_days if d["date"] == day)
        item["rows"] = len(rows)
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self._save()

    def test_661_day_source_spine_real_contract_identity(self):
        result = compile_spine(self.root, self.entry, self.plan)
        self.assertEqual(len(result["days"]), DAYS)
        self.assertEqual(result["unverified_position_plan_count"], 1)
        self.assertEqual(result["same_contract_daily_marks"], 32)
        self.assertEqual(result["expiry_due_count"], 1)
        monday = next(r for r in result["days"] if r["ts_ms"] ==
                      int(datetime(2021,12,13,23,59,59,tzinfo=timezone.utc).timestamp()*1000))
        self.assertEqual([e["kind"] for e in monday["market_events"]],
                         ["OPEN_SOURCE_ONLY", "MARK_SOURCE_ONLY"])
        self.assertEqual(monday["market_events"][1]["short"]["symbol"], SHORT)
        self.assertFalse(result["native_economic_train_executed"])
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["original_delivery_index_authenticated"])
        independently = independent_spine(self.root, self.entry, result)
        self.assertEqual(independently["independent_held_contract_mark_pairs"], 32)
        self.assertEqual(independently["independent_expiry_due"], 1)

    def test_missing_exact_held_mark_fails_closed(self):
        d = datetime(2021, 12, 15, tzinfo=timezone.utc)
        self._change("2021-12-15", [source_row(SHORT,d,23,59,58)])
        with self.assertRaisesRegex(ValueError, "STALE_FUTURE_OR_WRONG_ORIGINAL_HELD_MARK"):
            compile_spine(self.root, build(self.root, intents()), self.plan)

    def test_later_invalid_held_book_revokes_earlier_valid(self):
        d = datetime(2021, 12, 16, tzinfo=timezone.utc)
        rows = [source_row(SHORT,d,23,59,58),
                source_row(LONG,d,23,59,58,"0.01","0.012")]
        late = source_row(SHORT,d,23,59,58,bid="0",ask="0.052")
        late["local_timestamp"] = str(int(late["local_timestamp"])+500000)
        late["timestamp"] = str(int(late["timestamp"])+500000)
        rows.append(late)
        self._change("2021-12-16", rows)
        with self.assertRaisesRegex(ValueError, "LAST_INVALID_HELD_MARK_REVOKES_EARLIER"):
            compile_spine(self.root, build(self.root, intents()), self.plan)

    def test_changed_original_bytes_without_manifest_rejected(self):
        path = self.root/"2021-12-20.csv.gz"
        self.changed = [(path.name, path.read_bytes())]
        with path.open("ab") as f:
            f.write(b"altered")
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_SHA256_MISMATCH"):
            compile_spine(self.root, self.entry, self.plan)

    def test_duplicate_and_invented_plan_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_UNSCHEDULED"):
            compile_spine(self.root, self.entry, self.plan*2)
        forged = copy.deepcopy(self.plan)
        forged[0]["long_symbol"] = "BTC-14JAN22-31000-P"
        with self.assertRaisesRegex(ValueError, "POSITION_NOT_IN_FULL_ORIGINAL"):
            compile_spine(self.root, self.entry, forged)

    def test_independent_oracle_rejects_forged_original_mark(self):
        result = compile_spine(self.root, self.entry, self.plan)
        mark = next(e for day in result["days"] for e in day["market_events"]
                    if e["kind"] == "MARK_SOURCE_ONLY")
        mark["short"]["bid_coin"] = "0.99"
        with self.assertRaisesRegex(ValueError, "ORACLE_MARK_NOT_EQUAL_ORIGINAL"):
            independent_spine(self.root, self.entry, result)

    def test_independent_oracle_rejects_missing_expiry(self):
        result = compile_spine(self.root, self.entry, self.plan)
        expiry = next(day for day in result["days"] if any(
            e["kind"] == "SETTLEMENT_DUE_SOURCE_ONLY" for e in day["market_events"]))
        expiry["market_events"] = []
        with self.assertRaisesRegex(ValueError, "ORACLE_MISSING_DUPLICATED"):
            independent_spine(self.root, self.entry, result)

    def test_missing_original_manifest_no_fixture_fallback(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "ORIGINAL_661D_MANIFEST_NOT_DELIVERED"):
                compile_spine(root, self.entry, self.plan)


if __name__ == "__main__":
    unittest.main()

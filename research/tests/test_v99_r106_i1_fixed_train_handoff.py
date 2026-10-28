"""Deterministic handoff controls. In-memory fixtures are NEVER original source."""
import unittest

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_d1_real_train_source_join import FOLD_EDGES
from research.tools.v99_r106_i1_fixed_train_handoff import join_reports


def sample():
    decisions = eligible(False)
    rows = []
    for d in decisions:
        at = int(d.timestamp() * 1000)
        fold = next(i for i in range(1, 6)
                    if FOLD_EDGES[i-1] <= at < FOLD_EDGES[i])
        for asset in ("BTC", "ETH"):
            rows.append(dict(decision_ms=at, asset=asset, fold=fold,
                             signal="POSITIVE_EX_ANTE_PREMIUM"))
    signal = dict(schema="V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1",
                  source_original=True, observations=182, eligible_weeks=91,
                  economic_train_executed=False, promotion_authorized=False,
                  rows=rows)
    weekly = []
    for d in eligible(True):
        for asset in ("BTC", "ETH"):
            weekly.append(dict(decision_utc=d.date().isoformat(), asset=asset,
                               causal_entry_and_same_contract_pair_presence=False))
    weekly[0]["causal_entry_and_same_contract_pair_presence"] = True
    source = dict(schema="V99_I1_661_DAY_LIFECYCLE_DAILY_PRESENCE_REPORT_V1",
                  source_scope="FIXED_28_35D", days=661, asset_weeks=180,
                  certified_complete_option_lifecycles=0,
                  source_manifest_self_declared_not_vendor_certified=True,
                  same_contract_pair_still_not_executable_or_settlement_certified=True,
                  fixture=True, weekly=weekly, economic_train_executed=False,
                  validation_opened=False, holdout_opened=False,
                  orders_enabled=False, promotion_authorized=False)
    return signal, source


class Fixed90WeekHandoffTests(unittest.TestCase):
    def join(self, signal, source):
        return join_reports(signal, source, signal_sha256="test-signal-fixture",
                            source_manifest_sha256="test-source-fixture")

    def test_90_week_join_and_91st_week_right_censored(self):
        signal, source = sample()
        report = self.join(signal, source)
        self.assertEqual(report["fixed_maturity_eligible_asset_weeks"], 180)
        self.assertEqual(report["right_censored_signal_asset_weeks"], 2)
        self.assertEqual(report["signal_and_necessary_source_asset_weeks"], 1)
        self.assertEqual(sum(v["intersection"] for v in report["folds"].values()), 1)
        self.assertEqual(report["status"], "BLOCKED_FIXTURE_SOURCE_NOT_ORIGINAL")
        self.assertFalse(report["economic_train_executed"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["native_economics_verified"])

    def test_no_signal_no_intersection(self):
        signal, source = sample()
        signal["rows"][0]["signal"] = "NO_PREMIUM"
        report = self.join(signal, source)
        self.assertEqual(report["signal_and_necessary_source_asset_weeks"], 0)

    def test_duplicate_signal_rejected(self):
        signal, source = sample()
        signal["rows"][1] = dict(signal["rows"][0])
        with self.assertRaisesRegex(ValueError, "SIGNAL_GRID"):
            self.join(signal, source)

    def test_tampered_fold_rejected(self):
        signal, source = sample()
        signal["rows"][0]["fold"] = 5
        with self.assertRaisesRegex(ValueError, "FOLD_OR_SOURCE"):
            self.join(signal, source)

    def test_reordered_source_rejected(self):
        signal, source = sample()
        source["weekly"][0], source["weekly"][1] = source["weekly"][1], source["weekly"][0]
        with self.assertRaisesRegex(ValueError, "FOLD_OR_SOURCE"):
            self.join(signal, source)

    def test_source_fixture_cannot_promote(self):
        signal, source = sample()
        for row in source["weekly"]:
            row["causal_entry_and_same_contract_pair_presence"] = True
        report = self.join(signal, source)
        self.assertEqual(report["signal_and_necessary_source_asset_weeks"], 180)
        self.assertEqual(report["status"], "BLOCKED_FIXTURE_SOURCE_NOT_ORIGINAL")
        self.assertFalse(report["economic_train_executed"])
        self.assertFalse(report["promotion_authorized"])

    def test_nonoriginal_signal_rejected(self):
        signal, source = sample()
        signal["source_original"] = False
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_OR_NONORIGINAL"):
            self.join(signal, source)

    def test_legacy_182_week_source_rejected(self):
        signal, source = sample()
        source["asset_weeks"] = 182
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_OR_NONFIXED"):
            self.join(signal, source)

    def test_forged_economic_status_rejected(self):
        signal, source = sample()
        source["economic_train_executed"] = True
        with self.assertRaisesRegex(ValueError, "FORGED_SOURCE"):
            self.join(signal, source)

    def test_last_right_censored_signal_cannot_leak(self):
        signal, source = sample()
        signal["rows"][-1]["decision_ms"] += 7 * 86400000
        with self.assertRaisesRegex(ValueError, "SIGNAL_GRID"):
            self.join(signal, source)


    def test_end_to_end_661_day_source_and_independent_byte_oracle(self):
        """Exercise actual scanner -> independent reparse -> 90-week join.

        Explicitly synthetic 661-day tape; never economic or original evidence.
        """
        import csv
        import gzip
        import hashlib
        import io
        import json
        import tempfile
        from datetime import date, datetime, timedelta, timezone
        from pathlib import Path
        from research.tools.v99_r106_i1_fixed_train_handoff import run

        signal, _ = sample()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "synthetic_661_day_tape"
            archive.mkdir()
            entries = []
            start = date(2021, 12, 9)
            headers = ["exchange", "symbol", "timestamp", "local_timestamp",
                       "bid_price", "ask_price", "bid_amount", "ask_amount"]
            for i in range(661):
                day = start + timedelta(days=i)
                expiry = day + timedelta(days=28)
                epoch = int(datetime(day.year, day.month, day.day,
                                     tzinfo=timezone.utc).timestamp() * 1_000_000)
                buffer = io.StringIO(newline="")
                writer = csv.writer(buffer)
                writer.writerow(headers)
                for k, (asset, strike) in enumerate((("BTC", 30000), ("ETH", 2000))):
                    t = str(epoch + (k + 1) * 1_000_000)
                    writer.writerow(("deribit",
                                     f"{asset}-{expiry.strftime('%d%b%y').upper()}-{strike}-P",
                                     t, t, "0.02", "0.025", "2", "2"))
                compressed = gzip.compress(buffer.getvalue().encode())
                name = day.isoformat() + ".csv.gz"
                (archive / name).write_bytes(compressed)
                entries.append(dict(date=day.isoformat(), file=name,
                                    sha256=hashlib.sha256(compressed).hexdigest(),
                                    rows=2, complete_capture=True))
            manifest = dict(schema="V99_I1_FIXED_28_35D_661_DAY_TRAIN_LIFECYCLE_TAPE_V1",
                            venue="deribit", fixture=True,
                            train_start="2021-12-09",
                            train_end_exclusive="2023-10-01", days=entries)
            (archive / "manifest.json").write_text(json.dumps(manifest))
            signal_file = root / "synthetic_signal.json"
            signal_file.write_text(json.dumps(signal))
            report = run(str(signal_file), str(archive), str(root / "report.json"))
            self.assertEqual(report["status"], "BLOCKED_FIXTURE_SOURCE_NOT_ORIGINAL")
            self.assertEqual(report["fixed_maturity_eligible_asset_weeks"], 180)
            self.assertEqual(report["signal_and_necessary_source_asset_weeks"], 0)
            self.assertFalse(report["economic_train_executed"])
            self.assertFalse(report["promotion_authorized"])

            # A synthetic CSV relabeled as 'original' cannot reach the
            # 661-day handoff without original first-party signal receipts.
            # This is a direct executable-run gate, not just workflow policy.
            manifest["fixture"] = False
            (archive / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "ORIGINAL_SIGNAL_REPLAY_RECEIPTS_REQUIRED"):
                run(str(signal_file), str(archive), str(root / "forged.json"))
            with self.assertRaisesRegex(ValueError, "ORIGINAL_SIGNAL_REPLAY_FAILED"):
                run(str(signal_file), str(archive), str(root / "forged.json"),
                    str(root / "missing_okx"), str(root / "missing_dvol"))
            self.assertFalse((root / "forged.json").exists())


if __name__ == "__main__":
    unittest.main()

"""Offline-only tests of licensed-transfer preflight; synthetic bytes are NOT market evidence."""
import csv
import gzip
import hashlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_tardis_licensed_transfer import transfer

DAY = datetime(2021, 12, 9, tzinfo=timezone.utc)
DAY_US = int(DAY.timestamp() * 1_000_000)


def fake_gzip(day=DAY, *, missing_hour=None, missing_asset_hour=None):
    # Original-shaped OFFLINE source only; 24 distinct UTC arrival hours
    # for both assets, matching the downstream 661-day importer contract.
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(("exchange", "symbol", "timestamp", "local_timestamp",
                     "bid_price", "ask_price", "bid_amount", "ask_amount"))
    expiry = (day + timedelta(days=28)).strftime("%d%b%y").upper()
    day_us = int(day.timestamp() * 1_000_000)
    for hour in range(24):
        if hour == missing_hour:
            continue
        for i, asset, strike in ((1, "BTC", 30000), (2, "ETH", 2000)):
            if missing_asset_hour == (asset, hour):
                continue
            at_us = day_us + hour * 3_600_000_000 + i * 1_000_000
            writer.writerow(("deribit", f"{asset}-{expiry}-{strike}-P",
                             at_us, at_us, "0.02", "0.025", "1", "1"))
    return gzip.compress(buffer.getvalue().encode())


def scope_bytes(valid=True, *, start="2021-01-01T00:00:00Z",
                end="2024-01-01T00:00:00Z", symbols=None, exchange="deribit"):
    return json.dumps([{"exchange": exchange, "from": start, "to": end,
                        "dataPlan": "options" if valid else "perpetuals",
                        "symbols": ["OPTIONS"] if symbols is None else symbols}]).encode()


class Response:
    def __init__(self, body, *, status=200, content_type="application/gzip"):
        self.body = io.BytesIO(body)
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.body.close()
    def read(self, n=-1):
        return self.body.read(n)


class Opener:
    def __init__(self, *, valid_scope=True, body=None, content_type="application/gzip", day=DAY, scope_kwargs=None):
        self.valid_scope = valid_scope
        self.scope_kwargs = scope_kwargs or {}
        self.day = day
        self.body = fake_gzip(day) if body is None else body
        self.content_type = content_type
        self.urls = []
    def __call__(self, request, timeout=None):
        self.urls.append(request.full_url)
        if request.full_url.endswith("api-key-info"):
            return Response(scope_bytes(self.valid_scope, **self.scope_kwargs), content_type="application/json")
        if not request.full_url.endswith(self.day.strftime("/%Y/%m/%d/OPTIONS.csv.gz")):
            raise AssertionError("UNEXPECTED_OR_SEALED_NETWORK_REQUEST")
        return Response(self.body, content_type=self.content_type)


class LicensedTransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "original"
        self.license = Path(self.tmp.name) / "vendor-grant.txt"
        self.license.write_text("OFFLINE TEST PLACEHOLDER NOT A REAL LICENSE")
    def call(self, opener, **kw):
        kw.setdefault("max_days", 1)
        return transfer(self.root, execute=True, key="test-secret",
                        license_evidence=self.license, opener=opener, **kw)

    def test_default_dry_run_no_key_no_network(self):
        def no_network(*args, **kwargs):
            raise AssertionError("DRY_RUN_MADE_NETWORK_REQUEST")
        report = transfer(self.root, opener=no_network)
        self.assertEqual(report["planned_train_days"], 1)
        self.assertFalse(report["economic_train_executed"])
        self.assertFalse(self.root.exists())

    def test_missing_key_and_license_refused_before_network(self):
        opener = Opener()
        with self.assertRaisesRegex(ValueError, "API_KEY_NOT_CONFIGURED"):
            transfer(self.root, execute=True, key="", license_evidence=self.license, opener=opener)
        with self.assertRaisesRegex(ValueError, "LICENSE_EVIDENCE_REQUIRED"):
            transfer(self.root, execute=True, key="test-secret", opener=opener)
        self.assertEqual(opener.urls, [])

    def test_entitlement_must_cover_original_options(self):
        opener = Opener(valid_scope=False)
        with self.assertRaisesRegex(ValueError, "ENTITLEMENT_UNVERIFIED"):
            self.call(opener)
        self.assertEqual(len(opener.urls), 1)
        self.assertFalse(self.root.exists())

    def test_atomic_transfer_then_valid_existing_skip(self):
        opener = Opener()
        first = self.call(opener)
        self.assertEqual(first["downloaded_days"], 1)
        self.assertFalse(first["vendor_gap_attestation_verified"])
        self.assertFalse(first["promotion_authorized"])
        self.assertEqual((self.root / "2021-12-09.csv.gz").read_bytes(), opener.body)
        self.assertFalse((self.root / "manifest.json").exists())
        self.assertEqual(len(list(self.root.glob("*.part"))), 0)
        again = self.call(opener)
        self.assertEqual(again["downloaded_days"], 0)
        self.assertEqual(again["preexisting_valid_days"], 1)
        self.assertEqual(len(opener.urls), 3)

    def test_non_sample_paid_day_without_downloading_earlier_188_days(self):
        day = datetime(2022, 6, 15, tzinfo=timezone.utc)
        opener = Opener(day=day)
        result = self.call(opener, start_date="2022-06-15")
        self.assertEqual(result["planned_train_days"], 1)
        self.assertEqual(result["downloaded_days"], 1)
        self.assertEqual(len(opener.urls), 2)  # scope + one exact source day
        self.assertTrue(opener.urls[-1].endswith("/2022/06/15/OPTIONS.csv.gz"))
        self.assertEqual((self.root / "2022-06-15.csv.gz").read_bytes(),
                         opener.body)
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())
        self.assertFalse(result["economic_train_executed"])
        again = self.call(opener, start_date="2022-06-15")
        self.assertEqual(again["preexisting_valid_days"], 1)
        self.assertEqual(again["downloaded_days"], 0)

    def test_exact_2022_january_23_one_day_entitlement_no_full_train_purchase(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        scope = {"start": "2022-01-23T00:00:00Z",
                 "end": "2022-01-24T00:00:00Z"}
        opener = Opener(day=day, scope_kwargs=scope)
        result = self.call(opener, start_date="2022-01-23")
        self.assertEqual(result["downloaded_days"], 1)
        self.assertTrue(opener.urls[-1].endswith("/2022/01/23/OPTIONS.csv.gz"))
        self.assertEqual((self.root/"2022-01-23.csv.gz").read_bytes(), opener.body)
        self.assertFalse(result["full_661_days_transferred"])
        self.assertFalse(result["vendor_gap_attestation_verified"])
        self.assertFalse(result["economic_train_executed"])
        self.assertEqual(result["preselected_one_day_source_gate"]["status"],
                         "SOURCE_VETO_NOT_LOSS")
        self.assertEqual(result["preselected_one_day_source_gate"]["fresh_synchronized_two_strike_pairs_by_asset"],
                         {"BTC": 0, "ETH": 0})
        self.assertTrue(result["preselected_one_day_source_gate"]["independent_original_byte_replay_passed"])
        self.assertFalse(result["preselected_one_day_source_gate"]["promotion_authorized"])

    def test_paid_target_day_with_two_synchronized_strikes_is_source_only(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        raw = gzip.decompress(fake_gzip(day)).decode()
        rows = list(csv.DictReader(io.StringIO(raw)))
        stamp = int((day + timedelta(hours=23, minutes=59, seconds=58)).timestamp() * 1_000_000)
        for asset, strikes in (("BTC", (30000, 28000)),
                               ("ETH", (2000, 1800))):
            for strike in strikes:
                rows.append({
                    "exchange": "deribit",
                    "symbol": f"{asset}-25FEB22-{strike}-P",
                    "timestamp": str(stamp), "local_timestamp": str(stamp),
                    "bid_price": "0.05", "ask_price": "0.052",
                    "bid_amount": "2", "ask_amount": "2",
                })
        rows.sort(key=lambda row: int(row["local_timestamp"]))
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=(
            "exchange", "symbol", "timestamp", "local_timestamp",
            "bid_price", "ask_price", "bid_amount", "ask_amount"))
        writer.writeheader()
        writer.writerows(rows)
        source = gzip.compress(out.getvalue().encode())
        opener = Opener(day=day, body=source, scope_kwargs={
            "start": "2022-01-23T00:00:00Z",
            "end": "2022-01-24T00:00:00Z"})
        report = self.call(opener, start_date="2022-01-23")
        gate = report["preselected_one_day_source_gate"]
        self.assertEqual(gate["status"], "SOURCE_FEASIBLE_ONLY_NOT_ECONOMICS")
        self.assertEqual(gate["fresh_synchronized_two_strike_pairs_by_asset"],
                         {"BTC": 1, "ETH": 1})
        self.assertTrue(gate["independent_original_byte_replay_passed"])
        self.assertFalse(gate["vendor_completeness_attested"])
        self.assertEqual(gate["certified_lifecycles"], 0)
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["economic_train_executed"])
        self.assertEqual(len(opener.urls), 2)

    def test_target_day_independent_oracle_failure_never_publishes_new_original(self):
        # A valid vendor gzip + SHA + 24h coverage must not be published if
        # the independent target-day source replay fails afterward.
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        opener = Opener(day=day, scope_kwargs={
            "start": "2022-01-23T00:00:00Z",
            "end": "2022-01-24T00:00:00Z"})
        target = self.root / "2022-01-23.csv.gz"
        with patch(
            "research.tools.v99_r106_i1_single_day_source_feasibility.inspect",
            side_effect=ValueError("INDEPENDENT_ORIGINAL_DAY_REPLAY_DISAGREEMENT")
        ) as oracle:
            with self.assertRaisesRegex(
                ValueError, "INDEPENDENT_ORIGINAL_DAY_REPLAY_DISAGREEMENT"
            ):
                self.call(opener, start_date="2022-01-23")
        self.assertEqual(oracle.call_count, 1)
        staged = Path(oracle.call_args.args[0])
        self.assertEqual(staged.name, "2022-01-23.csv.gz")
        self.assertNotEqual(staged.parent, self.root)
        self.assertFalse(target.exists())
        self.assertFalse(staged.exists())
        self.assertEqual(list(self.root.glob("*.part")), [])
        self.assertEqual(list(self.root.glob(".target-day-gate-*")), [])
        self.assertEqual(len(opener.urls), 2)

    def test_existing_target_day_is_preserved_on_independent_oracle_failure(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        body = fake_gzip(day)
        self.root.mkdir()
        target = self.root / "2022-01-23.csv.gz"
        target.write_bytes(body)
        opener = Opener(day=day, scope_kwargs={
            "start": "2022-01-23T00:00:00Z",
            "end": "2022-01-24T00:00:00Z"})
        with patch(
            "research.tools.v99_r106_i1_single_day_source_feasibility.inspect",
            side_effect=ValueError("INDEPENDENT_ORIGINAL_DAY_REPLAY_DISAGREEMENT")
        ):
            with self.assertRaisesRegex(
                ValueError, "INDEPENDENT_ORIGINAL_DAY_REPLAY_DISAGREEMENT"
            ):
                self.call(opener, start_date="2022-01-23")
        self.assertEqual(target.read_bytes(), body)
        self.assertEqual(list(self.root.glob("*.part")), [])
        self.assertEqual(list(self.root.glob(".target-day-gate-*")), [])
        self.assertEqual(len(opener.urls), 1)  # scope only, never re-download

    def test_external_vendor_digest_match_is_source_only_not_legal_certification(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        body = fake_gzip(day)
        digest = hashlib.sha256(body).hexdigest()
        opener = Opener(day=day, body=body)
        report = self.call(opener, start_date="2022-01-23",
                           expected_sha256=digest)
        gate = report["preselected_one_day_source_gate"]
        self.assertTrue(gate["external_sha256_matched"])
        self.assertEqual(gate["original_gzip_sha256"], digest)
        self.assertEqual(gate["status"], "SOURCE_VETO_NOT_LOSS")
        self.assertFalse(gate["vendor_completeness_attested"])
        self.assertFalse(report["economic_train_executed"])

    def test_wrong_vendor_digest_never_publishes_new_day_or_reuses_existing(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        body = fake_gzip(day)
        opener = Opener(day=day, body=body)
        with self.assertRaisesRegex(ValueError, "EXTERNAL_SOURCE_SHA256_MISMATCH"):
            self.call(opener, start_date="2022-01-23",
                      expected_sha256="0" * 64)
        target = self.root / "2022-01-23.csv.gz"
        self.assertFalse(target.exists())
        self.assertEqual(list(self.root.glob("*.part")), [])
        self.root.mkdir(exist_ok=True)
        target.write_bytes(body)
        with self.assertRaisesRegex(ValueError, "EXTERNAL_SOURCE_SHA256_MISMATCH"):
            self.call(opener, start_date="2022-01-23",
                      expected_sha256="0" * 64)
        self.assertEqual(target.read_bytes(), body)

    def test_external_digest_wrong_scope_or_format_vetoes_before_network(self):
        for start, digest in (("2022-01-23", "not-a-digest"),
                              ("2022-01-23", "A" * 64),
                              ("2022-06-15", "0" * 64)):
            opener = Opener()
            with self.subTest(start=start, digest=digest):
                with self.assertRaisesRegex(ValueError,
                                            "INVALID_TARGET_DAY_EXTERNAL_SHA256_REQUEST"):
                    self.call(opener, start_date=start, expected_sha256=digest)
                self.assertEqual(opener.urls, [])
                self.assertFalse(self.root.exists())

    def test_day_only_entitlement_never_authorizes_adjacent_day_or_full_train(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        scope = {"start": "2022-01-23T00:00:00Z",
                 "end": "2022-01-24T00:00:00Z"}
        for start, count in (("2022-01-23", 2), ("2022-01-22", 1),
                             ("2021-12-09", 1)):
            opener = Opener(day=day, scope_kwargs=scope)
            with self.subTest(start=start, count=count):
                with self.assertRaisesRegex(ValueError, "ENTITLEMENT_UNVERIFIED"):
                    self.call(opener, start_date=start, max_days=count)
                self.assertEqual(len(opener.urls), 1)  # scope only
                self.assertFalse(self.root.exists())

    def test_partial_symbols_wrong_exchange_and_short_grant_fail_closed(self):
        day = datetime(2022, 1, 23, tzinfo=timezone.utc)
        base = {"start": "2022-01-23T00:00:00Z",
                "end": "2022-01-24T00:00:00Z"}
        variants = (
            dict(base, symbols=["BTC-25FEB22-30000-P", "ETH-25FEB22-2000-P"]),
            dict(base, exchange="bitmex"),
            dict(base, end="2022-01-23T23:59:59Z"),
            dict(base, start="2022-01-23T00:00:00"),
        )
        for scope in variants:
            opener = Opener(day=day, scope_kwargs=scope)
            with self.subTest(scope=scope):
                with self.assertRaisesRegex(ValueError, "ENTITLEMENT_UNVERIFIED"):
                    self.call(opener, start_date="2022-01-23")
                self.assertEqual(len(opener.urls), 1)
                self.assertFalse(self.root.exists())

    def test_outside_train_window_rejected_before_network_or_write(self):
        for start, days in (("2023-09-30", 2), ("2023-10-01", 1),
                            ("2021-12-08", 1), ("2022-06-15", 500),
                            ("2022-06-31", 1), ("20220615", 1),
                            (True, 1)):
            opener = Opener()
            with self.subTest(start=start, days=days):
                with self.assertRaisesRegex(ValueError, "INVALID_OR_SEALED_TRAIN_SOURCE_WINDOW"):
                    self.call(opener, start_date=start, max_days=days)
                self.assertEqual(opener.urls, [])
                self.assertFalse(self.root.exists())

    def test_bounded_final_train_day_and_dry_run_no_network(self):
        opener = Opener()
        dry = transfer(self.root, start_date="2023-09-30", max_days=1,
                       opener=opener)
        self.assertEqual(dry["first_day"], "2023-09-30")
        self.assertEqual(dry["last_day"], "2023-09-30")
        self.assertEqual(opener.urls, [])
        self.assertFalse(self.root.exists())

    def test_html_disguised_as_success_refused(self):
        opener = Opener(body=b"<html>paywall</html>", content_type="text/html")
        with self.assertRaisesRegex(ValueError, "NOT_GZIP"):
            self.call(opener)
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())
        self.assertEqual(len(list(self.root.glob("*.part"))), 0)

    def test_corrupt_gzip_crc_refused(self):
        damaged = fake_gzip()[:-5] + b"xxxxx"
        with self.assertRaises(ValueError):
            self.call(Opener(body=damaged))
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())

    def test_partial_23_hour_vendor_day_is_rejected_before_atomic_publish(self):
        partial = fake_gzip(missing_hour=13)
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP"):
            self.call(Opener(body=partial))
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())
        self.assertEqual(list(self.root.glob("*.part")), [])

    def test_one_asset_hour_missing_is_rejected(self):
        partial = fake_gzip(missing_asset_hour=("ETH", 17))
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP"):
            self.call(Opener(body=partial))
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())

    def test_existing_partial_day_never_skipped_or_overwritten(self):
        self.root.mkdir()
        destination = self.root / "2021-12-09.csv.gz"
        original_partial = fake_gzip(missing_hour=7)
        destination.write_bytes(original_partial)
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP"):
            self.call(Opener())
        self.assertEqual(destination.read_bytes(), original_partial)

    def test_existing_invalid_file_never_overwritten(self):
        self.root.mkdir()
        dest = self.root / "2021-12-09.csv.gz"
        dest.write_bytes(b"protected-invalid-original")
        with self.assertRaises(ValueError):
            self.call(Opener())
        self.assertEqual(dest.read_bytes(), b"protected-invalid-original")

    def test_byte_cap_fails_without_partial_published(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_TOO_LARGE"):
            self.call(Opener(), max_day_bytes=10)
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())

    def test_never_request_sealed_or_extra_day(self):
        with self.assertRaisesRegex(ValueError, "INVALID_BOUNDED"):
            transfer(self.root, execute=True, max_days=662,
                     key="test-secret", license_evidence=self.license,
                     opener=Opener())


if __name__ == "__main__":
    unittest.main()

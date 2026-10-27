#!/usr/bin/env python3
"""Offline deterministic synthetic source fixtures; not official archive acceptance."""
import csv
import hashlib
import io
import unittest
import zipfile
from unittest.mock import patch
import hq_gap_aware_spot_source as source
from hq_gap_aware_spot_source import ASSETS, GAP, MONTHS, month_hours, parse_month, window_valid, sha


def fixture(asset, year, month, skip=(), duplicate=False, invalid=False, bad_quote=False, bad_close_time=False, bad_taker=False, bad_schema=False):
    name = f"{asset}-1h-{year}-{month:02d}.csv"
    rows = []
    for t in month_hours(year, month):
        if t in skip:
            continue
        row = [str(t), "100", "110", "90", "105", "1", str(t + 3599999), "100", "5", "0.5", "50", "0"]
        if t == month_hours(year, month)[0]:
            if invalid:
                row[2] = "1"
            if bad_quote:
                row[7] = "10000"
            if bad_close_time:
                row[6] = str(t + 3600000)
            if bad_taker:
                row[10] = "500"
            if bad_schema:
                row.append("extra")
        rows.append(row)
    if duplicate:
        rows.insert(1, rows[0])
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, buffer.getvalue())
    return raw.getvalue()


class HQSourceFixtures(unittest.TestCase):
    def test_known_gap_is_mask_not_synthetic_price(self):
        for asset in ASSETS:
            rows, missing = parse_month(fixture(asset, 2023, 3, skip=(GAP,)), asset, 2023, 3)
            self.assertEqual(missing, [GAP])
            gap = [r for r in rows if int(r[1]) == GAP]
            self.assertEqual(gap, [(asset, str(GAP), "0", "", "", "", "", "")])
            self.assertEqual(sum(r[2] == "1" for r in rows), 743)

    def test_extra_missing_fails(self):
        for asset in ASSETS:
            with self.assertRaisesRegex(ValueError, "HQ_UNEXPECTED_MISSINGNESS"):
                parse_month(fixture(asset, 2023, 3, skip=(GAP, GAP + 3600000)), asset, 2023, 3)

    def test_duplicate_and_bad_ohlc_fail(self):
        for asset in ASSETS:
            with self.assertRaisesRegex(ValueError, "HQ_SPOT_UTC_OR_ORDER"):
                parse_month(fixture(asset, 2022, 12, duplicate=True), asset, 2022, 12)
            with self.assertRaisesRegex(ValueError, "HQ_SPOT_GEOMETRY"):
                parse_month(fixture(asset, 2022, 12, invalid=True), asset, 2022, 12)

    def test_native_spot_conservation_and_schema_fail_closed(self):
        for asset in ASSETS:
            for kw, code in (
                ({"bad_quote": True}, "HQ_SPOT_VOLUME_CONSERVATION"),
                ({"bad_taker": True}, "HQ_SPOT_VOLUME_CONSERVATION"),
                ({"bad_close_time": True}, "HQ_SPOT_CLOSE_TIME"),
                ({"bad_schema": True}, "HQ_SPOT_SCHEMA"),
            ):
                with self.subTest(asset=asset, variant=kw), self.assertRaisesRegex(ValueError, code):
                    parse_month(fixture(asset, 2022, 12, **kw), asset, 2022, 12)

    def test_sidecar_wrong_filename_is_rejected_before_canonical(self):
        key = (ASSETS[0], MONTHS[0][0], MONTHS[0][1])
        raw = fixture(*key)
        cache = {key: raw}
        checksums = {key: sha(raw) + "  WRONG-ASSET-1h-2022-12.zip"}
        with self.assertRaisesRegex(ValueError, "HQ_PROVIDER_CHECKSUM_FILENAME"):
            source.canonical_from_verified(cache, checksums)

    def test_window_causal_and_missingness(self):
        observed = [True] * 900
        observed[300] = False
        self.assertTrue(window_valid(observed, 299, 168))
        self.assertFalse(window_valid(observed, 300, 168))
        self.assertFalse(window_valid(observed, 467, 168))
        self.assertTrue(window_valid(observed, 468, 168))
        self.assertFalse(window_valid(observed, 20, 168))
        self.assertFalse(window_valid(observed, 900, 168))
        before = [window_valid(observed, i, 168) for i in range(700)]
        observed[750] = False
        self.assertEqual(before, [window_valid(observed, i, 168) for i in range(700)])

    def test_all_100_archive_end_to_end_mask_and_checksums(self):
        cache = {}
        checksums = {}
        for asset in ASSETS:
            for y, m in MONTHS:
                key = (asset, y, m)
                raw = fixture(asset, y, m, skip=(GAP,) if (y, m) == (2023, 3) else ())
                cache[key] = raw
                checksums[key] = sha(raw) + "  " + f"{asset}-1h-{y}-{m:02d}.zip"
        march = {asset: sha(cache[(asset, 2023, 3)]) for asset in ASSETS}
        manifest = "".join(f"{asset}|{y}-{m:02d}|{sha(cache[(asset, y, m)])}\n"
                           for asset in ASSETS for y, m in MONTHS)
        with patch.dict(source.PINNED_MARCH, march), patch.object(
                source, "PINNED_100_SHA_MANIFEST", sha(manifest.encode())):
            a, receipts = source.canonical_from_verified(cache, checksums)
            b, receipts2 = source.canonical_from_verified(cache, checksums)
            self.assertEqual((a, receipts), (b, receipts2))
            self.assertEqual(len(receipts), 100)
            self.assertEqual(sum(r["observed"] for r in receipts), 73148)
            self.assertEqual(sum(r["masked"] for r in receipts), 4)
            self.assertEqual(a.count(b",0,,,,,"), 4)
            with patch.object(source, "PINNED_100_SHA_MANIFEST", "0" * 64):
                with self.assertRaisesRegex(ValueError, "HQ_MANIFEST_PIN_MISMATCH"):
                    source.canonical_from_verified(cache, checksums)
            checksums[("BTCUSDT", 2022, 12)] = "0" * 64 + "  BTCUSDT-1h-2022-12.zip"
            with self.assertRaisesRegex(ValueError, "HQ_PROVIDER_SHA_MISMATCH"):
                source.canonical_from_verified(cache, checksums)

    def test_zip_bytes_deterministic_and_sha(self):
        raw = fixture("BTCUSDT", 2022, 12)
        self.assertEqual(sha(raw), hashlib.sha256(raw).hexdigest())
        a, miss = parse_month(raw, "BTCUSDT", 2022, 12)
        b, miss2 = parse_month(raw, "BTCUSDT", 2022, 12)
        self.assertEqual((a, miss), (b, miss2))
        self.assertEqual(len(a), 744)


if __name__ == "__main__":
    unittest.main()

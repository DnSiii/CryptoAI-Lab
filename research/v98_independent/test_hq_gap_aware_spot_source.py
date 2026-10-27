#!/usr/bin/env python3
"""Offline deterministic synthetic source fixtures; not official archive acceptance."""
import csv
import hashlib
import io
import unittest
import zipfile
from hq_gap_aware_spot_source import ASSETS, GAP, month_hours, parse_month, window_valid, sha


def fixture(asset, year, month, skip=(), duplicate=False, invalid=False):
    name = f"{asset}-1h-{year}-{month:02d}.csv"
    rows = []
    for t in month_hours(year, month):
        if t in skip:
            continue
        row = [str(t), "100", "110", "90", "105", "1", str(t + 3599999), "10000", "5", "1", "5000", "0"]
        if invalid and t == month_hours(year, month)[0]:
            row[2] = "1"
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

    def test_zip_bytes_deterministic_and_sha(self):
        raw = fixture("BTCUSDT", 2022, 12)
        self.assertEqual(sha(raw), hashlib.sha256(raw).hexdigest())
        a, miss = parse_month(raw, "BTCUSDT", 2022, 12)
        b, miss2 = parse_month(raw, "BTCUSDT", 2022, 12)
        self.assertEqual((a, miss), (b, miss2))
        self.assertEqual(len(a), 744)


if __name__ == "__main__":
    unittest.main()

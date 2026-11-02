"""Derived-only CoinAPI native-day bridge: synthetic, never original economics."""
import copy
import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_coinapi_derived_day_bridge import convert, SCHEMA
from research.tools.v99_r106_i1_local_tape_import import scan_day, build_manifest
from research.verification.independent_v99_r106_i1_coinapi_derived_day_oracle import verify as independent_verify

HEADER = "id_site_coinapi,time_exchange,time_coinapi,ask_px,ask_sx,bid_px,bid_sx\n"
DAY = "2022-01-01"


def prepare(root, *, rows=None):
    root = Path(root)
    source = root / "original"
    out = root / "derived"
    source.mkdir()
    out.mkdir()
    specs = []
    for asset, strike in (("BTC", "15000"), ("ETH", "1000")):
        symbol = f"{asset}-30DEC22-{strike}-P"
        key = f"T-QUOTES/D-20220101/E-DERIBIT/IDDI-123+SC-DERIBIT_OPTION_{asset}+S-{symbol}.csv.gz"
        path = source / f"{asset}.csv.gz"
        arrival = "2022-01-01T00:00:00.0000001" if asset == "BTC" else "2022-01-01T00:00:00.0000002"
        row = (f",2022-01-01T00:00:00.0000000,{arrival},0.0050,2,0.0045,3\n"
               if rows is None else rows[asset])
        payload = gzip.compress((HEADER + row).encode("utf-8"))
        path.write_bytes(payload)
        specs.append({
            "path": str(path), "source_key": key, "symbol": symbol,
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
    spec = root / "spec.json"
    spec.write_text(json.dumps({"schema": SCHEMA, "day": DAY, "sources": specs}))
    return spec, out, specs


class DerivedBridgeTests(unittest.TestCase):
    def test_two_asset_original_hash_and_conservative_100ns_arrival(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, originals = prepare(tmp)
            report = convert(spec, out, fixture=True)
            self.assertEqual(report["derived_rows"], 2)
            self.assertEqual(independent_verify(spec, out)["rows"], 2)
            self.assertEqual(report["status"], "DERIVED_ONLY_NOT_ORIGINAL_SOURCE")
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["original_economic_train_executed"])
            self.assertEqual([x["original_gzip_sha256"] for x in report["original_sources"]],
                             [x["sha256"] for x in originals])
            target = out / (DAY + ".csv.gz")
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),
                             report["derived_gzip_sha256"])
            with gzip.open(target, "rt", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([x["symbol"].split("-")[0] for x in rows], ["BTC", "ETH"])
            self.assertEqual([int(x["local_timestamp"]) for x in rows],
                             [1640995200000001, 1640995200000001])
            self.assertEqual([int(x["timestamp"]) for x in rows],
                             [1640995200000000, 1640995200000000])
            checked = scan_day(target, __import__("datetime").date(2022, 1, 1))
            self.assertEqual(checked["live_original_put_quote_rows_by_asset"],
                             {"BTC": 1, "ETH": 1})
            # Shape-compatible is NOT source-original. Guard against manifest laundering.
            with self.assertRaisesRegex(ValueError, "DERIVED_COINAPI_TAPE_CANNOT_BE_ORIGINAL"):
                build_manifest(out, fixture=True)

    def test_independent_oracle_rejects_forged_derived_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, _ = prepare(tmp)
            convert(spec, out, fixture=True)
            manifest = out/(DAY+".coinapi-derived.json")
            report = json.loads(manifest.read_text())
            report["derived_rows"] = 999
            manifest.write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError, "INDEPENDENT_DERIVED_INCOMPLETE"):
                independent_verify(spec, out)

    def test_header_only_declared_btc_or_eth_source_never_publishes(self):
        valid = (",2022-01-01T00:00:00.0000000,"
                 "2022-01-01T00:00:00.0000001,0.0050,2,0.0045,3\\n")
        for empty_asset in ("BTC", "ETH"):
            with self.subTest(empty_asset=empty_asset):
                with tempfile.TemporaryDirectory() as tmp:
                    rows = {asset: ("" if asset == empty_asset else valid)
                            for asset in ("BTC", "ETH")}
                    spec, out, _ = prepare(tmp, rows=rows)
                    with self.assertRaisesRegex(
                        ValueError, "EMPTY_DECLARED_ORIGINAL_COINAPI_SOURCE"
                    ):
                        convert(spec, out, fixture=True)
                    self.assertEqual(list(out.iterdir()), [])

    def test_independent_oracle_vetoes_legacy_empty_declared_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, originals = prepare(tmp)
            convert(spec, out, fixture=True)
            empty_gzip = gzip.compress(HEADER.encode("utf-8"))
            Path(originals[0]["path"]).write_bytes(empty_gzip)
            digest = hashlib.sha256(empty_gzip).hexdigest()
            specification = json.loads(spec.read_text())
            specification["sources"][0]["sha256"] = digest
            spec.write_text(json.dumps(specification))
            sidecar = out / (DAY + ".coinapi-derived.json")
            report = json.loads(sidecar.read_text())
            report["original_sources"][0]["original_gzip_sha256"] = digest
            sidecar.write_text(json.dumps(report))
            with self.assertRaisesRegex(
                AssertionError, "INDEPENDENT_EMPTY_DECLARED_ORIGINAL_SOURCE"
            ):
                independent_verify(spec, out)

    def test_source_tamper_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, originals = prepare(tmp)
            Path(originals[0]["path"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "ORIGINAL_SHA_MISMATCH"):
                convert(spec, out, fixture=True)
            self.assertFalse(list(out.iterdir()))

    def test_reversed_100ns_event_clock_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = (",2022-01-01T00:00:00.0000002,"
                   "2022-01-01T00:00:00.0000001,0.0050,2,0.0045,3\n")
            spec, out, _ = prepare(tmp, rows={"BTC": row, "ETH": row})
            with self.assertRaisesRegex(ValueError, "NONCAUSAL"):
                convert(spec, out, fixture=True)
            self.assertFalse(list(out.iterdir()))

    def test_submicrosecond_at_end_of_day_cannot_roll_into_sealed_next_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = (",2022-01-01T23:59:59.9999999,"
                   "2022-01-01T23:59:59.9999999,0.0050,2,0.0045,3\n")
            spec, out, _ = prepare(tmp, rows={"BTC": row, "ETH": row})
            with self.assertRaisesRegex(ValueError, "CEILED_ARRIVAL_ESCAPES"):
                convert(spec, out, fixture=True)
            self.assertFalse(list(out.iterdir()))

    def test_duplicate_symbol_and_missing_asset_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, originals = prepare(tmp)
            doc = json.loads(spec.read_text())
            doc["sources"][1] = copy.deepcopy(doc["sources"][0])
            spec.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "DUPLICATE_DERIVED_SOURCE"):
                convert(spec, out, fixture=True)
            doc["sources"] = [originals[0], {**originals[0], "symbol": originals[0]["symbol"]}]
            spec.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                convert(spec, out, fixture=True)

    def test_reused_original_file_path_cannot_impersonate_second_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, originals = prepare(tmp)
            doc = json.loads(spec.read_text())
            doc["sources"][1]["path"] = originals[0]["path"]
            doc["sources"][1]["sha256"] = originals[0]["sha256"]
            spec.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "DUPLICATE_DERIVED_SOURCE"):
                convert(spec, out, fixture=True)
            self.assertFalse(list(out.iterdir()))

    def test_zero_and_crossed_books_preserved_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = (",2022-01-01T00:00:00.0000000,"
                   "2022-01-01T00:00:00.0000001,0.0050,0,0.0060,3\n")
            spec, out, _ = prepare(tmp, rows={"BTC": row, "ETH": row})
            report = convert(spec, out, fixture=True)
            self.assertEqual(report["non_executable_or_crossed_rows"], 2)
            self.assertFalse(report["native_lot_fee_margin_delivery_certified"])

    def test_independent_replay_veto_prevents_any_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, _ = prepare(tmp)
            with patch(
                "research.verification.independent_v99_r106_i1_coinapi_derived_day_oracle.verify",
                side_effect=AssertionError("INDEPENDENT_ORIGINAL_REPLAY_REJECTED"),
            ):
                with self.assertRaisesRegex(AssertionError, "INDEPENDENT_ORIGINAL_REPLAY_REJECTED"):
                    convert(spec, out, fixture=True)
            self.assertEqual(list(out.iterdir()), [])
            # A failed independent check must not poison a valid later import.
            report = convert(spec, out, fixture=True)
            self.assertEqual(report["derived_rows"], 2)
            self.assertEqual(independent_verify(spec, out)["rows"], 2)

    def test_independent_replay_forged_success_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, _ = prepare(tmp)
            with patch(
                "research.verification.independent_v99_r106_i1_coinapi_derived_day_oracle.verify",
                return_value={"status": "INDEPENDENT_DERIVED_BYTE_REPLAY_MATCH_NOT_ORIGINAL_ECONOMICS",
                              "rows": 999, "original_files": 2,
                              "promotion_authorized": False,
                              "economic_train_executed": False},
            ):
                with self.assertRaisesRegex(ValueError, "INDEPENDENT_DERIVED_SOURCE_REPLAY_MISMATCH"):
                    convert(spec, out, fixture=True)
            self.assertEqual(list(out.iterdir()), [])

    def test_no_overwrite_and_nonfixture_requires_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out, _ = prepare(tmp)
            with self.assertRaisesRegex(ValueError, "WRITTEN_LICENSE_REQUIRED"):
                convert(spec, out)
            first = convert(spec, out, fixture=True)
            with self.assertRaisesRegex(ValueError, "REFUSE_OVERWRITE"):
                convert(spec, out, fixture=True)
            self.assertEqual(first["derived_gzip_sha256"],
                             hashlib.sha256((out/(DAY+".csv.gz")).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

"""Synthetic full TRAIN source-byte chain tests. NOT exchange data or economics."""
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_derived_day_bridge import convert, SCHEMA as DAY_SCHEMA
from research.tools.v99_r106_i1_coinapi_661d_original_byte_chain import verify, SCHEMA
from research.tools.v99_r106_i1_local_tape_import import FIRST, DAYS

HEADER = "id_site_coinapi,time_exchange,time_coinapi,ask_px,ask_sx,bid_px,bid_sx\n"


class Coinapi661DayChainTests(unittest.TestCase):
    def test_missing_source_and_rights_are_real_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("specs", "original", "derived"):
                (root/name).mkdir()
            with self.assertRaisesRegex(ValueError, "WRITTEN_COINAPI_CHAIN_LICENSE_REQUIRED"):
                verify(root/"specs", root/"original", root/"derived")
            with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_EXTRA_COINAPI_661D_SPEC_GRID"):
                verify(root/"specs", root/"original", root/"derived", fixture=True)

    def test_complete_original_byte_chain_and_adversarial_veto(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs, original, derived = (root/name for name in ("specs", "original", "derived"))
            for folder in (specs, original, derived):
                folder.mkdir()
            for i in range(DAYS):
                day = (FIRST + timedelta(days=i)).isoformat()
                ymd = day.replace("-", "")
                entries = []
                for asset, strike in (("BTC", "15000"), ("ETH", "1000")):
                    symbol = f"{asset}-30DEC23-{strike}-P"
                    key = (f"T-QUOTES/D-{ymd}/E-DERIBIT/"
                           f"IDDI-123+SC-DERIBIT_OPTION_{asset}+S-{symbol}.csv.gz")
                    path = original/f"{day}-{asset}.csv.gz"
                    lines = []
                    for hour in range(24):
                        clock = f"{day}T{hour:02d}:00:00"
                        lines.append(f",{clock}.0000000,{clock}.0000001,0.0050,2,0.0045,3\n")
                    payload = gzip.compress((HEADER + "".join(lines)).encode())
                    path.write_bytes(payload)
                    entries.append({"path": str(path), "source_key": key,
                                    "symbol": symbol,
                                    "sha256": hashlib.sha256(payload).hexdigest()})
                spec = specs/f"{day}.json"
                spec.write_text(json.dumps({"schema": DAY_SCHEMA, "day": day,
                                            "sources": entries}))
                convert(spec, derived, fixture=True)
            result = verify(specs, original, derived, fixture=True)
            self.assertEqual(result["schema"], SCHEMA)
            self.assertEqual(result["days_independently_replayed"], 661)
            self.assertEqual(result["original_vendor_files_byte_replayed"], 1322)
            self.assertEqual(result["derived_rows_checked"], 661 * 48)
            self.assertFalse(result["original_options_economic_train_certified"])
            self.assertFalse(result["promotion_authorized"])
            self.assertFalse(result["derived_daily_bytes_are_original_venue_archive"])
            self.assertFalse(result["signed_native_wallet_replayed"])
            first = FIRST.isoformat()
            path = original/f"{first}-BTC.csv.gz"
            original_bytes = path.read_bytes()
            # Regression: mutate original bytes AFTER the independent oracle
            # finishes its first-day replay. The pre-oracle hash alone passes.
            from unittest.mock import patch
            from research.tools.v99_r106_i1_coinapi_661d_original_byte_chain import (
                independent_original_byte_replay as actual_oracle,
            )
            calls = [0]
            def mutate_after_oracle(spec_path, derived_root):
                checked = actual_oracle(spec_path, derived_root)
                calls[0] += 1
                if calls[0] == 1:
                    path.write_bytes(b"replaced-after-independent-replay")
                return checked
            try:
                with patch(
                    "research.tools.v99_r106_i1_coinapi_661d_original_byte_chain."
                    "independent_original_byte_replay",
                    side_effect=mutate_after_oracle,
                ):
                    with self.assertRaisesRegex(
                        ValueError, "COINAPI_ORIGINAL_BYTES_CHANGED_DURING_REPLAY",
                    ):
                        verify(specs, original, derived, fixture=True)
                self.assertEqual(calls[0], 1)
            finally:
                path.write_bytes(original_bytes)
            # A same-row-count replacement after independent derived replay
            # must not reach the downstream daily scanner.
            daily = derived/f"{first}.csv.gz"
            derived_bytes = daily.read_bytes()
            first_sidecar = derived/f"{first}.coinapi-derived.json"
            sidecar_bytes = first_sidecar.read_bytes()
            try:
                valid_rows = gzip.decompress(derived_bytes).decode("utf-8")
                self.assertIn("0.0050", valid_rows)
                changed = gzip.compress(valid_rows.replace("0.0050", "0.0060").encode())
                self.assertEqual(
                    len(valid_rows.splitlines()),
                    len(gzip.decompress(changed).decode().splitlines()),
                )
                calls = [0]
                def mutate_derived_after_oracle(spec_path, derived_root):
                    checked = actual_oracle(spec_path, derived_root)
                    calls[0] += 1
                    if calls[0] == 1:
                        daily.write_bytes(changed)
                    return checked
                with patch(
                    "research.tools.v99_r106_i1_coinapi_661d_original_byte_chain."
                    "independent_original_byte_replay",
                    side_effect=mutate_derived_after_oracle,
                ):
                    with self.assertRaisesRegex(
                        ValueError, "COINAPI_DERIVED_BYTES_CHANGED_DURING_REPLAY",
                    ):
                        verify(specs, original, derived, fixture=True)
                self.assertEqual(calls[0], 1)
                daily.write_bytes(derived_bytes)
                sidecar_doc = json.loads(sidecar_bytes)
                sidecar_doc["derived_gzip_sha256"] = "0" * 64
                first_sidecar.write_text(json.dumps(sidecar_doc))
                with self.assertRaisesRegex(
                    ValueError, "COINAPI_DERIVED_BYTES_NOT_BOUND_TO_SIDECAR",
                ):
                    verify(specs, original, derived, fixture=True)
            finally:
                daily.write_bytes(derived_bytes)
                first_sidecar.write_bytes(sidecar_bytes)
            path.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "COINAPI_ORIGINAL_BYTES_CHANGED"):
                verify(specs, original, derived, fixture=True)
            path.write_bytes(original_bytes)
            first_spec = specs/f"{first}.json"
            doc = json.loads(first_spec.read_text())
            doc["sources"][0]["path"] = str(root/"not_original"/"fake.csv.gz")
            first_spec.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "MISSING_OR_UNSAFE_COINAPI_CHAIN_INPUT"):
                verify(specs, original, derived, fixture=True)
            self.assertFalse((derived/"manifest.json").exists())


if __name__ == "__main__":
    unittest.main()

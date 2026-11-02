"""CoinAPI ORIGINAL 7-column bytes -> DERIVED 8-column TRAIN chain, never economic certification.

Separate from the Tardis/Deribit original 661d manifest and signed runner.
Preregistered: research/V99_R106_I1_COINAPI_661D_ORIGINAL_BYTE_CHAIN_PREREG_20261102.md
"""
from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_derived_day_bridge import SCHEMA as DAY_SCHEMA
from research.tools.v99_r106_i1_coinapi_quote_intake import original_partition
from research.tools.v99_r106_i1_local_tape_import import (
    FIRST, DAYS, END, scan_day, require_hourly_original_coverage,
)
from research.verification.independent_v99_r106_i1_coinapi_derived_day_oracle import (
    verify as independent_original_byte_replay,
)

SCHEMA = "V99_I1_COINAPI_ORIGINAL_BYTES_DERIVED_661D_CHAIN_V1"


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _regular(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("MISSING_OR_UNSAFE_COINAPI_CHAIN_INPUT")
    return path


def verify(spec_root, original_root, derived_root, *, fixture=False,
           license_document=None):
    """Replay original bytes independently across exactly 661 TRAIN dates.

    Does not emit the ORIGINAL Deribit daily manifest or call the signed wallet.
    A derived day is never exchange-original evidence.
    """
    if type(fixture) is not bool:
        raise ValueError("INVALID_COINAPI_CHAIN_FIXTURE_FLAG")
    spec_root, original_root, derived_root = (
        Path(spec_root), Path(original_root), Path(derived_root))
    if any(not p.is_dir() or p.is_symlink()
           for p in (spec_root, original_root, derived_root)):
        raise ValueError("MISSING_OR_UNSAFE_COINAPI_CHAIN_DIRECTORY")
    if fixture:
        if license_document is not None:
            raise ValueError("FIXTURE_MUST_NOT_CLAIM_LICENSE")
        license_sha = None
    else:
        if license_document is None:
            raise ValueError("WRITTEN_COINAPI_CHAIN_LICENSE_REQUIRED")
        license_path = _regular(license_document)
        if not 0 < license_path.stat().st_size <= 4_000_000:
            raise ValueError("INVALID_COINAPI_CHAIN_LICENSE_DOCUMENT")
        license_sha = _sha(license_path)

    expected = [(FIRST + timedelta(days=i)).isoformat() for i in range(DAYS)]
    actual = {p.name for p in spec_root.glob("*.json")}
    if actual != {day + ".json" for day in expected}:
        raise ValueError("INCOMPLETE_OR_EXTRA_COINAPI_661D_SPEC_GRID")
    actual_days = {p.name for p in derived_root.glob("*.csv.gz")}
    actual_sidecars = {p.name for p in derived_root.glob("*.coinapi-derived.json")}
    if (actual_days != {day + ".csv.gz" for day in expected}
            or actual_sidecars != {day + ".coinapi-derived.json" for day in expected}):
        raise ValueError("INCOMPLETE_OR_EXTRA_COINAPI_DERIVED_661D_GRID")

    seen_keys, seen_paths = set(), set()
    original_files, derived_rows = 0, 0
    # Full original-byte independent replay is mandatory; the derived daily
    # gzip never becomes an "original" input, regardless of its shape.
    for day in expected:
        spec_path = _regular(spec_root / (day + ".json"))
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if (not isinstance(spec, dict) or set(spec) != {"schema", "day", "sources"}
                or spec["schema"] != DAY_SCHEMA or spec["day"] != day
                or not isinstance(spec["sources"], list)
                or not 2 <= len(spec["sources"]) <= 4096):
            raise ValueError("INVALID_COINAPI_ORIGINAL_DAY_SPEC")
        sidecar_path = _regular(derived_root / (day + ".coinapi-derived.json"))
        daily_path = _regular(derived_root / (day + ".csv.gz"))
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        if (sidecar.get("fixture") is not fixture
                or sidecar.get("license_document_sha256_operator_supplied_not_verified")
                != license_sha
                or sidecar.get("derived_file_must_never_be_attested_as_original") is not True
                or sidecar.get("native_lot_fee_margin_delivery_certified") is not False):
            raise ValueError("FORGED_COINAPI_CHAIN_RIGHTS_OR_PROVENANCE")
        day_originals = []
        for source in spec["sources"]:
            if not isinstance(source, dict) or set(source) != {
                "path", "source_key", "symbol", "sha256"
            }:
                raise ValueError("INVALID_COINAPI_CHAIN_SOURCE_DESCRIPTOR")
            path = _regular(source["path"])
            if not path.resolve().is_relative_to(original_root.resolve()):
                raise ValueError("COINAPI_ORIGINAL_PATH_ESCAPES_ROOT")
            key, symbol = source["source_key"], source["symbol"]
            if key in seen_keys or path.resolve() in seen_paths:
                raise ValueError("REUSED_COINAPI_ORIGINAL_SOURCE")
            seen_keys.add(key)
            seen_paths.add(path.resolve())
            start, _ = original_partition(key, symbol)
            from datetime import datetime, timezone
            expected_start = int(datetime.fromisoformat(
                day + "T00:00:00+00:00").timestamp()) * 1000000
            if start != expected_start:
                raise ValueError("COINAPI_ORIGINAL_KEY_DAY_MISMATCH")
            if _sha(path) != source["sha256"]:
                raise ValueError("COINAPI_ORIGINAL_BYTES_CHANGED")
            day_originals.append((path, source["sha256"]))
            original_files += 1
        result = independent_original_byte_replay(spec_path, derived_root)
        # An original can be replaced after its initial digest and after the
        # independent oracle reads it. Recheck ALL source bytes before the
        # day's derived data can be accepted by the nonfixture chain.
        for path, expected_sha in day_originals:
            if _sha(path) != expected_sha:
                raise ValueError("COINAPI_ORIGINAL_BYTES_CHANGED_DURING_REPLAY")
        if (result.get("status") !=
                "INDEPENDENT_DERIVED_BYTE_REPLAY_MATCH_NOT_ORIGINAL_ECONOMICS"
                or result.get("promotion_authorized") is not False
                or result.get("economic_train_executed") is not False
                or result.get("original_files") != len(spec["sources"])
                or type(result.get("rows")) is not int or result["rows"] <= 0):
            raise ValueError("INDEPENDENT_COINAPI_ORIGINAL_CHAIN_REPLAY_FAILED")
        scan = scan_day(daily_path, __import__("datetime").date.fromisoformat(day))
        require_hourly_original_coverage(scan)
        if scan["rows"] != result["rows"]:
            raise ValueError("COINAPI_DERIVED_DAY_ROW_COUNT_MISMATCH")
        derived_rows += result["rows"]
    return {
        "schema": SCHEMA,
        "status": "COINAPI_ORIGINAL_BYTES_TO_DERIVED_661D_PARITY_ONLY",
        "train_start": FIRST.isoformat(),
        "train_end_exclusive": END.isoformat(),
        "days_independently_replayed": DAYS,
        "original_vendor_files_byte_replayed": original_files,
        "derived_rows_checked": derived_rows,
        "fixture": fixture,
        "operator_license_sha256_not_legally_verified": license_sha,
        "original_venue_capture_completeness_certified": False,
        "native_lot_fee_margin_delivery_certified": False,
        "original_exchange_fills_certified": False,
        "original_options_economic_train_certified": False,
        "signed_native_wallet_replayed": False,
        "freeze_authorized": False, "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "paper_publication_authorized": False, "orders_enabled": False,
        "derived_daily_bytes_are_original_venue_archive": False,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("spec_root")
    p.add_argument("original_root")
    p.add_argument("derived_root")
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--license-document")
    a = p.parse_args()
    print(json.dumps(verify(a.spec_root, a.original_root, a.derived_root,
                            fixture=a.fixture,
                            license_document=a.license_document),
                     sort_keys=True))

"""Opt-in local Tardis OPTIONS tape transfer. SOURCE ONLY, never economics/orders.

Requires authorized 2021-2023 Deribit OPTIONS entitlement, local license file,
and explicit --execute. Does not upload, publish manifests, or certify fills.
Prereg: V99_R106_I1_LICENSED_TARDIS_TRANSFER_PREREG_20261028.md.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import FIRST, DAYS, scan_day
from research_tools.v99_r106_tardis_authenticated_scope import (
    SCOPE_URL, _scope_covers_train,
)

MAX_DAY_BYTES = 8 * 1024**3
REQUIRED = {"exchange", "symbol", "timestamp", "local_timestamp",
            "bid_price", "ask_price", "bid_amount", "ask_amount"}


def _scope(opener, key):
    req = urllib.request.Request(
        SCOPE_URL, headers={"Authorization": "Bearer " + key,
                            "User-Agent": "V99-I1-local-licensed-source-transfer/1.0"})
    try:
        with opener(req, timeout=30) as response:
            if int(response.status) != 200:
                raise ValueError("VENDOR_OPTIONS_ENTITLEMENT_UNVERIFIED")
            raw = response.read(16_385)
            if len(raw) > 16_384 or not _scope_covers_train(raw):
                raise ValueError("VENDOR_OPTIONS_ENTITLEMENT_UNVERIFIED")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError,
            TimeoutError) as exc:
        raise ValueError("VENDOR_OPTIONS_ENTITLEMENT_UNAVAILABLE") from None


def _validate_gzip(path, day):
    """Verify gzip CRC and CSV schema; importer checks both assets and clocks."""
    try:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError("LICENSED_OPTIONS_CSV_SCHEMA_MISSING")
            if next(reader, None) is None:
                raise ValueError("LICENSED_OPTIONS_CSV_EMPTY")
            # Exhaust stream to force gzip CRC verification, including trailer.
            for _ in reader:
                pass
        scan_day(path, day)
    except (OSError, EOFError, UnicodeError, csv.Error, gzip.BadGzipFile) as exc:
        raise ValueError("LICENSED_OPTIONS_GZIP_OR_CSV_CORRUPT") from None


def transfer(root, *, execute=False, max_days=1, key=None,
             license_evidence=None, opener=None, max_day_bytes=MAX_DAY_BYTES):
    if type(execute) is not bool or type(max_days) is not int or not 1 <= max_days <= DAYS:
        raise ValueError("INVALID_BOUNDED_TRAIN_TRANSFER_REQUEST")
    if type(max_day_bytes) is not int or not 1 <= max_day_bytes <= MAX_DAY_BYTES:
        raise ValueError("INVALID_SOURCE_BYTE_LIMIT")
    root = Path(root)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("UNSAFE_LOCAL_LICENSED_TAPE_DIRECTORY")
    dates = [FIRST + timedelta(days=i) for i in range(max_days)]
    if not execute:
        return {"status": "DRY_RUN_NO_NETWORK_NO_ARCHIVE", "planned_train_days": len(dates),
                "first_day": dates[0].isoformat(), "last_day": dates[-1].isoformat(),
                "downloaded_days": 0, "economic_train_executed": False,
                "promotion_authorized": False, "orders_enabled": False}
    key = key if key is not None else os.environ.get("TARDIS_API_KEY", "")
    if not isinstance(key, str) or not key.strip():
        raise ValueError("LICENSED_OPTIONS_API_KEY_NOT_CONFIGURED")
    license_evidence = Path(license_evidence) if license_evidence is not None else None
    if (license_evidence is None or not license_evidence.is_file()
            or license_evidence.is_symlink() or license_evidence.stat().st_size == 0):
        raise ValueError("LOCAL_WRITTEN_LICENSE_EVIDENCE_REQUIRED")
    opener = opener or urllib.request.urlopen
    _scope(opener, key.strip())
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("UNSAFE_LOCAL_LICENSED_TAPE_DIRECTORY")
    downloaded = existing = 0
    for day in dates:
        filename = day.isoformat() + ".csv.gz"
        destination = root / filename
        if destination.is_symlink():
            raise ValueError("UNSAFE_EXISTING_LICENSED_DAY")
        if destination.exists():
            if not destination.is_file():
                raise ValueError("CONFLICTING_EXISTING_LICENSED_DAY")
            _validate_gzip(destination, day)
            existing += 1
            continue
        url = (f"https://datasets.tardis.dev/v1/deribit/quotes/"
               f"{day.year:04d}/{day.month:02d}/{day.day:02d}/OPTIONS.csv.gz")
        request = urllib.request.Request(
            url, headers={"Authorization": "Bearer " + key.strip(),
                          "User-Agent": "V99-I1-local-licensed-source-transfer/1.0"})
        fd, temporary = tempfile.mkstemp(prefix=".licensed-", suffix=".part", dir=root)
        try:
            with os.fdopen(fd, "wb") as stream:
                try:
                    with opener(request, timeout=120) as response:
                        if int(response.status) != 200:
                            raise ValueError("LICENSED_OPTIONS_DOWNLOAD_DENIED")
                        content_type = response.headers.get("Content-Type", "").lower()
                        if "html" in content_type or "json" in content_type:
                            raise ValueError("LICENSED_OPTIONS_RESPONSE_NOT_GZIP")
                        declared = response.headers.get("Content-Length")
                        if declared is not None and (not declared.isdigit()
                                                      or int(declared) > max_day_bytes):
                            raise ValueError("LICENSED_OPTIONS_SOURCE_TOO_LARGE")
                        total = 0
                        prefix = b""
                        while True:
                            block = response.read(min(1024 * 1024, max_day_bytes-total+1))
                            if not block:
                                break
                            total += len(block)
                            if total > max_day_bytes:
                                raise ValueError("LICENSED_OPTIONS_SOURCE_TOO_LARGE")
                            if len(prefix) < 2:
                                prefix = (prefix + block)[:2]
                            stream.write(block)
                        if prefix != b"\x1f\x8b" or total < 10:
                            raise ValueError("LICENSED_OPTIONS_RESPONSE_NOT_GZIP")
                except (urllib.error.HTTPError, urllib.error.URLError,
                        TimeoutError, OSError):
                    raise ValueError("LICENSED_OPTIONS_TRANSFER_FAILED") from None
                stream.flush()
                os.fsync(stream.fileno())
            _validate_gzip(Path(temporary), day)
            # No overwrite, including an unexpected concurrent writer.
            if destination.exists() or destination.is_symlink():
                raise ValueError("CONCURRENT_OR_CONFLICTING_LICENSED_DAY")
            os.link(temporary, destination)
            downloaded += 1
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {"status": "LOCAL_SOURCE_BYTES_ONLY_NOT_VENDOR_COMPLETENESS_CERTIFIED",
            "planned_train_days": len(dates), "downloaded_days": downloaded,
            "preexisting_valid_days": existing, "full_661_days_transferred": max_days == DAYS,
            "vendor_gap_attestation_verified": False,
            "historical_native_terms_authenticated": False,
            "economic_train_executed": False, "promotion_authorized": False,
            "orders_enabled": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("secure_root")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-days", type=int, default=1)
    parser.add_argument("--license-evidence")
    args = parser.parse_args()
    print(json.dumps(transfer(args.secure_root, execute=args.execute,
                              max_days=args.max_days,
                              license_evidence=args.license_evidence), sort_keys=True))


if __name__ == "__main__":
    main()

"""Opt-in local Tardis OPTIONS tape transfer. SOURCE ONLY, never economics/orders.

Requires authorized 2021-2023 Deribit OPTIONS entitlement, local license file,
and explicit --execute. Does not upload, publish manifests, or certify fills.
Prereg: V99_R106_I1_LICENSED_TARDIS_TRANSFER_PREREG_20261028.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import (
    FIRST, END, DAYS, scan_day, require_hourly_original_coverage,
)
from research_tools.v99_r106_tardis_authenticated_scope import (
    SCOPE_URL, _scope_covers_window,
)

MAX_DAY_BYTES = 8 * 1024**3
def _scope(opener, key, start_date, end_date):
    req = urllib.request.Request(
        SCOPE_URL, headers={"Authorization": "Bearer " + key,
                            "User-Agent": "V99-I1-local-licensed-source-transfer/1.0"})
    try:
        with opener(req, timeout=30) as response:
            if int(response.status) != 200:
                raise ValueError("VENDOR_OPTIONS_ENTITLEMENT_UNVERIFIED")
            raw = response.read(16_385)
            if len(raw) > 16_384 or not _scope_covers_window(
                    raw, datetime.combine(start_date, datetime.min.time(), timezone.utc),
                    datetime.combine(end_date, datetime.min.time(), timezone.utc)):
                raise ValueError("VENDOR_OPTIONS_ENTITLEMENT_UNVERIFIED")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError,
            TimeoutError) as exc:
        raise ValueError("VENDOR_OPTIONS_ENTITLEMENT_UNAVAILABLE") from None


def _validate_gzip(path, day, expected_sha256=None):
    """One streaming CRC/CSV/causal-day pass; no duplicate multi-GB decompression.

    The existing independent 661-day importer later replays source bytes.
    """
    scanned = scan_day(path, day)
    if expected_sha256 is not None and scanned["sha256"] != expected_sha256:
        raise ValueError("EXTERNAL_SOURCE_SHA256_MISMATCH")
    # The downstream nonfixture 661-day importer already requires 24/24
    # original arrival hours for BOTH BTC and ETH. Reject a partial paid day
    # before publishing or counting it as a successfully transferred source.
    require_hourly_original_coverage(scanned)


def transfer(root, *, execute=False, max_days=1, start_date=None, key=None,
             license_evidence=None, opener=None, max_day_bytes=MAX_DAY_BYTES,
             expected_sha256=None):
    if type(execute) is not bool or type(max_days) is not int or not 1 <= max_days <= DAYS:
        raise ValueError("INVALID_BOUNDED_TRAIN_TRANSFER_REQUEST")
    if type(max_day_bytes) is not int or not 1 <= max_day_bytes <= MAX_DAY_BYTES:
        raise ValueError("INVALID_SOURCE_BYTE_LIMIT")
    # Validate the entire requested window before network, auth or writes.
    # Allows a non-sample paid entitlement proof and bounded missing-day retry.
    if start_date is None:
        start_date = FIRST
    elif isinstance(start_date, str):
        if (len(start_date) != 10 or start_date[4] != "-"
                or start_date[7] != "-"):
            raise ValueError("INVALID_OR_SEALED_TRAIN_SOURCE_WINDOW")
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError as exc:
            raise ValueError("INVALID_OR_SEALED_TRAIN_SOURCE_WINDOW") from exc
    if (type(start_date) is not date or start_date < FIRST
            or start_date + timedelta(days=max_days) > END):
        raise ValueError("INVALID_OR_SEALED_TRAIN_SOURCE_WINDOW")
    root = Path(root)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("UNSAFE_LOCAL_LICENSED_TAPE_DIRECTORY")
    dates = [start_date + timedelta(days=i) for i in range(max_days)]
    if expected_sha256 is not None and (
            dates != [date(2022, 1, 23)]
            or not isinstance(expected_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise ValueError("INVALID_TARGET_DAY_EXTERNAL_SHA256_REQUEST")
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
    _scope(opener, key.strip(), dates[0], dates[-1] + timedelta(days=1))
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("UNSAFE_LOCAL_LICENSED_TAPE_DIRECTORY")
    downloaded = existing = 0
    target_day_checked = None
    for day in dates:
        filename = day.isoformat() + ".csv.gz"
        destination = root / filename
        if destination.is_symlink():
            raise ValueError("UNSAFE_EXISTING_LICENSED_DAY")
        if destination.exists():
            if not destination.is_file():
                raise ValueError("CONFLICTING_EXISTING_LICENSED_DAY")
            _validate_gzip(destination, day, expected_sha256)
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
            _validate_gzip(Path(temporary), day, expected_sha256)
            # The fixed paid target must pass its independent source oracle
            # BEFORE the canonical original is published. The oracle requires
            # an exact basename; a private same-filesystem staging hard link
            # preserves it without copying gigabytes or exposing partial data.
            if len(dates) == 1 and day == date(2022, 1, 23):
                from research.tools.v99_r106_i1_single_day_source_feasibility import inspect
                with tempfile.TemporaryDirectory(prefix=".target-day-gate-", dir=root) as stage:
                    staged = Path(stage) / filename
                    os.link(temporary, staged)
                    target_day_checked = inspect(
                        staged, license_evidence=license_evidence,
                        expected_sha256=expected_sha256)
                    if (target_day_checked["status"] not in
                            ("SOURCE_FEASIBLE_ONLY_NOT_ECONOMICS", "SOURCE_VETO_NOT_LOSS")
                            or not target_day_checked["independent_original_byte_replay_passed"]):
                        raise ValueError("TARGET_DAY_INDEPENDENT_SOURCE_GATE_FAILED")
            # No overwrite, including an unexpected concurrent writer.
            if destination.exists() or destination.is_symlink():
                raise ValueError("CONCURRENT_OR_CONFLICTING_LICENSED_DAY")
            os.link(temporary, destination)
            downloaded += 1
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    # The already-preregistered single paid Sunday must be independently
    # evaluated BEFORE a full-history purchase is even considered. A valid
    # archive transfer alone is not a viable two-strike options market.
    target_day_gate = None
    if len(dates) == 1 and dates[0] == date(2022, 1, 23):
        from research.tools.v99_r106_i1_single_day_source_feasibility import inspect
        checked = target_day_checked
        if checked is None:  # Existing user-provided day: validate, never delete it.
            checked = inspect(root / "2022-01-23.csv.gz",
                              license_evidence=license_evidence,
                              expected_sha256=expected_sha256)
        if checked["status"] not in ("SOURCE_FEASIBLE_ONLY_NOT_ECONOMICS",
                                      "SOURCE_VETO_NOT_LOSS") or not checked[
                                          "independent_original_byte_replay_passed"]:
            raise ValueError("TARGET_DAY_INDEPENDENT_SOURCE_GATE_FAILED")
        target_day_gate = {
            "status": checked["status"],
            "source_day": checked["source_day"],
            "external_sha256_matched": checked["external_sha256_matched"],
            "original_gzip_sha256": checked["original_gzip_sha256"],
            "source_hour_coverage": checked["source_hour_coverage"],
            "fresh_synchronized_two_strike_pairs_by_asset":
                checked["fresh_synchronized_two_strike_pairs_by_asset"],
            "independent_original_byte_replay_passed": True,
            "vendor_completeness_attested": False,
            "historical_native_fees_margin_delivery_verified": False,
            "certified_lifecycles": 0,
            "promotion_authorized": False,
        }
    return {"status": "LOCAL_SOURCE_BYTES_ONLY_NOT_VENDOR_COMPLETENESS_CERTIFIED",
            "preselected_one_day_source_gate": target_day_gate,
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
    parser.add_argument("--start-date", help="first UTC TRAIN date, YYYY-MM-DD")
    parser.add_argument("--license-evidence")
    parser.add_argument("--expected-sha256",
                        help="independently supplied vendor digest for fixed 2022-01-23")
    args = parser.parse_args()
    print(json.dumps(transfer(args.secure_root, execute=args.execute,
                              max_days=args.max_days, start_date=args.start_date,
                              license_evidence=args.license_evidence,
                              expected_sha256=args.expected_sha256), sort_keys=True))


if __name__ == "__main__":
    main()

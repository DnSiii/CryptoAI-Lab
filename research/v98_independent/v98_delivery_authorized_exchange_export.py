#!/usr/bin/env python3
"""V98-only alternate *authorized exchange-origin* export byte/calendar preflight.

A self-described issuer, custodian, checksum, or attestation file does NOT
authenticate the exchange. Independent origin/custody verification is mandatory
before portfolio PnL. Never accesses a network, 2026+, or external engines.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ("symbol", "fundingTime", "fundingRate", "markPrice")

def _fail(code):
    raise ValueError("V98_AUTHORIZED_EXPORT_" + code)

def _basename(root, name, suffix=None):
    if not isinstance(name, str) or not name or name in (".", "..") or Path(name).name != name:
        _fail("UNSAFE_PATH")
    if suffix is not None and not name.endswith(suffix):
        _fail("FILE_SUFFIX")
    p = Path(root) / name
    if p.is_symlink() or not p.is_file():
        _fail("FILE_ABSENT_OR_SYMLINK")
    return p

def _digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def _decimal(x, field):
    try:
        v = Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError):
        _fail(field + "_INVALID")
    if not v.is_finite():
        _fail(field + "_NONFINITE")
    return v

def validate_export(root, manifest, expected, start, end, assets, slot_ms):
    """Return source-only metadata and canonical marks; no trading approval.

    Expected must already have been authenticated by the SHA-pinned Clean-4
    expected-event reader. The CSV must be a separately obtained exchange-origin
    export, not synthesized from hourly candles or a mark envelope.
    """
    if not isinstance(manifest, dict) or manifest.get("source_type") != "authorized_exchange_origin_export":
        _fail("SOURCE_TYPE")
    if manifest.get("schema") != "symbol,fundingTime,fundingRate,markPrice":
        _fail("SCHEMA_DECLARATION")
    for field in ("exchange_issuer", "independent_custodian", "custody_method", "export_reference"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            _fail("MISSING_" + field.upper())
    stamp = manifest.get("captured_at_utc")
    if not isinstance(stamp, str) or not stamp.endswith("Z"):
        _fail("CAPTURE_TIMESTAMP")
    try:
        parsed = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        _fail("CAPTURE_TIMESTAMP")
    if parsed.utcoffset() != dt.timedelta(0):
        _fail("CAPTURE_TIMESTAMP")
    # A file containing all 2025 events cannot have been captured before
    # 2026-01-01. Nor can it credibly have a future capture timestamp.
    if parsed.timestamp() * 1000 < end or parsed > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        _fail("IMPOSSIBLE_CAPTURE_TIME")
    raw = _basename(root, manifest.get("export_file"), ".csv")
    attestation = _basename(root, manifest.get("custody_attestation_file"))
    if _digest(raw) != manifest.get("export_sha256"):
        _fail("RAW_EXPORT_SHA256")
    if _digest(attestation) != manifest.get("custody_attestation_sha256"):
        _fail("ATTESTATION_SHA256")
    if raw == attestation:
        _fail("ATTESTATION_NOT_SEPARATE")
    seen = {}
    previous = {asset: -1 for asset in assets}
    with raw.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, restkey="__extra__", restval=None)
        if tuple(reader.fieldnames or ()) != FIELDS:
            _fail("CSV_HEADER")
        for row in reader:
            if set(row) != set(FIELDS) or any(v is None for v in row.values()):
                _fail("CSV_ROW_SHAPE")
            asset = row["symbol"]
            if asset not in assets:
                _fail("UNEXPECTED_ASSET")
            s = row["fundingTime"]
            if not s.isascii() or not s.isdecimal():
                _fail("NONINTEGER_TIMESTAMP")
            ts = int(s)
            if not start <= ts < end or ts <= previous[asset]:
                _fail("OUTSIDE_TRAINING_OR_NONMONOTONIC")
            previous[asset] = ts
            slot = start + (ts - start) // slot_ms * slot_ms
            if ts - slot > 60000:
                _fail("OFF_SLOT_GT_60S")
            key = (asset, slot)
            if key in seen or key not in expected:
                _fail("DUPLICATE_OR_UNEXPECTED_EVENT")
            rate = _decimal(row["fundingRate"], "RATE")
            mark = _decimal(row["markPrice"], "MARK")
            if mark <= 0 or abs(rate) > 1:
                _fail("RATE_OR_MARK_GEOMETRY")
            # Expected 12-significant-digit CSV can differ slightly from the
            # original exchange decimal. A one-native-tick discrepancy (1e-8)
            # must NEVER be accepted as a rounding artifact.
            if abs(rate - Decimal(str(expected[key]))) > Decimal("0.0000000001"):
                _fail("NATIVE_FUNDING_RATE_CONFLICT")
            seen[key] = (ts, str(rate), str(mark))
    if set(seen) != set(expected):
        _fail("INCOMPLETE_" + str(len(set(expected) - set(seen))))
    return ({
        "event_count": len(seen), "assets": list(assets), "source_pages": 0,
        "source_transport": "authorized_exchange_origin_csv",
        "raw_export_sha256": _digest(raw),
        "custody_attestation_sha256": _digest(attestation),
        "native_marks_reconciled": True,
        "exchange_origin_independently_authenticated": False,
        "custody_independently_authenticated": False,
        "pnl_computed": False,
    }, seen)

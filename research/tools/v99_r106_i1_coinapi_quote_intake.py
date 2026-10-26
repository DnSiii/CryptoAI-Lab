"""CoinAPI Deribit options flat-file quote intake: SOURCE ONLY, NEVER fills.

Separate provider route when Tardis 2021-23 entitlement is unavailable.
Preserves both original clocks and original bytes hash. No contract-size,
historical coverage, venue-lot, margin, fees, or execution certification.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUMNS = ("id_site_coinapi","time_exchange","time_coinapi",
           "ask_px","ask_sx","bid_px","bid_sx")
SYMBOL = re.compile(r"^(BTC|ETH)-[0-9]{1,2}[A-Z]{3}[0-9]{2}-[0-9]+-P$")
SITE_UUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
SOURCE_KEY = re.compile(
    r"^T-QUOTES/D-(\\d{8})/E-DERIBIT/IDDI-[^/+]+\\+SC-[^/+]+\\+S-([^/]+)\\.csv\\.gz$"
)
TRAIN_START = datetime(2021, 12, 9, tzinfo=timezone.utc)
TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)


def original_partition(source_key: str, symbol: str) -> tuple[int, int]:
    """Bind a claimed original S3 object identity, never certify the claim itself."""
    match = SOURCE_KEY.fullmatch(source_key) if isinstance(source_key, str) else None
    if not match or match.group(2) not in (symbol, symbol.replace("-", "__002D")):
        raise ValueError("SOURCE_KEY_DERIBIT_SYMBOL_IDENTITY_MISMATCH")
    try:
        start = datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("INVALID_SOURCE_KEY_DATE") from exc
    if not TRAIN_START <= start < TRAIN_END:
        raise ValueError("SOURCE_KEY_OUTSIDE_SEALED_TRAIN")
    return int(start.timestamp()) * 1_000_000, int(start.timestamp()) * 1_000_000 + 86_400_000_000



def microseconds(value: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|\+00:00)?", value
    ):
        raise ValueError("UNTRUSTED_COINAPI_CLOCK_FORMAT")
    prefix = value.replace("Z", "+00:00")
    fractional = value.split(".", 1)[1].split("+", 1)[0].rstrip("Z") if "." in value else ""
    if len(fractional) > 6 and any(c != "0" for c in fractional[6:]):
        raise ValueError("SUBMICROSECOND_TIME_CANNOT_BE_REPRESENTED")
    dt = datetime.fromisoformat(prefix)
    # CoinAPI official flat-file sample omits timezone suffix; treat as
    # provider UTC by convention, never as certified original venue clock.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.utcoffset().total_seconds() != 0:
        raise ValueError("NON_UTC_CLOCK")
    return int(dt.timestamp()) * 1_000_000 + dt.microsecond


def positive(value: str) -> Decimal:
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError("INVALID_ORIGINAL_COINAPI_NUMBER")
    if not d.is_finite() or d <= 0:
        raise ValueError("NONPOSITIVE_ORIGINAL_COINAPI_NUMBER")
    return d


def inspect(original_gzip: Path, *, venue: str, symbol: str, licensed: bool, source_key: str) -> dict:
    """Validate an explicitly identified original file; no inferred symbol from file name."""
    path = Path(original_gzip)
    if venue != "DERIBIT" or not SYMBOL.fullmatch(symbol):
        raise ValueError("EXPLICIT_DERIBIT_PUT_SYMBOL_REQUIRED")
    if not isinstance(licensed, bool) or not licensed:
        raise ValueError("WRITTEN_HISTORICAL_LICENSE_NOT_ATTESTED")
    day_start_us, day_end_us = original_partition(source_key, symbol)
    if not path.is_file() or path.is_symlink() or path.suffix != ".gz":
        raise ValueError("ORIGINAL_GZIP_FILE_REQUIRED")
    raw = path.read_bytes()
    if not raw.startswith(b"\x1f\x8b"):
        raise ValueError("NOT_ORIGINAL_GZIP")
    try:
        decompressed = gzip.decompress(raw).decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("INVALID_ORIGINAL_GZIP") from exc
    reader = csv.DictReader(io.StringIO(decompressed), delimiter=";")
    if tuple(reader.fieldnames or ()) != COLUMNS:
        raise ValueError("WRONG_COINAPI_QUOTES_COLUMNS")
    rows, last_arrival = 0, None
    first, last = None, None
    for row in reader:
        if row.get(None) is not None or any(row.get(k) is None for k in COLUMNS):
            raise ValueError("MALFORMED_ORIGINAL_COINAPI_ROW")
        if row["id_site_coinapi"] and not SITE_UUID.fullmatch(row["id_site_coinapi"]):
            raise ValueError("INVALID_COINAPI_RECEIVING_SITE_UUID")
        event = microseconds(row["time_exchange"])
        arrival = microseconds(row["time_coinapi"])
        if not (day_start_us <= arrival < day_end_us):
            raise ValueError("SOURCE_KEY_PARTITION_TIMESTAMP_MISMATCH")
        if event > arrival or (last_arrival is not None and arrival < last_arrival):
            raise ValueError("NONCAUSAL_OR_OUT_OF_ORDER_COINAPI_QUOTE")
        bid, ask = positive(row["bid_px"]), positive(row["ask_px"])
        positive(row["bid_sx"]); positive(row["ask_sx"])
        if bid >= ask:
            raise ValueError("CROSSED_OR_LOCKED_COINAPI_BOOK")
        first = arrival if first is None else first
        last = arrival
        last_arrival = arrival
        rows += 1
    if rows == 0:
        raise ValueError("EMPTY_COINAPI_OPTIONS_QUOTES")
    return {
        "schema":"V99_I1_COINAPI_ORIGINAL_QUOTE_INTAKE_V1",
        "status":"SOURCE_FORMAT_ONLY_NO_ECONOMICS",
        "provider":"CoinAPI", "venue":venue, "instrument":symbol,
        "timezone_for_naive_source_fields_assumed_utc_not_certified":True,
        "original_sha256":hashlib.sha256(raw).hexdigest(),
        "claimed_original_s3_key":source_key,
        "source_key_independently_verified":False,
        "license_document_independently_verified":False,
        "original_bytes":len(raw), "rows":rows,
        "first_arrival_us":first, "last_arrival_us":last,
        "source_quote_size_units_certified_as_native_contracts":False,
        "original_2021_2023_btc_eth_coverage_certified":False,
        "complete_21_45d_lifecycles_certified":False,
        "historical_fee_margin_certified":False,
        "economic_train_executed":False, "validation_opened":False,
        "holdout_opened":False, "orders_enabled":False,
        "promotion_authorized":False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Source-only CoinAPI Deribit options quote intake; no orders")
    parser.add_argument("original_gzip", type=Path)
    parser.add_argument("venue", choices=["DERIBIT"])
    parser.add_argument("symbol")
    parser.add_argument("--source-key", required=True, help="Original provider S3 object key, NOT a local filename")
    parser.add_argument("--license-document", type=Path, required=True, help="Operator-supplied written rights document")
    parser.add_argument("--license-sha256", required=True, help="Expected SHA-256 of written document")
    args = parser.parse_args(argv)
    doc = args.license_document
    if (not doc.is_file() or doc.is_symlink() or
            not 0 < doc.stat().st_size <= 4_000_000 or
            not re.fullmatch(r"[0-9a-fA-F]{64}", args.license_sha256) or
            hashlib.sha256(doc.read_bytes()).hexdigest() != args.license_sha256.lower()):
        raise ValueError("WRITTEN_LICENSE_DOCUMENT_MISSING_OR_HASH_MISMATCH")
    report = inspect(args.original_gzip, venue=args.venue, symbol=args.symbol,
                     licensed=True, source_key=args.source_key)
    report["operator_supplied_license_sha256"] = args.license_sha256.lower()
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    main()

"""CoinAPI Deribit options flat-file quote intake: SOURCE ONLY, NEVER fills.

Separate provider route when Tardis 2021-23 entitlement is unavailable.
Preserves both original clocks and original bytes hash. No contract-size,
historical coverage, venue-lot, margin, fees, or execution certification.
"""
from __future__ import annotations
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


def inspect(original_gzip: Path, *, venue: str, symbol: str, licensed: bool) -> dict:
    """Validate an explicitly identified original file; no inferred symbol from file name."""
    path = Path(original_gzip)
    if venue != "DERIBIT" or not SYMBOL.fullmatch(symbol):
        raise ValueError("EXPLICIT_DERIBIT_PUT_SYMBOL_REQUIRED")
    if not isinstance(licensed, bool) or not licensed:
        raise ValueError("WRITTEN_HISTORICAL_LICENSE_NOT_ATTESTED")
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
        if row["id_site_coinapi"] not in ("",):
            raise ValueError("UNEXPECTED_COINAPI_ID_SITE_VALUE")
        event = microseconds(row["time_exchange"])
        arrival = microseconds(row["time_coinapi"])
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


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_coinapi_quote_intake ORIGINAL.csv.gz DERIBIT BTC-30DEC22-15000-P")
    print(json.dumps(inspect(Path(sys.argv[1]), venue=sys.argv[2],
                             symbol=sys.argv[3], licensed=False), sort_keys=True))

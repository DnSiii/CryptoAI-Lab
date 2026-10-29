"""Independent original-byte I1 2022-01-23 source-only replay.

No imports of primary scanner, book builder, or pair counter. No economics.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1_000_000)
CUTOFF = START + 86_400_000_000
DECISION_MS = CUTOFF // 1000
FIELDS = {"exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount"}


def _option(symbol):
    if not isinstance(symbol, str):
        return None
    pieces = symbol.split("-")
    if len(pieces) != 4 or pieces[0] not in ("BTC", "ETH") or pieces[-1] != "P":
        return None
    try:
        expiry = datetime.strptime(pieces[1].upper(), "%d%b%y").replace(
            hour=8, tzinfo=timezone.utc)
        strike = Decimal(pieces[2])
    except (ValueError, InvalidOperation, OverflowError):
        return None
    if not strike.is_finite() or strike <= 0:
        return None
    return pieces[0], int(expiry.timestamp() * 1000), strike


def _book(row):
    try:
        bid, ask, bs, ass = (Decimal(row[x]) for x in
                            ("bid_price", "ask_price", "bid_amount", "ask_amount"))
    except (InvalidOperation, ValueError, TypeError, KeyError):
        return None
    if not all(x.is_finite() and x > 0 for x in (bid, ask, bs, ass)) or bid >= ask:
        return None
    return bid, ask, bs, ass


def replay(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as raw:
        for block in iter(lambda: raw.read(1024 * 1024), b""):
            digest.update(block)
    last = -1
    rows = 0
    masks = {"BTC": 0, "ETH": 0}
    latest = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise ValueError("ORACLE_SOURCE_COLUMNS_MISSING")
        for row in reader:
            rows += 1
            if row["exchange"] != "deribit":
                raise ValueError("ORACLE_SOURCE_EXCHANGE_INVALID")
            try:
                venue = int(row["timestamp"])
                arrived = int(row["local_timestamp"])
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError("ORACLE_SOURCE_CLOCK_INVALID") from exc
            if not (0 <= venue <= arrived and START <= arrived < CUTOFF
                    and arrived >= last):
                raise ValueError("ORACLE_SOURCE_CLOCK_NONCAUSAL")
            last = arrived
            contract = _option(row["symbol"])
            if contract is None:
                continue
            asset, expiry, strike = contract
            valid = _book(row)
            if (valid is not None and arrived - venue <= 300_000_000
                    and expiry > DECISION_MS):
                masks[asset] |= 1 << ((arrived - START) // 3_600_000_000)
            if 28 * 86_400_000 <= expiry - DECISION_MS <= 35 * 86_400_000:
                # Always retain the LAST update, even invalid or stale.
                latest[row["symbol"]] = (asset, expiry, strike, venue, arrived, valid)
    if rows <= 0:
        raise ValueError("ORACLE_SOURCE_EMPTY")
    coverage = {asset: mask.bit_count() for asset, mask in masks.items()}
    if any(value != 24 for value in coverage.values()):
        raise ValueError("ORACLE_SOURCE_HOURLY_GAP")
    eligible = defaultdict(list)
    for asset, expiry, strike, venue, arrived, valid in latest.values():
        if (valid is None or not 0 <= CUTOFF - arrived <= 300_000_000
                or not 0 <= CUTOFF - venue <= 300_000_000):
            continue
        eligible[(asset, expiry)].append((strike, venue, arrived))
    pairs = {"BTC": 0, "ETH": 0}
    for (asset, _expiry), group in eligible.items():
        for i, left in enumerate(group):
            for right in group[i + 1:]:
                if (left[0] != right[0] and abs(left[1] - right[1]) <= 1_000_000
                        and abs(left[2] - right[2]) <= 1_000_000):
                    pairs[asset] += 1
    return {"sha256": digest.hexdigest(), "rows": rows,
            "coverage_hours_by_asset": coverage, "pairs_by_asset": pairs}

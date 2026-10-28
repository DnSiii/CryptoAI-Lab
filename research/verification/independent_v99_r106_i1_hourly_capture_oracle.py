"""Independent streaming UTC-hour BTC/ETH original OPTIONS capture oracle.

Independent of the production scanner. Presence is necessary, NOT vendor
gap certification, economic execution, fee, index, native lot or PnL proof.
TRAIN dates only; never reads validation or final holdout.
"""
from __future__ import annotations

import csv
import gzip
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FIRST = date(2021, 12, 9)
END = date(2023, 10, 1)
FULL = (1 << 24) - 1
COLUMNS = {"exchange", "symbol", "timestamp", "local_timestamp",
           "bid_price", "ask_price", "bid_amount", "ask_amount"}


def verify(path: Path, day: date) -> dict:
    if type(day) is not date or not FIRST <= day < END:
        raise ValueError("ORACLE_SEALED_OR_INVALID_DAY")
    lower = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp() * 1_000_000)
    masks = {"BTC": 0, "ETH": 0}
    previous = -1
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError("ORACLE_MISSING_COLUMNS")
        for row in reader:
            if row["exchange"] != "deribit":
                raise ValueError("ORACLE_WRONG_VENUE")
            try:
                arrival = int(row["local_timestamp"])
                event = int(row["timestamp"])
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("ORACLE_INVALID_CLOCK") from exc
            if not (lower <= arrival < lower + 86_400_000_000
                    and 0 <= event <= arrival and arrival >= previous):
                raise ValueError("ORACLE_INVALID_ARRIVAL_ORDER")
            previous = arrival
            parts = row["symbol"].split("-")
            if len(parts) != 4 or parts[0] not in masks or parts[3] != "P":
                continue
            try:
                expiry = datetime.strptime(parts[1].upper(), "%d%b%y").date()
                strike = float(parts[2])
                bid, ask, bs, az = (float(row[k]) for k in
                                    ("bid_price", "ask_price", "bid_amount", "ask_amount"))
            except (ValueError, TypeError, OverflowError):
                continue
            if not (timedelta(days=28) <= expiry-day <= timedelta(days=45)
                    and 0 <= arrival-event <= 300_000_000
                    and all(math.isfinite(v) and v > 0
                            for v in (strike, bid, ask, bs, az))
                    and bid < ask):
                continue
            hour = (arrival - lower) // 3_600_000_000
            masks[parts[0]] |= 1 << hour
    hours = {asset: mask.bit_count() for asset, mask in masks.items()}
    if any(mask != FULL for mask in masks.values()):
        raise ValueError("ORACLE_BTC_ETH_HOURLY_ORIGINAL_CAPTURE_GAP:"
                         + str(day) + ":" + str(hours))
    return {"independently_verified_original_arrival_hours": hours,
            "independent_vendor_gap_certified": False,
            "independent_economic_train_certified": False,
            "independent_promotion_authorized": False}

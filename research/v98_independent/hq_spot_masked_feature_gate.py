#!/usr/bin/env python3
"""HQ masked spot feature-input gate: source-only, no signal or economic PnL.

Never infer a full-hour bar from the Binance March-2023 early-close candle.
No interpolation, 2025 holdout, 2026+ market data, or unmasked zero returns.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
FIELDS = ("asset", "open_time_ms", "observed", "full_hour",
          "open", "high", "low", "close", "quote_volume")
START = int(dt.datetime(2022, 12, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
CUT = int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
HOURS = (CUT - START) // 3600000
PARTIAL = int(dt.datetime(2023, 3, 24, 12, tzinfo=dt.timezone.utc).timestamp() * 1000)
MISSING = PARTIAL + 3600000


def valid_window(eligible: list[bool], end: int, lookback: int) -> bool:
    """Causal closed-bar window ending at t, never including t+1 or partial bars."""
    if lookback < 1 or end < lookback - 1 or end >= len(eligible):
        return False
    return all(eligible[end - lookback + 1:end + 1])


def load_verified(path: Path, receipt_path: Path) -> dict:
    path, receipt_path = Path(path), Path(receipt_path)
    for p in (path, receipt_path):
        if "v98_independent" not in p.resolve().parts:
            raise ValueError("HQ_FEATURE_V98_NAMESPACE_ONLY")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("decision") != "PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC" or
            receipt.get("validation_2025_read") is not False or
            receipt.get("data_2026_read") is not False or
            receipt.get("historical_system_pnl_computed") is not False or
            receipt.get("complete_grid_source_rejection_still_active") is not True or
            receipt.get("publisher_early_close_partial_asset_hours") != 4):
        raise ValueError("HQ_FEATURE_SOURCE_NOT_ACCEPTED")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt.get("canonical_sha256"):
        raise ValueError("HQ_FEATURE_CANONICAL_HASH_MISMATCH")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("HQ_FEATURE_SCHEMA")
    result = {}
    missing = partial = eligible_total = observed_total = 0
    iterator = iter(reader)
    for asset in ASSETS:
        close = []
        quote = []
        eligible = []
        for index in range(HOURS):
            row = next(iterator, None)
            if row is None or None in row or row.get("asset") != asset:
                raise ValueError("HQ_FEATURE_ASSET_OR_COVERAGE")
            t = START + index * 3600000
            if int(row["open_time_ms"]) != t or t >= CUT:
                raise ValueError("HQ_FEATURE_TIMESTAMP_OR_HOLDOUT")
            if row["observed"] not in ("0", "1") or row["full_hour"] not in ("0", "1"):
                raise ValueError("HQ_FEATURE_MASK_SCHEMA")
            obs = row["observed"] == "1"
            full = row["full_hour"] == "1"
            if not obs:
                if t != MISSING or full or any(row[k] for k in FIELDS[4:]):
                    raise ValueError("HQ_FEATURE_UNEXPECTED_MISSINGNESS")
                close.append(None)
                quote.append(None)
                eligible.append(False)
                missing += 1
                continue
            if full == (t == PARTIAL):
                raise ValueError("HQ_FEATURE_PARTIAL_MASK_MISMATCH")
            vals = [float(row[k]) for k in FIELDS[4:]]
            o, h, l, c, q = vals
            if (not all(math.isfinite(x) for x in vals) or min(o, h, l, c) <= 0 or
                    q < 0 or l > min(o, c) or h < max(o, c) or h < l):
                raise ValueError("HQ_FEATURE_INVALID_OBSERVED_CANDLE")
            close.append(c)
            quote.append(q)
            eligible.append(full)
            observed_total += 1
            eligible_total += int(full)
            partial += int(not full)
        result[asset] = {"close": close, "quote_volume": quote, "eligible": eligible}
    if next(iterator, None) is not None:
        raise ValueError("HQ_FEATURE_EXTRA_ROWS_OR_HOLDOUT")
    if (len(result) != 4 or missing != 4 or partial != 4 or
            observed_total != 73148 or eligible_total != 73144 or
            receipt.get("eligible_full_hour_asset_hours") != eligible_total):
        raise ValueError("HQ_FEATURE_GLOBAL_COUNTS")
    return {"status": "PASS_HQ_MASKED_FEATURE_INPUT_ONLY_NO_ALPHA",
            "source_sha256": receipt["canonical_sha256"],
            "hours_per_asset": HOURS, "observed_asset_hours": observed_total,
            "eligible_asset_hours": eligible_total, "missing_asset_hours": missing,
            "partial_asset_hours": partial, "assets": result,
            "holdout_2025_read": False, "historical_system_pnl_computed": False}


if __name__ == "__main__":
    p = ROOT / "hq_gap_aware_spot_source_only"
    x = load_verified(p / "hq_spot_calendar_masked.csv", p / "hq_masked_source_receipt.json")
    print("HQ_FEATURE_INPUT_PASS", x["source_sha256"], x["eligible_asset_hours"])

#!/usr/bin/env python3
"""V98 Independent Phase243 native funding source gate (DATA ONLY).

Validates the immutable 2022-12 warmup and 2023-2025 training window of the
five V98 Phase206 native CSVs. No signal, PnL, V99 access or holdout access.
The SOL 2022-11 variable-interval episode is outside this frozen window:
do not misclassify that historical episode as a 2023-2025 data failure.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path

UTC = timezone.utc
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
START = datetime(2022, 12, 1, tzinfo=UTC)
TRAIN_START = datetime(2023, 1, 1, tzinfo=UTC)
CUTOFF = datetime(2026, 1, 1, tzinfo=UTC)
STEP_MS = 8 * 3600 * 1000
ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT")
COLUMNS = ("fundingTime_ms", "fundingTime_utc", "fundingRate", "fundingIntervalHours")
THRESHOLDS = (Decimal("0.0007"), Decimal("0.0014"), Decimal("0.0028"))


def millis(dt: datetime) -> int:
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise ValueError("funding timestamp must be explicitly UTC")
    delta = dt - EPOCH
    if delta.microseconds % 1000:
        raise ValueError("funding timestamp has submillisecond precision")
    return delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000


def audit_bytes(raw: bytes, symbol: str, *, start: datetime = START,
                cut: datetime = CUTOFF, train_start: datetime = TRAIN_START) -> dict:
    if symbol not in ASSETS:
        raise ValueError("unexpected V98 symbol")
    if start < START or cut > CUTOFF or start >= cut or train_start < start or train_start >= cut:
        raise ValueError("invalid training window / holdout firewall")
    start_ms, cut_ms, train_ms = millis(start), millis(cut), millis(train_start)
    if (cut_ms - start_ms) % STEP_MS or start_ms % STEP_MS:
        raise ValueError("training window must align to 8h boundaries")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    except UnicodeDecodeError as exc:
        raise ValueError("non-UTF8 native funding CSV") from exc
    if tuple(reader.fieldnames or ()) != COLUMNS:
        raise ValueError("unexpected native funding schema")
    expected_count = (cut_ms - start_ms) // STEP_MS
    selected_count = training_count = warmup_count = jittered_count = 0
    max_jitter_ms = 0
    last_ms = None
    max_abs_rate = Decimal(0)
    exceed = [0, 0, 0]
    selected_sum = Decimal(0)
    for line_no, row in enumerate(reader, start=2):
        if None in row or any(row.get(c) is None for c in COLUMNS):
            raise ValueError(f"{symbol} line {line_no}: malformed CSV row")
        try:
            ms = int(row["fundingTime_ms"])
            stamp = datetime.fromisoformat(row["fundingTime_utc"].replace("Z", "+00:00"))
            rate = Decimal(row["fundingRate"])
            interval = int(row["fundingIntervalHours"])
        except (ValueError, TypeError, InvalidOperation) as exc:
            raise ValueError(f"{symbol} line {line_no}: invalid native funding value") from exc
        if not rate.is_finite() or millis(stamp) != ms:
            raise ValueError(f"{symbol} line {line_no}: nonfinite rate / timestamp mismatch")
        if last_ms is not None and ms <= last_ms:
            raise ValueError(f"{symbol} line {line_no}: nonmonotone or duplicate settlement")
        last_ms = ms
        if ms >= millis(CUTOFF):
            raise ValueError(f"{symbol} line {line_no}: 2026+ holdout firewall")
        if ms < start_ms:
            # Pre-warmup records are never used in Phase243. In particular,
            # SOL's 2022-11 2h settlements must not enter the 8h panel.
            continue
        if ms >= cut_ms:
            raise ValueError(f"{symbol} line {line_no}: beyond requested cutoff")
        scheduled = start_ms + selected_count * STEP_MS
        jitter = ms - scheduled
        if not (0 <= jitter <= 50) or interval != 8:
            raise ValueError(f"{symbol} line {line_no}: missing/off-slot/variable-interval settlement")
        selected_count += 1
        jittered_count += int(jitter > 0)
        max_jitter_ms = max(max_jitter_ms, jitter)
        max_abs_rate = max(max_abs_rate, abs(rate))
        selected_sum += rate
        if scheduled >= train_ms:
            training_count += 1
            for i, threshold in enumerate(THRESHOLDS):
                exceed[i] += int(abs(rate) > threshold)
        else:
            warmup_count += 1
    if selected_count != expected_count:
        raise ValueError(f"{symbol}: incomplete 8h coverage {selected_count}/{expected_count}")
    expected_train = (cut_ms - train_ms) // STEP_MS
    if training_count != expected_train:
        raise ValueError(f"{symbol}: training count mismatch")
    return {
        "symbol": symbol, "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "first_scheduled_utc": start.isoformat(), "cut_exclusive_utc": cut.isoformat(),
        "selected_events": selected_count, "warmup_events": warmup_count,
        "training_events": training_count, "jittered_events": jittered_count,
        "max_jitter_ms": max_jitter_ms, "max_abs_funding_bp": float(max_abs_rate * 10000),
        "training_abs_gt_7bp": exceed[0], "training_abs_gt_14bp": exceed[1],
        "training_abs_gt_28bp": exceed[2],
        "all_selected_signed_rate_sum": str(selected_sum),
    }


def audit_all(root: Path) -> dict:
    assets = {}
    for symbol in ASSETS:
        path = root / f"{symbol}_funding.csv"
        assets[symbol] = audit_bytes(path.read_bytes(), symbol)
    if len({v["selected_events"] for v in assets.values()}) != 1:
        raise ValueError("cross-asset funding coverage mismatch")
    return {
        "namespace": "V98 Independent", "phase": 243,
        "status": "PASS_SOURCE_INTEGRITY_DATA_ONLY_NO_ALPHA",
        "holdout_accessed": False, "external_engines_used": False,
        "settlement_semantics": "scheduled_8h_boundary_with_0_to_50ms_reporting_jitter",
        "assets": assets,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--funding-root", type=Path,
                   default=Path("research/v98_independent/data/phase206_funding"))
    p.add_argument("--out", type=Path,
                   default=Path("research/v98_independent/phase243_funding_source_gate_results.json"))
    args = p.parse_args()
    result = audit_all(args.funding_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                        encoding="utf-8")
    print(json.dumps({"status": result["status"], "assets": len(result["assets"])}))


if __name__ == "__main__":
    main()

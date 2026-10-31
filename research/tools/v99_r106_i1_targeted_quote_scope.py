"""Deterministic I1 original-source procurement windows. No market reads or economics.

Stage A requests reconstructible full-universe pre-Monday books, NOT just
last-300-second updates without the preceding book state. Stage B requires
exact-contract post-entry marks, risk and delivery after a verified selection.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
START = datetime(2021, 12, 9, tzinfo=UTC)
STOP = datetime(2023, 10, 1, tzinfo=UTC)
FOLD_EDGES = (
    START,
    datetime(2022, 4, 20, 4, tzinfo=UTC),
    datetime(2022, 8, 30, 9, tzinfo=UTC),
    datetime(2023, 1, 9, 14, tzinfo=UTC),
    datetime(2023, 5, 21, 19, tzinfo=UTC),
    STOP,
)
FIELDS = (
    "exchange", "symbol", "timestamp", "local_timestamp",
    "bid_price", "ask_price", "bid_amount", "ask_amount",
)


def request():
    first = START + timedelta(days=(7 - START.weekday()) % 7)
    mondays = [first + timedelta(weeks=i) for i in range(94)]
    assert len(mondays) == 94 and mondays[0].date().isoformat() == "2021-12-13"
    eligible = [m for m in mondays if m + timedelta(days=28) < STOP]
    assert len(eligible) == 90
    rows = []
    for monday in eligible:
        window_start = monday - timedelta(seconds=300)
        fold = next(i for i in range(1, 6)
                    if FOLD_EDGES[i - 1] <= monday < FOLD_EDGES[i])
        assert START <= window_start < monday < STOP
        expiry_min = monday + timedelta(days=28)
        expiry_max = min(monday + timedelta(days=35), STOP - timedelta(microseconds=1))
        for asset in ("BTC", "ETH"):
            rows.append({
                "asset": asset,
                "decision_utc": monday.isoformat(),
                "fold": fold,
                "venue": "deribit",
                "instrument_scope": "ALL_ASOF_LISTED_PUTS_28_TO_35D_BEFORE_TRAIN_STOP",
                "expiry_min_inclusive_utc": expiry_min.isoformat(),
                "expiry_max_inclusive_utc": expiry_max.isoformat(),
                "window_start_inclusive_utc": window_start.isoformat(),
                "window_end_exclusive_utc": monday.isoformat(),
                "required_fields": list(FIELDS),
                "required_source": "ORIGINAL_TWO_CLOCK_BBO_SIZE_AND_BOOK_CARRY_IN",
            })
    assert len(rows) == 180
    # Entry-only 450 minutes cannot certify 28-35d held-position risk.
    # Potential maximum-tenor UTC mark days; NOT actual traded days or a
    # vendor price quote. Bound to the sealed TRAIN calendar only.
    potential_days = set()
    for monday in eligible:
        day = (monday - timedelta(days=1)).date()
        last = min((monday + timedelta(days=35)).date(),
                   (STOP - timedelta(days=1)).date())
        while day <= last:
            potential_days.add(day.isoformat())
            day += timedelta(days=1)
    potential_days = sorted(potential_days)
    assert len(potential_days) == 658
    assert potential_days[0] == "2021-12-12"
    assert potential_days[-1] == "2023-09-30"
    payload = {
        "schema": "V99_I1_TARGETED_SOURCE_REQUEST_V1",
        "status": "PROCUREMENT_ONLY_NO_ECONOMICS_NO_PROMOTION",
        "train_start_utc": START.isoformat(),
        "train_stop_exclusive_utc": STOP.isoformat(),
        "fixed_monday_decisions": 90,
        "asset_windows": len(rows),
        "unique_window_minutes": 450,
        "asset_window_minutes": 900,
        "entry_windows_not_sufficient_for_lifecycle_economics": True,
        "potential_max_tenor_daily_mark_days": len(potential_days),
        "potential_max_tenor_daily_mark_utc_dates": potential_days,
        "potential_max_tenor_daily_mark_dates_sha256": hashlib.sha256(
            json.dumps(potential_days, separators=(",", ":")).encode()
        ).hexdigest(),
        "lifecycle_source_note": (
            "Conservative 28-35d maximum-tenor possible daily-mark calendar "
            "envelope only; not actual positions, not a minimum vendor bill, "
            "not licensed data. All 450 entry minutes alone cannot certify "
            "daily risk, expiry settlement, margin or NAV."
        ),
        "source_note": (
            "Require vendor-attested complete as-of listed eligible put state at each "
            "window start (or earlier original updates sufficient to rebuild "
            "it), plus every venue and collector-timestamped change through "
            "the decision. Last-5-minute deltas alone are insufficient."
        ),
        "followup_required": (
            "Only after original books and fixed ex-ante selector are verified: "
            "same selected contracts' complete entry-to-expiry marks and "
            "size-aware exits, native index/delivery, historical fees, "
            "lot/margin/liquidation and independently reexecuted NAV. "
            "Vendor may only sell full UTC days; no assumed availability "
            "or savings from minute-range requests."
        ),
        "written_entitlement_and_gap_attestation_required": True,
        "native_costs_certified": False,
        "economic_train_executed": False,
        "validation_opened": False,
        "holdout_opened": False,
        "promotion_authorized": False,
        "orders_enabled": False,
        "windows": rows,
    }
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    payload["windows_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_targeted_quote_scope OUTPUT.json")
    payload = request()
    path = Path(sys.argv[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in (
        "status", "fixed_monday_decisions", "asset_windows",
        "unique_window_minutes", "windows_sha256"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()

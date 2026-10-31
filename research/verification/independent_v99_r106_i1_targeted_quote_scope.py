"""Independent calendar/source-scope oracle for I1 vendor request; no prices."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
FIRST = datetime(2021, 12, 13, tzinfo=UTC)
END = datetime(2023, 10, 1, tzinfo=UTC)
EDGES = [
    datetime(2021, 12, 9, tzinfo=UTC),
    datetime(2022, 4, 20, 4, tzinfo=UTC),
    datetime(2022, 8, 30, 9, tzinfo=UTC),
    datetime(2023, 1, 9, 14, tzinfo=UTC),
    datetime(2023, 5, 21, 19, tzinfo=UTC),
    END,
]
FIELDS = {"exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount"}


def audit(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    assert obj["schema"] == "V99_I1_TARGETED_SOURCE_REQUEST_V1"
    assert obj["status"] == "PROCUREMENT_ONLY_NO_ECONOMICS_NO_PROMOTION"
    assert obj["train_start_utc"] == "2021-12-09T00:00:00+00:00"
    assert obj["train_stop_exclusive_utc"] == END.isoformat()
    assert obj["written_entitlement_and_gap_attestation_required"] is True
    for k in ("native_costs_certified", "economic_train_executed",
              "validation_opened", "holdout_opened", "promotion_authorized",
              "orders_enabled"):
        assert obj[k] is False, k
    assert "carry" in obj["source_note"].lower() or "state" in obj["source_note"].lower()
    assert "entry-to-expiry" in obj["followup_required"]
    rows = obj["windows"]
    assert obj["fixed_monday_decisions"] == 90
    assert obj["asset_windows"] == 180
    assert obj["unique_window_minutes"] == 450
    assert obj["asset_window_minutes"] == 900
    assert len(rows) == 180
    expected = []
    monday = FIRST
    while monday + timedelta(days=28) < END:
        fold = next(i for i in range(1, 6)
                    if EDGES[i-1] <= monday < EDGES[i])
        for asset in ("BTC", "ETH"):
            expected.append((asset, monday.isoformat(), fold,
                (monday - timedelta(minutes=5)).isoformat(),
                monday.isoformat()))
        monday += timedelta(days=7)
    assert len(expected) == 180
    for row, (asset, decision, fold, lower, upper) in zip(rows, expected):
        assert row["asset"] == asset
        assert row["decision_utc"] == decision
        assert row["fold"] == fold
        assert row["venue"] == "deribit"
        assert row["instrument_scope"] == "ALL_LISTED_OPTIONS_ALL_STRIKES_EXPIRIES"
        assert row["window_start_inclusive_utc"] == lower
        assert row["window_end_exclusive_utc"] == upper
        assert set(row["required_fields"]) == FIELDS
        assert row["required_source"] == "ORIGINAL_TWO_CLOCK_BBO_SIZE_AND_BOOK_CARRY_IN"
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == obj["windows_sha256"]
    return len(rows)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_targeted_quote_scope REQUEST.json")
    print(json.dumps({"independent": "VERIFIED_CALENDAR_ONLY",
                      "asset_windows": audit(sys.argv[1]),
                      "economics": False, "promotion": False}))

#!/usr/bin/env python3
"""Independent Decimal re-execution of partial quote friction; fail closed."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

root = Path("tardis_quote_probe")
m = json.loads((root / "manifest.json").read_text())
out = json.loads((root / "partial_friction.json").read_text())
assert m["complete_train"] is False and out["complete_train"] is False
assert out["promotion"] is False and out["native_fills_certified"] is False
assert out["economic_train_run"] is False
assert [d["date"] for d in m["days"]] == ["2022-01-01", "2023-01-01"]
expected = {}
for entry in m["days"]:
    path = root / entry["sample_file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["csv_sha256"]
    with path.open(newline="", encoding="utf-8") as f:
        records = list(csv.DictReader(f))
    assert len(records) == entry["rows_partial"]
    day_start = int(datetime.combine(date.fromisoformat(entry["date"]), datetime.min.time(),
                                     tzinfo=timezone.utc).timestamp() * 1_000_000)
    values = defaultdict(list)
    with_fees = defaultdict(list)
    counters = defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in records:
        assert r["exchange"] == "deribit"
        asset = r["symbol"].partition("-")[0]
        assert asset in ("BTC", "ETH") and r["symbol"].endswith(("-C", "-P"))
        stamp, arrived = int(r["timestamp"]), int(r["local_timestamp"])
        assert stamp > 0 and day_start <= arrived < day_start + 86_400_000_000
        key = (entry["date"], asset)
        counters[key][0] += 1
        if arrived < stamp:
            counters[key][3] += 1
        elif arrived - stamp > 1_000_000:
            counters[key][4] += 1
        try:
            bid, ask = Decimal(r["bid_price"]), Decimal(r["ask_price"])
            bid_size, ask_size = Decimal(r["bid_amount"]), Decimal(r["ask_amount"])
            if not all(x.is_finite() for x in (bid, ask, bid_size, ask_size)):
                raise InvalidOperation
            if min(bid, ask, bid_size, ask_size) <= 0:
                counters[key][1] += 1
            elif bid >= ask:
                counters[key][2] += 1
            elif arrived >= stamp:
                values[key].append(Decimal(20000) * (ask - bid) / (ask + bid))
                base = Decimal("0.0003")
                cap = Decimal("0.125")
                total = ask - bid + min(base, cap * ask) + min(base, cap * bid)
                with_fees[key].append(Decimal(20000) * total / (ask + bid))
        except (InvalidOperation, ValueError, TypeError):
            counters[key][1] += 1
    for key, c in counters.items():
        spreads = sorted(values[key])
        def quant(seq, p):
            if not seq:
                return None
            # Nearest-rank quantile; independent Decimal calculation.
            index = (p * len(seq) + 99) // 100 - 1
            return round(float(seq[index]), 6)
        expected[key] = {
            "rows_seen": c[0], "invalid_or_missing_quote": c[1],
            "locked_or_crossed": c[2], "negative_arrival_lag": c[3],
            "lag_over_one_second": c[4], "causally_eligible_two_sided": len(spreads),
            "spread_bps_p50": quant(spreads, 50), "spread_bps_p90": quant(spreads, 90),
            "illustrative_standard_fee_roundtrip_bps_p50": quant(sorted(with_fees[key]), 50),
            "illustrative_standard_fee_roundtrip_bps_p90": quant(sorted(with_fees[key]), 90)}
assert len(out["strata"]) == len(expected)
for entry in out["strata"]:
    key = (entry["date"], entry["asset"])
    assert key in expected
    for field, value in expected[key].items():
        assert entry[field] == value, (key, field, entry[field], value)
    print(f"INDEPENDENT PARTIAL QUOTE ORACLE PASS {key} rows={entry['rows_seen']} eligible={entry['causally_eligible_two_sided']} spread_bps_p50={entry['spread_bps_p50']} p90={entry['spread_bps_p90']}")
print("NO FULL TRAIN, NO FILL CERTIFICATION, NO ECONOMIC GATE, NO PROMOTION")

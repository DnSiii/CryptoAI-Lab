#!/usr/bin/env python3
"""Observed one-crossing option-quote friction only. Never a backtest, order or fill."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("tardis_quote_probe")
MANIFEST = json.loads((ROOT / "manifest.json").read_text())
assert MANIFEST["classification"] == "PARTIAL_SOURCE_SAMPLE_ONLY_NOT_EXECUTION_OR_PNL"
assert MANIFEST["complete_train"] is False
assert [d["date"] for d in MANIFEST["days"]] == ["2022-01-01", "2023-01-01"]
FIELDS = {"symbol", "exchange", "timestamp", "local_timestamp", "bid_price",
          "ask_price", "bid_amount", "ask_amount"}

def q(values, p):
    if not values:
        return None
    values = sorted(values)
    return round(values[math.ceil(p * len(values)) - 1], 6)

result = {
    "classification": "PARTIAL_QUOTE_FRICTION_LOWER_BOUND_NOT_PNL",
    "sample_only": True,
    "complete_train": False,
    "native_fills_certified": False,
    "economic_train_run": False,
    "promotion": False,
    "units": "relative bid-ask spread in basis points; no option USD premium inference",
    "strata": [],
    "days": [],
}
for entry in MANIFEST["days"]:
    path = ROOT / entry["sample_file"]
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry["csv_sha256"]
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert FIELDS.issubset(reader.fieldnames or [])
        rows = list(reader)
    assert len(rows) == entry["rows_partial"] and 0 < len(rows) <= 2000
    start = int(datetime.fromisoformat(entry["date"]).replace(tzinfo=timezone.utc).timestamp() * 1_000_000)
    grouped = defaultdict(lambda: {"seen": 0, "clean": [], "fee_inclusive": [], "invalid": 0,
                                    "crossed_or_locked": 0, "negative_arrival_lag": 0,
                                    "lag_over_one_second": 0})
    times = []
    for row in rows:
        assert row["exchange"] == "deribit"
        symbol = row["symbol"]
        assert symbol.endswith(("-C", "-P")) and "-" in symbol
        asset = symbol.split("-", 1)[0]
        assert asset in ("BTC", "ETH")
        g = grouped[asset]
        g["seen"] += 1
        ts = int(row["timestamp"])
        local = int(row["local_timestamp"])
        assert ts > 0 and start <= local < start + 86400 * 1_000_000
        times.append(local)
        if local < ts:
            g["negative_arrival_lag"] += 1
        elif local - ts > 1_000_000:
            g["lag_over_one_second"] += 1
        try:
            bid, ask = float(row["bid_price"]), float(row["ask_price"])
            bsz, asz = float(row["bid_amount"]), float(row["ask_amount"])
            if not all(math.isfinite(x) for x in (bid, ask, bsz, asz)):
                raise ValueError("nonfinite")
            if min(bid, ask, bsz, asz) <= 0:
                g["invalid"] += 1
            elif bid >= ask:
                g["crossed_or_locked"] += 1
            elif local >= ts:
                g["clean"].append(20000 * (ask - bid) / (ask + bid))
                standard_fee_buy = min(0.0003, 0.125 * ask)
                standard_fee_sell = min(0.0003, 0.125 * bid)
                g["fee_inclusive"].append(20000 * (ask - bid + standard_fee_buy + standard_fee_sell) / (ask + bid))
        except (TypeError, ValueError):
            g["invalid"] += 1
    result["days"].append({"date": entry["date"], "rows": len(rows),
                           "sample_span_seconds": round((max(times) - min(times)) / 1_000_000, 6)})
    for asset, g in sorted(grouped.items()):
        result["strata"].append({
            "date": entry["date"], "asset": asset, "rows_seen": g["seen"],
            "causally_eligible_two_sided": len(g["clean"]),
            "invalid_or_missing_quote": g["invalid"],
            "locked_or_crossed": g["crossed_or_locked"],
            "negative_arrival_lag": g["negative_arrival_lag"],
            "lag_over_one_second": g["lag_over_one_second"],
            "spread_bps_p50": q(g["clean"], .5),
            "spread_bps_p90": q(g["clean"], .9),
            "illustrative_standard_fee_roundtrip_bps_p50": q(g["fee_inclusive"], .5),
            "illustrative_standard_fee_roundtrip_bps_p90": q(g["fee_inclusive"], .9),
        })
assert sum(d["rows"] for d in result["days"]) == 4000
assert result["promotion"] is False and result["complete_train"] is False
(ROOT / "partial_friction.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))

#!/usr/bin/env python3
"""Read-only, fail-closed cross-feed eligibility audit for NEW research only.

Usage: python scripts/audit_v99_instrument_coverage.py paper_data_sync_v13.json
No strategy decisions, historical edits, or instrument substitutions.
"""
import datetime as dt
import json
import sys

UTC = dt.timezone.utc
MAX_KLINE_AGE_H = 2

def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("naive timestamp")
    return t.astimezone(UTC)

def audit(doc):
    boundary = timestamp(doc["expected_latest_closed_hour"])
    max_funding = doc.get("maximum_funding_lag_hours")
    if type(max_funding) not in (int, float) or not 0 <= max_funding <= 12:
        raise ValueError("unsafe funding threshold")
    rows = {}
    symbols = doc.get("symbols")
    if not isinstance(symbols, dict) or not symbols:
        raise ValueError("missing instruments")
    lagmap = doc.get("funding_lag_hours", {})
    for symbol, feeds in sorted(symbols.items()):
        reasons = []
        try:
            k = timestamp(feeds["klines"]["latest"])
            f = timestamp(feeds["funding"]["latest"])
            if k > boundary or f > boundary + dt.timedelta(hours=1):
                reasons.append("FUTURE_FEED")
            if (boundary - k).total_seconds() / 3600 > MAX_KLINE_AGE_H:
                reasons.append("STALE_KLINE")
            if (boundary - f).total_seconds() / 3600 > max_funding:
                reasons.append("STALE_FUNDING")
            declared = lagmap.get(symbol)
            if declared is None:
                reasons.append("MISSING_DECLARED_FUNDING_LAG")
            elif type(declared) not in (int, float) or abs(declared - (boundary - f).total_seconds() / 3600) > 1.01:
                reasons.append("FUNDING_LAG_MISMATCH")
        except (ValueError, KeyError, TypeError, OverflowError):
            reasons.append("INVALID_FEED")
        # A passing market-data check NEVER certifies exchange fills, native
        # fee tier, contract lifecycle, or settled funding for economic use.
        rows[symbol] = {"market_data_gate": "FAIL" if reasons else "PASS",
                        "economic_gate": "UNVERIFIED",
                        "reasons": reasons}
    return rows

def selftest():
    base = {"expected_latest_closed_hour":"2026-11-07T01:00:00Z",
            "maximum_funding_lag_hours":12,
            "funding_lag_hours":{"BTCUSDT":1},
            "symbols":{"BTCUSDT":{"klines":{"latest":"2026-11-07T01:00:00Z"},
                                  "funding":{"latest":"2026-11-07T00:00:00Z"}}}}
    assert audit(base)["BTCUSDT"]["market_data_gate"] == "PASS"
    assert audit(base)["BTCUSDT"]["economic_gate"] == "UNVERIFIED"
    base["symbols"]["BTCUSDT"]["klines"]["latest"] = "2025-05-21T09:00:00Z"
    assert "STALE_KLINE" in audit(base)["BTCUSDT"]["reasons"]
    base["symbols"]["BTCUSDT"]["klines"]["latest"] = "2026-11-07T01:00:00Z"
    base["symbols"]["BTCUSDT"]["funding"]["latest"] = "2025-01-01T00:00:00Z"
    assert "STALE_FUNDING" in audit(base)["BTCUSDT"]["reasons"]
    base["symbols"]["BTCUSDT"]["funding"]["latest"] = "2026-11-07T00:00:00Z"
    del base["funding_lag_hours"]["BTCUSDT"]
    assert "MISSING_DECLARED_FUNDING_LAG" in audit(base)["BTCUSDT"]["reasons"]
    base["symbols"]["BTCUSDT"]["klines"]["latest"] = "2026-11-08T00:00:00Z"
    assert "FUTURE_FEED" in audit(base)["BTCUSDT"]["reasons"]
    print("selftest: PASS (fresh, stale kline, stale funding, missing lag, future)")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) == 2:
        with open(sys.argv[1], encoding="utf-8") as fp:
            report = audit(json.load(fp))
        print(json.dumps(report, indent=2, sort_keys=True))
        if any(r["market_data_gate"] != "PASS" for r in report.values()):
            sys.exit(2)
    else:
        sys.exit("usage: audit_v99_instrument_coverage.py <manifest.json> | --selftest")

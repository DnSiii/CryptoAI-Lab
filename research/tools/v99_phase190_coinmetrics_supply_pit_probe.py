#!/usr/bin/env python3
"""Phase190 DATA_ONLY PIT probe for Coin Metrics SplyCur.

Bounded to historical TRAIN dates. It inspects publication/review metadata only;
it never reads price, computes a signal/PnL, or touches holdout observations.
Fail closed if a defensible observation-availability timestamp is unavailable.
"""
from __future__ import annotations
import json, urllib.parse, urllib.request
from datetime import datetime, timezone

BASE = "https://community-api.coinmetrics.io/v4"
ASSETS = ("usdt", "usdc")
METRIC = "SplyCur"
START = "2021-01-01"
END = "2021-01-07"


def get(asset: str) -> dict:
    q = urllib.parse.urlencode({
        "assets": asset, "metrics": METRIC, "frequency": "1d",
        "start_time": START, "end_time": END, "page_size": "20",
        "paging_from": "start", "pretty": "false",
    })
    req = urllib.request.Request(
        f"{BASE}/timeseries/asset-metrics?{q}",
        headers={"User-Agent": "CryptoAI-Lab-V99-Phase190-PIT-probe/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main() -> None:
    out = {
        "probe": "V99_R106_PHASE190_SPLYCUR_PIT_DATA_ONLY",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "window": [START, END],
        "pnl_read": False,
        "price_read": False,
        "holdout_observations_read": False,
        "assets": {},
    }
    gate = True
    for asset in ASSETS:
        rows = get(asset).get("data", [])
        status_key, stime_key = f"{METRIC}-status", f"{METRIC}-status-time"
        # Do not persist metric values; only timing/schema evidence.
        evidence = []
        for row in rows:
            evidence.append({
                "time": row.get("time"),
                "status": row.get(status_key),
                "status_time": row.get(stime_key),
                "keys": sorted(k for k in row if k != METRIC),
            })
        has_status = bool(rows) and all(e.get("status") for e in evidence)
        has_stime = bool(rows) and all(e.get("status_time") for e in evidence)
        # PIT admission requires an explicit per-observation availability/review time.
        passed = has_status and has_stime
        gate &= passed
        out["assets"][asset] = {
            "rows": len(rows), "status_present_all": has_status,
            "status_time_present_all": has_stime, "evidence": evidence,
            "pit_gate_pass": passed,
        }
    out["pit_gate_pass"] = gate
    print(json.dumps(out, sort_keys=True, indent=2))
    if not gate:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

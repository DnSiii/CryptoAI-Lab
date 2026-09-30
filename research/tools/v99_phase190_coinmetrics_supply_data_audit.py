#!/usr/bin/env python3
"""DATA_ONLY Phase190 source audit. Never fetches price/PnL or holdout observations."""
from __future__ import annotations
import hashlib, json, urllib.parse, urllib.request
from datetime import datetime, timezone

BASE = "https://community-api.coinmetrics.io/v4"
ASSETS = ("usdt", "usdc")
METRIC = "SplyCur"
FREQ = "1d"


def get_json(path: str, params: dict[str, str]):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-Lab-V99-Phase190-data-audit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    return url, raw, json.loads(raw)


def main() -> None:
    out = {
        "audit": "V99_R106_PHASE190_COINMETRICS_STABLECOIN_SUPPLY_DATA_ONLY",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "metric": METRIC,
        "frequency": FREQ,
        "pnl_read": False,
        "holdout_observations_read": False,
        "assets": {},
    }
    all_pass = True
    for asset in ASSETS:
        url, raw, obj = get_json("/catalog-v2/asset-metrics", {"assets": asset})
        entries = obj.get("data", [])
        record = next((x for x in entries if x.get("asset") == asset), None)
        metric = None
        if record:
            metric = next((m for m in record.get("metrics", []) if m.get("metric") == METRIC), None)
        freq = None
        if metric:
            freq = next((f for f in metric.get("frequencies", []) if f.get("frequency") == FREQ), None)
        passed = bool(freq and freq.get("community") is True and freq.get("min_time"))
        all_pass &= passed
        out["assets"][asset] = {
            "catalog_url": url,
            "raw_catalog_sha256": hashlib.sha256(raw).hexdigest(),
            "metric_present": metric is not None,
            "frequency_present": freq is not None,
            "community": None if not freq else freq.get("community"),
            "min_time": None if not freq else freq.get("min_time"),
            "max_time": None if not freq else freq.get("max_time"),
            "catalog_gate_pass": passed,
        }
    out["catalog_gate_pass"] = all_pass
    print(json.dumps(out, sort_keys=True, indent=2))
    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

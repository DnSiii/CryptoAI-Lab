#!/usr/bin/env python3
"""Authenticated Phase243 Clean-4 2022-12 through 2025-12 reader (data only).

Separate from the legacy 2024 reader. No signal, optimization, PnL or holdout.
"""
import csv
import hashlib
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS, load_funding

START_MS = 1669852800000
END_MS = 1767225600000
EXPECTED_HOURS = (END_MS - START_MS) // HOUR_MS

def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(price_root, price_manifest_path, funding_root):
    paths = (price_root, price_manifest_path, funding_root)
    if any("v98_independent" not in Path(p).absolute().parts for p in paths):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    price_root, price_manifest_path, funding_root = map(Path, paths)
    manifest = json.loads(price_manifest_path.read_text())
    if (manifest.get("mode") != "CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA"
            or manifest.get("holdout_accessed") is not False
            or set(manifest.get("prices", {})) != set(ASSETS)):
        raise ValueError("UNTRUSTED_PHASE243_MANIFEST")
    funding_manifest_path = funding_root / "funding_manifest.json"
    funding_manifest = json.loads(funding_manifest_path.read_text())
    if (funding_manifest.get("mode") != "V98_NATIVE_FUNDING_CANONICAL_SOURCE_ONLY"
            or funding_manifest.get("holdout_accessed") is not False
            or set(funding_manifest.get("assets", {})) != set(ASSETS)):
        raise ValueError("UNTRUSTED_NATIVE_FUNDING_MANIFEST")
    bars, funding = {}, {}
    for asset in ASSETS:
        path = price_root / (asset + "_1h.csv")
        if _sha(path) != manifest["prices"][asset]["canonical_sha256"]:
            raise ValueError("PHASE243_PRICE_HASH_MISMATCH_" + asset)
        asset_bars = []
        with path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                stamp = datetime.fromisoformat(row["open_time"].replace("Z", "+00:00"))
                if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
                    raise ValueError("NON_UTC_PHASE243_TIMESTAMP")
                t = int(stamp.timestamp() * 1000)
                if t != START_MS + len(asset_bars) * HOUR_MS or t >= END_MS:
                    raise ValueError("PHASE243_HOUR_CONTINUITY_" + asset)
                values = tuple(float(row[k]) for k in ("open", "high", "low", "close", "quote_volume"))
                op, hi, lo, cl, vol = values
                if (not all(math.isfinite(x) for x in values) or
                        min(op, hi, lo, cl) <= 0 or vol < 0 or
                        lo > min(op, cl) or hi < max(op, cl) or lo > hi):
                    raise ValueError("PHASE243_INVALID_OHLC_" + asset)
                asset_bars.append(values)
        if len(asset_bars) != EXPECTED_HOURS:
            raise ValueError("PHASE243_INCOMPLETE_HISTORY_" + asset)
        funding_path = funding_root / (asset + "_native_funding.csv")
        if _sha(funding_path) != funding_manifest["assets"][asset]["sha256"]:
            raise ValueError("PHASE243_FUNDING_HASH_MISMATCH_" + asset)
        events = load_funding(funding_path)
        if any(t < START_MS or t >= END_MS for t in events):
            raise ValueError("PHASE243_FUNDING_OUT_OF_TRAINING")
        bars[asset] = asset_bars
        funding[asset] = events
    return {"bars": bars, "funding": funding, "hours": EXPECTED_HOURS,
            "price_manifest_sha256": _sha(price_manifest_path),
            "funding_manifest_sha256": _sha(funding_manifest_path),
            "holdout_accessed": False, "status": "AUTHENTICATED_TRAINING_DATA_ONLY"}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--prices", type=Path, required=True)
    p.add_argument("--price-manifest", type=Path, required=True)
    p.add_argument("--funding", type=Path, required=True)
    a = p.parse_args()
    result = load(a.prices, a.price_manifest, a.funding)
    print(json.dumps({k: v for k, v in result.items() if k not in ("bars", "funding")}, sort_keys=True))

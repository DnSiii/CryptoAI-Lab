#!/usr/bin/env python3
"""Phase224 realized-funding snapshot integrity gate.

This tool intentionally does NOT fetch data. It validates a candidate V98-only,
training-only realized funding snapshot before Phase224 may be evaluated.
Expected CSV columns: timestamp, symbol, funding_rate; optional source_semantic.
No 2026+ row is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

ASSETS = ("BTC", "ETH", "BNB", "SOL", "XRP")
CUTOFF = pd.Timestamp("2026-01-01T00:00:00Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(path: Path) -> dict:
    df = pd.read_csv(path)
    required = {"timestamp", "symbol", "funding_rate"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    rates = pd.to_numeric(df["funding_rate"], errors="raise")
    symbols = df["symbol"].astype(str).str.upper().str.replace("USDT", "", regex=False)

    if len(df) == 0:
        raise ValueError("empty snapshot")
    if ts.max() >= CUTOFF:
        raise ValueError(f"holdout firewall violation: max timestamp {ts.max()}")
    if not rates.map(pd.notna).all():
        raise ValueError("non-finite funding rate")

    unexpected = sorted(set(symbols) - set(ASSETS))
    missing_assets = sorted(set(ASSETS) - set(symbols))
    if unexpected or missing_assets:
        raise ValueError(f"asset universe mismatch: unexpected={unexpected}, missing={missing_assets}")

    work = pd.DataFrame({"timestamp": ts, "symbol": symbols, "funding_rate": rates})
    duplicates = int(work.duplicated(["symbol", "timestamp"]).sum())
    if duplicates:
        raise ValueError(f"duplicate symbol/timestamp rows: {duplicates}")

    semantic = None
    if "source_semantic" in df.columns:
        vals = sorted(set(df["source_semantic"].dropna().astype(str).str.lower()))
        semantic = vals
        if vals != ["realized_funding"]:
            raise ValueError(f"source_semantic must be only realized_funding, got {vals}")

    per_asset = {}
    for asset in ASSETS:
        g = work[work.symbol == asset].sort_values("timestamp")
        gaps_hours = g.timestamp.diff().dt.total_seconds().div(3600).dropna()
        per_asset[asset] = {
            "rows": int(len(g)),
            "first": g.timestamp.min().isoformat(),
            "last": g.timestamp.max().isoformat(),
            "max_gap_hours": float(gaps_hours.max()) if len(gaps_hours) else None,
            "mean_rate": float(g.funding_rate.mean()),
            "min_rate": float(g.funding_rate.min()),
            "max_rate": float(g.funding_rate.max()),
        }

    return {
        "status": "PASS_STRUCTURAL_INTEGRITY",
        "file": str(path),
        "sha256": sha256(path),
        "rows": int(len(work)),
        "min_timestamp": work.timestamp.min().isoformat(),
        "max_timestamp": work.timestamp.max().isoformat(),
        "holdout_firewall": bool(work.timestamp.max() < CUTOFF),
        "duplicates": duplicates,
        "source_semantic": semantic,
        "per_asset": per_asset,
        "note": "PASS does not prove venue semantics; provenance evidence must separately establish that observations are realized settlements known by their timestamps.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = audit(args.csv)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

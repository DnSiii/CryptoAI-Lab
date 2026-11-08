#!/usr/bin/env python3
"""E2 TRAIN-only execution readiness. Never submits orders or reports PnL."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from v99_r106_e2_train_source_gate import audit, parse_time, CUTOFF

def read_receipts(path, digest, required):
    p = Path(path)
    if not p.is_file() or not digest or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
        raise ValueError("original receipt absent or sha256 mismatch")
    with p.open(newline="") as f:
        reader = csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("native receipt schema incomplete")
        rows = list(reader)
    if not rows:
        raise ValueError("native receipts empty")
    for row in rows:
        t = parse_time(row["timestamp"])
        if t >= CUTOFF:
            raise ValueError("receipt crosses TRAIN boundary")
    return len(rows)

def readiness(bars, bars_sha, funding, funding_sha, fees, fees_sha, fills, fills_sha):
    source = audit(bars, bars_sha)
    # Receipt existence alone is NOT reconciliation: historical execution fills
    # for hypothetical trades cannot be certified by unrelated real executions.
    counts = {
        "settled_funding": read_receipts(funding, funding_sha, {"timestamp","symbol","funding_rate","source_id"}),
        "native_fees": read_receipts(fees, fees_sha, {"timestamp","symbol","fee_tier","fee_rate","source_id"}),
        "native_execution": read_receipts(fills, fills_sha, {"timestamp","symbol","price","quantity","fee","source_id"}),
    }
    return {"status":"RECEIPTS_PRESENT_UNRECONCILED_NO_ECONOMICS",
            "source":source,"receipt_counts":counts,
            "historical_hypothetical_fills_exchange_certified":False,
            "five_fold_economics_run":False,"promotion":False,"orders":0}

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for name in ("bars","funding","fees","fills"):
        p.add_argument("--"+name,required=True)
        p.add_argument("--"+name+"-sha256",required=True)
    a=p.parse_args()
    print(json.dumps(readiness(a.bars,a.bars_sha256,a.funding,a.funding_sha256,
                               a.fees,a.fees_sha256,a.fills,a.fills_sha256),sort_keys=True))

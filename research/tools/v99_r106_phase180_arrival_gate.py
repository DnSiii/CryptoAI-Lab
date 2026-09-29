#!/usr/bin/env python3
"""Fail-closed DATA gate for Phase180 historical Bitcoin block-arrival timestamps.

No PnL or holdout data is read. A single preregistered observer/source is evaluated;
combining observers or substituting header timestamps for missing arrivals is forbidden.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HOLDOUT_START_MS = int(datetime(2024, 1, 18, tzinfo=timezone.utc).timestamp() * 1000)
BUCKET = 1008


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path):
    rows=[]
    with path.open(newline="") as f:
        for n,row in enumerate(csv.reader(f),1):
            if len(row) < 3: raise ValueError(f"row {n}: expected height,hash,timestamp_ms")
            height=int(row[0]); block_hash=row[1].strip().lower(); ts=int(row[2])
            if height < 0 or len(block_hash) != 64 or any(c not in '0123456789abcdef' for c in block_hash):
                raise ValueError(f"row {n}: invalid height/hash")
            rows.append((height,block_hash,ts))
    if not rows: raise ValueError("empty source")
    return rows


def evaluate(path: Path, train_start_ms: int, train_end_ms: int, min_bucket_coverage: float):
    if train_end_ms > HOLDOUT_START_MS: raise ValueError("train_end crosses untouched holdout firewall")
    rows=load(path)
    pairs=Counter((h,x) for h,x,_ in rows)
    heights={}
    conflicts=[]
    for h,x,t in rows:
        old=heights.get(h)
        if old and old[0] != x: conflicts.append(h)
        if old is None or t < old[1]: heights[h]=(x,t)  # earliest duplicate within SAME observer only
    selected={h:v for h,v in heights.items() if train_start_ms <= v[1] < train_end_ms}
    if not selected: raise ValueError("no TRAIN observations")
    leaked=[h for h,(_,t) in heights.items() if t >= HOLDOUT_START_MS]
    # leaked rows may exist in raw archive, but they are never admitted to canonical TRAIN output.
    hs=sorted(selected)
    bucket_counts=Counter(h//BUCKET for h in hs)
    bucket_span=range(hs[0]//BUCKET, hs[-1]//BUCKET+1)
    coverage={str(b): bucket_counts[b]/BUCKET for b in bucket_span}
    internal_missing=sum(max(0,b-a-1) for a,b in zip(hs,hs[1:]))
    pass_gate=(not conflicts and min(coverage.values()) >= min_bucket_coverage and internal_missing == 0)
    canonical=''.join(f"{h},{selected[h][0]},{selected[h][1]}\n" for h in hs).encode()
    return {
      "phase":"180","status":"PASS" if pass_gate else "FAIL","alpha_admitted":False,
      "source_policy":"single_observer_only","cross_source_min_forbidden":True,
      "header_time_fallback_forbidden":True,"holdout_start_ms":HOLDOUT_START_MS,
      "raw_sha256":sha256(path),"canonical_train_sha256":hashlib.sha256(canonical).hexdigest(),
      "raw_rows":len(rows),"train_unique_heights":len(hs),"train_height_min":hs[0],"train_height_max":hs[-1],
      "duplicate_pairs":sum(v-1 for v in pairs.values() if v>1),"conflicting_heights":sorted(set(conflicts)),
      "internal_missing_heights":internal_missing,"bucket_coverage":coverage,
      "raw_rows_at_or_after_holdout":len(leaked),"min_bucket_coverage_required":min_bucket_coverage,
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument("source_csv",type=Path); p.add_argument("--train-start-ms",type=int,required=True)
    p.add_argument("--train-end-ms",type=int,default=HOLDOUT_START_MS); p.add_argument("--min-bucket-coverage",type=float,default=0.99)
    p.add_argument("--report",type=Path,required=True); a=p.parse_args()
    r=evaluate(a.source_csv,a.train_start_ms,a.train_end_ms,a.min_bucket_coverage)
    a.report.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")
    raise SystemExit(0 if r["status"]=="PASS" else 2)
if __name__=="__main__": main()

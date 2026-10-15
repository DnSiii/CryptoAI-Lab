"""Read-only, byte-verified two-observation OKX 1H continuity witness.

A first-party HTTP observation is not a venue-signed exchange receipt.
Never treats archive hashes, funding notices, or cross-venue prices as
independent trading-PnL authentication. No strategy or holdout access.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from research.tools import v99_r106_okx_prospective_receipt as okx

KEYS=okx.INSTS
MAX_GAP_HOURS=1

def strict_json(raw):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out: raise ValueError("duplicate_json_key:"+k)
            out[k]=v
        return out
    def reject(value):raise ValueError("nonfinite_json_constant:"+value)
    return json.loads(raw,object_pairs_hook=unique,parse_constant=reject)

def load(root):
    root=Path(root)
    manifest=strict_json((root/"manifest.json").read_bytes())
    if (manifest.get("mode")!="DATA_ONLY" or
        manifest.get("schema")!="V99_R106_OKX_PROSPECTIVE_ASOF_V1" or
        manifest.get("paper_publication_authorized") is not False or
        manifest.get("promotion_authorized") is not False or
        manifest.get("real_orders_enabled") is not False or
        set(manifest.get("instruments",{}))!=set(KEYS)):
        raise ValueError("unapproved_asof_manifest")
    results={}
    for symbol in KEYS:
        item=manifest["instruments"][symbol]
        raw=(root/(symbol+".raw.json")).read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=item.get("source_raw_sha256"):
            raise ValueError(symbol+":raw_hash_mismatch")
        if item.get("source_http_url")!=okx.HOST+okx.candle_path(symbol):
            raise ValueError(symbol+":source_url_not_authorized")
        reply={"raw":raw,"received_utc":item["received_utc"]}
        verified=okx.validate_candles(reply,symbol)
        if verified["latest_confirmed_close_utc"]!=item.get("latest_confirmed_close_utc"):
            raise ValueError(symbol+":manifest_vs_raw_close_mismatch")
        bars={}
        for bar in okx.parse(reply):
            if bar[8]!="1":continue
            key=okx.iso(datetime.fromtimestamp(int(bar[0])/1000,okx.UTC))
            bars[key]=bar
        results[symbol]={
            "received_utc":item["received_utc"],
            "latest_close":verified["latest_confirmed_close_utc"],
            "raw_sha256":digest,
            "confirmed_bars":bars,
        }
    if len({x["latest_close"] for x in results.values()})!=1:
        raise ValueError("instrument_closes_diverge")
    if okx.as_utc(manifest["last_received_utc"]) < max(okx.as_utc(x["received_utc"]) for x in results.values()):
        raise ValueError("nonmonotonic_manifest_capture")
    return {"manifest":manifest,"instruments":results}

def evaluate(previous,current):
    a=previous["instruments"];b=current["instruments"]
    older=okx.as_utc(previous["manifest"]["last_received_utc"])
    newer=okx.as_utc(current["manifest"]["last_received_utc"])
    if newer<=older:raise ValueError("repeated_or_reversed_acquisition")
    old_close=okx.as_utc(next(iter(a.values()))["latest_close"])
    new_close=okx.as_utc(next(iter(b.values()))["latest_close"])
    if new_close<old_close:raise ValueError("source_confirmed_close_regressed")
    diff=(new_close-old_close).total_seconds()/3600
    if int(diff)!=diff:raise ValueError("nonhourly_source_advancement")
    # Compare confirmed overlaps even when both captures cover the same hour.
    # Same-hour snapshots are not independent evidence, but may reveal revisions.
    report={}
    changed=0
    overlap_total=0
    for sym in KEYS:
        aa=a[sym]["confirmed_bars"];bb=b[sym]["confirmed_bars"]
        keys=sorted(set(aa)&set(bb))
        changed_times=[time for time in keys if aa[time]!=bb[time]]
        changed+=len(changed_times);overlap_total+=len(keys)
        report[sym]={"overlap_hours":len(keys),"revised_overlap_hours":changed_times,
                     "old_raw_sha256":a[sym]["raw_sha256"],
                     "new_raw_sha256":b[sym]["raw_sha256"],
                     "old_last_close":a[sym]["latest_close"],
                     "new_last_close":b[sym]["latest_close"]}
    issues=[]
    if diff==0:issues.append("REPEAT_SAME_CONFIRMED_HOUR_NOT_INDEPENDENT_EVIDENCE")
    if diff>MAX_GAP_HOURS:issues.append("UNATTESTED_HOURLY_GAP:"+str(int(diff))+"h")
    if overlap_total==0:issues.append("NO_IDENTICAL_BAR_OBSERVATION_WINDOW")
    if changed:issues.append("CONFIRMED_SOURCE_REVISIONS:"+str(changed))
    return {
        "schema":"V99_R106_OKX_MULTIHOUR_CONTINUITY_V1",
        "status":("DATA_ONLY_HOLD_SAME_CONFIRMED_HOUR" if diff==0 else
                  "SOURCE_CONTINUITY_OBSERVED_ONLY" if not issues else "DATA_ONLY_HOLD_CONTINUITY"),
        "issues":issues,
        "previous_capture_utc":previous["manifest"]["last_received_utc"],
        "current_capture_utc":current["manifest"]["last_received_utc"],
        "previous_confirmed_close_utc":okx.iso(old_close),
        "current_confirmed_close_utc":okx.iso(new_close),
        "elapsed_source_hours":int(diff),
        "overlap_observations":overlap_total,
        "revised_confirmed_hours":changed,
        "instruments":report,
        "source_independently_exchange_signed":False,
        "historical_first_seen_authenticated":False,
        "binance_to_okx_strategy_transfer_authorized":False,
        "full_native_fee_funding_settlement_authenticated":False,
        "paper_publication_authorized":False,
        "promotion_authorized":False,
        "holdout_accessed":False,
        "economic_trials":0,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--previous",required=True,type=Path)
    p.add_argument("--current",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=evaluate(load(args.previous),load(args.current))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"issues":result["issues"],
                      "hours":result["elapsed_source_hours"],
                      "publication_authorized":False}))

if __name__=="__main__":main()

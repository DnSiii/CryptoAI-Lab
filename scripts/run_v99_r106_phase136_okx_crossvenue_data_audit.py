#!/usr/bin/env python3
"""V99 R106 Phase136 OKX cross-venue DATA_ONLY feasibility audit.

Downloads only the frozen training interval from OKX public 1H history candles.
Persists integrity/coverage metadata and hashes, never market values or PnL.
"""
from __future__ import annotations
import hashlib, json, math, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/"reports"/"candidate_v99_r106_phase136_okx_crossvenue_data_audit.json"
BASE="https://www.okx.com/api/v5/market/history-candles"
START=datetime(2021,12,1,tzinfo=timezone.utc)
END=datetime(2024,1,18,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000); END_MS=int(END.timestamp()*1000)
HOUR_MS=3600_000
EXPECTED=(END_MS-START_MS)//HOUR_MS
INSTRUMENTS=("BTC-USDT-SWAP","ETH-USDT-SWAP","SOL-USDT-SWAP","XRP-USDT-SWAP","DOGE-USDT-SWAP")
FOLD_ANCHORS=(
    datetime(2021,12,1,tzinfo=timezone.utc),
    datetime(2022,6,13,12,tzinfo=timezone.utc),
    datetime(2022,12,25,tzinfo=timezone.utc),
    datetime(2023,7,7,12,tzinfo=timezone.utc),
    datetime(2024,1,17,23,tzinfo=timezone.utc),
)

def fetch_json(params, retries=5):
    last=None
    for attempt in range(retries):
        try:
            req=Request(BASE+"?"+urlencode(params),headers={
                "User-Agent":"CryptoAI-Lab-V99-R106-Phase136/1.0",
                "Accept":"application/json",
                "Connection":"close",
            })
            with urlopen(req,timeout=45) as r:
                obj=json.loads(r.read().decode("utf-8"))
            if obj.get("code")!="0":
                raise RuntimeError(f"OKX code={obj.get('code')} msg={obj.get('msg')}")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<retries:
                time.sleep(min(10,1.5*(attempt+1)))
    raise RuntimeError(f"OKX request failed after {retries} retries: {last!r}")

def acquire(inst):
    cursor=END_MS
    rows={}
    requests=0
    raw_hash_rows=[]
    while True:
        obj=fetch_json({"instId":inst,"bar":"1H","after":str(cursor),"limit":"300"})
        requests+=1
        data=obj.get("data") or []
        if not data:
            break
        page_ts=[]
        for row in data:
            if len(row)<9:
                raise RuntimeError(f"{inst}: unexpected row length {len(row)}")
            ts=int(row[0]); page_ts.append(ts)
            if START_MS <= ts < END_MS:
                # Full normalized row participates in the digest, but values are never persisted.
                norm="|".join(str(x) for x in row)
                if ts in rows and rows[ts] != norm:
                    raise RuntimeError(f"{inst}: conflicting duplicate timestamp {ts}")
                rows[ts]=norm
        oldest=min(page_ts)
        if oldest<=START_MS:
            break
        if oldest>=cursor:
            raise RuntimeError(f"{inst}: pagination did not move backward")
        cursor=oldest
        time.sleep(0.12)
        if requests>1000:
            raise RuntimeError(f"{inst}: pagination safety limit")
    timestamps=sorted(rows)
    normalized="\n".join(rows[t] for t in timestamps).encode()
    digest=hashlib.sha256(normalized).hexdigest()
    unfinished=sum(1 for t in timestamps if rows[t].split("|")[-1]!="1")
    duplicate_count=0
    gaps=sum(1 for a,b in zip(timestamps,timestamps[1:]) if b-a!=HOUR_MS)
    coverage=len(timestamps)/EXPECTED if EXPECTED else 0.0
    anchor_presence=[]
    ts_set=set(timestamps)
    for a in FOLD_ANCHORS:
        x=int(a.timestamp()*1000)
        # source need not have exactly the anchor if exchange had an isolated outage;
        # require a candle within +/- 1 hour.
        anchor_presence.append(any((x+d*HOUR_MS) in ts_set for d in (-1,0,1)))
    return {
        "rows":len(timestamps),
        "coverage":coverage,
        "first_timestamp":datetime.fromtimestamp(timestamps[0]/1000,tz=timezone.utc).isoformat() if timestamps else None,
        "last_timestamp":datetime.fromtimestamp(timestamps[-1]/1000,tz=timezone.utc).isoformat() if timestamps else None,
        "duplicate_timestamps":duplicate_count,
        "non_hourly_gaps":gaps,
        "unfinished_candles":unfinished,
        "fold_anchor_presence":anchor_presence,
        "all_fold_anchors_present":all(anchor_presence),
        "normalized_full_rows_sha256":digest,
        "requests":requests,
    }

def main():
    first={}; second={}
    for inst in INSTRUMENTS:
        first[inst]=acquire(inst)
    for inst in INSTRUMENTS:
        second[inst]=acquire(inst)
    result={}
    pass_count=0
    for inst in INSTRUMENTS:
        a,b=first[inst],second[inst]
        reproducible=a["normalized_full_rows_sha256"]==b["normalized_full_rows_sha256"] and a["rows"]==b["rows"]
        passed=(
            a["coverage"]>=0.98 and a["duplicate_timestamps"]==0 and
            a["unfinished_candles"]==0 and a["all_fold_anchors_present"] and reproducible
        )
        pass_count+=int(passed)
        result[inst]={
            **{k:v for k,v in a.items() if k!="normalized_full_rows_sha256"},
            "normalized_full_rows_sha256":a["normalized_full_rows_sha256"],
            "reproducible_second_acquisition":reproducible,
            "second_sha256":b["normalized_full_rows_sha256"],
            "passed":passed,
        }
    decision="PASS_DATA_ONLY" if pass_count>=4 else "FAIL_DATA_NO_ALPHA"
    out={
        "study":"V99 R106 Phase136 — OKX CROSS-VENUE HOURLY DATA FEASIBILITY ONLY",
        "status":decision,
        "mode":"DATA_ONLY_NO_ALPHA_NO_PNL",
        "frozen_assets_untouched":{"v16":True,"v99_frozen":True},
        "source":{"provider":"OKX","endpoint":BASE,"bar":"1H","public_endpoint":True},
        "window":{"start":START.isoformat(),"end_exclusive":END.isoformat(),"expected_hours":EXPECTED},
        "frozen_instruments":list(INSTRUMENTS),
        "instruments":result,
        "passing_instruments":pass_count,
        "required_passing_instruments":4,
        "return_relation_computed":False,
        "alpha_computed":False,
        "pnl_computed":False,
        "holdout_used":False,
        "next_gate":"PASS permits a separately preregistered cross-venue economic hypothesis; FAIL closes this immediate source path.",
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":decision,"passing_instruments":pass_count,
                      "coverage":{k:round(v["coverage"],6) for k,v in result.items()},
                      "requests":{k:v["requests"] for k,v in result.items()}},indent=2))
    return 0 if decision=="PASS_DATA_ONLY" else 2

if __name__=="__main__":
    raise SystemExit(main())

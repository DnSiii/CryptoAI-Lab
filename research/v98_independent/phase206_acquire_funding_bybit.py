#!/usr/bin/env python3
"""V98 Independent Phase206 — acquire realized Bybit linear funding, training-only.
Fallback source was frozen in PHASE206_DATA_SOURCE_AUDIT.md before inspecting values.
Never requests timestamps >= 2026-01-01 UTC. No imputation.
"""
from __future__ import annotations
import csv, hashlib, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SYMBOLS=["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT"]
START_MS=int(datetime(2022,3,1,tzinfo=timezone.utc).timestamp()*1000)
END_EXCLUSIVE_MS=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
API="https://api.bybit.com/v5/market/funding/history"
OUT=Path("research/v98_independent/data/phase206_funding_bybit")

def page(symbol,end_ms):
    q=urllib.parse.urlencode({"category":"linear","symbol":symbol,"endTime":end_ms,"limit":200})
    req=urllib.request.Request(API+"?"+q,headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0"})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                obj=json.loads(r.read().decode())
            if str(obj.get("retCode"))!="0": raise RuntimeError(f"Bybit retCode {obj.get('retCode')}: {obj.get('retMsg')}")
            return obj["result"]["list"]
        except Exception:
            if attempt==6: raise
            time.sleep(min(2**attempt,20))

def acquire(symbol):
    rows=[]; end_ms=END_EXCLUSIVE_MS-1
    while end_ms>=START_MS:
        xs=page(symbol,end_ms)
        if not xs: break
        oldest=None
        for x in xs:
            ts=int(x["fundingRateTimestamp"]); oldest=ts if oldest is None else min(oldest,ts)
            if START_MS<=ts<END_EXCLUSIVE_MS: rows.append((ts,str(x["fundingRate"])))
        if oldest is None or oldest<=START_MS: break
        nxt=oldest-1
        if nxt>=end_ms: raise RuntimeError(f"non-retreating cursor {symbol}")
        end_ms=nxt; time.sleep(.08)
    rows=sorted(set(rows))
    if not rows: raise RuntimeError(f"no funding rows {symbol}")
    ts=[x[0] for x in rows]
    if len(ts)!=len(set(ts)) or any(b<=a for a,b in zip(ts,ts[1:])): raise RuntimeError(f"timestamp integrity {symbol}")
    if max(ts)>=END_EXCLUSIVE_MS: raise RuntimeError(f"holdout contamination {symbol}")
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m={"phase":"206","namespace":"V98 Independent","source":"Bybit V5 linear realized funding history","retrieved_utc":datetime.now(timezone.utc).isoformat(),"requested_start_utc":"2022-03-01T00:00:00Z","exclusive_cutoff_utc":"2026-01-01T00:00:00Z","symbols":{},"integrity":{"holdout_opened":False,"imputation":False}}
    for s in SYMBOLS:
        rows=acquire(s); p=OUT/f"{s}_funding.csv"
        with p.open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["fundingTime_ms","fundingTime_utc","fundingRate"])
            for t,r in rows: w.writerow([t,datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),r])
        gaps=[{"from_ms":a[0],"to_ms":b[0],"hours":round((b[0]-a[0])/3600000,3)} for a,b in zip(rows,rows[1:]) if b[0]-a[0]>12*3600000]
        blob=p.read_bytes(); m["symbols"][s]={"rows":len(rows),"first_ms":rows[0][0],"last_ms":rows[-1][0],"sha256":hashlib.sha256(blob).hexdigest(),"gaps_gt_12h":gaps}
    (OUT/"manifest.json").write_text(json.dumps(m,sort_keys=True,indent=2)+"\n")
    print(json.dumps(m,sort_keys=True,indent=2))
if __name__=="__main__": main()

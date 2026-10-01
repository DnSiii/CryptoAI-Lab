#!/usr/bin/env python3
"""V98 Independent Phase206: acquire realized Binance USD-M funding history.
Training-only utility. Never requests timestamps >= 2026-01-01 UTC.
"""
from __future__ import annotations
import csv, hashlib, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SYMBOLS = ["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT"]
START_MS = int(datetime(2022,1,1,tzinfo=timezone.utc).timestamp()*1000)
END_EXCLUSIVE_MS = int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
API = "https://fapi.binance.com/fapi/v1/fundingRate"
OUT = Path("research/v98_independent/data/phase206_funding")


def get_page(symbol: str, start_ms: int):
    q = urllib.parse.urlencode({"symbol":symbol,"startTime":start_ms,"endTime":END_EXCLUSIVE_MS-1,"limit":1000})
    req = urllib.request.Request(API+"?"+q, headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0"})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if attempt == 6: raise
            time.sleep(min(2**attempt, 20))


def acquire(symbol: str):
    rows, cursor = [], START_MS
    while cursor < END_EXCLUSIVE_MS:
        page = get_page(symbol, cursor)
        if not page: break
        for x in page:
            ts = int(x["fundingTime"])
            if START_MS <= ts < END_EXCLUSIVE_MS:
                rows.append((ts, str(x["fundingRate"]), str(x.get("markPrice",""))))
        nxt = int(page[-1]["fundingTime"]) + 1
        if nxt <= cursor: raise RuntimeError(f"non-advancing API cursor {symbol}")
        cursor = nxt
        if len(page) < 1000: break
        time.sleep(0.08)
    rows.sort(key=lambda z:z[0])
    if not rows: raise RuntimeError(f"no funding rows {symbol}")
    ts = [r[0] for r in rows]
    if len(ts) != len(set(ts)): raise RuntimeError(f"duplicate funding timestamps {symbol}")
    if any(b <= a for a,b in zip(ts,ts[1:])): raise RuntimeError(f"non-monotonic funding {symbol}")
    if max(ts) >= END_EXCLUSIVE_MS: raise RuntimeError(f"holdout contamination {symbol}")
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"phase":"206","namespace":"V98 Independent","source":"Binance USD-M public fundingRate endpoint","retrieved_utc":datetime.now(timezone.utc).isoformat(),"requested_start_utc":"2022-01-01T00:00:00Z","exclusive_cutoff_utc":"2026-01-01T00:00:00Z","symbols":{},"integrity":{"holdout_opened":False}}
    for symbol in SYMBOLS:
        rows = acquire(symbol)
        p = OUT/f"{symbol}_funding.csv"
        with p.open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["fundingTime_ms","fundingTime_utc","fundingRate","markPrice"])
            for t,rate,mark in rows:
                w.writerow([t,datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),rate,mark])
        blob=p.read_bytes(); gaps=[]
        for (a,_,_),(b,_,_) in zip(rows,rows[1:]):
            # Funding cadence may change historically; flag >12h only, do not impute.
            if b-a > 12*3600*1000: gaps.append({"from_ms":a,"to_ms":b,"hours":round((b-a)/3600000,3)})
        manifest["symbols"][symbol]={"rows":len(rows),"first_ms":rows[0][0],"last_ms":rows[-1][0],"sha256":hashlib.sha256(blob).hexdigest(),"gaps_gt_12h":gaps}
    canonical=json.dumps(manifest,sort_keys=True,indent=2)+"\n"
    (OUT/"manifest.json").write_text(canonical,encoding="utf-8")
    print(canonical)

if __name__ == "__main__": main()

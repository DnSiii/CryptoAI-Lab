#!/usr/bin/env python3
"""V98-only third-party transparent Binance funding mirror; 2023-01 BTC source probe, no PnL."""
import argparse, hashlib, json, math, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
START=1672531200000
END=1675209599999
EXPECTED=93
HOST="https://api-dev.pipai.org"
PATHS=(
    "/fapi/v1/fundingRate?"+urllib.parse.urlencode(dict(symbol="BTCUSDT",startTime=START,endTime=END,limit=1000)),
    "/funding/rates/BTCUSDT/history?"+urllib.parse.urlencode(dict(start_time=START,end_time=END,limit=1000)),
)
def validate(raw):
    rows=json.loads(raw)
    if not isinstance(rows,list) or len(rows)!=EXPECTED:raise ValueError("V98_PRIMIT_NOT_93_JAN2023_EVENTS")
    times=[]
    for row in rows:
        if not isinstance(row,dict) or not set(("symbol","fundingTime","fundingRate","markPrice")).issubset(row):
            raise ValueError("V98_PRIMIT_NOT_NATIVE_EXACT_EVENT_SCHEMA")
        if row["symbol"]!="BTCUSDT":raise ValueError("V98_PRIMIT_WRONG_SYMBOL")
        ts=int(row["fundingTime"])
        if ts<START or ts>END:raise ValueError("V98_PRIMIT_OUT_OF_TRAINING_MONTH")
        rate=float(row["fundingRate"]);mark=float(row["markPrice"])
        if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:raise ValueError("V98_PRIMIT_INVALID_RATE_MARK")
        times.append(ts)
    if times!=sorted(set(times)):raise ValueError("V98_PRIMIT_UNSORTED_DUPLICATE")
    if any((b-a)!=8*3600000 for a,b in zip(times,times[1:])):
        raise ValueError("V98_PRIMIT_NON_8H_EVENT")
    return {"rows":len(rows),"first_ms":times[0],"last_ms":times[-1],
            "min_mark":min(float(x["markPrice"]) for x in rows),
            "max_mark":max(float(x["markPrice"]) for x in rows)}
def probe():
    attempts=[]
    for path in PATHS:
        url=HOST+path
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"V98-Independent-Source-Integrity/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=18) as response:
                status=response.status;raw=response.read(2_000_001)
                ctype=response.headers.get("Content-Type","")
            entry={"url":url,"status":status,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"content_type":ctype}
            if status!=200 or not raw or len(raw)>2_000_000:raise ValueError("V98_PRIMIT_EMPTY_NON200_OVERSIZED")
            try:details=validate(raw)
            except (ValueError,TypeError,KeyError,OverflowError) as e:raise ValueError("V98_PRIMIT_SCHEMA_"+str(e))
            entry.update(details);attempts.append(entry)
            return {"decision":"PASS_THIRD_PARTY_TRANSPORT_SAMPLE_ONLY_NOT_OFFICIAL_PROVENANCE",
                    "attempts":attempts,"source_identity":"Primit transparent Binance proxy, unverified upstream",
                    "exact_native_full_history_attested":False,"pnl_computed":False,
                    "2025_or_future_data_accessed":False,"live_authorized":False},raw
        except Exception as e:
            attempts.append({"url":url,"failure_type":type(e).__name__,"failure":str(e)[:240]})
            print("V98_PRIMIT_PROBE_FAILED",attempts[-1],flush=True)
    return {"decision":"BLOCKED_NO_AUTHENTICATED_EVENT_MARK_SOURCE",
            "attempts":attempts,"source_identity":"Primit proxy, no usable response",
            "exact_native_full_history_attested":False,"pnl_computed":False,
            "2025_or_future_data_accessed":False,"live_authorized":False},None
def synthetic():
    rows=[{"symbol":"BTCUSDT","fundingTime":START+i*28800000,
           "fundingRate":"0.00010000","markPrice":"20000.0"} for i in range(EXPECTED)]
    assert validate(json.dumps(rows).encode())["rows"]==93
    for key,value in [("markPrice","-1"),("fundingRate","nan"),("symbol","ETHUSDT")]:
        bad=[dict(r) for r in rows];bad[0][key]=value
        try:validate(json.dumps(bad).encode())
        except ValueError:pass
        else:raise AssertionError("V98_PRIMIT_FAIL_OPEN_"+key)
    bad=[dict(r) for r in rows];bad[1]["fundingTime"]=bad[0]["fundingTime"]
    try:validate(json.dumps(bad).encode())
    except ValueError:pass
    else:raise AssertionError("V98_PRIMIT_DUPLICATE_ACCEPTED")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True);parser.add_argument("--raw-output",required=True)
    args=parser.parse_args()
    synthetic()
    receipt,raw=probe()
    Path(args.output).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    if raw is not None:Path(args.raw_output).write_bytes(raw)
    print("V98_PRIMIT_SOURCE_DECISION",receipt["decision"],flush=True)
    raise SystemExit(0 if raw is not None else 2)

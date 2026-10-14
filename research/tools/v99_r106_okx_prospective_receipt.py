"""OKX first-party prospective as-of 1H swaps: independent live receipt source.

Not Binance, not a cross-venue price substitute without re-preregistration.
No orders, returns, model tuning, funding, fees or paper publication. Capture
raw HTTP bodies, observed request/receive UTC and OKX public server clock.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

HOST="https://www.okx.com"
TIME="/api/v5/public/time"
CANDLES="/api/v5/market/candles"
INSTS=("BTC-USDT-SWAP","ETH-USDT-SWAP","SOL-USDT-SWAP","XRP-USDT-SWAP","DOGE-USDT-SWAP")
MAX_BODY=160_000
MAX_SKEW_MS=60_000
MAX_DELAY_HOURS=4
UTC=timezone.utc

def now():
    return datetime.now(UTC)

def iso(t):
    return t.astimezone(UTC).isoformat()

def as_utc(t):
    if not isinstance(t,str):raise ValueError("UTC timestamp required")
    x=datetime.fromisoformat(t.replace("Z","+00:00"))
    if x.tzinfo is None or x.utcoffset()!=timedelta(0):raise ValueError("explicit UTC required")
    return x.astimezone(UTC)

def safe_eligibility(t):
    observed=as_utc(t)
    return iso(observed.replace(minute=0,second=0,microsecond=0)+timedelta(hours=2))

def candle_path(inst):
    if inst not in INSTS:raise ValueError("not in preregistered OKX swaps")
    return CANDLES+"?"+urlencode({"instId":inst,"bar":"1H","limit":"6"})

def fetch(path):
    if path!=TIME and path not in {candle_path(inst) for inst in INSTS}:
        raise ValueError("not an approved first-party public endpoint")
    start=now()
    url=HOST+path
    req=Request(url,headers={"User-Agent":"CryptoAI-Lab-R106-OKX-asof/1.0","Accept":"application/json"})
    with urlopen(req,timeout=30) as response:
        if response.status!=200:raise ValueError("non-200 OKX source response")
        body=response.read(MAX_BODY+1)
        headers={k.lower():response.headers.get(k) for k in ("Date","Content-Type")}
    end=now()
    if not body or len(body)>MAX_BODY:raise ValueError("OKX response empty/oversized")
    if (end-start).total_seconds()>45:raise ValueError("OKX request too slow")
    return {"url":url,"requested_utc":iso(start),"received_utc":iso(end),
            "raw":body,"sha256":hashlib.sha256(body).hexdigest(),
            "byte_count":len(body),"http":headers}

def parse(reply):
    def unique(pairs):
        obj={}
        for k,v in pairs:
            if k in obj:raise ValueError("duplicate first-party OKX JSON property")
            obj[k]=v
        return obj
    def constant(x):raise ValueError("nonfinite OKX numeric constant")
    value=json.loads(reply["raw"],parse_constant=constant,object_pairs_hook=unique)
    if not isinstance(value,dict) or value.get("code")!="0" or not isinstance(value.get("data"),list):
        raise ValueError("OKX returned failure or malformed data")
    return value["data"]

def get_clock(reply):
    data=parse(reply)
    if len(data)!=1 or not isinstance(data[0],dict):
        raise ValueError("OKX server timestamp missing")
    millis=data[0].get("ts")
    if not isinstance(millis,str) or not millis.isdecimal():
        raise ValueError("noninteger OKX server clock")
    value=int(millis)
    if abs(value-int(as_utc(reply["received_utc"]).timestamp()*1000))>MAX_SKEW_MS:
        raise ValueError("OKX reported server time not near observed UTC")
    return value

def numeric(x):
    try:
        d=Decimal(str(x))
        if not d.is_finite():raise ValueError("nonfinite OKX quantity")
        return d
    except (InvalidOperation,TypeError) as exc:
        raise ValueError("invalid OKX OHLCV decimal") from exc

def validate_candles(reply,inst):
    data=parse(reply)
    if not (4<=len(data)<=6):
        raise ValueError("unexpected number of OKX 1H candles")
    observed=as_utc(reply["received_utc"])
    all_times=set();complete=[];unconfirmed=0
    for row in data:
        if not isinstance(row,list) or len(row)<9:
            raise ValueError("malformed OKX 1H row")
        if not isinstance(row[0],str) or not row[0].isdecimal():
            raise ValueError("invalid OKX native start epoch")
        ts=int(row[0])
        if ts%3_600_000:
            raise ValueError("OKX candle starts off UTC hour")
        if ts in all_times:
            raise ValueError("duplicate OKX candle time")
        all_times.add(ts)
        bar=datetime.fromtimestamp(ts/1000,UTC)
        if bar>observed:
            raise ValueError("future OKX candle")
        o,h,l,c,vol,quote=(numeric(row[i]) for i in (1,2,3,4,5,7))
        if l<=0 or l>min(o,c) or h<max(o,c) or vol<0 or quote<0:
            raise ValueError("malformed OKX native price-volume semantics")
        if row[8]=="1":
            if bar+timedelta(hours=1)>observed:
                raise ValueError("OKX confirmed not yet closed bar")
            complete.append(bar)
        elif row[8]=="0": unconfirmed+=1
        else: raise ValueError("unknown OKX confirm state")
    times=sorted(all_times)
    if any(b-a!=3600000 for a,b in zip(times,times[1:])):
        raise ValueError("gapped or reordered OKX 1H source")
    if len(complete)<3:
        raise ValueError("insufficient confirmed OKX 1H candles")
    last=max(complete)
    if observed-last>timedelta(hours=MAX_DELAY_HOURS):
        raise ValueError("stale OKX last confirmed source bar")
    return {"instrument":inst,"received_utc":reply["received_utc"],
            "latest_confirmed_open_utc":iso(last),
            "latest_confirmed_close_utc":iso(last+timedelta(hours=1)),
            "confirmed_candles":len(complete),"unconfirmed_candles":unconfirmed,
            "first_observed_now":True,
            "min_safe_tminus1_decision_utc":safe_eligibility(reply["received_utc"])}

def corroborate(before,after,requests):
    first=get_clock(before)
    last=get_clock(after)
    if last<first:raise ValueError("OKX server clock regressed")
    spans=[(as_utc(x["requested_utc"]),as_utc(x["received_utc"])) for x in (before,*requests,after)]
    if any(b<a for a,b in spans):
        raise ValueError("negative request duration")
    if any(c[0]<p[0] or c[1]<p[1] for p,c in zip(spans,spans[1:])):
        raise ValueError("nonmonotonic OKX request order")
    if spans[-1][1]-spans[0][0]>timedelta(minutes=2):
        raise ValueError("OKX capture elapsed >2min")
    return {"before_ms":first,"after_ms":last}

def acquire():
    time_before=fetch(TIME)
    replies={}
    summaries={}
    for inst in INSTS:
        reply=fetch(candle_path(inst))
        replies[inst]=reply
        summaries[inst]=validate_candles(reply,inst)
    time_after=fetch(TIME)
    clock=corroborate(time_before,time_after,list(replies.values()))
    last_received=max(as_utc(x["received_utc"]) for x in (time_before,time_after,*replies.values()))
    manifest={
        "schema":"V99_R106_OKX_PROSPECTIVE_ASOF_V1",
        "status":"FIRST_PARTY_OKX_HTTP_OBSERVED_DATA_ONLY",
        "mode":"DATA_ONLY",
        "provider":"OKX",
        "venue":"OKX_USDT_PERPETUALS_NOT_BINANCE",
        "original_r106_binance_fee_and_funding_model_transfer_authorized":False,
        "first_party_observation_only_not_venue_signed":True,
        "server_clock_corrob":clock,
        "first_received_utc":time_before["received_utc"],
        "last_received_utc":iso(last_received),
        "earliest_candidate_decision_utc":safe_eligibility(iso(last_received)),
        "instruments":{k:{**summaries[k], "source_raw_sha256":v["sha256"],
                          "source_http_url":v["url"],
                          "raw_byte_count":v["byte_count"]}
                       for k,v in replies.items()},
        "clock_receipts":[{"received_utc":x["received_utc"],"sha256":x["sha256"]} for x in (time_before,time_after)],
        "symbol_listing_first_seen_historically_authenticated":False,
        "real_orders_enabled":False,
        "paper_publication_authorized":False,
        "promotion_authorized":False,
        "holdout_accessed":False,
        "economic_trials":0,
    }
    return manifest,{"clock_before":time_before,
                     **{k:replies[k] for k in INSTS},"clock_after":time_after}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    manifest,originals=acquire()
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    for name,reply in originals.items():
        (args.out/(name+".raw.json")).write_bytes(reply["raw"])
    print(json.dumps({"status":manifest["status"],"instruments":len(manifest["instruments"]),
                      "earliest_candidate_decision_utc":manifest["earliest_candidate_decision_utc"],
                      "paper_publication_authorized":False},sort_keys=True))

if __name__=="__main__":
    main()

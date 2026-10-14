"""First-party OKX native USDT swap contract terms and funding notices.

Prospective DATA_ONLY evidence, not a tradable fee/funding backtest.
An observed projected fundingRate is NEVER classified as a settled cashflow.
No real orders, no R106 Binance cross-venue model substitution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

from research.tools import v99_r106_okx_prospective_receipt as okx

META_PATH="/api/v5/public/instruments"
FUND_PATH="/api/v5/public/funding-rate"
HOST=okx.HOST
INSTS=okx.INSTS
LIMIT=160_000

def path_meta(inst):
    if inst not in INSTS: raise ValueError("instrument not preregistered")
    return META_PATH+"?"+urlencode({"instType":"SWAP","instId":inst})

def path_fund(inst):
    if inst not in INSTS: raise ValueError("instrument not preregistered")
    return FUND_PATH+"?"+urlencode({"instId":inst})

def fetch(path):
    approved={okx.TIME}|{path_meta(x) for x in INSTS}|{path_fund(x) for x in INSTS}
    if path not in approved:
        raise ValueError("unapproved native-terms endpoint")
    if path==okx.TIME:
        return okx.fetch(path)
    start=okx.now()
    url=HOST+path
    request=Request(url,headers={"User-Agent":"CryptoAI-Lab-R106-OKX-native-terms/1.0",
                                 "Accept":"application/json"})
    with urlopen(request,timeout=30) as response:
        if response.status!=200 or response.geturl()!=url:
            raise ValueError("wrong provider or redirected terms response")
        raw=response.read(LIMIT+1)
    end=okx.now()
    if not raw or len(raw)>LIMIT or (end-start).total_seconds()>30:
        raise ValueError("invalid native-terms request")
    return {"url":url,"requested_utc":okx.iso(start),"received_utc":okx.iso(end),
            "raw":raw,"sha256":hashlib.sha256(raw).hexdigest(),"byte_count":len(raw)}

def decimal(value):
    try:
        if isinstance(value,bool) or value is None: raise ValueError("invalid native decimal")
        x=Decimal(str(value))
        if not x.is_finite():raise ValueError("nonfinite native field")
        return x
    except (InvalidOperation,TypeError) as exc:
        raise ValueError("malformed native contract/funding field") from exc

def verify_contract(reply,inst):
    rows=okx.parse(reply)
    if len(rows)!=1 or not isinstance(rows[0],dict):
        raise ValueError("exactly one native contract expected")
    row=rows[0]
    if (row.get("instId")!=inst or row.get("ctType")!="linear" or
        row.get("settleCcy")!="USDT" or row.get("state")!="live"):
        raise ValueError("live linear USDT swap contract proof absent")
    amounts={}
    for key in ("ctVal","lotSz","tickSz","minSz"):
        x=decimal(row.get(key))
        if x<=0:raise ValueError("nonpositive native contract term "+key)
        amounts[key]=str(x)
    if not isinstance(row.get("ctValCcy"),str) or not row["ctValCcy"]:
        raise ValueError("missing native contract multiplier currency")
    return {"instId":inst,"ctVal":amounts["ctVal"],
            "ctValCcy":row["ctValCcy"],
            "lotSz":amounts["lotSz"],
            "tickSz":amounts["tickSz"],
            "minSz":amounts["minSz"],
            "state":"live","ctType":"linear","settleCcy":"USDT"}

def verify_current_funding(reply,inst):
    rows=okx.parse(reply)
    if len(rows)!=1 or not isinstance(rows[0],dict):
        raise ValueError("exactly one native funding notice expected")
    row=rows[0]
    if row.get("instId")!=inst:
        raise ValueError("funding instrument mismatch")
    rate=decimal(row.get("fundingRate"))
    if abs(rate)>Decimal("1"):
        raise ValueError("funding rate exceeds plausible unit range")
    stamp=row.get("fundingTime")
    if not isinstance(stamp,str) or not stamp.isdecimal():
        raise ValueError("funding time absent or not epoch milliseconds")
    funding=datetime.fromtimestamp(int(stamp)/1000,timezone.utc)
    observed=okx.as_utc(reply["received_utc"])
    if abs((funding-observed).total_seconds())>48*3600:
        raise ValueError("funding notice outside 48-hour observation window")
    nexttime=row.get("nextFundingTime")
    if nexttime not in (None,""):
        if not isinstance(nexttime,str) or not nexttime.isdecimal():
            raise ValueError("invalid next funding notice")
        if int(nexttime)<=int(stamp):
            raise ValueError("funding interval not increasing")
    return {"instId":inst,"observed_rate_not_settled":str(rate),
            "notice_funding_time_utc":okx.iso(funding),
            "received_utc":reply["received_utc"],
            "nextFundingTime":nexttime or None,
            "settled_cashflow_authenticated":False}

def acquire():
    before=fetch(okx.TIME)
    originals={}
    terms={}
    for inst in INSTS:
        m=fetch(path_meta(inst))
        f=fetch(path_fund(inst))
        originals["metadata_"+inst]=m
        originals["funding_"+inst]=f
        terms[inst]={
            "contract":verify_contract(m,inst),
            "funding_notice":verify_current_funding(f,inst),
            "contract_raw_sha256":m["sha256"],
            "funding_raw_sha256":f["sha256"],
            "contract_received_utc":m["received_utc"],
            "funding_received_utc":f["received_utc"],
        }
    after=fetch(okx.TIME)
    okx.corroborate(before,after,list(originals.values()))
    last=max(okx.as_utc(r["received_utc"]) for r in (before,after,*originals.values()))
    manifest={
      "schema":"V99_R106_OKX_NATIVE_TERMS_ASOF_V1","mode":"DATA_ONLY",
      "status":"OKX_NATIVE_CONTRACT_AND_FUNDING_OBSERVED",
      "provider":"OKX","contracts":terms,
      "first_party_clock_receipts":[before["sha256"],after["sha256"]],
      "acquisition_last_utc":okx.iso(last),
      "earliest_safe_decision_utc":okx.safe_eligibility(okx.iso(last)),
      "fee_schedule_independently_proven":False,
      "funding_cashflows_settled_and_pit_authenticated":False,
      "binance_r106_parameters_crossvenue_transfer_authorized":False,
      "historical_first_seen_authenticated":False,
      "real_orders_enabled":False,
      "paper_publication_authorized":False,
      "promotion_authorized":False,
      "holdout_accessed":False,
      "economic_trials":0,
    }
    return manifest,{"clock_before":before,**originals,"clock_after":after}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    manifest,raw=acquire()
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    for name,entry in raw.items():
        (args.out/(name+".raw.json")).write_bytes(entry["raw"])
    print(json.dumps({"status":manifest["status"],"instruments":len(manifest["contracts"]),
                      "paper_publication_authorized":False,"fee_schedule_proven":False},sort_keys=True))

if __name__=="__main__":
    main()

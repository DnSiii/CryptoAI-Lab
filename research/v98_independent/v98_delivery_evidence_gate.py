#!/usr/bin/env python3
"""V98 Independent: fail-closed native settlement/cost evidence preflight.

Byte custody and event equality are NOT proof of exchange authenticity,
executable profit, seven-slot validation, or trading authorization.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=int(dt.datetime(2022,12,1,tzinfo=dt.timezone.utc).timestamp()*1000)
END=int(dt.datetime(2026,1,1,tzinfo=dt.timezone.utc).timestamp()*1000)
EXPECTED_COUNT=13524
PINNED_EXPECTED_FUNDING_SHA256="3a7e5cc35152663ecfd08edb991c9f5cf1db845877cfb0d0b802d0682f55e7c1"
EIGHT_HOURS_MS=8*3600*1000
MAX_SETTLEMENT_OFFSET_MS=60000
FIELDS=("asset","funding_time_ms","funding_rate")

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fail(code):
    raise ValueError("V98_EVIDENCE_"+code)

def positive_number(value,name,*,allow_zero=False):
    if type(value) is bool:fail(name+"_INVALID")
    try:v=float(value)
    except (TypeError,ValueError):fail(name+"_NOT_NUMERIC")
    if not math.isfinite(v) or (v<0 if allow_zero else v<=0):fail(name+"_INVALID")
    return v

def timestamp_ms(v):
    try:n=int(v)
    except (ValueError,TypeError):fail("BAD_TIMESTAMP")
    if not START<=n<END:fail("OUTSIDE_EXPOSED_TRAINING")
    return n

def utc_timestamp(value):
    if not isinstance(value,str) or not value.endswith("Z"):fail("UTC_ATTESTATION_REQUIRED")
    try:x=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:fail("UTC_ATTESTATION_INVALID")
    if x.utcoffset()!=dt.timedelta(0):fail("UTC_ATTESTATION_OFFSET")
    return x

def expected_events(path,declared_sha):
    if declared_sha!=PINNED_EXPECTED_FUNDING_SHA256:fail("UNPINNED_EXPECTED_SOURCE")
    if sha256(path)!=declared_sha:fail("NATIVE_FUNDING_EXPECTED_SHA")
    with Path(path).open(newline="") as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ())!=FIELDS:fail("NATIVE_FUNDING_SCHEMA")
        rows=list(reader)
    if len(rows)!=EXPECTED_COUNT:fail("NATIVE_FUNDING_EXPECTED_COUNT")
    events={};counts={a:0 for a in ASSETS}
    for row in rows:
        a=row["asset"]
        if a not in ASSETS:fail("NATIVE_FUNDING_ASSET")
        ts=timestamp_ms(row["funding_time_ms"])
        try:rate=float(row["funding_rate"])
        except (TypeError,ValueError):fail("NATIVE_FUNDING_RATE")
        if not math.isfinite(rate) or abs(rate)>1:fail("NATIVE_FUNDING_RATE")
        key=(a,ts)
        if key in events:fail("NATIVE_FUNDING_DUPLICATE")
        events[key]=rate;counts[a]+=1
    if set(counts.values())!={EXPECTED_COUNT//len(ASSETS)}:fail("NATIVE_FUNDING_ASSET_COUNTS")
    return events

def unique_json_object(pairs):
    out={}
    for key,value in pairs:
        if key in out:fail("DUPLICATE_JSON_KEY")
        out[key]=value
    return out

def read_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=unique_json_object)

def exact_integer(value,code):
    if type(value) is not int:fail(code)
    return value

def native_mark_pages(manifest,root,expected):
    pages=manifest.get("pages")
    if not isinstance(pages,list) or not pages:fail("NATIVE_PAGES_MISSING")
    seen={}
    for page in pages:
        if not isinstance(page,dict):fail("NATIVE_PAGE_METADATA")
        if page.get("source_type")!="official_binance_usdm_fundingRate":fail("NATIVE_ORIGIN_NOT_OFFICIAL_API")
        url=urlsplit(page.get("url",""))
        if (url.scheme!="https" or url.hostname not in ("fapi.binance.com","fapi1.binance.com")
            or url.port not in (None,443) or url.username or url.password or url.fragment
            or url.path!="/fapi/v1/fundingRate"):
            fail("NATIVE_ORIGIN_URL")
        params=parse_qs(url.query,keep_blank_values=True)
        if set(params)!={"symbol","startTime","endTime","limit"} or any(len(v)!=1 for v in params.values()):
            fail("NATIVE_QUERY_CONTRACT")
        asset=params["symbol"][0]
        if asset not in ASSETS or params["limit"][0]!="1000":fail("NATIVE_QUERY_CONTRACT")
        try:
            lo=int(params["startTime"][0]);hi=int(params["endTime"][0])
        except ValueError:fail("NATIVE_QUERY_TIMESTAMP")
        if (str(lo)!=params["startTime"][0] or str(hi)!=params["endTime"][0]
            or lo<START or hi>=END or lo>hi):fail("NATIVE_QUERY_OUTSIDE_TRAINING")
        if type(page.get("http_status")) is not int or page["http_status"]!=200:
            fail("NATIVE_HTTP_NOT_200")
        headers=page.get("response_headers")
        if not isinstance(headers,dict) or sum(k.lower()=="date" for k in headers)!=1:
            fail("NATIVE_HTTP_DATE_HEADER")
        capture=utc_timestamp(page.get("retrieved_at_utc"))
        raw_date=next(v for k,v in headers.items() if k.lower()=="date")
        try:server=parsedate_to_datetime(raw_date)
        except (ValueError,TypeError,IndexError):fail("NATIVE_HTTP_DATE_INVALID")
        if server.tzinfo is None or server.utcoffset()!=dt.timedelta(0):
            fail("NATIVE_HTTP_DATE_INVALID")
        if abs((capture-server).total_seconds())>600:fail("NATIVE_HTTP_DATE_DRIFT")
        name=page.get("file","")
        if (not isinstance(name,str) or not name.endswith(".json")
            or Path(name).name!=name or name in (".","..")):
            fail("NATIVE_PAGE_PATH")
        p=Path(root)/name
        if p.is_symlink() or not p.is_file() or sha256(p)!=page.get("sha256"):
            fail("NATIVE_PAGE_SHA")
        try:records=read_manifest(p)
        except (ValueError,UnicodeError):fail("NATIVE_PAGE_JSON")
        if not isinstance(records,list) or not records or len(records)>1000:fail("NATIVE_PAGE_SHAPE")
        prev=-1
        for row in records:
            if not isinstance(row,dict) or row.get("symbol")!=asset:fail("NATIVE_ROW_SYMBOL")
            ts=timestamp_ms(exact_integer(row.get("fundingTime"),"NATIVE_TIMESTAMP_TYPE"))
            if not lo<=ts<=hi:fail("NATIVE_ROW_OUTSIDE_REQUEST")
            if ts<=prev:fail("NATIVE_PAGE_ORDER")
            prev=ts
            slot=START+((ts-START)//EIGHT_HOURS_MS)*EIGHT_HOURS_MS
            if ts-slot>MAX_SETTLEMENT_OFFSET_MS:fail("NATIVE_SETTLEMENT_OFFSET_GT_60S")
            key=(asset,slot)
            if key in seen or key not in expected:fail("NATIVE_DUPLICATE_OR_UNKNOWN_EVENT")
            try:rate=float(row["fundingRate"])
            except (TypeError,ValueError):fail("NATIVE_ROW_RATE")
            if not math.isfinite(rate) or abs(rate-expected[key])>1e-10:fail("NATIVE_RATE_CONFLICT")
            seen[key]=positive_number(row.get("markPrice"),"NATIVE_MARK")
    if set(seen)!=set(expected):fail("NATIVE_INCOMPLETE_COVERAGE")
    return {"event_count":len(seen),"assets":list(ASSETS),"source_pages":len(pages),
            "native_marks_reconciled":True,"exchange_origin_independently_authenticated":False}

def cost_evidence(manifest,root):
    bands=manifest.get("fee_periods")
    if not isinstance(bands,list) or not bands:fail("ACCOUNT_FEE_PERIODS_MISSING")
    for band in bands:
        if not isinstance(band,dict):fail("ACCOUNT_FEE_PERIOD_SHAPE")
        exact_integer(band.get("start_ms"),"ACCOUNT_FEE_PERIOD_TIMESTAMP_TYPE")
        exact_integer(band.get("end_ms"),"ACCOUNT_FEE_PERIOD_TIMESTAMP_TYPE")
    bands=sorted(bands,key=lambda x:x["start_ms"])
    cursor=START
    for band in bands:
        start,end=band["start_ms"],band["end_ms"]
        if start!=cursor or not start<end<=END:fail("ACCOUNT_FEE_PERIOD_GAP_OR_OVERLAP")
        for k in ("spot_taker_bps","perp_taker_bps","spot_spread_bps","perp_spread_bps",
                  "spot_impact_bps","perp_impact_bps"):
            positive_number(band.get(k),k,allow_zero=True)
        cursor=end
    if cursor!=END:fail("ACCOUNT_FEE_PERIOD_INCOMPLETE")
    for name in ("account_fee_schedule","historical_bid_ask_depth","collateral_liquidation_policy"):
        proof=manifest.get(name)
        if not isinstance(proof,dict):fail(name.upper()+"_MISSING")
        fname=proof.get("file","")
        if (not isinstance(fname,str) or not fname or fname in (".","..")
            or Path(fname).name!=fname):fail(name.upper()+"_PATH")
        p=Path(root)/fname
        if p.is_symlink() or not p.is_file() or sha256(p)!=proof.get("sha256"):
            fail(name.upper()+"_SHA")
        if not proof.get("issuer") or not proof.get("applicable_account_tier"):
            fail(name.upper()+"_IDENTITY")
    return {"fee_periods":len(bands),"evidence_files":3,
            "actual_fills_or_orderbook_replay_verified":False,
            "independent_account_provenance_authenticated":False}

def evaluate(root,expected_csv,expected_sha):
    result={"decision":"HOLD_MISSING_EXTERNAL_EVIDENCE","engine":"V98 Independent",
            "training_only":True,"2026_training_accessed":False,
            "holdout_accessed":False,"benchmarks_accessed":False,
            "paper_or_live_authorized":False}
    root=Path(root)
    if not (root/"native_pages_manifest.json").is_file():
        result["blocker"]="official fundingRate raw pages + authenticated custody absent"
        return result
    if not (root/"account_costs_manifest.json").is_file():
        result["blocker"]="historical account fee, depth and liquidation evidence absent"
        return result
    try:
        expected=expected_events(expected_csv,expected_sha)
        native=native_mark_pages(read_manifest(root/"native_pages_manifest.json"),root,expected)
        costs=cost_evidence(read_manifest(root/"account_costs_manifest.json"),root)
    except (OSError,KeyError,TypeError,ValueError) as exc:
        result["blocker"]=str(exc)
        return result
    result.update({"decision":"PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION",
                   "native":native,"costs":costs,
                   "blocker":"manual independent exchange/account custody authentication and physical fill validation"})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence-dir",type=Path,required=True)
    p.add_argument("--expected-funding-csv",type=Path,required=True)
    p.add_argument("--expected-funding-sha256",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    out=evaluate(a.evidence_dir,a.expected_funding_csv,a.expected_funding_sha256)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["decision"].startswith("HOLD"):raise SystemExit(2)

if __name__=="__main__":main()

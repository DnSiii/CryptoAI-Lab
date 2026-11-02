#!/usr/bin/env python3
"""V98-only exact USD-M funding settlement mark ingestion; never infer provenance from proxies.

Consumes authorized RAW Binance /fapi/v1/fundingRate JSON captures and custody manifest.
No live network, no account credentials, no market PnL. Schema/hash/rate reconciliation
is necessary but not sufficient for independent exchange-origin authentication.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,tempfile
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import ASSETS,HOURS,source_gate

START_MS=1669852800000
HOUR_MS=3600000
EVENTS_PER_ASSET=HOURS//8
RATE_TOL=Decimal("0.00000000005")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def decimal_field(value,field):
    if not isinstance(value,(str,int,float)) or isinstance(value,bool):
        raise ValueError("V98_MARK_BAD_"+field)
    try:
        d=Decimal(str(value))
    except InvalidOperation:
        raise ValueError("V98_MARK_BAD_"+field)
    if not d.is_finite():
        raise ValueError("V98_MARK_NONFINITE_"+field)
    return d

def verify_manifest_entry(entry,root):
    required=("symbol","file","sha256","source_url","retrieved_at_utc","http_status","response_headers")
    if any(k not in entry for k in required):
        raise ValueError("V98_MARK_MISSING_CUSTODY_FIELD")
    symbol=entry["symbol"]
    if symbol not in ASSETS:
        raise ValueError("V98_MARK_NON_CLEAN4_SYMBOL")
    path=Path(entry["file"])
    if path.is_absolute() or ".." in path.parts or path.suffix!=".json":
        raise ValueError("V98_MARK_UNSAFE_CAPTURE_PATH")
    full=(root/path).resolve()
    if not full.is_relative_to(root.resolve()) or not full.is_file():
        raise ValueError("V98_MARK_CAPTURE_NOT_FOUND")
    raw=full.read_bytes()
    if not re.fullmatch("[0-9a-f]{64}",str(entry["sha256"])) or digest(raw)!=entry["sha256"]:
        raise ValueError("V98_MARK_CAPTURE_SHA_MISMATCH")
    url=urlsplit(entry["source_url"])
    if (url.scheme!="https" or url.hostname!="fapi.binance.com"
        or url.path!="/fapi/v1/fundingRate" or url.username or url.password or url.fragment):
        raise ValueError("V98_MARK_UNOFFICIAL_CAPTURE_URL")
    query=parse_qs(url.query)
    if set(query)-{"symbol","startTime","endTime","limit"} or query.get("symbol")!=[symbol]:
        raise ValueError("V98_MARK_CAPTURE_QUERY")
    if int(entry["http_status"])!=200:
        raise ValueError("V98_MARK_CAPTURE_NOT_HTTP_200")
    if not isinstance(entry["response_headers"],dict) or not entry["response_headers"]:
        raise ValueError("V98_MARK_MISSING_RESPONSE_HEADERS")
    try:
        when=datetime.fromisoformat(entry["retrieved_at_utc"].replace("Z","+00:00"))
    except (ValueError,AttributeError):
        raise ValueError("V98_MARK_BAD_RETRIEVAL_TIME")
    if when.tzinfo is None or when.utcoffset().total_seconds()!=0 or when>datetime.now(timezone.utc):
        raise ValueError("V98_MARK_BAD_RETRIEVAL_TIME")
    try:
        records=json.loads(raw)
    except (UnicodeDecodeError,json.JSONDecodeError):
        raise ValueError("V98_MARK_INVALID_RAW_JSON")
    if not isinstance(records,list):
        raise ValueError("V98_MARK_RESPONSE_NOT_LIST")
    return symbol,records

def reconcile(captures,root,expected):
    """expected maps (symbol, fundingTime) -> (native_rate, lower, upper)."""
    seen={}; outside=[]
    for entry in captures:
        symbol,records=verify_manifest_entry(entry,root)
        for record in records:
            if not isinstance(record,dict) or record.get("symbol")!=symbol:
                raise ValueError("V98_MARK_RECORD_SYMBOL")
            try:
                ts=int(record["fundingTime"])
            except (ValueError,TypeError,KeyError):
                raise ValueError("V98_MARK_BAD_EVENT_TIME")
            key=(symbol,ts)
            if key not in expected:
                raise ValueError("V98_MARK_UNEXPECTED_EVENT")
            if key in seen:
                raise ValueError("V98_MARK_DUPLICATE_EVENT")
            rate=decimal_field(record.get("fundingRate"),"RATE")
            mark=decimal_field(record.get("markPrice"),"PRICE")
            if mark<=0:
                raise ValueError("V98_MARK_NONPOSITIVE_PRICE")
            exp_rate,lo,hi=expected[key]
            if abs(rate-Decimal(str(exp_rate)))>RATE_TOL:
                raise ValueError("V98_MARK_RATE_CONFLICT_"+symbol+"_"+str(ts))
            if not float(lo)<=float(mark)<=float(hi):
                outside.append(key)
            seen[key]=(rate,mark)
    missing=set(expected)-set(seen)
    if missing:
        raise ValueError("V98_MARK_MISSING_EVENTS_"+str(len(missing)))
    if outside:
        raise ValueError("V98_MARK_OUTSIDE_PREEXISTING_ENVELOPE_"+str(len(outside)))
    return [(symbol,ts,str(seen[(symbol,ts)][0]),str(seen[(symbol,ts)][1]))
            for symbol,ts in sorted(seen)]

def expected_from_clean4(d):
    source_gate(d)
    expected={}
    for j,symbol in enumerate(ASSETS):
        for t in range(0,HOURS,8):
            if not d["event"][t,j]:
                raise ValueError("V98_MARK_PINNED_EVENT_CLOCK")
            expected[(symbol,START_MS+t*HOUR_MS)]=(
                d["rate"][t,j],d["mark_lower"][t,j],d["mark_upper"][t,j])
    if len(expected)!=13524:
        raise ValueError("V98_MARK_EXPECTED_COUNT")
    return expected

def run(raw_root,d,out_dir):
    root=Path(raw_root)
    manifest=json.loads((root/"custody_manifest.json").read_text())
    if not isinstance(manifest,dict) or not isinstance(manifest.get("captures"),list):
        raise ValueError("V98_MARK_BAD_MANIFEST")
    expected=expected_from_clean4(d)
    rows=reconcile(manifest["captures"],root,expected)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    csv_path=out/"v98_exact_funding_marks_source_only.csv"
    with csv_path.open("w",newline="") as f:
        writer=csv.writer(f,lineterminator="\n")
        writer.writerow(("symbol","fundingTime","fundingRate","markPrice"))
        writer.writerows(rows)
    receipt={"decision":"PASS_V98_EXACT_MARK_SCHEMA_AND_HASH_RECONCILIATION_ONLY_NOT_INDEPENDENT_ORIGIN_ATTESTATION",
             "event_count":len(rows),"assets":list(ASSETS),
             "captures":len(manifest["captures"]),
             "canonical_csv_sha256":digest(csv_path.read_bytes()),
             "transport_origin_independently_authenticated":False,
             "historical_account_costs_authenticated":False,
             "collateral_liquidation_rules_authenticated":False,
             "2026_accessed":False,"holdout_accessed":False,
             "paper_live_authorized":False}
    (out/"v98_exact_mark_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt

def self_test():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        records=[{"symbol":"BTCUSDT","fundingTime":START_MS,"fundingRate":"0.00010000","markPrice":"100.00"},
                 {"symbol":"BTCUSDT","fundingTime":START_MS+8*HOUR_MS,"fundingRate":"-0.00020000","markPrice":"101.00"}]
        raw=json.dumps(records).encode()
        (root/"capture.json").write_bytes(raw)
        entry={"symbol":"BTCUSDT","file":"capture.json","sha256":digest(raw),
               "source_url":"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1000",
               "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
               "http_status":200,"response_headers":{"Content-Type":"application/json"}}
        expected={("BTCUSDT",START_MS):(.0001,99.,101.),
                  ("BTCUSDT",START_MS+8*HOUR_MS):(-.0002,100.,102.)}
        assert len(reconcile([entry],root,expected))==2
        checks=0
        for bad in ("hash","duplicate","rate","missing","url","envelope"):
            changed=dict(entry)
            exp=dict(expected)
            if bad=="hash":changed["sha256"]="0"*64
            elif bad=="duplicate":
                changed["sha256"]=digest(raw)
                items=records+records[:1]
                payload=json.dumps(items).encode()
                (root/"capture.json").write_bytes(payload)
                changed["sha256"]=digest(payload)
            elif bad=="rate":exp[("BTCUSDT",START_MS)]=(.001,99.,101.)
            elif bad=="missing":exp[("BTCUSDT",START_MS+16*HOUR_MS)]=(.0001,99.,101.)
            elif bad=="url":changed["source_url"]="https://example.com/fapi/v1/fundingRate?symbol=BTCUSDT"
            elif bad=="envelope":exp[("BTCUSDT",START_MS)]=(.0001,101.,102.)
            try:reconcile([changed],root,exp)
            except ValueError:checks+=1
            else:raise AssertionError("V98_MARK_TAMPER_NOT_REJECTED_"+bad)
            (root/"capture.json").write_bytes(raw)
        if checks!=6:raise AssertionError("V98_MARK_NEGATIVE_TESTS")
    return {"decision":"PASS_V98_MARK_IMPORTER_SYNTHETIC_ONLY_NO_EXCHANGE_EVIDENCE",
            "positive_test":1,"negative_tests":checks,
            "2026_accessed":False,"paper_live_authorized":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    for key in ("raw-root","old-root","old-envelope","new-root","corrected-root","out-dir"):
        p.add_argument("--"+key)
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),sort_keys=True))
    else:
        for key in ("raw_root","old_root","old_envelope","new_root","corrected_root","out_dir"):
            if not getattr(a,key):
                p.error("--"+key.replace("_","-")+" required")
        d=load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)
        print(json.dumps(run(a.raw_root,d,a.out_dir),sort_keys=True))

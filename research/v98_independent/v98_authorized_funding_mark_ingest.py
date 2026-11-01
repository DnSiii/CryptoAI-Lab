#!/usr/bin/env python3
"""V98-only offline gate for exchange-origin funding-event markPrice evidence.

No network calls, no 2026 access, no strategy or PnL. SHA256 verifies byte
integrity, NOT exchange authenticity; provenance remains an independent gate.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=1669852800000  # 2022-12-01 00:00 UTC
END=1767225600000    # 2026-01-01 00:00 UTC, exclusive
SLOT=8*3600*1000
EXPECTED=(END-START)//SLOT*len(ASSETS)
OFFICIAL_HOST="fapi.binance.com"

def digest(b):
    return hashlib.sha256(b).hexdigest()

def dec(x):
    try:
        v=Decimal(str(x))
        if not v.is_finite(): raise ValueError("NONFINITE")
        return v
    except (InvalidOperation,ValueError,TypeError):
        raise ValueError("BAD_DECIMAL")

def canonical_calendar():
    return {(a,t) for a in ASSETS for t in range(START,END,SLOT)}

def read_expected(path):
    with Path(path).open(newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames!=["asset","fundingTime","fundingRate"]:
            raise ValueError("EXPECTED_SCHEMA")
        rows={}
        for r in rd:
            a=r["asset"]; t=int(r["fundingTime"])
            k=(a,t)
            if k in rows: raise ValueError("EXPECTED_DUPLICATE")
            rows[k]=dec(r["fundingRate"])
    if len(rows)!=EXPECTED or set(rows)!=canonical_calendar():
        raise ValueError("EXPECTED_NATIVE_FUNDING_CALENDAR")
    return rows

def unique_json_object(pairs):
    """Reject duplicate keys in BOTH page metadata and exchange body."""
    out={}
    for k,v in pairs:
        if k in out:raise ValueError("DUPLICATE_RAW_JSON_FIELD")
        out[k]=v
    return out

def validate(pages_path,expected_path,output_path):
    expected=read_expected(expected_path)
    seen={}; page_receipts=[]; retrieved=[]
    with Path(pages_path).open(encoding="utf-8") as f:
        for line_number,line in enumerate(f,1):
            if not line.strip(): continue
            page=json.loads(line,object_pairs_hook=unique_json_object)
            url=page["url"]
            parsed=urlparse(url)
            if (parsed.scheme!="https" or parsed.netloc!=OFFICIAL_HOST or
                parsed.path!="/fapi/v1/fundingRate" or parsed.fragment):
                raise ValueError("NON_OFFICIAL_ENDPOINT")
            params=parse_qs(parsed.query)
            if set(params)!={"symbol","startTime","endTime","limit"} or any(len(v)!=1 for v in params.values()):
                raise ValueError("REQUEST_QUERY_SCHEMA")
            a=params["symbol"][0]
            if a not in ASSETS or not 1<=int(params["limit"][0])<=1000:
                raise ValueError("REQUEST_SYMBOL_OR_LIMIT")
            lo=int(params["startTime"][0]); hi=int(params["endTime"][0])
            if lo<START or hi>=END or lo>hi: raise ValueError("REQUEST_OUT_OF_TRAINING")
            if page["status"]!=200: raise ValueError("NON_200_HTTP")
            headers=page["response_headers"]
            if not isinstance(headers,dict) or sum(k.lower()=="date" for k in headers)!=1:
                raise ValueError("MISSING_OR_DUPLICATE_HTTP_DATE")
            at=dt.datetime.fromisoformat(page["retrieved_at_utc"].replace("Z","+00:00"))
            if at.tzinfo is None or at.utcoffset()!=dt.timedelta(0):
                raise ValueError("RETRIEVAL_NOT_UTC")
            date_value=next(v for k,v in headers.items() if k.lower()=="date")
            try:
                server_at=parsedate_to_datetime(date_value)
            except (ValueError,TypeError,IndexError):
                raise ValueError("MALFORMED_HTTP_DATE")
            if server_at.tzinfo is None or abs((server_at-at).total_seconds())>300:
                raise ValueError("HTTP_DATE_RETRIEVAL_MISMATCH")
            retrieved.append(at.isoformat())
            body=page["response_body"]
            if not isinstance(body,str) or digest(body.encode("utf-8"))!=page["response_body_sha256"]:
                raise ValueError("RAW_BODY_SHA256")
            data=json.loads(body,object_pairs_hook=unique_json_object)
            if not isinstance(data,list) or not data or len(data)>int(params["limit"][0]):
                raise ValueError("EMPTY_OR_OVERSIZED_PAGE")
            times=[]
            for row in data:
                if not {"symbol","fundingTime","fundingRate","markPrice"}.issubset(row):
                    raise ValueError("MISSING_OFFICIAL_FIELDS")
                if row["symbol"]!=a: raise ValueError("SYMBOL_MISMATCH")
                if type(row["fundingTime"]) is not int:
                    raise ValueError("FUNDING_TIME_NOT_INTEGER")
                t=row["fundingTime"]; k=(a,t)
                if t<lo or t>hi or t<START or t>=END or (t-START)%SLOT:
                    raise ValueError("OFF_CALENDAR_OR_FUTURE_EVENT")
                if k in seen: raise ValueError("DUPLICATE_FUNDING_EVENT")
                rate=dec(row["fundingRate"]); mark=dec(row["markPrice"])
                if mark<=0: raise ValueError("INVALID_EXACT_MARK")
                if k not in expected or abs(rate-expected[k])>Decimal("0.000000005"):
                    raise ValueError("NATIVE_FUNDING_RATE_CONFLICT")
                seen[k]=(str(rate),str(mark))
                times.append(t)
            if times!=sorted(times) or len(times)!=len(set(times)):
                raise ValueError("UNSORTED_PAGE")
            page_receipts.append({"line":line_number,"symbol":a,"records":len(data),
                                  "raw_sha256":page["response_body_sha256"],
                                  "retrieved_at_utc":at.isoformat(),"url":url})
    if set(seen)!=set(expected):
        missing=set(expected)-set(seen)
        raise ValueError(f"EXACT_MARK_INCOMPLETE_{len(missing)}_OF_{EXPECTED}")
    out=Path(output_path)
    out.parent.mkdir(parents=True,exist_ok=True)
    csv_path=out.with_suffix(".csv")
    with csv_path.open("w",newline="") as f:
        w=csv.writer(f)
        w.writerow(("asset","fundingTime","fundingRate","markPrice"))
        for a,t in sorted(seen,key=lambda x:(x[1],x[0])):
            rate,mark=seen[(a,t)]
            w.writerow((a,t,rate,mark))
    receipt={"decision":"STRUCTURAL_MATCH_ONLY_ORIGIN_ATTESTATION_REQUIRED",
             "records":len(seen),"pages":len(page_receipts),"train_start_ms":START,
             "train_end_exclusive_ms":END,"exact_marks_csv_sha256":digest(csv_path.read_bytes()),
             "source_pages_sha256":digest(Path(pages_path).read_bytes()),
             "native_expected_sha256":digest(Path(expected_path).read_bytes()),
             "pages_provenance":page_receipts,
             "caveat":"User-supplied HTTP headers and SHA256 are not cryptographic proof of exchange origin. Independent authorized custody required before using for system PnL.",
             "2026_data_used":False,"pnl_computed":False}
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt

def export_native_expected(old_root,old_envelope,new_root,corrected_root,output):
    from v98_2025_full_training_source_bridge import load
    d=load(old_root,old_envelope,new_root,corrected_root)
    if d["exact_funding_tick_mark"] or not d["training_only"]:
        raise ValueError("SOURCE_BRIDGE_CONTRACT")
    import pandas as pd
    with Path(output).open("w",newline="") as f:
        w=csv.writer(f);w.writerow(("asset","fundingTime","fundingRate"))
        for i,t in enumerate(d["time"]):
            for j,a in enumerate(ASSETS):
                if d["event"][i,j]:
                    w.writerow((a,int(t.timestamp()*1000),format(float(d["rate"][i,j]),".12g")))
    return read_expected(output)

def self_test():
    # Structural and tamper tests on a 1-day miniature, never claimed as market data.
    import tempfile
    global START,END,EXPECTED
    saved=(START,END,EXPECTED)
    with tempfile.TemporaryDirectory() as td:
        START=1669852800000;END=START+24*3600000;EXPECTED=12
        expected=Path(td)/"native.csv"
        with expected.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(("asset","fundingTime","fundingRate"))
            for a in ASSETS:
                for t in range(START,END,SLOT):w.writerow((a,t,"0.0001"))
        pages=Path(td)/"pages.jsonl"; lines=[]
        for a in ASSETS:
            rows=[{"symbol":a,"fundingTime":t,"fundingRate":"0.0001","markPrice":"100.0"} for t in range(START,END,SLOT)]
            raw=json.dumps(rows,separators=(",",":"))
            lines.append({"url":f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={a}&startTime={START}&endTime={END-1}&limit=1000",
                          "status":200,"response_headers":{"Date":"Sun, 01 Nov 2026 12:00:00 GMT"},
                          "retrieved_at_utc":"2026-11-01T12:00:00Z","response_body":raw,
                          "response_body_sha256":digest(raw.encode())})
        pages.write_text("\n".join(json.dumps(x) for x in lines)+"\n")
        assert validate(pages,expected,Path(td)/"receipt.json")["records"]==12
        bad=json.loads(lines[0]["response_body"]);bad[0]["markPrice"]="-1"
        lines[0]["response_body"]=json.dumps(bad)
        lines[0]["response_body_sha256"]=digest(lines[0]["response_body"].encode())
        pages.write_text("\n".join(json.dumps(x) for x in lines)+"\n")
        try:validate(pages,expected,Path(td)/"bad.json")
        except ValueError as e:assert str(e)=="INVALID_EXACT_MARK"
        else:raise AssertionError("INVALID_MARK_ACCEPTED")
        # Reject malformed HTTP metadata even when body hashes are valid.
        lines[0]["response_body"]=json.dumps([{"symbol":ASSETS[0],"fundingTime":START+q*SLOT,"fundingRate":"0.0001","markPrice":"100"} for q in range(3)])
        lines[0]["response_body_sha256"]=digest(lines[0]["response_body"].encode())
        lines[0]["response_headers"]={"Date":"not-an-http-date"}
        pages.write_text("\n".join(json.dumps(x) for x in lines)+"\n")
        try:validate(pages,expected,Path(td)/"bad.json")
        except ValueError as e:assert str(e)=="MALFORMED_HTTP_DATE"
        else:raise AssertionError("MALFORMED_DATE_ACCEPTED")
        lines[0]["response_headers"]={"Date":"Sun, 01 Nov 2026 12:00:00 GMT"}
        # A fractional timestamp must never be silently truncated onto a valid 8h slot.
        altered=json.loads(lines[0]["response_body"])
        altered[0]["fundingTime"]=float(START)+.25
        lines[0]["response_body"]=json.dumps(altered)
        lines[0]["response_body_sha256"]=digest(lines[0]["response_body"].encode())
        pages.write_text("\\n".join(json.dumps(x) for x in lines)+"\\n")
        try:validate(pages,expected,Path(td)/"bad.json")
        except ValueError as e:assert str(e)=="FUNDING_TIME_NOT_INTEGER"
        else:raise AssertionError("FRACTIONAL_FUNDING_TIME_ACCEPTED")
        altered[0]["fundingTime"]=START
        lines[0]["response_body"]=json.dumps(altered)
        lines[0]["response_body_sha256"]=digest(lines[0]["response_body"].encode())
        # A duplicate top-level JSONL key must fail even if its last value is valid.
        first=json.dumps(lines[0])
        duplicate=first[:-1]+',"status":200}'
        pages.write_text(duplicate+"\\n"+"\\n".join(json.dumps(x) for x in lines[1:])+"\\n")
        try:validate(pages,expected,Path(td)/"bad.json")
        except ValueError as e:assert str(e)=="DUPLICATE_RAW_JSON_FIELD"
        else:raise AssertionError("DUPLICATE_PAGE_METADATA_ACCEPTED")
        lines[0]["url"]=lines[0]["url"].replace("limit=1000","limit=0")
        pages.write_text("\n".join(json.dumps(x) for x in lines)+"\n")
        try:validate(pages,expected,Path(td)/"bad.json")
        except ValueError as e:assert str(e)=="REQUEST_SYMBOL_OR_LIMIT"
        else:raise AssertionError("INVALID_LIMIT_ACCEPTED")
        lines[0]["url"]=lines[0]["url"].replace("limit=0","limit=1000")
        lines[0]["response_body_sha256"]="0"*64
        pages.write_text("\n".join(json.dumps(x) for x in lines)+"\n")
        try:validate(pages,expected,Path(td)/"bad.json")
        except ValueError as e:assert str(e)=="RAW_BODY_SHA256"
        else:raise AssertionError("TAMPER_ACCEPTED")
    START,END,EXPECTED=saved
    print("PASS_V98_EXACT_MARK_OFFLINE_STRUCTURAL_FIXTURE_ONLY_NO_VENDOR_DATA_NO_PNL")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--export-native",action="store_true")
    p.add_argument("--old-root");p.add_argument("--old-envelope")
    p.add_argument("--new-root");p.add_argument("--corrected-root")
    p.add_argument("--pages");p.add_argument("--expected");p.add_argument("--output")
    a=p.parse_args()
    if a.self_test:self_test();return
    if a.export_native:
        if not all((a.old_root,a.old_envelope,a.new_root,a.corrected_root,a.output)):
            p.error("missing source-bridge arguments")
        print("V98_NATIVE_EXPECTED_EVENTS",len(export_native_expected(a.old_root,a.old_envelope,a.new_root,a.corrected_root,a.output)))
        return
    if not all((a.pages,a.expected,a.output)):p.error("--pages --expected --output required")
    print(json.dumps(validate(a.pages,a.expected,a.output),sort_keys=True))
if __name__=="__main__":main()

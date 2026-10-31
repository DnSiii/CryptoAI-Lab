#!/usr/bin/env python3
"""V98-only independent reconstruction of a captured fundingRate HTTP evidence bundle.

Checks raw-page -> assembled-file -> manifest content chain. This is NOT an
exchange-origin certificate and NEVER substitutes for native-source attestation.
No PnL, future data, XRP or benchmark access.
"""
from __future__ import annotations
import argparse, hashlib, json, math, tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
SCOPE="V98_CLEAN4_2022_2024_TRAINING_ONLY"
FIRST=1669852800000
STEP=28800000
N=2286
LAST=FIRST+(N-1)*STEP
ENDPOINT="https://fapi.binance.com/fapi/v1/fundingRate"

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def within(root:Path,relative:str)->Path:
    if not isinstance(relative,str) or not relative or Path(relative).is_absolute():
        raise ValueError("V98_INVALID_RELATIVE_PATH")
    p=(root/relative).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError("V98_CAPTURE_PATH_ESCAPE_OR_MISSING")
    return p

def official_url(url:str,symbol:str,start:int)->None:
    parsed=urlparse(url)
    if (parsed.scheme!="https" or parsed.netloc!="fapi.binance.com" or
        parsed.path!="/fapi/v1/fundingRate" or parsed.fragment):
        raise ValueError("V98_NON_OFFICIAL_URL")
    q=parse_qs(parsed.query,strict_parsing=True)
    expected={"symbol":[symbol],"startTime":[str(start)],
              "endTime":[str(LAST+60000)],"limit":["1000"]}
    if q!=expected:
        raise ValueError("V98_PAGE_QUERY_MISMATCH")

def validate_row(row:dict,symbol:str,expected_slot:int)->None:
    if not isinstance(row,dict) or row.get("symbol")!=symbol:
        raise ValueError("V98_BAD_SYMBOL")
    if not all(k in row for k in ("fundingTime","fundingRate","markPrice")):
        raise ValueError("V98_MISSING_EVENT_FIELDS")
    ts=row["fundingTime"]
    if type(ts) is not int or not 0<=ts-(FIRST+expected_slot*STEP)<=60000:
        raise ValueError("V98_NONCAUSAL_OR_MISSING_EVENT_SLOT")
    try:
        rate=float(row["fundingRate"]);mark=float(row["markPrice"])
    except (TypeError,ValueError,OverflowError):
        raise ValueError("V98_BAD_EVENT_VALUE")
    if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
        raise ValueError("V98_NONFINITE_RATE_OR_MARK")

def audit(directory:Path)->dict:
    root=directory.resolve()
    receipt=json.loads(within(root,"v98_transport_capture_receipt.json").read_bytes())
    manifest=json.loads(within(root,"v98_exact_funding_manifest.json").read_bytes())
    if receipt.get("scope")!=SCOPE or manifest.get("scope")!=SCOPE:
        raise ValueError("V98_WRONG_SCOPE")
    if (receipt.get("endpoint")!=ENDPOINT or
        receipt.get("event_count")!=4*N or
        receipt.get("operator_asserted_transport_only") is not True or
        receipt.get("official_origin_independently_attested") is not False or
        receipt.get("pnl_computed") is not False or
        receipt.get("2025_accessed") is not False or
        receipt.get("2026_plus_accessed") is not False):
        raise ValueError("V98_MISLEADING_CAPTURE_RECEIPT")
    captures=receipt.get("capture_pages")
    assets=manifest.get("assets")
    if not isinstance(captures,dict) or not isinstance(assets,dict) or set(captures)!=set(ASSETS) or set(assets)!=set(ASSETS):
        raise ValueError("V98_ASSET_SET_MISMATCH")
    stats={}
    for symbol in ASSETS:
        pages=captures[symbol]
        meta=assets[symbol]
        if not isinstance(pages,list) or not 3<=len(pages)<=7 or not isinstance(meta,dict):
            raise ValueError("V98_BAD_PAGINATION_OR_MANIFEST")
        rows=[];expected_start=FIRST
        for i,page in enumerate(pages,1):
            if not isinstance(page,dict) or page.get("page")!=i or page.get("http_status")!=200:
                raise ValueError("V98_PAGE_STATUS_OR_ORDER")
            official_url(page.get("request_url",""),symbol,expected_start)
            if not page.get("request_utc") or not page.get("response_utc"):
                raise ValueError("V98_MISSING_TRANSPORT_TIMESTAMPS")
            raw=within(root,page.get("raw_path"))
            data=raw.read_bytes()
            if digest(data)!=page.get("raw_sha256"):
                raise ValueError("V98_RAW_PAGE_SHA_MISMATCH")
            part=json.loads(data)
            if not isinstance(part,list) or not 1<=len(part)<=1000 or page.get("rows")!=len(part):
                raise ValueError("V98_PAGE_COUNT")
            if page.get("first_time")!=part[0].get("fundingTime") or page.get("last_time")!=part[-1].get("fundingTime"):
                raise ValueError("V98_PAGE_BOUNDARY_MISMATCH")
            if len(rows)+len(part)>N:
                raise ValueError("V98_TOO_MANY_EVENTS")
            for j,row in enumerate(part):
                validate_row(row,symbol,len(rows)+j)
            rows.extend(part)
            expected_start=rows[-1]["fundingTime"]+1
        if len(rows)!=N:
            raise ValueError("V98_INCOMPLETE_EVENTS")
        official_url(meta.get("source_url",""),symbol,FIRST)
        assembled=within(root,meta.get("path"))
        raw=assembled.read_bytes()
        if digest(raw)!=meta.get("sha256"):
            raise ValueError("V98_ASSEMBLED_SHA_MISMATCH")
        if json.loads(raw)!=rows:
            raise ValueError("V98_RAW_PAGES_ASSEMBLED_DIVERGENCE")
        stats[symbol]={"events":len(rows),"pages":len(pages),
                       "assembled_sha256":digest(raw)}
    return {"decision":"PASS_CAPTURE_CONTENT_CHAIN_TRANSPORT_ORIGIN_UNATTESTED",
            "events_reconciled":N*4,"assets":stats,
            "manifest_sha256":digest(within(root,"v98_exact_funding_manifest.json").read_bytes()),
            "exchange_origin_attested":False,
            "native_rate_and_mark_envelope_reconciled":False,
            "pnl_computed":False,"2025_accessed":False,"2026_plus_accessed":False}

def self_test()->dict:
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);caps={};assets={}
        for symbol in ASSETS:
            rows=[{"symbol":symbol,"fundingTime":FIRST+i*STEP,
                   "fundingRate":"0.0001","markPrice":"100.01"} for i in range(N)]
            pages=[]
            for j in range(0,N,1000):
                chunk=rows[j:j+1000]
                raw=json.dumps(chunk,separators=(",",":")).encode()
                name=f"{symbol}_page_{j//1000+1:03d}.json"
                (root/name).write_bytes(raw)
                url=(ENDPOINT+f"?symbol={symbol}&startTime={chunk[0]['fundingTime']}"
                     +f"&endTime={LAST+60000}&limit=1000")
                pages.append({"page":j//1000+1,"request_url":url,
                              "request_utc":"2026-10-31T00:00:00Z",
                              "response_utc":"2026-10-31T00:00:01Z",
                              "http_status":200,"raw_path":name,
                              "raw_sha256":digest(raw),"rows":len(chunk),
                              "first_time":chunk[0]["fundingTime"],
                              "last_time":chunk[-1]["fundingTime"]})
            raw=json.dumps(rows,separators=(",",":")).encode()
            name=f"{symbol}_fundingRate_exact_2022_2024.json"
            (root/name).write_bytes(raw)
            assets[symbol]={"path":name,"sha256":digest(raw),"source_url":pages[0]["request_url"]}
            caps[symbol]=pages
        manifest={"scope":SCOPE,"assets":assets}
        receipt={"scope":SCOPE,"endpoint":ENDPOINT,"event_count":4*N,
                 "operator_asserted_transport_only":True,
                 "official_origin_independently_attested":False,
                 "pnl_computed":False,"2025_accessed":False,
                 "2026_plus_accessed":False,"capture_pages":caps}
        mp=root/"v98_exact_funding_manifest.json"
        rp=root/"v98_transport_capture_receipt.json"
        mp.write_text(json.dumps(manifest));rp.write_text(json.dumps(receipt))
        assert audit(root)["events_reconciled"]==9144
        rawpath=root/caps["BTCUSDT"][0]["raw_path"]
        original=rawpath.read_bytes()
        rawpath.write_bytes(original+b" ")
        try:audit(root)
        except ValueError as exc:
            assert "RAW_PAGE_SHA_MISMATCH" in str(exc)
        else:raise AssertionError("V98_UNDETECTED_RAW_TAMPER")
        rawpath.write_bytes(original)
        bad=json.loads(mp.read_text())
        bad["assets"]["BTCUSDT"]["source_url"]="https://fake.example/fapi/v1/fundingRate"
        mp.write_text(json.dumps(bad))
        try:audit(root)
        except ValueError as exc:
            assert "NON_OFFICIAL_URL" in str(exc)
        else:raise AssertionError("V98_UNDETECTED_URL_TAMPER")
        mp.write_text(json.dumps(manifest))
        assembled=root/assets["BTCUSDT"]["path"]
        original=assembled.read_bytes()
        forged=json.loads(original);forged[0]["markPrice"]="123.45"
        forged_raw=json.dumps(forged,separators=(",",":")).encode()
        assembled.write_bytes(forged_raw)
        manifest["assets"]["BTCUSDT"]["sha256"]=digest(forged_raw)
        mp.write_text(json.dumps(manifest))
        try:audit(root)
        except ValueError as exc:
            assert "RAW_PAGES_ASSEMBLED_DIVERGENCE" in str(exc)
        else:raise AssertionError("V98_UNDETECTED_ASSEMBLED_TAMPER")
    return {"decision":"PASS_SYNTHETIC_CAPTURE_CHAIN_TEST_NOT_OFFICIAL_SOURCE",
            "events_fixture":9144,"tamper_cases":3,
            "official_events_acquired":0,"pnl_computed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--capture-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        result=self_test()
    else:
        if args.capture_dir is None:raise SystemExit("--capture-dir required")
        result=audit(args.capture_dir)
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()

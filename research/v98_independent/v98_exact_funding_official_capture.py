#!/usr/bin/env python3
"""V98 ONLY: fail-closed Binance USD-M exact funding mark capture for authorized networks.

Not an exchange signature, not an independent provenance certificate, not PnL.
Requires subsequent V98 exact importer and independent chain-of-custody audit.
Hard-coded 2022-12 through 2025-12 exploratory training; never fetches 2026+.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,math,os
from pathlib import Path
from urllib.parse import urlencode,urlparse,parse_qs
from urllib.request import Request,urlopen

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
ENDPOINT="https://fapi.binance.com/fapi/v1/fundingRate"
FIRST_MS=1669852800000
INTERVAL_MS=28800000
EVENTS_PER_ASSET=3381
LAST_MS=FIRST_MS+(EVENTS_PER_ASSET-1)*INTERVAL_MS
LIMIT=1000
SCOPE="V98_CLEAN4_2022_2025_EXPOSED_TRAINING_ONLY"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def utc_now()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def page_url(symbol:str,start_ms:int)->str:
    if symbol not in ASSETS or start_ms<FIRST_MS or start_ms>LAST_MS+60000:
        raise ValueError("V98_INVALID_REQUEST_SCOPE")
    return ENDPOINT+"?"+urlencode({"symbol":symbol,"startTime":start_ms,
                                   "endTime":LAST_MS+60000,"limit":LIMIT})

def check_page(body:bytes,symbol:str,start_ms:int):
    if not body or len(body)>5_000_000:raise ValueError("V98_EMPTY_OR_OVERSIZE_RESPONSE")
    rows=json.loads(body)
    if not isinstance(rows,list) or not 1<=len(rows)<=LIMIT:
        raise ValueError("V98_BAD_PAGE_COUNT")
    last=start_ms-1
    for row in rows:
        if not isinstance(row,dict) or row.get("symbol")!=symbol:
            raise ValueError("V98_BAD_SYMBOL")
        if not all(k in row for k in ("fundingTime","fundingRate","markPrice")):
            raise ValueError("V98_MISSING_OFFICIAL_FIELDS")
        if not isinstance(row["fundingTime"],int) or isinstance(row["fundingTime"],bool):
            raise ValueError("V98_BAD_TIMESTAMP_TYPE")
        t=row["fundingTime"]
        if t<=last or t<FIRST_MS or t>LAST_MS+60000:
            raise ValueError("V98_DUPLICATE_UNSORTED_OR_OUT_OF_SCOPE")
        slot,offset=divmod(t-FIRST_MS,INTERVAL_MS)
        if slot>=EVENTS_PER_ASSET or offset>60000:
            raise ValueError("V98_OFF_CALENDAR_EVENT")
        try:
            rate=float(row["fundingRate"]);mark=float(row["markPrice"])
        except (ValueError,TypeError,OverflowError):
            raise ValueError("V98_BAD_NATIVE_VALUES")
        if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
            raise ValueError("V98_BAD_RATE_OR_MARK")
        last=t
    return rows

def capture_symbol(out:Path,symbol:str,timeout:int):
    pages=[];rows=[];start_ms=FIRST_MS
    for page_num in range(1,8): # 4 expected pages; fail on runaway pagination
        url=page_url(symbol,start_ms)
        req=Request(url,headers={"Accept":"application/json","User-Agent":"V98-Independent-Official-Funding-Capture/1.0"})
        requested=utc_now()
        with urlopen(req,timeout=timeout) as response:
            status=response.status
            headers=dict(response.headers.items())
            raw=response.read(5_000_001)
        captured=utc_now()
        if status!=200:raise ValueError("V98_NON_200_"+str(status))
        if "json" not in headers.get("Content-Type",headers.get("content-type","")).lower():
            raise ValueError("V98_NON_JSON_CONTENT_TYPE")
        part=check_page(raw,symbol,start_ms)
        # Prevent pages that overlap or omit earlier events; the complete
        # sequential 8h slot invariant is checked again below.
        if rows and part[0]["fundingTime"]<=rows[-1]["fundingTime"]:
            raise ValueError("V98_PAGE_OVERLAP")
        filename=f"{symbol}_page_{page_num:03d}.json"
        (out/filename).write_bytes(raw)
        pages.append({"page":page_num,"request_url":url,"request_utc":requested,
                      "response_utc":captured,"http_status":status,
                      "response_headers":{k:v for k,v in headers.items()
                          if k.lower() in ("date","content-type","server","x-mbx-used-weight-1m")},
                      "raw_path":filename,"raw_sha256":sha(raw),
                      "rows":len(part),"first_time":part[0]["fundingTime"],
                      "last_time":part[-1]["fundingTime"]})
        rows.extend(part)
        if len(rows)>=EVENTS_PER_ASSET:break
        start_ms=part[-1]["fundingTime"]+1
    if len(rows)!=EVENTS_PER_ASSET:raise ValueError("V98_INCOMPLETE_EVENT_COUNT_"+symbol)
    for index,row in enumerate(rows):
        slot,offset=divmod(row["fundingTime"]-FIRST_MS,INTERVAL_MS)
        if slot!=index or offset>60000:
            raise ValueError("V98_MISSING_DUPLICATE_OR_OFF_CALENDAR_SLOT_"+symbol)
    assembled=json.dumps(rows,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    filename=f"{symbol}_fundingRate_exact_2022_2025.json"
    (out/filename).write_bytes(assembled)
    return {"path":filename,"sha256":sha(assembled),"source_url":pages[0]["request_url"]},pages

def self_test():
    row={"symbol":"BTCUSDT","fundingTime":FIRST_MS,"fundingRate":"0.0001","markPrice":"100.25"}
    good=json.dumps([row]).encode()
    if len(check_page(good,"BTCUSDT",FIRST_MS))!=1:raise AssertionError("V98_GOOD_FIXTURE")
    for mutate in (
        lambda x:x.pop("markPrice"),
        lambda x:x.update(markPrice="-1"),
        lambda x:x.update(symbol="XRPUSDT"),
        lambda x:x.update(fundingTime=FIRST_MS+60001),
        lambda x:x.update(fundingTime=FIRST_MS-1),
    ):
        bad=dict(row);mutate(bad)
        try:check_page(json.dumps([bad]).encode(),"BTCUSDT",FIRST_MS)
        except ValueError:pass
        else:raise AssertionError("V98_TAMPER_NOT_DETECTED")
    if "2025" in page_url("BTCUSDT",FIRST_MS):
        raise AssertionError("V98_UNEXPECTED_URL")
    return {"decision":"PASS_SYNTHETIC_SOURCE_CAPTURE_CONTRACT_NOT_PROVENANCE",
            "tamper_cases":5,"actual_official_events_downloaded":0,
            "pnl_computed":False,"2025_accessed":False,"2026_plus_accessed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--timeout",type=int,default=20)
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),indent=2));return
    if a.dry_run:
        print(json.dumps({"scope":SCOPE,"endpoint":ENDPOINT,
            "first_page_urls":[page_url(s,FIRST_MS) for s in ASSETS],
            "network_accessed":False,"pnl_computed":False},indent=2));return
    if a.output_dir is None:raise SystemExit("--output-dir required")
    out=a.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("V98_FAIL_CLOSED_OUTPUT_DIRECTORY_MUST_BE_EMPTY")
    out.mkdir(parents=True,exist_ok=True)
    assets={};captures={}
    for symbol in ASSETS:
        assets[symbol],captures[symbol]=capture_symbol(out,symbol,a.timeout)
    manifest={"scope":SCOPE,"assets":assets}
    receipt={"scope":SCOPE,"endpoint":ENDPOINT,"created_utc":utc_now(),
             "capture_pages":captures,"event_count":EVENTS_PER_ASSET*len(ASSETS),
             "operator_asserted_transport_only":True,
             "official_origin_independently_attested":False,
             "requires_original_HTTP_and_external_source_identity_verification":True,
             "requires_strict_V98_importer_and_independent_oracle":True,
             "pnl_computed":False,"2025_accessed":False,"2026_plus_accessed":False,
             "decision":"CAPTURE_COMPLETE_CONTENT_CONTRACT_PENDING_EXTERNAL_PROVENANCE_AUDIT"}
    (out/"v98_exact_funding_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    (out/"v98_transport_capture_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":receipt["decision"],"events":receipt["event_count"],
                      "manifest_sha256":sha((out/"v98_exact_funding_manifest.json").read_bytes()),
                      "provenance_attested":False},indent=2))
if __name__=="__main__":main()

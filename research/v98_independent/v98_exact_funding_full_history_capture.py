#!/usr/bin/env python3
"""V98 ONLY: authorized Binance USD-M exact funding mark capture, Dec-2022 to Dec-2025.
Fail closed; does not bypass HTTP 451 or independently attest exchange provenance.
No PnL, benchmarks, 2026+, holdout, paper or live access.
"""
import argparse,datetime as dt,hashlib,json,math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
URL="https://fapi.binance.com/fapi/v1/fundingRate"
FIRST=1669852800000
INTERVAL=28800000
COUNT=3381
LAST=FIRST+(COUNT-1)*INTERVAL
SCOPE="V98_CLEAN4_2022_2025_EXPOSED_TRAINING_ONLY"

def digest(raw):return hashlib.sha256(raw).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def url(symbol,start):
    if symbol not in ASSETS or not FIRST<=start<=LAST+60000:
        raise ValueError("V98_FULL_CAPTURE_REQUEST_SCOPE")
    return URL+"?"+urlencode({"symbol":symbol,"startTime":start,
                               "endTime":LAST+60000,"limit":1000})
def check_page(raw,symbol,start):
    if not raw or len(raw)>5_000_000:raise ValueError("V98_FULL_CAPTURE_BODY_SIZE")
    rows=json.loads(raw)
    if not isinstance(rows,list) or not 1<=len(rows)<=1000:
        raise ValueError("V98_FULL_CAPTURE_PAGE_COUNT")
    previous=start-1
    for row in rows:
        if not isinstance(row,dict) or row.get("symbol")!=symbol:
            raise ValueError("V98_FULL_CAPTURE_SYMBOL")
        if not all(k in row for k in ("fundingTime","fundingRate","markPrice")):
            raise ValueError("V98_FULL_CAPTURE_MISSING_FIELDS")
        t=row["fundingTime"]
        if type(t) is not int or t<=previous or t>LAST+60000:
            raise ValueError("V98_FULL_CAPTURE_TIMESTAMP")
        slot,offset=divmod(t-FIRST,INTERVAL)
        if not 0<=slot<COUNT or offset>60000:
            raise ValueError("V98_FULL_CAPTURE_OFF_CALENDAR")
        try:rate=float(row["fundingRate"]);mark=float(row["markPrice"])
        except (TypeError,ValueError,OverflowError):
            raise ValueError("V98_FULL_CAPTURE_NATIVE_VALUES")
        if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
            raise ValueError("V98_FULL_CAPTURE_NONFINITE")
        previous=t
    return rows

def capture_symbol(folder,symbol,timeout):
    rows=[];pages=[];start=FIRST
    for number in range(1,8):
        requested_url=url(symbol,start)
        request=Request(requested_url,headers={"Accept":"application/json",
                         "User-Agent":"V98-Independent-Full-History-Capture/1.0"})
        requested=now()
        with urlopen(request,timeout=timeout) as response:
            status=response.status
            headers=dict(response.headers.items())
            body=response.read(5_000_001)
        responded=now()
        if status!=200:raise ValueError("V98_FULL_CAPTURE_HTTP_"+str(status))
        if "json" not in headers.get("Content-Type",headers.get("content-type","")).lower():
            raise ValueError("V98_FULL_CAPTURE_NOT_JSON")
        part=check_page(body,symbol,start)
        if rows and part[0]["fundingTime"]<=rows[-1]["fundingTime"]:
            raise ValueError("V98_FULL_CAPTURE_OVERLAPPING_PAGE")
        filename=f"{symbol}_page_{number:03d}.json"
        (folder/filename).write_bytes(body)
        pages.append({"request_url":requested_url,"request_utc":requested,
                      "response_utc":responded,"http_status":status,
                      "response_headers":{k:v for k,v in headers.items() if k.lower() in
                         ("date","content-type","server","x-mbx-used-weight-1m")},
                      "raw_path":filename,"raw_sha256":digest(body),
                      "rows":len(part),"first_time":part[0]["fundingTime"],
                      "last_time":part[-1]["fundingTime"]})
        rows.extend(part)
        if len(rows)>=COUNT:break
        start=part[-1]["fundingTime"]+1
    if len(rows)!=COUNT:raise ValueError("V98_FULL_CAPTURE_INCOMPLETE_"+symbol)
    for index,row in enumerate(rows):
        slot,offset=divmod(row["fundingTime"]-FIRST,INTERVAL)
        if slot!=index or offset>60000:
            raise ValueError("V98_FULL_CAPTURE_MISSING_OR_DUPLICATE_SLOT")
    assembled=json.dumps(rows,separators=(",",":"),ensure_ascii=False).encode()
    filename=f"{symbol}_fundingRate_exact_2022_2025.json"
    (folder/filename).write_bytes(assembled)
    return {"path":filename,"sha256":digest(assembled),
            "source_url":pages[0]["request_url"]},pages

def self_test():
    sample={"symbol":"BTCUSDT","fundingTime":FIRST,"fundingRate":"0.0001",
            "markPrice":"100.5"}
    if len(check_page(json.dumps([sample]).encode(),"BTCUSDT",FIRST))!=1:
        raise AssertionError("V98_FULL_CAPTURE_GOOD_FIXTURE")
    cases=[("markPrice","-1"),("fundingRate","nan"),("symbol","XRPUSDT"),
           ("fundingTime",FIRST+60001),("fundingTime",FIRST-1)]
    for key,bad in cases:
        row=dict(sample);row[key]=bad
        try:check_page(json.dumps([row]).encode(),"BTCUSDT",FIRST)
        except ValueError:pass
        else:raise AssertionError("V98_FULL_CAPTURE_TAMPER")
    if str(LAST+60000) not in url("BTCUSDT",FIRST):
        raise AssertionError("V98_FULL_CAPTURE_END_SCOPE")
    return {"decision":"PASS_V98_FULL_CAPTURE_SYNTHETIC_CONTRACT_NOT_OFFICIAL_DATA",
            "tamper_cases":len(cases),"native_events_downloaded":0,"pnl_computed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--timeout",type=int,default=20)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if a.self_test:print(json.dumps(self_test(),sort_keys=True));return
    if a.dry_run:
        print(json.dumps({"scope":SCOPE,"first_page_urls":[url(s,FIRST) for s in ASSETS],
                          "network_accessed":False,"pnl_computed":False},indent=2));return
    if a.output_dir is None:p.error("--output-dir required")
    folder=a.output_dir.resolve()
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit("V98_FULL_CAPTURE_OUTPUT_MUST_BE_EMPTY")
    folder.mkdir(parents=True,exist_ok=True)
    assets={};pages={}
    for symbol in ASSETS:
        assets[symbol],pages[symbol]=capture_symbol(folder,symbol,a.timeout)
    manifest={"scope":SCOPE,"assets":assets}
    receipt={"scope":SCOPE,"endpoint":URL,"created_utc":now(),
             "capture_pages":pages,"native_events":COUNT*len(ASSETS),
             "operator_asserted_transport_only":True,
             "official_origin_independently_attested":False,
             "requires_original_HTTP_headers_raw_body_SHA256_and_independent_audit":True,
             "requires_v98_full_history_importer":True,
             "2025_exposed_training_only":True,"2026_plus_accessed":False,
             "holdout_accessed":False,"pnl_computed":False,"paper_or_live_authorized":False,
             "decision":"CAPTURE_CONTENT_COMPLETE_PENDING_EXTERNAL_TRANSPORT_ATTESTATION"}
    (folder/"v98_exact_funding_full_history_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    (folder/"v98_exact_funding_full_history_transport.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":receipt["decision"],"events":COUNT*4,
                      "manifest_sha256":digest((folder/"v98_exact_funding_full_history_manifest.json").read_bytes()),
                      "provenance_attested":False},sort_keys=True))
if __name__=="__main__":main()

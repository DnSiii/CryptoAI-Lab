#!/usr/bin/env python3
"""V98 independent full-history raw HTTP-page -> assembled funding mark chain audit.
Checks 13,524 event objects and hashes. Cannot prove HTTP origin by itself.
No source acquisition, PnL, 2026+ market data, holdout or benchmark.
"""
import argparse,datetime as dt,hashlib,json,math,tempfile
from pathlib import Path
from urllib.parse import urlsplit,parse_qs

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
FIRST=1669852800000;STEP=28800000;N=3381;LAST=FIRST+(N-1)*STEP
SCOPE="V98_CLEAN4_2022_2025_EXPOSED_TRAINING_ONLY"
ENDPOINT="https://fapi.binance.com/fapi/v1/fundingRate"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def utc(value):
    if not isinstance(value,str):raise ValueError("V98_FULL_AUDIT_TIME_TYPE")
    try:stamp=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:raise ValueError("V98_FULL_AUDIT_TIME_FORMAT")
    if stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0):
        raise ValueError("V98_FULL_AUDIT_TIME_NOT_UTC")
    return stamp

def safe(root,name):
    if not isinstance(name,str) or not name or Path(name).is_absolute():
        raise ValueError("V98_FULL_AUDIT_BAD_PATH")
    path=(root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("V98_FULL_AUDIT_ESCAPE_OR_MISSING")
    return path

def check_url(value,symbol,start):
    if not isinstance(value,str):raise ValueError("V98_FULL_AUDIT_URL_TYPE")
    p=urlsplit(value)
    if p.scheme!="https" or p.netloc!="fapi.binance.com" or p.path!="/fapi/v1/fundingRate" or p.fragment:
        raise ValueError("V98_FULL_AUDIT_OFFICIAL_URL_CLAIM")
    q=parse_qs(p.query,strict_parsing=True)
    if q!={"symbol":[symbol],"startTime":[str(start)],
           "endTime":[str(LAST+60000)],"limit":["1000"]}:
        raise ValueError("V98_FULL_AUDIT_QUERY")

def audit(folder):
    root=Path(folder).resolve()
    receipt=json.loads(safe(root,"v98_exact_funding_full_history_transport.json").read_bytes())
    manifest=json.loads(safe(root,"v98_exact_funding_full_history_manifest.json").read_bytes())
    if receipt.get("scope")!=SCOPE or manifest.get("scope")!=SCOPE:
        raise ValueError("V98_FULL_AUDIT_SCOPE")
    if (receipt.get("endpoint")!=ENDPOINT or receipt.get("native_events")!=4*N
        or receipt.get("operator_asserted_transport_only") is not True
        or receipt.get("official_origin_independently_attested") is not False
        or receipt.get("2025_exposed_training_only") is not True
        or receipt.get("2026_plus_accessed") is not False
        or receipt.get("holdout_accessed") is not False
        or receipt.get("pnl_computed") is not False):
        raise ValueError("V98_FULL_AUDIT_RECEIPT_SCOPE")
    caps=receipt.get("capture_pages");files=manifest.get("assets")
    if not isinstance(caps,dict) or not isinstance(files,dict) or set(caps)!=set(ASSETS) or set(files)!=set(ASSETS):
        raise ValueError("V98_FULL_AUDIT_ASSETS")
    summary={}
    for symbol in ASSETS:
        pages=caps[symbol];meta=files[symbol]
        if not isinstance(pages,list) or not 4<=len(pages)<=7 or not isinstance(meta,dict):
            raise ValueError("V98_FULL_AUDIT_PAGE_COUNT")
        rows=[];next_start=FIRST;last_response=None
        for page_number,page in enumerate(pages,1):
            if not isinstance(page,dict) or type(page.get("http_status")) is not int or page["http_status"]!=200:
                raise ValueError("V98_FULL_AUDIT_TRANSPORT_META")
            request_utc=utc(page.get("request_utc"));response_utc=utc(page.get("response_utc"))
            if response_utc<request_utc or (last_response is not None and request_utc<last_response):
                raise ValueError("V98_FULL_AUDIT_NONCAUSAL_HTTP_CHRONOLOGY")
            last_response=response_utc
            headers=page.get("response_headers")
            if not isinstance(headers,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in headers.items()):
                raise ValueError("V98_FULL_AUDIT_HTTP_HEADERS_MISSING")
            lower={k.lower():v for k,v in headers.items()}
            if "json" not in lower.get("content-type","").lower():
                raise ValueError("V98_FULL_AUDIT_HTTP_CONTENT_TYPE")
            check_url(page.get("request_url"),symbol,next_start)
            expected_page=f"{symbol}_page_{page_number:03d}.json"
            if page.get("raw_path")!=expected_page:
                raise ValueError("V98_FULL_AUDIT_PAGE_FILENAME_OR_ALIAS")
            raw=safe(root,expected_page).read_bytes()
            if sha(raw)!=page.get("raw_sha256"):
                raise ValueError("V98_FULL_AUDIT_PAGE_SHA")
            part=json.loads(raw)
            if not isinstance(part,list) or not 1<=len(part)<=1000 or len(part)!=page.get("rows"):
                raise ValueError("V98_FULL_AUDIT_PAGE_BODY")
            if page.get("first_time")!=part[0].get("fundingTime") or page.get("last_time")!=part[-1].get("fundingTime"):
                raise ValueError("V98_FULL_AUDIT_PAGE_BOUNDARY")
            if len(rows)+len(part)>N:raise ValueError("V98_FULL_AUDIT_EXCESS_EVENTS")
            for row in part:
                if not isinstance(row,dict) or row.get("symbol")!=symbol:
                    raise ValueError("V98_FULL_AUDIT_SYMBOL")
                if not all(k in row for k in ("fundingTime","fundingRate","markPrice")):
                    raise ValueError("V98_FULL_AUDIT_FIELDS")
                t=row["fundingTime"];i=len(rows)
                if type(t) is not int or not 0<=t-(FIRST+i*STEP)<=60000:
                    raise ValueError("V98_FULL_AUDIT_SLOT")
                try:rate=float(row["fundingRate"]);mark=float(row["markPrice"])
                except (ValueError,TypeError,OverflowError):raise ValueError("V98_FULL_AUDIT_VALUES")
                if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
                    raise ValueError("V98_FULL_AUDIT_NONFINITE")
                rows.append(row)
            next_start=rows[-1]["fundingTime"]+1
        if len(rows)!=N:raise ValueError("V98_FULL_AUDIT_MISSING_EVENTS")
        check_url(meta.get("source_url"),symbol,FIRST)
        expected_assembled=f"{symbol}_fundingRate_exact_2022_2025.json"
        if meta.get("path")!=expected_assembled:
            raise ValueError("V98_FULL_AUDIT_ASSEMBLED_FILENAME_OR_ALIAS")
        assembled=safe(root,expected_assembled).read_bytes()
        if sha(assembled)!=meta.get("sha256"):
            raise ValueError("V98_FULL_AUDIT_ASSEMBLED_SHA")
        if json.loads(assembled)!=rows:
            raise ValueError("V98_FULL_AUDIT_ASSEMBLED_DIVERGENCE")
        summary[symbol]={"events":N,"pages":len(pages),"assembled_sha256":sha(assembled)}
    return {"decision":"PASS_V98_FULL_CAPTURE_CONTENT_CHAIN_EXCHANGE_ORIGIN_UNATTESTED",
            "events_reconciled":4*N,"assets":summary,
            "manifest_sha256":sha(safe(root,"v98_exact_funding_full_history_manifest.json").read_bytes()),
            "exchange_origin_independently_attested":False,
            "native_rate_and_hourly_mark_envelope_reconciled":False,
            "2025_exposed_training_only":True,"2026_plus_accessed":False,
            "holdout_accessed":False,"pnl_computed":False}

def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);captures={};assets={}
        for symbol in ASSETS:
            rows=[{"symbol":symbol,"fundingTime":FIRST+i*STEP,
                   "fundingRate":"0.0001","markPrice":"100.5"} for i in range(N)]
            pages=[]
            for j in range(0,N,1000):
                part=rows[j:j+1000];raw=json.dumps(part,separators=(",",":")).encode()
                name=f"{symbol}_page_{j//1000+1:03d}.json";(root/name).write_bytes(raw)
                start=FIRST if j==0 else rows[j-1]["fundingTime"]+1
                url=ENDPOINT+f"?symbol={symbol}&startTime={start}&endTime={LAST+60000}&limit=1000"
                request_time=dt.datetime(2026,10,31,tzinfo=dt.timezone.utc)+dt.timedelta(seconds=2*(j//1000))
                pages.append({"request_url":url,"request_utc":request_time.isoformat(),
                              "response_utc":(request_time+dt.timedelta(seconds=1)).isoformat(),"http_status":200,
                              "response_headers":{"Content-Type":"application/json","Date":"Sat, 31 Oct 2026 00:00:00 GMT"},
                              "raw_path":name,"raw_sha256":sha(raw),"rows":len(part),
                              "first_time":part[0]["fundingTime"],"last_time":part[-1]["fundingTime"]})
            data=json.dumps(rows,separators=(",",":")).encode()
            name=f"{symbol}_fundingRate_exact_2022_2025.json";(root/name).write_bytes(data)
            assets[symbol]={"path":name,"sha256":sha(data),"source_url":pages[0]["request_url"]}
            captures[symbol]=pages
        mp=root/"v98_exact_funding_full_history_manifest.json"
        rp=root/"v98_exact_funding_full_history_transport.json"
        manifest={"scope":SCOPE,"assets":assets}
        receipt={"scope":SCOPE,"endpoint":ENDPOINT,"native_events":4*N,
                 "operator_asserted_transport_only":True,"official_origin_independently_attested":False,
                 "2025_exposed_training_only":True,"2026_plus_accessed":False,
                 "holdout_accessed":False,"pnl_computed":False,"capture_pages":captures}
        mp.write_text(json.dumps(manifest));rp.write_text(json.dumps(receipt))
        if audit(root)["events_reconciled"]!=13524:raise AssertionError("V98_FULL_AUDIT_FIXTURE")
        p=root/captures["BTCUSDT"][0]["raw_path"];old=p.read_bytes();p.write_bytes(old+b" ")
        try:audit(root)
        except ValueError as e:
            if "PAGE_SHA" not in str(e):raise
        else:raise AssertionError("V98_FULL_AUDIT_UNDETECTED_PAGE_TAMPER")
        p.write_bytes(old)
        forged=json.loads(mp.read_text());forged["assets"]["BTCUSDT"]["source_url"]="https://fake.example/fapi/v1/fundingRate"
        mp.write_text(json.dumps(forged))
        try:audit(root)
        except ValueError as e:
            if "OFFICIAL_URL" not in str(e):raise
        else:raise AssertionError("V98_FULL_AUDIT_UNDETECTED_URL_TAMPER")
        mp.write_text(json.dumps(manifest))
        original_page=captures["BTCUSDT"][0]
        original_headers=original_page["response_headers"]
        original_page["response_headers"]={}
        rp.write_text(json.dumps(receipt))
        try:audit(root)
        except ValueError as e:
            if "HTTP_CONTENT_TYPE" not in str(e):raise
        else:raise AssertionError("V98_FULL_AUDIT_UNDETECTED_HEADER_TAMPER")
        original_page["response_headers"]=original_headers
        original_page["request_utc"]="2026-10-31T00:00:03+00:00"
        original_page["response_utc"]="2026-10-31T00:00:02+00:00"
        rp.write_text(json.dumps(receipt))
        try:audit(root)
        except ValueError as e:
            if "NONCAUSAL_HTTP_CHRONOLOGY" not in str(e):raise
        else:raise AssertionError("V98_FULL_AUDIT_UNDETECTED_TIME_TAMPER")
        original_page["request_utc"]="2026-10-31T00:00:00+00:00"
        original_page["response_utc"]="2026-10-31T00:00:01+00:00"
        rp.write_text(json.dumps(receipt))
        p=root/assets["BTCUSDT"]["path"];old=p.read_bytes()
        forged=json.loads(old);forged[0]["markPrice"]="200"
        data=json.dumps(forged,separators=(",",":")).encode();p.write_bytes(data)
        manifest["assets"]["BTCUSDT"]["sha256"]=sha(data);mp.write_text(json.dumps(manifest))
        try:audit(root)
        except ValueError as e:
            if "ASSEMBLED_DIVERGENCE" not in str(e):raise
        else:raise AssertionError("V98_FULL_AUDIT_UNDETECTED_ASSEMBLED_TAMPER")
    return {"decision":"PASS_V98_FULL_CAPTURE_CHAIN_SYNTHETIC_NOT_PROVENANCE",
            "synthetic_events":13524,"tamper_cases":5,
            "official_events_acquired":0,"pnl_computed":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--capture-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:result=self_test()
    else:
        if a.capture_dir is None:p.error("--capture-dir required")
        result=audit(a.capture_dir)
    print(json.dumps(result,sort_keys=True))

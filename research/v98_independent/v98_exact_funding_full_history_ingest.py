#!/usr/bin/env python3
"""V98 Clean-4 2022-25 EXPOSED TRAINING: exact native funding mark content gate.
This is NOT a downloader, provenance attestation, economic PnL or holdout validator.
It cannot certify a manifest URL without separately verified raw HTTP transport.
"""
import argparse,hashlib,json,math
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=27048
FIRST_MS=1669852800000
INTERVAL_MS=8*3600*1000
EVENTS_PER_ASSET=HOURS//8
SCOPE="V98_CLEAN4_2022_2025_EXPOSED_TRAINING_ONLY"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def official_url_claim(url,symbol):
    if not isinstance(url,str):return False
    p=urlsplit(url)
    if p.scheme!="https" or p.netloc!="fapi.binance.com" or p.path!="/fapi/v1/fundingRate" or p.fragment:
        return False
    try:
        qs=parse_qs(p.query,strict_parsing=True,keep_blank_values=True)
    except ValueError:
        return False
    last=FIRST_MS+(EVENTS_PER_ASSET-1)*INTERVAL_MS
    return qs=={"symbol":[symbol],"startTime":[str(FIRST_MS)],
                "endTime":[str(last+60000)],"limit":["1000"]}

def validate_rows(rows,symbol,d):
    if symbol not in ASSETS or not isinstance(rows,list) or len(rows)!=EVENTS_PER_ASSET:
        raise ValueError("V98_FULL_EXACT_EVENT_COUNT_OR_SYMBOL")
    j=ASSETS.index(symbol)
    exact=np.full(HOURS,np.nan)
    previous=-1
    nonzero_offsets=0
    for i,row in enumerate(rows):
        if not isinstance(row,dict) or row.get("symbol")!=symbol:
            raise ValueError("V98_FULL_EXACT_SYMBOL")
        if not all(k in row for k in ("fundingTime","fundingRate","markPrice")):
            raise ValueError("V98_FULL_EXACT_MISSING_FIELDS")
        # The official endpoint emits an integer millisecond timestamp.
        # int(float/string) silently truncates altered transport data: fail closed.
        timestamp=row["fundingTime"]
        if type(timestamp) is not int:
            raise ValueError("V98_FULL_EXACT_TIMESTAMP_TYPE")
        if type(row["fundingRate"]) not in (str,int,float) or type(row["markPrice"]) not in (str,int,float):
            raise ValueError("V98_FULL_EXACT_VALUE_TYPE")
        try:
            rate=float(row["fundingRate"])
            mark=float(row["markPrice"])
        except (TypeError,ValueError,OverflowError):
            raise ValueError("V98_FULL_EXACT_VALUE_TYPE")
        if timestamp<=previous or not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
            raise ValueError("V98_FULL_EXACT_VALUE_OR_ORDER")
        previous=timestamp
        slot,offset=divmod(timestamp-FIRST_MS,INTERVAL_MS)
        if slot!=i or offset>60000:
            raise ValueError("V98_FULL_EXACT_OFF_CALENDAR_OR_MISSING")
        nonzero_offsets+=int(offset>0)
        t=i*8
        if not bool(d["event"][t,j]):
            raise ValueError("V98_FULL_EXACT_NOT_NATIVE_EVENT")
        if not math.isclose(rate,float(d["rate"][t,j]),rel_tol=0.,abs_tol=1e-11):
            raise ValueError("V98_FULL_EXACT_NATIVE_RATE_MISMATCH")
        lo=float(d["mark_lower"][t,j]);hi=float(d["mark_upper"][t,j])
        if not (math.isfinite(lo) and math.isfinite(hi) and lo>0 and lo-1e-7<=mark<=hi+1e-7):
            raise ValueError("V98_FULL_EXACT_MARK_OUTSIDE_PINNED_ENVELOPE")
        exact[t]=mark
    if np.count_nonzero(np.isfinite(exact))!=EVENTS_PER_ASSET:
        raise ValueError("V98_FULL_EXACT_MISSING_EVENTS")
    return exact,nonzero_offsets

def read_exact_marks(manifest_path,d):
    if (len(d["time"])!=HOURS or not d.get("training_only") or
        not d.get("year_2025_exposed") or d.get("holdout_accessed") or
        d.get("exact_funding_tick_mark") or int(d["event"].sum())!=EVENTS_PER_ASSET*4):
        raise ValueError("V98_FULL_EXACT_TRAINING_SOURCE_GATE")
    manifest_path=Path(manifest_path).resolve()
    raw=manifest_path.read_bytes()
    manifest=json.loads(raw)
    if manifest.get("scope")!=SCOPE or not isinstance(manifest.get("assets"),dict) or set(manifest["assets"])!=set(ASSETS):
        raise ValueError("V98_FULL_EXACT_MANIFEST_SCOPE")
    marks=np.full((HOURS,4),np.nan)
    evidence={}
    for j,symbol in enumerate(ASSETS):
        meta=manifest["assets"][symbol]
        if not isinstance(meta,dict) or not all(k in meta for k in ("path","sha256","source_url")):
            raise ValueError("V98_FULL_EXACT_MANIFEST_FIELDS")
        if not official_url_claim(meta["source_url"],symbol):
            raise ValueError("V98_FULL_EXACT_ENDPOINT_CLAIM")
        path=(manifest_path.parent/meta["path"]).resolve()
        if not path.is_relative_to(manifest_path.parent) or not path.is_file():
            raise ValueError("V98_FULL_EXACT_PATH_ESCAPE_OR_MISSING")
        data=path.read_bytes()
        if digest(data)!=meta["sha256"]:
            raise ValueError("V98_FULL_EXACT_SHA256_MISMATCH")
        marks[:,j],offsets=validate_rows(json.loads(data),symbol,d)
        evidence[symbol]={"events":EVENTS_PER_ASSET,"sha256":digest(data),
                          "nonzero_timestamp_offsets":offsets,
                          "mark_min":float(np.nanmin(marks[:,j])),
                          "mark_max":float(np.nanmax(marks[:,j]))}
    return marks,{"decision":"PASS_V98_FULL_EXACT_CONTENT_CONTRACT_PROVENANCE_NOT_ATTESTED",
                  "scope":SCOPE,"hours":HOURS,"native_event_marks":EVENTS_PER_ASSET*4,
                  "manifest_sha256":digest(raw),"per_symbol":evidence,
                  "official_origin_independently_attested":False,
                  "raw_http_transport_and_headers_required":True,
                  "2025_exposed_training_only":True,"holdout_accessed":False,
                  "2026_plus_accessed":False,"pnl_computed":False,"paper_or_live_authorized":False}

def self_test():
    n=EVENTS_PER_ASSET
    ev=np.zeros((HOURS,4),bool);ev[::8]=True
    d={"event":ev,"rate":np.zeros((HOURS,4)),
       "mark_lower":np.full((HOURS,4),99.),
       "mark_upper":np.full((HOURS,4),101.)}
    rows=[{"symbol":"BTCUSDT","fundingTime":FIRST_MS+i*INTERVAL_MS,
           "fundingRate":"0","markPrice":"100"} for i in range(n)]
    good,offsets=validate_rows(rows,"BTCUSDT",d)
    if offsets or int(np.isfinite(good).sum())!=n:
        raise AssertionError("V98_FULL_EXACT_GOOD_FIXTURE")
    cases=[
        (0,"markPrice","-1"),(0,"markPrice","105"),
        (0,"fundingRate","0.01"),(0,"symbol","XRPUSDT"),
        (0,"fundingTime",FIRST_MS+60001),
        (1,"fundingTime",FIRST_MS),
        (0,"fundingTime",str(FIRST_MS)),
        (0,"fundingTime",float(FIRST_MS)),
        (0,"fundingRate",True),
        (0,"markPrice",True),
    ]
    for idx,key,value in cases:
        old=rows[idx][key];rows[idx][key]=value
        try:validate_rows(rows,"BTCUSDT",d)
        except ValueError:pass
        else:raise AssertionError("V98_FULL_EXACT_TAMPER_NOT_REJECTED")
        finally:rows[idx][key]=old
    good_url=("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT"
              f"&startTime={FIRST_MS}&endTime={FIRST_MS+(EVENTS_PER_ASSET-1)*INTERVAL_MS+60000}&limit=1000")
    if not official_url_claim(good_url,"BTCUSDT"):
        raise AssertionError("V98_FULL_EXACT_OFFICIAL_URL")
    invalid_urls=[
        good_url.replace("fapi.binance.com","fake.example"),
        good_url.replace("limit=1000","limit=1000&symbol=BTCUSDT"),
        good_url.replace("limit=1000","limit=1000&extra=1"),
        good_url.replace("limit=1000","limit=500"),
        good_url.replace(str(FIRST_MS+(EVENTS_PER_ASSET-1)*INTERVAL_MS+60000),
                         str(FIRST_MS+(EVENTS_PER_ASSET-1)*INTERVAL_MS+60000+365*24*3600000)),
    ]
    if any(official_url_claim(u,"BTCUSDT") for u in invalid_urls):
        raise AssertionError("V98_FULL_EXACT_URL_SCOPE_BYPASS")
    return {"decision":"PASS_V98_FULL_EXACT_SYNTHETIC_CONTRACT_NOT_PROVENANCE",
            "tamper_cases":len(cases)+len(invalid_urls),"official_events_retrieved":0,"pnl_computed":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--old-root")
    p.add_argument("--old-envelope")
    p.add_argument("--new-root")
    p.add_argument("--corrected-root")
    p.add_argument("--manifest")
    p.add_argument("--receipt")
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),sort_keys=True));raise SystemExit(0)
    if not all((a.old_root,a.old_envelope,a.new_root,a.corrected_root,a.manifest,a.receipt)):
        p.error("all source paths, manifest and receipt are required")
    from v98_2025_full_training_source_bridge import load
    d=load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)
    _,receipt=read_exact_marks(a.manifest,d)
    Path(a.receipt).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))

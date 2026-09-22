#!/usr/bin/env python3
"""V98 Independent Phase095: CandleFeed Bybit daily liquidation feasibility only.
NO alpha, returns, prices, validation, Phase083, holdout, or 2026 selection data.
"""
import hashlib, json, os, sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://api.candlefeed.ai/v1/liquidations/aggregated"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
START, END = "2023-01-01", "2025-12-31"
OUT = "reports/v98_independent_phase095_liquidation_feasibility.json"

def fetch(symbol, key):
    q = urlencode({"exchange":"bybit","symbol":symbol,"interval":"1d","start":START,"end":END,"limit":5000})
    req = Request(BASE+"?"+q, headers={"Accept":"application/json","Authorization":f"Bearer {key}","X-API-Key":key,"User-Agent":"CryptoAI-Lab-V98-Phase095/1.0"})
    with urlopen(req, timeout=45) as r:
        raw=r.read(); status=r.status
    return status, raw

def parse_rows(obj):
    if isinstance(obj,list): return obj
    for k in ("data","rows","results","liquidations"):
        if isinstance(obj.get(k),list): return obj[k]
    return []

def ts_value(row):
    for k in ("timestamp","time","date","period"):
        if row.get(k) is not None: return row[k]
    return None

def parse_ts(v):
    if isinstance(v,(int,float)):
        if v>1e12: v=v/1000
        return datetime.fromtimestamp(v,tz=timezone.utc)
    s=str(v).strip().replace("Z","+00:00")
    dt=datetime.fromisoformat(s)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def main():
    key=os.getenv("CANDLEFEED_API_KEY","").strip()
    report={"phase":"095","mode":"DATA_ONLY_NO_ALPHA_NO_PNL","source":"CandleFeed","venue":"bybit","dataset":"liquidations/aggregated","interval":"1d","window":[START,END],"symbols":{},"generated_at":datetime.now(timezone.utc).isoformat(),"gate":"FAIL_DATA_NO_ALPHA"}
    if not key:
        report["failure"]="CANDLEFEED_API_KEY unavailable in runner; frozen source requires credential; no source substitution permitted"
    else:
        allpass=True
        for sym in SYMBOLS:
            try:
                status,raw=fetch(sym,key); obj=json.loads(raw); rows=parse_rows(obj)
                parsed=[]; invalid=0
                for i,row in enumerate(rows):
                    try: parsed.append((parse_ts(ts_value(row)),i,row))
                    except Exception: invalid+=1
                parsed.sort(key=lambda x:(x[0],x[1]))
                unique={}
                for t,i,row in parsed: unique.setdefault(t,(i,row))
                times=sorted(unique)
                expected=1096 # leap year 2024 included, inclusive 2023-01-01..2025-12-31
                coverage=len(times)/expected
                first=times[0].date().isoformat() if times else None; last=times[-1].date().isoformat() if times else None
                duplicate_count=len(parsed)-len(times)
                monotonic=all(a<b for a,b in zip(times,times[1:]))
                passed=bool(times and first<="2023-01-07" and last>="2025-12-24" and coverage>=.95 and invalid==0 and duplicate_count==0 and monotonic)
                report["symbols"][sym]={"http_status":status,"raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),"rows":len(rows),"unique_timestamps":len(times),"invalid_timestamps":invalid,"duplicate_timestamps":duplicate_count,"coverage_fraction":coverage,"first":first,"last":last,"strictly_monotonic":monotonic,"pass":passed,"meta":obj.get("meta") if isinstance(obj,dict) else None}
                allpass &= passed
            except HTTPError as e:
                body=e.read(); report["symbols"][sym]={"error":f"HTTP {e.code}","body_sha256":hashlib.sha256(body).hexdigest(),"body_preview":body[:300].decode("utf-8","replace")}; allpass=False
            except (URLError,TimeoutError,ValueError,json.JSONDecodeError) as e:
                report["symbols"][sym]={"error":type(e).__name__,"detail":str(e)[:300]}; allpass=False
        report["gate"]="PASS_DATA_ONLY" if allpass else "FAIL_DATA_NO_ALPHA"
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w") as f: json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": sys.exit(main())

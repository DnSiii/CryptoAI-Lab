#!/usr/bin/env python3
"""V98 Independent Phase096: DefiLlama chain-TVL feasibility only.
NO alpha, returns, crypto prices, validation, Phase083, holdout, V16/V99, or 2026 selection data.
"""
import hashlib, json, math, os, sys
from datetime import datetime, timezone, date
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://api.llama.fi/v2/historicalChainTvl/{}"
CHAINS = ("Ethereum", "BSC")
START, END = date(2023,1,1), date(2025,12,31)
EXPECTED = 1096
OUT = "reports/v98_independent_phase096_defi_tvl_feasibility.json"

def fetch(chain):
    url=BASE.format(quote(chain,safe=""))
    req=Request(url,headers={"Accept":"application/json","User-Agent":"CryptoAI-Lab-V98-Phase096/1.0"})
    with urlopen(req,timeout=60) as r:
        raw=r.read(); status=r.status
    return status,raw,url

def parse_day(v):
    if isinstance(v,(int,float)):
        if v>1e12: v=v/1000
        return datetime.fromtimestamp(v,tz=timezone.utc).date()
    s=str(v).strip().replace("Z","+00:00")
    dt=datetime.fromisoformat(s)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()

def main():
    report={"phase":"096","mode":"DATA_ONLY_NO_ALPHA_NO_PNL","source":"DefiLlama","dataset":"historicalChainTvl","chains":{},"window":[START.isoformat(),END.isoformat()],"generated_at":datetime.now(timezone.utc).isoformat(),"gate":"FAIL_DATA_NO_ALPHA"}
    allpass=True
    for chain in CHAINS:
        try:
            status,raw,url=fetch(chain); obj=json.loads(raw)
            rows=obj if isinstance(obj,list) else []
            parsed=[]; invalid=0; invalid_value=0
            for i,row in enumerate(rows):
                try:
                    d=parse_day(row.get("date")); v=float(row.get("tvl"))
                    if not math.isfinite(v) or v<0: invalid_value+=1; continue
                    if START<=d<=END: parsed.append((d,i,v))
                except Exception: invalid+=1
            parsed.sort(key=lambda x:(x[0],x[1]))
            by_day={}
            for d,i,v in parsed: by_day.setdefault(d,(i,v))
            days=sorted(by_day)
            duplicate_days=len(parsed)-len(days)
            coverage=len(days)/EXPECTED
            first=days[0].isoformat() if days else None; last=days[-1].isoformat() if days else None
            monotonic=all(a<b for a,b in zip(days,days[1:]))
            passed=bool(days and first<="2023-01-07" and last>="2025-12-24" and coverage>=.95 and invalid==0 and invalid_value==0 and duplicate_days==0 and monotonic)
            report["chains"][chain]={"url":url,"http_status":status,"raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),"raw_rows":len(rows),"in_window_rows":len(parsed),"unique_days":len(days),"duplicate_days":duplicate_days,"invalid_rows":invalid,"invalid_values":invalid_value,"coverage_fraction":coverage,"first":first,"last":last,"strictly_monotonic":monotonic,"pass":passed}
            allpass &= passed
        except HTTPError as e:
            body=e.read(); report["chains"][chain]={"error":f"HTTP {e.code}","body_sha256":hashlib.sha256(body).hexdigest(),"body_preview":body[:300].decode("utf-8","replace")}; allpass=False
        except (URLError,TimeoutError,ValueError,json.JSONDecodeError) as e:
            report["chains"][chain]={"error":type(e).__name__,"detail":str(e)[:300]}; allpass=False
    report["gate"]="PASS_DATA_ONLY" if allpass else "FAIL_DATA_NO_ALPHA"
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w") as f: json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__": sys.exit(main())

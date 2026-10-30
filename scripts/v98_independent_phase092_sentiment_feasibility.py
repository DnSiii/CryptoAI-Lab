#!/usr/bin/env python3
"""V98 Independent Phase092 sentiment DATA FEASIBILITY ONLY; no alpha/PnL."""
import datetime as dt, hashlib, json, math, urllib.request
from pathlib import Path
URL='https://api.alternative.me/fng/?limit=0&format=json'; OUT=Path('reports/v98_independent_phase092_sentiment_feasibility.json')
START=dt.date(2023,1,1); END=dt.date(2025,12,31); EXPECTED=(END-START).days+1

def main():
    err=None; raw=b''; obj={}
    try:
        req=urllib.request.Request(URL,headers={'User-Agent':'CryptoAI-Lab-V98-Phase092/1.0'})
        with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
        obj=json.loads(raw)
    except Exception as e: err=f'{type(e).__name__}: {e}'
    rows=[]
    for x in obj.get('data',[]):
        try:
            ts=int(x['timestamp']); d=dt.datetime.fromtimestamp(ts,dt.timezone.utc).date(); v=int(x['value'])
            if START<=d<=END: rows.append((d.isoformat(),ts,v))
        except Exception: pass
    dates=[r[0] for r in rows]; uniq=sorted(set(dates)); dup=len(dates)-len(uniq); coverage=len(uniq)/EXPECTED
    dts=[dt.date.fromisoformat(x) for x in uniq]; gaps=[(b-a).days-1 for a,b in zip(dts,dts[1:]) if (b-a).days>1]
    gates={'coverage_ge_99pct':coverage>=.99,'duplicate_rate_lt_0_1pct':dup/max(1,len(rows))<.001,
      'no_gap_gt_3_days':max(gaps,default=0)<=3,'values_integer_0_100':all(0<=r[2]<=100 for r in rows) and bool(rows),
      'training_boundary_enforced':all(dt.date.fromisoformat(r[0])<=END for r in rows) and bool(rows),
      'source_reacquirable_and_hashed':err is None and bool(raw)}
    decision='PASS_DATA_ONLY' if all(gates.values()) else 'FAIL_DATA_NO_ALPHA'
    p={'engine':'V98 Independent','phase':'092','kind':'DATA_FEASIBILITY_ONLY','decision':decision,'source_url':URL,
      'source_error':err,'raw_sha256':hashlib.sha256(raw).hexdigest() if raw else None,'raw_bytes':len(raw),'period_utc':[str(START),str(END)],
      'expected_days':EXPECTED,'observed_rows':len(rows),'unique_days':len(uniq),'coverage':coverage,'duplicates':dup,
      'max_gap_days':max(gaps,default=0),'first_date':uniq[0] if uniq else None,'last_date':uniq[-1] if uniq else None,'gates':gates,
      'alpha_executed':False,'pnl_executed':False,'crypto_return_join':False,'direction_selected':False,'parameter_search':False,
      'phase083_selection_use':False,'v99_used':False,'v16_used':False,'preregistration':'reports/v98_independent_phase092_sentiment_feasibility_prereg.md'}
    OUT.write_text(json.dumps(p,indent=2,sort_keys=True)+'\n'); print(json.dumps(p,indent=2))
if __name__=='__main__': main()

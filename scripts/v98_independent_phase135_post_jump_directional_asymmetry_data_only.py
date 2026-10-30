#!/usr/bin/env python3
"""V98 Independent Phase135 DATA_ONLY. Emits event counts/hashes only; never emits next-day returns/alpha/PnL."""
from __future__ import annotations
import csv, hashlib, json, math
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT')
ROOT=Path('data/canonical'); OUT=Path('reports/v98_independent_phase135_post_jump_directional_asymmetry_data_only.json')
PREREG=Path('reports/v98_independent_phase135_post_jump_directional_asymmetry_data_only_prereg.md')
START=datetime(2023,1,1,tzinfo=timezone.utc); END=datetime(2025,12,31,23,tzinfo=timezone.utc)
LOOKBACK=28; MULT=3.0; BREADTH=3

def sha(b): return hashlib.sha256(b).hexdigest()
def parse(s):
    try:
        d=datetime.fromisoformat(str(s).replace('Z','+00:00')); return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except Exception:return None

def main():
    per={}; returns={}; complete={}; integrity=True
    for a in ASSETS:
        p=ROOT/f'{a}_1h.csv'; rows=[]; seen=set(); prev=None; dup=mal=future=0; ordered=True
        with p.open(newline='') as f:
            r=csv.DictReader(f)
            for x in r:
                dt=parse(x.get('timestamp',''))
                if dt is None: mal+=1; continue
                if dt in seen: dup+=1
                seen.add(dt)
                if prev is not None and dt<=prev: ordered=False
                prev=dt
                if dt>END: future+=1; continue
                if dt<START-timedelta(days=LOOKBACK+1): continue
                try:c=float(x['close'])
                except Exception:continue
                if math.isfinite(c) and c>0: rows.append((dt,c))
        byday={}
        for dt,c in rows: byday.setdefault(dt.date(),[]).append((dt,c))
        complete[a]={d for d,v in byday.items() if len(v)>=24}
        arr=[]; last=None
        for dt,c in rows:
            if last is not None: arr.append((dt,math.log(c/last)))
            last=c
        returns[a]=arr
        per[a]={'duplicate_timestamps':dup,'malformed_timestamps':mal,'future_rows':future,'strictly_increasing':ordered}
        integrity &= dup==0 and mal==0 and future==0 and ordered
    shock_days={}
    for a,arr in returns.items():
        hist={}
        for dt,r in arr: hist.setdefault(dt.date(),[]).append(r)
        days=sorted(hist)
        for i,d in enumerate(days):
            if d<START.date() or d>END.date(): continue
            prior=[]
            lo=d-timedelta(days=LOOKBACK)
            for pd in days:
                if lo<=pd<d: prior.extend(hist[pd])
            if not prior: continue
            scale=float(np.median(np.abs(np.asarray(prior,dtype=float))))
            if scale>0 and any(r<=-MULT*scale for r in hist[d]): shock_days.setdefault(d,set()).add(a)
    events=sorted(d for d,s in shock_days.items() if len(s)>=BREADTH)
    fold_counts={str(y):sum(d.year==y for d in events) for y in (2023,2024,2025)}
    available=0
    for d in events:
        nxt=d+timedelta(days=1)
        if sum(nxt in complete[a] for a in ASSETS)>=4: available+=1
    coverage=available/len(events) if events else 0.0
    manifest=('\n'.join(d.isoformat() for d in events)+('\n' if events else '')).encode()
    gates={'integrity':integrity,'event_days_gte_20':len(events)>=20,'each_fold_event_days_gte_5':all(v>=5 for v in fold_counts.values()),'next_day_availability_gte_95pct':coverage>=.95}
    passed=all(gates.values())
    out={'engine':'V98 Independent','phase':'135','mode':'DATA_ONLY','family':'post-jump directional asymmetry testability','parameters':{'lookback_days':LOOKBACK,'jump_multiple':MULT,'breadth_assets':BREADTH},'integrity':per,'event_day_count':len(events),'event_days_by_fold':fold_counts,'next_day_availability_ratio':coverage,'event_manifest_sha256':sha(manifest),'gates':gates,'decision':'PASS_DATA_ONLY' if passed else 'FAIL_DATA_NO_ALPHA','next_day_return_values_exposed':False,'alpha_or_pnl_inspected':False,'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'phase083_selection_use':False,'parameter_search':False,'rescue_allowed':False,'prereg_sha256':sha(PREREG.read_bytes())}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':'135','decision':out['decision'],'event_day_count':len(events),'event_days_by_fold':fold_counts,'next_day_availability_ratio':coverage,'gates':gates},sort_keys=True))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""V98 Independent Phase129: BTC realized-volatility DATA_ONLY gate. Emits no RV values."""
from __future__ import annotations
import csv, hashlib, json, math
from collections import defaultdict
from datetime import datetime, timezone, date
from pathlib import Path

IN=Path('data/canonical/BTCUSDT_1h.csv')
OUT=Path('reports/v98_independent_phase129_realized_volatility_data_only.json')
PREREG=Path('reports/v98_independent_phase129_realized_volatility_data_only_prereg.md')
START=date(2023,1,1); END=date(2025,12,31)
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def parse_ts(s):
    s=str(s).strip().replace('Z','+00:00')
    try:
        if s.isdigit():
            x=int(s); x=x/1000 if x>10**12 else x
            return datetime.fromtimestamp(x,tz=timezone.utc)
        d=datetime.fromisoformat(s); return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except Exception:return None

def main():
    exists=IN.exists(); rows=[]; malformed=0
    if exists:
        with IN.open(newline='') as f:
            r=csv.DictReader(f); fields=r.fieldnames or []
            tcol=next((x for x in fields if x.lower() in ('timestamp','open_time','datetime','date','time')),None)
            ccol=next((x for x in fields if x.lower()=='close'),None)
            if tcol and ccol:
                for x in r:
                    dt=parse_ts(x.get(tcol,''))
                    try:c=float(x.get(ccol,'')); ok=math.isfinite(c) and c>0
                    except Exception:ok=False
                    if dt is None: malformed+=1; continue
                    if START<=dt.date()<=END and ok: rows.append((dt,c))
    rows.sort(key=lambda z:z[0]); ts=[x[0] for x in rows]
    dup=len(ts)-len(set(ts)); increasing=all(a<b for a,b in zip(ts,ts[1:])); future=any(x.date()>END for x in ts)
    byday=defaultdict(list)
    for (a,pa),(b,pb) in zip(rows,rows[1:]):
        if b.date()!=a.date() and b.hour==0: pass
        if b.date()>=START and b.date()<=END and pa>0 and pb>0: byday[b.date()].append(math.log(pb/pa))
    eligible=[]
    for d,rr in sorted(byday.items()):
        if len(rr)>=23:
            rv=math.sqrt(sum(x*x for x in rr))
            if math.isfinite(rv): eligible.append(d)
    represented=len(byday); coverage=len(eligible)/represented if represented else 0.0
    manifest=('\n'.join(d.isoformat() for d in eligible)+('\n' if eligible else '')).encode()
    gates={'canonical_exists':exists,'eligible_days_gte_1000':len(eligible)>=1000,'finite_day_coverage_gte_95pct':coverage>=.95,'zero_duplicate_timestamps':dup==0,'strictly_increasing':increasing,'zero_future_training_rows':not future,'zero_malformed_timestamps':malformed==0}
    passed=all(gates.values())
    out={'engine':'V98 Independent','phase':'129','mode':'DATA_ONLY','family':'BTC realized volatility','window':{'start':str(START),'end':str(END)},'integrity':{'input_rows':len(rows),'represented_days':represented,'eligible_days':len(eligible),'eligible_day_coverage':coverage,'duplicate_timestamps':dup,'malformed_timestamps':malformed,'eligible_date_manifest_sha256':sha(manifest)},'gates':gates,'decision':'PASS_DATA_ONLY' if passed else 'FAIL_DATA_NO_ALPHA','numeric_values_exposed':False,'alpha_or_pnl_inspected':False,'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'phase083_selection_use':False,'parameter_search':False,'rescue_allowed':False,'prereg_sha256':sha(PREREG.read_bytes())}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':'129','decision':out['decision'],'integrity':out['integrity'],'gates':gates},sort_keys=True))
if __name__=='__main__':main()

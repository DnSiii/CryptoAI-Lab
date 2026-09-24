#!/usr/bin/env python3
"""V98 Independent Phase133: cross-asset jump-breadth DATA_ONLY gate. Emits no return/jump/feature values."""
from __future__ import annotations
import csv, hashlib, json, math
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT')
ROOT=Path('data/canonical'); OUT=Path('reports/v98_independent_phase133_cross_asset_jump_breadth_data_only.json')
PREREG=Path('reports/v98_independent_phase133_cross_asset_jump_breadth_data_only_prereg.md')
START=datetime(2023,1,1,tzinfo=timezone.utc); END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def parse_ts(s):
    try:
        d=datetime.fromisoformat(str(s).strip().replace('Z','+00:00'))
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except Exception:return None

def main():
    per={}; daysets={}; all_exist=True; schema_ok=True; future_total=0; malformed_total=0
    for a in ASSETS:
        p=ROOT/f'{a}_1h.csv'; all_exist &= p.exists(); byday={}; malformed=dup=future=0; seen=set(); ordered=True; prev=None
        if p.exists():
            with p.open(newline='') as f:
                r=csv.DictReader(f); fields=r.fieldnames or []; schema_ok &= ('timestamp' in fields and 'close' in fields)
                if 'timestamp' in fields and 'close' in fields:
                    for x in r:
                        dt=parse_ts(x.get('timestamp',''))
                        if dt is None: malformed+=1; continue
                        if dt in seen: dup+=1
                        seen.add(dt)
                        if prev is not None and dt<=prev: ordered=False
                        prev=dt
                        if dt>END: future+=1; continue
                        if dt<START: continue
                        try: finite=math.isfinite(float(x.get('close','')))
                        except Exception: finite=False
                        if finite: byday[dt.date()]=byday.get(dt.date(),0)+1
        # N finite closes imply at least N-1 finite close-to-close returns; require >=24 closes => >=23 returns.
        days={d for d,n in byday.items() if n>=24}
        daysets[a]=days; future_total+=future; malformed_total+=malformed
        per[a]={'eligible_asset_days':len(days),'duplicate_timestamps':dup,'malformed_timestamps':malformed,'strictly_increasing':ordered}
    total_days=(END.date()-START.date()).days+1
    eligible=[]
    d=START.date()
    while d<=END.date():
        if sum(d in daysets[a] for a in ASSETS)>=4: eligible.append(d)
        d+=timedelta(days=1)
    coverage=len(eligible)/total_days
    manifest=('\n'.join(x.isoformat() for x in eligible)+('\n' if eligible else '')).encode()
    gates={'all_five_files_exist':all_exist,'schema_ok':schema_ok,'eligible_days_gte_1000':len(eligible)>=1000,'calendar_coverage_gte_95pct':coverage>=.95,'zero_duplicate_timestamps':all(x['duplicate_timestamps']==0 for x in per.values()),'strictly_increasing_per_asset':all(x['strictly_increasing'] for x in per.values()),'zero_malformed_timestamps':malformed_total==0,'zero_future_training_rows':future_total==0}
    passed=all(gates.values())
    out={'engine':'V98 Independent','phase':'133','mode':'DATA_ONLY','family':'cross-asset jump breadth','window':{'start':START.isoformat(),'end':END.isoformat()},'integrity':{'per_asset':per,'calendar_days':total_days,'eligible_day_count':len(eligible),'eligible_calendar_coverage':coverage,'eligible_day_manifest_sha256':sha(manifest)},'gates':gates,'decision':'PASS_DATA_ONLY' if passed else 'FAIL_DATA_NO_ALPHA','feature_values_exposed':False,'returns_or_jump_values_exposed':False,'alpha_or_pnl_inspected':False,'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'phase083_selection_use':False,'parameter_search':False,'rescue_allowed':False,'prereg_sha256':sha(PREREG.read_bytes())}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':'133','decision':out['decision'],'eligible_day_count':len(eligible),'coverage':coverage,'gates':gates},sort_keys=True))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""V98 Independent Phase131: cross-asset funding dispersion DATA_ONLY gate. Emits no funding values."""
from __future__ import annotations
import csv, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT')
ROOT=Path('data/canonical'); OUT=Path('reports/v98_independent_phase131_funding_dispersion_data_only.json')
PREREG=Path('reports/v98_independent_phase131_funding_dispersion_data_only_prereg.md')
START=datetime(2023,1,1,tzinfo=timezone.utc); END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def parse_ts(s):
    try:
        d=datetime.fromisoformat(str(s).strip().replace('Z','+00:00'))
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except Exception:return None

def main():
    sets={}; per={}; malformed_total=0; future_total=0; all_exist=True; schema_ok=True
    for a in ASSETS:
        p=ROOT/f'{a}_funding.csv'; all_exist &= p.exists(); vals=set(); malformed=dup=future=0
        if p.exists():
            with p.open(newline='') as f:
                r=csv.DictReader(f); fields=r.fieldnames or []; schema_ok &= ('timestamp' in fields and 'funding_rate' in fields)
                if 'timestamp' in fields and 'funding_rate' in fields:
                    seen=set()
                    for x in r:
                        dt=parse_ts(x.get('timestamp',''))
                        if dt is None: malformed+=1; continue
                        if dt>END: future+=1; continue
                        if dt<START: continue
                        if dt in seen: dup+=1
                        seen.add(dt)
                        try:v=float(x.get('funding_rate','')); finite=math.isfinite(v)
                        except Exception:finite=False
                        if finite: vals.add(dt)
        sets[a]=vals; malformed_total+=malformed; future_total+=future
        per[a]={'finite_event_count':len(vals),'duplicate_timestamps':dup,'malformed_timestamps':malformed,'strictly_increasing_after_parse':True}
    union=set().union(*sets.values()) if sets else set()
    eligible=sorted(t for t in union if sum(t in sets[a] for a in ASSETS)>=4)
    coverage=len(eligible)/len(union) if union else 0.0
    manifest=('\n'.join(t.isoformat() for t in eligible)+('\n' if eligible else '')).encode()
    gates={'all_five_files_exist':all_exist,'schema_ok':schema_ok,'eligible_timestamps_gte_3000':len(eligible)>=3000,'eligible_union_coverage_gte_90pct':coverage>=.90,'zero_duplicate_timestamps':all(x['duplicate_timestamps']==0 for x in per.values()),'zero_malformed_timestamps':malformed_total==0,'zero_future_training_rows':future_total==0}
    passed=all(gates.values())
    out={'engine':'V98 Independent','phase':'131','mode':'DATA_ONLY','family':'cross-asset funding dispersion','window':{'start':START.isoformat(),'end':END.isoformat()},'integrity':{'per_asset':per,'union_event_count':len(union),'eligible_timestamp_count':len(eligible),'eligible_union_coverage':coverage,'eligible_timestamp_manifest_sha256':sha(manifest)},'gates':gates,'decision':'PASS_DATA_ONLY' if passed else 'FAIL_DATA_NO_ALPHA','numeric_values_exposed':False,'alpha_or_pnl_inspected':False,'validation':None,'final_holdout':None,'v16_used':False,'v99_used':False,'phase083_selection_use':False,'parameter_search':False,'rescue_allowed':False,'prereg_sha256':sha(PREREG.read_bytes())}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':'131','decision':out['decision'],'eligible_timestamp_count':len(eligible),'coverage':coverage,'gates':gates},sort_keys=True))
if __name__=='__main__':main()

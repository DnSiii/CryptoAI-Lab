#!/usr/bin/env python3
"""V98 OB source-only authentication and causal structural gate. Not an independent PnL oracle."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from ob_sources import bundle,synthetic_causality,NAMES
def check(d):
    synthetic_causality()
    raw,updates,active=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    times=np.flatnonzero(updates[:,1])
    coretimes=np.flatnonzero(updates[:,0])
    expected=np.arange(WARMUP,HOURS,336)
    failures=[]
    if not np.array_equal(times,expected) or not np.all(updates[times,1:]):
        failures.append('OB_DECISION_CALENDAR')
    if not np.array_equal(coretimes,np.arange(WARMUP,HOURS,672)):
        failures.append('OB_CORE_DECISION_CALENDAR')
    if int(d['event'].sum())!=9144:failures.append('OB_FUNDING_EVENTS')
    if np.any(np.abs(raw[:,0]).sum(axis=1)>.80+1e-10):
        failures.append('OB_CORE_BUDGET')
    if np.any((np.abs(np.diff(raw,axis=0)).sum(axis=(1,2))>1e-12)&~updates[1:,0]):
        failures.append('OB_SILENT_TARGET_CHANGE')
    if not np.isfinite(raw).all():failures.append('OB_NONFINITE')
    counts={str(year):{name:int(active[times[(times>=lo)&(times<hi)],i].sum()) for i,name in enumerate(NAMES)}
            for year,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'source_hours':HOURS,'decision_count':len(times),'core_decision_count':len(coretimes),
        'funding_events':int(d['event'].sum()),'raw_active_decision_counts':counts,
        'synthetic_future_mutation_pass':True,'pnl_computed':False,
        'training_only':True,'holdout_accessed':False}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();out=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['decision']=='PASS_SOURCE_ONLY' else 2)

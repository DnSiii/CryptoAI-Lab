#!/usr/bin/env python3
"""MI independent full-hour source-only oracle; no system PnL or holdout access."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mi_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES
MINIMUM=(6,4,3)
def independent(d):
    p=np.log(d['c']);q=d['q']
    weights=np.zeros((HOURS,4,4))
    events=np.zeros((HOURS,3),bool)
    refresh=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    due=[-1,-1,-1]
    for hour in range(WARMUP,HOURS):
        elapsed=hour-WARMUP
        good=bool((q[hour-671:hour+1]>0).all())
        r672=p[hour]-p[hour-672]
        r336=p[hour]-p[hour-336]
        r168=p[hour]-p[hour-168]
        r72=p[hour]-p[hour-72]
        breadth=int((r168>0).sum())
        expired=[False,False,False]
        for k in range(3):
            if due[k]>=0 and hour>=due[k]:
                due[k]=-1
                state[k+1]=0
                expired[k]=True
        if good and elapsed%672==0:
            state[0]=[.54,0,0,0]
            refresh[hour]=True
        if good and elapsed%336==0 and due[0]<0 and not expired[0]:
            if r672[0]>0 and r168[0]>0:
                state[1]=[.12,0,0,0]
                due[0]=hour+336
                events[hour,0]=True
        if good and elapsed%336==0 and due[1]<0 and not expired[1]:
            best=int(np.argmax(r672[1:]-r672[0]))+1
            if r672[best]-r672[0]>0 and r168[best]>0 and r672[0]>0:
                state[2,best]=.12
                due[1]=hour+336
                events[hour,1]=True
        if good and elapsed%168==0 and due[2]<0 and not expired[2]:
            if r336[0]<0 and r72[0]>0 and int((r72>0).sum())>=2:
                state[3,0]=.10
                due[2]=hour+168
                events[hour,2]=True
        z=state.copy()
        z[1:3]*=(4+breadth)/8
        z[3]*=(8-breadth)/8
        optional=float(np.abs(z[1:]).sum())
        if optional>0:
            z[1:]*=min(1.,max(0.,(.88-float(np.abs(z[0]).sum()))/optional))
        weights[hour]=z
    return weights,events,refresh
def check(d):
    a=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    synthetic_causality()
    b,entries,refresh=independent(d)
    mismatches=int(np.count_nonzero(np.abs(a[0]-b)>1e-12))
    event_mismatches=int(np.count_nonzero(a[2]!=entries))
    silent=int(np.count_nonzero((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]))
    missing_refresh=int(np.count_nonzero(refresh&~a[1][:,0]))
    invalid=int(np.count_nonzero(a[2][~a[3]]))
    counts={str(y):{n:int(a[2][lo:hi,k].sum()) for k,n in enumerate(NAMES)}
            for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    gross=float(np.abs(a[0]).sum(axis=(1,2)).max())
    failures=[]
    if mismatches or event_mismatches:failures.append('INDEPENDENT_SOURCE_MISMATCH')
    if silent or missing_refresh:failures.append('SILENT_OR_MISSING_FORCED_REFRESH')
    if invalid:failures.append('INVALID_SOURCE_ENTRY')
    if gross>.88+1e-10:failures.append('TARGET_GROSS')
    if any(counts[str(y)][name]<MINIMUM[k] for y in (2023,2024)
           for k,name in enumerate(NAMES)):failures.append('ACTIVATION_MINIMUM')
    if int(d['event'].sum())!=9144:failures.append('NATIVE_FUNDING_EVENTS')
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
            'failures':failures,'counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
            'independent_hourly_weight_mismatches':mismatches,
            'independent_entry_mismatches':event_mismatches,
            'silent_updates':silent,'missing_forced_core_refreshes':missing_refresh,
            'forced_core_refreshes':int(refresh.sum()),'invalid_entries':invalid,
            'intended_gross_peak':gross,'native_funding_events':int(d['event'].sum()),
            'training_only':True,'pnl_computed':False,'holdout_accessed':False,
            'synthetic_future_mutation_pass':True}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args()
    r=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps(r,indent=2,sort_keys=True))
    raise SystemExit(0 if r['decision']=='PASS_SOURCE_ONLY' else 2)

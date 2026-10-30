#!/usr/bin/env python3
"""V98 NT independent source decision reconstruction. Source-only, no PnL/holdout."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nt_sources import bundle

def oracle(d):
    actual,updates,active=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    expected=np.zeros((4,4),float)
    mismatches=[];checked=0
    decisions=range(WARMUP,HOURS,168)
    for t in decisions:
        expected[:]=0.
        r336=[math.log(float(d['c'][t,j]/d['c'][t-336,j])) for j in range(4)]
        hi=[max(float(z) for z in d['h'][t-671:t+1,j]) for j in range(4)]
        lo=[min(float(z) for z in d['l'][t-671:t+1,j]) for j in range(4)]
        loc=[min(1.,max(0.,(float(d['c'][t,j])-lo[j])/max(hi[j]-lo[j],1e-12))) for j in range(4)]
        qualified=[j for j in range(4) if r336[j]>0 and loc[j]>.65]
        if qualified:
            scores=[(loc[j]-.5)*max(r336[j],0.) for j in range(4)]
            winner=min(qualified,key=lambda j:(-scores[j],j))
            expected[0,winner]=.70
        elif r336[0]<-.10 and loc[0]<.35:
            expected[0,0]=-.35
        r168=[math.log(float(d['c'][t,j]/d['c'][t-168,j])) for j in range(4)]
        r24=[math.log(float(d['c'][t,j]/d['c'][t-24,j])) for j in range(4)]
        r48=[math.log(float(d['c'][t,j]/d['c'][t-48,j])) for j in range(4)]
        qualified=[j for j in range(4) if r168[j]>0 and r24[j]<0 and d['rate'][t,j]<0]
        if qualified:
            winner=min(qualified,key=lambda j:(-r168[j],j))
            expected[1,winner]=.16
        ranked=sorted((1,2,3),key=lambda j:(r168[j]-r168[0],j))
        if (r168[ranked[-1]]-r168[ranked[0]])>=.10:
            # tie convention matches explicit highest tie-by-index.
            high_j=min((1,2,3),key=lambda j:(-(r168[j]-r168[0]),j))
            low_j=min((1,2,3),key=lambda j:((r168[j]-r168[0]),j))
            expected[2,high_j]=.12
            expected[2,low_j]=-.12
        rs=[math.log(float(d['c'][k,0]/d['c'][k-1,0])) for k in range(t-335,t+1)]
        def stdev(a):
            mean=sum(a)/len(a)
            return math.sqrt(sum((x-mean)**2 for x in a)/len(a))
        if r24[0]<-.055 and stdev(rs[-24:])>1.4*stdev(rs):
            expected[3,0]=-.14
        elif r168[0]<-.12 and r48[0]>.045:
            expected[3,0]=.14
        risk_on=r336[0]>0 and sum(x>0 for x in r336)>=3
        expected[1:]*=np.array([1.,1.,.5] if risk_on else [.75,.75,1.])[:,None]
        error=float(np.max(np.abs(expected-actual[t])))
        if error>1e-10 or not updates[t].all():
            mismatches.append({'t':t,'error':error})
        checked+=1
    if checked!=105 or mismatches:
        raise ValueError('NT_INDEPENDENT_SOURCE_DECISION_MISMATCH_'+str(mismatches[:5]))
    if int(d['event'].sum())!=9144 or np.any(updates[:WARMUP]) or int(updates[:,0].sum())!=105:
        raise ValueError('NT_INDEPENDENT_SOURCE_CALENDAR')
    if np.any(np.abs(np.diff(actual,axis=0)).sum(axis=(1,2))>1e-12 & ~updates[1:,0]):
        raise ValueError('NT_INDEPENDENT_SOURCE_SILENT_TARGET_CHANGE')
    return {'decision':'PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL','independent_decisions':checked,
            'source_hours':HOURS,'funding_events':int(d['event'].sum()),
            'raw_target_mismatches':0,'independent_math':True,
            'uses_only_2023_2024_development':True,'2025_validation_accessed':False,
            'future_holdout_accessed':False,'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    out=oracle(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

#!/usr/bin/env python3
"""LI independent native source-only gate; computes event counts without LI signal import."""
import json
import numpy as np
from ko_source import load,HOURS,WARMUP
from li_sources import bundle,static_check,NAMES

def independent_counts(frames):
    o,h,l,c,q,r,e=frames[:7];lc=np.log(c)
    out=np.zeros((HOURS,3),bool);expiry=[-1]*3
    for t in range(WARMUP,HOURS):
        if not np.all(q[t-167:t+1]>0):continue
        a=lc[t]-lc[t-168];b=lc[t]-lc[t-72];d=lc[t]-lc[t-24]
        m168=float(np.median(a));m72=float(np.median(b))
        state='STRESS' if m72<0 else 'RECOVERY' if m168<0 and m72>0 else 'RISK_ON' if m168>0 else 'RANGE'
        if (t-WARMUP)%96==0 and state=='RISK_ON' and t>expiry[0]:
            if np.any((a>0)&(d>0)):
                out[t,0]=True;expiry[0]=t+96
        if (t-WARMUP)%168==0 and state in ('RISK_ON','RECOVERY') and t>expiry[1]:
            f=(r[t-167:t+1]*e[t-167:t+1]).sum(axis=0)
            if f.max()-f.min()>.0005:
                out[t,1]=True;expiry[1]=t+168
        if (t-WARMUP)%96==0 and state in ('STRESS','RECOVERY') and t>expiry[2]:
            out[t,2]=True;expiry[2]=t+96
    return out

def run(root):
    assert static_check()
    frames,manifest=load(root)
    source=bundle(*frames[:7]);intents,updates,entries,valid,regimes=source
    independent=independent_counts(frames)
    mismatches=int(np.any(entries!=independent,axis=1).sum())
    counts={yr:{nm:int(entries[lo:hi,j].sum()) for j,nm in enumerate(NAMES)} for yr,lo,hi in [('2023',744,9504),('2024',9504,HOURS)]}
    failures=[]
    if mismatches:failures.append('INDEPENDENT_MISMATCH')
    for yr in counts:
        for nm,num in counts[yr].items():
            if num<8:failures.append('LOW_'+yr+'_'+nm)
    if np.any(entries[~valid]):failures.append('INVALID_QUOTE_ENTRY')
    if np.any(np.abs(intents).sum(axis=(1,2))>.98+1e-9):failures.append('HIDDEN_GROSS')
    if np.any(np.any(np.diff(intents,axis=0)!=0,axis=2)&~updates[1:]):failures.append('SILENT_UPDATE')
    frames2=[z.copy() for z in frames[:7]]
    for z in frames2[:4]:z[14000:]*=1.3
    frames2[4][14000:]*=2;frames2[5][14000:]*=-1
    source2=bundle(*frames2)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(source,source2)):
        failures.append('FUTURE_LEAK')
    return {'architecture':'LI','training_only':True,'source_only':True,'system_pnl_computed':False,
            'hours':HOURS,'native_funding_events':int(frames[6].sum()),'manifest':manifest,
            'counts':counts,'independent_entry_mismatches':mismatches,
            'real_future_mutation_prefix_hours':14000,
            'max_intended_gross':float(np.abs(intents).sum(axis=(1,2)).max()),
            'failures':failures,'decision':'PASS_SOURCE_ONLY' if not failures else 'REJECT_SOURCE_ONLY'}

if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();rec=run(a.root)
    Path(a.output).write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
    print(rec['decision'],rec['counts'],rec['failures'])
    raise SystemExit(0 if not rec['failures'] else 2)

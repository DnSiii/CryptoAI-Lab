#!/usr/bin/env python3
"""Independent LC Opportunity source-entry oracle; no LC module import, no PnL."""
from __future__ import annotations
import json
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS

def main():
    frames,_=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    assert len(c)==HOURS==18288
    lc=np.log(c)
    expiry=-1
    counts={'2023':0,'2024':0}
    events=[]
    for t in range(744,HOURS,168):
        if not np.all(q[t-671:t+1]>0):continue
        if expiry>=0 and t>=expiry:
            expiry=-1
            continue
        if expiry>=0:continue
        r336=lc[t]-lc[t-336]
        r24=lc[t]-lc[t-24]
        r6=lc[t]-lc[t-6]
        if np.median(r336)<=0:continue
        eligible=(r336>0)&(r24<0)&(r6>0)
        if not eligible.any():continue
        j=int(np.argmin(np.where(eligible,r24,np.inf)))
        counts['2023' if t<9504 else '2024']+=1
        events.append([int(t),int(j)])
        expiry=t+168
    report={'independent':True,'pnl_computed':False,
            'opportunity_counts':counts,'events_hour_asset_index':events,
            'decision':'CONFIRM_LC_2024_SOURCE_FAILURE' if
            counts=={'2023':8,'2024':6} else 'SOURCE_DISAGREEMENT'}
    print(json.dumps(report,sort_keys=True))
    return report
if __name__=='__main__':
    raise SystemExit(0 if main()['decision']=='CONFIRM_LC_2024_SOURCE_FAILURE' else 2)

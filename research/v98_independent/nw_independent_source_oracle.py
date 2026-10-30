#!/usr/bin/env python3
"""V98 NW independently recomputed price indicators and target decisions."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nw_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    checked=0
    for t in range(WARMUP,HOURS,336):
        target=np.zeros((4,4))
        def ret(j,k):return math.log(float(d['c'][t,j]/d['c'][t-k,j]))
        r336=[ret(j,336) for j in range(4)]
        r168=[ret(j,168) for j in range(4)]
        r72=[ret(j,72) for j in range(4)]
        r24=[ret(j,24) for j in range(4)]
        av=[math.fsum(float(d['c'][i,j]) for i in range(t-167,t+1))/168 for j in range(4)]
        good=[j for j in range(4) if r336[j]>0 and r168[j]>0 and float(d['c'][t,j])>av[j]]
        good.sort(key=lambda j:(-r336[j],j))
        if good:
            target[0,good[0]]=.72
            if len(good)>1:target[0,good[1]]=.08
        elif r168[0]<-.04 and float(d['c'][t,0])<math.fsum(float(d['c'][i,0]) for i in range(t-335,t+1))/336:
            target[0,0]=-.52
        now=[];prior=[]
        for j in range(4):
            now.append(math.fsum((float(d['h'][i,j])-float(d['l'][i,j]))/float(d['c'][i,j]) for i in range(t-71,t+1))/72)
            prior.append(math.fsum((float(d['h'][i,j])-float(d['l'][i,j]))/float(d['c'][i,j]) for i in range(t-239,t-71))/168)
        good=[j for j in range(4) if float(d['c'][t,j])>max(float(d['h'][i,j]) for i in range(t-168,t))
              and r72[j]>0 and now[j]<.90*prior[j]]
        if good:
            j=min(good,key=lambda k:(-r72[k],k))
            target[1,j]=.18
        btc=[math.log(float(d['c'][i,0]/d['c'][i-1,0])) for i in range(t-335,t+1)]
        mean_b=math.fsum(btc)/336
        vb=math.fsum((x-mean_b)**2 for x in btc)/336
        residual={}
        for j in (1,2,3):
            rr=[math.log(float(d['c'][i,j]/d['c'][i-1,j])) for i in range(t-335,t+1)]
            mean_r=math.fsum(rr)/336
            cov=math.fsum((rr[i]-mean_r)*(btc[i]-mean_b) for i in range(336))/336
            beta=max(0.,min(2.,cov/max(vb,1e-12)))
            residual[j]=r72[j]-beta*r72[0]
        worst=min((1,2,3),key=lambda j:(residual[j],j))
        best=min((1,2,3),key=lambda j:(-residual[j],j))
        if worst!=best and residual[best]-residual[worst]>.035:
            target[2,worst]=.12
            target[2,best]=-.12
        drawdown=1.-float(d['c'][t,0])/max(float(d['h'][i,0]) for i in range(t-336,t))
        if drawdown>.12 and r24[0]>.015:target[3,0]=.18
        elif drawdown>.12 and r24[0]<-.07:target[3,0]=-.18
        risk_on=r168[0]>0 and sum(v>0 for v in r168)>=2
        target[1:]*=np.array([1.,.7,.5] if risk_on else [.65,.8,1.])[:,None]
        err=float(np.max(np.abs(raw[t]-target)))
        if err>1e-9 or not updates[t].all():
            raise ValueError('NW_INDEPENDENT_SOURCE_MISMATCH_'+str(t)+'_'+str(err))
        checked+=1
    if checked!=53 or int(updates[:,0].sum())!=53 or int(d['event'].sum())!=9144:
        raise ValueError('NW_INDEPENDENT_SOURCE_CALENDAR')
    return {'decision':'PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL','decisions':checked,
            'source_hours':HOURS,'funding_events':9144,'raw_target_mismatches':0,
            '2025_validation_accessed':False,'future_holdout_accessed':False,'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

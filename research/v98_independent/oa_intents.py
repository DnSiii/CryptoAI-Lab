#!/usr/bin/env python3
"""V98 OA: causal weekly six-completed-window net-growth allocator; no optimizer grid."""
import math
import numpy as np
from oa_sources import HOURS,WARMUP,STEP
LOOKBACK=6
CAP=.84
WEIGHT=np.arange(1,7,dtype=float)/21.
def shadow_history(raw,o,c,t):
    if raw.shape!=(HOURS,4,4) or o.shape!=(HOURS,4) or c.shape!=(HOURS,4):
        raise ValueError("OA_SHADOW_SHAPE")
    if (t-WARMUP)%STEP or t<WARMUP or t>=HOURS:
        raise ValueError("OA_SHADOW_TIME")
    if t<WARMUP+LOOKBACK*STEP:
        return np.zeros((4,LOOKBACK)),False
    hist=np.zeros((4,LOOKBACK))
    for k in range(LOOKBACK):
        start=t-(LOOKBACK-k)*STEP
        end=start+STEP
        if start<WARMUP or end>t:raise ValueError("OA_SHADOW_FUTURE")
        change=c[end]/o[start+1]-1.
        for i in range(4):
            w=raw[start,i]
            gross=float(np.abs(w).sum())
            if gross==0:continue
            gain=float(np.dot(w,change))
            if gain<=-1 or not math.isfinite(gain):
                raise ValueError("OA_SHADOW_INSOLVENT")
            hist[i,k]=math.log1p(gain)/gross
    return hist,True
def allocate(raw,previous_net,history,funding,ready):
    raw=np.asarray(raw,float);previous_net=np.asarray(previous_net,float)
    history=np.asarray(history,float);funding=np.asarray(funding,float)
    if raw.shape!=(4,4) or previous_net.shape!=(4,) or history.shape!=(4,6) or funding.shape!=(21,4):
        raise ValueError("OA_ALLOC_SHAPE")
    if not all(np.isfinite(z).all() for z in (raw,previous_net,history,funding)):
        raise ValueError("OA_ALLOC_NONFINITE")
    held=np.zeros((4,4))
    held[0]=raw[0]
    used=float(np.abs(held).sum())
    if used>CAP+1e-10:raise ValueError("OA_ALLOC_CORE_GROSS")
    scores=[]
    if ready:
        meanrate=funding.mean(axis=0)
        for i in (1,2,3):
            w=raw[i];gross=float(np.abs(w).sum())
            if gross<=1e-12:continue
            historical=float(np.dot(history[i],WEIGHT))
            carry=float(21*np.dot(w,meanrate)/gross)
            turnover=float(np.abs(w).sum()/gross)*.0006
            score=historical-carry-turnover
            if score>.002:
                scores.append((score,i))
    scores.sort(key=lambda x:(-x[0],x[1]))
    chosen=0
    for score,i in scores:
        if chosen>=2:break
        remaining=CAP-used
        if remaining<=1e-12:break
        gross=float(np.abs(raw[i]).sum())
        factor=min(1.,remaining/gross)
        if factor<=1e-12:continue
        held[i]=raw[i]*factor
        used+=gross*factor
        chosen+=1
    net=held.sum(axis=0)
    if used>CAP+1e-9 or np.abs(net).sum()>used+1e-9:
        raise ValueError("OA_ALLOC_GROSS")
    return held,net,{'chosen':chosen,'candidate_count':len(scores),
                     'ready':bool(ready),'virtual_gross':used}
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):
        raise ValueError("OA_INTENTS_SHAPE")
    result=np.zeros_like(raw)
    held=np.zeros((4,4));old=np.zeros(4)
    counts={"Opportunity":0,"Relative_Value":0,"Stress_Recovery":0}
    decisions=ready_decisions=0
    for t in range(WARMUP,HOURS):
        if updates[t,0]:
            if not updates[t].all() or t%8 or not d['event'][t-160:t+1:8].all():
                raise ValueError("OA_INTENTS_CALENDAR")
            history,ready=shadow_history(raw,d['o'],d['c'],t)
            funding=d['rate'][t-160:t+1:8]
            held,old,diag=allocate(raw[t],old,history,funding,ready)
            if not ready and np.any(np.abs(held[1:])>1e-12):
                raise ValueError("OA_PREMATURE_SHADOW")
            ready_decisions+=int(ready)
            for i,name in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[name]+=1
            decisions+=1
        result[t]=held
    if decisions!=105 or ready_decisions!=99:
        raise ValueError("OA_INTENTS_DECISION_COUNT")
    return {'weights':result,'allocation_decisions':decisions,
            'shadow_ready_decisions':ready_decisions,
            'activated_week_counts':counts,'causal_t_minus_one':True,
            'funding_future_used':False,'training_or_holdout_read_by_allocator':False}
def synthetic_tests():
    from oa_sources import synthetic_causality,bundle
    synthetic_causality()
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    d={'o':o,'h':h,'l':l,'c':c,'q':q,'rate':rate,'event':event}
    raw,updates,_=bundle(o,h,l,c,q,rate,event)
    a=build(d,raw,updates)
    changed={k:v.copy() for k,v in d.items()}
    for k in ('o','h','l','c'):changed[k][14000:]*=1.7
    changed['rate'][14000:]*=-1.
    new_raw,new_updates,_=bundle(*(changed[k] for k in ('o','h','l','c','q','rate','event')))
    b=build(changed,new_raw,new_updates)
    if not np.array_equal(a['weights'][:14000],b['weights'][:14000]):
        raise AssertionError("OA_INTENTS_FUTURE_LEAK")
    trial=np.zeros((4,4));trial[0,0]=.60;trial[1,1]=.16;trial[2,1]=.09;trial[2,2]=-.09
    hist=np.zeros((4,6));hist[1]=.02;hist[2]=.03
    out,net,diag=allocate(trial,np.zeros(4),hist,np.zeros((21,4)),True)
    assert diag['chosen']==2 and abs(diag['virtual_gross']-.84)<1e-9
    assert np.abs(net).sum()<=diag['virtual_gross']+1e-9
    assert np.abs(allocate(trial,np.zeros(4),hist,np.zeros((21,4)),False)[0][1:]).sum()==0
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print("OA_WEEKLY_ALLOCATOR_CAUSAL_SYNTHETIC_PASS_NOT_PNL")

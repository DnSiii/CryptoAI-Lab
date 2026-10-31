#!/usr/bin/env python3
"""V98 OB causal two-clock allocator: persistent core, one carry-confirmed sleeve."""
import math
import numpy as np
from ob_sources import HOURS,WARMUP,STEP
CAP=.84
def completed_shadows(raw,o,c,t):
    if raw.shape!=(HOURS,4,4) or o.shape!=(HOURS,4) or c.shape!=(HOURS,4):
        raise ValueError("OB_SHADOW_SHAPE")
    if t<WARMUP or t>=HOURS or (t-WARMUP)%STEP:
        raise ValueError("OB_SHADOW_TIME")
    if t<WARMUP+4*STEP:return np.zeros((4,4)),False
    hist=np.zeros((4,4))
    for k in range(4):
        start=t-(4-k)*STEP
        end=start+STEP
        if start<WARMUP or end>t:raise ValueError("OB_SHADOW_FUTURE")
        change=c[end]/o[start+1]-1.
        for i in range(4):
            w=raw[start,i];gross=float(np.abs(w).sum())
            if gross<=1e-12:continue
            pnl=float(np.dot(w,change))
            if pnl<=-1 or not math.isfinite(pnl):raise ValueError("OB_SHADOW_INSOLVENT")
            hist[i,k]=math.log1p(pnl)/gross
    return hist,True
def allocate(raw,shadow,funding,ready):
    raw=np.asarray(raw,float);shadow=np.asarray(shadow,float);funding=np.asarray(funding,float)
    if raw.shape!=(4,4) or shadow.shape!=(4,4) or funding.shape!=(21,4):
        raise ValueError("OB_ALLOC_SHAPE")
    if not all(np.isfinite(z).all() for z in (raw,shadow,funding)):
        raise ValueError("OB_ALLOC_NONFINITE")
    held=np.zeros((4,4));held[0]=raw[0]
    gross=float(np.abs(held[0]).sum())
    if gross>CAP+1e-10:raise ValueError("OB_CORE_CAP")
    candidates=[]
    if ready:
        meanrate=funding.mean(axis=0)
        for i in (1,2,3):
            w=raw[i];size=float(np.abs(w).sum())
            if size<=1e-12:continue
            positive=int(np.count_nonzero(shadow[i]>0))
            historical=float(np.dot(shadow[i],np.array([.1,.2,.3,.4])))
            carry=42*float(np.dot(w,meanrate))/size
            score=historical-carry-.0006
            if positive>=2 and score>.005:candidates.append((score,i))
    candidates.sort(key=lambda x:(-x[0],x[1]))
    chosen=None
    if candidates and gross<CAP-1e-12:
        score,i=candidates[0]
        size=float(np.abs(raw[i]).sum())
        held[i]=raw[i]*min(1.,(CAP-gross)/size)
        chosen=i
    total=float(np.abs(held).sum());net=held.sum(axis=0)
    if total>CAP+1e-10 or float(np.abs(net).sum())>total+1e-10:
        raise ValueError("OB_ALLOC_HIDDEN_LEVERAGE")
    return held,{'chosen':chosen,'virtual_gross':total,'ready':bool(ready)}
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):
        raise ValueError("OB_INTENTS_SHAPE")
    result=np.zeros_like(raw);held=np.zeros((4,4))
    counts={"Opportunity":0,"Relative_Value":0,"Stress_Recovery":0}
    decisions=ready_decisions=core_decisions=0
    for t in range(WARMUP,HOURS):
        if updates[t,1]:
            if not updates[t,1:].all() or t%8 or not d['event'][t-160:t+1:8].all():
                raise ValueError("OB_INTENTS_CALENDAR")
            history,ready=completed_shadows(raw,d['o'],d['c'],t)
            candidate,diag=allocate(raw[t],history,d['rate'][t-160:t+1:8],ready)
            if updates[t,0]:
                held[0]=candidate[0]
                core_decisions+=1
            held[1:]=candidate[1:]
            if not ready and np.any(np.abs(held[1:])>1e-12):
                raise ValueError("OB_PREMATURE_SHADOW")
            ready_decisions+=int(ready)
            for i,name in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[name]+=1
            decisions+=1
        result[t]=held
    if decisions!=53 or core_decisions!=27 or ready_decisions!=49:
        raise ValueError("OB_INTENTS_DECISION_COUNT")
    return {'weights':result,'allocation_decisions':decisions,'core_decisions':core_decisions,
            'shadow_ready_decisions':ready_decisions,'activated_period_counts':counts,
            'causal_t_minus_one':True,'funding_future_used':False,
            'training_or_holdout_read_by_allocator':False}
def synthetic_tests():
    from ob_sources import synthetic_causality,bundle
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
        raise AssertionError("OB_INTENTS_FUTURE_LEAK")
    trial=np.zeros((4,4));trial[0,0]=.6;trial[1,1]=.16
    hist=np.zeros((4,4));hist[1]=.02
    out,diag=allocate(trial,hist,np.zeros((21,4)),True)
    assert diag['chosen']==1 and abs(diag['virtual_gross']-.76)<1e-9
    out,diag=allocate(trial,hist,np.zeros((21,4)),False)
    assert diag['chosen'] is None and np.abs(out[1:]).sum()==0
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print("OB_TWO_CLOCK_ALLOCATOR_CAUSAL_SYNTHETIC_PASS_NOT_PNL")

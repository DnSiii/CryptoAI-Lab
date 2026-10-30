#!/usr/bin/env python3
"""V98 NU fixed future-only capital competition; no 2025 or future PnL."""
import numpy as np
from nu_sources import HOURS,WARMUP
from v98_future_net_growth_capital_competition import allocate
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):
        raise ValueError('NU_INUENUS_SHAPE')
    p=np.log(d['c'])
    returns=np.diff(p,axis=0,prepend=p[:1])
    result=np.zeros_like(raw)
    held=np.zeros((4,4))
    previous_net=np.zeros(4)
    counts={'Opportunity':0,'Relative_Value':0,'Stress_Recovery':0}
    decisions=0
    for t in range(WARMUP,HOURS):
        if updates[t,0]:
            if not updates[t].all() or t%8 or not d['event'][t-160:t+1:8].all():
                raise ValueError('NU_INUENUS_CALENDAR')
            r=returns[t-335:t+1]
            funding=d['rate'][t-160:t+1:8]
            out=allocate(raw[t,0],raw[t,1:],previous_net,r,funding)
            held[0]=out['core_weights']
            held[1:]=out['optional_weights']
            previous_net=out['net_weights'].copy()
            if float(np.abs(held).sum())>.84+1e-10:
                raise ValueError('NU_INUENUS_GROSS')
            for i,name in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[name]+=1
            decisions+=1
        result[t]=held
    if decisions!=27:raise ValueError('NU_INUENUS_DECISION_COUNU')
    return {'weights':result,'allocation_decisions':decisions,'activated_week_counts':counts,
            'causal_t_minus_one':True,'funding_future_used':False,
            'training_or_holdout_read_by_allocator':False}
def synthetic_tests():
    from nu_sources import synthetic_causality,bundle
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
    if a['allocation_decisions']!=27:raise AssertionError('NU_INUENUS_DECISIONU')
    changed={k:v.copy() for k,v in d.items()}
    for k in ('o','h','l','c'):changed[k][14000:]*=1.7
    changed['rate'][14000:]*=-1.
    new_raw,new_updates,_=bundle(*(changed[k] for k in ('o','h','l','c','q','rate','event')))
    b=build(changed,new_raw,new_updates)
    if not np.array_equal(a['weights'][:14000],b['weights'][:14000]):
        raise AssertionError('NU_INUENUS_FUTURE_LEAK')
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print('NU_NET_GROWTH_INUENUS_CAUSAL_SYNUHETIC_PASS_NOT_PNL')

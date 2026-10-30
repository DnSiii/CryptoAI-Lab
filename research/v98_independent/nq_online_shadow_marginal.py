#!/usr/bin/env python3
"""V98 NQ causal reference shadow portfolios, before adaptive full-book execution.
Reference shadows never receive adaptive weights. Only settled historical hours
can affect a later decision; conservative funding is not an exact event tick.
"""
import math
import numpy as np
from v98_oneway_net_atomic_planner import plan_virtual,settle_virtual
from v98_next_pretrade_projection import project
from v98_mark_envelope_settlement import worst_funding
from nq_sources import BOOKS

def build(d,raw,updates,lo,hi,start=744,period=168,lookback=1344):
    o,c,rate,event=[np.asarray(d[k]) for k in ('o','c','rate','event')]
    n=len(o)
    if raw.shape!=(n,4,4) or updates.shape!=(n,4) or lo.shape!=(n,4) or hi.shape!=(n,4):
        raise ValueError('NQ_SHADOW_SHAPE')
    if start<1 or period<1 or lookback<period or lookback%period:
        raise ValueError('NQ_SHADOW_WINDOW')
    names=tuple(BOOKS)
    q=np.zeros((4,4,4))
    nav=np.full(4,10000.,dtype=float)
    equity=np.full((n,4),np.nan)
    equity[start]=nav
    scores=np.full((n,3),np.nan)
    multipliers=np.array([.5,.5,.5])
    adaptive=np.zeros_like(raw)
    def apply(t):
        w=raw[t].copy()
        w[1:]*=multipliers[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NQ_SHADOW_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if float(np.abs(w).sum())>.84+1e-10:
            raise ValueError('NQ_SHADOW_ADAPTIVE_GROSS')
        return w
    current=apply(start)
    adaptive[start]=current
    for t in range(start+1,n):
        px=o[t]
        is_event=bool(event[t].any())
        for b,name in enumerate(names):
            old=q[b].copy()
            nav[b]+=float(np.dot(old.sum(axis=0),px-c[t-1]))
            if nav[b]<=0 or not math.isfinite(nav[b]):
                raise ValueError('NQ_SHADOW_OPEN_INSOLVENCY_'+str(t))
            pre_gross=float(np.sum(np.abs(old)*px))
            active=BOOKS[name]
            update=np.array([bool(updates[t-1,k]) and k in active for k in range(4)])
            guard=pre_gross>.84*nav[b] or (is_event and pre_gross>.82*nav[b])
            planned=None
            if update.any() or guard:
                source=raw[t-1].copy()
                enabled=np.zeros(4,bool);enabled[list(active)]=True
                source[~enabled]=0.
                projected=project(old,source,update,px,nav[b],funding_event=is_event)
                planned=plan_virtual(old,projected['weights'],px,nav[b],.0004,.0002,
                                     funding_event=is_event)
                new=planned['virtual_quantity']
            else:new=old
            funding=(worst_funding(old.sum(axis=0),new.sum(axis=0),rate[t],
                                   event[t],lo[t],hi[t],'carried_before_fill')
                     if is_event else 0.)
            if planned is not None:
                nav[b]=settle_virtual(planned,funding,'carried_before_fill',nav[b],old,px)
            else:nav[b]+=funding
            q[b]=new
            nav[b]+=float(np.dot(new.sum(axis=0),c[t]-px))
            if nav[b]<=0 or not math.isfinite(nav[b]):
                raise ValueError('NQ_SHADOW_CLOSE_INSOLVENCY_'+str(t))
            equity[t,b]=nav[b]
        if (t-start)%period==0:
            if t-lookback>=start:
                for j in range(3):
                    x=float(math.log(equity[t,0]/equity[t-lookback,0])-
                            math.log(equity[t,j+2]/equity[t-lookback,j+2]))
                    scores[t,j]=x
                    multipliers[j]=1. if x>0 else .25
            else:multipliers[:]=.5
            current=apply(t)
        adaptive[t]=current
    # All decisions are t-close and applied no earlier than t+1 open.
    return {'weights':adaptive,'shadow_equity':equity,'scores':scores,
            'shadow_books':names,'score_decision_count':int(np.isfinite(scores).any(axis=1).sum()),
            'uses_future_funding_for_sizing':False,'shadow_cost_tier':'base',
            'shadow_funding_order':'carried_before_fill'}

def synthetic_tests():
    n=12;start=2
    o=np.full((n,4),100.);c=o.copy()
    c[:,0]=100.+np.arange(n)*.5
    c[:,1]=100.+np.arange(n)*.2
    rate=np.zeros_like(o);event=np.zeros_like(o,dtype=bool);event[::2]=True
    lo=o.copy();hi=o.copy()
    d={'o':o,'c':c,'rate':rate,'event':event}
    raw=np.zeros((n,4,4));updates=np.zeros((n,4),bool)
    for t in range(start,n,2):
        raw[t,0,0]=.2;raw[t,1,1]=.1;raw[t,2,0]=-.05;raw[t,3,0]=.07
        updates[t]=True
    # Persist source targets after each close; mutate only future bars in second run.
    for t in range(start+1,n):
        if not updates[t].any():raw[t]=raw[t-1]
    a=build(d,raw,updates,lo,hi,start=start,period=2,lookback=4)
    assert np.all(np.isfinite(a['shadow_equity'][start:]))
    assert a['score_decision_count']==3
    assert np.all(np.abs(a['weights']).sum(axis=(1,2))<=.84+1e-10)
    d2={k:v.copy() for k,v in d.items()}
    d2['c'][9:,0]*=1.4;d2['rate'][9:,0]=.02
    b=build(d2,raw,updates,lo,hi,start=start,period=2,lookback=4)
    assert np.allclose(a['weights'][:9],b['weights'][:9])
    assert np.allclose(a['shadow_equity'][:9],b['shadow_equity'][:9],equal_nan=True)
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print('NQ_SHADOW_CAUSAL_SYNTHETIC_PASS_NOT_HISTORICAL_PNL')

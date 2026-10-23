#!/usr/bin/env python3
"""AD source-only causal multiplicative virtual-sleeve wealth allocator.

Does not assume executable fills, NAV, or governor clearance.
"""
from __future__ import annotations
import numpy as np
from phase1189_ad_online_core_router import stable_softmax

PRIOR=np.array([.70,.10,.10,.10],dtype=float)
ETA=.25
FLOOR=.03
FEE=.0012


def sleeve_matrix(growth,opportunity,relative_value,stress):
    g,o,r,s=(np.asarray(x,dtype=float) for x in (growth,opportunity,relative_value,stress))
    if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (g,o,r,s)):
        raise ValueError('AD1195_SLEEVE_SHAPE')
    if np.any(g<0) or g.sum()>1+1e-9 or np.any(np.abs(o)>1) or np.any(o!=np.round(o)):
        raise ValueError('AD1195_CORE_OPPORTUNITY')
    if np.abs(r).sum()>1+1e-8 or abs(r.sum())>1e-7:
        raise ValueError('AD1195_RV_NEUTRALITY')
    if np.any(s>0) or np.abs(s).sum()>.30+1e-9 or np.max(s)-np.min(s)>1e-9:
        raise ValueError('AD1195_STRESS_INTENT')
    return np.vstack([g,.10*o,.15*r,s])


class ADAllocator:
    def __init__(self):
        self.wealth=np.ones(4,dtype=float)
        self.prev=np.zeros((4,4),dtype=float)
        self.turnover=np.zeros(4,dtype=float)
        self.hours=0

    def step(self, realized_return, funding_rate, funding_event, next_sleeves, regime):
        ret=np.asarray(realized_return,dtype=float)
        fund=np.asarray(funding_rate,dtype=float)
        event=np.asarray(funding_event,dtype=float)
        nxt=np.asarray(next_sleeves,dtype=float)
        p=np.asarray(regime,dtype=float)
        if (ret.shape!=(4,) or fund.shape!=(4,) or event.shape!=(4,) or
                nxt.shape!=(4,4) or p.shape!=(3,) or
                not all(np.isfinite(x).all() for x in (ret,fund,event,nxt,p)) or
                np.any((event!=0)&(event!=1)) or np.any(fund[event==0]!=0) or
                np.any(p<0) or abs(p.sum()-1)>1e-9):
            raise ValueError('AD1195_STATE_INPUT')
        # Mark only previous t-1 sleeve holdings with completed t returns.
        realized=self.prev@(ret-fund*event)-FEE*self.turnover
        multiplier=1+realized
        if np.any(multiplier<=0) or not np.isfinite(multiplier).all():
            raise ValueError('AD1195_VIRTUAL_INSOLVENCY')
        self.wealth*=multiplier
        if np.any(self.wealth<=0) or not np.isfinite(self.wealth).all():
            raise ValueError('AD1195_VIRTUAL_WEALTH')
        base=stable_softmax(np.log(PRIOR)+ETA*np.log(self.wealth))
        base=np.maximum(base,FLOOR)
        base/=base.sum()
        off,transition,on=p
        route=np.array([.5+on,.5+.5*transition,.5+.5*transition,.5+off])
        posterior=base*route
        posterior/=posterior.sum()
        desired=posterior@nxt
        self.turnover=np.abs(nxt-self.prev).sum(axis=1)
        self.prev=nxt.copy()
        self.hours+=1
        return desired,posterior.copy()

    def diagnostic(self):
        return {'phase':1195,'source_only':True,'historical_system_pnl_computed':False,
                'validation_2025_read':False,'external_benchmarks_used':False,
                'actual_execution_proven':False,'steps':self.hours}

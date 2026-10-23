#!/usr/bin/env python3
"""V98 U causal signed contingent ledger, synthetic-only and UNFROZEN.

No authenticated historical PnL. Do not use for 2025 or future holdout.
"""
from __future__ import annotations
import math
import numpy as np
from phase1093_u_contingent_execution import (
    plan, audit_bracket_paths, corners_audit, PARTICIPATION)
from phase1096_u_safety_oracle import require_full_stop_coverage, realized_funding_buffer

FEE_TIERS={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')
CAPITAL_MODES={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}

def simulate_synthetic_u(target,op,hi,lo,cl,quote,rate,mark,event,down,up,
                         *,fee=.0007,order='carried_before_fill',mode='immediate',
                         years=None):
    w,o,h,l,c,q,fr,mk,ev,dn,sh=[np.asarray(x) for x in
      (target,op,hi,lo,cl,quote,rate,mark,event,down,up)]
    n=len(w);yy=np.asarray(years if years is not None else np.full(n,2023))
    if (n<2 or any(x.shape!=(n,4) for x in (w,o,h,l,c,q,fr,ev,dn,sh)) or
        mk.shape!=(n,4,2) or yy.shape!=(n,) or
        not np.isin(yy,(2022,2023,2024)).all() or
        not np.isin(np.asarray(ev).dtype.kind,('b',)) or
        order not in ORDERS or mode not in CAPITAL_MODES or fee not in FEE_TIERS.values()):
        raise ValueError('U_INTEGRATED_GEOMETRY_OR_FUTURE')
    if (not all(np.isfinite(x).all() for x in (w,o,h,l,c,q,fr)) or
        (o<=0).any() or (l<=0).any() or (h<np.maximum(o,c)).any() or
        (l>np.minimum(o,c)).any() or (q<0).any() or
        (np.abs(w).max()>.45+1e-10) or (np.abs(w).sum(axis=1).max()>1.35+1e-10) or
        (np.abs(w.sum(axis=1)).max()>.75+1e-10) or
        (dn<0).any() or (dn>=1).any() or (sh<0).any()):
        raise ValueError('U_INTEGRATED_SOURCE_OR_TARGET')
    if (not np.isfinite(mk[ev]).all() or (mk[ev]<=0).any() or
        (mk[:,:,0][ev]>mk[:,:,1][ev]).any() or np.isfinite(mk[~ev]).any() or
        (fr[~ev]!=0).any()):
        raise ValueError('U_INTEGRATED_SIGNED_FUNDING')
    initial=CAPITAL_MODES[mode];cash=initial;units=np.zeros(4)
    nav=initial;navs=[];reason=None;breach=None
    fees=turnover=funding=0.;entries=stops=limits=0;max_paths=0
    for t in range(1,n):
        prior_equity=nav
        if prior_equity<=0 or not math.isfinite(prior_equity):
            reason='U_NONPOSITIVE_PRIOR_EQUITY';breach=t;break
        desired=w[t-1]*prior_equity/c[t-1]
        carried=units.copy()
        # Before the open, cover the maximum committed quantity; never
        # use a smaller desired quantity to leave residual carried units.
        opposite=(np.abs(carried)>1e-9)&(np.abs(desired)>1e-9)&(np.sign(carried)!=np.sign(desired))
        if np.any(opposite):
            reason='U_UNSUPPORTED_PREPLACED_REVERSAL';breach=t;break
        committed=np.where(np.abs(desired)<1e-9,carried,
                   np.sign(desired)*np.maximum(np.abs(desired),np.abs(carried)))
        bracket=plan(c[t-1],committed,dn[t-1],sh[t-1],q[t-1])
        changed=(t==1 or not np.array_equal(w[t-1],w[t-2]))
        if changed:
            delta=desired-units
            max_qty=PARTICIPATION*q[t-1]/o[t]
            delta=np.sign(delta)*np.minimum(np.abs(delta),max_qty)
            if np.any((units+delta)*desired<-1e-8):
                reason='U_ENTRY_PARTIAL_OPPOSITE_SIDE';breach=t;break
            price=o[t]*(1+np.sign(delta)*fee)
            cash-=float(np.dot(delta,price))+fee*float(np.abs(delta*price).sum())
            units+=delta
            entries+=int(np.count_nonzero(np.abs(delta)>1e-10))
            turnover+=float(np.abs(delta*price).sum())
            fees+=fee*float(np.abs(delta*price).sum())
        reason=require_full_stop_coverage(bracket,units)
        if reason is not None:
            breach=t;break
        # Prior-only reserve is an estimate, never used to alter target.
        historical_max=np.max(np.abs(fr[max(0,t-720):t]),axis=0)
        reserve_prior=float(np.sum(np.maximum(np.abs(carried),np.abs(units))*o[t]*historical_max))
        # Realized t funding is used only for ex-post intrabar verification.
        reserve_realized=realized_funding_buffer(carried,units,fr[t],ev[t],mk[t])
        reserve=max(reserve_prior,reserve_realized)
        audit=audit_bracket_paths(bracket,cash,units,o[t],h[t],l[t],fee,
                                 slippage=fee,buffer=reserve,capacity=True)
        if not audit['ok']:
            reason=audit['reason'];breach=t;break
        max_paths=max(max_paths,audit['scenarios'])
        cash=float(audit['cash']);units=audit['units']
        fees+=audit['fee_usd'];turnover+=audit['turnover_usd']
        stops+=sum(e['action']=='STOP' for e in audit['events'])
        limits+=sum(e['action']=='LIMIT' for e in audit['events'])
        if ev[t].any():
            held=carried if order=='carried_before_fill' else units
            signed=held[ev[t]]*fr[t,ev[t]]
            adverse=np.where(signed>=0,mk[t,ev[t],1],mk[t,ev[t],0])
            debit=float(np.sum(signed*adverse))
            cash-=debit;funding+=debit
        close_audit=corners_audit(cash,units,c[t],np.zeros(4),np.zeros(4),baseline=prior_equity)
        if not close_audit['ok']:
            reason='U_CLOSE_'+close_audit['reason'];breach=t;break
        nav=cash+float(np.dot(units,c[t]));navs.append(nav)
        if nav<=0 or not math.isfinite(nav):reason='U_NONPOSITIVE_NAV';breach=t;break
    return {'survived':reason is None,'reason':reason,'breach_index':breach,
            'observations':len(navs),'initial_usd':initial,
            'terminal_usd':nav if reason is None else None,
            'fees_usd':fees,'turnover_usd':turnover,'funding_debit_usd':funding,
            'entry_fills':entries,'stop_fills':stops,'limit_fills':limits,
            'max_mixed_paths_checked':max_paths,
            'historical_pnl_validated':False,'authenticated_source':False,
            'validation_2025_read':False,'external_benchmarks_used':False}

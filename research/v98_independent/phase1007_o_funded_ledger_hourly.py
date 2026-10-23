#!/usr/bin/env python3
"""V98 O hourly-observable economic kernel; SYNTHETIC ONLY until fresh source gate.

Distinct O seven-slot engine; preregistered Phases1005/1007. Never edits N.
All fills at open(t) from N target[t-1], previous-hour quote volume.
"""
from __future__ import annotations
import math
import numpy as np
from phase1002_lp_opening_repair import repair_open_lp as repair_open, PARTICIPATION
from phase935_hourly_drawdown_integrity import drawdown
from phase876_k_funded_ledger import (_within,_intrabar,_risk,_fold_metrics,
                                         FEE_TIERS,ORDERS,CAPITAL_MODES,CAP_GROSS,CAP_ASSET)


def simulate_o_with_hourly(target,op,hi,lo,cl,quote,rate,mark,event,fee,*,order,mode,years,require_full_sample=True):
    arrays=[np.asarray(x) for x in (target,op,hi,lo,cl,quote,rate,mark,event)]
    w,o,h,l,c,q,fr,mk,ev=arrays
    n=len(w);yy=np.asarray(years)
    if n<3 or any(x.shape!=(n,4) for x in arrays) or yy.shape!=(n,):
        raise ValueError('O aligned four-asset hourly source required')
    if not np.isin(yy,(2022,2023,2024)).all():raise ValueError('2025+ and holdout forbidden')
    if mode not in CAPITAL_MODES or order not in ORDERS or fee not in FEE_TIERS.values():
        raise ValueError('unregistered O economic cell')
    if not all(np.isfinite(x).all() for x in (w,o,h,l,c,q,fr)):
        raise ValueError('nonfinite target/OHLC/funding')
    if (w<0).any() or (w.max(axis=1)>CAP_ASSET+1e-9).any() or (w.sum(axis=1)>CAP_GROSS+1e-9).any():
        raise ValueError('invalid preregistered O target')
    if (l<=0).any() or (l>np.minimum(o,c)).any() or (h<np.maximum(o,c)).any() or (q<0).any():
        raise ValueError('invalid OHLC/quote source')
    if np.asarray(ev).dtype!=bool or np.any(~np.isfinite(mk[ev])) or np.any(mk[ev]<=0):
        raise ValueError('funding event/mark invalid')
    if np.isfinite(mk[~ev]).any() or np.any(fr[~ev]!=0):
        raise ValueError('unauthenticated non-event funding mark/rate')
    initial=CAPITAL_MODES[mode]
    cash=initial;units=np.zeros(4,float)
    fees=funding=turnover=repair_turnover=0.
    filled=partial=repair_events=0
    days=[];hourly=[];reason=None;breach_index=None;terminal=initial
    for t in range(1,n):
        if yy[t]==2022:continue
        if yy[t] not in (2023,2024):raise ValueError('invalid calendar')
        opening=o[t]
        carried=units.copy()
        prior_cash=cash
        # O exact LP opening repair is sell-only and uses strictly t-1 quote volume.
        cash,units,repaired,ok=repair_open(cash,units,opening,q[t-1],fee)
        if not ok:
            reason='OPEN_REPAIR_INFEASIBLE';breach_index=t;break
        if not _within(cash,units,opening):
            reason='OPEN_REPAIR_CAP_BREACH';breach_index=t;break
        repair_sum=float(repaired.sum())
        repair_turnover+=repair_sum
        repair_events+=int(repair_sum>1e-8)
        fees+=repair_sum*fee;turnover+=repair_sum
        filled+=int((repaired>1e-8).sum())
        # O target is computed at close(t-1), never with current OHLC.
        equity=float(cash+np.dot(units,opening))
        desired=w[t-1]*equity
        current=units*opening
        if mode=='immediate':
            discretionary_cap=np.full(4,np.inf)
        else:
            discretionary_cap=np.maximum(PARTICIPATION*q[t-1]-repaired,0.)
        sells=np.minimum(np.maximum(current-desired,0),discretionary_cap)
        cash+=float(sells.sum()*(1-fee));units-=sells/opening
        fees+=float(sells.sum()*fee);turnover+=float(sells.sum())
        filled+=int((sells>1e-8).sum())
        if not _within(cash,units,opening):
            reason='POST_SELL_CAP_BREACH';breach_index=t;break
        current=units*opening
        requested=np.maximum(desired-current,0)
        # Never undo a mandatory opening repair with a same-hour rebuy.
        requested[repaired>1e-8]=0.
        if mode=='immediate':
            buy_cap=np.full(4,np.inf)
        else:
            buy_cap=np.maximum(discretionary_cap-sells,0.)
        buys=np.minimum(requested,buy_cap)
        def feasible(k):
            buy=buys*k
            return _within(cash-float(buy.sum()*(1+fee)),units+buy/opening,opening)
        if not feasible(0):
            reason='PRE_BUY_CAP_BREACH';breach_index=t;break
        if not feasible(1):
            low=0.;high=1.
            for _ in range(48):
                mid=(low+high)/2
                if feasible(mid):low=mid
                else:high=mid
            buys*=low
        cash-=float(buys.sum()*(1+fee));units+=buys/opening
        fees+=float(buys.sum()*fee);turnover+=float(buys.sum())
        filled+=int((buys>1e-8).sum())
        partial+=int(np.sum(np.abs(units*opening-desired)>1e-6*equity))
        if not _within(cash,units,opening):
            reason='POST_FILL_CAP_BREACH';breach_index=t;break
        if ev[t].any():
            held=carried if order=='carried_before_fill' else units
            debit=float(np.sum(held[ev[t]]*mk[t,ev[t]]*fr[t,ev[t]]))
            cash-=debit;funding+=debit
        # Current bar high/low are ex-post rejection only, NEVER used to size.
        if not _intrabar(cash,units,l[t],h[t]):
            reason='INTRABAR_SURVIVAL_BREACH';breach_index=t;break
        if not _within(cash,units,c[t]):
            reason='CLOSE_SURVIVAL_BREACH';breach_index=t;break
        terminal=float(cash+np.dot(units,c[t]))
        hourly.append((int(yy[t]),terminal))
        if t==n-1 or yy[t+1]!=yy[t] or t%24==23:
            _,gross,asset=_risk(cash,units,c[t])
            days.append((int(yy[t]),terminal,gross,asset))
    out={'survived':reason is None,'reason':reason,'breach_index':breach_index,
         'initial_usd':initial,'terminal_usd':terminal if reason is None else None,
         'fees_usd':fees,'funding_debit_usd':funding,'turnover_usd':turnover,
         'opening_repair_turnover_usd':repair_turnover,'opening_repair_events':repair_events,
         'filled_orders':filled,'partial_asset_hours':partial,'daily_nav_observations':len(days),
         'hourly_nav_observations':len(hourly),
         'hourly_sample_complete':len(hourly)==17544}
    if reason is None:
        groups={2023:[d for d in days if d[0]==2023],2024:[d for d in days if d[0]==2024]}
        base=initial;folds={}
        for year in (2023,2024):
            folds[str(year)]=_fold_metrics(groups[year],base,None) if groups[year] else {'survived':False,'reason':'empty_fold'}
            if groups[year]:
                hourly_fold=[nav for y,nav in hourly if y==year]
                if require_full_sample and len(hourly_fold)!=(8760 if year==2023 else 8784):
                    raise ValueError('incomplete hourly fold: telemetry fail closed')
                folds[str(year)]['hourly_close_max_drawdown']=drawdown(hourly_fold,base)
                folds[str(year)]['daily_close_max_drawdown']=folds[str(year)]['max_drawdown']
                if folds[str(year)]['hourly_close_max_drawdown']>folds[str(year)]['daily_close_max_drawdown']+1e-12:
                    raise AssertionError('hourly MDD cannot understate daily MDD')
                folds[str(year)]['hourly_nav_observations']=len(hourly_fold)
                base=groups[year][-1][1]
        out['folds']=folds
        if require_full_sample and len(hourly)!=17544:
            raise ValueError('incomplete 2023/2024 hourly sample')
        out['all_hourly_close_max_drawdown']=drawdown([nav for _,nav in hourly],initial)
        out['total_log_wealth']=float(math.log(terminal/initial))
        out['total_wealth_multiple']=float(terminal/initial)
    return out

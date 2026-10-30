#!/usr/bin/env python3
"""V98 Independent P hourly funded ledger kernel, not authorized for economics
until the five canonical P target hashes and source/code bytes are frozen.

All decisions from close(t-1); opening prices are observable at execution.
Native funding mark/rate at t are used only in ex-post debits, never for sizing.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from phase1025_p_state_aware_governor import execute_open, survives
from phase935_hourly_drawdown_integrity import drawdown
from phase876_k_funded_ledger import (_within,_intrabar,_risk,_fold_metrics,
                                         FEE_TIERS,ORDERS,CAPITAL_MODES,CAP_GROSS,CAP_ASSET)


def simulate_p_hourly(target,op,hi,lo,cl,quote,rate,mark,event,down,up,fee,*,order,mode,years,require_full_sample=True):
    data=[np.asarray(x) for x in (target,op,hi,lo,cl,quote,rate,mark,event,down,up)]
    w,o,h,l,c,q,fr,mk,ev,dn,sh=data
    n=len(w);yy=np.asarray(years)
    if n<3 or any(x.shape!=(n,4) for x in data) or yy.shape!=(n,):
        raise ValueError('P aligned four-asset hourly source required')
    if not np.isin(yy,(2022,2023,2024)).all() or mode not in CAPITAL_MODES or order not in ORDERS or fee not in FEE_TIERS.values():
        raise ValueError('P training-only registered economic cell required')
    if not all(np.isfinite(x).all() for x in (w,o,h,l,c,q,fr)):
        raise ValueError('P nonfinite targets/OHLC/funding')
    if (w<0).any() or (w.max(axis=1)>CAP_ASSET+1e-9).any() or (w.sum(axis=1)>CAP_GROSS+1e-9).any():
        raise ValueError('P invalid target')
    if (l<=0).any() or (l>np.minimum(o,c)).any() or (h<np.maximum(o,c)).any() or (q<0).any():
        raise ValueError('P invalid OHLC/quote source')
    if np.asarray(ev).dtype!=bool or np.any(~np.isfinite(mk[ev])) or np.any(mk[ev]<=0) or np.isfinite(mk[~ev]).any() or np.any(fr[~ev]!=0):
        raise ValueError('P unauthenticated funding event/mark')
    if not np.all(np.isfinite(dn[1439:])) or not np.all(np.isfinite(sh[1439:])):
        raise ValueError('P 1440h shock source missing')
    if np.any(dn[1439:]<0) or np.any(dn[1439:]>=1) or np.any(sh[1439:]<0):
        raise ValueError('P invalid causal shock')
    rate_max=pd.DataFrame(np.abs(fr)).rolling(1440,min_periods=1).max().to_numpy()
    initial=CAPITAL_MODES[mode]
    cash=float(initial);units=np.zeros(4)
    fees=funding=turnover=opening_repair_turnover=stress_repair_turnover=0.
    filled=partial=repair_events=0
    days=[];hourly=[];reason=None;breach_index=None;terminal=initial
    for t in range(1,n):
        if yy[t]==2022:continue
        opening=o[t]
        carried=units.copy()
        # Prior-only shocks: warmup requires 1440 completed bars; until then stay cash.
        if t-1<1439:
            if np.any(units) or cash!=initial:raise AssertionError('P_WARMUP_POSITION_BREACH')
            post={'ok':True,'cash':cash,'units':units.copy(),
                  'opening_repair_usd':np.zeros(4),'stress_repair_usd':np.zeros(4),
                  'sells_usd':np.zeros(4),'buys_usd':np.zeros(4),'funding_buffer_usd':0.,
                  'pre_open_equity':float(initial)}
        else:
            # Upper bound on either funding ordering, using rates observed <=t-1.
            # Mark/rate/event at t are NEVER used to choose the buffer.
            eq=cash+float(np.dot(units,opening))
            desired=w[t-1]*eq
            funding_buffer=float(np.sum(np.maximum(units*opening,desired)*rate_max[t-1]))
            post=execute_open(cash,units,opening,q[t-1],w[t-1],fee,dn[t-1],sh[t-1],
                              funding_buffer=funding_buffer,mode=mode)
        if not post['ok']:
            reason=post['reason'];breach_index=t;break
        cash=float(post['cash']);units=post['units'].copy()
        repaired=float(post['opening_repair_usd'].sum()+post['stress_repair_usd'].sum())
        opening_repair_turnover+=float(post['opening_repair_usd'].sum())
        stress_repair_turnover+=float(post['stress_repair_usd'].sum())
        repair_events+=int(repaired>1e-8)
        traded=repaired+float(post['sells_usd'].sum()+post['buys_usd'].sum())
        fees+=fee*traded;turnover+=traded
        filled+=int(np.count_nonzero(post['opening_repair_usd']>1e-8)+
                    np.count_nonzero(post['stress_repair_usd']>1e-8)+
                    np.count_nonzero(post['sells_usd']>1e-8)+np.count_nonzero(post['buys_usd']>1e-8))
        if t-1>=1439:
            eq=cash+float(np.dot(units,opening))
            partial+=int(np.sum(np.abs(units*opening-w[t-1]*eq))>1e-6*eq)
        if ev[t].any():
            held=carried if order=='carried_before_fill' else units
            debit=float(np.sum(held[ev[t]]*mk[t,ev[t]]*fr[t,ev[t]]))
            cash-=debit;funding+=debit
        # Ex-post only: enumerate ALL 16 realized OHLC corners; no current
        # high/low has influenced orders or pretrade funding buffer.
        if not survives(cash,units,opening,1-l[t]/opening,h[t]/opening-1,
                        baseline=post['pre_open_equity']):
            reason='P_INTRABAR_16CORNER_SURVIVAL_BREACH';breach_index=t;break
        if not _intrabar(cash,units,l[t],h[t]):
            reason='P_INTRABAR_SURVIVAL_BREACH';breach_index=t;break
        if not _within(cash,units,c[t]):
            reason='P_CLOSE_SURVIVAL_BREACH';breach_index=t;break
        terminal=float(cash+np.dot(units,c[t]))
        hourly.append((int(yy[t]),terminal))
        if t==n-1 or yy[t+1]!=yy[t] or t%24==23:
            _,gross,asset=_risk(cash,units,c[t])
            days.append((int(yy[t]),terminal,gross,asset))
    out={'survived':reason is None,'reason':reason,'breach_index':breach_index,
         'initial_usd':initial,'terminal_usd':terminal if reason is None else None,
         'fees_usd':fees,'funding_debit_usd':funding,'turnover_usd':turnover,
         'opening_repair_turnover_usd':opening_repair_turnover,
         'stress_repair_turnover_usd':stress_repair_turnover,'opening_repair_events':repair_events,
         'filled_orders':filled,'partial_asset_hours':partial,'daily_nav_observations':len(days),
         'hourly_nav_observations':len(hourly),'hourly_sample_complete':len(hourly)==17544}
    if reason is None:
        groups={y:[d for d in days if d[0]==y] for y in (2023,2024)}
        base=initial;folds={}
        for year in (2023,2024):
            group=groups[year]
            folds[str(year)]=_fold_metrics(group,base,None) if group else {'survived':False,'reason':'empty_fold'}
            if group:
                hs=[nav for y,nav in hourly if y==year]
                if require_full_sample and len(hs)!=(8760 if year==2023 else 8784):
                    raise ValueError('P incomplete hourly fold')
                folds[str(year)]['hourly_close_max_drawdown']=drawdown(hs,base)
                folds[str(year)]['hourly_nav_observations']=len(hs)
                base=group[-1][1]
        out['folds']=folds
        if require_full_sample and len(hourly)!=17544:raise ValueError('P incomplete two-fold sample')
        out['all_hourly_close_max_drawdown']=drawdown([nav for _,nav in hourly],initial)
        out['total_log_wealth']=float(math.log(terminal/initial))
        out['total_wealth_multiple']=float(terminal/initial)
    return out

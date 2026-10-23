#!/usr/bin/env python3
"""V98 Independent Q signed native-funded hourly ledger; NOT an economic dispatcher.

Pure ledger kernel for preregistered Q: no data acquisition, no 2025, no P
execution imports. Do not call on historical data until Q code+targets freeze.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from phase1040_q_signed_margin_oracle import execute_signed,corner_audit

FEE_TIERS={'base':.0007,'severe':.0012,'supersevere':.0020}
ORDERS=('carried_before_fill','new_after_fill')
CAPITAL_MODES={'immediate':10000.,'capacity_1m':1_000_000.,'capacity_10m':10_000_000.}


def _drawdown(nav,initial):
    x=np.asarray(nav,float)
    if not len(x) or not np.isfinite(x).all() or (x<=0).any():return None
    highs=np.maximum.accumulate(np.r_[initial,x])[1:]
    return float(np.min(x/highs-1))


def _fold(days,initial):
    nav=np.asarray(days,float)
    if len(nav)<2 or (nav<=0).any():return {'complete':False}
    ret=nav/np.r_[initial,nav[:-1]]-1
    pos=ret[ret>0];neg=ret[ret<0]
    pf=float(pos.sum()/(-neg.sum())) if len(neg) else None
    payoff=float(pos.mean()/(-neg.mean())) if len(pos) and len(neg) else None
    return {'complete':True,'days':len(nav),'terminal':float(nav[-1]),
            'log_wealth':float(math.log(nav[-1]/initial)),
            'cagr':float((nav[-1]/initial)**(365/len(nav))-1),
            'max_drawdown':_drawdown(nav,initial),
            'profit_factor':pf,'payoff':payoff,'win_rate':float(np.mean(ret>0)),
            'positive_days':int((ret>0).sum()),
            'cvar_5pct':float(np.mean(np.sort(ret)[:max(1,int(np.ceil(len(ret)*.05)))]))}


def simulate_q_hourly(target,op,hi,lo,cl,quote,rate,mark,event,down,up,fee,*,order,mode,years,require_full_sample=True):
    fields=[np.asarray(x) for x in (target,op,hi,lo,cl,quote,rate,mark,event,down,up)]
    w,o,h,l,c,q,fr,mk,ev,dn,sh=fields
    n=len(w);yy=np.asarray(years)
    if n<1600 or any(x.shape!=(n,4) for i,x in enumerate(fields) if i!=7) or mk.shape!=(n,4,2) or yy.shape!=(n,):
        raise ValueError('Q_ALIGNED_CLEAN4_HOURLY_SOURCE_REQUIRED')
    if not np.isin(yy,(2022,2023,2024)).all() or order not in ORDERS or mode not in CAPITAL_MODES or fee not in FEE_TIERS.values():
        raise ValueError('Q_TRAINING_ONLY_ECONOMIC_CELL')
    if not all(np.isfinite(x).all() for x in (w,o,h,l,c,q,fr)) or np.max(np.abs(w))>.55+1e-10 or np.max(np.abs(w).sum(axis=1))>1.4+1e-10 or np.max(np.abs(w.sum(axis=1)))>.65+1e-10:
        raise ValueError('Q_NONFINITE_OR_UNBOUNDED_TARGET')
    if (o<=0).any() or (l<=0).any() or (l>np.minimum(o,c)).any() or (h<np.maximum(o,c)).any() or (q<0).any():
        raise ValueError('Q_INVALID_OHLC_VOLUME')
    if np.asarray(ev).dtype!=bool or np.any(~np.isfinite(mk[ev])) or np.any(mk[ev]<=0) or np.any(mk[ev,0]>mk[ev,1]) or np.isfinite(mk[~ev]).any() or np.any(fr[~ev]!=0):
        raise ValueError('Q_INVALID_NATIVE_FUNDING')
    if np.any(~np.isfinite(dn[1439:])) or np.any(~np.isfinite(sh[1439:])) or np.any(dn[1439:]<0) or np.any(dn[1439:]>=1) or np.any(sh[1439:]<0):
        raise ValueError('Q_INVALID_PRIOR_SHOCK')
    max_rate=pd.DataFrame(np.abs(fr)).rolling(1440,min_periods=1).max().to_numpy()
    initial=CAPITAL_MODES[mode];cash=initial;units=np.zeros(4)
    fees=funding=turnover=0.;fills=0;daily=[];hourly=[];reason=None;breach_index=None
    for t in range(1,n):
        if yy[t]==2022:continue
        pre_eq=cash+float(np.dot(units,o[t]))
        if pre_eq<=0 or not math.isfinite(pre_eq):
            reason='Q_OPEN_EQUITY_NONPOSITIVE';breach_index=t;break
        carried=units.copy()
        try:
            if t-1<1439:
                if np.any(units):raise AssertionError('Q_WARMUP_EXPOSURE')
                post={'ok':True,'cash':cash,'units':units.copy(),'turnover_usd':0.,'fee_usd':0.,'trade_usd':np.zeros(4)}
            else:
                buffer=float(np.sum(np.maximum(np.abs(units*o[t]),np.abs(w[t-1]*pre_eq))*max_rate[t-1]))
                post=execute_signed(cash,units,o[t],q[t-1],w[t-1],fee,dn[t-1],sh[t-1],funding_buffer=buffer,mode=mode)
            if not post['ok']:
                reason=post['reason'];breach_index=t;break
            cash=float(post['cash']);units=post['units'].copy()
            fees+=post['fee_usd'];turnover+=post['turnover_usd'];fills+=int(np.count_nonzero(np.abs(post['trade_usd'])>1e-8))
            if ev[t].any():
                held=carried if order=='carried_before_fill' else units
                signed_rate=held[ev[t]]*fr[t,ev[t]]
                # Worst-case native mark for either sign: high for debit, low for credit.
                adverse_mark=np.where(signed_rate>=0,mk[t,ev[t],1],mk[t,ev[t],0])
                debit=float(np.sum(signed_rate*adverse_mark))
                cash-=debit;funding+=debit
            # Actual current OHLC used EX POST only, never for order selection.
            audit=corner_audit(cash,units,o[t],1-l[t]/o[t],h[t]/o[t]-1,baseline=pre_eq)
            if not audit['ok']:
                reason='Q_REALIZED_INTRABAR_'+audit['reason'];breach_index=t;break
            close_audit=corner_audit(cash,units,c[t],np.zeros(4),np.zeros(4),baseline=pre_eq)
            if not close_audit['ok']:
                reason='Q_CLOSE_'+close_audit['reason'];breach_index=t;break
            terminal=cash+float(np.dot(units,c[t]))
            hourly.append((int(yy[t]),terminal))
            if t==n-1 or yy[t+1]!=yy[t] or t%24==23:
                daily.append((int(yy[t]),terminal))
        except Exception as e:
            reason=type(e).__name__+': '+str(e)[:140];breach_index=t;break
    result={'survived':reason is None,'reason':reason,'breach_index':breach_index,
            'fees_usd':float(fees),'funding_debit_usd':float(funding),
            'turnover_usd':float(turnover),'filled_orders':fills,
            'hourly_nav_observations':len(hourly),'daily_nav_observations':len(daily),
            'initial_usd':initial,'terminal_usd':float(hourly[-1][1]) if reason is None and hourly else None}
    if reason is None:
        prev=initial;folds={}
        for year,days_expected,hours_expected in ((2023,365,8760),(2024,366,8784)):
            d=[nav for y,nav in daily if y==year];hvals=[nav for y,nav in hourly if y==year]
            folds[str(year)]=_fold(d,prev)
            folds[str(year)]['hourly_max_drawdown']=_drawdown(hvals,prev)
            folds[str(year)]['hourly_observations']=len(hvals)
            if require_full_sample and (len(d)!=days_expected or len(hvals)!=hours_expected):
                raise ValueError('Q_INCOMPLETE_CHRONOLOGICAL_FOLD')
            if d:prev=d[-1]
        result['folds']=folds
        result['total_log_wealth']=float(math.log(prev/initial))
        result['total_wealth_multiple']=float(prev/initial)
        result['all_hourly_max_drawdown']=_drawdown([v for _,v in hourly],initial)
    return result

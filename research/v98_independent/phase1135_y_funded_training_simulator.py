#!/usr/bin/env python3
"""V98 Y Phase1135: source-agnostic, signed, self-financing training simulator.

NO authenticated historical PnL without Phase1137 immutable freeze.
Uses only Y frozen targets and Clean-4 signed native mark bounds.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from phase1126_y_hourly_ledger import execute_hour, ASSET, NET, GROSS
from phase1131_y_growth_metrics import summarize
from phase1132_y_closed_trade_accounting import TradeBook

FEE_TIERS={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')
CAPITAL_MODES={'immediate':10000.,'capacity_1m':1000000.,'capacity_10m':10000000.}
SLIPPAGE=.002
N_HOURS=18288
FIRST_TRAINING_HOUR=744
REBALANCE_HOURS=12

def prior_bounds(close,high,low,rate):
    """At t only use observations <=t-1; 336h adverse shocks, 720h funding."""
    c,h,l,r=[np.asarray(x,float) for x in (close,high,low,rate)]
    n=len(c)
    if any(x.shape!=(n,4) or not np.isfinite(x).all() for x in (c,h,l,r)):
        raise ValueError('Y1135_PRIOR_SOURCE_GEOMETRY')
    if (c<=0).any() or (l<=0).any() or (h<l).any():
        raise ValueError('Y1135_PRIOR_PRICE')
    downside=np.full((n,4),np.nan)
    upside=np.full((n,4),np.nan)
    fund=np.full((n,4),np.nan)
    stepdown=np.maximum(0.,1.-l[1:]/c[:-1])
    stepup=np.maximum(0.,h[1:]/c[:-1]-1.)
    for t in range(336,n):
        downside[t]=stepdown[t-336:t].max(axis=0)
        upside[t]=stepup[t-336:t].max(axis=0)
    for t in range(719,n):
        fund[t]=np.abs(r[t-719:t+1]).max(axis=0)
    if (downside[335:]>=1).any():
        raise ValueError('Y1135_PRIOR_DOWN_GE_ONE')
    return downside,upside,fund

def validate_inputs(w,o,h,l,c,q,rate,marks,event,years,fee,order,mode,strict):
    n=len(w)
    if (any(x.shape!=(n,4) for x in (w,o,h,l,c,q,rate,event))
        or marks.shape!=(n,4,2) or years.shape!=(n,)
        or event.dtype!=bool or n<FIRST_TRAINING_HOUR+2):
        raise ValueError('Y1135_GEOMETRY')
    if strict and (n!=N_HOURS or not np.array_equal(years,
       pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC').year)):
        raise ValueError('Y1135_FUTURE_OR_INCOMPLETE_TRAINING')
    if (not np.isin(years,(2022,2023,2024)).all() or
        fee not in FEE_TIERS.values() or order not in ORDERS or mode not in CAPITAL_MODES):
        raise ValueError('Y1135_UNREGISTERED_CELL')
    if (any(not np.isfinite(x).all() for x in (w,o,h,l,c,q,rate))
        or (o<=0).any() or (c<=0).any() or (l<=0).any()
        or (h<np.maximum(o,c)).any() or (l>np.minimum(o,c)).any()
        or (q<0).any() or np.any(rate[~event]!=0)
        or np.any(~np.isfinite(marks[event])) or np.any(marks[event]<=0)
        or np.any(marks[:,:,0][event]>marks[:,:,1][event])
        or np.isfinite(marks[~event]).any()):
        raise ValueError('Y1135_INVALID_AUTHENTICATED_INPUT')
    if (np.abs(w).max()>ASSET+1e-10 or
        np.abs(w).sum(axis=1).max()>GROSS+1e-10 or
        np.abs(w.sum(axis=1)).max()>NET+1e-10):
        raise ValueError('Y1135_TARGET_CAP')
    if strict and (int(event.sum())!=9144 or any(event[:,j].sum()!=2286 for j in range(4))):
        raise ValueError('Y1135_FUNDING_EVENT_COUNT')

def adverse_signed_mark(funded_units,rate,marks,event,close):
    """Upper vendor mark for debits; lower for credits, including shorts."""
    u,r,m,e,p=[np.asarray(x) for x in (funded_units,rate,marks,event,close)]
    if (u.shape!=(4,) or r.shape!=(4,) or m.shape!=(4,2) or
        e.shape!=(4,) or p.shape!=(4,) or not np.isfinite(u).all() or
        not np.isfinite(r).all() or not np.isfinite(p).all() or
        (p<=0).any() or np.any(~np.isfinite(m[e])) or
        np.any(m[e]<=0) or np.any(m[e,0]>m[e,1])):
        raise ValueError('Y1135_BAD_SIGNED_MARK')
    return np.where(e,np.where(u*r>=0,m[:,1],m[:,0]),p)

def simulate_y(target,opening,high,low,closing,quote,rate,signed_mark,event,
               *,fee,order,mode,years,regimes=None,strict=True):
    w,o,h,l,c,q,fr,mk,ev,yy=[np.asarray(x) for x in
       (target,opening,high,low,closing,quote,rate,signed_mark,event,years)]
    validate_inputs(w,o,h,l,c,q,fr,mk,ev,yy,fee,order,mode,strict)
    n=len(w)
    states=np.ones(n,dtype=int) if regimes is None else np.asarray(regimes)
    if states.shape!=(n,) or not np.isin(states,(0,1,2)).all():
        raise ValueError('Y1135_REGIME_GEOMETRY')
    dn,up,fund=prior_bounds(c,h,l,fr)
    initial=CAPITAL_MODES[mode]
    cash=initial;units=np.zeros(4);book=TradeBook(initial)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    equity=[];exposure=[];timestamps=[];regime_seq=[]
    fees=turnover=funding=0.;fills=stops=feedback=active=0
    first_failure=None
    for t in range(FIRST_TRAINING_HOUR,n):
        try:
            # All controls, including capacity, use prior-bar information only.
            # Funding settlement uses adverse signed vendor bounds at hour t.
            args=(c[t-1],o[t],h[t],l[t],c[t],units,w[t-1],cash,
                dn[t-1],up[t-1],fund[t-1],q[t-1],fee,SLIPPAGE)
            kw={'rebalance':((t-1)%REBALANCE_HOURS==0),
                'funding_rate':fr[t],'funding_event':ev[t],
                'funding_order':order}
            # First pass obtains the deterministic t-1 planned inventory;
            # its mark is provisional and its success is NOT a selection gate.
            # Settlement replays the same decision with signed vendor extremes.
            provisional=np.where(ev[t],mk[t,:,1],c[t])
            probe=execute_hour(*args,funding_mark=provisional,**kw)
            planned=np.asarray(probe['planned_units'],float)
            prior_stop=c[t-1]*np.where(units>=0,1-dn[t-1],1+up[t-1])
            gap=bool(np.any(((units>1e-12)&(o[t]<=prior_stop))|
                            ((units<-1e-12)&(o[t]>=prior_stop))))
            held=units if order=='carried_before_fill' or gap else planned
            signed=held*fr[t]
            mark=adverse_signed_mark(held,fr[t],mk[t],ev[t],c[t])
            x=execute_hour(*args,funding_mark=mark,**kw)
            if not np.array_equal(np.asarray(x['planned_units']),planned):
                raise ArithmeticError('Y1135_MARK_CHANGED_PRETRADE_DECISION')
            if not x['ok']:
                first_failure={'hour_index':t,'timestamp':idx[t].isoformat(),
                    'reason':x['reason']}
                break
            # Exact per-hour self-financing identity and FIFO trade observer.
            book.apply_hour(x['events'],x['funding_by_asset'],idx[t],
                            funding_order=order)
            if not np.allclose(book.units(),x['units'],atol=1e-8,rtol=0):
                raise ArithmeticError('Y1135_TRADEBOOK_UNITS_DRIFT')
            nav=x['equity']
            if not np.isclose(book.total_pnl(c[t]),nav-initial,
                              rtol=0,atol=max(1e-6,initial*1e-9)):
                raise ArithmeticError('Y1135_TRADEBOOK_NAV_DRIFT')
            cash=float(x['cash']);units=x['units'].copy()
            fees+=x['fees'];turnover+=x['turnover']
            funding+=x['funding_cash_delta']
            fills+=len(x['events']);stops+=int(x['basket_stop'])
            feedback+=int((t-1)%REBALANCE_HOURS!=0)
            active+=int(np.any(np.abs(units)>1e-12))
            timestamps.append(idx[t]);equity.append(nav)
            exposure.append(units*c[t]);regime_seq.append(states[t-1])
        except Exception as exc:
            first_failure={'hour_index':t,'timestamp':idx[t].isoformat(),
                           'reason':type(exc).__name__+': '+str(exc)[:180]}
            break
    result={'survived':first_failure is None,'reason':None if first_failure is None else first_failure['reason'],
        'first_failure':first_failure,'breach_index':None if first_failure is None else first_failure['hour_index'],
        'hourly_nav_observations':len(equity),'filled_orders':fills,'basket_stops':stops,
        'feedback_hours':feedback,'active_hours':active,'fees_usd':float(fees),
        'funding_cash_usd':float(funding),'funding_debit_usd':float(-funding),
        'turnover_usd':float(turnover),'initial_usd':initial,
        'terminal_usd':float(equity[-1]) if equity else initial,
        'validation_2025_read':False,'external_benchmarks_used':False}
    if first_failure is not None or not strict:
        return result
    if len(equity)!=17544:
        raise ValueError('Y1135_INCOMPLETE_FOLDS')
    closed=[{'timestamp':x['timestamp'],'pnl_usd':x['pnl_usd']} for x in book.closed]
    metrics=summarize(pd.DatetimeIndex([idx[FIRST_TRAINING_HOUR-1]]+timestamps),\n        [initial]+equity,[np.zeros(4)]+exposure,closed,[1]+regime_seq)
    result.update(metrics)
    nav=np.asarray(equity,float)
    peak=np.maximum.accumulate(np.r_[initial,nav])
    result['all_hourly_max_drawdown']=float(np.min(np.r_[initial,nav]/peak-1))
    xp=np.asarray(exposure,float)/nav[:,None]
    result['max_asset_weight']=float(np.max(np.abs(xp)))
    result['max_gross_weight']=float(np.max(np.sum(np.abs(xp),axis=1)))
    result['max_net_weight']=float(np.max(np.abs(np.sum(xp,axis=1))))
    changes=np.log(nav/np.r_[initial,nav[:-1]])
    result['regime_log_wealth']={str(k):float(np.sum(changes[np.asarray(regime_seq)==k])) for k in range(3)}
    result['total_log_wealth']=float(math.log(equity[-1]/initial))
    result['total_wealth_multiple']=float(equity[-1]/initial)
    result['hourly_cvar_5pct']=float(min(v['hourly_cvar_5pct'] for v in metrics['folds'].values()))
    result['concentration']={'asset_hhi':float(np.mean([v['concentration']['asset_hhi'] for v in metrics['folds'].values()])),
        'asset_exposure_shares':np.mean([v['concentration']['asset_exposure_shares'] for v in metrics['folds'].values()],axis=0).tolist()}
    result['regime_hours']={str(k):int(np.sum(np.asarray(regime_seq)==k)) for k in range(3)}
    return result

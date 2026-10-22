#!/usr/bin/env python3
"""V98 Independent K funded ledger; deterministic pure kernel, no source I/O.

Historical use ONLY through Phase877 fresh official same-run source gate.
Preregistered Phase865 and Phase876; synthetic fixtures are NOT performance.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np

CAP_GROSS = 1.75
CAP_ASSET = .70
PARTICIPATION = .05
FEE_TIERS = {'base':.0007,'severe':.0012,'supersevere':.0020}
ORDERS = ('carried_before_fill','new_after_fill')
CAPITAL_MODES = {'immediate':1_000_000.,'capacity_1m':1_000_000.,'capacity_10m':10_000_000.}


def _risk(cash, units, price):
    gross_values = units * price
    equity = float(cash + gross_values.sum())
    if not math.isfinite(equity) or equity <= 0:
        return equity, math.inf, math.inf
    return equity, float(gross_values.sum()/equity), float(gross_values.max(initial=0)/equity)


def _within(cash, units, price, tolerance=1e-9):
    equity, gross, asset = _risk(cash, units, price)
    return equity > 0 and gross <= CAP_GROSS + tolerance and asset <= CAP_ASSET + tolerance


def _intrabar(cash, units, low, high):
    """Adverse OHLC corners; conservative simultaneous extrema, not true path."""
    if not _within(cash,units,low) or not _within(cash,units,high):return False
    for j in range(4):
        p=low.copy();p[j]=high[j]
        if not _within(cash,units,p):return False
    return True


def _fold_metrics(daily, start, end):
    # daily entries are (year, close_NAV, gross, asset), first day's baseline
    # is previous day close or initial NAV (provided explicitly).
    if not daily:
        return {'survived':False,'reason':'empty_fold'}
    prev = float(start)
    returns=[]
    peak=prev
    mdd=0.
    for _,nav,_,_ in daily:
        r=float(nav/prev-1)
        returns.append(r)
        peak=max(peak,nav)
        mdd=min(mdd,nav/peak-1)
        prev=nav
    arr=np.array(returns,dtype=float)
    wins=arr[arr>0];loss=arr[arr<0]
    profit=float(wins.sum());losses=float(-loss.sum())
    factor=(profit/losses if losses>0 else None)
    payoff=(float(wins.mean()/-loss.mean()) if len(wins) and len(loss) else None)
    # CAGR on exact calendar days, not per-bar compounding assumption.
    log_wealth=float(math.log(prev/start))
    years=len(daily)/365.25
    cagr=float(math.expm1(log_wealth/years)) if years else None
    k=max(1,math.ceil(.05*len(arr)))
    return {'survived':True,'days':len(arr),'wealth_multiple':float(prev/start),
            'log_wealth':log_wealth,'cagr':cagr,'max_drawdown':float(mdd),
            'daily_profit_factor':factor,'daily_profit_factor_no_losses':bool(losses==0),
            'daily_payoff':payoff,
            'daily_win_rate':float((arr>0).mean()),'positive_days':int((arr>0).sum()),
            'daily_cvar_5pct':float(np.sort(arr)[:k].mean()),
            'mean_gross':float(np.mean([d[2] for d in daily])),
            'max_gross':float(max(d[2] for d in daily)),
            'max_asset_weight':float(max(d[3] for d in daily))}


def simulate(target, o, h, l, c, quote, rate, mark, event, fee,
             order='carried_before_fill', mode='immediate', years=None):
    """Full fee-inclusive dynamic USD equity and long-only quantities.

    Every t>=1: use target[t-1] and quote[t-1] to fill at open[t].
    Current-hour mark/funding and OHLC extremes used only for accounting
    and ex-post risk rejection, NEVER for order sizing.
    """
    arrays=[np.asarray(x) for x in (target,o,h,l,c,quote,rate,mark,event)]
    w,op,hi,lo,cl,q,fr,mk,ev=arrays
    n=len(w)
    if n<3 or any(a.shape!=(n,4) for a in arrays):raise ValueError('4-asset aligned hourly arrays required')
    if years is None:raise ValueError('explicit calendar years required')
    yy=np.asarray(years)
    if yy.shape!=(n,) or np.any((yy!=2022)&(yy!=2023)&(yy!=2024)):
        raise ValueError('training-only calendar required')
    if order not in ORDERS or mode not in CAPITAL_MODES or fee not in FEE_TIERS.values():
        raise ValueError('unregistered economic cell')
    if (not all(np.isfinite(x).all() for x in (w,op,hi,lo,cl,q,fr)) or
        (w<0).any() or (w.max(axis=1)>CAP_ASSET+1e-10).any() or
        (w.sum(axis=1)>CAP_GROSS+1e-10).any() or (lo<=0).any() or
        (lo>np.minimum(op,cl)).any() or (hi<np.maximum(op,cl)).any() or (q<0).any() or
        np.asarray(ev).dtype!=bool or np.any(~np.isfinite(mk[ev])) or np.any(mk[ev]<=0)):
        raise ValueError('invalid frozen targets or source geometry')
    if np.any(np.isfinite(mk[~ev])):
        raise ValueError('mark only at authenticated funding events')
    if np.any(fr[~ev]!=0):raise ValueError('funding rate without settlement event')
    initial=CAPITAL_MODES[mode]
    cash=initial
    units=np.zeros(4,dtype=float)
    fees=0.;funding=0.;turnover=0.;fills=0;partial=0
    daily=[];prior_daily=initial;equity_last=initial
    reason=None;breach_t=None
    # 2022-12 is signal warmup ONLY, not trading/economic sample.
    for t in range(1,n):
        if yy[t]==2022:continue
        if yy[t] not in (2023,2024):raise ValueError('forbidden year')
        opening=op[t]
        if not _within(cash,units,opening):reason='OPEN_GAP_RISK';breach_t=t;break
        carried=units.copy()
        opening_equity=float(cash+np.dot(units,opening))
        desired=w[t-1]*opening_equity
        budget=np.full(4,math.inf) if mode=='immediate' else PARTICIPATION*q[t-1]
        current=units*opening
        sell=np.minimum(np.maximum(current-desired,0),budget)
        cash+=float(sell.sum()*(1-fee))
        units-=sell/opening
        fees+=float(sell.sum()*fee);turnover+=float(sell.sum());fills+=int((sell>1e-8).sum())
        current=units*opening
        requested=np.maximum(desired-current,0)
        buys=np.minimum(requested,budget)
        # Fee-inclusive leverage constraints; binary search single pro-rata
        # fill factor. No price, high/low, mark or funding at t enters.
        def feasible(k):
            buy=buys*k
            post_cash=cash-float(buy.sum()*(1+fee))
            post_units=units+buy/opening
            return _within(post_cash,post_units,opening)
        if not feasible(0):reason='POST_SELL_CAP_BREACH';breach_t=t;break
        if not feasible(1):
            low_scale=0.;high_scale=1.
            for _ in range(48):
                mid=(low_scale+high_scale)/2
                if feasible(mid):low_scale=mid
                else:high_scale=mid
            buys*=low_scale
        cash-=float(buys.sum()*(1+fee))
        units+=buys/opening
        fees+=float(buys.sum()*fee);turnover+=float(buys.sum());fills+=int((buys>1e-8).sum())
        partial+=int(np.sum(np.abs(units*opening-desired)>1e-6*opening_equity))
        if not _within(cash,units,opening):reason='POST_FILL_CAP_BREACH';breach_t=t;break
        # Funding settlement t is accounting-only; after open execution.
        if ev[t].any():
            held=carried if order=='carried_before_fill' else units
            debit=float(np.sum(held[ev[t]]*mk[t,ev[t]]*fr[t,ev[t]]))
            cash-=debit;funding+=debit
        if not _intrabar(cash,units,lo[t],hi[t]):reason='INTRABAR_SURVIVAL_BREACH';breach_t=t;break
        if not _within(cash,units,cl[t]):reason='CLOSE_SURVIVAL_BREACH';breach_t=t;break
        equity_last=float(cash+np.dot(units,cl[t]))
        # close hour 23 UTC is daily NAV; date arithmetic supplied by calendar
        if t==n-1 or yy[t+1]!=yy[t] or (t%24==23):
            _,gross,asset=_risk(cash,units,cl[t])
            daily.append((int(yy[t]),equity_last,gross,asset))
    out={'survived':reason is None,'reason':reason,'breach_index':breach_t,
         'initial_usd':initial,'terminal_usd':equity_last if reason is None else None,
         'fees_usd':fees,'funding_debit_usd':funding,'turnover_usd':turnover,
         'filled_orders':fills,'partial_asset_hours':partial,
         'daily_nav_observations':len(daily)}
    if reason is None:
        # Never compare 2024 to initial equity: continuous compounding.
        groups={2023:[d for d in daily if d[0]==2023],2024:[d for d in daily if d[0]==2024]}
        base=initial;folds={}
        for year in (2023,2024):
            folds[str(year)]=_fold_metrics(groups[year],base,None)
            if groups[year]:base=groups[year][-1][1]
        out['folds']=folds
        out['total_log_wealth']=float(math.log(equity_last/initial))
        out['total_wealth_multiple']=float(equity_last/initial)
    return out


def complete_matrix(path_targets,prices,quote,rate,mark,event,years):
    """Attempt every one of the 90 preregistered cells, including failures."""
    expected=('K_core_only','K_full','K_minus_opportunity','K_minus_relative_value','K_minus_recovery')
    if tuple(path_targets)!=expected:raise ValueError('frozen K five-path ordering required')
    result={};count=0;failures=[]
    for name,weights in path_targets.items():
        result[name]={}
        for tier,fee in FEE_TIERS.items():
            result[name][tier]={}
            for order in ORDERS:
                result[name][tier][order]={}
                for mode in CAPITAL_MODES:
                    count+=1
                    try:
                        cell=simulate(weights,prices['open'],prices['high'],prices['low'],prices['close'],
                                      quote,rate,mark,event,fee,order=order,mode=mode,years=years)
                    except Exception as exc:
                        cell={'survived':False,'reason':f'{type(exc).__name__}: {str(exc)[:200]}'}
                    if not cell['survived']:failures.append((name,tier,order,mode,cell['reason']))
                    result[name][tier][order][mode]=cell
    assert count==90
    return {'cells_attempted':count,'cells_survived':count-len(failures),
            'failures':failures,'cases':result}


def growth_gate(matrix):
    """Training-only, all scenario edges reported; never cherry-pick first fail."""
    if matrix['cells_attempted']!=90 or matrix['failures']:
        return {'passed':False,'reason':'incomplete_or_failed_survival','failed_cells':len(matrix['failures'])}
    for path in ('K_core_only','K_full','K_minus_opportunity','K_minus_relative_value','K_minus_recovery'):
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    folds=matrix['cases'][path][tier][order][mode].get('folds',{})
                    if set(folds)!=set(('2023','2024')) or folds['2023'].get('days')!=365 or folds['2024'].get('days')!=366:
                        return {'passed':False,'reason':'incomplete_chronological_folds'}
    edges={};failures=[]
    for year in ('2023','2024'):
        for tier in ('base','severe'):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    full=matrix['cases']['K_full'][tier][order][mode]['folds'][year]['log_wealth']
                    key=f'{year}/{tier}/{order}/{mode}'
                    if not math.isfinite(full) or not full>0:
                        failures.append({'scenario':key,'reason':'full_nonpositive_fold_growth','log_wealth':full})
                    marginal={}
                    for other in ('K_core_only','K_minus_opportunity','K_minus_relative_value','K_minus_recovery'):
                        diff=full-matrix['cases'][other][tier][order][mode]['folds'][year]['log_wealth']
                        marginal[other]=diff
                        if not math.isfinite(diff) or not diff>0:
                            failures.append({'scenario':key,'reason':'nonpositive_marginal','path':other,'edge':diff})
                    edges[key]={'full_log_wealth':full,'marginals':marginal}
    return {'passed':not failures,
            'reason':('training_only_pass_requires_separate_validation' if not failures
                      else 'nonpositive_training_growth_or_marginal'),
            'failure_count':len(failures),'failures':failures,'all_edges':edges}

#!/usr/bin/env python3
"""V98 Independent S signed, funded, causal hourly economic kernel.

Pure simulation, no data download, no external engines, no future selection.
All economic input contracts are checked before any PnL. Caller must freeze S after Phase1071–1072 source PASS.
"""
from __future__ import annotations
import math
import numpy as np
from phase1073_s_signed_execution import execute,audit,ASSET_CAP,GROSS_CAP,NET_CAP

FEE_TIERS={'base':.0007,'severe':.0012,'supersevere':.0020}
ORDERS=('carried_before_fill','new_after_fill')
CAPITAL_MODES={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}


def prior_shocks(opening, high, low, window=720):
    """Backward-only 30d worst realized intrabar shocks, no current-bar access."""
    import pandas as pd
    o=np.asarray(opening,float);h=np.asarray(high,float);l=np.asarray(low,float)
    if o.ndim!=2 or o.shape[1]!=4 or h.shape!=o.shape or l.shape!=o.shape or not all(np.isfinite(x).all() for x in (o,h,l)) or (o<=0).any() or (l<=0).any() or (h<o).any() or (l>o).any():
        raise ValueError('S_PRIOR_SHOCK_SOURCE_GEOMETRY')
    d=1-l/o;u=h/o-1
    return (pd.DataFrame(d).rolling(window,min_periods=24).max().to_numpy(),
            pd.DataFrame(u).rolling(window,min_periods=24).max().to_numpy())


def drawdown(values,initial):
    v=np.asarray(values,float)
    if not len(v) or not np.isfinite(v).all() or (v<=0).any():return None
    return float(np.min(v/np.maximum.accumulate(np.r_[initial,v])[1:]-1))


def fold(days,initial):
    v=np.asarray(days,float)
    if len(v)<2 or (v<=0).any():return {'complete':False}
    r=v/np.r_[initial,v[:-1]]-1
    win=r[r>0];lose=r[r<0]
    return {'complete':True,'days':len(v),'terminal':float(v[-1]),
            'log_wealth':float(math.log(v[-1]/initial)),
            'cagr':float((v[-1]/initial)**(365/len(v))-1),
            'max_drawdown':drawdown(v,initial),
            'profit_factor':float(win.sum()/-lose.sum()) if len(lose) else None,
            'payoff':float(win.mean()/-lose.mean()) if len(win) and len(lose) else None,
            'win_rate':float(np.mean(r>0)),'positive_days':int((r>0).sum()),
            'cvar_5pct':float(np.sort(r)[:max(1,int(np.ceil(len(r)*.05)))].mean())}


def simulate(target,op,hi,lo,cl,quote,rate,mark,event,down,up,fee,*,order,mode,years,regimes=None,require_full_sample=True):
    w,o,h,l,c,q,fr,mk,ev,dn,sh=[np.asarray(x) for x in (target,op,hi,lo,cl,quote,rate,mark,event,down,up)]
    n=len(w);yy=np.asarray(years);states=np.ones(n,dtype=int) if regimes is None else np.asarray(regimes)
    if n<1600 or any(x.shape!=(n,4) for x in (w,o,h,l,c,q,fr,ev,dn,sh)) or mk.shape!=(n,4,2) or yy.shape!=(n,) or states.shape!=(n,):
        raise ValueError('S_PREFLIGHT_SOURCE_GEOMETRY')
    if not np.isin(yy,(2022,2023,2024)).all() or not np.isin(states,(0,1,2)).all() or order not in ORDERS or mode not in CAPITAL_MODES or fee not in FEE_TIERS.values():
        raise ValueError('S_PREFLIGHT_TRAINING_CELL')
    if not np.isfinite(w).all():raise ValueError('S_PREFLIGHT_NONFINITE_TARGET')
    if np.abs(w).max()>ASSET_CAP+1e-10 or np.abs(w).sum(axis=1).max()>GROSS_CAP+1e-10 or np.abs(w.sum(axis=1)).max()>NET_CAP+1e-10:
        raise ValueError('S_PREFLIGHT_TARGET_CAP')
    if not all(np.isfinite(x).all() for x in (o,h,l,c,q,fr)) or (o<=0).any() or (l<=0).any() or (q<0).any() or (l>np.minimum(o,c)).any() or (h<np.maximum(o,c)).any():
        raise ValueError('S_PREFLIGHT_PRICE_OR_FUNDING_SOURCE')
    if ev.dtype!=bool or not np.isfinite(mk[ev]).all() or (mk[ev]<=0).any() or (mk[:,:,0][ev]>mk[:,:,1][ev]).any() or np.isfinite(mk[~ev]).any() or (fr[~ev]!=0).any():
        raise ValueError('S_PREFLIGHT_NATIVE_FUNDING')
    if not np.isfinite(dn[24:]).all() or not np.isfinite(sh[24:]).all() or (dn[24:]<0).any() or (dn[24:]>=1).any() or (sh[24:]<0).any():
        raise ValueError('S_PREFLIGHT_PRIOR_SHOCK')
    # 30-day backward-only native funding bound; no future event lookahead.
    import pandas as pd
    maxrate=pd.DataFrame(np.abs(fr)).rolling(720,min_periods=1).max().to_numpy()
    initial=CAPITAL_MODES[mode];cash=initial;units=np.zeros(4)
    fees=funding=turnover=0.;fills=0;daily=[];hourly=[];exposures=[];regime_pnl={0:[],1:[],2:[]}
    reason=None;breach=None;previous=initial
    for t in range(1,n):
        if yy[t]==2022:continue
        pre=cash+float(np.dot(units,o[t]))
        if pre<=0 or not math.isfinite(pre):reason='S_OPEN_EQUITY_NONPOSITIVE';breach=t;break
        carried=units.copy()
        try:
            if t-1<24:
                if np.any(units):raise AssertionError('S_WARMUP_EXPOSURE')
                post={'ok':True,'cash':cash,'units':units.copy(),'fee_usd':0.,'turnover_usd':0.,'trade_usd':np.zeros(4)}
            else:
                buffer=float(np.sum(np.maximum(np.abs(units*o[t]),np.abs(w[t-1]*pre))*maxrate[t-1]))
                post=execute(cash,units,o[t],q[t-1],w[t-1],fee,dn[t-1],sh[t-1],buffer=buffer,mode=mode)
            if not post['ok']:reason=post['reason'];breach=t;break
            cash=float(post['cash']);units=post['units'].copy()
            fees+=post['fee_usd'];turnover+=post['turnover_usd'];fills+=int(np.count_nonzero(np.abs(post['trade_usd'])>1e-8))
            if ev[t].any():
                held=carried if order=='carried_before_fill' else units
                signed=held[ev[t]]*fr[t,ev[t]]
                mark_adverse=np.where(signed>=0,mk[t,ev[t],1],mk[t,ev[t],0])
                debit=float(np.sum(signed*mark_adverse));cash-=debit;funding+=debit
            actual=audit(cash,units,o[t],1-l[t]/o[t],h[t]/o[t]-1,baseline=pre)
            if not actual['ok']:reason='S_INTRABAR_'+actual['reason'];breach=t;break
            closing=audit(cash,units,c[t],np.zeros(4),np.zeros(4),baseline=pre)
            if not closing['ok']:reason='S_CLOSE_'+closing['reason'];breach=t;break
            nav=cash+float(np.dot(units,c[t]))
            hourly.append((int(yy[t]),nav))
            exposures.append(np.abs(units*c[t])/nav)
            if previous>0 and nav>0:regime_pnl[int(states[t-1])].append(float(math.log(nav/previous)))
            previous=nav
            if t==n-1 or yy[t+1]!=yy[t] or t%24==23:daily.append((int(yy[t]),nav))
        except Exception as e:
            reason=type(e).__name__+': '+str(e)[:150];breach=t;break
    result={'survived':reason is None,'reason':reason,'breach_index':breach,
            'fees_usd':float(fees),'funding_debit_usd':float(funding),
            'turnover_usd':float(turnover),'filled_orders':fills,
            'hourly_nav_observations':len(hourly),'daily_nav_observations':len(daily),
            'initial_usd':initial,'terminal_usd':float(hourly[-1][1]) if reason is None and hourly else None}
    if reason is None:
        prev=initial;folds={}
        for year,days,hours in ((2023,365,8760),(2024,366,8784)):
            d=[v for y,v in daily if y==year];hvals=[v for y,v in hourly if y==year]
            folds[str(year)]=fold(d,prev)
            folds[str(year)]['hourly_max_drawdown']=drawdown(hvals,prev)
            folds[str(year)]['hourly_observations']=len(hvals)
            if require_full_sample and (len(d)!=days or len(hvals)!=hours):
                raise ValueError('S_INCOMPLETE_CHRONOLOGICAL_FOLD')
            if d:prev=d[-1]
        result['folds']=folds
        result['total_log_wealth']=float(math.log(prev/initial))
        result['total_wealth_multiple']=float(prev/initial)
        result['all_hourly_max_drawdown']=drawdown([v for _,v in hourly],initial)
        xp=np.asarray(exposures,float)
        if len(xp):
            a=xp.sum(axis=0);s=a/a.sum() if a.sum()>0 else np.zeros(4)
            result['concentration']={'asset_exposure_shares':s.tolist(),
                'asset_hhi':float(np.square(s).sum()),'max_asset_weight':float(xp.max()),
                'max_gross':float(xp.sum(axis=1).max()),'mean_gross':float(xp.sum(axis=1).mean())}
        result['regime_log_wealth']={str(k):float(sum(v)) for k,v in regime_pnl.items()}
        result['regime_hours']={str(k):len(v) for k,v in regime_pnl.items()}
        hv=np.asarray([v for _,v in hourly],float);ret=hv/np.r_[initial,hv[:-1]]-1
        result['hourly_cvar_5pct']=float(np.sort(ret)[:max(1,int(np.ceil(len(ret)*.05)))].mean())
        result['positive_hours']=int((ret>0).sum())
    return result

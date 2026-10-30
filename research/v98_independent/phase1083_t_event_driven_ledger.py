#!/usr/bin/env python3
"""V98 T causal signed event-driven funded ledger. No data downloads or alpha reuse.
Read-only V98 mechanical 16-corner oracle and chronological metrics; not S signals.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from phase1073_s_signed_execution import execute,audit,ASSET_CAP,GROSS_CAP,NET_CAP
from phase1074_s_funded_ledger import prior_shocks,drawdown,fold,FEE_TIERS,ORDERS,CAPITAL_MODES

def simulate_t(target,op,hi,lo,cl,quote,rate,mark,event,down,up,fee,*,order,mode,years,regimes=None):
    w,o,h,l,c,q,fr,mk,ev,dn,sh=[np.asarray(x) for x in (target,op,hi,lo,cl,quote,rate,mark,event,down,up)]
    n=len(w);yy=np.asarray(years);states=np.ones(n,dtype=int) if regimes is None else np.asarray(regimes)
    if n<1600 or any(x.shape!=(n,4) for x in (w,o,h,l,c,q,fr,ev,dn,sh)) or mk.shape!=(n,4,2) or yy.shape!=(n,) or states.shape!=(n,):
        raise ValueError('T_PREFLIGHT_SOURCE_GEOMETRY')
    if (not np.isin(yy,(2022,2023,2024)).all() or not np.isin(states,(0,1,2)).all() or
        order not in ORDERS or mode not in CAPITAL_MODES or fee not in FEE_TIERS.values()):
        raise ValueError('T_PREFLIGHT_TRAINING_CELL')
    if (not np.isfinite(w).all() or np.abs(w).max()>ASSET_CAP+1e-10 or
        np.abs(w).sum(axis=1).max()>GROSS_CAP+1e-10 or np.abs(w.sum(axis=1)).max()>NET_CAP+1e-10):
        raise ValueError('T_PREFLIGHT_TARGET')
    if (not all(np.isfinite(x).all() for x in (o,h,l,c,q,fr)) or
        (o<=0).any() or (l<=0).any() or (q<0).any() or
        (l>np.minimum(o,c)).any() or (h<np.maximum(o,c)).any()):
        raise ValueError('T_PREFLIGHT_PRICE')
    if (ev.dtype!=bool or not np.isfinite(mk[ev]).all() or (mk[ev]<=0).any() or
        (mk[:,:,0][ev]>mk[:,:,1][ev]).any() or np.isfinite(mk[~ev]).any() or (fr[~ev]!=0).any()):
        raise ValueError('T_PREFLIGHT_FUNDING')
    if (not np.isfinite(dn[24:]).all() or not np.isfinite(sh[24:]).all() or
        (dn[24:]<0).any() or (dn[24:]>=1).any() or (sh[24:]<0).any()):
        raise ValueError('T_PREFLIGHT_SHOCK')
    maxrate=pd.DataFrame(np.abs(fr)).rolling(720,min_periods=1).max().to_numpy()
    initial=CAPITAL_MODES[mode];cash=initial;units=np.zeros(4)
    fees=funding=turnover=0.;fills=0;daily=[];hourly=[];exposures=[]
    regime_pnl={0:[],1:[],2:[]};reason=None;breach=None;previous=initial
    signal_changes=0;risk_repairs=0;skipped_rebalances=0
    for t in range(1,n):
        if yy[t]==2022:continue
        pre=cash+float(np.dot(units,o[t]))
        if pre<=0 or not math.isfinite(pre):reason='T_OPEN_EQUITY_NONPOSITIVE';breach=t;break
        carried=units.copy()
        try:
            if t-1<24:
                if np.any(units):raise AssertionError('T_WARMUP_EXPOSURE')
                post={'ok':True,'cash':cash,'units':units.copy(),'fee_usd':0.,
                      'turnover_usd':0.,'trade_usd':np.zeros(4)}
            else:
                buffer=float(np.sum(np.maximum(np.abs(units*o[t]),np.abs(w[t-1]*pre))*maxrate[t-1]))
                target_changed=(t==1 or not np.array_equal(w[t-1],w[t-2]))
                safe=audit(cash,units,o[t],dn[t-1],sh[t-1],baseline=pre,buffer=buffer)
                if target_changed or not safe['ok']:
                    post=execute(cash,units,o[t],q[t-1],w[t-1],fee,dn[t-1],sh[t-1],buffer=buffer,mode=mode)
                    signal_changes+=int(target_changed)
                    risk_repairs+=int(not safe['ok'])
                else:
                    skipped_rebalances+=1
                    post={'ok':True,'cash':cash,'units':units.copy(),'fee_usd':0.,
                          'turnover_usd':0.,'trade_usd':np.zeros(4)}
            if not post['ok']:reason=post['reason'];breach=t;break
            cash=float(post['cash']);units=post['units'].copy()
            fees+=post['fee_usd'];turnover+=post['turnover_usd']
            fills+=int(np.count_nonzero(np.abs(post['trade_usd'])>1e-8))
            if ev[t].any():
                held=carried if order=='carried_before_fill' else units
                signed=held[ev[t]]*fr[t,ev[t]]
                adverse=np.where(signed>=0,mk[t,ev[t],1],mk[t,ev[t],0])
                debit=float(np.sum(signed*adverse));cash-=debit;funding+=debit
            actual=audit(cash,units,o[t],1-l[t]/o[t],h[t]/o[t]-1,baseline=pre)
            if not actual['ok']:reason='T_INTRABAR_'+actual['reason'];breach=t;break
            closing=audit(cash,units,c[t],np.zeros(4),np.zeros(4),baseline=pre)
            if not closing['ok']:reason='T_CLOSE_'+closing['reason'];breach=t;break
            nav=cash+float(np.dot(units,c[t]));hourly.append((int(yy[t]),nav))
            exposures.append(np.abs(units*c[t])/nav)
            if previous>0 and nav>0:regime_pnl[int(states[t-1])].append(float(math.log(nav/previous)))
            previous=nav
            if t==n-1 or yy[t+1]!=yy[t] or t%24==23:daily.append((int(yy[t]),nav))
        except Exception as e:
            reason=type(e).__name__+': '+str(e)[:150];breach=t;break
    result={'survived':reason is None,'reason':reason,'breach_index':breach,
            'fees_usd':float(fees),'funding_debit_usd':float(funding),
            'turnover_usd':float(turnover),'filled_orders':fills,
            'signal_changes':signal_changes,'risk_repairs':risk_repairs,
            'skipped_rebalances':skipped_rebalances,
            'hourly_nav_observations':len(hourly),'daily_nav_observations':len(daily),
            'initial_usd':initial,'terminal_usd':float(hourly[-1][1]) if reason is None and hourly else None}
    if reason is None:
        prev=initial;folds={}
        for year,days,hours in ((2023,365,8760),(2024,366,8784)):
            d=[v for y,v in daily if y==year];hvals=[v for y,v in hourly if y==year]
            folds[str(year)]=fold(d,prev)
            folds[str(year)]['hourly_max_drawdown']=drawdown(hvals,prev)
            folds[str(year)]['hourly_observations']=len(hvals)
            if len(d)!=days or len(hvals)!=hours:raise ValueError('T_INCOMPLETE_CHRONOLOGICAL_FOLD')
            if d:prev=d[-1]
        result['folds']=folds
        result['total_log_wealth']=float(math.log(prev/initial))
        result['total_wealth_multiple']=float(prev/initial)
        result['all_hourly_max_drawdown']=drawdown([v for _,v in hourly],initial)
        xp=np.asarray(exposures,float)
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

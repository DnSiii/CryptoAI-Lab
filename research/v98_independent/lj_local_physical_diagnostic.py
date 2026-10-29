#!/usr/bin/env python3
"""LJ conservative local signed physical TRAIN diagnostic, rejection-only (not independent oracle)."""
from __future__ import annotations
import argparse,json,math
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from lj_sources import bundle,PATHS
from lj_independent_source_gate import run as source_gate
INITIAL=10000.
COSTS={'base':(.0004,.0002),'severe':(.0010,.0010),'supersevere':(.0015,.0020)}
INCLUDE={'LJ_core_only':(0,),'LJ_full':(0,1,2,3),'LJ_minus_opportunity':(0,2,3),
         'LJ_minus_RV':(0,1,3),'LJ_minus_stress':(0,1,2)}

def physical(data,intents,updates,path,tier,order):
    o,h,l,c,rate,mark,event=(data[k] for k in ('o','h','l','c','rate','mark','event'))
    fee,slip=COSTS[tier]
    include=INCLUDE[path];qty=np.zeros((4,4));equity=INITIAL
    prev=c[WARMUP];equity_history=[];turnover=0.;fees=0.;slippage=0.;funding=0.
    clipped=0;gross_breaches=0;min_intrabar_equity=INITIAL;trades=[]
    annual_start={2023:INITIAL,2024:None};annual_end={}
    for t in range(WARMUP+1,HOURS):
        px=o[t];equity+=float(np.sum(qty*(px-prev)))
        if equity<=0 or not math.isfinite(equity):
            return {'passed':False,'failure':'INSOLVENT_OPEN','t':t,'path':path,'tier':tier,'order':order}
        # Native funding before fills: carried inventory settles at the timestamp.
        if order=='carried_before_fill' and event[t].any():
            cash=-float(np.nansum(qty.sum(axis=0)[event[t]]*mark[t,event[t]]*rate[t,event[t]]))
            equity+=cash;funding+=cash
        # Apply completed t-1 source changes at actual t open. Exit first; no funding/order hindsight.
        source_t=t-1
        if np.any(updates[source_t,list(include)]):
            for k in include:
                if not updates[source_t,k]:continue
                old=qty[k].copy()
                notional=float(np.sum(np.abs(old)*px))
                if notional:
                    cost=notional*(fee+slip);equity-=cost
                    turnover+=notional;fees+=notional*fee;slippage+=notional*slip
                    trades.append(float(np.dot(old,px-prev))-cost)
                qty[k]=0
            for k in include:
                if not updates[source_t,k]:continue
                target=intents[source_t,k].copy()
                # Signed gross of independently financed rows; never net opposing inventory.
                occupied=float(np.sum(np.abs(qty)*px))
                available=max(0.,.95*equity-occupied)
                requested=float(np.sum(np.abs(target))*equity)
                if requested>available+1e-8:
                    clipped+=1
                    target*=max(0.,available/max(requested,1e-12))
                new=target*equity/px
                notional=float(np.sum(np.abs(new)*px))
                if notional:
                    cost=notional*(fee+slip);equity-=cost
                    turnover+=notional;fees+=notional*fee;slippage+=notional*slip
                qty[k]=new
        # Native funding after new fills is the alternative boundary permutation.
        if order=='new_after_fill' and event[t].any():
            cash=-float(np.nansum(qty.sum(axis=0)[event[t]]*mark[t,event[t]]*rate[t,event[t]]))
            equity+=cash;funding+=cash
        # Prior-only risk governor: if open notional breaches 95% of equity, deleverage at current open.
        gross=float(np.sum(np.abs(qty)*px))
        if gross>.95*equity and gross>0:
            fraction=max(0.,(.93*equity)/gross)
            removed=qty*(1-fraction)
            notional=float(np.sum(np.abs(removed)*px))
            cost=notional*(fee+slip)
            qty*=fraction;equity-=cost
            turnover+=notional;fees+=notional*fee;slippage+=notional*slip;clipped+=1
        gross=float(np.sum(np.abs(qty)*px))
        if gross>.95*equity+1e-6:gross_breaches+=1
        # 81 OHLC corner extrema reduce to low for net longs/high for net shorts
        # under linear mark-to-market; not a separate settlement oracle.
        net=qty.sum(axis=0)
        worst=np.where(net>=0,l[t],h[t])
        intrabar=equity+float(np.dot(net,worst-px))
        min_intrabar_equity=min(min_intrabar_equity,intrabar)
        equity+=float(np.dot(net,c[t]-px))
        prev=c[t]
        equity_history.append(equity)
        if t==9503:annual_end[2023]=equity;annual_start[2024]=equity
        if equity<=0 or not math.isfinite(equity):
            return {'passed':False,'failure':'INSOLVENT_CLOSE','t':t,'path':path,'tier':tier,'order':order}
    annual_end[2024]=equity
    curve=np.array(equity_history)
    peak=np.maximum.accumulate(np.r_[INITIAL,curve]);dd=float(np.min(np.r_[INITIAL,curve]/peak-1))
    daily=curve[23::24];day_rets=np.diff(np.r_[INITIAL,daily])/np.r_[INITIAL,daily[:-1]]
    wins=[x for x in trades if x>0];losses=[x for x in trades if x<0]
    years={str(y):float(annual_end[y]/annual_start[y]-1) for y in (2023,2024)}
    return {'passed':not gross_breaches and min_intrabar_equity>0,'path':path,'tier':tier,'order':order,
      'final_equity':float(equity),'cagr':float((equity/INITIAL)**.5-1),'net_log_growth':float(np.log(equity/INITIAL)),
      'year_returns':years,'max_drawdown':dd,'turnover_usd':turnover,'fees_usd':fees,'slippage_usd':slippage,
      'funding_cash_usd':funding,'clipped_events':clipped,'gross_breaches':gross_breaches,
      'min_intrabar_equity':min_intrabar_equity,'positive_days':int(np.sum(day_rets>0)),
      'daily_count':len(day_rets),'cvar_1pct':float(np.mean(np.sort(day_rets)[:max(1,len(day_rets)//100)])),
      'win_rate':float(len(wins)/max(1,len(trades))),'profit_factor':float(sum(wins)/max(1,-sum(losses))),
      'payoff':float(np.mean(wins)/max(1e-12,-np.mean(losses))) if wins and losses else None}

def run(root,tiers,orders):
    gate=source_gate(root)
    if gate['decision']!='PASS_SOURCE_ONLY':raise ValueError('LJ_SOURCE_REJECT_NO_PNL')
    data=load(root);src=bundle(*(data[x] for x in ('o','h','l','c','q','rate','event')))
    intents,updates=src[:2];cells=[]
    for tier in tiers:
        for order in orders:
            for path in PATHS:
                result=physical(data,intents,updates,path,tier,order)
                cells.append(result)
                print('LJ_DIAG',tier,order,path,'CAGR',round(result.get('cagr',-2)*100,3),
                      'TURNOVER',round(result.get('turnover_usd',-1)),flush=True)
    full={(c['tier'],c['order']):c for c in cells if c['path']=='LJ_full'}
    marginals={}
    for tier in tiers:
        for order in orders:
            f=full[(tier,order)];key=tier+'/'+order;marginals[key]={}
            for name,path in [('Opportunity','LJ_minus_opportunity'),('Relative_Value','LJ_minus_RV'),('Stress_Recovery','LJ_minus_stress')]:
                a=next(c for c in cells if c['tier']==tier and c['order']==order and c['path']==path)
                marginals[key][name]=float(f['net_log_growth']-a['net_log_growth'])
    return {'architecture':'LJ','training_only':True,'source_gate':gate,
            'local_diagnostic_only':True,'original_github_30cell_run':False,
            'independent_settlement_oracle_completed':False,'eligible_for_promotion':False,
            'holdout_2025_read':False,'external_benchmarks_used':False,'cells':cells,'marginals':marginals}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    p.add_argument('--tiers',nargs='+',default=['base','severe'],choices=tuple(COSTS))
    p.add_argument('--orders',nargs='+',default=['carried_before_fill'],choices=('carried_before_fill','new_after_fill'))
    a=p.parse_args();r=run(a.root,a.tiers,a.orders)
    open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('LJ_LOCAL_DIAGNOSTIC_ONLY',json.dumps(r['marginals'],indent=2))

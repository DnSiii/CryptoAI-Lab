#!/usr/bin/env python3
"""V98 LO local signed physical training diagnostic. May REJECT, never PROMOTE."""
from __future__ import annotations
import argparse,json,math
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from lo_sources import bundle,PATHS
from lo_independent_source_gate import run as source_gate
INITIAL=10000.
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
INCLUDE={'LO_core_only':(0,),'LO_full':(0,1,2,3),'LO_minus_opportunity':(0,2,3),
         'LO_minus_RV':(0,1,3),'LO_minus_stress':(0,1,2)}

def physical(data,intents,updates,path,tier,order):
    o,h,l,c,rate,mark,event=(data[k] for k in ('o','h','l','c','rate','mark','event'))
    fee,slip=COSTS[tier];include=INCLUDE[path]
    qty=np.zeros((4,4));equity=INITIAL;prev=c[WARMUP]
    hist=[];turnover=fees=slippage=funding=0.;clipped=breaches=0;min_intra=INITIAL
    annual_start={2023:INITIAL,2024:None};annual_end={}
    for t in range(WARMUP+1,HOURS):
        px=o[t];equity+=float(np.sum(qty*(px-prev)))
        if equity<=0 or not math.isfinite(equity):
            return {'passed':False,'failure':'INSOLVENT_OPEN','t':t,'path':path,'tier':tier,'order':order}
        if order=='carried_before_fill' and event[t].any():
            cash=-float(np.nansum(qty.sum(axis=0)[event[t]]*mark[t,event[t]]*rate[t,event[t]]))
            equity+=cash;funding+=cash
        if np.any(updates[t-1,list(include)]):
            for k in include:
                if not updates[t-1,k]:continue
                old=qty[k].copy();notional=float(np.sum(np.abs(old)*px))
                if notional:
                    equity-=notional*(fee+slip);turnover+=notional
                    fees+=notional*fee;slippage+=notional*slip
                qty[k]=0
            for k in include:
                if not updates[t-1,k]:continue
                target=intents[t-1,k].copy()
                occupied=float(np.sum(np.abs(qty)*px));available=max(0.,.95*equity-occupied)
                requested=float(np.sum(np.abs(target))*equity)
                if requested>available+1e-8:
                    clipped+=1;target*=max(0.,available/max(requested,1e-12))
                new=target*equity/px;notional=float(np.sum(np.abs(new)*px))
                if notional:
                    equity-=notional*(fee+slip);turnover+=notional
                    fees+=notional*fee;slippage+=notional*slip
                qty[k]=new
        if order=='new_after_fill' and event[t].any():
            cash=-float(np.nansum(qty.sum(axis=0)[event[t]]*mark[t,event[t]]*rate[t,event[t]]))
            equity+=cash;funding+=cash
        gross=float(np.sum(np.abs(qty)*px))
        if gross>.95*equity and gross>0:
            frac=max(0.,(.93*equity)/gross);removed=qty*(1-frac)
            notional=float(np.sum(np.abs(removed)*px));cost=notional*(fee+slip)
            qty*=frac;equity-=cost;turnover+=notional;fees+=notional*fee;slippage+=notional*slip;clipped+=1
        gross=float(np.sum(np.abs(qty)*px))
        if gross>.95*equity+1e-6:breaches+=1
        net=qty.sum(axis=0);worst=np.where(net>=0,l[t],h[t])
        intra=equity+float(np.dot(net,worst-px));min_intra=min(min_intra,intra)
        equity+=float(np.dot(net,c[t]-px));prev=c[t]
        hist.append(equity)
        if t==9503:annual_end[2023]=equity;annual_start[2024]=equity
        if equity<=0 or not math.isfinite(equity):
            return {'passed':False,'failure':'INSOLVENT_CLOSE','t':t,'path':path,'tier':tier,'order':order}
    annual_end[2024]=equity
    curve=np.asarray(hist);peak=np.maximum.accumulate(np.r_[INITIAL,curve]);dd=float(np.min(np.r_[INITIAL,curve]/peak-1))
    daily=curve[23::24];daily_returns=np.diff(np.r_[INITIAL,daily])/np.r_[INITIAL,daily[:-1]]
    return {'passed':not breaches and min_intra>0,'path':path,'tier':tier,'order':order,
      'final_equity':float(equity),'cagr':float((equity/INITIAL)**.5-1),'net_log_growth':float(np.log(equity/INITIAL)),
      'year_returns':{str(y):float(annual_end[y]/annual_start[y]-1) for y in (2023,2024)},
      'max_drawdown':dd,'turnover_usd':turnover,'fees_usd':fees,'slippage_usd':slippage,
      'funding_cash_usd':funding,'clipped_events':clipped,'gross_breaches':breaches,
      'min_intrabar_equity':min_intra,'positive_days':int(np.sum(daily_returns>0)),
      'daily_count':len(daily_returns),'cvar_1pct':float(np.mean(np.sort(daily_returns)[:max(1,len(daily_returns)//100)])),
      'pf_payoff_win_rate_not_independently_reconciled':True}

def run(root,tiers,orders):
    gate=source_gate(root)
    if gate['decision']!='PASS_SOURCE_ONLY':raise ValueError('LO_SOURCE_REJECT_NO_PNL')
    data=load(root);intents,updates=bundle(*(data[x] for x in ('o','h','l','c','q','rate','event')))[:2]
    cells=[]
    for tier in tiers:
        for order in orders:
            for path in PATHS:
                r=physical(data,intents,updates,path,tier,order);cells.append(r)
                print('LO_DIAG',tier,order,path,'CAGR',round(r.get('cagr',-2)*100,3),'TURNOVER',round(r.get('turnover_usd',-1)),flush=True)
    marginals={}
    for tier in tiers:
        for order in orders:
            key=tier+'/'+order
            full=next(c for c in cells if c['tier']==tier and c['order']==order and c['path']=='LO_full')
            marginals[key]={}
            for name,path in [('Opportunity','LO_minus_opportunity'),('Relative_Value','LO_minus_RV'),('Stress_Recovery','LO_minus_stress')]:
                ablated=next(c for c in cells if c['tier']==tier and c['order']==order and c['path']==path)
                marginals[key][name]=float(full['net_log_growth']-ablated['net_log_growth'])
    return {'architecture':'LO','training_only':True,'source_gate':gate,'local_diagnostic_only':True,
      'original_github_30cell_run':False,'independent_settlement_oracle_completed':False,
      'eligible_for_promotion':False,'holdout_read':False,'benchmark_used':False,
      'cells':cells,'marginals':marginals}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    p.add_argument('--tiers',nargs='+',default=['base','severe'],choices=tuple(COSTS))
    p.add_argument('--orders',nargs='+',default=['carried_before_fill'],choices=('carried_before_fill','new_after_fill'))
    a=p.parse_args();r=run(a.root,a.tiers,a.orders)
    open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('LO_LOCAL_MARGINALS',json.dumps(r['marginals'],indent=2))

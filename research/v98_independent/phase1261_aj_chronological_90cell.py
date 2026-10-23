#!/usr/bin/env python3
"""V98 AJ1261 frozen chronological 2023/2024 90-cell training; no holdout."""
from __future__ import annotations
import argparse
import itertools
import json
import math
import numpy as np
from phase1246_ai_two_stage_margin import settle_hour
from phase1255_aj_signed_sources import source_bundle
from phase1256_aj_wealth_allocator import AJWealthAllocator
from phase1257_aj_open_viability_governor import aj_governor,FEES,ORDERS
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from phase1258_aj_complete_180cell import PATHS,CAPITAL

WARMUP=744
YEAR_2024=9504

def prior_risk(frames):
    o,h,l,c,q,r,e,ml,mh=frames
    d=np.zeros((HOURS,4))
    u=np.zeros((HOURS,4))
    f=np.zeros((HOURS,4))
    qmin=np.zeros((HOURS,4))
    for t in range(WARMUP,HOURS):
        sl=slice(t-336,t)
        d[t]=np.maximum(.45,np.max(1-l[sl]/o[sl],axis=0))
        u[t]=np.maximum(.80,np.max(h[sl]/o[sl]-1,axis=0))
        f[t]=np.maximum(.0005,3*np.max(np.abs(
            r[t-720:t]*e[t-720:t]),axis=0))
        qmin[t]=np.min(q[sl],axis=0)
    return d,u,f,qmin

def metrics_hourly(net_dollars,net_returns,positive_days,total_days):
    x=np.asarray(net_dollars,dtype=float)
    z=np.asarray(net_returns,dtype=float)
    wins=x[x>1e-10]
    losses=-x[x< -1e-10]
    pf=(float(wins.sum()/losses.sum()) if len(losses) and
        losses.sum()>0 else None)
    payoff=(float(wins.mean()/losses.mean()) if len(wins) and
            len(losses) else None)
    win_rate=(float(len(wins)/(len(wins)+len(losses))) if
              len(wins)+len(losses) else 0.)
    if len(z):
        var=float(np.quantile(z,.01))
        cvar=float(np.mean(z[z<=var]))
        worst=float(np.min(z))
    else:
        var=cvar=worst=None
    return {'hourly_net_profit_factor':pf,
            'hourly_net_payoff':payoff,
            'hourly_net_win_rate':win_rate,
            'positive_utc_days':positive_days,
            'total_utc_days':total_days,
            'positive_day_fraction':positive_days/total_days if total_days else 0.,
            'worst_hour_net_return':worst,
            'hourly_var_1pct':var,'hourly_cvar_1pct':cvar,
            'positive_hours':int(len(wins)),
            'negative_hours':int(len(losses))}

def cell(path,mode,fee,order,frames,slots,risk):
    o,h,l,c,q,r,e,ml,mh=frames
    growth,op,rv,stress,router=slots
    d,u,f,qmin=risk
    cash=CAPITAL[mode]
    old=np.zeros(4)
    pending=np.zeros(4)
    allocator=AJWealthAllocator()
    initial=cash
    peak=cash
    max_dd=0.
    min_nav=cash
    turnover=fees=slippage=funding=0.
    rebalances=0
    max_gross=0.
    max_net=0.
    max_concentration=0.
    year_start={'2023':cash}
    year_end={}
    year_peak={'2023':cash}
    year_dd={'2023':0.,'2024':0.}
    dollars={'2023':[],'2024':[]}
    returns={'2023':[],'2024':[]}
    positive_days={'2023':0,'2024':0}
    total_days={'2023':0,'2024':0}
    day_start=cash
    for t in range(HOURS):
        if t>=WARMUP:
            year='2023' if t<YEAR_2024 else '2024'
            if t==YEAR_2024:
                year_start['2024']=cash
                year_peak['2024']=cash
                day_start=cash
            prior_cash=cash
            try:
                kw=dict(cash_previous=cash,old_units=old,
                    prior_close=c[t-1],opening=o[t],
                    prior_down=d[t],prior_up=u[t],
                    funding_bound=f[t],prior_quote=q[t-1],
                    min_quote=qmin[t],fee_mode=fee,
                    funding_order=order)
                target=aj_governor(signed_target=pending,**kw)
                out=settle_hour(cash,old,c[t-1],o[t],h[t],l[t],c[t],
                    target['units'],r[t],e[t],ml[t],mh[t],
                    fee_mode=fee,funding_order=order)
            except Exception as exc:
                raise ValueError('AJ1261_T'+str(t)+'_'+str(exc)) from exc
            cash=out['cash']
            old=out['units']
            if (out['hidden_borrow'] or not out['cash_settled'] or
                not np.isclose(out['equity'],cash,atol=1e-7,rtol=0)):
                raise ValueError('AJ1261_NAV_RECONCILIATION_T'+str(t))
            net_delta=cash-prior_cash
            dollars[year].append(float(net_delta))
            returns[year].append(float(net_delta/prior_cash))
            turnover+=out['turnover']
            fees+=out['fees']
            slippage+=out['slippage']
            funding+=out['funding']
            rebalances+=int(out['turnover']>1e-10)
            peak=max(peak,cash)
            min_nav=min(min_nav,cash)
            max_dd=max(max_dd,1-cash/peak)
            year_peak[year]=max(year_peak[year],cash)
            year_dd[year]=max(year_dd[year],1-cash/year_peak[year])
            notionals=np.abs(old*c[t])
            gross=float(notionals.sum())
            if gross>0:
                max_concentration=max(max_concentration,
                                      float(notionals.max()/gross))
            max_gross=max(max_gross,gross/cash)
            max_net=max(max_net,abs(float(old@c[t]))/cash)
            if t%24==23:
                total_days[year]+=1
                positive_days[year]+=int(cash>day_start)
                day_start=cash
            if t==YEAR_2024-1:
                year_end['2023']=cash
            if t==HOURS-1:
                year_end['2024']=cash
        s=np.stack((growth[t],op[t],rv[t],stress[t]))
        if path=='AJ_core_only':
            s[1:]=0.
        if path=='AJ_minus_opportunity':
            s[1]=0.
        if path=='AJ_minus_RV':
            s[2]=0.
        if path=='AJ_minus_stress':
            s[3]=0.
        lr=np.log(c[t]/c[t-1]) if t else np.zeros(4)
        allocator.observe(lr,r[t],e[t])
        decision=allocator.decide(s,str(router['state'][t]))
        pending=decision['signed_target']
    annual={}
    for year in ('2023','2024'):
        start=year_start[year]
        end=year_end[year]
        days=365 if year=='2023' else 366
        annual[year]={
            'start_nav':float(start),'end_nav':float(end),
            'net_return':float(end/start-1),
            'annualized_cagr':float((end/start)**(365.25/days)-1),
            'net_log_growth':float(math.log(end/start)),
            'max_drawdown':float(year_dd[year]),
            **metrics_hourly(dollars[year],returns[year],
                             positive_days[year],total_days[year])}
    combined_dollars=dollars['2023']+dollars['2024']
    combined_returns=returns['2023']+returns['2024']
    return {'path':path,'mode':mode,'fee':fee,'order':order,
        'passed':True,'historical_training_only':True,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'executed_hours':HOURS-WARMUP,'rebalances':rebalances,
        'initial_nav':float(initial),'final_nav':float(cash),
        'net_total_return':float(cash/initial-1),
        'net_log_growth':float(math.log(cash/initial)),
        'two_year_cagr':float((cash/initial)**(365.25/731)-1),
        'min_nav':float(min_nav),'max_drawdown':float(max_dd),
        'max_gross_to_nav':float(max_gross),
        'max_abs_net_to_nav':float(max_net),
        'max_single_asset_gross_concentration':float(max_concentration),
        'turnover':float(turnover),'fees':float(fees),
        'slippage':float(slippage),'funding':float(funding),
        'annual':annual,
        **metrics_hourly(combined_dollars,combined_returns,
            positive_days['2023']+positive_days['2024'],
            total_days['2023']+total_days['2024'])}

def run(path):
    if path not in PATHS:
        raise ValueError('AJ1261_UNKNOWN_PATH')
    frames,manifest=load_official()
    slots=source_bundle(frames[3],frames[1],frames[2],
                        frames[5],frames[6])
    risk=prior_risk(frames)
    cells=[]
    for mode,fee,order in itertools.product(CAPITAL,FEES,ORDERS):
        try:
            cells.append(cell(path,mode,fee,order,frames,slots,risk))
        except Exception as exc:
            msg=type(exc).__name__+': '+str(exc)
            cells.append({'path':path,'mode':mode,'fee':fee,'order':order,
                'passed':False,'reason':msg[:350],
                'historical_training_only':True,
                'validation_2025_read':False})
    return {'phase':1261,'architecture':'AJ','path':path,
        'cells':cells,'cells_expected':18,'historical_training_only':True,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'source_manifest_sha256':manifest['calendar_sha256'],
        'decision':('PASS_AJ1261_PATH_18_TRAINING_CELLS' if
            len(cells)==18 and all(x['passed'] for x in cells) else
            'REJECT_AJ1261_PATH_TRAINING_SURVIVAL')}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--path',required=True,choices=PATHS)
    p.add_argument('--output',default='aj1261_90cell_path_receipt.json')
    args=p.parse_args()
    receipt=run(args.path)
    with open(args.output,'w') as f:
        json.dump(receipt,f,sort_keys=True,indent=2,allow_nan=False)
    failures=[x for x in receipt['cells'] if not x['passed']]
    print('AJ1261_TRAINING',json.dumps({
        'path':args.path,'decision':receipt['decision'],
        'passed':len(receipt['cells'])-len(failures),
        'failed':len(failures),'first_failures':failures[:5]},
        sort_keys=True))
    raise SystemExit(0 if not failures else 2)

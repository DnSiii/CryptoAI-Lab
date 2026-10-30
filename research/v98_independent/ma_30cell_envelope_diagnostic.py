#!/usr/bin/env python3
"""V98 MA 30-cell signed native training diagnostic, rejection-only; never promotion."""
import argparse,json,math,numpy as np
from v98_clean4_training_reader import load
from ma_sources import bundle,HOURS,WARMUP,BOOKS
from ma_independent_source_gate import run as source_gate
from v98_mark_envelope_settlement import read_envelope,worst_funding
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}

def physical(d,intents,updates,book,tier,order,lo,hi):
    o,h,l,c,rate,mark,event=[d[k] for k in ('o','h','l','c','rate','mark','event')]
    fee,slip=COSTS[tier];active=BOOKS[book]
    qty=np.zeros((4,4));equity=10000.;prev=c[WARMUP]
    turn=fees=slippage=funding=0.;clipped=breaches=0;intramin=10000.;year_start={2023:10000.,2024:None};year_end={}
    hist=[];deltas=[];grosspeak=0.;concpeak=0.
    for t in range(WARMUP+1,HOURS):
        before=equity;px=o[t];equity+=float(np.sum(qty*(px-prev)))
        if equity<=0 or not math.isfinite(equity):return {'passed':False,'failure':'INSOLVENT_OPEN','t':t,'book':book,'tier':tier,'order':order}
        if order=='carried_before_fill' and event[t].any():
            f=worst_funding(qty.sum(axis=0),qty.sum(axis=0),rate[t],event[t],lo[t],hi[t],order);equity+=f;funding+=f
        for k in active:
            if not updates[t-1,k]:continue
            target=intents[t-1,k]*equity/px
            delta=target-qty[k];notion=float(np.sum(np.abs(delta)*px))
            cost=notion*(fee+slip);qty[k]=target
            equity-=cost;turn+=notion;fees+=notion*fee;slippage+=notion*slip
        if order=='new_after_fill' and event[t].any():
            f=worst_funding(qty.sum(axis=0),qty.sum(axis=0),rate[t],event[t],lo[t],hi[t],order);equity+=f;funding+=f
        gross=float(np.sum(np.abs(qty)*px));grosspeak=max(grosspeak,gross/max(equity,1e-10))
        if gross>.95*equity and gross>0:
            frac=max(0.,(.93*equity)/gross);delta=qty*(1-frac)
            notion=float(np.sum(np.abs(delta)*px));qty*=frac
            equity-=notion*(fee+slip);turn+=notion;fees+=notion*fee;slippage+=notion*slip;clipped+=1
        g=float(np.sum(np.abs(qty)*px));concpeak=max(concpeak,float(np.max(np.sum(np.abs(qty)*px,axis=0)))/g if g>0 else 0.)
        if g>.95*equity+1e-6:breaches+=1
        net=qty.sum(axis=0);worst=np.where(net>=0,l[t],h[t]);intramin=min(intramin,equity+float(np.dot(net,worst-px)))
        equity+=float(np.dot(net,c[t]-px));prev=c[t];hist.append(equity);deltas.append(equity-before)
        if t==9503:year_end[2023]=equity;year_start[2024]=equity
        if equity<=0 or not math.isfinite(equity):return {'passed':False,'failure':'INSOLVENT_CLOSE','t':t,'book':book,'tier':tier,'order':order}
    year_end[2024]=equity
    curve=np.asarray(hist);peak=np.maximum.accumulate(np.r_[10000.,curve]);dd=float(np.min(np.r_[10000.,curve]/peak-1))
    daily=curve[23::24];dr=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
    changes=np.asarray(deltas);wins=changes[changes>1e-10];loss=-changes[changes< -1e-10]
    return {'passed':not breaches and intramin>0,'book':book,'tier':tier,'order':order,'final_equity':float(equity),
       'cagr':float((equity/10000.)**(365.25/731)-1),'log_growth':float(np.log(equity/10000.)),
       'year_returns':{str(y):float(year_end[y]/year_start[y]-1) for y in (2023,2024)},
       'max_dd':dd,'turnover':turn,'fees':fees,'slippage':slippage,'funding':funding,'clipped':clipped,
       'gross_breaches':breaches,'min_intrabar_equity':intramin,'max_pre_governor_gross_fraction':grosspeak,
       'max_single_asset_gross_concentration':concpeak,'positive_days':int((dr>0).sum()),'daily_count':len(dr),
       'daily_win_rate':float(np.mean(dr>0)),'cvar_1pct':float(np.mean(np.sort(dr)[:max(1,len(dr)//100)])),
       'hourly_net_pf':float(wins.sum()/loss.sum()) if len(loss) else None,
       'hourly_net_payoff':float(wins.mean()/loss.mean()) if len(wins) and len(loss) else None,
       'hourly_net_win_rate':float(len(wins)/(len(wins)+len(loss))) if len(wins)+len(loss) else 0.,
       'trade_pf_payoff_win_rate_independent':False}

def run(root,envelope_path,tiers=('base','severe','supersevere'),orders=('carried_before_fill','new_after_fill')):
    g=source_gate(root)
    if g['decision']!='PASS_SOURCE_ONLY':raise ValueError('MA_SOURCE_GATE_REJECT_NO_PNL')
    d=load(root);lo,hi,envelope_sha=read_envelope(envelope_path,d)
    intents,updates,*_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    cells=[]
    for tier in tiers:
        for order in orders:
            for book in BOOKS:
                x=physical(d,intents,updates,book,tier,order,lo,hi);cells.append(x)
                print('MA_LOCAL',tier,order,book,'CAGR',round(x.get('cagr',-1)*100,3),'TURN',round(x.get('turnover',-1)),flush=True)
    marg={}
    for tier in tiers:
        for order in orders:
            group={z['book']:z for z in cells if z['tier']==tier and z['order']==order}
            f=group['MA_full'];marg[tier+'/'+order]={s:float(f['log_growth']-group[b]['log_growth']) for s,b in [('Opportunity','MA_minus_opportunity'),('Relative_Value','MA_minus_RV'),('Stress_Recovery','MA_minus_stress')]}
    failures=[]
    for order in orders:
        for tier in ('base','severe'):
            if tier not in tiers:continue
            group={z['book']:z for z in cells if z['tier']==tier and z['order']==order}
            full=group['MA_full']
            if not full.get('passed'):failures.append(f'{tier}/{order}:physical_invariant')
            if full.get('cagr',-1)<=(.5 if tier=='base' else .3):failures.append(f'{tier}/{order}:cagr')
            if full.get('turnover',float('inf'))>600000:failures.append(f'{tier}/{order}:turnover')
            if tier=='severe':
                if full.get('max_dd',-1)<=-.45:failures.append(f'{tier}/{order}:max_dd')
                if any(x<=0 for x in full.get('year_returns',{}).values()):failures.append(f'{tier}/{order}:year_return')
            for sleeve,book in [('Opportunity','MA_minus_opportunity'),('Relative_Value','MA_minus_RV'),('Stress_Recovery','MA_minus_stress')]:
                delta=marg[tier+'/'+order][sleeve]
                if delta<=.02:failures.append(f'{tier}/{order}:{sleeve}:marginal')
                if full.get('passed') and group[book].get('passed'):
                    for year in ('2023','2024'):
                        f=full['year_returns'][year];b=group[book]['year_returns'][year]
                        if f<=-1 or b<=-1 or math.log1p(f)-math.log1p(b)<-.03:
                            failures.append(f'{tier}/{order}:{sleeve}:{year}:annual_marginal')
    return {'architecture':'MA','source_gate':g,'cells':cells,'marginals':marg,'training_only':True,
            'decision':'REJECT_EARLY_TRAINING_ECONOMIC' if failures else 'PASS_PROVISIONAL_TRAINING_NOT_INDEPENDENTLY_VALIDATED',
            'gate_failures':failures,'signed_funding':'SHA_PINNED_OFFICIAL_OHLC_TWO_SIDED_WORST_ENVELOPE',
            'envelope_sha256':envelope_sha,'native_30cell_executed':len(cells)==30,
            'local_diagnostic_only':True,'eligible_for_promotion':False,'independent_settlement_oracle':False,
            'original_30cell_workflow':False,'holdout_accessed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True);p.add_argument('--output',required=True)
    p.add_argument('--tiers',nargs='+',default=['base','severe','supersevere'],choices=tuple(COSTS));p.add_argument('--orders',nargs='+',default=['carried_before_fill','new_after_fill'],choices=('carried_before_fill','new_after_fill'))
    a=p.parse_args();result=run(a.root,a.envelope_csv,a.tiers,a.orders)
    open(a.output,'w').write(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('MA_ECONOMIC_GATE',result['decision'],result['gate_failures'],flush=True)
    print('MA_MARGINALS',json.dumps(result['marginals'],indent=2))
    raise SystemExit(0 if result['decision']=='PASS_PROVISIONAL_TRAINING_NOT_INDEPENDENTLY_VALIDATED' else 2)

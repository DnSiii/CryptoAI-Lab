#!/usr/bin/env python3
"""V98 OK preregistered volatility-budgeted seven-slot 30-cell signed physical TRAINING, no live/holdout."""
import argparse,json,math
import numpy as np
from v98_clean4_training_reader import load
from ok_sources import bundle,load_oi,BOOKS,HOURS,WARMUP
from ok_source_gate import run as source_gate
from ok_intents import build as intents_build
from v98_mark_envelope_settlement import read_envelope,worst_funding
from v98_oneway_net_atomic_planner import plan_virtual,settle_virtual
from v98_next_pretrade_projection import project
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
ORDERS=('carried_before_fill','new_after_fill')
LEDGER=[]
def physical(d,intents,updates,book,tier,order,lo,hi):
    o,h,l,c,rate,event=[d[k] for k in ('o','h','l','c','rate','event')]
    fee,slip=COSTS[tier];active=BOOKS[book]
    qty=np.zeros((4,4));equity=10000.;prev=c[WARMUP]
    turn=fees=slippage=funding=0.;scales=0;intramin=10000.
    year_start={2023:10000.,2024:None};year_end={}
    hist=[];deltas=[];grosspeak=0.;condpeak=0.;max_intermediate=0.;refresh_count=0
    def fail(why,t):
        return {'passed':False,'failure':why,'t':t,'book':book,'tier':tier,'order':order,
                'turnover_until_failure':turn,'training_only':True}
    for t in range(WARMUP+1,HOURS):
        before=equity;before_qty=qty.copy();px=o[t]
        equity+=float(np.sum(qty*(px-prev)))
        if equity<=0 or not math.isfinite(equity):return fail('INTOLVENT_OPEN',t)
        pre_gross=float(np.sum(np.abs(qty)*px))
        pre_net=float(np.sum(np.abs(qty.sum(axis=0))*px))
        grosspeak=max(grosspeak,pre_gross/equity)
        if max(pre_gross,pre_net)>equity*(1+1e-9):return fail('PREEXISTING_GAP_LEVERAGE',t)
        # OK uses the previously validated shared causal all-hour funding-aware governor.
        # The guard uses only inventory, current open price, NAV and known event
        # calendar. It never reads the realized funding rate or mark for sizing.
        guard=bool(pre_gross>.84*equity or
                   (bool(event[t].any()) and pre_gross>.82*equity))
        need=bool(any(updates[t-1,k] for k in active) or guard)
        planned=None
        if need:
            # Pre-registered OK causal joint projection: updated vs carried
            # sleeve weights, then source-independent atomic net execution.
            source_w=intents[t-1].copy()
            enabled=np.zeros(4,bool)
            updated=np.zeros(4,bool)
            for k in active:
                enabled[k]=True
                updated[k]=updates[t-1,k]
            source_w[~enabled]=0.
            try:
                projection=project(qty,source_w,updated,px,equity,
                                   funding_event=bool(event[t].any()))
                planned=plan_virtual(qty,projection['weights'],px,equity,fee,slip,
                                    funding_event=bool(event[t].any()))
            except ValueError as e:return fail('ATOMIC_'+str(e),t)
            max_intermediate=max(max_intermediate,planned['max_intermediate_net_gross_fraction'])
            if 0 in active and (t-1-WARMUP)%672==0 and updates[t-1,0]:
                refresh_count+=1
        # Execution feasibility: an open price without traded volume is not a fill.
        # Reject the frozen candidate; never skip or re-time an intended trade.
        if planned is not None:
            traded=np.abs(planned['net_delta'])>1e-12
            if np.any(traded & (d['q'][t]<=0)):
                return fail('ZERO_VOLUME_EXECUTION',t)
        newqty=planned['virtual_quantity'] if planned is not None else qty
        if event[t].any():
            cash=worst_funding(qty.sum(axis=0),newqty.sum(axis=0),rate[t],event[t],lo[t],hi[t],order)
        else:cash=0.
        if planned is not None:
            try:equity=settle_virtual(planned,cash,order,equity,qty,px)
            except ValueError as e:return fail('SETTLE_'+str(e),t)
            qty=newqty
            turn+=planned['turnover'];fees+=planned['fees'];slippage+=planned['slippage']
            if planned['scale']<1-1e-10:scales+=1
        else:equity+=cash
        funding+=cash
        if equity<=0 or not math.isfinite(equity):return fail('INTOLVENT_AFTER_FUNDING',t)
        gross=float(np.sum(np.abs(qty)*px))
        netgross=float(np.sum(np.abs(qty.sum(axis=0))*px))
        grosspeak=max(grosspeak,gross/equity)
        if max(gross,netgross)>equity*(1+1e-9):return fail('POST_FUNDING_LEVERAGE',t)
        if max(gross,netgross)>equity*.90+1e-7:return fail('POST_FUNDING_GROSS_CAP',t)
        if gross:condpeak=max(condpeak,float(np.max(np.sum(np.abs(qty)*px,axis=0)))/gross)
        net=qty.sum(axis=0);worst=np.where(net>=0,l[t],h[t])
        intramin=min(intramin,equity+float(np.dot(net,worst-px)))
        if intramin<=0:return fail('INTOLVENT_INTRABAR',t)
        equity+=float(np.dot(net,c[t]-px));prev=c[t]
        if equity<=0 or not math.isfinite(equity):return fail('INTOLVENT_CLOSE',t)
        if max(float(np.sum(np.abs(qty)*c[t])),float(np.sum(np.abs(qty.sum(axis=0))*c[t])))>equity*(1+1e-9):return fail('CLOSE_MARK_GROSS_ABOVE_NAV',t)
        if book=='OK_full' and tier=='base' and order=='carried_before_fill':
            LEDGER.append({'t':t,'qty_before':before_qty.tolist(),'qty_after':qty.tolist(),
                'equity_before':float(before),'fee_cash':float(planned['fees'] if planned else 0.),
                'slippage_cash':float(planned['slippage'] if planned else 0.),
                'funding_cash':float(cash),'equity_close':float(equity),'net_before':before_qty.sum(axis=0).tolist(),
                'net_after':qty.sum(axis=0).tolist()})
        hist.append(equity);deltas.append(equity-before)
        if t==9503:year_end[2023]=equity;year_start[2024]=equity
    year_end[2024]=equity
    curve=np.asarray(hist);peak=np.maximum.accumulate(np.r_[10000.,curve])
    dd=float(np.min(np.r_[10000.,curve]/peak-1))
    daily=curve[22::24];dr=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
    changes=np.asarray(deltas);wins=changes[changes>1e-10];loss=-changes[changes< -1e-10]
    return {'passed':True,'book':book,'tier':tier,'order':order,
        'final_equity':float(equity),'cagr':float((equity/10000.)**(365.25/731)-1),
        'lok_growth':float(np.log(equity/10000.)),
        'year_returns':{str(y):float(year_end[y]/year_start[y]-1) for y in (2023,2024)},
        'max_dd':dd,'turnover':turn,'fees':fees,'slippage':slippage,'funding':funding,
        'scaled_atomic_fills':scales,'forced_core_refreshes_executed':refresh_count,
        'max_intermediate_gross_fraction':max_intermediate,
        'max_pretrade_or_post_gross_fraction':grosspeak,
        'min_intrabar_equity':intramin,'max_single_asset_gross_concentration':condpeak,
        'positive_days':int((dr>0).sum()),'daily_count':len(dr),
        'daily_win_rate':float(np.mean(dr>0)),
        'cvar_1pct':float(np.mean(np.sort(dr)[:max(1,len(dr)//100)])),
        'hourly_net_pf':float(wins.sum()/loss.sum()) if len(loss) else None,
        'hourly_net_payoff':float(wins.mean()/loss.mean()) if len(wins) and len(loss) else None,
        'hourly_net_win_rate':float(len(wins)/(len(wins)+len(loss))) if len(wins)+len(loss) else 0.,
        'trade_pf_payoff_win_rate_independent':False,
        'one_way_netting':True}
def run(root,oi_root,envelope_path):
    g=source_gate(root,oi_root)
    if g['decision']!='PASS_SOURCE_ONLY':raise ValueError('OK_SOURCE_REJECT_NT_PNL')
    d=load(root);oi,_=load_oi(oi_root);lo,hi,envelope_sha=read_envelope(envelope_path,d)
    raw,updates,_,eligible=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')),oi)
    allocation=intents_build(d,raw,updates)
    intents=allocation['weights']
    cells=[]
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                x=physical(d,intents,updates,book,tier,order,lo,hi)
                cells.append(x)
                print('OK_CELL',tier,order,book,'PASS',x['passed'],
                    'CAGR',round(x.get('cagr',-1)*100,3),
                    'TURN',round(x.get('turnover',-1)),x.get('failure',''),flush=True)
    marg={};failures=[]
    for tier in COSTS:
        for order in ORDERS:
            group={z['book']:z for z in cells if z['tier']==tier and z['order']==order}
            if not all(x['passed'] for x in group.values()):
                failures.append(tier+'/'+order+':physical_invariant')
                continue
            f=group['OK_full']
            marg[tier+'/'+order]={s:float(f['lok_growth']-group[b]['lok_growth'])
                for s,b in [('Opportunity','OK_minus_opportunity'),
                            ('Relative_Value','OK_minus_RV'),('Stress_Recovery','OK_minus_stress')]}
            if tier not in ('base','severe'):continue
            if f['cagr']<=(.8 if tier=='base' else .6):failures.append(tier+'/'+order+':cagr')
            if f['turnover']>600000:failures.append(tier+'/'+order+':turnover')
            if tier=='severe':
                if f['max_dd']<=-.45:failures.append(tier+'/'+order+':max_dd')
                if any(z<=0 for z in f['year_returns'].values()):failures.append(tier+'/'+order+':annual_return')
            for sleeve,book in [('Opportunity','OK_minus_opportunity'),
                                ('Relative_Value','OK_minus_RV'),('Stress_Recovery','OK_minus_stress')]:
                if marg[tier+'/'+order][sleeve]<=.02:failures.append(tier+'/'+order+':'+sleeve+':marginal')
                b=group[book]
                for year in ('2023','2024'):
                    delta=math.log1p(f['year_returns'][year])-math.log1p(b['year_returns'][year])
                    if delta<-.03:failures.append(tier+'/'+order+':'+sleeve+':'+year+':annual_marginal')
    return {'architecture':'OK','source_gate':g,'allocation_decisions':allocation['allocation_decisions'],
        'allocation_active_periods':allocation['activated_period_counts'],'cells':cells,'marginals':marg,
        'decision':'REJECT_EARLY_TRAINING' if failures else 'PASS_PROVISIONAL_TRAINING_NOT_VALIDATED',
        'gate_failures':failures,'native_30cell_executed':len(cells)==30,
        'funding_envelope_sha256':envelope_sha,'actual_future_funding_used_to_size':False,
        'independent_pnt_oracle':False,'one_way_netting':True,'training_only':True,'holdout_accessed':False,
        'eligible_for_promotion':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--oi-root',required=True);p.add_argument('--envelope-csv',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--ledger-output',default='ok_base_full_hourly_forensic.jsonl')
    a=p.parse_args();result=run(a.root,a.oi_root,a.envelope_csv)
    with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    if len(LEDGER)==HOURS-WARMUP-1:
        with open(a.ledger_output,'w') as f:
            for row in LEDGER:f.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n')
        print('OK_FULL_BASE_LEDGER_FOR_INDEPENDENT_ACCOUNTING',len(LEDGER),flush=True)
    print('OK_ECONOMIC_GATE',result['decision'],result['gate_failures'],flush=True)
    raise SystemExit(0 if result['decision']=='PASS_PROVISIONAL_TRAINING_NOT_VALIDATED' else 2)
